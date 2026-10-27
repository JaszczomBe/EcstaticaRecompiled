#!/usr/bin/env python3
"""Run recovered gameplay regressions in dependency order, with GoogleTest-like output."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
import sys

from e2_suite_parallel import configuration_display, run_lanes
from e2_suite import ROOT, BLOCKS, block_patterns, display_driver, catalogue, executor, ordered, run_cases, selection, digest, journey_plan, isolated_plan


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--configurations',choices=('debug','asan'),nargs='+',default=['debug','asan'])
    parser.add_argument('--build',action='store_true',help='Build each already-configured SDL Debug preset first')
    parser.add_argument('--game-data',type=Path)
    parser.add_argument('--output',type=Path,help='New directory; default .tmp/gameplay-suite/run_<UTC>')
    parser.add_argument('--block',choices=BLOCKS,default='full',help='Target block; prerequisites are included automatically')
    parser.add_argument('--filter',nargs='+',help='Glob targets within the block; prerequisites are included automatically')
    parser.add_argument('--display',choices=('headless','visible','visible-debug','visible-asan','visible-both'),default='headless',
                        help='Headless, one visible configuration, or both (visible/visible-both)')
    parser.add_argument('--workers',type=int,choices=(1,2),default=2,
                        help='Run Debug/ASan concurrently by default; one process per configuration')
    parser.add_argument('--video-driver',choices=('auto','x11','wayland'),default='auto',help='Desktop driver for visible journeys')
    parser.add_argument('--execution',choices=('shared','isolated'),default='shared',
                        help='Share checkpoint journeys by default; isolated repeats scenarios for diagnosis')
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
            units=journey_plan(cases,patterns) if args.execution=='shared' else isolated_plan(cases,patterns)
            print(f'{len(chosen)} logical cases; {sum((1 if unit.options.get('failure_case') else 2) if unit.kind=='persistence' else unit.kind=='journey' for unit in units)} gameplay processes ({args.execution})')
            for unit in units:
                if unit.checkpoints:
                    print(unit.name+' => '+', '.join(unit.checkpoints))
                    continue
                case=unit
                print(case.name+(' <- '+', '.join(case.requires) if case.requires else '')+
                      (' [SKIPPED: '+case.skip+']' if case.skip else ''))
            return 0
        chosen=selection(cases,patterns)
        has_gameplay=any(case.name in chosen and case.kind in ('journey','replay','persistence') for case in cases)
        if has_gameplay:
            has_visible=any(case.name in chosen and case.kind in ('journey','replay','persistence') and
                            configuration_display(args.display,case.configuration)=='visible' for case in cases)
            driver=display_driver('visible' if has_visible else 'headless',args.video_driver)
        else:
            driver='dummy'
            print('[ INFO     ] No gameplay executions selected: no game process or SDL window will open. '
                  '--display applies to gameplay journeys.',flush=True)
        needs_data=any(case.name in chosen and (case.kind in ('journey','replay','persistence') or '.Original.' in case.name) for case in cases)
        if needs_data and not (data/'E2WIN95.EXE').is_file():
            parser.error('Original game installation not found; use --game-data')
        stamp=datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S_%f')
        output=(args.output or ROOT/'.tmp/gameplay-suite'/('run_'+stamp)).resolve()
        active_configurations=list(dict.fromkeys(case.configuration for case in cases if case.name in chosen and case.configuration))
        drivers={configuration:driver if configuration_display(args.display,configuration)=='visible' else 'dummy'
                 for configuration in active_configurations}
        workers=min(args.workers,max(1,len(active_configurations)))
        metadata=dict(game_data=str(data),configurations=configurations,recording='off; input transitions and bounded inspection retained',
                      execution=args.execution,block=args.block,filters=args.filter,display=args.display,video_driver=driver,workers=workers,
                      display_by_configuration={c:configuration_display(args.display,c) for c in active_configurations},
                      gameplay_selected=has_gameplay,
                      started_utc=datetime.now(timezone.utc).isoformat(),
                      original_sha256=digest(data/'E2WIN95.EXE') if (data/'E2WIN95.EXE').is_file() else None,
                      test_sources={path.name:digest(path) for path in [
                          ROOT/'scripts/run-e2-suite.py',ROOT/'scripts/e2_suite.py',ROOT/'scripts/e2_gameplay_steps.py',
                          ROOT/'scripts/probe-e2-player-motion.py',ROOT/'scripts/check-e2-suite.py',
                          ROOT/'scripts/e2_menu_steps.py',ROOT/'scripts/e2_suite_parallel.py',
                          ROOT/'scripts/probe-e2-game-save-load.py',ROOT/'scripts/e2_save_load_steps.py',
                          *sorted((ROOT/'scripts').glob('check-e2-save-*.py')),
                          ROOT/'E2Recomp/platform/e2recomp_win32_compat.c',
                          ROOT/'E2Recomp/native/e2recomp_native_main.c',
                          ROOT/'scripts/e2_population_profile.py',ROOT/'scripts/e2_startup_steps.py',
                          ROOT/'scripts/e2_navigation.py',ROOT/'scripts/check-e2-navigation.py',
                          ROOT/'scripts/e2_scene_navigation.py',
                          ROOT/'scripts/e2_probe_diagnostics.py',
                          ROOT/'scripts/replay-e2.py',ROOT/'scripts/e2_scenarios.py',ROOT/'scripts/e2-debug.py',
                          ROOT/'scripts/e2_bundle.py',ROOT/'scripts/e2_inspection.py',ROOT/'scripts/scenarios/intro-menu.json',
                          ROOT/'scripts/check-e2-test-population.py',ROOT/'scripts/check-e2-npc-spawn.py',
                          ROOT/'scripts/check-e2-menu-contracts.py',
                          ROOT/'scripts/check-e2-menu-layout.py',
                          ROOT/'scripts/check-e2-ddraw-surfaces.py',
                          ROOT/'scripts/check-e2-action-pose-events.py',
                          ROOT/'scripts/check-e2-bitmap-records.py',
                          ROOT/'E2Recomp/reconstructed/E2Recomp_recon.c',
                          ROOT/'E2Recomp/reconstructed/E2Recomp_stubs.c',
                          ROOT/'E2Recomp/tools/GenerateRecon.js',
                          ROOT/'E2Recomp/platform/e2recomp_test_population.h',
                          ROOT/'scripts/scenarios/courtyard-waypoints.json',ROOT/'scripts/scenarios/water-waypoints.json',
                          ROOT/'scripts/check-e2-session-maintenance.py',ROOT/'src/artifacts/tests/maintenance.cpp',
                          ROOT/'src/log/src/Session/SessionRetention.cpp']},
                      revision=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True,timeout=15).strip())
        if workers>1:
            def command(lane,names,destination):
                child=[sys.executable,str(ROOT/'scripts/run-e2-suite.py'),'--workers','1',
                       '--configurations',lane if lane!='shared' else configurations[0],
                       '--game-data',str(data),'--execution',args.execution,
                       '--display',configuration_display(args.display,lane) if lane!='shared' else 'headless',
                       '--video-driver',args.video_driver,'--output',str(destination),'--filter',*names]
                if args.build:child.append('--build')
                if args.replay_corpus:child+=['--replay-corpus',str(args.replay_corpus.resolve())]
                return child
            result=run_lanes(cases,patterns,output,metadata,command,shared=args.execution=='shared',workers=workers)
        else:
            executors={c:executor(data,drivers[c]) for c in active_configurations}
            source_executor=executor(data,'dummy')
            def perform(case,destination,results):
                return executors.get(case.configuration,source_executor)(case,destination,results)
            result=run_cases(cases,perform,output,patterns,metadata,shared=args.execution=='shared')
        # Pointer only: previous run directories remain untouched.
        if args.output is None:
            (output.parent/'latest.json').write_text(json.dumps(dict(directory=str(output),exit_code=result['exit_code']),indent=2)+'\n')
        return result['exit_code']
    except (ValueError,OSError) as error:
        parser.error(str(error))


if __name__=='__main__':
    raise SystemExit(main())
