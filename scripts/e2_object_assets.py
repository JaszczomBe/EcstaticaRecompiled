"""Read original object resources and their scene/action links without loading them."""
import argparse
import hashlib
import json
from pathlib import Path
import struct


class ObjectAssets:
    def __init__(self, root):
        self.root = root
        self.archive = (root / 'Files/ECSTATIC').read_bytes()
        self.offset_bytes = (root / 'OFFSETS').read_bytes()
        self.offsets = struct.unpack('>' + str(len(self.offset_bytes) // 4) + 'I', self.offset_bytes)
        self.names_bytes = (root / 'Code/ECSTATIC.FAN').read_bytes()
        self.names = []
        cursor = 34
        assert self.names_bytes[:8] == b'FANT\x007\x00\x00'
        for _ in range(11):
            pool = []
            while self.names_bytes[cursor]:
                end = self.names_bytes.index(0, cursor)
                pool.append(self.names_bytes[cursor:end].decode('ascii'))
                cursor = end + 1
            self.names.append(pool)
            cursor += 1
        self.scripts = {}
        cursor += 30  # Three empty prefix records, as consumed by 0x444c10.
        def word():
            nonlocal cursor
            value = struct.unpack_from('>H', self.names_bytes, cursor)[0]
            cursor += 2
            return value
        for _ in range(word()):
            identity = word()
            tokens = []
            while (token := word()):
                tokens.append(token)
                if token & 0xf000 == 0xe000:
                    tokens.extend(word() for _ in range(((token & 4095) + 1) // 2))
            for _ in range(word()):
                cursor = self.names_bytes.index(0, cursor) + 1
            self.scripts[identity] = tokens

    def resource(self, group, identity):
        base, count = {'scene': (0, 2500), 'actor': (2500, 5000),
                       'action': (7500, 2000), 'representation': (9500, 500)}[group]
        assert 0 <= identity < count
        start = self.offsets[base + identity]
        if start == 0xffffffff:
            return None
        assert self.archive[start:start + 4] == b'FANT'
        end = self.archive.find(b'FANT', start + 4)
        if end < 0:
            end = len(self.archive)
        return start, self.archive[start:end]

    def actor(self, identity):
        resource = self.resource('actor', identity)
        if resource is None:
            return dict(id=identity, name=self.names[1][identity], present=False)
        start, data = resource
        assert struct.unpack_from('>3H', data, 44) == (8, 0, identity)
        records = []
        for cursor in range(44, len(data) - 9, 10):
            row = struct.unpack_from('>5h', data, cursor)
            if row[0] == 0:
                break
            assert 0 < row[0] <= 0x4e, (identity, cursor, row)
            records.append(row)
        nodes = []
        for row in records:
            if row[0] in (7, 10):
                nodes.append(dict(id=row[2]))
        for node in nodes:
            own = [row for row in records if row[1] == node['id']]
            for label, kind in [('dimensions', 4), ('material', 3), ('flags', 14),
                                ('texture', 70), ('light', 72)]:
                node[label] = [row[2:] for row in own if row[0] == kind]
        reps = [row[2] for row in records if row[0] == 55 and row[2] >= 0]
        representations = []
        for rep in reps:
            entry = dict(id=rep, name=self.names[7][rep], actions=[])
            resource = self.resource('representation', rep)
            if resource:
                rep_start, body = resource
                entry['offset'] = rep_start
                for cursor in range(76, len(body) - 9, 10):
                    row = struct.unpack_from('>5h', body, cursor)
                    if row[0] == 54:
                        entry['actions'].append(dict(slot=row[2], id=row[3], name=self.names[2][row[3]]))
                    elif row[0] == 0:
                        break
            representations.append(entry)
        scenes = []
        signature = struct.pack('>2H', 26, 0xffff)
        for scene in range(2500):
            resource = self.resource('scene', scene)
            if not resource:
                continue
            scene_start, body = resource
            if len(body) < 64 or struct.unpack_from('>2H', body, 54) != (25, scene):
                continue
            cursor = 0
            while (cursor := body.find(signature, cursor)) >= 0:
                if cursor + 10 <= len(body) and struct.unpack_from('>2H', body, cursor + 6) == (2, identity):
                    end = body.find(signature, cursor + 10)
                    track = body[cursor:len(body) if end < 0 else end]
                    position = None
                    at = track.find(struct.pack('>2H', 22, 0))
                    if at >= 0 and at + 10 <= len(track):
                        position = struct.unpack_from('>3h', track, at + 4)
                    scenes.append(dict(id=scene, name=self.names[3][scene], offset=scene_start,
                                       camera=struct.unpack_from('>H', body, 58)[0], position=position))
                cursor += 2
        callbacks = []
        for row in records:
            if row[0] in (66, 78):
                for slot, code in enumerate(row[2:]):
                    if code > 0:
                        # Stored callback references are script ID + 1.
                        callbacks.append(dict(record=row[0], slot=slot, id=code - 1,
                            name=self.names[6][code - 1], tokens=self.scripts.get(code - 1)))
        return dict(id=identity, name=self.names[1][identity], present=True, offset=start,
                    nodes=nodes, polygons=sum(row[0] == 43 for row in records),
                    vertices=sum(row[0] == 41 for row in records), representations=representations,
                    texture_ids=sorted({row[2] for row in records if row[0] == 70 and row[2] >= 0}),
                    callbacks=callbacks, scenes=scenes)

    def representation_actors(self, representations):
        """Select original roots by their authored representation record (55)."""
        result = set()
        for identity in range(1, 5000):
            resource = self.resource('actor', identity)
            if resource is None:
                continue
            for cursor in range(44, len(resource[1]) - 9, 10):
                row = struct.unpack_from('>5h', resource[1], cursor)
                if row[0] == 0:
                    break
                if row[0] == 55 and row[2] in representations:
                    result.add(identity)
        return result

    def inventory(self, identities, representations=()):
        family_ids = self.representation_actors(representations) if representations else set()
        return dict(source='original version-55 OFFSETS/FANT/name pools; read-only inventory',
                    hashes={name: hashlib.sha256(data).hexdigest() for name, data in
                            [('Files/ECSTATIC', self.archive), ('OFFSETS', self.offset_bytes),
                             ('Code/ECSTATIC.FAN', self.names_bytes)]},
                    selected_representations=list(representations), family_actor_ids=sorted(family_ids),
                    actors=[self.actor(identity) for identity in sorted(set(identities) | family_ids)])


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('game_data', type=Path)
    parser.add_argument('--actors', type=int, nargs='+', default=[5, 55, 537, 603, 710, 711, 908, 909, 912, 963, 980, 1085, 3717, 3820, 3821, 3822])
    parser.add_argument('--representations', type=int, nargs='+', default=[],
                        help='Also inventory every actor authored with these original representation IDs')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = ObjectAssets(args.game_data).inventory(args.actors, args.representations)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + '\n')
    print('Mapped', [(row['id'], row['name']) for row in result['actors']])
