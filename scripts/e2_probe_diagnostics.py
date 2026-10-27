"""Bound agent probes and retain stopped-thread evidence before terminating GDB."""
import json
from pathlib import Path
import signal
import subprocess
import time


def install(prefix):
    """Called inside GDB, before starting the inferior; never writes game state."""
    import gdb

    # A direct probe may reuse its output prefix. These describe this process,
    # whereas the suite normally gives every execution a fresh directory.
    for suffix in ('-heartbeat', '-stall.json', '-stopped.json'):
        Path(prefix + suffix).unlink(missing_ok=True)
    heartbeat = Path(prefix + '-heartbeat')
    last_heartbeat = 0.0

    def progress(event):
        nonlocal last_heartbeat
        now = time.monotonic()
        if now - last_heartbeat >= 0.25:
            heartbeat.touch()
            last_heartbeat = now

    gdb.events.cont.connect(progress)
    gdb.events.stop.connect(progress)
    gdb.execute('set breakpoint pending on', to_string=True)
    gdb.execute('catch throw std::bad_alloc', to_string=True)
    allocation_catch = gdb.breakpoints()[-1]

    def stopped(event):
        allocation = allocation_catch in getattr(event, 'breakpoints', ())
        if not allocation and not isinstance(event, gdb.SignalEvent):
            return
        pid = gdb.selected_inferior().pid
        result = dict(pid=pid, signal=getattr(event, 'stop_signal', None),
                      exception='std::bad_alloc' if allocation else None,
                      time=time.time(), commands={}, process={})
        gdb.execute('set print elements 32', to_string=True)
        for command in ('thread apply all bt 32', 'bt full 16', 'info registers', 'info args'):
            try:
                result['commands'][command] = gdb.execute(command, to_string=True)[:262144]
            except gdb.error as error:
                result['commands'][command] = str(error)
        for name in ('status', 'maps', 'limits'):
            try:
                result['process'][name] = Path(f'/proc/{pid}/{name}').read_text()[:262144]
            except OSError as error:
                result['process'][name] = str(error)
        Path(prefix + '-stopped.json').write_text(json.dumps(result, indent=2) + '\n')
        gdb.write('PROBE STOP: saved ' + prefix + '-stopped.json\n')

    gdb.events.stop.connect(stopped)


def communicate(process, prefix, timeout, stall_timeout=30, capture_timeout=5):
    """Interrupt stalled GDB once, allowing bounded stack capture before cleanup.

    Inspection frames cover uninterrupted startup; GDB events cover normal
    breakpoint-driven gameplay even if inspection reaches its observation cap.
    The caller owns process-tree termination after TimeoutExpired.
    """
    started = last_progress = time.monotonic()
    latest = 0
    interrupted = None
    stall_path = Path(prefix + '-stall.json')
    while True:
        try:
            output, _ = process.communicate(timeout=min(1, capture_timeout))
            return output, stall_path.is_file()
        except subprocess.TimeoutExpired:
            pass
        now = time.monotonic()
        if interrupted is not None:
            if now - interrupted >= capture_timeout:
                raise subprocess.TimeoutExpired(process.args, timeout)
            continue
        paths = [Path(prefix + '-heartbeat')]
        paths.extend(Path(prefix + '-runtime/logs').glob('session*/inspection/timeline.csv'))
        for path in paths:
            try:
                modified = path.stat().st_mtime_ns
            except OSError:
                continue
            if modified > latest:
                latest = modified
                last_progress = now
        reason = ('probe timeout' if now - started >= timeout else
                  'no debugger or inspection progress' if now - last_progress >= stall_timeout else None)
        if reason:
            stall_path.write_text(json.dumps(dict(reason=reason, gdb_pid=process.pid,
                elapsed=now-started, idle=now-last_progress, time=time.time()), indent=2) + '\n')
            process.send_signal(signal.SIGINT)
            interrupted = now
