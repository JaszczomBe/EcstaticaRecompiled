"""Dependency-aware Ecstatica regression catalogue, execution and reports."""
from __future__ import annotations

from dataclasses import dataclass, field, replace
import fnmatch
import hashlib
import html
import json
import os
import re
from pathlib import Path
import signal
import subprocess
import sys
import time
import xml.etree.ElementTree as ET

from e2_population_profile import profile_for

ROOT = Path(__file__).resolve().parent.parent

# Blocks select targets; selection() always adds their transitive prerequisites.
BLOCKS = {
    'full': ('*',),
    'checks': ('Source.*','Tools.*','*.Original.*','*.Host.*'),
    'startup': ('*.Startup.*',),
    'movement': ('*.Movement.ControlsAndRelease','*.Traversal.CourtyardReturn'),
    'unarmed': ('*.Combat.Unarmed*','*.Combat.TakeDamage'),
    'workshop': ('*.Traversal.Workshop','*.Interaction.SwordPickup','*.Combat.FourDirections',
                 '*.Combat.KillSmith','*.Interaction.DoorPassage','*.Interaction.DoorPassageDisplaced'),
    'potions': ('*.Potion.*','*.Interaction.PotionThenSword'),
    'swimming': ('*.Movement.Swimming','*.Traversal.Water','*.Combat.SwimmingDirections',
                 '*.Movement.ArmedSwimming','*.Combat.ArmedSwimmingDirections','*.Traversal.ArmedWater','*.Movement.ShoreExit'),
    'menus': ('*.Menus.*',),
    'persistence': ('*.Persistence.*',),
    'stability': ('*.Stability.*',),
    'replay': ('*.Replay.*',),
}


def block_patterns(cases, block, filters=None):
    targets=[case.name for case in cases if any(fnmatch.fnmatchcase(case.name,p) for p in BLOCKS[block])]
    if filters:
        targets=[name for name in targets if any(fnmatch.fnmatchcase(name,p) for p in filters)]
    if not targets:raise ValueError('No cases match the selected block/filter')
    return targets


def display_driver(display, driver='auto', environment=None):
    environment=os.environ if environment is None else environment
    if display=='headless':return 'dummy'
    if driver=='auto':
        driver='wayland' if environment.get('WAYLAND_DISPLAY') else 'x11'
    variable='WAYLAND_DISPLAY' if driver=='wayland' else 'DISPLAY'
    if not environment.get(variable):
        raise ValueError('Visible SDL requires '+variable+'; run from the desktop or select headless')
    return driver


@dataclass
class Case:
    name: str
    command: tuple[str, ...] = ()
    requires: tuple[str, ...] = ()
    timeout: float = 120
    kind: str = 'command'
    scenario: str | None = None
    configuration: str | None = None
    required: bool = True
    skip: str | None = None
    options: dict = field(default_factory=dict)
    observes: tuple[str, ...] = ()
    checkpoints: tuple[str, ...] = ()
    population_profile: str | None = None


def journey_population(case):
    return case.population_profile or profile_for(case.scenario,case.options.get("checks",[]))


def ordered(cases):
    by_name = {case.name: case for case in cases}
    if len(by_name) != len(cases):
        raise ValueError('Duplicate suite case identity')
    result, visiting, visited = [], set(), set()
    def visit(name):
        if name not in by_name:
            raise ValueError('Unknown dependency: '+name)
        if name in visiting:
            raise ValueError('Dependency cycle: '+name)
        if name in visited:
            return
        visiting.add(name)
        for dependency in (*by_name[name].requires,*by_name[name].observes):
            visit(dependency)
        visiting.remove(name)
        visited.add(name)
        result.append(by_name[name])
    for case in cases:
        visit(case.name)
    return result


def selection(cases, patterns):
    selected = {case.name for case in cases if any(fnmatch.fnmatchcase(case.name,p) for p in patterns)}
    if not selected:
        raise ValueError('No suite cases match the filter')
    by_name = {case.name: case for case in cases}
    def add(name):
        for dependency in (*by_name[name].requires,*by_name[name].observes):
            if dependency not in selected:
                selected.add(dependency)
                add(dependency)
    for name in tuple(selected):
        add(name)
    return selected


MENU_STAGES = ('Intro','Pedestal','Gameplay')
MENU_ACTIONS = ('ShowHide','Settings','MusicToggle','SoundToggle','Difficulty','ResolutionToggle','LoadDialog','SaveDialog')
MENU_CHECKS = tuple('Menus.'+stage+'.'+action for stage in MENU_STAGES for action in (*MENU_ACTIONS,'StartGame')) + (
    'Menus.CancelResumeQuit',)
MENU_UNFINISHED = {
    'MusicPlayback': 'Audible MIDI playback is not implemented; a control toggle is not audio acceptance',
    'SoundPlayback': 'Audible sound-effect output lacks implemented/accepted backend coverage',
    'ResolutionRendering': 'Resolution resource reload and rendered dimensions lack accepted end-to-end coverage',
    'LoadState': 'Functional saved-game loading and restored scene/actor state are unproven',
    'SaveState': 'Functional game-state serialization/round-trip is unproven; quick-save is a no-op',
    'Subtitles': 'Subtitle visibility/content has no accepted rendered assertion or exposed settings item',
    'FemaleStartGame': 'Female start path has no accepted restart/state assertions',
}


# Compatible routes are explicit; dependencies alone never establish coverage.
# The longest useful route owns each selected checkpoint once. Other routes only
# repeat the input setup needed to reach their distinct state, not smoke checks.
SHARED_ROUTES = {
    'DelayedSkip': ('Startup.DelayedSkip','Menus.CancelResumeQuit'),
    'Controls': ('Startup.DelayedSkip','Movement.ControlsAndRelease','Combat.UnarmedDirections','Menus.CancelResumeQuit'),
    # Live unarmed contact can alter the later destructible-door setup. Keep
    # its own declared route; every journey still performs its real setup.
    'Workshop': ('Startup.DelayedSkip','Movement.ControlsAndRelease',
                 'Traversal.Workshop','Interaction.SwordPickup','Combat.FourDirections',
                 'Combat.KillSmith','Interaction.DoorPassage','Stability.MixedJourney','Menus.CancelResumeQuit'),
    # A fresh intact door is necessary for the deliberately distant approach.
    'DisplacedDoor': ('Interaction.DoorPassageDisplaced','Menus.CancelResumeQuit'),
    'UnarmedContact': ('Startup.DelayedSkip','Movement.ControlsAndRelease','Combat.UnarmedDirections',
                      'Traversal.Workshop','Combat.UnarmedContact','Menus.CancelResumeQuit'),
    'Courtyard': ('Startup.DelayedSkip','Movement.ControlsAndRelease','Traversal.CourtyardReturn','Menus.CancelResumeQuit'),
    'Swimming': ('Startup.DelayedSkip','Movement.ControlsAndRelease','Movement.Swimming','Combat.SwimmingDirections',
                 'Traversal.Water','Menus.CancelResumeQuit'),
    'ArmedSwimming': ('Startup.DelayedSkip','Movement.ControlsAndRelease','Traversal.Workshop','Interaction.SwordPickup',
                      'Movement.ArmedSwimming','Combat.ArmedSwimmingDirections','Traversal.ArmedWater','Menus.CancelResumeQuit'),
    'Damage': ('Startup.DelayedSkip','Movement.ControlsAndRelease','Combat.TakeDamage','Menus.CancelResumeQuit'),
    'PotionA': ('Startup.DelayedSkip','Movement.ControlsAndRelease','Potion.TrialA','Interaction.PotionThenSword','Menus.CancelResumeQuit'),
    'PotionB': ('Startup.DelayedSkip','Movement.ControlsAndRelease','Potion.TrialB','Menus.CancelResumeQuit'),
    'PotionC': ('Startup.DelayedSkip','Movement.ControlsAndRelease','Combat.TakeDamage','Potion.TrialC','Menus.CancelResumeQuit'),
    'PotionD': ('Startup.DelayedSkip','Movement.ControlsAndRelease','Combat.TakeDamage','Potion.TrialD','Menus.CancelResumeQuit'),
    'EarlySkip': ('Startup.EarlySkip','Menus.CancelResumeQuit'),
    'Natural': ('Startup.Natural','Menus.CancelResumeQuit'),
}


def journey_plan(cases, patterns=('*',)):
    """Greedily cover explicit compatible paths, then order external prerequisites.

    This small fixed catalogue needs no general state planner. Ties prefer fewer
    route steps, then declaration order. Steps not assigned are setup-only and
    cannot receive a logical PASS. --execution isolated bypasses this function.
    """
    cases=ordered(cases)
    selected=selection(cases,patterns)
    by_name={case.name:case for case in cases}
    remaining={name for name in selected if by_name[name].kind=='journey'}
    units=[case for case in cases if case.name in selected and case.kind!='journey']
    # Menu stage transitions/restarts have their own one-process route. Assign
    # it before core gameplay so a failed restart cannot erase earlier startup.
    for configuration in dict.fromkeys(case.configuration for case in cases if case.kind=='journey'):
        prefix=configuration+'.'
        menu=tuple(prefix+name for name in ('Startup.DelayedSkip',*MENU_CHECKS) if prefix+name in remaining)
        if any(by_name[name].scenario=='menu-matrix' for name in menu):
            # Other live routes already need their own startup. Let one own
            # that assertion so an intro-menu fault cannot block unrelated
            # gameplay solely because its startup evidence lived in the menu.
            if any(name.startswith(prefix) and name not in menu for name in remaining):
                menu=tuple(name for name in menu if name!=prefix+'Startup.DelayedSkip')
            units.append(Case(prefix+'Journey.MenuStages',kind='journey',scenario='menu-matrix',
                configuration=configuration,checkpoints=menu,timeout=360,population_profile='noncombat-opening',
                options=dict(checks=[name[len(prefix):] for name in menu])))
            remaining.difference_update(menu)
    for configuration in dict.fromkeys(case.configuration for case in cases if case.kind=='journey'):
        prefix=configuration+'.'
        while any(name.startswith(prefix) for name in remaining):
            candidates=[]
            for route,checks in SHARED_ROUTES.items():
                covered=tuple(prefix+check for check in checks if prefix+check in remaining)
                if covered:candidates.append((route,checks,covered))
            if not candidates:raise ValueError('Selected gameplay case has no declared journey coverage')
            # Assign the shared workshop prerequisites before fresh potion trials.
            # Otherwise a trial could own movement while awaiting a workshop
            # journey that itself depends on that movement checkpoint.
            if prefix+'Traversal.Workshop' in remaining:
                candidates=[item for item in candidates if 'Traversal.Workshop' in item[1]]
            route,checks,covered=max(candidates,key=lambda item:(len(item[2]),-len(item[1])))
            options=dict(checks=[name[len(prefix):] for name in covered])
            for name in covered:
                options.update({key:value for key,value in by_name[name].options.items() if key!='intro'})
            intro='early' if route=='EarlySkip' else 'natural' if route=='Natural' else 'delayed'
            options['intro']=intro
            if route=='Workshop' and any(name.endswith(('Interaction.DoorPassage','Stability.MixedJourney')) for name in covered):
                options['observe_door_health']=True
            # Observation is part of the stability checkpoint, before menu exit.
            if 'observe' in options:options['observe_seconds']=options.pop('observe')
            units.append(Case(prefix+'Journey.'+route,kind='journey',scenario='shared',configuration=configuration,
                              checkpoints=covered,options=options,population_profile=profile_for('shared',options['checks']),timeout=max(by_name[name].timeout for name in covered)))
            remaining.difference_update(covered)
    owner={name:unit.name for unit in units for name in (unit.checkpoints or (unit.name,))}
    graph=[]
    for unit in units:
        dependencies=[]
        for name in unit.checkpoints or (unit.name,):
            for dependency in (*by_name[name].requires,*by_name[name].observes):
                if owner[dependency]!=unit.name and owner[dependency] not in dependencies:
                    dependencies.append(owner[dependency])
        # Project only for sorting; runtime still evaluates logical prerequisites.
        graph.append(Case(unit.name,requires=tuple(dependencies)))
    unit_by_name={unit.name:unit for unit in units}
    return [unit_by_name[node.name] for node in ordered(graph)]


def digest(path):
    value = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda:stream.read(1024*1024), b''):
            value.update(block)
    return value.hexdigest()


def isolated_plan(cases, patterns=('*',)):
    selected=selection(cases,patterns)
    # One logical menu check per process, with an independent lifecycle gate.
    return [replace(unit,name=unit.configuration+'.Journey.Isolated.'+unit.name.split('.',1)[1],
                    checkpoints=(unit.name,),options=unit.options|dict(checks=[unit.name.split('.',1)[1]]))
            if unit.scenario=='menu-matrix' else unit for unit in ordered(cases) if unit.name in selected]


def stop_process(process):
    # Include descendants that GDB may have put into a separate process group.
    def children(pid):
        try:
            ids=Path(f'/proc/{pid}/task/{pid}/children').read_text().split()
        except OSError:
            return []
        result=[]
        for child in ids:
            result += children(int(child))+[int(child)]
        return result
    descendants=children(process.pid)
    for number in (signal.SIGTERM,signal.SIGKILL):
        for pid in descendants:
            try: os.kill(pid,number)
            except ProcessLookupError: pass
        try: os.killpg(process.pid,number)
        except ProcessLookupError: pass
        try:
            process.wait(timeout=2)
        except subprocess.TimeoutExpired:
            continue
    process.wait(timeout=5)


def execute(command, directory, timeout, environment=None, phase_path=None):
    directory.mkdir(parents=True,exist_ok=True)
    (directory/'command.json').write_text(json.dumps(list(command),indent=2)+'\n')
    start=time.monotonic()
    with (directory/'console.log').open('wb') as log:
        process=subprocess.Popen(command,cwd=ROOT,env=environment,start_new_session=True,
                                 stdout=log,stderr=subprocess.STDOUT)
        previous=None
        try:
            while process.poll() is None:
                if time.monotonic()-start>timeout:
                    stop_process(process)
                    return dict(status='FAIL',reason=f'Host timeout after {timeout:g}s',timeout=True)
                if phase_path and phase_path.is_file():
                    try:
                        phases=json.loads(phase_path.read_text()).get('phases',[])
                        current=phases[-1]['name'] if phases else None
                        if current and current!=previous:
                            print('  [ PHASE    ] '+current,flush=True)
                            previous=current
                    except (OSError,ValueError,KeyError):
                        pass
                time.sleep(.1)
        except BaseException:
            stop_process(process)
            raise
    output=(directory/'console.log').read_text(errors='replace')
    if process.returncode or 'ERROR: AddressSanitizer' in output or 'SUMMARY: AddressSanitizer' in output:
        reason='Process exit '+str(process.returncode)
        lines=output.strip().splitlines()
        useful=[line for line in lines if line.startswith('FAIL:') or ('Assertion' in line and 'failed' in line) or 'ERROR: AddressSanitizer' in line]
        if useful:reason+=': '+useful[0][:500]
        elif lines:reason+=': '+lines[-1][:500]
        return dict(status='FAIL',reason=reason,returncode=process.returncode)
    return dict(status='PASS',reason='',returncode=0)


def write_reports(destination, report):
    data=json.dumps(report,indent=2)+'\n'
    temporary=destination/'report.json.tmp'
    temporary.write_text(data)
    temporary.replace(destination/'report.json')
    counts={key:sum(r['status']==key for r in report['results']) for key in ('PASS','FAIL','BLOCKED','SKIPPED')}
    lifecycles=[dict(row,required=True) for row in report.get('journeys',[]) if row['status']=='FAIL']
    suite=ET.Element('testsuite',name='Ecstatica II',tests=str(len(report['results'])+len(lifecycles)),
                     failures=str(counts['FAIL']+len(lifecycles)),skipped=str(counts['BLOCKED']+counts['SKIPPED']),
                     time=f"{report.get('seconds',0):.3f}")
    rows=[]
    for result in [*report['results'],*lifecycles]:
        case=ET.SubElement(suite,'testcase',name=result['name'],classname='Ecstatica',
                           time=f"{result.get('seconds',0):.3f}")
        props=ET.SubElement(case,'properties')
        ET.SubElement(props,'property',name='status',value=result['status'])
        for key in ('journey','checkpoint','evidence','population_profile'):
            if isinstance(result.get(key),str):ET.SubElement(props,'property',name=key,value=result[key])
        if result['status']=='FAIL':
            ET.SubElement(case,'failure',message=result['reason']).text=result['reason']
        elif result['status'] in ('BLOCKED','SKIPPED'):
            ET.SubElement(case,'skipped',type=result['status'].lower(),message=result['reason'])
        name=html.escape(result['name']);reason=html.escape(result.get('reason',''))
        artifact=result.get('artifacts')
        link=f'<a href="{html.escape(artifact,quote=True)}/console.log">log</a>' if artifact else ''
        if result.get('evidence'):
            link+=f' · <a href="{html.escape(result["evidence"],quote=True)}">checkpoints</a>'
        coverage=html.escape(result.get('journey',''))+' / '+html.escape(result.get('checkpoint','')) if isinstance(result.get('journey'),str) else ''
        if result.get('population_profile'):coverage+=' · '+html.escape(result['population_profile'])
        rows.append(f'<tr><td>{name}</td><td class="{result["status"]}">{result["status"]}</td>'
                    f'<td>{result.get("seconds",0):.2f}s</td><td>{reason}</td><td>{coverage}</td><td>{link}</td></tr>')
    ET.indent(suite)
    ET.ElementTree(suite).write(destination/'report.xml',encoding='utf-8',xml_declaration=True)
    document='''<!doctype html><meta charset="utf-8"><title>Ecstatica II regression suite</title>
<style>body{font:16px system-ui;margin:2rem;background:#171b22;color:#e9edf3}table{border-collapse:collapse;width:100%}td,th{text-align:left;padding:.6rem;border-bottom:1px solid #444}.PASS{color:#83d997}.FAIL{color:#ff8a8a}.BLOCKED{color:#ffd175}.SKIPPED{color:#b0b8c7}a{color:#8ecbff}</style>
<h1>Ecstatica II regression suite</h1>'''
    journey_failures=sum(row['status']=='FAIL' for row in report.get('journeys',[]))
    document+=f'<p>{html.escape(report.get("state","running"))} · '+html.escape(str(counts))+f' · {journey_failures} failed journeys</p>'
    document+='<table><tr><th>Scenario</th><th>Status</th><th>Time</th><th>Reason</th><th>Journey / checkpoint</th><th>Evidence</th></tr>'+''.join(rows)+'</table>'
    (destination/'report.html').write_text(document)


def shared_results(unit, outcome, cases):
    """Credit only explicit, completed checkpoints in the retained journal."""
    rows={row['name']:row for row in outcome.get('progress',{}).get('checkpoints',[])}
    prefix=unit.configuration+'.'
    results=[]
    failed=next(((unit.name+'::'+name if name.startswith('setup.') else prefix+name)
                 for name,row in reversed(rows.items()) if row['status'] in ('FAIL','RUNNING')),None)
    missing=[name for name in unit.checkpoints if name[len(prefix):] not in rows]
    # A startup/native failure may precede creation of the in-GDB journal.
    if not failed and missing:failed=missing[0]
    for name in unit.checkpoints:
        case=cases[name];checkpoint=name[len(prefix):];row=rows.get(checkpoint)
        result=dict(name=name,required=case.required,requires=list(case.requires),observes=list(case.observes),
                    journey=unit.name,checkpoint=checkpoint,artifacts=unit.name,
                    population_profile=outcome.get('population_profile',journey_population(unit)),
                    evidence=unit.name+'/probe-journey.json',seconds=(row or {}).get('seconds',
                        max(0,time.monotonic()-(row or {}).get('started_monotonic',time.monotonic()))))
        if row and row['status']=='PASS':
            result.update(status='PASS',reason='',phase_start=row['phase_start'],phase_end=row['phase_end'],
                          observations=row.get('details',{}))
        elif row and row['status']=='SKIPPED':
            result.update(status='SKIPPED',reason=row.get('reason','Feature unavailable'),observations=row.get('details',{}))
        elif row and row['status']=='FAIL' and not any(other.get('parent')==checkpoint and other['status']=='FAIL' for other in rows.values()):
            result.update(status='FAIL',reason=row.get('reason') or outcome.get('reason','Checkpoint failed'),root_causes=[name])
        elif name==failed:
            result.update(status='FAIL',reason=outcome.get('reason') or (row or {}).get('reason','Checkpoint interrupted'),
                          root_causes=[name])
        else:
            result.update(status='BLOCKED',reason='Journey stopped before checkpoint; '+str(failed or unit.name),
                          root_causes=[failed or unit.name])
        results.append(result)
    return results


def run_cases(cases, executor, destination, patterns=('*',), metadata=None, shared=False):
    cases=ordered(cases)
    selected=selection(cases,patterns)
    by_name={case.name:case for case in cases}
    units=journey_plan(cases,patterns) if shared else isolated_plan(cases,patterns)
    destination.mkdir(parents=True,exist_ok=False)
    report=dict(schema='e2suite.result.2',state='running',metadata=metadata or {},results=[],journeys=[],seconds=0,
                planned_executions=len(units),planned_gameplay_processes=sum(unit.kind=='journey' for unit in units)
                +sum(1 if unit.options.get('failure_case') else 2 for unit in units if unit.kind=='persistence'))
    results={};start=time.monotonic();interrupted=False
    print(f'[==========] Running {len(selected)} selected cases in {len(units)} execution units.',flush=True)
    def retain(result):
        results[result['name']]=result
        report['results'].append(result)
        print(f"[ {result['status']:<8} ] {result['name']} ({result['seconds']:.2f}s)"
              +(f" — {result['reason']}" if result.get('reason') else ''),flush=True)
        report['seconds']=time.monotonic()-start
        write_reports(destination,report)
    for unit in units:
        members=[by_name[name] for name in unit.checkpoints] if unit.checkpoints else [unit]
        blocked={}
        if unit.checkpoints:
            for case in members:
                unavailable=[name for name in case.requires if
                    (name in blocked or (name not in unit.checkpoints and results[name]['status']!='PASS'))]
                if unavailable:
                    previous=results|blocked
                    roots=sorted({root for name in unavailable for root in previous[name].get('root_causes',[name])})
                    blocked[case.name]=dict(name=case.name,required=case.required,requires=list(case.requires),
                        observes=list(case.observes),journey=unit.name,checkpoint=case.name.split('.',1)[1],
                        status='BLOCKED',reason='Requires '+', '.join(unavailable),blocked_by=unavailable,
                        evidence=next((previous[name]['evidence'] for name in unavailable if previous[name].get('evidence')),
                                      'report.json'),root_causes=roots,seconds=0)
            eligible=tuple(case.name for case in members if case.name not in blocked)
            active=replace(unit,checkpoints=eligible,options=unit.options|
                           dict(checks=[name.split('.',1)[1] for name in eligible]))
            unavailable=[]
        else:
            active=unit
            unavailable=[name for name in unit.requires if results[name]['status']!='PASS']
        unit_start=time.monotonic()
        outcome=None
        if unit.checkpoints and not eligible:
            outcome=dict(status='BLOCKED',reason='All assigned checkpoints blocked by external prerequisites')
        elif unit.skip:
            outcome=dict(status='SKIPPED',reason=unit.skip)
        elif unavailable:
            roots=sorted({root for name in unavailable for root in results[name].get('root_causes',[name])})
            outcome=dict(status='BLOCKED',reason='Requires '+', '.join(unavailable),
                         blocked_by=unavailable,root_causes=roots)
        else:
            print('[ RUN      ] '+unit.name,flush=True)
            if active.kind=='journey':
                startup={'early':'early Space skip','delayed':'delayed Space skip',
                         'natural':'natural intro completion (no skip)'}[active.options.get('intro','delayed')]
                if active.scenario=='menu-matrix':startup='menu stages: horseback intro, pedestal intro, gameplay'
                print(f'  [ STARTUP  ] {startup}; configuration: {active.configuration}',flush=True)
                print('  [ WORLD    ] '+journey_population(active),flush=True)
                if active.checkpoints:
                    print('  [ CHECKS   ] '+', '.join(active.checkpoints),flush=True)
            try:
                outcome=executor(active,destination,results)
                if outcome.get('status') not in ('PASS','FAIL','SKIPPED','BLOCKED'):
                    raise ValueError('Executor returned an invalid status')
            except KeyboardInterrupt:
                interrupted=True
                outcome=dict(status='FAIL',reason='Suite interrupted',interrupted=True)
                progress=destination/unit.name/'probe-journey.json'
                if progress.is_file():outcome['progress']=json.loads(progress.read_text())
            except Exception as error:
                outcome=dict(status='FAIL',reason=f'{type(error).__name__}: {error}')
            progress=destination/unit.name/'probe-journey.json'
            if unit.checkpoints and 'progress' not in outcome and progress.is_file():
                outcome['progress']=json.loads(progress.read_text())
            interrupted=interrupted or outcome.get('interrupted',False)
        elapsed=time.monotonic()-unit_start
        if unit.checkpoints:
            lifecycle=dict(outcome,name=unit.name,seconds=elapsed,checkpoints=list(unit.checkpoints),artifacts=unit.name,
                           configuration=unit.configuration,startup='menu-stages' if unit.scenario=='menu-matrix' else unit.options.get('intro','delayed'))
            mapped=shared_results(active,outcome,by_name) if eligible else []
            mapped_by_name={row['name']:row for row in mapped}|blocked
            mapped=[mapped_by_name[case.name] for case in members]
            lifecycle['scheduled_checkpoints']=list(eligible)
            rows=outcome.get('progress',{}).get('checkpoints',[])
            lifecycle['started_checkpoints']=[unit.configuration+'.'+row['name'] for row in rows
                                               if unit.configuration+'.'+row['name'] in eligible]
            lifecycle['failed_checkpoint']=next((row['name'] for row in reversed(rows)
                                                  if row['status'] in ('FAIL','RUNNING')),None)
            if outcome['status']=='PASS' and any(row['status'] not in ('PASS','SKIPPED') for row in mapped if row['name'] not in blocked):
                lifecycle.update(status='FAIL',reason=next((row['reason'] for row in mapped if row['status']=='FAIL'),
                                                            'Missing successful checkpoint evidence'))
            report['journeys'].append(lifecycle)
            for result in mapped:retain(result)
            print(f"[ JOURNEY  ] {unit.name}: {lifecycle['status']} ({elapsed:.2f}s)",flush=True)
        else:
            result=dict(name=unit.name,required=unit.required,requires=list(unit.requires),observes=list(unit.observes),
                        seconds=elapsed,**outcome)
            if result['status']=='FAIL':result['root_causes']=[unit.name]
            retain(result)
        if interrupted:break
    if interrupted:
        owners={name:unit.name for unit in units for name in unit.checkpoints}
        for case in cases:
            if case.name in selected and case.name not in results:
                pending=dict(name=case.name,status='SKIPPED',required=case.required,
                             reason='Suite interrupted',requires=list(case.requires),seconds=0)
                if case.name in owners:
                    pending.update(journey=owners[case.name],checkpoint=case.name.split('.',1)[1],evidence='report.json')
                retain(pending)
    counts={key:sum(r['status']==key for r in report['results']) for key in ('PASS','FAIL','BLOCKED','SKIPPED')}
    report.update(state='interrupted' if interrupted else 'complete',seconds=time.monotonic()-start,counts=counts)
    journey_failed=any(row['status']=='FAIL' for row in report['journeys'])
    report['exit_code']=130 if interrupted else (1 if counts['FAIL'] or counts['BLOCKED'] or journey_failed else
        2 if any(r['required'] and r['status']=='SKIPPED' for r in report['results']) else 0)
    write_reports(destination,report)
    print(f"[==========] {len(report['results'])} cases ({report['seconds']:.2f}s)",flush=True)
    for status,count in counts.items():print(f'[ {status:<8} ] {count}',flush=True)
    if report['journeys']:
        print(f"[ JOURNEYS ] {sum(row['status']=='FAIL' for row in report['journeys'])} failed; exit {report['exit_code']}",flush=True)
    print('Reports: '+str(destination/'report.html')+' (JSON and JUnit XML alongside)',flush=True)
    return report


def catalogue(configurations, game_data, build=False, replay_corpus=None):
    py=sys.executable;original=str(game_data/'E2WIN95.EXE');names=str(game_data/'Code/ECSTATIC.FAN')
    cases=[Case('Source.GeneratorParity',(py,str(ROOT/'scripts/check-e2-generation-parity.py'))),
           Case('Tools.SuiteContracts',(py,str(ROOT/'scripts/check-e2-suite.py'))),
           Case('Tools.NavigationContracts',(py,str(ROOT/'scripts/check-e2-navigation.py')))]
    for configuration in configurations:
        prefix=configuration+'.';asan=configuration=='asan'
        preset='linux-clang32-sdl-debug'+('-asan' if asan else '')
        cases.append(Case(prefix+'Build',kind='build',configuration=configuration,
                          options=dict(preset=preset,build=build),timeout=240))
        cases.append(Case(prefix+'Host.SessionMaintenance',
            (py,str(ROOT/'scripts/check-e2-session-maintenance.py'),*(['--asan'] if asan else [])),
            configuration=configuration,timeout=120))
        cases.append(Case(prefix+'Host.DirectDrawSurfaces',
            (py,str(ROOT/'scripts/check-e2-ddraw-surfaces.py'),*(['--asan'] if asan else [])),
            configuration=configuration,timeout=100))
        for label,script in [('SaveStorage','save-storage'),('SaveStreams','save-streams')]:
            cases.append(Case(prefix+'Host.'+label,
                (py,str(ROOT/f'scripts/check-e2-{script}.py'),*(['--asan'] if asan else [])),
                configuration=configuration,timeout=100))
        for label,script,extra in [
            ('ActorNames','actor-names',[names]),('AnimationNames','animation-names',[names]),
            ('ScriptNames','script-names',[]),('Menus','menu-contracts',[]),
            ('MenuLayout','menu-layout',[]),
            ('Hud','original-hud',[]),('HudPixels','hud-pixels',[]),
            ('Inventory','inventory',[]),
            ('PlayerMesh','player-mesh',[]),('EllipsoidPixels','ellipsoid-pixels',[]),
            ('InterpolatedNodeEvents','interpolated-node-events',[]),('RenderCopies','render-copies',[]),
            ('PoseEvents','action-pose-events',[]),('BitmapRecords','bitmap-records',[]),
            ('ActorEviction','actor-eviction',[]),('KeyRelease','key-release',None),
            ('SaveContracts','save-contracts',[]),('SaveWriter','save-writer',[]),
            ('SaveSlotCallbacks','save-slot-callbacks',[]),('SaveRestoreTimers','save-restore-timers',[]),
            ('AttackTarget','attack-target',[]),('Pickup','pickup',[]),
            ('Attachment','pickup-attachment',[]),('Detach','attachment-detach',[]),
            ('Timers','potion-timers',[]),('CacheReclamation','action-reclamation',[]),
            ('ScriptFlow','script-flow',[]),('TowerConditions','tower-conditions',[]),
            ('WaterIdentity','water-entry',[str(game_data/'Files/ECSTATIC')])]:
            command=[py,str(ROOT/f'scripts/check-e2-{script}.py')]
            if extra is not None: command += [original,*extra]
            if asan: command += ['--asan']
            cases.append(Case(prefix+'Original.'+label,tuple(command),timeout=100,configuration=configuration))
        cases.append(Case(prefix+'Original.NoncombatPopulation',
            (py,str(ROOT/'scripts/check-e2-test-population.py'),str(game_data/'Files/ECSTATIC'),*(['--asan'] if asan else [])),
            configuration=configuration,timeout=100))
        def live(label,scenario,requires=(),**options):
            timeout=options.pop('timeout',240);required=options.pop('required',True)
            cases.append(Case(prefix+label,requires=(prefix+'Build',*[prefix+r for r in requires]),
                kind='journey',scenario=scenario,configuration=configuration,timeout=timeout,options=options,required=required))
        for label,equipment,profile,failure in [('World',False,'live',None),
                ('Attachment',True,'noncombat-opening',None),('SaveFailure',False,'live','save-open')]:
            cases.append(Case(prefix+'Persistence.'+label,kind='persistence',configuration=configuration,
                requires=tuple(prefix+name for name in ('Build','Host.SaveStorage','Host.SaveStreams',
                    'Original.SaveContracts','Original.SaveWriter','Original.SaveSlotCallbacks','Original.SaveRestoreTimers','Original.Inventory',
                    'Original.Menus','Original.MenuLayout','Original.Hud','Original.HudPixels')),
                timeout=180 if failure else 600,
                options=dict(equipment=equipment,population_profile=profile,failure_case=failure)))
        live('Startup.EarlySkip','startup',intro='early')
        live('Startup.DelayedSkip','startup',intro='delayed')
        live('Startup.Natural','startup',intro='natural',timeout=180)
        live('Movement.ControlsAndRelease','movement',('Startup.DelayedSkip',))
        motion=('Movement.ControlsAndRelease',)
        live('Combat.UnarmedDirections','unarmed',motion)
        live('Traversal.CourtyardReturn','courtyard',motion)
        live('Traversal.Workshop','workshop',motion)
        workshop=('Traversal.Workshop',)
        live('Combat.UnarmedContact','unarmed-contact',('Combat.UnarmedDirections','Traversal.Workshop'))
        live('Interaction.SwordPickup','sword',workshop)
        sword=('Interaction.SwordPickup',)
        live('Combat.FourDirections','attacks',sword)
        combat=('Combat.FourDirections',)
        live('Combat.KillSmith','enemy',combat)
        live('Interaction.DoorPassage','door',combat)
        live('Interaction.DoorPassageDisplaced','door',('Combat.KillSmith',),
             displaced_door_start=True,observe_door_health=True,timeout=360)
        live('Combat.TakeDamage','damage',motion)
        for label,wait,damaged in [('A',0,False),('B',37,False),('C',83,True),('D',221,True)]:
            live('Potion.Trial'+label,'potion-damaged' if damaged else 'potion',
                 ('Combat.TakeDamage',) if damaged else workshop,potion_wait=wait,timeout=300)
        for branch in ('healing','poison','invisibility','noop'):
            cases.append(Case(prefix+'Potion.Branch.'+branch,kind='coverage',configuration=configuration,required=False,
                options=dict(branch=branch,trials=[prefix+'Potion.Trial'+label for label in 'ABCD']),
                observes=tuple(prefix+'Potion.Trial'+label for label in 'ABCD')))
        live('Interaction.PotionThenSword','potion-sword',('Potion.TrialA','Interaction.SwordPickup'))
        live('Movement.Swimming','swimming',motion,timeout=300)
        live('Traversal.Water','water-traversal',('Movement.Swimming',),timeout=300)
        live('Combat.SwimmingDirections','water-combat',('Movement.Swimming',),timeout=300)
        live('Movement.ArmedSwimming','armed-swimming',sword,timeout=360)
        live('Combat.ArmedSwimmingDirections','armed-water-combat',('Movement.ArmedSwimming',),timeout=360)
        live('Traversal.ArmedWater','armed-water-traversal',('Movement.ArmedSwimming',),timeout=360)
        live('Menus.CancelResumeQuit','menus',('Startup.DelayedSkip',))
        for check in MENU_CHECKS:
            if check=='Menus.CancelResumeQuit':continue
            live(check,'menu-matrix',timeout=360,required=not check.endswith('.ResolutionToggle'))
        for stage in MENU_STAGES:
            for action,reason in MENU_UNFINISHED.items():
                cases.append(Case(prefix+'Menus.'+stage+'.'+action,required=False,skip=reason,
                                  configuration=configuration))
        live('Stability.MixedJourney','stability',('Interaction.DoorPassage',),stability_batches=24,observe=60,timeout=300)
        for label,reason in [('Potion.DeathExpiryCure','Final poison death, invisibility expiry/cure are not recovered acceptance yet'),
                             ('Movement.ShoreExit','Shore exit needs a recovered climb/exit route; swimming attacks and traversal run separately')]:
            cases.append(Case(prefix+label,required=False,skip=reason,configuration=configuration))
        if replay_corpus:
            corpus=json.loads(replay_corpus.read_text())
            if corpus.get('schema')!='e2suite.recordings.1' or not isinstance(corpus.get('recordings'),list):
                raise ValueError('Unsupported replay corpus manifest')
            for i,recording in enumerate(corpus['recordings']):
                source=(replay_corpus.parent/recording['source']).resolve()
                spec=(replay_corpus.parent/recording['specification']).resolve()
                cases.append(Case(prefix+f'Replay.{i+1}',kind='replay',configuration=configuration,
                    requires=(prefix+'Build',),options=dict(source=str(source),specification=str(spec)),timeout=180))
        else:
            cases.append(Case(prefix+'Replay.CompleteCorpus',required=False,
                skip='No portable complete-recording corpus supplied; use --replay-corpus',configuration=configuration))
    return cases


def qualify_journey_failure(case, result):
    """A repeated setup can fail even after its independent smoke case passed."""
    if result['status']!='FAIL' or result.get('native_failure'):return result
    phases=result.get('phases',[])
    failed=next((p for p in reversed(phases) if p['status']=='FAIL'),None)
    if not failed:return result
    targets={
        'startup':('startup.',),'movement':('movement.',),
        'courtyard':('traversal.courtyard',),'workshop':('traversal.workshop',),
        'sword':('interaction.sword',),'attacks':('combat.attack-',),
        'enemy':('combat.kill-enemy',),'damage':('combat.take-natural-damage',),
        'unarmed':('combat.unarmed-',),'unarmed-contact':('combat.unarmed-contact',),
        'door':('interaction.break-door','traversal.door-passage'),
        'potion':('interaction.drink',),'potion-damaged':('interaction.drink',),
        'potion-sword':('interaction.drink','interaction.sword'),
        'swimming':('movement.swimming',),'menus':('menus.',),
        'water-traversal':('traversal.water-outward','traversal.water-return'),
        'water-combat':('combat.swimming-',),
        'armed-swimming':('movement.swimming',),
        'armed-water-traversal':('traversal.water-outward','traversal.water-return'),
        'armed-water-combat':('combat.swimming-',),
        'stability':('stability.',),
    }.get(case.scenario,())
    if targets and not any(p['name'].startswith(targets) for p in phases):
        result.update(status='BLOCKED',reason='Fresh prerequisite '+failed['name']+' failed: '+
                      failed['reason']+'; target action not exercised',
                      root_causes=[case.name+'::'+failed['name']],failed_phase=failed)
    return result


def executor(game_data, video_driver='dummy'):
    def perform(case, destination, results):
        directory=destination/case.name
        binary=ROOT/'build/Debug'/('clang21-i386-sdl-asan' if case.configuration=='asan' else 'clang21-i386-sdl')/'e2recomp'
        environment=os.environ.copy()
        for key in list(environment):
            if key.startswith('E2R_') or key in ('SDL_VIDEODRIVER','SDL_AUDIODRIVER','ASAN_OPTIONS'):
                environment.pop(key)
        environment.update(E2R_RECORD='off',E2R_DATA_DIR=str(directory/'runtime'),
                           SDL_VIDEODRIVER=video_driver,ASAN_OPTIONS='detect_leaks=0')
        if case.kind=='coverage':
            trials=[results.get(name) for name in case.options['trials']]
            for result in trials:
                potion=(result or {}).get('observations',{}).get('potion',{})
                if not potion and isinstance((result or {}).get('journey'),dict):
                    potion=result['journey'].get('details',{}).get('potion',{})
                if (result or {}).get('status')=='PASS' and potion.get('branch')==case.options['branch']:
                    if potion['branch']=='healing' and potion['before_health']>=100: continue
                    provenance={key:result[key] for key in ('journey','artifacts','evidence')
                                if key in result and isinstance(result[key],str)}
                    return dict(status='PASS',reason='Observed by '+result['name'],
                                checkpoint=case.name.split('.',1)[-1],source_checkpoint=result.get('checkpoint'),
                                observed_by=result['name'],**provenance)
            failed=[r['name'] for r in trials if r and r['status'] in ('FAIL','BLOCKED')]
            if failed:
                roots=sorted({root for name in failed for root in results[name].get('root_causes',[name])})
                return dict(status='BLOCKED',reason='Potion trials failed before branch acceptance',root_causes=roots)
            return dict(status='SKIPPED',reason='Random outcome not sampled; consumption accepts any original branch')
        if case.kind=='build':
            if case.options['build']:
                result=execute(('cmake','--build','--preset',case.options['preset']),directory,case.timeout,environment)
                if result['status']!='PASS':return result|dict(artifacts=case.name)
            if not binary.is_file():
                return dict(status='FAIL',reason='Executable missing; configure its SDL preset and use --build')
            directory.mkdir(parents=True,exist_ok=True)
            identity=dict(path=str(binary),sha256=digest(binary),pinned=str(directory/'e2recomp'))
            (directory/'binary.json').write_text(json.dumps(identity,indent=2)+'\n')
            # Pin once per configuration, before executing any runtime case.
            import shutil
            shutil.copy2(binary,directory/'e2recomp')
            return dict(status='PASS',reason='',binary=identity)
        if case.kind in ('journey','replay','persistence'):
            binary=destination/(case.configuration+'.Build')/'e2recomp'
            expected=results[case.configuration+'.Build']['binary']['sha256']
            if digest(binary)!=expected:
                return dict(status='FAIL',reason='Pinned executable identity changed')
        if case.kind=='persistence':
            processes=1 if case.options.get('failure_case') else 2
            command=[sys.executable,str(ROOT/'scripts/probe-e2-game-save-load.py'),str(binary),
                '--game-data',str(game_data),'--output',str(directory/'probe'),
                '--timeout',str(int(case.timeout/processes)-10),'--video-driver',video_driver,
                '--population-profile',case.options['population_profile']]
            if case.options['equipment']:command+=['--equipment']
            if case.options.get('failure_case'):command+=['--failure-case',case.options['failure_case']]
            else:command+=['--hud','--inventory']
            result=execute(command,directory,case.timeout,environment)
            report_path=directory/'probe/report.json'
            if report_path.is_file():
                report=json.loads(report_path.read_text())
                accepted=(report.get('probe_complete') and len(report.get('processes',[]))==processes
                    and all(row.get('native_exit_code')==0 for row in report['processes'])
                    and all(report.get('installed_saves_unchanged',{}).values())
                    and all(report.get('unowned_private_slots_unchanged',{}).values()))
                if result['status']=='PASS' and not accepted:
                    result.update(status='FAIL',reason='Missing completed persistence/preservation evidence')
                result['persistence']=report
            elif result['status']=='PASS':result.update(status='FAIL',reason='Persistence probe emitted no report')
            return result|dict(artifacts=case.name,population_profile=case.options['population_profile'])
        if case.kind=='journey':
            # Watch mode adds host pacing only. Fresh timing/RNG may differ;
            # retain the same assertions with a larger, still bounded timeout.
            timeout=case.timeout*(3 if video_driver!='dummy' else 1)
            options={k:v for k,v in case.options.items() if k not in ('intro','observe')}
            profile=journey_population(case)
            command=[sys.executable,str(ROOT/'scripts/probe-e2-player-motion.py'),str(binary),
                '--game-data',str(game_data),'--suite-scenario',case.scenario,'--suite-options',json.dumps(options),'--population-profile',profile,
                '--player-mesh','--npc-mesh','--burst-frames','--gameplay-menu-exit','--timeout',str(int(timeout)-10),
                '--video-driver',video_driver,'--window-title',case.name,
                '--output',str(directory/'probe')]
            if profile=='live':command+=['--background-spawns']
            if video_driver!='dummy':command+=['--watch']
            intro=case.options.get('intro','delayed')
            if case.scenario!='menu-matrix':
                command += ['--natural-intro'] if intro=='natural' else ['--intro-skip-action','1','--intro-skip-progress','1' if intro=='early' else '83']
            if case.options.get('observe'):command+=['--observe-seconds',str(case.options['observe'])]
            if case.checkpoints:
                directory.mkdir(parents=True,exist_ok=True)
                first=case.options['checks'][0]
                initial=first if first.startswith('Startup.') else 'setup.Startup'
                (directory/'probe-journey.json').write_text(json.dumps(dict(schema='e2suite.journey.1',
                    scenario='shared',phases=[],checkpoints=[dict(name=initial,status='RUNNING',phase_start=0,started_monotonic=time.monotonic())],
                    inputs=[],updates=0,details={},complete=False),indent=2)+'\n')
            result=execute(command,directory,timeout,environment,directory/'probe-journey.json')
            report_path=directory/'probe.json'
            if report_path.is_file():
                probe=json.loads(report_path.read_text())
                if result['status']=='PASS' and (not probe.get('probe_complete') or not probe.get('suite_result')):
                    result=dict(status='FAIL',reason='Missing completed journey report')
                result['journey']=probe.get('suite_result') or {}
                if result['status']=='PASS':
                    from e2_inspection import Inspection
                    captures=sorted((directory/'probe-runtime/logs').glob('session_*/inspection'))
                    if probe.get('native_exit_code')!=0 or not captures or not Inspection(captures[-1]).complete:
                        result.update(status='FAIL',reason='Native clean exit / completed inspection missing')
            elif result['status']=='PASS':result=dict(status='FAIL',reason='Probe emitted no report')
            native_log=directory/'probe.log'
            if native_log.is_file():
                native_output=native_log.read_text(errors='replace')
                signal_match=re.search(r'(?:received|terminated with) signal (\w+)',native_output)
                stopped=re.search(r'received signal [^\n]+\n(?:0x[0-9a-f]+ in )?(\w+) \(',native_output)
                sanitizer=re.search(r'ERROR: AddressSanitizer: ([^\s]+).*?\n.*?\n\s*#0 .*? in (\w+) ',native_output,re.S)
                frame_match=stopped or (None if sanitizer else re.search(r'^#0 .*? in (\w+) ',native_output,re.M))
                if signal_match or 'ERROR: AddressSanitizer' in native_output:
                    result['native_failure']=dict(signal=signal_match[1] if signal_match else 'AddressSanitizer',
                        function=frame_match[1] if frame_match else sanitizer[2] if sanitizer else None,log='probe.log')
                    if sanitizer:result['native_failure']['diagnostic']=sanitizer[1]
                    result.update(status='FAIL',reason=result['native_failure']['signal']+
                        (' in '+frame_match[1] if frame_match else ''))
            stopped_path=directory/'probe-stopped.json'
            stall_path=directory/'probe-stall.json'
            if stopped_path.is_file():
                stopped_data=json.loads(stopped_path.read_text())
                result['stopped_evidence']=stopped_path.name
                if stopped_data.get('exception'):
                    result['native_failure']=dict(exception=stopped_data['exception'],log=stopped_path.name)
                    result.update(status='FAIL',reason=stopped_data['exception'])
            if stall_path.is_file():
                result['stall']=json.loads(stall_path.read_text())
                result['native_failure']=result.get('native_failure',{})|dict(stall=stall_path.name)
                result.update(status='FAIL',reason=result['stall']['reason']+'; see '+stall_path.name)
            progress=directory/'probe-journey.json'
            if progress.is_file():
                journey=json.loads(progress.read_text())
                result['phases']=journey.get('phases',[])
                if result['status']=='FAIL':
                    failed=next((p for p in reversed(result['phases']) if p['status']=='FAIL'),None)
                    if failed:
                        phase_reason=failed['name']+': '+failed['reason']
                        result['reason']=(result['reason']+'; '+phase_reason) if result.get('native_failure') else phase_reason
            if case.checkpoints:
                result['progress']=journey if progress.is_file() else {}
                return result|dict(artifacts=case.name,population_profile=profile)
            return qualify_journey_failure(case,result)|dict(artifacts=case.name,population_profile=profile)
        if case.kind=='replay':
            command=(sys.executable,str(ROOT/'scripts/e2-debug.py'),'scenario',str(binary),
                case.options['source'],case.options['specification'],str(directory/'replay'),
                '--compatible','--timeout',str(int(case.timeout)-10),'--video-driver',video_driver)
        else:
            command=case.command
            if case.name=='Source.GeneratorParity':command+=('--output',str(directory/'generation'))
            if '.Original.Save' in case.name or '.Original.Menu' in case.name or '.Host.Save' in case.name:
                command+=('--keep-harness',str(directory/'fixture.c'))
        result=execute(command,directory,case.timeout,environment)
        return result|dict(artifacts=case.name)
    return perform
