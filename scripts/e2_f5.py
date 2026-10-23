"""Session artifacts for the ordinary VS Code gameplay investigation launch."""
from __future__ import annotations
import argparse
import fcntl
import hashlib
import json
from pathlib import Path
import shutil
import sys
from e2_bundle import ROOT, digest, source_context, source_lock
from e2_inspection import Inspection, write_report

INDEX = ROOT/'.tmp/f5-investigations'


def save_json(path, value):
    temporary = path.with_name(path.name+'.tmp')
    temporary.write_text(json.dumps(value,indent=2)+'\n')
    temporary.replace(path)


def begin(session: Path, executable: Path, pid: int):
    """Pin /proc/PID/exe: a rebuild may already have replaced the launch path."""
    session = session.resolve(strict=True)
    destination = session/'investigation'
    destination.mkdir(exist_ok=False)
    INDEX.mkdir(parents=True,exist_ok=True)
    key = hashlib.sha256(str(session).encode()).hexdigest()[:12]
    record = INDEX/(session.name+'_'+key+'.json')
    state = dict(schema='e2debug.f5.1',session=str(session),program=str(executable),pid=pid,
                 state='collecting',result={'status':'debugger-disconnected; exit cause unavailable'})
    save_json(record,state)
    image = Path(f'/proc/{pid}/exe')
    shutil.copyfile(image,destination/'e2recomp')
    (destination/'e2recomp').chmod(0o555)
    state['executable_sha256'] = digest(destination/'e2recomp')
    state['context_revision'] = source_context(destination/'context',[0])
    state['source_context'] = 'working tree at debugger startup; executable hash pins the actual running image'
    for name in ('CMakeCache.txt','compile_commands.json'):
        if (executable.parent/name).is_file():
            shutil.copyfile(executable.parent/name,destination/name)
    save_json(record,state)
    save_json(destination/'manifest.json',state)
    return record


def append(record: Path, kind: str, detail: str, **progress):
    state = json.loads(record.read_text())
    destination = Path(state['session'])/'investigation'
    path = destination/'debugger.log'
    remaining = 8*1024*1024-(path.stat().st_size if path.exists() else 0)
    if remaining <= 0:
        return
    value=json.dumps(dict(kind=kind,**progress))+'\n'+detail[:512*1024]+'\n'
    with path.open('ab') as stream:
        stream.write(value.encode()[:remaining])


def ended(record: Path, result):
    state = json.loads(record.read_text())
    state['result'] = result
    save_json(record,state)


def finalize(record: Path):
    # Serialize postDebugTask and debugger-exit fallback for the same session.
    with record.with_suffix('.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX)
        state = json.loads(record.read_text())
        if state['state'] == 'finalized':
            return state
        session = Path(state['session'])
        if not session.is_dir():
            state.update(state='expired',note='Session was removed by ordinary retention before finalization')
            save_json(record,state)
            return state
        with source_lock(session):
            destination = session/'investigation'
            capture = Inspection(session)
            report = destination/'report.html'
            if not report.exists():
                write_report(capture,report)
            state.update(state='finalized',inspection_complete=capture.complete,report=str(report))
            save_json(destination/'manifest.json',state)
            save_json(record,state)
        return state


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--pending',action='store_true',help='Finalize closed F5 sessions after the debugger ends')
    args = parser.parse_args()
    if not args.pending:
        parser.error('--pending is required')
    failed = False
    for record in sorted(INDEX.glob('*.json')):
        try:
            state = json.loads(record.read_text())
            if state['state'] != 'collecting':
                continue
            state = finalize(record)
            print('F5 investigation: '+state.get('report',state['session']))
        except BlockingIOError:
            # Another F5 session still owns its lease; leave it pending.
            continue
        except (OSError,ValueError,KeyError) as error:
            failed = True
            print(f'F5 investigation retained; could not finalize {record}: {error}',file=sys.stderr)
    return int(failed)


if __name__ == '__main__':
    raise SystemExit(main())
