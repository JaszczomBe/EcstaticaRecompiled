"""Two independent configuration processes with merged incremental suite reports.

A configuration remains sequential. Each child uses the existing checkpoint
runner, isolated artifacts and process-tree cleanup; source/tool cases run once.
"""
import copy
import json
from pathlib import Path
import signal
import subprocess
import time

from e2_suite import isolated_plan, journey_plan, ordered, selection, shared_results, stop_process, write_reports


def configuration_display(display, configuration):
    if display=='headless':return 'headless'
    if display in ('visible','visible-both'):return 'visible'
    return 'visible' if display=='visible-'+configuration else 'headless'


def prefix_evidence(row, lane):
    result=copy.deepcopy(row)
    for key in ('artifacts','evidence'):
        if isinstance(result.get(key),str) and not Path(result[key]).is_absolute():
            result[key]=lane+'/'+result[key]
    return result


def run_lanes(cases, patterns, destination, metadata, command_builder, shared=True, workers=2):
    """Run at most one child per configuration, recovering partial checkpoints.

    command_builder(lane, logical_names, output_directory) returns explicit argv.
    Cross-configuration prerequisites are rejected rather than silently bypassed.
    """
    cases=ordered(cases);selected=selection(cases,patterns)
    selected_cases=[case for case in cases if case.name in selected]
    by_name={case.name:case for case in cases}
    groups={}
    for case in selected_cases:
        lane=case.configuration or 'shared'
        groups.setdefault(lane,[]).append(case.name)
        for dependency in (*case.requires,*case.observes):
            if by_name[dependency].configuration!=case.configuration:
                raise ValueError('Parallel lanes require configuration-local prerequisites: '+case.name)
    destination.mkdir(parents=True,exist_ok=False)
    plans={lane:journey_plan(cases,names) if shared else isolated_plan(cases,names)
           for lane,names in groups.items()}
    report=dict(schema='e2suite.result.2',state='running',metadata=metadata,results=[],journeys=[],lanes=[],seconds=0,
                planned_executions=sum(len(plan) for plan in plans.values()),
                planned_gameplay_processes=sum(unit.kind=='journey' for plan in plans.values() for unit in plan))
    started=time.monotonic();interrupted=False;states={};previous=None;coordinator_error=None
    print(f'[==========] Running {len(selected)} selected cases in {report["planned_executions"]} execution units; '
          f'{workers} configuration workers, sequential within each configuration.',flush=True)

    def spawn(lane):
        command=command_builder(lane,groups[lane],destination/lane)
        (destination/(lane+'.runner-command.json')).write_text(json.dumps(command,indent=2)+'\n')
        log=destination/(lane+'.runner.log')
        output=log.open('wb')
        try:process=subprocess.Popen(command,stdout=output,stderr=subprocess.STDOUT,start_new_session=True)
        except BaseException:
            output.close();raise
        states[lane]=dict(process=process,output=output,reader=log.open(errors='replace'),pending='',
                          start=time.monotonic(),end=None)

    def output_lines(lane):
        state=states[lane];state['pending']+=state['reader'].read()
        while '\n' in state['pending']:
            line,state['pending']=state['pending'].split('\n',1)
            if line.startswith(('[==========]','[ JOURNEYS ]','Reports:')):continue
            if any(line.strip().startswith('[ '+status) and line.strip().split('] ',1)[-1].isdigit()
                   for status in ('PASS','FAIL','BLOCKED','SKIPPED')):continue
            if '[ PHASE ' in line:line='  ['+lane+'] '+line.strip()
            print(line,flush=True)

    def read_child(lane):
        path=destination/lane/'report.json'
        if not path.is_file():return None
        try:return json.loads(path.read_text())
        except (OSError,ValueError):return None

    def merge(final=False):
        nonlocal previous
        found={};journeys=[];lanes=[]
        for lane,names in groups.items():
            state=states.get(lane);child=read_child(lane) if state else None
            if child:
                for row in child.get('results',[]):found[row['name']]=prefix_evidence(row,lane)
                journeys.extend(prefix_evidence(row,lane) for row in child.get('journeys',[]))
            process=state['process'] if state else None
            code=process.poll() if process else None
            if state and code is not None and state['end'] is None:state['end']=time.monotonic()
            lanes.append(dict(name=lane,results=lane+'/report.json',returncode=code,
                              start_seconds=state['start']-started if state else None,
                              end_seconds=state['end']-started if state and state['end'] else None))
            finished=bool(process and code is not None)
            valid=bool(child and child.get('state') in ('complete','interrupted') and code==child.get('exit_code'))
            if finished and not valid:
                worker=lane+'.Runner';reason='Configuration worker exited without a matching completed report (exit '+str(code)+')'
                journeys.append(dict(name=worker,status='FAIL',reason=reason,configuration=None if lane=='shared' else lane,
                    checkpoints=[],seconds=state['end']-state['start'],evidence=lane+'.runner.log'))
                # If the Python worker died, its atomic GDB journal is still
                # usable evidence. Never turn completed assertions into skips.
                for unit in plans[lane]:
                    missing=[name for name in unit.checkpoints if name not in found]
                    path=destination/lane/unit.name/'probe-journey.json'
                    if missing and path.is_file():
                        try:progress=json.loads(path.read_text())
                        except (OSError,ValueError):continue
                        outcome=dict(status='FAIL',reason=reason,progress=progress)
                        for row in shared_results(unit,outcome,by_name):
                            if row['name'] in missing:found[row['name']]=prefix_evidence(row,lane)
            if final or finished:
                for name in names:
                    if name in found:continue
                    case=by_name[name]
                    status='SKIPPED' if case.skip or interrupted else 'BLOCKED'
                    found[name]=dict(name=name,required=case.required,requires=list(case.requires),
                        observes=list(case.observes),status=status,seconds=0,
                        reason=case.skip or ('Suite interrupted' if interrupted else 'Configuration worker did not exercise this check'),
                        evidence=lane+'.runner.log',root_causes=[lane+'.Runner'])
        report.update(results=[found[case.name] for case in selected_cases if case.name in found],journeys=journeys,
                      lanes=lanes,seconds=time.monotonic()-started)
        if coordinator_error:
            report['journeys'].append(dict(name='Suite.Coordinator',status='FAIL',reason=coordinator_error,
                                          checkpoints=[],seconds=time.monotonic()-started,evidence='report.json'))
        # Reports change only when child results/worker state change, not on
        # every poll; the parent is the sole writer of the merged files.
        identity=json.dumps(dict(results=report['results'],journeys=journeys,lanes=lanes),sort_keys=True)
        if final or identity!=previous:
            write_reports(destination,report);previous=identity

    def wait_for(lanes):
        while any(states[lane]['process'].poll() is None for lane in lanes):
            for lane in lanes:output_lines(lane)
            merge()
            time.sleep(.1)
        for lane in lanes:output_lines(lane)
        merge()

    try:
        if 'shared' in groups:
            spawn('shared');wait_for(['shared'])
        pending=[lane for lane in groups if lane!='shared']
        while pending:
            batch=pending[:workers];pending=pending[workers:]
            for lane in batch:spawn(lane)
            wait_for(batch)
    except KeyboardInterrupt:
        interrupted=True
        for state in states.values():
            if state['process'].poll() is None:state['process'].send_signal(signal.SIGINT)
        deadline=time.monotonic()+20
        while any(state['process'].poll() is None for state in states.values()) and time.monotonic()<deadline:
            for lane in states:output_lines(lane)
            merge();time.sleep(.1)
        for state in states.values():
            if state['process'].poll() is None:stop_process(state['process'])
    except Exception as error:
        coordinator_error=f'{type(error).__name__}: {error}'
        print('[ FAIL     ] Suite.Coordinator — '+coordinator_error,flush=True)
    finally:
        # An exception in the coordinator must not leave another lane alive.
        for state in states.values():
            if state['process'].poll() is None:stop_process(state['process'])
        for lane in states:output_lines(lane)
        for state in states.values():
            state['output'].close();state['reader'].close()
    merge(final=True)
    counts={status:sum(row['status']==status for row in report['results']) for status in ('PASS','FAIL','BLOCKED','SKIPPED')}
    interrupted=interrupted or any(row.get('returncode')==130 for row in report['lanes'])
    failed=counts['FAIL'] or counts['BLOCKED'] or any(row['status']=='FAIL' for row in report['journeys'])
    code=130 if interrupted else 1 if failed else 2 if any(row['required'] and row['status']=='SKIPPED' for row in report['results']) else 0
    report.update(state='interrupted' if interrupted else 'complete',counts=counts,exit_code=code,seconds=time.monotonic()-started)
    write_reports(destination,report)
    print(f"[==========] {len(report['results'])} cases ({report['seconds']:.2f}s)",flush=True)
    for status,count in counts.items():print(f'[ {status:<8} ] {count}',flush=True)
    print(f"[ JOURNEYS ] {sum(row['status']=='FAIL' for row in report['journeys'])} failed; exit {code}",flush=True)
    print('Reports: '+str(destination/'report.html')+' (JSON and JUnit XML alongside)',flush=True)
    return report
