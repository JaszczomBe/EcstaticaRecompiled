#!/usr/bin/env python3
"""Run recovered gameplay regressions in dependency order, with GoogleTest-like output."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
import sys

from e2_suite import ROOT, BLOCKS, block_patterns, display_driver, catalogue, executor, ordered, run_cases, selection, digest


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--configurations',choices=('debug','asan'),nargs='+',default=['debug','asan'])
    parser.add_argument('--build',action='store_true',help='Build each already-configured SDL Debug preset first')
    parser.add_argument('--game-data',type=Path)
    parser.add_argument('--output',type=Path,help='New directory; default .tmp/gameplay-suite/run_<UTC>')
    parser.add_argument('--block',choices=BLOCKS,default='full',help='Target block; prerequisites are included automatically')
    parser.add_argument('--filter',nargs='+',help='Glob targets within the block; prerequisites are included automatically')
    parser.add_argument('--display',choices=('headless','visible'),default='headless')
    parser.add_argument('--video-driver',choices=('auto','x11','wayland'),default='auto',help='Desktop driver for visible journeys')
    parser.add_argument('--list',action='store_true')
    parser.add_argument('--replay-corpus',type=Path,help='Optional e2suite.recordings.1 manifest of complete recordings')
    args=parser.parse_args()
    configurations=list(dict.fromkeys(args.configurations))
    data=args.game_data
    if not data:
        cache=ROOT/'build/Debug/clang21-i386-sdl/CMakeCache.txt'
        if cache.is_file():
            for line in cache.read_text().splitlines():
                if line.startswith('ECSTATICA2_DATA_DIR:'):
                    data=Path(line.split('=',1)[1]);break
        if not data:
            data=ROOT/'build/Debug/clang21-i386-sdl/Ecstatica2'
    data=data.resolve()
    try:
        cases=ordered(catalogue(configurations,data,args.build,args.replay_corpus))
        patterns=block_patterns(cases,args.block,args.filter)
        if args.list:
            chosen=selection(cases,patterns)
            for case in cases:
                if case.name not in chosen:continue
                print(case.name+(' <- '+', '.join(case.requires) if case.requires else '')+
                      (' [SKIPPED: '+case.skip+']' if case.skip else ''))
            return 0
        driver=display_driver(args.display,args.video_driver)
        chosen=selection(cases,patterns)
        needs_data=any(case.name in chosen and (case.kind in ('journey','replay') or '.Original.' in case.name) for case in cases)
        if needs_data and not (data/'E2WIN95.EXE').is_file():
            parser.error('Original game installation not found; use --game-data')
        stamp=datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S_%f')
        output=(args.output or ROOT/'.tmp/gameplay-suite'/('run_'+stamp)).resolve()
        metadata=dict(game_data=str(data),configurations=configurations,recording='off; input transitions and bounded inspection retained',
                      block=args.block,filters=args.filter,display=args.display,video_driver=driver,workers=1,
                      started_utc=datetime.now(timezone.utc).isoformat(),
                      original_sha256=digest(data/'E2WIN95.EXE') if (data/'E2WIN95.EXE').is_file() else None,
                      test_sources={path.name:digest(path) for path in [
                          ROOT/'scripts/run-e2-suite.py',ROOT/'scripts/e2_suite.py',ROOT/'scripts/e2_gameplay_steps.py',
                          ROOT/'scripts/probe-e2-player-motion.py',ROOT/'scripts/check-e2-suite.py',
                          ROOT/'scripts/check-e2-session-maintenance.py',ROOT/'src/artifacts/tests/maintenance.cpp',
                          ROOT/'src/log/src/Session/SessionRetention.cpp']},
                      revision=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True,timeout=15).strip())
        result=run_cases(cases,executor(data,driver),output,patterns,metadata)
        # Pointer only: previous run directories remain untouched.
        if args.output is None:
            (output.parent/'latest.json').write_text(json.dumps(dict(directory=str(output),exit_code=result['exit_code']),indent=2)+'\n')
        return result['exit_code']
    except (ValueError,OSError) as error:
        parser.error(str(error))


if __name__=='__main__':
    raise SystemExit(main())
