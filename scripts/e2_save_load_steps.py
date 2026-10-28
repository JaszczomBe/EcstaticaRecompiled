"""Input-only persistence journeys, loaded inside GDB by the bounded save/load probe."""
import hashlib
import json
from pathlib import Path
import struct

import gdb

from e2_menu_steps import MenuJourney

# Fields actually serialized in the active-actor section, excluding its duplicate +0x98.
FIELDS = (0x82,0x84,0x86,0x88,0x8a,0x8c,0x8e,0x90,0x92,0x94,
          0x96,0x98,0xe8,0xea,0xec,0xee,0xf0,0x182,0x186,0x184)


class PersistenceJourney(MenuJourney):
    def open(self):
        super().open()
        bounds=[self.value(f'*(short*)(0x47a588+{offset})') for offset in (16,18,20,22,24,26)]
        self.require(bounds==[110,530,105,375,420,270],'Main requester differs from original record geometry')
        items=[self.item(address) for address in (0x643b30,0x643b10,0x643cc4,0x6439d8,0x643ca4,0x643780)]
        self.require(all(item['label'] for item in items),'Main requester has an empty button label')
        self.details['main_menu_items']=items
        if 'main_menu_bounds' not in self.details:
            self.details['main_menu_bounds']=bounds
            gdb.execute('call (int)e2r_write_surface_set('+json.dumps(self.prefix+'-main-menu')+')',to_string=True)
            self.save()

    def preview_pages(self):
        read=lambda address,size:bytes(gdb.selected_inferior().read_memory(address,size))
        visible=self.value('DAT_0047a279 >> 24')&1
        pages={}
        for surface in range(4):
            if surface<2:
                symbol='DAT_0047d0cc' if surface==visible else 'DAT_0047d0d0'
                descriptor=f'((E2R_DDSurface*){symbol})'
                base=self.value(descriptor+'->pixels');pitch=self.value(descriptor+'->pitch')
            else:
                base=self.value('_DAT_00636158' if surface==2 else '_DAT_0063615c')
                pitch=self.value('_DAT_006401ec')
            pages[str(surface)]=b''.join(read(base+(162+row)*pitch+72,160) for row in range(120))
        return pages

    def preview(self, slot, label, before):
        bounds=[self.value(f'*(short*)(0x47a5a4+{offset})') for offset in (16,18,20,22,24,26)]
        self.require(bounds==[50,590,109,371,540,262],'Slot requester differs from original record geometry')
        requester=self.value('*(unsigned short*)((char*)&DAT_0047a45e+2)')
        first,count=(0x642fb0,10) if requester==0x29 else (0x6432f8,9)
        items=[self.item(first+index*30) for index in range(count)]
        for index,item in enumerate(items):
            y=109+(37+index*11)*3//2
            self.require(item['bounds']==[254,570,y,y+12],'Save slot row is misplaced or extends outside its panel')
        self.details['slot_menu_layout']=dict(bounds=bounds,items=items,preview=[72,232,162,282])
        path=Path(self.runtime)/'Saved'/f'{slot:04d}.ECS'
        data=path.read_bytes()
        thumbnail=data[28:4828]
        expected=bytes(thumbnail[(column//2)*60+row//2] for row in range(120) for column in range(160)) if len(thumbnail)==4800 else bytes(160*120)
        pages=self.preview_pages()
        row=dict(label=label,slot=slot,expected_sha256=hashlib.sha256(expected).hexdigest(),
                 matches={key:page==expected for key,page in pages.items()},
                 physical_unchanged={key:pages[key]==before[key] for key in ('0','1')})
        self.details.setdefault('previews',[]).append(row);self.save()
        self.present()
        capture=self.prefix+'-'+label
        gdb.execute('call (int)e2r_write_surface_set('+json.dumps(capture)+')',to_string=True)
        self.require(all(row['matches'][key] for key in ('2','3')),'Saved thumbnail does not match both displayed menu pages')
        self.require(all(row['physical_unchanged'].values()),'Preview changed a physical gameplay page')

    def cancel_previews(self, slot):
        loads=[]
        class ObserveLoad(gdb.Breakpoint):
            def stop(self):
                loads.append(True)
                return False
        watch=ObserveLoad('FUN_004544a4',internal=True)
        self.open();self.click(0x643cc4);self.pump();self.requester(0x29)
        initial=self.preview_pages()
        empty=[i for i in range(9) if i!=slot and (Path(self.runtime)/'Saved'/f'{i:04d}.ECS').read_bytes()==b'\r\n\r\n']
        sequence=[slot,*empty[:1],slot]
        for index,selected in enumerate(sequence):
            before=self.preview_pages()
            self.click(0x642fb0+selected*30);self.pump()
            self.preview(selected,'cancel-preview-'+str(index),before)
        self.key(27,True);self.key(27,False);self.pump();self.requester(0x28)
        returned=self.preview_pages()
        self.require(all(returned[key]==initial[key] for key in ('0','1')),
                     'Cancelling Load left thumbnail pixels in gameplay pages')
        self.close();self.step(30)
        watch.delete()
        self.require(not loads,'Cancelling previews dispatched the game loader')
        self.details['cancel_preview_load_calls']=len(loads)
        self.details['cancel_preview_resumed']=self.state('cancel-preview-resumed');self.save()

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
        preview_before=self.preview_pages()
        self.click(0x6432f8+slot*30);self.pump()
        self.preview(slot,'save-preview-'+str(len(self.details.get('save_close_results',[]))),preview_before)
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
        before=self.preview_pages()
        self.click(0x642fb0+slot*30);self.pump()
        self.preview(slot,'load-preview-'+str(len(self.details.get('previews',[]))),before)
        self.require(self.value('_DAT_0064353c')==slot,'Load rejected the test-owned save')
        entry=gdb.Breakpoint('FUN_004544a4',internal=True)
        self.click(0x643de4);self.menu.enabled=False
        gdb.execute('continue',to_string=True)
        self.require(gdb.selected_frame().name()=='FUN_004544a4','Loader entry not reached')
        entry.delete();finished=gdb.FinishBreakpoint(internal=True)
        gdb.execute('continue',to_string=True)
        self.require(not finished.is_valid(),'Loader stopped before returning')
        self.compare_world(expected,self.world())
        self.menu.enabled=True;self.frame.enabled=True
        dismissal=[]
        for _ in range(12):
            gdb.execute('continue',to_string=True)
            dismissal.append(dict(frame=gdb.selected_frame().name(),modal=self.value('_DAT_00643650'),
                requester=self.value('*(unsigned short*)((char*)&DAT_0047a45e+2)'),
                closed=self.value('_DAT_006443d0'),loaded=self.value('E2R_requester_load_succeeded'),
                backdrop_depth=self.value('E2R_requester_backdrop_depth')))
            if dismissal[-1]['modal']==0 and dismissal[-1]['requester']==0 and dismissal[-1]['backdrop_depth']==0:break
        else:
            self.details['dismissal_failure']=dict(samples=dismissal,stack=gdb.execute('bt 16',to_string=True));self.save()
            raise gdb.GdbError('Successful Load did not automatically dismiss the menu')
        self.menu.delete();self.menu=None;self.step(3)
        self.require(self.value('_DAT_00643650')==0,'Loaded game remains modal')
        self.details['load_auto_dismissed']=True;self.save()
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


def run(prefix, runtime, game_data, slot, mode, equipment, expected_path, hud=False):
    journey=PersistenceJourney(prefix,{'checks':['Menus.Gameplay.SaveDialog']},False,'save-load',game_data,0,False)
    journey.runtime=runtime
    journey.frame=gdb.Breakpoint('FUN_00415d40',internal=True);journey.frame.condition=journey.HORSE
    command='run --game-data-dir '+json.dumps(game_data)+' --data-dir '+json.dumps(runtime)+' --record off --run-recon'
    gdb.execute(command,to_string=True)
    journey.require(gdb.selected_frame().name()=='FUN_00415d40','Opening intro not reached')
    journey.frame.condition=None;journey.initial=journey.state('initial')
    if hud:
        from e2_hud_steps import HudChecks
        hud_checks=HudChecks(journey)
        hud_checks.check_default()
    if mode=='same':
        journey.reach_pedestal();journey.reach_gameplay()
        if equipment:journey.equipment(game_data)
        if hud:
            hud_checks.switches('gameplay')
            hud_checks.menu_switches()
        for cycle in range(2):
            if hud:hud_checks.select(cycle,'before-save')
            expected=journey.menu_save(slot,'E2RTEST',expected_path)
            if hud:hud_checks.check_mode(cycle)
            if cycle==0:journey.cancel_previews(slot)
            journey.move();journey.menu_load(slot,expected);journey.move();journey.interact()
            if hud:
                hud_checks.check_mode(cycle)
                hud_checks.switches('load-'+str(cycle))
    else:
        expected=json.loads(Path(expected_path).read_text())
        journey.menu_load(slot,expected);journey.move();journey.interact()
        if hud:hud_checks.switches('fresh-load')
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
