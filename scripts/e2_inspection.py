"""Read bounded observational captures. Truncated tails never become complete runs."""
from __future__ import annotations

import csv
import io
import json
from pathlib import Path
import struct
import zlib

LIMIT = 32 * 1024 * 1024
EVENT_HEADER = ['event_id', 'replay_sequence', 'replay_checkpoint', 'update_id',
                'present_id', 'snapshot_id', 'kind', 'a', 'b']
STATE_HEADER = ['snapshot_id', 'scope', 'entity_id', 'field', 'value', 'present']


def rows(path: Path, header: list[str]):
    if path.is_symlink() or not path.is_file() or path.stat().st_size > LIMIT:
        raise ValueError(f'Invalid or oversized inspection file: {path}')
    data = path.read_bytes()
    # Native writer never emits quoted/multiline fields. Only newline-published
    # rows are recoverable; complete malformed rows remain errors.
    data = data[:data.rfind(b'\n') + 1]
    reader = csv.reader(io.StringIO(data.decode('utf-8')), strict=True)
    if next(reader, None) != header:
        raise ValueError(f'Unsupported inspection header: {path}')
    for row in reader:
        if len(row) != len(header):
            raise ValueError(f'Malformed inspection row: {path}')
        yield dict(zip(header, row))


class Inspection:
    def __init__(self, source: Path):
        self.path = source.resolve(strict=True)
        if (self.path / 'inspection').is_dir():
            self.path /= 'inspection'
        self.events = []
        snapshot = 0
        for raw in rows(self.path / 'timeline.csv', EVENT_HEADER):
            event = {k: int(v) if k != 'kind' else v for k, v in raw.items()}
            if event['event_id'] != len(self.events) + 1 or any(event[k] < 0 for k in EVENT_HEADER[:6]):
                raise ValueError('Inspection event identity/order mismatch')
            expected = snapshot if event['kind'] in ('frame_written', 'frame_failed', 'frame_evicted', 'frame_unavailable') else snapshot+1
            if event['snapshot_id'] != expected or self.events and self.events[-1]['kind'] == 'end':
                raise ValueError('Inspection snapshot order mismatch')
            snapshot = expected
            self.events.append(event)
        published = {e['snapshot_id'] for e in self.events}
        self.changes: dict[int, list[dict]] = {}
        last = 0
        for raw in rows(self.path / 'state.csv', STATE_HEADER):
            row = {k: int(v) if k in ('snapshot_id', 'entity_id', 'value', 'present') else v
                   for k, v in raw.items()}
            sid = row.pop('snapshot_id')
            if sid < last or sid < 1 or row['present'] not in (0, 1):
                raise ValueError('Invalid state delta')
            last = sid
            if sid in published:
                self.changes.setdefault(sid, []).append(row)
        self.complete = bool(self.events and self.events[-1]['kind'] == 'end'
                             and not (self.path / 'inspection.incomplete').exists())
        if self.complete and last > snapshot:
            raise ValueError('Completed inspection has unpublished state')

    def iter_states(self):
        """Yield each published snapshot with a borrowed, incrementally updated map."""
        state = {}
        for sid in sorted({e['snapshot_id'] for e in self.events}):
            for row in self.changes.get(sid, []):
                key = row['scope'], row['entity_id'], row['field']
                if row['present']:
                    state[key] = row['value']
                else:
                    state.pop(key, None)
            yield sid, state

    def state(self, snapshot: int | None = None, scope: str | None = None,
              entity: int | None = None) -> list[dict]:
        if snapshot is None:
            snapshot = self.events[-1]['snapshot_id'] if self.events else 0
        if snapshot not in {e['snapshot_id'] for e in self.events}:
            raise ValueError(f'Unpublished snapshot: {snapshot}')
        result = {}
        for sid, changes in self.changes.items():
            if sid > snapshot:
                break
            for row in changes:
                key = row['scope'], row['entity_id'], row['field']
                if row['present']:
                    result[key] = row['value']
                else:
                    result.pop(key, None)
        return [dict(scope=s, entity_id=i, field=f, value=v)
                for (s, i, f), v in sorted(result.items())
                if (scope is None or s == scope) and (entity is None or i == entity)]

    def timeline(self, kind=None, limit=100, after=0):
        return [dict(e, changes=self.changes.get(e['snapshot_id'], [])
                     if e['kind'] not in ('frame_written', 'frame_failed', 'frame_evicted', 'frame_unavailable') else [])
                for e in self.events if e['event_id'] > after
                and (kind is None or e['kind'] == kind)][:limit]

    def frame_path(self, number: int):
        if number < 1 or number > 2**63-1:
            raise ValueError('Invalid frame number')
        if not any(e['kind'] == 'frame_written' and e['a'] == number for e in self.events):
            raise ValueError('Frame was not successfully published')
        path = self.path / f'frame-{number}.ppm'
        if path.is_symlink() or not path.is_file() or path.stat().st_size > 1024 * 1024:
            raise ValueError('Missing, symlinked or oversized frame')
        return path


def differences(left, right):
    def keyed(state):
        return {(r['scope'], r['entity_id'], r['field']): r['value'] for r in state}
    a, b = keyed(left), keyed(right)
    return [dict(scope=k[0], entity_id=k[1], field=k[2], before=a.get(k), after=b.get(k))
            for k in sorted(a.keys() | b.keys()) if a.get(k) != b.get(k)]


def png(path: Path) -> bytes:
    # Reuse the project's Netpbm decoder; dimensions are independently bounded.
    from e2r_visibility_sheet import read_netpbm
    width, height, pixels = read_netpbm(path)
    if not (0 < width <= 640 and 0 < height <= 480):
        raise ValueError('Inspection frame exceeds game resolution')
    def chunk(tag, data):
        return struct.pack('!I', len(data)) + tag + data + struct.pack('!I', zlib.crc32(tag + data))
    data = b''.join(b'\0' + pixels[y * width * 3:(y + 1) * width * 3] for y in range(height))
    return (b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('!2I5B', width, height, 8, 2, 0, 0, 0))
            + chunk(b'IDAT', zlib.compress(data)) + chunk(b'IEND', b''))


def write_report(capture: Inspection, destination: Path):
    import base64
    data = dict(complete=capture.complete, events=capture.events,
                changes=capture.changes, frames={})
    for event in capture.events:
        if event['kind'] == 'frame_written':
            try:
                data['frames'][event['a']] = base64.b64encode(png(capture.frame_path(event['a']))).decode()
            except (OSError, ValueError):
                pass
    payload = json.dumps(data).replace('<', '\\u003c')
    html = '''<!doctype html><meta charset="utf-8"><title>Ecstatica II inspection</title>
<style>body{font:16px system-ui;background:#161a20;color:#eee;margin:24px}
button,input,select{font:inherit}table{border-collapse:collapse;width:100%}td,th{text-align:left;padding:5px;border-bottom:1px solid #444}
img{max-width:640px;width:100%;image-rendering:pixelated}pre{white-space:pre-wrap}label{margin-right:20px}</style>
<h1>Ecstatica II inspection</h1><p id="status"></p>
<label>Event <input id="event" type="range" min="0" value="0"></label>
<button id="back">Previous</button> <button id="next">Next</button>
<label>Filter <input id="filter" placeholder="actor 0, script, camera..."></label>
<pre id="where"></pre><img id="frame" alt="Nearest preceding captured game frame">
<table><thead><tr><th>Scope</th><th>Entity</th><th>Field</th><th>Value</th></tr></thead><tbody id="state"></tbody></table>
<script id="data" type="application/json">PAYLOAD</script><script>
const data=JSON.parse(document.getElementById('data').textContent),slider=document.getElementById('event');
slider.max=Math.max(0,data.events.length-1);
document.getElementById('status').textContent=data.complete?'Completed observational capture':'Incomplete capture: only published observations are shown';
function render(){const e=data.events[+slider.value];if(!e)return;
document.getElementById('where').textContent=JSON.stringify(e,null,2);
const state=new Map();for(let sid=1;sid<=e.snapshot_id;sid++)for(const r of data.changes[sid]||[]){const key=JSON.stringify([r.scope,r.entity_id,r.field]);if(r.present)state.set(key,r);else state.delete(key);}
const body=document.getElementById('state'),filter=document.getElementById('filter').value.toLowerCase();body.replaceChildren();
for(const r of state.values()){if(![r.scope,r.entity_id,r.field].join(' ').toLowerCase().includes(filter))continue;const tr=document.createElement('tr');for(const k of ['scope','entity_id','field','value']){const td=document.createElement('td');td.textContent=r[k];tr.append(td);}body.append(tr);}
let frame=null;for(const x of data.events){if(x.event_id>e.event_id)break;if(x.kind==='frame_written'&&data.frames[x.a])frame=data.frames[x.a];}
const img=document.getElementById('frame');img.hidden=!frame;if(frame)img.src='data:image/png;base64,'+frame;
}slider.oninput=render;document.getElementById('filter').oninput=render;
for(const [id,delta] of [['back',-1],['next',1]])document.getElementById(id).onclick=()=>{slider.value=+slider.value+delta;render();};render();</script>'''
    with destination.open('x') as stream:
        stream.write(html.replace('PAYLOAD', payload))
