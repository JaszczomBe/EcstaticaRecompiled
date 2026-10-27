"""Bounded input-only menu checks in horseback, pedestal and gameplay contexts.

Loaded by GDB through probe-e2-player-motion.py. Game fields are observation-only;
all menu changes, skips and restarts use actual SDL keyboard/mouse events.
"""
from contextlib import contextmanager
import copy
import json
from pathlib import Path
import time

import gdb


class Unavailable(Exception):
    pass


class MenuJourney:
    HORSE = 'DAT_0047a470 != 0 && _DAT_0073cc3c != 0 && _DAT_0073cc3c != 0x67da4c && *(unsigned int*)((int)DAT_0047a470+0xa6) != 0'

    def __init__(self, prefix, options, watch, title, game_data, logo_delay=5000, logo_skip=True):
        from e2_suite import MENU_CHECKS
        self.prefix,self.watch,self.title=prefix,watch,title
        self.logo_delay,self.logo_skip=logo_delay,logo_skip
        self.checks=options.get('checks',[])
        allowed={'Startup.DelayedSkip',*MENU_CHECKS}
        if not self.checks or len(self.checks)!=len(set(self.checks)) or any(name not in allowed for name in self.checks):
            raise ValueError('Invalid menu checkpoint selection')
        self.rows,self.phases,self.inputs,self.states=[],[],[],[]
        self.updates=0;self.details={};self.complete=False;self.stage='Intro'
        self.frame=None;self.menu=None;self.exit_codes=[];self.game_data=game_data;self.resume_validated=False
        gdb.events.exited.connect(lambda event:self.exit_codes.append(getattr(event,'exit_code',None)))
        self.save()

    def value(self, expression):
        return int(gdb.parse_and_eval(expression))

    def require(self, condition, message):
        if not condition:raise gdb.GdbError(message)

    def save(self):
        value=dict(schema='e2suite.journey.1',scenario='menu-matrix',checkpoints=self.rows,
                   phases=self.phases,inputs=self.inputs,updates=self.updates,details=self.details,complete=self.complete)
        path=Path(self.prefix+'-journey.json');temporary=path.with_suffix('.json.tmp')
        temporary.write_text(json.dumps(value,indent=2)+'\n');temporary.replace(path)

    def state(self, label):
        from e2_population_profile import observe
        self.details['population']=observe(self.prefix,label)
        actor=self.value('DAT_0047a470')
        field=lambda offset,kind='short':self.value(f'*({kind}*)({actor}+{offset})') if actor else 0
        action=field(0xa6,'unsigned int')
        return dict(label=label,actor=actor,identity=field(0),camera=(self.value('_DAT_0073cc3c')-0x67c728)//28,
            wait=self.value('DAT_0047a76c'),modal=self.value('_DAT_00643650'),
            requester=self.value('*(unsigned short*)((char*)&DAT_0047a45e+2)'),
            health=field(0xec),state=field(0x82),action=action,
            action_id=self.value(f'*(short*){action}') if action else -1,progress=field(0xac,'unsigned short'),
            position=[field(offset) for offset in (0x84,0x86,0x88)],
            music=self.value('DAT_0047a49c'),sound=self.value('DAT_0047a4a0'),
            difficulty=self.value('DAT_0047a4a4'),resolution=self.value('DAT_0047a43c'))

    @contextmanager
    def checkpoint(self, name):
        started=time.monotonic();row=dict(name=name,status='RUNNING',phase_start=len(self.phases),started_monotonic=started,parent=None)
        phase=dict(name='menus.'+name.removeprefix('Menus.'),status='RUNNING',update=self.updates)
        self.rows.append(row);self.phases.append(phase);self.save()
        print('[ PHASE    ] '+phase['name'],flush=True)
        try:
            self.set_title(name)
            self.states.append(self.state(name+'.before')) if gdb.selected_inferior().pid else None
            yield
            row['status']=phase['status']='PASS'
        except Unavailable as error:
            row.update(status='SKIPPED',reason=str(error));phase.update(status='SKIPPED',reason=str(error))
        except BaseException as error:
            row.update(status='FAIL',reason=str(error));phase.update(status='FAIL',reason=str(error))
            raise
        finally:
            if gdb.selected_inferior().pid:
                try:self.states.append(self.state(name+'.after'))
                except gdb.error:pass
            row.update(phase_end=len(self.phases),seconds=time.monotonic()-started,
                       details=copy.deepcopy(self.details))
            phase['end_update']=self.updates
            self.save()

    def set_title(self, phase):
        if self.watch and gdb.selected_inferior().pid and self.value('e2r_sdl_backend.window != 0'):
            gdb.execute('call (bool)SDL_SetWindowTitle(e2r_sdl_backend.window,'+json.dumps(self.title+' | '+phase)+')',to_string=True)
            time.sleep(.2)

    def key(self, key, down):
        scans={27:41,32:44,38:82,40:81}
        gdb.execute('set $menu_event=(SDL_Event*)calloc(1,sizeof(SDL_Event))',to_string=True)
        for member,number in [('type',0x300 if down else 0x301),('down',int(down)),('key',key if key<38 else 0x40000000|scans[key]),('scancode',scans[key])]:
            gdb.execute(f'set $menu_event->key.{member}={number}',to_string=True)
        gdb.execute('set $menu_event->key.windowID=SDL_GetWindowID(e2r_sdl_backend.window)',to_string=True)
        self.require(self.value('SDL_PushEvent($menu_event)')==1,'SDL key injection failed')
        gdb.execute('call (void)free($menu_event)',to_string=True)
        gdb.execute('call e2r_poll_host_events("menu-matrix")',to_string=True)
        self.inputs.append(dict(update=self.updates,key=key,down=down,stage=self.stage));self.save()

    def step(self, count=1):
        self.require(self.updates+count<=30000,'Menu journey update bound exceeded')
        for _ in range(count):
            started=time.monotonic();gdb.execute('continue',to_string=True)
            self.require(gdb.selected_inferior().pid and gdb.selected_frame().name()=='FUN_00415d40','Unexpected native stop during menu route')
            self.updates+=1
            if self.watch:time.sleep(max(0,1/60-(time.monotonic()-started)))

    def pump(self, count=3):
        for _ in range(count):
            gdb.execute('continue',to_string=True)
            self.require(gdb.selected_inferior().pid and gdb.selected_frame().name()=='FUN_0041ba7c','Unexpected stop while pumping requester')

    def present(self):
        gdb.execute('call e2r_present_current_frame((HWND)_DAT_00ac4dac,1)',to_string=True)
        if self.watch:time.sleep(.4)

    def requester(self, expected):
        actual=self.value('*(unsigned short*)((char*)&DAT_0047a45e+2)')
        self.require(actual==expected,f'Expected requester {expected:#x}, observed {actual:#x}')

    def open(self):
        self.frame.enabled=False;self.menu=gdb.Breakpoint('FUN_0041ba7c',internal=True)
        self.key(27,True);self.pump(1);self.key(27,False);self.pump()
        self.requester(0x28);self.require(self.value('_DAT_00643650')==5,'Menu did not become active')
        self.present()

    def close(self, button=False):
        if button:self.click(0x643780)
        else:self.key(27,True);self.key(27,False)
        self.menu.delete();self.menu=None;self.frame.enabled=True;self.step(3)
        self.require(self.value('_DAT_00643650')==0,'Menu did not close')

    def item(self, address):
        text=self.value(f'*(unsigned int*)({address}+8)')
        label=gdb.selected_inferior().read_memory(text, min(100,256)).tobytes().split(b'\0',1)[0].decode('ascii','replace') if text else ''
        return dict(address=address,label=label,flags=self.value(f'*(unsigned short*)({address}+16)'),
                    bounds=[self.value(f'*(short*)({address}+{offset})') for offset in (22,24,26,28)])

    def click(self, address):
        item=self.item(address);x1,x2,y1,y2=item['bounds'];x,y=(x1+x2)//2,(y1+y2)//2
        self.require(x2>x1 and y2>y1,'Menu item has no live hit rectangle: '+hex(address))
        gdb.execute(f'call SetCursorPos({x},{y})',to_string=True)
        gdb.execute('set $menu_event=(SDL_Event*)calloc(1,sizeof(SDL_Event))',to_string=True)
        for member,number in [('type',0x401),('down',1),('button',1),('x',x),('y',y+80)]:
            gdb.execute(f'set $menu_event->button.{member}={number}',to_string=True)
        gdb.execute('set $menu_event->button.windowID=SDL_GetWindowID(e2r_sdl_backend.window)',to_string=True)
        self.require(self.value('SDL_PushEvent($menu_event)')==1,'SDL mouse injection failed')
        gdb.execute('call (void)free($menu_event)',to_string=True)
        self.inputs.append(dict(update=self.updates,click=item,stage=self.stage));self.save()

    def settings(self):
        self.open();self.click(0x6439d8);self.pump();self.requester(0x31)
        self.option_baseline={symbol:self.value(symbol) for symbol in ('DAT_0047a49c','DAT_0047a4a0','DAT_0047a4a4')}
        self.details['settings']=[self.item(address) for address in (0x643998,0x6439f8,0x643958,0x6436e0,0x643de4)]
        self.present()

    def close_settings(self):
        self.click(0x643de4);self.pump();self.requester(0x28);self.close()

    def check(self, action):
        if action=='ShowHide':
            before=self.state('before-show-hide')
            self.open();self.close()
            self.open();self.close(button=True)
            self.open();self.click(0x643ca4);self.pump();self.requester(0x14)
            self.click(0x643c84);self.pump();self.requester(0x28);self.close()
            after=self.state('after-show-hide')
            self.require(before['camera']==after['camera'] and before['wait']==after['wait'] and after['identity']==0,
                         'Menu cancellation changed stage/player identity')
        elif action=='Settings':self.settings();self.close_settings()
        elif action in ('MusicToggle','SoundToggle','Difficulty'):
            self.settings()
            address,symbol=(0x643998,'DAT_0047a49c') if action=='MusicToggle' else (0x6439f8,'DAT_0047a4a0') if action=='SoundToggle' else (0x643958,'DAT_0047a4a4')
            original=self.value(symbol);samples=[dict(value=original,item=self.item(address))]
            if self.item(address)['flags']&0x80:
                self.close_settings();raise Unavailable('Original menu disables this control on the available backend')
            for index in range(3 if action=='Difficulty' else 2):
                self.click(address);self.pump()
                current=self.value(symbol);samples.append(dict(value=current,item=self.item(address)))
                self.details[action]=samples;self.save()
                expected=(original+index+1)%3 if action=='Difficulty' else int(not original) if index==0 else original
                self.require(current==expected,'Option did not change through SDL input: '+action)
                self.require(samples[-1]['item']['label']!=samples[-2]['item']['label'],'Option label did not reflect its state')
            self.details[action]=samples
            self.require(self.value(symbol)==original,'Option did not return to original value through input')
            self.close_settings()
        elif action=='ResolutionToggle':
            self.settings();self.details['resolution_control']=self.item(0x6436e0);self.close_settings()
            raise Unavailable('Resolution control observed; resource reload/rendered dimensions lack accepted assertions')
        elif action in ('LoadDialog','SaveDialog'):
            self.open();self.click(0x643cc4 if action=='LoadDialog' else 0x643b10);self.pump()
            if action=='SaveDialog' and self.stage!='Gameplay':
                self.requester(0x28)
                self.require(self.value('DAT_0047a76c')!=0 and self.value('_DAT_00643650')==5,'Save was not disabled during the intro')
                self.details['save']=dict(disabled_during_intro=True);self.close();return
            self.requester(0x29 if action=='LoadDialog' else 0x2a);self.present()
            self.key(27,True);self.key(27,False)
            if action=='SaveDialog':
                # Gameplay Save is a standalone requester opened after the
                # main menu unwinds (FUN_00415d40 case 3).
                self.menu.delete();self.menu=None;self.frame.enabled=True;self.step(3)
                self.require(self.value('_DAT_00643650')==0,'Save cancellation did not resume gameplay')
            else:self.pump();self.requester(0x28);self.close()
            self.details[action]=dict(opened=True,cancelled=True,state_round_trip=False)
        else:raise ValueError('Unknown menu check '+action)

    def reach_pedestal(self):
        if self.value('_DAT_0073cc3c')!=0x67da4c:
            # Match the standalone delayed-skip assertion: release Space only
            # after observing at least tick 83 of the opening action.
            for _ in range(600):
                before=self.state('before-delayed-skip')
                self.require(before['action_id']==self.initial['action_id'],'Opening action ended before delayed skip')
                if before['progress']>=83:break
                self.step()
            else:raise gdb.GdbError('Opening action did not reach delayed skip progress')
            self.details['intro_skip']=dict(action=before['action_id'],progress=before['progress'],key='SDL Space')
            self.key(32,True);self.step();self.key(32,False)
        for _ in range(1800):
            if self.value('_DAT_0073cc3c')==0x67da4c and self.value('DAT_0047a76c')!=0:
                self.stage='Pedestal';return
            self.step()
        raise gdb.GdbError('Pedestal intro not reached after SDL Space')

    def reach_gameplay(self):
        for _ in range(3000):
            if self.value('_DAT_0073cc3c')==0x67da4c and self.value('DAT_0047a76c')==0:
                self.stage='Gameplay';self.step(3)
                state=self.state('gameplay-ready')
                self.require(state['identity']==0 and state['health']==100 and state['state']==4 and state['position'][1]==3328,
                             'Menu route did not release healthy Joe in courtyard')
                return
            self.step()
        raise gdb.GdbError('Released gameplay not reached')

    def recover_menu(self, stage, failed_check):
        # Independent option checks may continue only after real input closes
        # the dialog and returns changed controls to their observed baseline.
        # A signal/unexpected native frame is never treated as a recoverable UI assertion.
        self.require(gdb.selected_inferior().pid and self.menu is not None and gdb.selected_frame().name()=='FUN_0041ba7c',
                     'Cannot recover an unexpected native stop')
        with self.checkpoint('setup.Recover.'+failed_check):
            rid=self.value('*(unsigned short*)((char*)&DAT_0047a45e+2)')
            if rid==0x31:
                for address,symbol in ((0x643998,'DAT_0047a49c'),(0x6439f8,'DAT_0047a4a0'),(0x643958,'DAT_0047a4a4')):
                    for _ in range(3):
                        if self.value(symbol)==self.option_baseline[symbol]:break
                        self.click(address);self.pump()
                    self.require(self.value(symbol)==self.option_baseline[symbol],'Could not restore option through input')
                self.close_settings()
            elif rid==0x28:self.close()
            else:raise gdb.GdbError('Unaccepted requester recovery path '+hex(rid))
            state=self.state('recovered')
            self.require(state['identity']==0 and state['health']>0 and state['modal']==0,'Recovery did not return a live player')
            self.stage=stage

    def stage_checks(self, stage):
        self.stage=stage
        for name in self.checks:
            if name.startswith('Menus.'+stage+'.') and not name.endswith('.StartGame'):
                try:
                    with self.checkpoint(name):self.check(name.rsplit('.',1)[1])
                except gdb.GdbError:
                    self.recover_menu(stage,name)


    def restart(self, stage):
        name='Menus.'+stage+'.StartGame'
        if name not in self.checks:return
        with self.checkpoint(name):
            self.require(self.stage==stage,'Restart checkpoint reached from wrong stage')
            if stage=='Intro':
                for _ in range(120):
                    if self.state('before-intro-restart')['progress']>=20:break
                    self.step()
                self.require(self.state('before-intro-restart')['progress']>=20,'Intro did not advance before restart')
            before=self.state('before-start-game');self.open();self.click(0x643b30)
            self.menu.delete();self.menu=None;self.frame.enabled=True
            self.details['restart']=dict(source=stage,before=before,initial=self.initial)
            for _ in range(120):
                self.step()
                after=self.state('after-start-game')
                self.details['restart']['after']=after
                if after['camera']==self.initial['camera'] and after['action_id']==self.initial['action_id'] and after['progress']<=self.initial['progress']+4:break
            else:raise gdb.GdbError('Start Game did not return to the initial horseback intro')
            self.require(after['identity']==self.initial['identity'] and after['health']==self.initial['health'],
                         'Start Game did not restore initial player identity/health')
            self.details['restart']=dict(source=stage,before=before,after=after,initial=self.initial)
            self.stage='Intro'

    def restart_checked(self, stage):
        try:self.restart(stage)
        except gdb.GdbError:
            # A failed transition can leave the same stage live. Continue
            # independent checks only after observing that boundary; no failed
            # restart is retried and no actor/camera state is restored.
            self.require(gdb.selected_inferior().pid and gdb.selected_frame().name()=='FUN_00415d40',
                         'Restart stopped outside the update boundary')
            with self.checkpoint('setup.AfterFailedRestart.'+stage):
                state=self.state('failed-restart')
                camera=self.initial['camera'] if stage=='Intro' else 175
                self.require(state['camera']==camera and state['health']>0 and state['identity']==0 and state['modal']==0,
                             'Failed restart left an incompatible stage')
                self.require(bool(state['wait'])==(stage!='Gameplay'),'Failed restart changed intro/gameplay stage')
                self.stage=stage

    def quit(self, logical=False):
        with self.checkpoint('Menus.CancelResumeQuit' if logical else 'setup.MenuExit'):
            if logical:self.require(self.resume_validated,'Gameplay cancellation/movement was not exercised')
            self.open();self.close()
            if self.stage=='Gameplay':
                before=self.state('resume-before')['position']
                for vk in (38,40):
                    self.key(vk,True);self.step(30);self.key(vk,False);self.step(90)
                    if self.state('resume-after')['position']!=before:break
                self.require(self.state('resume-after')['position']!=before,'Menu cancellation did not restore movement')
            self.open();self.click(0x643ca4);self.pump();self.requester(0x14);self.present()
            self.click(0x643dc4);self.menu.delete();self.menu=None
            self.frame.enabled=False;gdb.execute('continue',to_string=True)
            self.require(not gdb.selected_inferior().pid and self.exit_codes and self.exit_codes[-1]==0,'Confirmed Quit did not exit zero')

    def run(self):
        with self.checkpoint('setup.InitialIntro'):
            self.frame=gdb.Breakpoint('FUN_00415d40',internal=True);self.frame.condition=self.HORSE
            command='run '+('--game-data-dir '+json.dumps(self.game_data)+' ' if self.game_data else '')+'--run-recon'
            if self.logo_delay:
                from e2_startup_steps import start
                self.details['logos']=start(command,self.prefix,self.watch,self.title,self.logo_skip)
            else:gdb.execute(command,to_string=True)
            self.require(gdb.selected_frame().name()=='FUN_00415d40','Opening horseback intro not reached')
            self.frame.condition=None;self.initial=self.state('initial-horseback')
            self.require(self.initial['identity']==0 and self.initial['health']==100,'Initial intro player identity/health wrong')
        self.stage_checks('Intro')
        self.restart_checked('Intro')
        only_intro=all(name.startswith('Menus.Intro.') for name in self.checks)
        if only_intro:
            self.quit();return self.finish()
        with self.checkpoint('setup.Pedestal'):self.reach_pedestal()
        self.stage_checks('Pedestal')
        self.restart_checked('Pedestal')
        if self.stage=='Intro':
            with self.checkpoint('setup.PedestalAfterRestart'):self.reach_pedestal()
        only_early=all(name.startswith(('Menus.Intro.','Menus.Pedestal.')) for name in self.checks)
        if only_early:
            self.quit();return self.finish()
        with self.checkpoint('Startup.DelayedSkip' if 'Startup.DelayedSkip' in self.checks else 'setup.Gameplay'):
            self.reach_gameplay()
        self.stage_checks('Gameplay')
        if 'Menus.CancelResumeQuit' in self.checks:
            # Validate the legacy gameplay cancel/resume assertion before any
            # destructive restart; final native Quit is a separate lifecycle gate.
            with self.checkpoint('setup.GameplayCancelResume'):
                self.open();self.close()
                before=self.state('resume-before')['position']
                for vk in (38,40):
                    self.key(vk,True);self.step(30);self.key(vk,False);self.step(90)
                    if self.state('resume-after')['position']!=before:break
                self.require(self.state('resume-after')['position']!=before,'Menu cancellation did not restore movement')
                self.open();self.click(0x643ca4);self.pump();self.requester(0x14)
                self.click(0x643c84);self.pump();self.requester(0x28);self.close()
                self.resume_validated=True
        self.restart_checked('Gameplay')
        self.quit(logical='Menus.CancelResumeQuit' in self.checks);return self.finish()

    def finish(self):
        self.complete=True;self.save()
        report=dict(probe_complete=True,native_exit_code=self.exit_codes[-1],suite_result=dict(scenario='menu-matrix',
            phases=self.phases,checkpoints=self.rows,details=self.details),states=self.states)
        Path(self.prefix+'.json').write_text(json.dumps(report,indent=2)+'\n')
        print('PROBE COMPLETE: menu matrix; native exit zero',flush=True)
        return report


def run(prefix, options, watch, title, game_data=None, logo_delay=5000, logo_skip=True):
    journey=MenuJourney(prefix,options,watch,title,game_data,logo_delay,logo_skip)
    try:return journey.run()
    except BaseException:
        if gdb.selected_inferior().pid:
            try:gdb.execute('thread apply all bt');gdb.execute('info registers')
            except gdb.error:pass
        journey.save()
        raise
