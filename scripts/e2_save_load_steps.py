"""Input-only persistence journeys, loaded inside GDB by the bounded save/load probe."""
import json
from pathlib import Path
import struct

import gdb

from e2_menu_steps import MenuJourney

# Fields actually serialized in the active-actor section, excluding its duplicate +0x98.
FIELDS = (0x82,0x84,0x86,0x88,0x8a,0x8c,0x8e,0x90,0x92,0x94,
          0x96,0x98,0xe8,0xea,0xec,0xee,0xf0,0x182,0x186,0x184)


class PersistenceJourney(MenuJourney):
    def key(self, key, down):
        scans = {8:42,13:40,17:224,18:226,16:225,27:41,32:44,37:80,38:82,39:79,40:81}
        scan = scans.get(key)
        if scan is None:
            scan = 4 + ord(chr(key).lower()) - 97 if chr(key).isalpha() else 30 + (key - 49) % 10
        code = (0x40000000 | scan) if key in (16,17,18,37,38,39,40) else ord(chr(key).lower())
        gdb.execute('set $save_event=(SDL_Event*)calloc(1,sizeof(SDL_Event))',to_string=True)
        for member, number in [('type',0x300 if down else 0x301),('down',int(down)),('key',code),('scancode',scan)]:
            gdb.execute(f'set $save_event->key.{member}={number}',to_string=True)
        gdb.execute('set $save_event->key.windowID=SDL_GetWindowID(e2r_sdl_backend.window)',to_string=True)
        self.require(self.value('SDL_PushEvent($save_event)') == 1,'SDL key injection failed')
        gdb.execute('call (void)free($save_event)',to_string=True)
        gdb.execute('call e2r_poll_host_events("save-load")',to_string=True)
        self.inputs.append(dict(update=self.updates,key=key,down=down));self.save()

    def world(self):
        inferior = gdb.selected_inferior()
        read = lambda pointer, size: bytes(inferior.read_memory(pointer,size))
        word = lambda pointer: struct.unpack('<I',read(pointer,4))[0]
        short = lambda pointer: struct.unpack('<h',read(pointer,2))[0]
        current_tick = self.value('_DAT_00636588')
        actors,seen = {},set()
        cursor = self.value('_DAT_0063726c')
        while cursor:
            self.require(cursor not in seen and len(seen)<256,'Actor-list cycle/bound')
            seen.add(cursor)
            data = read(cursor,0x18c)
            s = lambda offset: struct.unpack_from('<h',data,offset)[0]
            w = lambda offset: struct.unpack_from('<I',data,offset)[0]
            identity = s(0)
            self.require(word(0x630b60+identity*4)==cursor,'Actor table identity mismatch')
            timers,visited = [],set()
            timer = w(0x17c)
            while timer:
                self.require(timer not in visited and len(visited)<100,'Timer cycle/bound')
                visited.add(timer)
                relative = (word(timer+2)-current_tick+32768)%65536-32768
                timers.append([short(timer),relative]);timer=word(timer+6)
            attachment = None
            if w(0xf2):
                node=w(0xf2);owner=word(node+0x22)
                attachment=dict(owner=short(owner),node=short(node),reciprocal=word(node+0x13a)==cursor)
            action=w(0xa6)
            action_owner=w(0x132)
            actors[str(identity)] = dict(
                fields={hex(offset):s(offset) for offset in FIELDS},
                matrix=list(struct.unpack_from('<9h',data,0xc6)),
                actions=[short(w(offset)) if w(offset) else -1 for offset in (0x126,0x12a)],
                script=dict(kind=1 if action_owner else 2 if action else 0,
                            identity=short(action_owner) if action_owner else short(action) if action else -1,
                            progress=s(0xac)&65535,phase=s(0xb2)&65535) if action else None,
                timers=timers,attachment=attachment)
            cursor=w(0x4c)
        return dict(tick=current_tick,actors=actors,player=self.state('player'))

    def compare_world(self, expected, actual):
        self.require(set(expected['actors'])==set(actual['actors']),'Restored active actor identities differ')
        for identity, before in expected['actors'].items():
            after=actual['actors'][identity]
            for field in ('fields','matrix','actions','script','timers','attachment'):
                self.require(before[field]==after[field],f'Actor {identity} restored {field} differs: expected {before[field]}, actual {after[field]}')
        self.details['restored_actor_count']=len(actual['actors'])
        self.details['restored_timer_count']=sum(len(row['timers']) for row in actual['actors'].values())
        self.details['restored_attachments']={identity:row['attachment'] for identity,row in actual['actors'].items() if row['attachment']}
        self.save()

    def equipment(self, game_data):
        from e2_gameplay_steps import Journey
        actor=self.value('DAT_0047a470')
        field=lambda offset,kind='short':self.value(f'*({kind}*)({actor}+{offset})')
        context=dict(value=self.value,field=field,actor=actor,prefix=self.prefix+'-equipment',
                     advance=self.step,key=self.key,set_phase_title=lambda name:None,
                     checkpoint=lambda label:self.states.append(self.state(label)),
                     snapshot=self.state,observe_camera=lambda:self.state('camera')['camera'],
                     game_data_root=game_data)
        equipment=Journey(context,'sword',{})
        equipment.sword()
        self.details['equipment']=equipment.details;self.save()

    def menu_save(self, slot, label, expected_path):
        journey=self
        snapshots=[]
        class SaveExit(gdb.FinishBreakpoint):
            def stop(self):
                result=int(self.return_value)&0xffffffff
                journey.details.setdefault('save_close_results',[]).append(result);journey.save()
                if result:
                    print('FAIL: save writer close returned '+hex(result),flush=True)
                    return True
                return False
        class SaveEntry(gdb.Breakpoint):
            def stop(self):
                # Stop before any unexpected writer could overwrite an occupied private copy.
                if journey.value('param_1')!=slot:
                    raise gdb.GdbError('Writer targeted a slot outside this probe ownership')
                SaveExit(internal=True)
                snapshots.append(journey.world())
                Path(expected_path).write_text(json.dumps(snapshots[-1],indent=2)+'\n')
                return False
        watch=SaveEntry('FUN_00453920',internal=True)
        self.open();self.click(0x643b10);self.pump();self.requester(0x2a)
        self.click(0x6432f8+slot*30);self.pump()
        self.require(self.value('_DAT_0064353c')==slot,'Wrong Save selection')
        # The first cycle begins with an empty slot; repeated cycles retain its label.
        existing=bytes(gdb.selected_inferior().read_memory(0x643434+slot*26,26)).split(b'\0')[0]
        if not existing:
            for character in label:
                self.key(ord(character),True);self.pump(1);self.key(ord(character),False)
        self.click(0x643de4)
        self.menu.delete();self.menu=None;self.frame.enabled=True;self.step(3)
        watch.delete()
        self.require(len(snapshots)==1,'Save did not dispatch exactly once')
        self.require(self.value('_DAT_00643650')==0,'Save did not resume gameplay')
        return snapshots[0]

    def menu_load(self, slot, expected):
        self.open();self.click(0x643cc4);self.pump();self.requester(0x29)
        self.click(0x642fb0+slot*30);self.pump()
        self.require(self.value('_DAT_0064353c')==slot,'Load rejected the test-owned save')
        entry=gdb.Breakpoint('FUN_004544a4',internal=True)
        self.click(0x643de4);self.menu.enabled=False
        gdb.execute('continue',to_string=True)
        self.require(gdb.selected_frame().name()=='FUN_004544a4','Loader entry not reached')
        entry.delete();finished=gdb.FinishBreakpoint(internal=True)
        gdb.execute('continue',to_string=True)
        self.require(not finished.is_valid(),'Loader stopped before returning')
        self.compare_world(expected,self.world())
        self.menu.enabled=True;self.pump();self.requester(0x28);self.close()
        self.require(self.state('resumed')['camera']==expected['player']['camera'],'Saved camera not reconstructed')

    def move(self):
        before=self.state('move.before')
        attachments={identity:row for identity,row in self.world()['actors'].items()
                     if row['attachment'] and row['attachment']['owner']==0}
        attempts=[]
        animation=[]
        for key in (38,40):
            self.key(key,True)
            for _ in range(4):
                self.step(15);sample=self.state('move.animation')
                animation.append([sample['action_id'],sample['progress']])
            self.key(key,False);self.step(30)
            after=self.state('move.after')
            attempts.append(dict(key=key,state=after))
            if before['position']!=after['position']:break
        moved=self.world()['actors']
        for identity,row in attachments.items():
            self.require(moved[identity]['attachment']==row['attachment'] and row['attachment']['reciprocal'],
                         'Restored attachment lost reciprocal ownership during movement')
            self.require(any(row['fields'][hex(offset)]!=moved[identity]['fields'][hex(offset)]
                             for offset in (0x84,0x86,0x88)),
                         'Restored attachment did not follow moving Joe')
        self.details.setdefault('movement',[]).append(dict(before=before,attempts=attempts,after=after,
            animation=animation,following_attachments=list(attachments)));self.save()
        self.require(before['position']!=after['position'],'Bounded forward/backward input did not change gameplay state')
        self.require(after['health']>0,'Joe did not survive restored input')
        self.require(len({tuple(sample) for sample in animation})>1,'Restored animation did not advance')

    def interact(self):
        actor=self.value('DAT_0047a470')
        self.key(17,True);self.key(38,True)
        for _ in range(24):
            self.step(15)
            slot=self.value(f'*(short*)({actor}+0x96)')
            if 0xb8<=slot<=0xd3:break
        else:raise gdb.GdbError('Attack input did not start an action after loading')
        state=self.state('restored.attack')
        representation=self.value(f'*(unsigned int*)({actor}+0x11e)')
        expected=self.value(f'*(short*)({representation}+2+{slot}*2)')
        self.require(state['action_id']==expected,'Restored attack did not use its original animation')
        self.details.setdefault('interaction',[]).append(dict(slot=slot,state=state));self.save()
        self.key(38,False);self.key(17,False);self.step(90)


def run(prefix, runtime, game_data, slot, mode, equipment, expected_path):
    journey=PersistenceJourney(prefix,{'checks':['Menus.Gameplay.SaveDialog']},False,'save-load',game_data,0,False)
    journey.frame=gdb.Breakpoint('FUN_00415d40',internal=True);journey.frame.condition=journey.HORSE
    command='run --game-data-dir '+json.dumps(game_data)+' --data-dir '+json.dumps(runtime)+' --record off --run-recon'
    gdb.execute(command,to_string=True)
    journey.require(gdb.selected_frame().name()=='FUN_00415d40','Opening intro not reached')
    journey.frame.condition=None;journey.initial=journey.state('initial')
    if mode=='same':
        journey.reach_pedestal();journey.reach_gameplay()
        if equipment:journey.equipment(game_data)
        for cycle in range(2):
            expected=journey.menu_save(slot,'E2RTEST',expected_path)
            journey.move();journey.menu_load(slot,expected);journey.move();journey.interact()
    else:
        expected=json.loads(Path(expected_path).read_text())
        journey.menu_load(slot,expected);journey.move();journey.interact()
    journey.stage='Gameplay';journey.quit()
    journey.complete=True;journey.save()
    result=dict(probe_complete=True,mode=mode,slot=slot,native_exit_code=journey.exit_codes[-1],
                updates=journey.updates,details=journey.details)
    Path(prefix+'.json').write_text(json.dumps(result,indent=2)+'\n')
    print('PASS: '+mode+' menu persistence, restored fields and subsequent input; native exit zero',flush=True)
    return result


def run_failure(prefix, runtime, game_data, slot, failure):
    journey=PersistenceJourney(prefix,{'checks':['Menus.Gameplay.SaveDialog']},False,'save-load-failure',game_data,0,False)
    journey.frame=gdb.Breakpoint('FUN_00415d40',internal=True);journey.frame.condition=journey.HORSE
    gdb.execute('run --game-data-dir '+json.dumps(game_data)+' --data-dir '+json.dumps(runtime)+
                ' --record off --run-recon',to_string=True)
    journey.frame.condition=None;journey.initial=journey.state('initial')
    journey.reach_pedestal();journey.reach_gameplay()
    before=journey.world()
    save=failure=='save-open'
    journey.open();journey.click(0x643b10 if save else 0x643cc4);journey.pump()
    journey.requester(0x2a if save else 0x29)
    journey.click((0x6432f8 if save else 0x642fb0)+slot*30);journey.pump()
    selected=journey.value('(int)_DAT_0064353c')
    stopped=False
    if failure=='empty':
        journey.require(selected==-1,'Empty Load slot was accepted')
        journey.click(0x643de4);journey.pump();journey.requester(0x15)
        journey.details['message']=journey.value('*(unsigned int*)0x47a53c')
        journey.click(0x643de4);journey.pump();journey.requester(0x29)
        journey.key(27,True);journey.key(27,False);journey.pump();journey.requester(0x28);journey.close()
    elif failure in ('truncated','missing'):
        journey.require(selected==slot,'Invalid-file test slot not selected')
        if failure=='missing':(Path(runtime)/'Saved'/f'{slot:04d}.ECS').unlink()
        fatal=gdb.Breakpoint('E2R_LoadSaveFailure',internal=True)
        journey.click(0x643de4);journey.menu.enabled=False
        gdb.execute('continue',to_string=True)
        journey.require(gdb.selected_frame().name()=='E2R_LoadSaveFailure','Expected loader failure not reached')
        message=gdb.parse_and_eval('message').string()
        journey.require(message==('open failed' if failure=='missing' else 'truncated resource records'),
                        'Unexpected failure boundary: '+message)
        after=journey.world()
        if failure=='missing':journey.compare_world(before,after)
        else:journey.require(not after['actors'] and not journey.value('DAT_0047a470'),
                             'Truncated load did not expose its destructive boundary')
        journey.details.update(message=message,before=before,at_failure=after)
        fatal.delete();gdb.execute('kill',to_string=True);stopped=True
    elif failure=='unsupported':
        journey.require(selected==slot,'Unsupported save not selected')
        journey.click(0x643de4);journey.pump();journey.requester(0x2e)
        text=bytes(gdb.selected_inferior().read_memory(0x64403a,102))
        journey.require(b"Can't load game" in text and b'Game was saved in old version' in text,
                        'Unsupported-version explanation missing')
        journey.click(0x643de4);journey.pump();journey.requester(0x28);journey.close()
    else:
        for character in 'E2RTEST':
            journey.key(ord(character),True);journey.pump(1);journey.key(ord(character),False)
        journey.click(0x643de4);journey.pump();journey.requester(0x15)
        pointer=journey.value('*(unsigned int*)0x47a53c')
        message=gdb.Value(pointer).cast(gdb.lookup_type('char').pointer()).string()
        journey.require(message=="Can't open file to save game",'Save-open explanation missing')
        journey.details['message']=message
        journey.click(0x643de4);journey.menu.delete();journey.menu=None;journey.frame.enabled=True;journey.step(3)
        journey.require((Path(runtime)/'Saved'/f'{slot:04d}.ECS').is_dir(),'Failed save changed its blocker')
    if not stopped:
        after=journey.state('after-error')
        journey.require(after['identity']==0 and after['health']>0 and set(journey.world()['actors'])==set(before['actors']),
                        'Non-destructive rejection lost player/world')
        journey.move();journey.stage='Gameplay';journey.quit()
    result=dict(probe_complete=True,failure_case=failure,details=journey.details,
                native_exit_code=None if stopped else journey.exit_codes[-1],
                stopped_before_unqualified_fatal_cleanup=stopped)
    Path(prefix+'.json').write_text(json.dumps(result,indent=2)+'\n')
    return result
