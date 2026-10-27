#!/usr/bin/env python3
"""Verify suite dependency/report/lifecycle contracts without game data or GDB."""
from contextlib import redirect_stdout
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch
import xml.etree.ElementTree as ET

from e2_suite import BLOCKS, Case, ROOT, block_patterns, display_driver, catalogue, execute, executor, ordered, run_cases, selection, qualify_journey_failure, digest, journey_plan, shared_results
from e2_suite_parallel import configuration_display, run_lanes


class SuiteContracts(unittest.TestCase):
    def setUp(self):
        self.temporary=tempfile.TemporaryDirectory(prefix='e2-suite-contract-')
        self.root=Path(self.temporary.name)
        self.addCleanup(self.temporary.cleanup)

    def run_suite(self,cases,callback,patterns=('*',)):
        with redirect_stdout(io.StringIO()):
            return run_cases(cases,callback,self.root/'report',patterns)

    def test_population_profiles_keep_combat_live_and_do_not_change_after_blocking(self):
        from dataclasses import replace
        from e2_population_profile import profile_for
        from e2_suite import journey_population
        cases=self.shared_catalogue()
        for check,expected in [('Startup.EarlySkip','live'),('Startup.Natural','live'),
                               ('Startup.DelayedSkip','live'),('Traversal.CourtyardReturn','noncombat-opening'),
                               ('Interaction.SwordPickup','noncombat-opening'),('Combat.UnarmedDirections','noncombat-opening'),
                               ('Combat.UnarmedContact','live'),('Combat.KillSmith','live'),
                               ('Combat.TakeDamage','live'),('Potion.TrialA','live'),('Stability.MixedJourney','live')]:
            unit=next(unit for unit in journey_plan(cases,['debug.'+check]) if 'debug.'+check in unit.checkpoints)
            self.assertEqual(journey_population(unit),expected,check)
            reduced=replace(unit,options=dict(checks=['Movement.ControlsAndRelease']))
            self.assertEqual(journey_population(reduced),expected,check)
        self.assertEqual(profile_for('menu-matrix'),'noncombat-opening')
        self.assertEqual(profile_for('enemy'),'live')

    def test_population_census_rejects_leaks_and_preserves_evidence(self):
        import struct
        from types import SimpleNamespace
        from e2_population_profile import observe
        slots=[0]*5000;slots[0]=0x10000;slots[980]=0x20000
        flags=bytearray(10000)
        def memory(at,size):return struct.pack('<5000I',*slots) if at==0x630b60 else bytes(flags)
        gdb=SimpleNamespace(selected_inferior=lambda:SimpleNamespace(read_memory=memory),
                            parse_and_eval=lambda _:7,GdbError=RuntimeError)
        prefix=str(self.root/'population')
        with patch.dict(sys.modules,{'gdb':gdb}),patch.dict('os.environ',E2R_TEST_POPULATION='noncombat-opening'):
            row=observe(prefix,'good')
            self.assertEqual(row['loaded_actors'],[0,980])
            for identity,generated in ((284,False),(293,False),(602,False),(52,True)):
                slots[identity]=0x30000
                if generated:flags[identity*2]=8
                with self.assertRaisesRegex(RuntimeError,'leaked actors'):observe(prefix,'bad')
                slots[identity]=0;flags[identity*2]=0
            slots[0]=0
            with self.assertRaisesRegex(RuntimeError,'lost original Joe'):observe(prefix,'missing-player')
        rows=json.loads(Path(prefix+'-population-profile.json').read_text())
        self.assertEqual(len(rows),6)
        self.assertIn(602,rows[3]['loaded_actors'])

    def test_population_profile_is_forwarded_and_reported_in_all_formats(self):
        pinned=self.root/'debug.Build/e2recomp';pinned.parent.mkdir();pinned.write_bytes(b'pinned')
        cases=self.shared_catalogue()
        unit=next(unit for unit in journey_plan(cases,['debug.Traversal.CourtyardReturn']) if unit.checkpoints)
        with patch('e2_suite.execute',return_value=dict(status='FAIL',reason='contract stub')) as call:
            executor(Path('/external'))(unit,self.root,{'debug.Build':dict(binary=dict(sha256=digest(pinned)))})
        command=call.call_args.args[0]
        self.assertEqual(command[command.index('--population-profile')+1],'noncombat-opening')
        self.assertNotIn('--background-spawns',command)
        with redirect_stdout(io.StringIO()):
            report=run_cases(cases,lambda u,*_:self.checkpoint_outcome(u) if u.checkpoints else dict(status='PASS',reason=''),
                             self.root/'report',['debug.Traversal.CourtyardReturn'],shared=True)
        result=next(row for row in report['results'] if '.Traversal.' in row['name'])
        self.assertEqual(result['population_profile'],'noncombat-opening')
        self.assertIn('noncombat-opening',(self.root/'report/report.html').read_text())
        self.assertTrue(ET.parse(self.root/'report/report.xml').findall(".//property[@name='population_profile']"))

    def test_logos_use_separate_input_and_reject_interruption(self):
        import importlib.util
        from types import SimpleNamespace
        for first in (False,True):
            for policy in ('skip','natural','crash'):
                with self.subTest(first=first,policy=policy):
                    state=dict(frame='',ordinal=0,space=0,down=False,pushed=[],finish=0)
                    names=['gbnklogo','psyglogo','aasglogo'] if first else ['psyglogo','aasglogo']
                    pointers={name:index+10 for index,name in enumerate(('gbnklogo','psyglogo','aasglogo'))}
                    breaks={}
                    class Breakpoint:
                        def __init__(self,name,**_):self.enabled=True;breaks[name]=self
                        def delete(self):pass
                    def value(expression):
                        if expression=='param_1':return pointers[names[state['ordinal']]]
                        if expression.startswith('(uintptr_t)'):return pointers[expression.split('s_')[1].split('_raw')[0]]
                        if expression=='DAT_00636850':return state['space']
                        if expression=='DAT_00636844':return 0
                        if expression=='SDL_PushEvent($logo_event)':
                            state['pushed'].append(state['down']);state['space']=int(state['down']);return 1
                        raise AssertionError(expression)
                    def show():breaks['FUN_00414998'].stop();state['frame']='E2R_WaitStartupLogo'
                    def execute(command,**_):
                        if command.startswith('run '):show()
                        elif command.startswith('set $logo_event->key.down='):state['down']=command.endswith('=1')
                        elif command=='finish':
                            state['finish']+=1;state['space']=0
                            state['frame']='fault' if policy=='crash' else 'FUN_00410a48'
                        elif command=='continue':
                            state['ordinal']+=1
                            if state['ordinal']<len(names):show()
                            else:state['frame']='FUN_00415d40'
                    gdb=SimpleNamespace(Breakpoint=Breakpoint,parse_and_eval=value,execute=execute,GdbError=RuntimeError,
                        selected_frame=lambda:SimpleNamespace(name=lambda:state['frame']),
                        selected_inferior=lambda:SimpleNamespace(pid=1))
                    spec=importlib.util.spec_from_file_location('logo_contract',ROOT/'scripts/e2_startup_steps.py')
                    module=importlib.util.module_from_spec(spec)
                    with patch.dict(sys.modules,{'gdb':gdb}):spec.loader.exec_module(module)
                    prefix=str(self.root/f'logos-{first}-{policy}')
                    with redirect_stdout(io.StringIO()):
                        if policy=='crash':
                            with self.assertRaisesRegex(RuntimeError,'interrupted'):module.start('run --run-recon',prefix)
                        else:
                            rows=module.start('run --run-recon',prefix,skip=policy=='skip')
                            self.assertEqual([row['name'] for row in rows],[name+'.raw' for name in names])
                            self.assertEqual(state['pushed'],[True,False]*len(names) if policy=='skip' else [])
                            self.assertTrue(all(row['completed'] for row in rows))
                    retained=json.loads(Path(prefix+'-logos.json').read_text())
                    if policy=='crash':self.assertNotIn('completed',retained[-1])

    def test_dependencies_and_independent_failure(self):
        cases=[Case('Sword',requires=('Workshop',)),Case('Movement'),
               Case('Workshop',requires=('Movement',)),Case('Menu'),
               Case('Future',skip='Not recovered',required=False)]
        calls=[]
        def perform(case,*_):
            calls.append(case.name)
            return dict(status='FAIL' if case.name=='Movement' else 'PASS',reason='held key' if case.name=='Movement' else '')
        report=self.run_suite(cases,perform)
        results={r['name']:r for r in report['results']}
        self.assertEqual(calls,['Movement','Menu'])
        self.assertEqual(results['Sword']['status'],'BLOCKED')
        self.assertEqual(results['Sword']['root_causes'],['Movement'])
        self.assertEqual(results['Future']['status'],'SKIPPED')
        self.assertEqual(report['exit_code'],1)
        xml=ET.parse(self.root/'report/report.xml').getroot()
        self.assertEqual(xml.attrib['failures'],'1')
        self.assertEqual(xml.attrib['skipped'],'3')
        self.assertEqual(json.loads((self.root/'report/report.json').read_text())['state'],'complete')

    def test_filter_includes_transitive_prerequisites_and_observations(self):
        cases=ordered([Case('Movement'),Case('Potion',requires=('Movement',)),
                       Case('Coverage',observes=('Potion',)),Case('Menu')])
        self.assertEqual(selection(cases,['Coverage']),{'Movement','Potion','Coverage'})
        calls=[]
        def perform(case,*_):
            calls.append(case.name)
            return dict(status='FAIL' if case.name=='Potion' else 'PASS',reason='')
        report=self.run_suite(cases,perform,['Coverage'])
        self.assertEqual(calls,['Movement','Potion','Coverage'])
        self.assertEqual(len(report['results']),3)

    def test_invalid_graphs(self):
        for cases in ([Case('A'),Case('A')],[Case('A',requires=('Missing',))],
                      [Case('A',requires=('B',)),Case('B',observes=('A',))]):
            with self.assertRaises(ValueError):ordered(cases)
        with self.assertRaises(ValueError):selection([Case('A')],['Missing'])

    def test_required_skip_is_incomplete(self):
        report=self.run_suite([Case('Healing')],lambda *_:dict(status='SKIPPED',reason='Branch not sampled'))
        self.assertEqual(report['exit_code'],2)
        self.assertEqual(report['counts']['PASS'],0)

    def test_completed_optional_skip(self):
        report=self.run_suite([Case('Control'),Case('Future',skip='Unrecovered',required=False)],
                              lambda *_:dict(status='PASS',reason=''))
        self.assertEqual(report['exit_code'],0)

    def test_interrupted_report(self):
        def interrupt(*_):raise KeyboardInterrupt
        report=self.run_suite([Case('A'),Case('B',requires=('A',))],interrupt)
        self.assertEqual(report['exit_code'],130)
        self.assertEqual(report['state'],'interrupted')
        self.assertEqual(len(report['results']),2)
        self.assertFalse(any(r['status']=='PASS' for r in report['results']))

    def test_timeout_kills_descendant_and_retains_output(self):
        pidfile=self.root/'child.pid'
        code=('import subprocess,sys,time; '
              'p=subprocess.Popen([sys.executable,"-c","import time; time.sleep(60)"]); '
              f'open({str(pidfile)!r},"w").write(str(p.pid)); '
              'print("before timeout",flush=True); time.sleep(60)')
        result=execute((sys.executable,'-c',code),self.root/'timeout',.5)
        self.assertEqual(result['status'],'FAIL')
        self.assertTrue(result['timeout'])
        self.assertIn('before timeout',(self.root/'timeout/console.log').read_text())
        pid=int(pidfile.read_text())
        stat=Path(f'/proc/{pid}/stat')
        # An orphan may briefly be a zombie before the environment's init reaps it.
        self.assertTrue(not stat.exists() or stat.read_text().split()[2]=='Z')

    def test_exit_zero_with_sanitizer_report_fails(self):
        result=execute((sys.executable,'-c','print("ERROR: AddressSanitizer: test")'),self.root/'asan',3)
        self.assertEqual(result['status'],'FAIL')

    def test_coverage_requires_damaged_healing_and_successful_trial(self):
        perform=executor(Path('/unneeded'))
        case=Case('Coverage',kind='coverage',options=dict(branch='healing',trials=['Trial']))
        result=dict(name='Trial',status='PASS',journey=dict(details=dict(potion=dict(branch='healing',before_health=100))))
        self.assertEqual(perform(case,self.root,{'Trial':result})['status'],'SKIPPED')
        result['journey']['details']['potion']['before_health']=85
        self.assertEqual(perform(case,self.root,{'Trial':result})['status'],'PASS')
        result['status']='FAIL'
        self.assertEqual(perform(case,self.root,{'Trial':result})['status'],'BLOCKED')

    def test_fresh_setup_failure_blocks_unexercised_action(self):
        case=Case('Potion',scenario='potion-damaged')
        failure=dict(status='FAIL',reason='no hit',phases=[
            dict(name='startup.released-player',status='PASS'),
            dict(name='combat.take-natural-damage',status='FAIL',reason='no hit')])
        self.assertEqual(qualify_journey_failure(case,failure)['status'],'BLOCKED')
        self.assertIn('Potion::combat.take-natural-damage',failure['root_causes'])
        actual=dict(status='FAIL',reason='bottle persists',phases=[
            dict(name='interaction.drink-and-remove-bottle',status='FAIL',reason='bottle persists')])
        self.assertEqual(qualify_journey_failure(case,actual)['status'],'FAIL')
        crash=dict(status='FAIL',reason='SIGSEGV',native_failure=dict(signal='SIGSEGV'),phases=failure['phases'])
        self.assertEqual(qualify_journey_failure(case,crash)['status'],'FAIL')

    def test_complete_catalogue_and_launch(self):
        cases=ordered(catalogue(['debug','asan'],Path('/external')))
        for configuration in ('debug','asan'):
            names={case.name for case in cases}
            for name in ('Startup.Natural','Combat.KillSmith','Combat.TakeDamage','Combat.UnarmedDirections',
                         'Combat.UnarmedContact','Host.SessionMaintenance','Movement.Swimming',
                         'Interaction.PotionThenSword','Menus.CancelResumeQuit','Stability.MixedJourney'):
                self.assertIn(configuration+'.'+name,names)
        launches=json.loads((ROOT/'.vscode/launch.json').read_text())['configurations']
        game=[c for c in launches if c.get('type')=='cppdbg' and
              c.get('program')=='${command:cmake.launchTargetPath}']
        suite=[c for c in launches if 'run-e2-suite.py' in c.get('command','') and '--block ' not in c['command']]
        self.assertEqual(len(game),1)
        self.assertEqual(game[0]['args'],['--run-recon'])
        self.assertEqual(len(suite),1)
        self.assertIn('run-e2-suite.py',suite[0]['command'])
        self.assertIn('--configurations debug asan',suite[0]['command'])
        self.assertNotIn('--filter',suite[0]['command'])
        regression=[c for c in launches if 'run-e2-suite.py' in c.get('command','')]
        self.assertIs(regression[0],suite[0])
        self.assertIn('--display ${input:e2SuiteDisplay}',suite[0]['command'])

    def test_blocks_include_dependencies_without_equipping_unarmed_tests(self):
        cases=ordered(catalogue(['debug','asan'],Path('/external')))
        for block in BLOCKS:
            self.assertTrue(selection(cases,block_patterns(cases,block)))
        targets=block_patterns(cases,'unarmed',['debug.Combat.UnarmedContact'])
        names=selection(cases,targets)
        self.assertIn('debug.Traversal.Workshop',names)
        self.assertIn('debug.Movement.ControlsAndRelease',names)
        self.assertIn('debug.Combat.UnarmedDirections',names)
        self.assertNotIn('debug.Interaction.SwordPickup',names)
        self.assertFalse(any(name.startswith('asan.') for name in names))
        potion_names=selection(cases,block_patterns(cases,'potions'))
        self.assertIn('debug.Combat.TakeDamage',potion_names)
        with self.assertRaises(ValueError):block_patterns(cases,'menus',['*.Potion.*'])

    def test_display_resolution_requires_real_desktop(self):
        self.assertEqual(display_driver('headless',environment={}),'dummy')
        self.assertEqual(display_driver('visible',environment={'DISPLAY':':0'}),'x11')
        self.assertEqual(display_driver('visible',environment={'WAYLAND_DISPLAY':'wayland-0'}),'wayland')
        self.assertEqual(display_driver('visible','x11',{'DISPLAY':':0','WAYLAND_DISPLAY':'wayland-0'}),'x11')
        with self.assertRaises(ValueError):display_driver('visible',environment={})

    def test_visible_forwarding_and_bounded_timeout(self):
        pinned=self.root/'debug.Build/e2recomp'
        pinned.parent.mkdir();pinned.write_bytes(b'pinned executable')
        case=Case('debug.Menus.CancelResumeQuit',kind='journey',scenario='menus',configuration='debug',timeout=100)
        results={'debug.Build':dict(binary=dict(sha256=digest(pinned)))}
        with patch('e2_suite.execute',return_value=dict(status='FAIL',reason='contract stub')) as execute_mock:
            executor(Path('/external'),'wayland')(case,self.root,results)
        command,directory,timeout,environment,*_=execute_mock.call_args.args
        self.assertEqual(command[command.index('--video-driver')+1],'wayland')
        self.assertIn('--watch',command)
        self.assertEqual(command[command.index('--window-title')+1],case.name)
        self.assertEqual(timeout,300)
        self.assertEqual(environment['E2R_RECORD'],'off')
        self.assertEqual(environment['SDL_VIDEODRIVER'],'wayland')

    def test_block_launches_share_default_headless_picker(self):
        config=json.loads((ROOT/'.vscode/launch.json').read_text())
        picker=next(item for item in config['inputs'] if item['id']=='e2SuiteDisplay')
        self.assertEqual(picker['default'],'headless')
        self.assertEqual(picker['options'],['headless','visible-debug','visible-asan','visible-both'])
        for block in BLOCKS:
            if block=='full':continue
            launches=[c for c in config['configurations'] if '--block '+block+' ' in c.get('command','')+' ']
            self.assertEqual(len(launches),1,block)
            if block=='checks':
                self.assertNotIn('${input:',launches[0]['command'])
                self.assertNotIn('--display',launches[0]['command'])
            else:
                self.assertIn('--display ${input:e2SuiteDisplay}',launches[0]['command'])
            self.assertIn('--execution shared',launches[0]['command'])
        suites=[c for c in config['configurations'] if 'run-e2-suite.py' in c.get('command','')]
        expected=['checks','startup','menus','movement','unarmed','workshop','swimming','potions','stability','replay']
        self.assertEqual(len(suites),len(expected)+1)
        self.assertNotIn('--block ',suites[0]['command'])
        self.assertIn('--display ${input:e2SuiteDisplay}',suites[0]['command'])
        for index,(launch,block) in enumerate(zip(suites[1:],expected),1):
            self.assertTrue(launch['name'].startswith(f'Regression {index:02d}: '))
            self.assertNotIn('Ecstatica',launch['name'])
            if block!='checks':self.assertIn('--display ${input:e2SuiteDisplay}',launch['command'])
            if block!='full':self.assertIn('--block '+block+' ',launch['command']+' ')

    def shared_catalogue(self):
        return catalogue(['debug'],Path('/external'))

    def checkpoint_outcome(self, unit, stop=None, crash=False):
        rows=[]
        for index,name in enumerate(unit.checkpoints):
            suffix=name.split('.',1)[1]
            rows.append(dict(name=suffix,status='FAIL' if name==stop else 'PASS',
                             phase_start=index,phase_end=index+1,seconds=.1,details={}))
            if name==stop:break
        return dict(status='FAIL' if stop or crash else 'PASS',reason='native fault' if crash else 'assertion' if stop else '',
                    progress=dict(checkpoints=rows))

    def test_shared_plan_covers_each_selected_check_once(self):
        cases=catalogue(['debug','asan'],Path('/external'))
        units=journey_plan(cases)
        names=[name for unit in units for name in unit.checkpoints or (unit.name,)]
        self.assertEqual(set(names),{case.name for case in cases})
        self.assertEqual(len(names),184)
        self.assertEqual(sum(unit.kind=='journey' for unit in cases),96)
        self.assertEqual(sum(unit.kind=='journey' for unit in units),20)
        for unit in units:
            if unit.checkpoints:
                self.assertTrue(all(name.startswith(unit.configuration+'.') for name in unit.checkpoints))

    def test_shared_prerequisites_and_distinct_routes(self):
        cases=self.shared_catalogue()
        workshop=journey_plan(cases,block_patterns(cases,'workshop'))
        live=[unit for unit in workshop if unit.checkpoints]
        self.assertEqual(len(live),1)
        self.assertIn('debug.Movement.ControlsAndRelease',live[0].checkpoints)
        self.assertIn('debug.Combat.KillSmith',live[0].checkpoints)
        self.assertNotIn('debug.Combat.UnarmedDirections',live[0].checkpoints)
        startup=[unit for unit in journey_plan(cases,block_patterns(cases,'startup')) if unit.checkpoints]
        self.assertEqual(len(startup),3)
        self.assertEqual({unit.options['intro'] for unit in startup},{'early','delayed','natural'})
        full=journey_plan(cases)
        trials=[unit for unit in full if any('.Potion.Trial' in name for name in unit.checkpoints)]
        self.assertEqual(len(trials),4)
        self.assertEqual({unit.options['potion_wait'] for unit in trials},{0,37,83,221})
        potion_a=next(unit for unit in trials if 'debug.Potion.TrialA' in unit.checkpoints)
        self.assertIn('debug.Interaction.PotionThenSword',potion_a.checkpoints)
        water=next(unit for unit in full if 'debug.Movement.Swimming' in unit.checkpoints)
        self.assertNotIn('debug.Interaction.SwordPickup',water.checkpoints)

    def test_all_single_and_block_selections_have_valid_plans(self):
        cases=self.shared_catalogue()
        patterns=[[case.name] for case in cases]+[block_patterns(cases,block) for block in BLOCKS]
        patterns += [['debug.Potion.TrialA','debug.Combat.UnarmedContact','debug.Menus.CancelResumeQuit']]
        for targets in patterns:
            units=journey_plan(cases,targets)
            covered=[name for unit in units for name in unit.checkpoints or (unit.name,)]
            self.assertEqual(set(covered),selection(cases,targets))
            self.assertEqual(len(covered),len(set(covered)))

    def test_shared_failure_preserves_passes_and_blocks_unexercised_checks(self):
        cases=self.shared_catalogue()
        def perform(unit,*_):
            if not unit.checkpoints:return dict(status='PASS',reason='')
            return self.checkpoint_outcome(unit,stop='debug.Interaction.SwordPickup')
        with redirect_stdout(io.StringIO()):
            report=run_cases(cases,perform,self.root/'report',['debug.Interaction.DoorPassage'],shared=True)
        results={row['name']:row for row in report['results']}
        self.assertEqual(results['debug.Traversal.Workshop']['status'],'PASS')
        self.assertEqual(results['debug.Interaction.SwordPickup']['status'],'FAIL')
        self.assertEqual(results['debug.Combat.FourDirections']['status'],'BLOCKED')
        self.assertEqual(results['debug.Interaction.DoorPassage']['root_causes'],['debug.Interaction.SwordPickup'])
        self.assertEqual(report['exit_code'],1)
        sword=results['debug.Interaction.SwordPickup']
        self.assertEqual(sword['checkpoint'],'Interaction.SwordPickup')
        self.assertEqual(sword['evidence'],sword['journey']+'/probe-journey.json')
        xml=ET.parse(self.root/'report/report.xml').getroot()
        row=next(row for row in xml.findall('testcase') if row.attrib['name']=='debug.Traversal.Workshop')
        props={p.attrib['name']:p.attrib['value'] for p in row.find('properties')}
        self.assertEqual(props['journey'],sword['journey'])
        self.assertIn('checkpoint',props)
        self.assertIn(sword['evidence'],(self.root/'report/report.html').read_text())

    def test_crash_after_all_checkpoints_still_fails_journey(self):
        cases=self.shared_catalogue()
        def perform(unit,*_):
            return self.checkpoint_outcome(unit,crash=True) if unit.checkpoints else dict(status='PASS',reason='')
        with redirect_stdout(io.StringIO()):
            report=run_cases(cases,perform,self.root/'report',['debug.Menus.CancelResumeQuit'],shared=True)
        self.assertTrue(all(row['status']=='PASS' for row in report['results']))
        self.assertEqual(report['journeys'][0]['status'],'FAIL')
        self.assertEqual(report['exit_code'],1)
        self.assertEqual(ET.parse(self.root/'report/report.xml').getroot().attrib['failures'],'1')

    def test_shared_dependencies_do_not_substitute_for_checkpoint_assertions(self):
        cases=self.shared_catalogue()
        unit=next(unit for unit in journey_plan(cases,['debug.Traversal.Workshop']) if unit.checkpoints)
        outcome=self.checkpoint_outcome(unit)
        outcome['progress']['checkpoints']=[row for row in outcome['progress']['checkpoints']
                                            if row['name']!='Movement.ControlsAndRelease']
        results=shared_results(unit,outcome,{case.name:case for case in cases})
        movement=next(row for row in results if '.Movement.' in row['name'])
        self.assertEqual(movement['status'],'FAIL')
        with redirect_stdout(io.StringIO()):
            report=run_cases(cases,lambda u,*_:outcome if u.checkpoints else dict(status='PASS',reason=''),
                             self.root/'report',['debug.Traversal.Workshop'],shared=True)
        self.assertEqual(report['exit_code'],1)

    def test_interrupted_shared_journey_retains_completed_checkpoints(self):
        cases=self.shared_catalogue()
        def perform(unit,destination,*_):
            if not unit.checkpoints:return dict(status='PASS',reason='')
            progress=self.checkpoint_outcome(unit,stop='debug.Movement.ControlsAndRelease')['progress']
            progress['checkpoints'][-1]['status']='RUNNING'
            path=destination/unit.name/'probe-journey.json'
            path.parent.mkdir();path.write_text(json.dumps(progress))
            raise KeyboardInterrupt
        with redirect_stdout(io.StringIO()):
            report=run_cases(cases,perform,self.root/'report',['debug.Combat.UnarmedDirections'],shared=True)
        results={row['name']:row for row in report['results']}
        self.assertEqual(results['debug.Startup.DelayedSkip']['status'],'PASS')
        self.assertEqual(results['debug.Movement.ControlsAndRelease']['status'],'FAIL')
        self.assertEqual(results['debug.Combat.UnarmedDirections']['status'],'BLOCKED')
        self.assertEqual(report['exit_code'],130)
        self.assertEqual(json.loads((self.root/'report/report.json').read_text())['state'],'interrupted')

    def test_external_failure_only_blocks_dependent_shared_checkpoints(self):
        cases=self.shared_catalogue()
        calls=[]
        def perform(unit,*_):
            if not unit.checkpoints:return dict(status='PASS',reason='')
            calls.extend(unit.checkpoints)
            stop='debug.Interaction.SwordPickup' if 'debug.Interaction.SwordPickup' in unit.checkpoints else None
            return self.checkpoint_outcome(unit,stop=stop)
        with redirect_stdout(io.StringIO()):
            report=run_cases(cases,perform,self.root/'report',['debug.Interaction.PotionThenSword'],shared=True)
        results={row['name']:row for row in report['results']}
        self.assertIn('debug.Potion.TrialA',calls)
        self.assertNotIn('debug.Interaction.PotionThenSword',calls)
        self.assertEqual(results['debug.Potion.TrialA']['status'],'PASS')
        self.assertEqual(results['debug.Interaction.PotionThenSword']['status'],'BLOCKED')
        self.assertEqual(results['debug.Interaction.PotionThenSword']['evidence'],results['debug.Interaction.SwordPickup']['evidence'])

    def test_isolated_journey_details_remain_reportable(self):
        report=self.run_suite([Case('Isolated')],lambda *_:dict(status='PASS',reason='',
            journey=dict(details=dict(potion=dict(branch='poison')))))
        self.assertEqual(report['exit_code'],0)
        self.assertTrue((self.root/'report/report.xml').is_file())
        self.assertTrue((self.root/'report/report.html').is_file())

    def test_checkpoint_dispatch_reuses_workshop_sword_and_attacks(self):
        import importlib.util
        from types import SimpleNamespace
        fake_gdb=SimpleNamespace(GdbError=RuntimeError,error=RuntimeError)
        with patch.dict(sys.modules,{'gdb':fake_gdb}):
            spec=importlib.util.spec_from_file_location('contract_steps',ROOT/'scripts/e2_gameplay_steps.py')
            module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        checks=['Startup.DelayedSkip','Movement.ControlsAndRelease','Traversal.Workshop',
                'Interaction.SwordPickup','Combat.FourDirections','Combat.KillSmith','Interaction.DoorPassage']
        context=dict(value=lambda _:0,field=lambda *_:0,actor=1,prefix=str(self.root/'probe'),
                     set_phase_title=lambda _:None,checkpoint=lambda _:None)
        observer=patch('e2_population_profile.observe',return_value=dict(profile='live'))
        observer.start();self.addCleanup(observer.stop)
        journey=module.Journey(context,'shared',dict(checks=checks))
        from unittest.mock import Mock
        for method in ('startup','movement','workshop','sword','attacks','strike','release','advance','alive'):
            setattr(journey,method,Mock())
        with redirect_stdout(io.StringIO()):journey.run()
        journey.workshop.assert_called_once_with()
        journey.sword.assert_called_once_with(traverse=False)
        journey.attacks.assert_called_once_with()
        self.assertEqual(journey.strike.call_count,2)
        self.assertEqual([row['name'] for row in journey.checkpoints if not row['name'].startswith('setup.')],checks)
        # Menu is completed by the probe only after real native exit, not here.
        self.assertNotIn('Menus.CancelResumeQuit',journey.local)

    def test_courtyard_requires_central_destination_and_pedestal_floor(self):
        import importlib.util
        from types import SimpleNamespace
        fake_gdb=SimpleNamespace(GdbError=RuntimeError,error=RuntimeError,execute=lambda *_a,**_k:None)
        with patch.dict(sys.modules,{'gdb':fake_gdb}):
            spec=importlib.util.spec_from_file_location('courtyard_contract',ROOT/'scripts/e2_gameplay_steps.py')
            module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        observer=patch('e2_population_profile.observe',return_value=dict(profile='live'))
        observer.start();self.addCleanup(observer.stop)
        route=json.loads((ROOT/'scripts/scenarios/courtyard-waypoints.json').read_text())
        self.assertEqual(route['source']['session'],'session_20261026_110852_153')
        self.assertEqual(route['outward'][-1]['camera'],125)
        self.assertEqual(route['returning'][-1]['camera'],175)
        self.assertTrue(all(a['snapshot']<b['snapshot'] and a['update']<=b['update'] for a,b in zip(route['outward']+route['returning'],
                                                                 (route['outward']+route['returning'])[1:])))
        from unittest.mock import Mock
        for failure in (None,'displaced start','occupied stairs','clearance input selector','central camera','return floor','return location'):
            with self.subTest(failure=failure):
                state=dict(camera=175,position=list(route['outward'][0]['position']))
                if failure=='displaced start':state['position']=[9085,3712,-16443]
                context=dict(value=lambda _:293 if failure=='occupied stairs' else 0,
                             field=lambda offset:state['position'][1] if offset==0x86 else 100,
                             actor=1,prefix=str(self.root/'probe'),set_phase_title=lambda _:None,checkpoint=lambda _:None)
                diagnostic=failure=='clearance input selector'
                journey=module.Journey(context,'courtyard',dict(courtyard_stair_clearance=diagnostic))
                returning=route['returning']
                if failure in ('occupied stairs','clearance input selector'):
                    clearance=route['stair_clearance']
                    returning=[row for row in returning if row['snapshot']<clearance['gate_snapshot']]+[
                        dict(snapshot=None,camera=175,position=[x,3328,z]) for x,z in clearance['waypoints']]
                approach=([dict(snapshot=None,camera=175,position=[x,3328,z])
                           for x,z in route['stair_clearance']['waypoints']] if failure=='displaced start' else [])
                expected_points=approach+route['outward']+returning
                points=iter(expected_points);visited=[]
                def walk(targets,*,on_waypoint=None):
                    for index,target in enumerate(targets):
                        row=next(points);visited.append(row)
                        self.assertEqual(tuple(target),(row['position'][0],row['position'][2]))
                        state.update(camera=row['camera'],position=list(row['position']))
                        if row is route['outward'][-1] and failure=='central camera':state['camera']=166
                        if row is route['returning'][-1]:
                            if failure=='return floor':state['position'][1]=4096
                            if failure=='return location':state['position'][0]+=1000
                        if on_waypoint:on_waypoint(index)
                journey.walk=walk;journey.camera=lambda:state['camera']
                journey.position=lambda actor=None: [9365,3584,-16348] if actor==293 else list(state['position'])
                journey.alive=Mock();journey.release=Mock();journey.advance=Mock()
                with redirect_stdout(io.StringIO()):
                    if failure not in (None,'displaced start','occupied stairs','clearance input selector'):
                        with self.assertRaises(RuntimeError):journey.courtyard()
                    else:
                        journey.courtyard()
                        self.assertEqual(len(visited),len(expected_points))
                        self.assertEqual(len(journey.details['courtyard']['returning']),len(returning))
                        details=journey.details['courtyard']['stair_clearance']
                        self.assertEqual(details['used'],failure in ('occupied stairs','clearance input selector'))
                        self.assertEqual(details['diagnostic'],diagnostic)
                        self.assertEqual(details['occupied'],failure=='occupied stairs')
                with self.assertRaises(ValueError):module.Journey(context,'courtyard',dict(courtyard_stair_clearance='true'))

    def test_courtyard_keeps_shared_startup_and_movement_assertions(self):
        cases=self.shared_catalogue()
        units=journey_plan(cases,block_patterns(cases,'movement'))
        live=[unit for unit in units if unit.kind=='journey']
        self.assertEqual(len(live),1)
        courtyard=next(unit for unit in live if 'debug.Traversal.CourtyardReturn' in unit.checkpoints)
        route=json.loads((ROOT/'scripts/scenarios/courtyard-waypoints.json').read_text())
        self.assertEqual(route['source']['intro_skip_progress'],438)
        self.assertEqual(courtyard.checkpoints,('debug.Startup.DelayedSkip','debug.Movement.ControlsAndRelease','debug.Traversal.CourtyardReturn'))
        self.assertNotIn('intro_skip_progress',live[0].options)
        # Human timing is provenance, not state restoration. Isolated diagnosis
        # still uses the same declared progress-83 startup as shared execution.
        pinned=self.root/'debug.Build/e2recomp';pinned.parent.mkdir();pinned.write_bytes(b'pinned')
        result={'debug.Build':dict(binary=dict(sha256=digest(pinned)))}
        target=next(case for case in cases if case.name=='debug.Traversal.CourtyardReturn')
        with patch('e2_suite.execute',return_value=dict(status='FAIL',reason='contract stub')) as perform:
            executor(Path('/external'))(target,self.root,result)
        command=perform.call_args.args[0]
        self.assertEqual(command[command.index('--intro-skip-progress')+1],'83')
        self.assertNotIn('intro_skip_progress',json.loads(command[command.index('--suite-options')+1]))


    def test_shared_setup_failure_blocks_target_without_erasing_prior_pass(self):
        cases=self.shared_catalogue()
        unit=next(unit for unit in journey_plan(cases) if unit.checkpoints and
                  'debug.Potion.TrialD' in unit.checkpoints)
        outcome=self.checkpoint_outcome(unit)
        # The fresh process can lose a prerequisite already passed elsewhere.
        outcome['status']='FAIL';outcome['reason']='fresh natural damage not observed'
        outcome['progress']['checkpoints'][-1]['status']='FAIL'
        outcome['progress']['checkpoints'].append(dict(name='setup.Combat.TakeDamage',status='FAIL',reason='no hit',parent='Potion.TrialD'))
        rows=shared_results(unit,outcome,{case.name:case for case in cases})
        trial=next(row for row in rows if row['name']=='debug.Potion.TrialD')
        self.assertEqual(trial['status'],'BLOCKED')
        self.assertEqual(trial['root_causes'],[unit.name+'::setup.Combat.TakeDamage'])

    def test_shared_timeout_retains_journal_and_fails_active_checkpoint(self):
        cases=self.shared_catalogue()
        def perform(unit,destination,*_):
            if not unit.checkpoints:return dict(status='PASS',reason='')
            directory=destination/unit.name
            directory.mkdir()
            journal=directory/'probe-journey.json'
            progress=self.checkpoint_outcome(unit,stop='debug.Movement.ControlsAndRelease')['progress']
            progress['checkpoints'][-1]['status']='RUNNING'
            code=('import pathlib,time; '+f'pathlib.Path({str(journal)!r}).write_text({json.dumps(progress)!r}); '
                  'print("checkpoint retained",flush=True); time.sleep(60)')
            return execute((sys.executable,'-c',code),directory,.3)
        with redirect_stdout(io.StringIO()):
            report=run_cases(cases,perform,self.root/'report',['debug.Combat.UnarmedDirections'],shared=True)
        rows={row['name']:row for row in report['results']}
        self.assertEqual(rows['debug.Startup.DelayedSkip']['status'],'PASS')
        self.assertEqual(rows['debug.Movement.ControlsAndRelease']['status'],'FAIL')
        self.assertEqual(rows['debug.Combat.UnarmedDirections']['status'],'BLOCKED')
        self.assertTrue(report['journeys'][0]['timeout'])
        self.assertEqual(report['exit_code'],1)

    def test_shared_random_coverage_keeps_checkpoint_provenance(self):
        trial=dict(name='debug.Potion.TrialA',status='PASS',journey='debug.Journey.PotionA',
                   checkpoint='Potion.TrialA',evidence='debug.Journey.PotionA/probe-journey.json',
                   observations=dict(potion=dict(branch='poison',before_health=100)))
        case=Case('debug.Potion.Branch.poison',kind='coverage',options=dict(branch='poison',trials=[trial['name']]))
        result=executor(Path('/external'))(case,self.root,{trial['name']:trial})
        self.assertEqual(result['status'],'PASS')
        self.assertEqual(result['journey'],trial['journey'])
        self.assertEqual(result['evidence'],trial['evidence'])
        self.assertEqual(result['source_checkpoint'],'Potion.TrialA')
        self.assertEqual(result['checkpoint'],'Potion.Branch.poison')

    def test_menu_matrix_covers_stages_once_and_exposes_unfinished_effects(self):
        from e2_suite import MENU_CHECKS, MENU_STAGES, MENU_UNFINISHED
        cases=self.shared_catalogue()
        units=journey_plan(cases,block_patterns(cases,'menus'))
        live=[unit for unit in units if unit.kind=='journey']
        self.assertEqual(len(live),1)
        self.assertEqual(live[0].scenario,'menu-matrix')
        self.assertEqual(set(live[0].options['checks']),{'Startup.DelayedSkip',*MENU_CHECKS})
        for stage in MENU_STAGES:
            for action in ('ShowHide','StartGame','MusicToggle','SoundToggle','Difficulty','LoadDialog','SaveDialog'):
                self.assertIn('debug.Menus.'+stage+'.'+action,live[0].checkpoints)
            for action in MENU_UNFINISHED:
                case=next(case for case in cases if case.name=='debug.Menus.'+stage+'.'+action)
                self.assertTrue(case.skip)
                self.assertFalse(case.required)

    def test_multiple_independent_menu_failures_and_skips_survive_clean_exit(self):
        cases=self.shared_catalogue()
        names=['debug.Menus.Intro.'+action for action in ('ShowHide','MusicToggle','SoundToggle','ResolutionToggle')]
        def perform(unit,*_):
            if not unit.checkpoints:return dict(status='PASS',reason='')
            outcome=self.checkpoint_outcome(unit)
            for row in outcome['progress']['checkpoints']:
                row.update(status='FAIL' if row['name'].endswith(('MusicToggle','SoundToggle')) else
                           'SKIPPED' if row['name'].endswith('ResolutionToggle') else 'PASS',reason='observed option failure')
            return outcome
        with redirect_stdout(io.StringIO()):
            report=run_cases(cases,perform,self.root/'report',names,shared=True)
        rows={row['name']:row for row in report['results']}
        self.assertEqual([rows[name]['status'] for name in names],['PASS','FAIL','FAIL','SKIPPED'])
        self.assertEqual(report['journeys'][0]['status'],'FAIL')
        self.assertEqual(report['exit_code'],1)

    def test_menu_fault_does_not_own_unrelated_gameplay_startup(self):
        cases=self.shared_catalogue()
        patterns=['debug.Menus.Intro.LoadDialog','debug.Movement.ControlsAndRelease']
        units=journey_plan(cases,patterns)
        menu=next(unit for unit in units if unit.scenario=='menu-matrix')
        self.assertNotIn('debug.Startup.DelayedSkip',menu.checkpoints)
        self.assertEqual(sum('debug.Startup.DelayedSkip' in unit.checkpoints for unit in units),1)
        def perform(unit,*_):
            if not unit.checkpoints:return dict(status='PASS',reason='')
            return self.checkpoint_outcome(unit,stop=menu.checkpoints[0] if unit.name==menu.name else None)
        with redirect_stdout(io.StringIO()):report=run_cases(cases,perform,self.root/'report',patterns,shared=True)
        rows={row['name']:row for row in report['results']}
        self.assertEqual(rows['debug.Menus.Intro.LoadDialog']['status'],'FAIL')
        self.assertEqual(rows['debug.Startup.DelayedSkip']['status'],'PASS')
        self.assertEqual(rows['debug.Movement.ControlsAndRelease']['status'],'PASS')

    def fake_worker(self, lane, names, destination, crash=None):
        # Real subprocesses exercise concurrent execution, not mocked Popen.
        script=self.root/(lane+'.worker.py')
        script.write_text('''import json, os, pathlib, signal, sys, time
sys.path.insert(0, sys.argv[1])
from e2_suite import write_reports
spec=json.loads(sys.argv[2]); destination=pathlib.Path(spec['output']); destination.mkdir()
rows=[dict(name=name,status='PASS',required=True,seconds=.01,reason='',artifacts='unit',evidence='unit/probe.json') for name in spec['names']]
report=dict(schema='e2suite.result.2',state='running',metadata={},results=rows[:1],journeys=[],seconds=0)
write_reports(destination,report)
if spec.get('crash')=='after-complete':
    report.update(state='complete',exit_code=0,results=rows)
    write_reports(destination,report); os._exit(7)
if spec.get('crash'):
    unit=spec['crash']; folder=destination/unit['name']; folder.mkdir()
    checkpoints=[dict(name=name.split('.',1)[1],status='PASS' if index==0 else 'RUNNING',phase_start=0,phase_end=1,seconds=.01) for index,name in enumerate(unit['checks'][:2])]
    (folder/'probe-journey.json').write_text(json.dumps(dict(checkpoints=checkpoints)))
    os._exit(7)
def interrupt(*_):
    report.update(state='interrupted',exit_code=130,results=rows[:1]+[dict(row,status='SKIPPED',reason='Interrupted') for row in rows[1:]])
    write_reports(destination,report); sys.exit(130)
signal.signal(signal.SIGINT,interrupt)
time.sleep(.35)
report.update(state='complete',exit_code=0,results=rows)
write_reports(destination,report)
''')
        spec=dict(output=str(destination),names=names,crash=crash)
        return [sys.executable,str(script),str(ROOT/'scripts'),json.dumps(spec)]

    def test_parallel_overlap_shared_once_and_merged_evidence(self):
        cases=[Case('Source'),Case('debug.A',configuration='debug'),Case('asan.A',configuration='asan')]
        calls=[]
        def command(lane,names,destination):
            calls.append(lane)
            return self.fake_worker(lane,names,destination)
        with redirect_stdout(io.StringIO()):
            report=run_lanes(cases,['*'],self.root/'report',{},command)
        self.assertEqual(calls,['shared','debug','asan'])
        lanes={row['name']:row for row in report['lanes']}
        self.assertLess(lanes['asan']['start_seconds'],lanes['debug']['end_seconds'])
        self.assertLess(lanes['debug']['start_seconds'],lanes['asan']['end_seconds'])
        self.assertGreaterEqual(lanes['debug']['start_seconds'],lanes['shared']['end_seconds'])
        rows={row['name']:row for row in report['results']}
        self.assertEqual(rows['debug.A']['evidence'],'debug/unit/probe.json')
        self.assertEqual(rows['asan.A']['artifacts'],'asan/unit')
        self.assertEqual(report['exit_code'],0)
        self.assertEqual(len(ET.parse(self.root/'report/report.xml').getroot().findall('testcase')),3)
        self.assertTrue((self.root/'report/report.html').is_file())

    def test_parallel_crash_preserves_checkpoint_pass_and_other_configuration(self):
        cases=catalogue(['debug','asan'],Path('/external'))
        patterns=['debug.Combat.UnarmedDirections','asan.Startup.EarlySkip']
        unit=next(unit for unit in journey_plan(cases,patterns) if unit.configuration=='debug' and unit.checkpoints)
        def command(lane,names,destination):
            crash=dict(name=unit.name,checks=unit.checkpoints) if lane=='debug' else None
            return self.fake_worker(lane,names,destination,crash)
        with redirect_stdout(io.StringIO()):
            report=run_lanes(cases,patterns,self.root/'report',{},command)
        rows={row['name']:row for row in report['results']}
        self.assertEqual(rows['debug.Startup.DelayedSkip']['status'],'PASS')
        self.assertEqual(rows['debug.Movement.ControlsAndRelease']['status'],'FAIL')
        self.assertEqual(rows['debug.Combat.UnarmedDirections']['status'],'BLOCKED')
        self.assertEqual(rows['asan.Startup.EarlySkip']['status'],'PASS')
        self.assertEqual(rows['debug.Startup.DelayedSkip']['evidence'],'debug/'+unit.name+'/probe-journey.json')
        self.assertEqual(report['exit_code'],1)
        self.assertTrue(any(row['name']=='debug.Runner' and row['status']=='FAIL' for row in report['journeys']))

    def test_parallel_interrupt_and_spawn_error_write_final_reports(self):
        cases=[Case('debug.A',configuration='debug'),Case('debug.B',configuration='debug'),
               Case('asan.A',configuration='asan')]
        real_sleep=time.sleep
        calls=0
        def interrupt_once(seconds):
            nonlocal calls
            calls+=1
            if calls==1:
                real_sleep(.15)
                raise KeyboardInterrupt
            real_sleep(seconds)
        with redirect_stdout(io.StringIO()), patch('e2_suite_parallel.time.sleep',side_effect=interrupt_once):
            report=run_lanes(cases,['*'],self.root/'interrupted',{},self.fake_worker)
        self.assertEqual(report['exit_code'],130)
        self.assertEqual(report['state'],'interrupted')
        self.assertEqual(next(row for row in report['results'] if row['name']=='debug.A')['status'],'PASS')
        self.assertTrue(all(row['returncode'] is not None for row in report['lanes']))
        with redirect_stdout(io.StringIO()):
            report=run_lanes(cases,['*'],self.root/'spawn-error',{},lambda *_:['/no/such/worker'])
        self.assertEqual(report['exit_code'],1)
        self.assertEqual(report['state'],'complete')
        self.assertEqual(report['journeys'][0]['name'],'Suite.Coordinator')

    def test_parallel_crash_after_passes_still_fails_overall(self):
        cases=[Case('debug.A',configuration='debug'),Case('asan.A',configuration='asan')]
        def command(lane,names,destination):
            return self.fake_worker(lane,names,destination,'after-complete' if lane=='debug' else None)
        with redirect_stdout(io.StringIO()):report=run_lanes(cases,['*'],self.root/'report',{},command)
        self.assertTrue(all(row['status']=='PASS' for row in report['results']))
        self.assertEqual(report['exit_code'],1)
        self.assertEqual(report['journeys'][0]['status'],'FAIL')
        xml=ET.parse(self.root/'report/report.xml').getroot()
        self.assertEqual(xml.attrib['failures'],'1')

    def test_parallel_display_and_dependency_boundaries(self):
        for configuration in ('debug','asan'):
            self.assertEqual(configuration_display('headless',configuration),'headless')
            self.assertEqual(configuration_display('visible-both',configuration),'visible')
            self.assertEqual(configuration_display('visible',configuration),'visible')
            self.assertEqual(configuration_display('visible-'+configuration,configuration),'visible')
        self.assertEqual(configuration_display('visible-debug','asan'),'headless')
        self.assertEqual(configuration_display('visible-asan','debug'),'headless')
        cases=[Case('debug.A',configuration='debug'),Case('asan.A',configuration='asan',requires=('debug.A',))]
        with self.assertRaises(ValueError):run_lanes(cases,['*'],self.root/'invalid',{},self.fake_worker)

    def test_parallel_full_catalogue_can_be_selected_by_each_child(self):
        cases=catalogue(['debug','asan'],Path('/external'))
        groups={}
        for case in cases:groups.setdefault(case.configuration or 'shared',[]).append(case.name)
        for lane,names in groups.items():
            child=ordered(catalogue([lane if lane!='shared' else 'debug'],Path('/external')))
            self.assertEqual(selection(child,names),set(names))
            if lane!='shared':self.assertTrue(all(name.startswith(lane+'.') for name in names))

    def test_isolated_menu_retains_skip_and_failed_lifecycle(self):
        cases=self.shared_catalogue()
        def perform(unit,*_):
            if not unit.checkpoints:return dict(status='PASS',reason='')
            outcome=self.checkpoint_outcome(unit,crash=True)
            outcome['progress']['checkpoints'][0].update(status='SKIPPED',reason='Renderer unaccepted')
            return outcome
        with redirect_stdout(io.StringIO()):
            report=run_cases(cases,perform,self.root/'report',['debug.Menus.Intro.ResolutionToggle'])
        logical=next(row for row in report['results'] if row['name'].endswith('.ResolutionToggle'))
        self.assertEqual(logical['status'],'SKIPPED')
        self.assertEqual(report['journeys'][0]['status'],'FAIL')
        self.assertEqual(report['exit_code'],1)

    def test_menu_route_keeps_restart_order_and_boundaries(self):
        import importlib.util
        import types
        spec=importlib.util.spec_from_file_location('menu_contract',ROOT/'scripts/e2_menu_steps.py')
        module=importlib.util.module_from_spec(spec)
        with patch.dict(sys.modules,{'gdb':types.SimpleNamespace(GdbError=RuntimeError)}):spec.loader.exec_module(module)
        journey=module.MenuJourney.__new__(module.MenuJourney)
        journey.checks=['Menus.Intro.StartGame','Menus.Pedestal.StartGame','Menus.Gameplay.StartGame']
        journey.rows=[];journey.phases=[];journey.inputs=[];journey.details={};journey.states=[]
        journey.updates=0;journey.stage='Intro';journey.complete=False;journey.prefix=str(self.root/'probe')
        journey.frame=None;journey.game_data=None;journey.watch=False;journey.title='contract'
        journey.logo_delay=0;journey.logo_skip=True
        from unittest.mock import Mock
        calls=[]
        def restart(stage):calls.append('restart.'+stage)
        def reach(stage):journey.stage=stage;calls.append('reach.'+stage)
        from contextlib import contextmanager
        @contextmanager
        def checkpoint(_):yield
        journey.checkpoint=checkpoint
        journey.require=lambda condition,message: self.assertTrue(condition,message)
        journey.state=lambda _:dict(identity=0,health=100)
        journey.HORSE='condition'
        journey.stage_checks=lambda stage:calls.append('checks.'+stage)
        journey.restart_checked=restart
        journey.reach_pedestal=lambda:reach('Pedestal')
        journey.reach_gameplay=lambda:reach('Gameplay')
        journey.quit=lambda **_:calls.append('quit')
        journey.finish=lambda:None
        gdb_mock=types.SimpleNamespace(Breakpoint=Mock(),execute=Mock(),selected_frame=lambda:types.SimpleNamespace(name=lambda:'FUN_00415d40'))
        with patch.object(module,'gdb',gdb_mock):journey.run()
        self.assertEqual(calls,['checks.Intro','restart.Intro','reach.Pedestal','checks.Pedestal','restart.Pedestal',
                               'reach.Gameplay','checks.Gameplay','restart.Gameplay','quit'])

    def test_native_failure_identifies_stopped_thread_and_sanitizer_leaf(self):
        pinned=self.root/'debug.Build/e2recomp'
        pinned.parent.mkdir();pinned.write_bytes(b'pinned')
        case=Case('debug.Menu',kind='journey',configuration='debug',scenario='menus')
        results={'debug.Build':dict(binary=dict(sha256=digest(pinned)))}
        for log,expected in (
                ('Thread 1 received signal SIGSEGV, fault.\n0x123 in FUN_0043a39c (x=1) at recon.c:31219\n'
                 'Thread 2:\n#0 0x456 in __kernel_vsyscall ()\n','FUN_0043a39c'),
                ('ERROR: AddressSanitizer: stack-buffer-overflow on address 0x123\nWRITE of size 1\n'
                 '    #0 0x123 in FUN_0043ce58 recon.c:33786\n','FUN_0043ce58')):
            def failure(command,directory,*_):
                directory.mkdir(exist_ok=True)
                (directory/'probe.log').write_text(log)
                return dict(status='FAIL',reason='Native failure')
            with patch('e2_suite.execute',side_effect=failure):result=executor(Path('/external'))(case,self.root,results)
            self.assertEqual(result['native_failure']['function'],expected)
            self.assertEqual(result['status'],'FAIL')


if __name__=='__main__':
    unittest.main(verbosity=2)
