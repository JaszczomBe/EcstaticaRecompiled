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

from e2_suite import BLOCKS, Case, ROOT, block_patterns, display_driver, catalogue, execute, executor, ordered, run_cases, selection, qualify_journey_failure, digest


class SuiteContracts(unittest.TestCase):
    def setUp(self):
        self.temporary=tempfile.TemporaryDirectory(prefix='e2-suite-contract-')
        self.root=Path(self.temporary.name)
        self.addCleanup(self.temporary.cleanup)

    def run_suite(self,cases,callback,patterns=('*',)):
        with redirect_stdout(io.StringIO()):
            return run_cases(cases,callback,self.root/'report',patterns)

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
        game=[c for c in launches if c['name']=='Ecstatica Recompiled']
        suite=[c for c in launches if c['name']=='Ecstatica: Full regression suite']
        self.assertEqual(len(game),1)
        self.assertEqual(game[0]['args'],['--run-recon'])
        self.assertEqual(len(suite),1)
        self.assertIn('run-e2-suite.py',suite[0]['command'])
        self.assertIn('--configurations debug asan',suite[0]['command'])
        self.assertNotIn('--filter',suite[0]['command'])

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
        self.assertEqual(picker['options'],['headless','visible'])
        for block in BLOCKS:
            if block=='full':continue
            launches=[c for c in config['configurations'] if '--block '+block+' ' in c.get('command','')]
            self.assertEqual(len(launches),1,block)
            self.assertIn('--display ${input:e2SuiteDisplay}',launches[0]['command'])
        self.assertTrue(any('--display visible' in c.get('command','') for c in config['configurations']))


if __name__=='__main__':
    unittest.main(verbosity=2)
