"""Read-only GDB samples of selected original objects and their render owners."""
import hashlib
import json
from pathlib import Path
import struct


def selected_actor_ids(identities, representations):
    import gdb
    result = set(identities)
    cursor = int(gdb.parse_and_eval('_DAT_0063726c'))
    seen = set()
    while cursor:
        if cursor in seen or len(seen) >= 256:
            raise gdb.GdbError('Invalid selected-object chain')
        seen.add(cursor)
        if any(int(gdb.parse_and_eval(f'*(short*)({cursor}+{offset})')) in representations
               for offset in (0x122, 0x124)):
            identity = int(gdb.parse_and_eval(f'*(short*){cursor}'))
            if identity > 0:
                result.add(identity)
        cursor = int(gdb.parse_and_eval(f'*(unsigned int*)({cursor}+0x4c)'))
    return sorted(result)


def observe(prefix, label, identities, representations=()):
    import gdb
    inferior = gdb.selected_inferior()
    read = lambda address, count: bytes(inferior.read_memory(address, count))
    word = lambda address: struct.unpack('<I', read(address, 4))[0]
    active = set()
    cursor = int(gdb.parse_and_eval('_DAT_0063726c'))
    while cursor:
        if cursor in active or len(active) >= 256:
            raise gdb.GdbError('Invalid active object chain')
        active.add(cursor)
        cursor = word(cursor + 0x4c)
    actors = []
    for identity in selected_actor_ids(identities, representations):
        actor = word(0x630b60 + identity * 4)
        if not actor:
            actors.append(dict(id=identity, actor=0))
            continue
        raw = read(actor, 0x194)
        h = lambda offset: struct.unpack_from('<h', raw, offset)[0]
        u = lambda offset: struct.unpack_from('<I', raw, offset)[0]
        nodes = []
        cursor = u(0x1e)
        while cursor:
            if cursor in [row['node'] for row in nodes] or len(nodes) >= 256:
                raise gdb.GdbError('Invalid object node chain')
            body = read(cursor, 0x15a)
            nodes.append(dict(node=cursor, id=struct.unpack_from('<h', body)[0],
                flags=struct.unpack_from('<H', body, 2)[0],
                owner=struct.unpack_from('<I', body, 0x22)[0],
                dimensions=struct.unpack_from('<3h', body, 0x68),
                world=struct.unpack_from('<3h', body, 0x80),
                camera=struct.unpack_from('<3h', body, 0x92),
                local_pose_hash=hashlib.sha256(body[0x26:0x32]+body[0x68:0x74]+body[0xec:0xfe]).hexdigest(),
                material=struct.unpack_from('<h', body, 0xce)[0],
                texture=struct.unpack_from('<h', body, 0x156)[0]))
            cursor = struct.unpack_from('<I', body, 0x4c)[0]
        polygons = []
        cursor = u(0xd8)
        while cursor:
            if cursor in [row['polygon'] for row in polygons] or len(polygons) >= 1024:
                raise gdb.GdbError('Invalid object polygon chain')
            body = read(cursor, 0x40)
            polygons.append(dict(polygon=cursor, flags=struct.unpack_from('<H', body, 2)[0],
                vertices=struct.unpack_from('<3I', body, 4),
                owner=struct.unpack_from('<I', body, 0x22)[0],
                material=struct.unpack_from('<2h', body, 0x10),
                texture=struct.unpack_from('<h', body, 0x2c)[0]))
            cursor = struct.unpack_from('<I', body, 0x1e)[0]
        rep, action = u(0x11e), u(0xa6)
        actors.append(dict(id=identity, actor=actor, active=actor in active,
            position=[h(0x84+i*2) for i in range(3)], attachment=u(0xf2),
            requested_representation=h(0x122), standing_representation=h(0x124),
            representation=struct.unpack('<h',read(rep,2))[0] if rep else -1,
            action=struct.unpack('<h',read(action,2))[0] if action else -1,
            progress=struct.unpack_from('<H',raw,0xac)[0], state=h(0x82), health=h(0xec),nodes=nodes,polygons=polygons))
    path = Path(prefix+'-object-mesh.json')
    rows = json.loads(path.read_text()) if path.exists() else []
    rows.append(dict(phase=label, actors=actors))
    path.write_text(json.dumps(rows,indent=2)+'\n')


def watch_rasters(prefix, identities, representations=()):
    """Observe bounded real pixel writes; no raster, page or gameplay interception."""
    import gdb
    selected = set(identities)
    value = lambda expression: int(gdb.parse_and_eval(expression))
    rows = {}
    path = Path(prefix + '-raster.json')

    class Finished(gdb.FinishBreakpoint):
        def __init__(self, identity, kind, surface, pixels, before, width, height):
            super().__init__(internal=True)
            self.identity, self.kind, self.surface = identity, kind, surface
            self.pixels, self.before = pixels, before
            self.width, self.height = width, height

        def stop(self):
            row = rows[self.identity]
            after = bytes(gdb.selected_inferior().read_memory(self.pixels, len(self.before)))
            changed = [i for i, (a, b) in enumerate(zip(self.before, after)) if a != b]
            if changed:
                xs, ys = [i % self.width for i in changed], [i // self.width for i in changed]
                row['writes'].append(dict(kind=self.kind, surface=self.surface, changed_pixels=len(changed),
                                          bounds=[min(xs), min(ys), max(xs), max(ys)],
                                          simulation_time=int(gdb.parse_and_eval('_DAT_00636588')),
                                          camera=(int(gdb.parse_and_eval('_DAT_0073cc3c'))-0x67c728)//28))
                for stage, data in (('before', self.before), ('after', after)):
                    Path(prefix + '-raster-' + str(self.identity) + '-' + self.kind + '-' + stage + '.pgm').write_bytes(
                        f'P5\n{self.width} {self.height}\n255\n'.encode() + data)
            path.write_text(json.dumps(rows, indent=2) + '\n')
            return False

    class Raster(gdb.Breakpoint):
        def __init__(self, function, kind):
            super().__init__(function, internal=True)
            self.kind = kind

        def stop(self):
            primitive = value('polygon' if self.kind == 'flat' else 'param_1')
            owner = value(f'*(unsigned int*)({primitive}+0x22)')
            identity = value(f'*(short*){owner}')
            if identity not in selected and not any(
                    value(f'*(short*)({owner}+{offset})') in representations for offset in (0x122,0x124)):
                return False
            if self.kind == 'rounded' and not any(
                    value(f'*(short*)({primitive}+{0x68+axis*2})') for axis in range(3)):
                # Scene effects have many authored zero-size dormant nodes.
                # Retain the observation budget for their actual shapes.
                return False
            row = rows.setdefault(identity, dict(attempts=0, attempts_by_kind={}, writes=[]))
            attempts = row['attempts_by_kind'].get(self.kind, 0)
            if any(w['kind'] == self.kind for w in row['writes']) or attempts >= 128:
                return False
            row['attempts'] += 1
            row['attempts_by_kind'][self.kind] = attempts + 1
            if attempts < 3:
                row.setdefault('first_attempts', []).append(dict(kind=self.kind,
                    node=value(f'*(short*){primitive}'),
                    dimensions=[value(f'*(short*)({primitive}+{0x68+axis*2})') for axis in range(3)]
                               if self.kind == 'rounded' else None,
                    camera=[value(f'*(short*)({primitive}+{0x92+axis*2})') for axis in range(3)]
                           if self.kind == 'rounded' else None,
                    simulation_time=value('_DAT_00636588')))
            surface = value('param_2')
            pixels = value(f'e2r_surface_framebuffer({surface})')
            width, height = value('_DAT_006401ec'), value('_DAT_006401d4')
            before = bytes(gdb.selected_inferior().read_memory(pixels, width * height))
            Finished(identity, self.kind, surface, pixels, before, width, height)
            return False

    return [Raster('FUN_00431a7c', 'flat'), Raster('FUN_00430fd8', 'rounded')]
