"""Dependency-aware Ecstatica regression catalogue, execution and reports."""
from __future__ import annotations

from dataclasses import dataclass, field
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

ROOT = Path(__file__).resolve().parent.parent

# Blocks select targets; selection() always adds their transitive prerequisites.
BLOCKS = {
    'full': ('*',),
    'checks': ('Source.*','Tools.*','*.Original.*','*.Host.*'),
    'startup': ('*.Startup.*',),
    'movement': ('*.Movement.ControlsAndRelease','*.Traversal.CourtyardReturn'),
    'unarmed': ('*.Combat.Unarmed*','*.Combat.TakeDamage'),
    'workshop': ('*.Traversal.Workshop','*.Interaction.SwordPickup','*.Combat.FourDirections',
                 '*.Combat.KillSmith','*.Interaction.DoorPassage'),
    'potions': ('*.Potion.*','*.Interaction.PotionThenSword'),
    'swimming': ('*.Movement.Swimming','*.Movement.ArmedSwimmingAndShoreExit'),
    'menus': ('*.Menus.*',),
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


def digest(path):
    value = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda:stream.read(1024*1024), b''):
            value.update(block)
    return value.hexdigest()


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
    suite=ET.Element('testsuite',name='Ecstatica II',tests=str(len(report['results'])),
                     failures=str(counts['FAIL']),skipped=str(counts['BLOCKED']+counts['SKIPPED']),
                     time=f"{report.get('seconds',0):.3f}")
    rows=[]
    for result in report['results']:
        case=ET.SubElement(suite,'testcase',name=result['name'],classname='Ecstatica',
                           time=f"{result.get('seconds',0):.3f}")
        props=ET.SubElement(case,'properties')
        ET.SubElement(props,'property',name='status',value=result['status'])
        if result['status']=='FAIL':
            ET.SubElement(case,'failure',message=result['reason']).text=result['reason']
        elif result['status'] in ('BLOCKED','SKIPPED'):
            ET.SubElement(case,'skipped',type=result['status'].lower(),message=result['reason'])
        name=html.escape(result['name']);reason=html.escape(result.get('reason',''))
        artifact=result.get('artifacts')
        link=f'<a href="{html.escape(artifact,quote=True)}/console.log">log</a>' if artifact else ''
        rows.append(f'<tr><td>{name}</td><td class="{result["status"]}">{result["status"]}</td>'
                    f'<td>{result.get("seconds",0):.2f}s</td><td>{reason}</td><td>{link}</td></tr>')
    ET.indent(suite)
    ET.ElementTree(suite).write(destination/'report.xml',encoding='utf-8',xml_declaration=True)
    document='''<!doctype html><meta charset="utf-8"><title>Ecstatica II regression suite</title>
<style>body{font:16px system-ui;margin:2rem;background:#171b22;color:#e9edf3}table{border-collapse:collapse;width:100%}td,th{text-align:left;padding:.6rem;border-bottom:1px solid #444}.PASS{color:#83d997}.FAIL{color:#ff8a8a}.BLOCKED{color:#ffd175}.SKIPPED{color:#b0b8c7}a{color:#8ecbff}</style>
<h1>Ecstatica II regression suite</h1>'''
    document+=f'<p>{html.escape(report.get("state","running"))} · '+html.escape(str(counts))+'</p>'
    document+='<table><tr><th>Scenario</th><th>Status</th><th>Time</th><th>Reason</th><th>Evidence</th></tr>'+''.join(rows)+'</table>'
    (destination/'report.html').write_text(document)


def run_cases(cases, executor, destination, patterns=('*',), metadata=None):
    cases=ordered(cases)
    selected=selection(cases,patterns)
    destination.mkdir(parents=True,exist_ok=False)
    report=dict(schema='e2suite.result.1',state='running',metadata=metadata or {},results=[],seconds=0)
    results={};start=time.monotonic();interrupted=False
    print(f'[==========] Running {len(selected)} selected cases in dependency order.',flush=True)
    try:
        for case in cases:
            if case.name not in selected:
                continue
            case_start=time.monotonic()
            result=dict(name=case.name,required=case.required,requires=list(case.requires),observes=list(case.observes))
            unavailable=[dependency for dependency in case.requires if results[dependency]['status']!='PASS']
            if case.skip:
                result.update(status='SKIPPED',reason=case.skip)
            elif unavailable:
                roots=sorted({root for name in unavailable for root in results[name].get('root_causes',[name])})
                result.update(status='BLOCKED',reason='Requires '+', '.join(unavailable),
                              blocked_by=unavailable,root_causes=roots)
            else:
                print('[ RUN      ] '+case.name,flush=True)
                try:
                    result.update(executor(case,destination,results))
                    if result.get('status') not in ('PASS','FAIL','SKIPPED','BLOCKED'):
                        raise ValueError('Executor returned an invalid status')
                except Exception as error:
                    result.update(status='FAIL',reason=f'{type(error).__name__}: {error}')
            result['seconds']=time.monotonic()-case_start
            if result['status']=='FAIL': result['root_causes']=[case.name]
            results[case.name]=result
            report['results'].append(result)
            print(f"[ {result['status']:<8} ] {case.name} ({result['seconds']:.2f}s)"
                  +(f" — {result['reason']}" if result.get('reason') else ''),flush=True)
            report['seconds']=time.monotonic()-start
            write_reports(destination,report)
    except KeyboardInterrupt:
        interrupted=True
        for case in cases:
            if case.name in selected and case.name not in results:
                report['results'].append(dict(name=case.name,status='SKIPPED',required=case.required,
                    reason='Suite interrupted',requires=list(case.requires),seconds=0))
    counts={key:sum(r['status']==key for r in report['results']) for key in ('PASS','FAIL','BLOCKED','SKIPPED')}
    report.update(state='interrupted' if interrupted else 'complete',seconds=time.monotonic()-start,counts=counts)
    report['exit_code']=130 if interrupted else (1 if counts['FAIL'] or counts['BLOCKED'] else
        2 if any(r['required'] and r['status']=='SKIPPED' for r in report['results']) else 0)
    write_reports(destination,report)
    print(f"[==========] {len(report['results'])} cases ({report['seconds']:.2f}s)",flush=True)
    for status,count in counts.items(): print(f'[ {status:<8} ] {count}',flush=True)
    print('Reports: '+str(destination/'report.html')+' (JSON and JUnit XML alongside)',flush=True)
    return report


def catalogue(configurations, game_data, build=False, replay_corpus=None):
    py=sys.executable;original=str(game_data/'E2WIN95.EXE');names=str(game_data/'Code/ECSTATIC.FAN')
    cases=[Case('Source.GeneratorParity',(py,str(ROOT/'scripts/check-e2-generation-parity.py'))),
           Case('Tools.SuiteContracts',(py,str(ROOT/'scripts/check-e2-suite.py')))]
    for configuration in configurations:
        prefix=configuration+'.';asan=configuration=='asan'
        preset='linux-clang32-sdl-debug'+('-asan' if asan else '')
        cases.append(Case(prefix+'Build',kind='build',configuration=configuration,
                          options=dict(preset=preset,build=build),timeout=240))
        cases.append(Case(prefix+'Host.SessionMaintenance',
            (py,str(ROOT/'scripts/check-e2-session-maintenance.py'),*(['--asan'] if asan else [])),
            configuration=configuration,timeout=120))
        for label,script,extra in [
            ('ActorNames','actor-names',[names]),('AnimationNames','animation-names',[names]),
            ('ScriptNames','script-names',[]),('KeyRelease','key-release',None),
            ('AttackTarget','attack-target',[]),('Pickup','pickup',[]),
            ('Attachment','pickup-attachment',[]),('Detach','attachment-detach',[]),
            ('Timers','potion-timers',[]),('CacheReclamation','action-reclamation',[]),
            ('ScriptFlow','script-flow',[]),('WaterIdentity','water-entry',[str(game_data/'Files/ECSTATIC')])]:
            command=[py,str(ROOT/f'scripts/check-e2-{script}.py')]
            if extra is not None: command += [original,*extra]
            if asan: command += ['--asan']
            cases.append(Case(prefix+'Original.'+label,tuple(command),timeout=100,configuration=configuration))
        def live(label,scenario,requires=(),**options):
            cases.append(Case(prefix+label,requires=(prefix+'Build',*[prefix+r for r in requires]),
                kind='journey',scenario=scenario,configuration=configuration,timeout=options.pop('timeout',240),options=options))
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
        live('Combat.TakeDamage','damage',motion)
        for label,wait,damaged in [('A',0,False),('B',37,False),('C',83,True),('D',221,True)]:
            live('Potion.Trial'+label,'potion-damaged' if damaged else 'potion',
                 ('Combat.TakeDamage',) if damaged else workshop,potion_wait=wait,timeout=300)
        for branch in ('healing','poison','invisibility','noop'):
            cases.append(Case(prefix+'Potion.Branch.'+branch,kind='coverage',configuration=configuration,
                options=dict(branch=branch,trials=[prefix+'Potion.Trial'+label for label in 'ABCD']),
                observes=tuple(prefix+'Potion.Trial'+label for label in 'ABCD')))
        live('Interaction.PotionThenSword','potion-sword',('Potion.TrialA','Interaction.SwordPickup'))
        live('Movement.Swimming','swimming',motion,timeout=300)
        live('Menus.CancelResumeQuit','menus',('Startup.DelayedSkip',))
        live('Stability.MixedJourney','stability',('Interaction.DoorPassage',),stability_batches=24,observe=60,timeout=300)
        for label,reason in [('Potion.DeathExpiryCure','Final poison death, invisibility expiry/cure are not recovered acceptance yet'),
                             ('Movement.ArmedSwimmingAndShoreExit','Armed swimming and shore exit lack accepted routes')]:
            cases.append(Case(prefix+label,required=False,skip=reason))
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
                skip='No portable complete-recording corpus supplied; use --replay-corpus'))
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
                potion=(result or {}).get('journey',{}).get('details',{}).get('potion',{})
                if (result or {}).get('status')=='PASS' and potion.get('branch')==case.options['branch']:
                    if potion['branch']=='healing' and potion['before_health']>=100: continue
                    return dict(status='PASS',reason='Observed by '+result['name'])
            failed=[r['name'] for r in trials if r and r['status'] in ('FAIL','BLOCKED')]
            if failed:
                roots=sorted({root for name in failed for root in results[name].get('root_causes',[name])})
                return dict(status='BLOCKED',reason='Potion trials failed before branch acceptance',root_causes=roots)
            return dict(status='SKIPPED',reason='Required random branch was not exercised by bounded fresh trials')
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
        if case.kind in ('journey','replay'):
            binary=destination/(case.configuration+'.Build')/'e2recomp'
            expected=results[case.configuration+'.Build']['binary']['sha256']
            if digest(binary)!=expected:
                return dict(status='FAIL',reason='Pinned executable identity changed')
        if case.kind=='journey':
            # Watch mode adds host pacing only. Fresh timing/RNG may differ;
            # retain the same assertions with a larger, still bounded timeout.
            timeout=case.timeout*(3 if video_driver!='dummy' else 1)
            options={k:v for k,v in case.options.items() if k not in ('intro','observe')}
            command=[sys.executable,str(ROOT/'scripts/probe-e2-player-motion.py'),str(binary),
                '--game-data',str(game_data),'--suite-scenario',case.scenario,'--suite-options',json.dumps(options),'--background-spawns',
                '--burst-frames','--gameplay-menu-exit','--timeout',str(int(timeout)-10),
                '--video-driver',video_driver,'--window-title',case.name,
                '--output',str(directory/'probe')]
            if video_driver!='dummy':command+=['--watch']
            intro=case.options.get('intro','delayed')
            command += ['--natural-intro'] if intro=='natural' else ['--intro-skip-action','1','--intro-skip-progress','1' if intro=='early' else '83']
            if case.options.get('observe'):command+=['--observe-seconds',str(case.options['observe'])]
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
                signal_match=re.search(r'received signal (\w+)',native_output)
                frame_match=re.search(r'^#0 .*? in (\w+) ',native_output,re.M)
                if signal_match or 'ERROR: AddressSanitizer' in native_output:
                    result['native_failure']=dict(signal=signal_match[1] if signal_match else 'AddressSanitizer',
                        function=frame_match[1] if frame_match else None,log='probe.log')
                    result.update(status='FAIL',reason=result['native_failure']['signal']+
                        (' in '+frame_match[1] if frame_match else ''))
            progress=directory/'probe-journey.json'
            if progress.is_file():
                journey=json.loads(progress.read_text())
                result['phases']=journey.get('phases',[])
                if result['status']=='FAIL':
                    failed=next((p for p in reversed(result['phases']) if p['status']=='FAIL'),None)
                    if failed:
                        phase_reason=failed['name']+': '+failed['reason']
                        result['reason']=(result['reason']+'; '+phase_reason) if result.get('native_failure') else phase_reason
            return qualify_journey_failure(case,result)|dict(artifacts=case.name)
        if case.kind=='replay':
            command=(sys.executable,str(ROOT/'scripts/e2-debug.py'),'scenario',str(binary),
                case.options['source'],case.options['specification'],str(directory/'replay'),
                '--compatible','--timeout',str(int(case.timeout)-10))
        else:
            command=case.command
            if case.name=='Source.GeneratorParity':command+=('--output',str(directory/'generation'))
        result=execute(command,directory,case.timeout,environment)
        return result|dict(artifacts=case.name)
    return perform
