"""Explicit outcome gates over recorded routes and published observations."""
import json
import os
from pathlib import Path
import subprocess
from e2_bundle import execute
from e2_inspection import Inspection


def validate(specification):
    if not isinstance(specification, dict) or specification.get('schema') != 'e2debug.scenario.1':
        raise ValueError('Unsupported scenario schema')
    assertions, events = specification.get('assertions', []), specification.get('events', [])
    if not isinstance(assertions,list) or not isinstance(events,list) or not 0 < len(assertions)+len(events) <= 256:
        raise ValueError('Scenario requires 1..256 assertions/event selectors')
    for assertion in assertions:
        if not isinstance(assertion,dict) or not isinstance(assertion.get('scope'),str) or not isinstance(assertion.get('field'),str):
            raise ValueError('Assertion requires scope and field strings')
        if type(assertion.get('entity_id')) is not int:
            raise ValueError('Assertion requires integer entity_id')
        mode, op = assertion.get('when','eventually'), assertion.get('op','eq')
        if mode not in ('eventually','always','final','changes') or op not in ('eq','ne','ge','le'):
            raise ValueError('Invalid assertion operation')
        if mode != 'changes' and type(assertion.get('value')) is not int:
            raise ValueError('Comparison assertions require an integer value')
        if type(assertion.get('from_snapshot',1)) is not int or assertion.get('from_snapshot',1) < 1:
            raise ValueError('from_snapshot must be positive')
    for event in events:
        if not isinstance(event,dict) or not isinstance(event.get('kind'),str) or any(k not in ('kind','a','b') for k in event):
            raise ValueError('Event selector requires kind and optional a/b')
        if any(type(v) is not int for k,v in event.items() if k != 'kind'):
            raise ValueError('Event selector values must be integers')


def evaluate(capture: Inspection, specification):
    validate(specification)
    checks = []
    snapshots = sorted({e['snapshot_id'] for e in capture.events})
    for assertion in specification.get('assertions', []):
        scope, entity, field = assertion['scope'], assertion['entity_id'], assertion['field']
        mode, operation = assertion.get('when', 'eventually'), assertion.get('op', 'eq')
        if mode not in ('eventually', 'always', 'final', 'changes') or operation not in ('eq', 'ne', 'ge', 'le'):
            raise ValueError('Invalid scenario assertion operation')
        values = []
        selected = snapshots[-1:] if mode == 'final' else snapshots
        selected = [s for s in selected if s >= assertion.get('from_snapshot', 1)]
        selected = set(selected)
        for sid, state in capture.iter_states():
            if sid in selected:
                values.append(state.get((scope, entity, field)))
        if mode == 'changes':
            present = [v for v in values if v is not None]
            passed = len(set(present)) > 1
        else:
            expected = assertion['value']
            def matches(value):
                if value is None:
                    return False
                return {'eq':lambda:value == expected, 'ne':lambda:value != expected,
                        'ge':lambda:value >= expected, 'le':lambda:value <= expected}[operation]()
            results = [matches(v) for v in values]
            passed = bool(results) and (any(results) if mode == 'eventually' else all(results))
        checks.append(dict(name=assertion.get('name', f'{scope}[{entity}].{field}'),
                           passed=passed, observed_values=list(dict.fromkeys(values))))
    for required in specification.get('events', []):
        if any(k not in ('kind','a','b') for k in required):
            raise ValueError('Unsupported scenario event selector')
        checks.append(dict(name='event '+json.dumps(required),
                           passed=any(all(e[k] == v for k,v in required.items()) for e in capture.events)))
    if not checks:
        raise ValueError('Scenario must specify at least one behavioral expectation')
    return checks


def run(executable: Path, source: Path, spec: Path, destination: Path, compatible=False, timeout=120, video_driver=None):
    if spec.stat().st_size > 1024*1024:
        raise ValueError('Scenario file exceeds 1 MiB')
    specification = json.loads(spec.read_text())
    # Validate the schema before launching any native program.
    validate(specification)
    if video_driver not in (None,'dummy','x11','wayland'):
        raise ValueError('Unsupported SDL video driver')
    destination = destination.absolute()
    destination.mkdir(parents=True, exist_ok=False)
    (destination/'scenario.json').write_text(json.dumps(specification, indent=2)+'\n')
    script = Path(__file__).with_name('replay-e2.py')
    command = ['python3', str(script), 'run', str(executable.resolve(strict=True)), str(source.resolve(strict=True)),
               '--inspect', '--timeout', str(timeout), '--data-dir', str(destination/'runtime')]
    if compatible:
        command += ['--compatible']
    if video_driver:
        command += ['--video-driver', video_driver]
    result = execute(command, os.environ.copy(), timeout+5, destination/'replay.log')
    captures = sorted((destination/'runtime/logs').glob('session_*/inspection'))
    if captures:
        capture = Inspection(captures[-1])
        checks = evaluate(capture, specification)
        complete = capture.complete
    else:
        checks, complete = [], False
    report = dict(schema='e2debug.scenario-result.1', name=specification.get('name', spec.stem),
                  video_driver_override=video_driver,
                  process=result, inspection_complete=complete, checks=checks,
                  passed=result['status'] == 'exited' and result['returncode'] == 0
                  and complete and bool(checks) and all(c['passed'] for c in checks),
                  limit='Assertions describe sampled observations; native replay completion is separately required')
    (destination/'result.json').write_text(json.dumps(report, indent=2)+'\n')
    return report
