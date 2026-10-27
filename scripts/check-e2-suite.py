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
                               ('Interaction.DoorPassageDisplaced','live'),
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

    def test_random_potion_outcomes_are_optional_and_do_not_require_rng_luck(self):
        cases=self.shared_catalogue()
        coverage=[case for case in cases if case.kind=='coverage']
        self.assertEqual(len(coverage),4)
        self.assertTrue(all(not case.required for case in coverage))
        trial=dict(name='Trial',status='PASS',observations=dict(potion=dict(branch='noop',before_health=85)))
        perform=executor(Path('/unneeded'))
        checks=[Case('Observed.'+branch,kind='coverage',required=False,
                     options=dict(branch=branch,trials=['Trial']))
                for branch in ('healing','poison','invisibility','noop')]
        report=self.run_suite(checks,lambda case,dest,_:perform(case,dest,{'Trial':trial}))
        self.assertEqual(report['exit_code'],0)
        self.assertEqual(report['counts']['PASS'],1)
        self.assertEqual(report['counts']['SKIPPED'],3)

    def potion_module(self):
        import importlib.util
        from types import SimpleNamespace
        fake_gdb=SimpleNamespace(GdbError=RuntimeError,error=RuntimeError)
        with patch.dict(sys.modules,{'gdb':fake_gdb}):
            spec=importlib.util.spec_from_file_location('potion_contract',ROOT/'scripts/e2_gameplay_steps.py')
            module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        return module

    def test_consumption_accepts_each_natural_effect_including_no_change(self):
        failure=self.potion_module().potion_failure
        for branch,script,action,timers,after in (
            ('healing',156,391,[],100),('poison',183,409,[5],85),
            ('invisibility',157,383,[387],85),('noop',1803,369,[],85)):
            row=dict(branch=branch,before_health=85,after_health=after,scripts=[189,script],
                     actions=[369,action],timers=[dict(action=a) for a in timers],samples=[
                         dict(attached_to_joe=True,attachment=1,representation=2),
                         dict(attached_to_joe=False,attachment=0,representation=0)])
            self.assertIsNone(failure(row),branch)
            row['actions']=[0xf7370000 | action for action in row['actions']]
            self.assertIsNone(failure(row),'Upper word is outside the original short action ID')
            if branch=='healing':
                row['before_health']=100
                self.assertIsNone(failure(row),'Already healthy is valid consumption')
            row['samples'][-1]['attachment']=1
            self.assertIn('remains attached',failure(row))
            row['samples'][-1]['attachment']=0
            row['samples'][0]['attached_to_joe']=False
            self.assertIn('pickup and drinking',failure(row))

    def test_consumption_rejects_missing_or_contradictory_effect(self):
        failure=self.potion_module().potion_failure
        row=dict(branch='poison',before_health=85,after_health=85,scripts=[189,183],
                 actions=[369,409],timers=[],samples=[
                     dict(attached_to_joe=True,attachment=1,representation=2),
                     dict(attached_to_joe=False,attachment=0,representation=0)])
        self.assertIn('death timer missing',failure(row))
        row.update(branch='healing',scripts=[189,156],actions=[369,391])
        self.assertIn('maximum health',failure(row))
        row.update(branch='noop',scripts=[189,1803],after_health=100)
        self.assertIn('no-op changed',failure(row))
        row.update(after_health=85,scripts=[189,1803,156])
        self.assertIn('not uniquely observed',failure(row))

    def test_potion_corridor_joins_actual_floor_after_a_hit(self):
        from unittest.mock import Mock
        module=self.potion_module();journey=module.Journey.__new__(module.Journey)
        journey.details={};journey.save=lambda:None;journey.scene_map=lambda:'actual scene'
        for start in ([8814,4096,-16965],[8566,4096,-17229],[10000,3328,-16910],[3611,4096,-17894]):
            journey.position=lambda:list(start)
            navigator=Mock()
            journey.workshop_corridor(navigator)
            path=navigator.follow_route.call_args.args[0]
            if journey.details['workshop_entry']['distance']>=4000:
                navigator.navigate.assert_called_once_with('actual scene',path[0])
            else:navigator.navigate.assert_not_called()
            self.assertLessEqual(abs(path[0][1]-start[1]),300)
            self.assertEqual(path[-1],[2350,4096,-10889])
            if start[1]==4096:self.assertNotEqual(path[0][0],9736)

    def test_encounter_corridor_uses_live_scene_join_after_displaced_movement(self):
        from unittest.mock import Mock
        module=self.potion_module();journey=module.Journey.__new__(module.Journey)
        journey.details={};journey.save=lambda:None;journey.scene_map=lambda:'actual scene'
        for start in ([7854,3328,-18678],[9733,3328,-16943],[5729,4096,-16430]):
            journey.position=lambda:list(start)
            navigator=Mock();journey.encounter_corridor(navigator)
            path=navigator.follow_route.call_args.args[0]
            self.assertEqual(path[0][1],start[1])
            if journey.details['encounter_entry']['distance']>=1800:
                navigator.navigate.assert_called_once_with('actual scene',path[0])
            else:navigator.navigate.assert_not_called()
        journey.position=lambda:[7854,10000,-18678]
        with self.assertRaisesRegex(RuntimeError,'No observed floor'):journey.encounter_corridor(Mock())

    def test_potion_to_sword_keeps_consumed_bottle_removed(self):
        from unittest.mock import Mock
        module=self.potion_module();journey=module.Journey.__new__(module.Journey)
        journey.name='potion-sword'
        journey.phase=lambda _:__import__('contextlib').nullcontext()
        navigator=Mock();journey.navigator=Mock(return_value=navigator)
        journey.scene_map=Mock(return_value='observed workshop floors')
        journey.sword=Mock();journey.attacks=Mock();journey.actor_by_id=lambda _:537
        for condition in ('pass','attached','represented'):
            journey.value=lambda expr:int(condition=='attached' and '+0xf2' in expr or
                                          condition=='represented' and '+0x11e' in expr)
            if condition=='pass':journey.potion_then_sword()
            else:
                with self.assertRaisesRegex(RuntimeError,'restored the consumed bottle'):journey.potion_then_sword()
        self.assertEqual(navigator.navigate.call_args.args,('observed workshop floors',[-871,4096,-10006]))
        self.assertEqual(navigator.navigate.call_args.kwargs,dict(avoid_actors=True))
        navigator.follow_route.assert_not_called()
        self.assertEqual(journey.sword.call_args.kwargs,dict(traverse=False))
        self.assertEqual(journey.attacks.call_count,3)

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

    def test_replay_display_is_explicit_for_each_configuration(self):
        pinned=self.root/'debug.Build/e2recomp'
        pinned.parent.mkdir();pinned.write_bytes(b'pinned executable')
        case=Case('debug.Replay.1',kind='replay',configuration='debug',timeout=180,
                  options=dict(source='/recording/replay',specification='/scenario.json'))
        results={'debug.Build':dict(binary=dict(sha256=digest(pinned)))}
        for driver in ('dummy','x11','wayland'):
            with patch('e2_suite.execute',return_value=dict(status='FAIL',reason='contract stub')) as call:
                executor(Path('/external'),driver)(case,self.root,results)
            command=call.call_args.args[0]
            self.assertEqual(command[command.index('--video-driver')+1],driver)
            self.assertIn('--compatible',command)
            self.assertEqual(call.call_args.args[3]['SDL_VIDEODRIVER'],driver)

    def test_replay_launcher_preserves_recording_and_overrides_display(self):
        import csv
        # Incomplete synthetic input only tests launcher policy; this executable
        # never runs the native parser or establishes gameplay replay acceptance.
        source=self.root/'replay';source.mkdir()
        with (source/'metadata.csv').open('w',newline='') as stream:
            csv.writer(stream).writerows([['key','value'],['schema','e2replay.csv.1'],
                ['game_data_path',str(self.root)],['env.SDL_VIDEODRIVER','x11'],['env.E2R_RECORD','1']])
        (source/'events.csv').write_text('seq,kind\n')
        (source/'checkpoints.csv').write_text('seq,kind\n')
        (source/'recording.incomplete').write_text('launcher fixture; not a complete recording\n')
        original={path.name:digest(path) for path in source.iterdir()}
        executable=self.root/'launcher-fixture'
        executable.write_text('''#!/usr/bin/env python3
import hashlib,json,os,sys
from pathlib import Path
source=Path(sys.argv[sys.argv.index('--replay')+1])
destination=Path(sys.argv[sys.argv.index('--data-dir')+1]);destination.mkdir(parents=True)
(destination/'launch.json').write_text(json.dumps(dict(driver=os.environ.get('SDL_VIDEODRIVER'),
    recording=os.environ.get('E2R_RECORD'),inspect=os.environ.get('E2R_INSPECT'),
    hashes={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in source.iterdir()})))
''')
        executable.chmod(0o755)
        for driver in (None,'dummy'):
            destination=self.root/('default' if driver is None else driver)
            command=[sys.executable,str(ROOT/'scripts/replay-e2.py'),'run',str(executable),str(source),
                     '--inspect','--data-dir',str(destination),'--timeout','10']
            if driver:command+=['--video-driver',driver]
            result=subprocess.run(command,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,timeout=15)
            self.assertEqual(result.returncode,0,result.stdout)
            launch=json.loads((destination/'launch.json').read_text())
            self.assertEqual(launch,dict(driver=driver or 'x11',recording='off',inspect='1',hashes=original))
            self.assertEqual({path.name:digest(path) for path in source.iterdir()},original)

        specification=self.root/'scenario.json'
        specification.write_text(json.dumps(dict(schema='e2debug.scenario.1',
            assertions=[dict(scope='world',entity_id=0,field='camera',value=175)])))
        destination=self.root/'scenario'
        result=subprocess.run([sys.executable,str(ROOT/'scripts/e2-debug.py'),'scenario',str(executable),
            str(source),str(specification),str(destination),'--video-driver','dummy','--timeout','10'],
            stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,timeout=20)
        self.assertEqual(result.returncode,1,result.stdout)
        report=json.loads((destination/'result.json').read_text())
        self.assertEqual(report['video_driver_override'],'dummy')
        self.assertFalse(report['passed'])
        self.assertFalse(report['inspection_complete'])
        self.assertEqual(json.loads((destination/'runtime/launch.json').read_text())['driver'],'dummy')
        self.assertEqual({path.name:digest(path) for path in source.iterdir()},original)

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
        expected=['checks','startup','menus','movement','unarmed','workshop','swimming','potions','stability','replay','persistence']
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
        self.assertEqual(len(names),233)
        self.assertIn('debug.Original.ActorEviction',names)
        self.assertIn('asan.Original.ActorEviction',names)
        self.assertEqual(sum(unit.kind=='journey' for unit in cases),108)
        self.assertEqual(sum(unit.kind=='journey' for unit in units),26)
        for unit in units:
            if unit.checkpoints:
                self.assertTrue(all(name.startswith(unit.configuration+'.') for name in unit.checkpoints))

    def test_navigation_setup_failure_blocks_damage_and_fails_lifecycle(self):
        cases=self.shared_catalogue()
        units=journey_plan(cases,['debug.Combat.TakeDamage'])
        unit=next(unit for unit in units if unit.kind=='journey')
        def perform(active,*_):
            if active.kind!='journey':return dict(status='PASS')
            rows=[dict(name='Startup.DelayedSkip',status='PASS',phase_start=0,phase_end=1,details={}),
                  dict(name='Movement.ControlsAndRelease',status='PASS',phase_start=1,phase_end=2,details={}),
                  dict(name='Combat.TakeDamage',status='FAIL',parent=None),
                  dict(name='setup.ReceiveHitEncounter',status='FAIL',parent='Combat.TakeDamage',
                       reason='height mismatch; connected route required')]
            return dict(status='FAIL',reason='height mismatch; connected route required',
                        progress=dict(checkpoints=rows,details=dict(navigation=[dict(outcome='FAIL',
                            reason='height mismatch',target=284,replans=0)])))
        with redirect_stdout(io.StringIO()):
            report=run_cases(cases,perform,self.root/'report',['debug.Combat.TakeDamage'],shared=True)
        results={row['name']:row for row in report['results']}
        self.assertEqual(results['debug.Movement.ControlsAndRelease']['status'],'PASS')
        self.assertEqual(results['debug.Combat.TakeDamage']['status'],'BLOCKED')
        self.assertEqual(results['debug.Combat.TakeDamage']['root_causes'],[unit.name+'::setup.ReceiveHitEncounter'])
        self.assertEqual(report['journeys'][0]['status'],'FAIL')
        self.assertEqual(report['journeys'][0]['progress']['details']['navigation'][0]['target'],284)
        self.assertEqual(report['exit_code'],1)
        self.assertIn('height mismatch',(self.root/'report/report.html').read_text())
        self.assertIn('BLOCKED',(self.root/'report/report.xml').read_text())

    def test_shared_prerequisites_and_distinct_routes(self):
        cases=self.shared_catalogue()
        workshop=journey_plan(cases,block_patterns(cases,'workshop'))
        live=[unit for unit in workshop if unit.checkpoints]
        self.assertEqual(len(live),2)
        self.assertIn('debug.Movement.ControlsAndRelease',live[0].checkpoints)
        self.assertIn('debug.Combat.KillSmith',live[0].checkpoints)
        self.assertNotIn('debug.Combat.UnarmedDirections',live[0].checkpoints)
        displaced=next(unit for unit in live if 'debug.Interaction.DoorPassageDisplaced' in unit.checkpoints)
        self.assertNotIn('debug.Interaction.DoorPassage',displaced.checkpoints)
        self.assertTrue(displaced.options['displaced_door_start'])
        self.assertTrue(displaced.options['observe_door_health'])
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

    def test_live_unarmed_contact_cannot_consume_the_later_fresh_door_setup(self):
        cases=self.shared_catalogue()
        patterns=['debug.Combat.UnarmedContact','debug.Interaction.DoorPassage']
        units=[unit for unit in journey_plan(cases,patterns) if unit.checkpoints]
        unarmed=next(unit for unit in units if 'debug.Combat.UnarmedContact' in unit.checkpoints)
        door=next(unit for unit in units if 'debug.Interaction.DoorPassage' in unit.checkpoints)
        self.assertNotEqual(unarmed.name,door.name)
        self.assertTrue(door.options['observe_door_health'])
        self.assertIn('debug.Combat.FourDirections',door.checkpoints)
        self.assertIn('debug.Interaction.SwordPickup',door.checkpoints)
        def execute(unit,*_):
            if not unit.checkpoints:return dict(status='PASS',reason='')
            fresh_door=True
            for name in unit.checkpoints:
                if name.endswith('Combat.UnarmedContact'):fresh_door=False
                if name.endswith('Interaction.DoorPassage') and not fresh_door:
                    return self.checkpoint_outcome(unit,stop=name)
            return self.checkpoint_outcome(unit)
        with redirect_stdout(io.StringIO()):
            report=run_cases(cases,execute,self.root/'report',patterns,shared=True)
        self.assertEqual(report['exit_code'],0)
        self.assertTrue(all(row['status']=='PASS' for row in report['results']))

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

    def test_smith_kill_tracks_retreat_and_preserves_fixed_target_and_death_assertions(self):
        from types import SimpleNamespace
        from unittest.mock import Mock
        module=self.potion_module()
        module.gdb.execute=lambda *_a,**_k:None
        observer=patch('e2_population_profile.observe',return_value=dict(profile='live'))
        observer.start();self.addCleanup(observer.stop)
        for condition in ('pass','intact','still represented','replaced'):
            state=dict(health=100,state=2,representation=1,player=[0,4096,0],
                       target=[300,4096,0],faced=None,held=set(),updates=0,bouts=0)
            def value(expression):
                if expression=='DAT_0047a470':return 1
                if expression=='_DAT_00643650':return 0
                for offset,key in ((0xec,'health'),(0x82,'state'),(0x11e,'representation')):
                    if expression in (f'*(short*)(602+{offset:#x})',f'*(unsigned int*)(602+{offset:#x})'):
                        return state[key]
                raise AssertionError(expression)
            context=dict(value=value,field=lambda *_:100,actor=1,prefix=str(self.root/'smith'),
                         set_phase_title=lambda _:None,checkpoint=lambda _:None)
            journey=module.Journey(context,'enemy',{})
            journey.actor_by_id=lambda identity:identity+int(condition=='replaced' and state['bouts']>0)
            journey.position=lambda actor=None:list(state['player'] if actor is None else state['target'])
            journey.walk=Mock()
            def face(_):state['faced']=list(state['target'])
            journey.face=face
            def key(vk,down):
                if down:state['held'].add(vk)
                else:state['held'].discard(vk)
            journey.key=key
            journey.release=lambda:state['held'].clear()
            def advance(count):
                state['updates']+=count
                if state['held']=={0x11,0x26}:
                    self.assertEqual(count,60)
                    state['bouts']+=1
                    if condition!='intact' and state['player']==state['target'] and state['faced']==state['target']:
                        state['health']-=40
                        if state['health']<=0:
                            state.update(state=11,representation=int(condition=='still represented'))
                    state['target'][0]+=600
            journey.advance=advance
            navigator=SimpleNamespace(await_actor=Mock(),approach=Mock(
                side_effect=lambda **_:state.update(player=list(state['target']))))
            journey.navigator=Mock(return_value=navigator)
            with self.subTest(condition=condition),redirect_stdout(io.StringIO()):
                if condition=='pass':journey.strike(602,death=True)
                else:
                    with self.assertRaises(RuntimeError):journey.strike(602,death=True)
            journey.navigator.assert_called_once_with('kill_enemy',(602,),fixed=602,reach=380)
            self.assertLessEqual(state['updates'],1350)
            self.assertLessEqual(state['bouts'],20)
            if condition=='pass':
                self.assertEqual(state['bouts'],3)
                self.assertEqual(state['held'],set())
                self.assertGreaterEqual(navigator.approach.call_count,3)
                self.assertEqual(journey.details['target']['samples'][-1]['representation'],0)

    def test_smith_prerequisite_kill_requires_observed_original_joe_melee_and_final_removal(self):
        from types import SimpleNamespace
        from unittest.mock import Mock
        module=self.potion_module()
        observer=patch('e2_population_profile.observe',return_value=dict(profile='live'))
        observer.start();self.addCleanup(observer.stop)
        for condition in ('pass','other writer','other attacker','replaced','truncated','still represented','still dying'):
            state=dict(health=100,state=2,representation=1)
            watches=[]
            class Breakpoint:
                def __init__(self,*_a,**_k):watches.append(self)
                def delete(self):pass
            frame=SimpleNamespace(name=lambda:'other' if condition=='other writer' else 'FUN_0042efdc',
                                  read_var=lambda _:900,older=lambda:None)
            module.gdb=SimpleNamespace(Breakpoint=Breakpoint,BP_WATCHPOINT=1,WP_WRITE=2,
                newest_frame=lambda:frame,GdbError=RuntimeError,error=RuntimeError,execute=lambda *_a,**_k:None)
            def value(expression):
                if expression=='DAT_0047a470':return 1
                if expression=='_DAT_00643650':return 0
                if expression=='*(unsigned int*)(900+0x22)':return 1000
                if expression=='*(short*)1000':return 602 if condition=='other attacker' else 0
                for offset,key in ((0xec,'health'),(0x82,'state'),(0x11e,'representation')):
                    if expression in (f'*(short*)(602+{offset:#x})',f'*(unsigned int*)(602+{offset:#x})'):
                        return state[key]
                raise AssertionError(expression)
            context=dict(value=value,field=lambda *_:100,actor=1,prefix=str(self.root/'early-smith'),
                         set_phase_title=lambda _:None,checkpoint=lambda _:None)
            journey=module.Journey(context,'enemy',{})
            journey.actor_by_id=lambda identity:identity
            journey.position=lambda *_:[0,4096,0]
            journey.phases.append(dict(name='combat.attack-down'))
            journey.observe_smith_health()
            state.update(health=-20,state=5 if condition=='still dying' else 11,
                         representation=int(condition=='still represented'))
            self.assertFalse(watches[0].stop())
            trace=journey.details['smith_melee']
            if condition=='replaced':trace['pointer']=603
            if condition=='truncated':trace['truncated']=True
            journey.walk=Mock();journey.face=Mock();journey.key=Mock();journey.release=Mock()
            journey.advance=Mock()
            navigator=SimpleNamespace(await_actor=Mock(side_effect=RuntimeError('dead before encounter')),approach=Mock())
            journey.navigator=Mock(return_value=navigator)
            with self.subTest(condition=condition),redirect_stdout(io.StringIO()):
                if condition=='pass':journey.strike(602,death=True)
                else:
                    with self.assertRaises(RuntimeError):journey.strike(602,death=True)
            if condition=='pass':
                navigator.await_actor.assert_not_called();navigator.approach.assert_not_called()
                journey.walk.assert_not_called();journey.face.assert_not_called();journey.key.assert_not_called()
                self.assertTrue(trace['satisfied_during_prerequisites'])
                self.assertEqual(trace['hits'][0]['before'],100)
                self.assertEqual(trace['hits'][0]['attacker'],0)
                journey.release.assert_called()

    def test_door_passage_requires_destruction_and_actual_released_crossing(self):
        import importlib.util
        from types import SimpleNamespace
        from unittest.mock import Mock
        fake_gdb=SimpleNamespace(GdbError=RuntimeError,error=RuntimeError,execute=lambda *_a,**_k:None)
        with patch.dict(sys.modules,{'gdb':fake_gdb}):
            spec=importlib.util.spec_from_file_location('door_contract',ROOT/'scripts/e2_gameplay_steps.py')
            module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        observer=patch('e2_population_profile.observe',return_value=dict(profile='live'))
        observer.start();self.addCleanup(observer.stop)
        for condition in ('pass','intact','still represented','no passage','wrong floor'):
            state=dict(health=100,state=7,representation=1,player=[0,4096,400])
            def value(expression):
                if expression=='DAT_0047a470':return 1
                if expression=='_DAT_00643650':return 0
                for offset,key in ((0xec,'health'),(0x82,'state'),(0x11e,'representation')):
                    if expression in (f'*(short*)(980+{offset:#x})',f'*(unsigned int*)(980+{offset:#x})'):
                        return state[key]
                raise AssertionError(expression)
            context=dict(value=value,field=lambda *_:100,actor=1,prefix=str(self.root/'door'),
                         set_phase_title=lambda _:None,checkpoint=lambda _:None)
            journey=module.Journey(context,'door',{})
            journey.actor_by_id=lambda identity:identity
            journey.position=lambda actor=None:list(state['player']) if actor is None else [0,4096,0]
            journey.walk=Mock();journey.face=Mock();journey.key=Mock();journey.release=Mock()
            journey.scene_map=Mock()
            journey.camera=lambda:164
            def advance(count):
                if journey.phases[-1]['name']=='interaction.break-door':
                    state.update(health=100 if condition=='intact' else -20,
                                 state=7 if condition=='intact' else 11,
                                 representation=1 if condition=='still represented' else 0)
            journey.advance=advance
            def cross(*_):
                state['player']=[0,4864 if condition=='wrong floor' else 4096,
                                 400 if condition=='no passage' else -640]
                return dict(crossed=True)
            navigator=SimpleNamespace(cross_opening=Mock(side_effect=cross),navigate=Mock())
            journey.navigator=Mock(return_value=navigator)
            with self.subTest(condition=condition),redirect_stdout(io.StringIO()):
                if condition=='pass':journey.strike(980)
                else:
                    with self.assertRaises(RuntimeError):journey.strike(980)
            if condition in ('intact','still represented'):
                navigator.cross_opening.assert_not_called()
            else:
                navigator.cross_opening.assert_called_once_with(980,[0,4096,0],(0,-1))
            if condition=='pass':
                self.assertEqual(journey.details['door_passage']['distance_beyond_door'],640)

    def test_displaced_door_case_requires_observed_start_before_attempting_destruction(self):
        from contextlib import nullcontext
        from unittest.mock import Mock
        module=self.potion_module()
        for position in ([4790,4096,-11985],[0,4096,-9800],[4790,4352,-11985]):
            journey=module.Journey.__new__(module.Journey)
            journey.details={};journey.c={}
            journey.position=lambda:list(position)
            journey.phase=lambda _:nullcontext()
            journey.save=Mock();journey.release=Mock();journey.advance=Mock()
            journey.scene_map=Mock()
            navigators=[]
            def navigator(*args,**kwargs):
                result=module.Journey.navigator(journey,*args,**kwargs)
                result.navigate=Mock();navigators.append(result)
                return result
            journey.navigator=navigator
            if position==[4790,4096,-11985]:
                journey.displaced_door_start()
                self.assertEqual(journey.details['displaced_door_start']['actual'],position)
            else:
                with self.assertRaisesRegex(RuntimeError,'required displaced door start'):
                    journey.displaced_door_start()
            self.assertTrue(navigators[0].navigate.call_args.kwargs['avoid_actors'])
            journey.advance.assert_not_called()

    def test_navigation_watch_pacing_scales_only_the_host_budget(self):
        import importlib.util
        from types import SimpleNamespace
        with patch.dict(sys.modules,{'gdb':SimpleNamespace()}):
            spec=importlib.util.spec_from_file_location('watch_navigation_contract',ROOT/'scripts/e2_gameplay_steps.py')
            module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        for watch,seconds in ((False,55),(True,165)):
            context=SimpleNamespace(details={},c=dict(watch_mode=watch))
            navigator=module.Journey.navigator(context,'reach_water',(0,))
            self.assertEqual(navigator.limits.seconds,seconds)
            self.assertEqual(navigator.limits.updates,2400)
            self.assertEqual(navigator.limits.replans,6)

    def test_navigation_streams_decisions_and_actual_inputs_before_progress_publication(self):
        import importlib.util
        from types import SimpleNamespace
        from unittest.mock import Mock
        fake_gdb=SimpleNamespace(GdbError=RuntimeError,error=RuntimeError)
        with patch.dict(sys.modules,{'gdb':fake_gdb}):
            spec=importlib.util.spec_from_file_location('navigation_stream_contract',ROOT/'scripts/e2_gameplay_steps.py')
            module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        with patch('e2_population_profile.observe',return_value=dict(profile='noncombat-opening')):
            context=dict(actor=1,value=lambda _:0,field=lambda *_:0,prefix=str(self.root/'stream'),
                         key=Mock(),advance=Mock())
            journey=module.Journey(context,'shared',dict(checks=['Movement.Swimming']))
        journey.save=Mock()
        bridge=journey.navigator('reach_water',(0,)).bridge
        bridge.record(dict(goal='reach_water',action='steer',updates=0,keys=[0x26]))
        bridge.apply([0x26],3)
        bridge.record(dict(goal='reach_water',action='steer',updates=3,keys=[]))
        self.assertEqual(journey.save.call_count,1)
        events=[json.loads(line) for line in Path(journey.prefix+'-navigation.jsonl').read_text().splitlines()]
        self.assertEqual([row['updates'] for row in events],[0,3])
        self.assertEqual(json.loads(Path(journey.prefix+'-inputs.jsonl').read_text()),dict(update=0,key=0x26,down=True))
        bridge.record(dict(goal='reach_water',outcome='FAIL',reason='blocked',updates=3))
        self.assertEqual(journey.save.call_count,2)
        bridge.release()
        inputs=[json.loads(line) for line in Path(journey.prefix+'-inputs.jsonl').read_text().splitlines()]
        self.assertEqual(inputs[-1],dict(update=3,key=0x26,down=False))
        self.assertFalse(any(journey.held.values()))

    def test_swimming_plans_from_live_scene_and_requires_real_swimming(self):
        import importlib.util
        from types import SimpleNamespace
        from unittest.mock import Mock
        fake_gdb=SimpleNamespace(GdbError=RuntimeError,error=RuntimeError,execute=lambda *_a,**_k:None)
        with patch.dict(sys.modules,{'gdb':fake_gdb}):
            spec=importlib.util.spec_from_file_location('swimming_contract',ROOT/'scripts/e2_gameplay_steps.py')
            module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        observer=patch('e2_population_profile.observe',return_value=dict(profile='noncombat-opening'))
        observer.start();self.addCleanup(observer.stop)
        unit=next(unit for unit in journey_plan(self.shared_catalogue(),['debug.Movement.Swimming']) if unit.checkpoints)
        for condition in ('pass','wrong camera','wrong representation','no displacement','blocked plan'):
            state=dict(position=[8011,3328,-18581],camera=175,representation=12)
            def value(expression):
                if expression=='DAT_0047a470':return 1
                if expression=='_DAT_00643650':return 0
                if expression=='*(short*)1':return state['representation']
                raise AssertionError(expression)
            def field(offset,*_):return {0x11e:1,0xec:100,0x82:4}[offset]
            context=dict(value=value,field=field,actor=1,prefix=str(self.root/'water'),
                         set_phase_title=lambda _:None,checkpoint=lambda _:None)
            journey=module.Journey(context,'shared',dict(checks=['Movement.Swimming']))
            journey.position=lambda:list(state['position']);journey.camera=lambda:state['camera']
            journey.walk=Mock(side_effect=AssertionError('Legacy waypoint controller used'))
            def key(vk,down):journey.held[vk]=down
            def advance(count):
                journey.updates+=count
                if journey.held.get(0x26) and condition!='no displacement':state['position'][2]+=60
            journey.key=key;journey.advance=advance
            scene=SimpleNamespace(region_goal=Mock(return_value=[-768,5120,-2304]))
            journey.scene_map=Mock(return_value=scene)
            def navigate(actual,goal,*,water):
                self.assertIs(actual,scene);self.assertEqual(goal,[-768,5120,-2304]);self.assertTrue(water)
                scene.region_goal.assert_called_once_with([8011,3328,-18581],543,7,5120,entry=True)
                if condition=='blocked plan':raise RuntimeError('No connected scene-floor plan')
                state.update(position=list(goal),camera=175 if condition=='wrong camera' else 543,
                             representation=12 if condition=='wrong representation' else 13)
            navigator=SimpleNamespace(navigate=Mock(side_effect=navigate))
            journey.navigator=Mock(return_value=navigator)
            with self.subTest(condition=condition),redirect_stdout(io.StringIO()):
                with journey.checkpoint('Startup.DelayedSkip'):pass
                with journey.checkpoint('Movement.ControlsAndRelease'):pass
                if condition=='pass':
                    with journey.checkpoint('Movement.Swimming'):journey.swimming()
                else:
                    with self.assertRaises(RuntimeError),journey.checkpoint('Movement.Swimming'):journey.swimming()
            results=shared_results(unit,dict(status='FAIL' if condition!='pass' else 'PASS',
                progress=dict(checkpoints=journey.checkpoints)),{case.name:case for case in self.shared_catalogue()})
            status=next(row['status'] for row in results if row['name']=='debug.Movement.Swimming')
            self.assertEqual(status,'PASS' if condition=='pass' else 'BLOCKED' if condition in
                             ('wrong camera','blocked plan') else 'FAIL')
            journey.navigator.assert_called_once_with('reach_water',(0,),updates=3200)
            self.assertFalse(any(journey.held.values()))

    def test_water_combat_requires_all_real_directional_actions_and_release(self):
        import importlib.util
        from types import SimpleNamespace
        fake_gdb=SimpleNamespace(GdbError=RuntimeError,error=RuntimeError,execute=lambda *_a,**_k:None)
        with patch.dict(sys.modules,{'gdb':fake_gdb}):
            spec=importlib.util.spec_from_file_location('water_combat_contract',ROOT/'scripts/e2_gameplay_steps.py')
            module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        observer=patch('e2_population_profile.observe',return_value=dict(profile='noncombat-opening'))
        observer.start();self.addCleanup(observer.stop)
        for condition in ('pass','armed pass','no attack','wrong action','left water','no movement'):
            armed=condition=='armed pass'
            state=dict(position=[0,5120,0],slot=1000,action=1521)
            def value(expression):
                if expression=='DAT_0047a470':return 1
                if expression=='_DAT_00643650':return 0
                if expression=='DAT_0047a7ec':return 7
                if expression=='*(short*)1':return 12 if condition=='left water' else 10 if armed else 13
                if expression=='*(short*)2':return -1 if condition=='wrong action' else state['action']
                if expression.startswith('*(short*)(1+2+'):return state['action']
                if expression=='*(unsigned int*)(3+0xf2)':return 4
                if expression=='*(unsigned int*)(4+0x22)':return 1
                if expression=='*(unsigned int*)(4+0x13a)':return 3
                raise AssertionError(expression)
            def field(offset,*_):return {0x11e:1,0xec:100,0x82:4,0x86:5120,0xf0:3 if armed else 0,0xa6:2,0x96:state['slot']}[offset]
            context=dict(value=value,field=field,actor=1,prefix=str(self.root/'water-combat'),
                         set_phase_title=lambda _:None,checkpoint=lambda _:None)
            journey=module.Journey(context,'shared',dict(checks=['Combat.SwimmingDirections']))
            journey.position=lambda:list(state['position'])
            journey.actor_by_id=lambda _:3
            journey.key=lambda vk,down:journey.held.update({vk:down})
            def advance(count):
                journey.updates+=count
                if journey.held.get(0x11):
                    index=next(i for i,vk in enumerate((0x26,0x25,0x27,0x28)) if journey.held.get(vk))
                    if condition!='no attack':state.update(slot=184+index,action=((1479,1479,1479,1482) if armed else (1521,1521,1520,1522))[index])
                elif journey.held.get(0x26) and condition!='no movement':state['position'][2]+=30
            journey.advance=advance
            with self.subTest(condition=condition),redirect_stdout(io.StringIO()):
                if condition in ('pass','armed pass'):
                    with journey.checkpoint('Combat.SwimmingDirections'):journey.water_combat(armed)
                    self.assertEqual([r['direction'] for r in journey.details['water_combat']],['up','left','right','down'])
                else:
                    with self.assertRaises(RuntimeError),journey.checkpoint('Combat.SwimmingDirections'):journey.water_combat()
            self.assertFalse(any(journey.held.values()))

    def test_water_block_exercises_armed_and_unarmed_attacks_and_crossings(self):
        cases=self.shared_catalogue();chosen=selection(cases,block_patterns(cases,'swimming'))
        for check in ('Movement.Swimming','Combat.SwimmingDirections','Traversal.Water',
                      'Movement.ArmedSwimming','Combat.ArmedSwimmingDirections','Traversal.ArmedWater'):
            case=next(c for c in cases if c.name=='debug.'+check)
            self.assertIn(case.name,chosen)
            self.assertTrue(case.required);self.assertEqual(case.kind,'journey');self.assertIsNone(case.skip)
        units=[unit for unit in journey_plan(cases,block_patterns(cases,'swimming')) if unit.checkpoints]
        self.assertEqual(len(units),2)
        armed=next(unit for unit in units if 'debug.Movement.ArmedSwimming' in unit.checkpoints)
        unarmed=next(unit for unit in units if 'debug.Movement.Swimming' in unit.checkpoints)
        self.assertIn('debug.Interaction.SwordPickup',armed.checkpoints)
        self.assertNotIn('debug.Interaction.SwordPickup',unarmed.checkpoints)
        self.assertEqual(armed.population_profile,'noncombat-opening')

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
                 '    #0 0x123 in FUN_0043ce58 recon.c:33786\n','FUN_0043ce58'),
                ('Program terminated with signal SIGKILL, Killed.\n',None)):
            def failure(command,directory,*_):
                directory.mkdir(exist_ok=True)
                (directory/'probe.log').write_text(log)
                return dict(status='FAIL',reason='Native failure')
            with patch('e2_suite.execute',side_effect=failure):result=executor(Path('/external'))(case,self.root,results)
            self.assertEqual(result['native_failure']['function'],expected)
            self.assertEqual(result['status'],'FAIL')

    def test_stalled_probe_interrupts_before_cleanup_and_keeps_capture(self):
        from e2_probe_diagnostics import communicate
        prefix=str(self.root/'stall')
        child=('import pathlib,signal,time,sys\n'
               'def capture(*_):\n'
               ' pathlib.Path(sys.argv[1]+"-stopped.json").write_text("captured")\n'
               ' print("stopped stack",flush=True)\n'
               ' raise SystemExit(0)\n'
               'signal.signal(signal.SIGINT,capture)\n'
               'while True:time.sleep(.1)\n')
        process=subprocess.Popen([sys.executable,'-c',child,prefix],stdout=subprocess.PIPE,
                                 stderr=subprocess.STDOUT,text=True,start_new_session=True)
        self.addCleanup(lambda:process.poll() is None and process.kill())
        output,stalled=communicate(process,prefix,10,stall_timeout=1.5)
        self.assertTrue(stalled)
        self.assertEqual(process.returncode,0)
        self.assertIn('stopped stack',output)
        self.assertTrue(Path(prefix+'-stopped.json').is_file())
        self.assertEqual(json.loads(Path(prefix+'-stall.json').read_text())['reason'],
                         'no debugger or inspection progress')

    def test_probe_heartbeat_prevents_false_stall_without_inspection(self):
        from e2_probe_diagnostics import communicate
        prefix=str(self.root/'progress')
        child=('import pathlib,time,sys\n'
               'for _ in range(25):\n'
               ' pathlib.Path(sys.argv[1]+"-heartbeat").touch()\n'
               ' time.sleep(.1)\n'
               'print("complete")\n')
        process=subprocess.Popen([sys.executable,'-c',child,prefix],stdout=subprocess.PIPE,
                                 stderr=subprocess.STDOUT,text=True,start_new_session=True)
        self.addCleanup(lambda:process.poll() is None and process.kill())
        output,stalled=communicate(process,prefix,10,stall_timeout=1.5)
        self.assertFalse(stalled)
        self.assertIn('complete',output)


if __name__=='__main__':
    unittest.main(verbosity=2)
