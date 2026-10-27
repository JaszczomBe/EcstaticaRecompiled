#!/usr/bin/env python3
"""Inspect captured state, reproduce native failures and query recovery evidence."""
import argparse
import json
import subprocess
from pathlib import Path
from e2_inspection import Inspection, differences, write_report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    timeline = sub.add_parser('timeline')
    timeline.add_argument('source', type=Path)
    timeline.add_argument('--kind')
    timeline.add_argument('--limit', type=int, default=50)
    timeline.add_argument('--after', type=int, default=0)
    state = sub.add_parser('state')
    state.add_argument('source', type=Path)
    state.add_argument('--snapshot', type=int)
    state.add_argument('--scope')
    state.add_argument('--actor', type=int)
    diff = sub.add_parser('diff')
    diff.add_argument('source', type=Path)
    diff.add_argument('before', type=int)
    diff.add_argument('after', type=int)
    diff.add_argument('--other', type=Path, help='Compare the second snapshot from another capture')
    report = sub.add_parser('report')
    report.add_argument('source', type=Path)
    report.add_argument('destination', type=Path)
    bundle = sub.add_parser('bundle', help='Freeze an inactive session with its matching binary')
    bundle.add_argument('source', type=Path)
    bundle.add_argument('executable', type=Path)
    bundle.add_argument('destination', type=Path)
    verify = sub.add_parser('verify', help='Verify every immutable bundle file')
    verify.add_argument('source', type=Path)
    run = sub.add_parser('capture', help='Record a bounded normal run and automatically export its evidence')
    run.add_argument('executable', type=Path)
    run.add_argument('destination', type=Path)
    run.add_argument('--timeout', type=float, default=90)
    run.add_argument('--game-data', type=Path)
    run.add_argument('--dummy', action='store_true')
    run.add_argument('--gdb', action='store_true', help='Capture native stopped-thread stacks and registers')
    sub.add_parser('capabilities', help='Report available reverse-debugging backends')
    reverse = sub.add_parser('reverse', help='Prepare a GDB recording window or run an rr pilot')
    reverse.add_argument('source', type=Path, help='Verified bug bundle')
    reverse.add_argument('destination', type=Path)
    reverse.add_argument('--backend', choices=('gdb','rr'), default='gdb')
    reverse.add_argument('--function')
    reverse.add_argument('--ignore', type=int, default=0)
    reverse.add_argument('--timeout', type=float, default=120)
    scenario = sub.add_parser('scenario', help='Run a recorded route with explicit behavioral expectations')
    scenario.add_argument('executable', type=Path)
    scenario.add_argument('source', type=Path)
    scenario.add_argument('specification', type=Path)
    scenario.add_argument('destination', type=Path)
    scenario.add_argument('--compatible', action='store_true')
    scenario.add_argument('--timeout', type=float, default=120)
    scenario.add_argument('--video-driver', choices=('dummy','x11','wayland'), help='Override the recorded SDL video driver')
    recovery = sub.add_parser('recovery', help='Find original addresses, signatures, fixtures, journals and risk hints')
    recovery.add_argument('--function', help='Address or function name')
    recovery.add_argument('--limit', type=int, default=20)
    diagnostics = sub.add_parser('diagnostics', help='Analyze current C without changing normal compiler flags')
    diagnostics.add_argument('build', type=Path)
    diagnostics.add_argument('--function')
    diagnostics.add_argument('--limit', type=int, default=50)
    args = parser.parse_args()
    try:
        if args.command == 'diagnostics':
            from e2_diagnostics import diagnose
            if not 1 <= args.limit <= 1000:
                parser.error('--limit must be 1..1000')
            print(json.dumps(diagnose(args.build, args.function, args.limit), indent=2))
            return
        if args.command == 'scenario':
            from e2_scenarios import run
            result = run(args.executable, args.source, args.specification, args.destination, args.compatible, args.timeout, args.video_driver)
            print(json.dumps(result, indent=2))
            if not result['passed']:
                raise SystemExit(1)
            return
        if args.command == 'recovery':
            from e2_recovery import index
            result = index()
            if args.function:
                address = args.function.lower().removeprefix('fun_').removeprefix('0x').zfill(8)
                result['functions'] = [f for f in result['functions'] if f['address'] == '0x'+address]
            if not 1 <= args.limit <= 1000:
                parser.error('--limit must be 1..1000')
            result['functions'] = result['functions'][:args.limit]
            print(json.dumps(result, indent=2))
            return
        if args.command in ('bundle', 'verify', 'capture', 'capabilities', 'reverse'):
            from e2_bundle import publish, verify as verify_bundle, capture as capture_run
            from e2_reverse import capabilities, prepare, pilot
            if args.command == 'bundle':
                result = publish(args.destination, args.executable, args.source)
            elif args.command == 'verify':
                result = verify_bundle(args.source)
            elif args.command == 'capture':
                result = capture_run(args.executable, args.destination, timeout=args.timeout,
                                     game_data=args.game_data, dummy=args.dummy, gdb=args.gdb)
            elif args.command == 'capabilities':
                result = capabilities()
            elif args.backend == 'rr':
                result = pilot(args.source, args.destination, args.timeout)
            else:
                if not args.function:
                    parser.error('--function is required for a GDB recording window')
                result = prepare(args.source, args.destination, args.function, args.ignore)
            print(json.dumps(result, indent=2))
            return
        capture = Inspection(args.source)
        if args.command == 'timeline':
            if not 1 <= args.limit <= 10000 or args.after < 0:
                parser.error('--limit must be 1..10000; --after must be nonnegative')
            result = dict(complete=capture.complete, events=capture.timeline(args.kind, args.limit, args.after))
        elif args.command == 'state':
            result = capture.state(args.snapshot, 'actor' if args.actor is not None else args.scope, args.actor)
        elif args.command == 'diff':
            other = Inspection(args.other) if args.other else capture
            result = differences(capture.state(args.before), other.state(args.after))
        else:
            write_report(capture, args.destination)
            result = dict(report=str(args.destination.absolute()), complete=capture.complete)
        print(json.dumps(result, indent=2))
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        parser.exit(1, f'{error}\n')


if __name__ == '__main__':
    main()
