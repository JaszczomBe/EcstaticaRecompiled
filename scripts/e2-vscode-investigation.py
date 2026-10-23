"""Loaded by GDB from launch.json; observes stops without resuming or repairing state."""
import os
from pathlib import Path
import sys
import gdb

sys.path.insert(0,str(Path(__file__).resolve().parent))
import e2_f5

record = None
startup = None
requesters = []


def diagnostic(error):
    gdb.write(f'F5 investigation: {error}\n',gdb.STDERR)


class InvestigationStart(gdb.Breakpoint):
    def stop(self):
        global record
        try:
            # Observe the first sample, after ASan's startup prologue has stored
            # arguments. Entry-line DWARF can expose uninitialized argument slots.
            frame=gdb.newest_frame()
            while frame and not (frame.name() or '').startswith('E2R_InspectStart'):
                frame=frame.older()
            if frame is None:raise gdb.GdbError('inspection startup frame is unavailable')
            session = Path(frame.read_var('session').string())
            executable = Path(gdb.current_progspace().filename).absolute()
            record = e2_f5.begin(session,executable,gdb.selected_inferior().pid)
            gdb.write(f'F5 investigation: {session}/investigation\n')
        except Exception as error:
            diagnostic(error)
        return False


def stopped(event):
    if record is None:
        return
    try:
        progress = {}
        for name in ('E2R_replay_sequence','E2R_replay_last_checkpoint'):
            try: progress[name] = int(gdb.parse_and_eval(name))
            except gdb.error: pass
        detail = []
        for command in ('thread apply all bt full','info registers'):
            try: detail.append(gdb.execute(command,to_string=True))
            except gdb.error as error: detail.append(str(error))
        signal = getattr(event,'stop_signal',None)
        e2_f5.append(record,'signal' if signal else 'breakpoint', '\n'.join(detail),
                     signal=signal,**progress)
        # A signal stop is an observation, not proof of process termination.
    except Exception as error:
        diagnostic(error)


def exited(event):
    if record is None:
        return
    try:
        code = getattr(event,'exit_code',None)
        e2_f5.ended(record,dict(status='exited' if code is not None else 'terminated-by-debugger-or-signal',returncode=code))
    except Exception as error:
        diagnostic(error)


def debugger_exiting(event):
    if record is None:
        return
    try:
        state = e2_f5.finalize(record)
        gdb.write('F5 investigation: '+state.get('report',state['session'])+'\n')
    except BlockingIOError:
        pass  # postDebugTask retries after the inferior releases its lease.
    except Exception as error:
        diagnostic(error)


class RequesterEntry(gdb.Breakpoint):
    def stop(self):
        if record is not None:
            try:
                detail = gdb.execute('thread apply all bt full',to_string=True)
                e2_f5.append(record,'requester',detail,function=self.location,
                             replay_sequence=int(gdb.parse_and_eval('E2R_replay_sequence')),
                             replay_checkpoint=int(gdb.parse_and_eval('E2R_replay_last_checkpoint')))
            except Exception as error:
                diagnostic(error)
        return False


def install(event=None):
    global startup
    # cppdbg can source setup commands before executable symbols are loaded.
    if record is None and (startup is None or not startup.is_valid()):
        if gdb.lookup_global_symbol('E2R_SampleInspection') is not None:
            startup = InvestigationStart('E2R_SampleInspection',internal=True,temporary=True)
    for name in ('FUN_0043cbf0','FUN_00414e5c'):
        if gdb.lookup_global_symbol(name) is not None and not any(b.location == name for b in requesters):
            requesters.append(RequesterEntry(name,internal=True))


gdb.events.new_objfile.connect(install)
gdb.events.cont.connect(install)
gdb.events.stop.connect(stopped)
gdb.events.exited.connect(exited)
if hasattr(gdb.events,'gdb_exiting'):
    gdb.events.gdb_exiting.connect(debugger_exiting)
install()
