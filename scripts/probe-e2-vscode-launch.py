#!/usr/bin/env python3
"""Run the actual launch.json game entry through the installed cppdbg adapter.

Uses the current desktop backend and physical input, with no dummy SDL override,
alternate game command, injected inputs or gameplay breakpoints. Success means
the launch survived the bounded observation, not full gameplay acceptance.
"""
import argparse
import json
import os
from pathlib import Path
import queue
import re
import signal
import subprocess
import threading
import time

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('exe', type=Path, help='Executable selected by the CMake preset')
parser.add_argument('--adapter', type=Path, help='OpenDebugAD7 path; otherwise discover in ~/.vscode/extensions')
parser.add_argument('--record', choices=['off', 'auto'], default='off',
                    help='Agent runs default off; auto explicitly verifies human F5 recording')
parser.add_argument('--seconds', type=float, default=30)
parser.add_argument('--output', type=Path, default=Path('/tmp/e2-vscode-launch'))
args = parser.parse_args()
if args.seconds <= 0:
    parser.error('--seconds must be positive')
root = Path(__file__).resolve().parent.parent
launch = json.loads((root / '.vscode/launch.json').read_text())['configurations'][0]
assert launch['type'] == 'cppdbg' and launch['request'] == 'launch'
assert launch['program'] == '${command:cmake.launchTargetPath}'
assert launch['cwd'] == '${command:cmake.getLaunchTargetDirectory}'
launch.setdefault('environment', []).append({'name':'E2R_RECORD','value':args.record})
launch['program'] = str(args.exe.resolve(strict=True))
launch['cwd'] = str(args.exe.resolve().parent)
for item in launch.get('environment', []):
    item['value'] = re.sub(r'\$\{env:([^}]+)\}', lambda m: os.environ.get(m[1], ''), item['value'])
if args.adapter:
    adapter = args.adapter
else:
    adapters = list((Path.home() / '.vscode/extensions').glob('ms-vscode.cpptools-*/debugAdapters/bin/OpenDebugAD7'))
    if not adapters:
        parser.error('No installed cppdbg adapter; pass --adapter')
    adapter = max(adapters, key=lambda p: p.stat().st_mtime)
prefix = args.output.resolve()
prefix.parent.mkdir(parents=True, exist_ok=True)
messages = queue.Queue()
sequence = 0

with open(str(prefix) + '.jsonl', 'w') as log, open(str(prefix) + '-adapter.log', 'w') as error_log:
    process = subprocess.Popen([str(adapter)], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                               stderr=error_log, start_new_session=True)

    def read_messages():
        try:
            while True:
                headers = {}
                while True:
                    line = process.stdout.readline()
                    if not line:
                        messages.put({'type': 'adapter_eof'})
                        return
                    if line in (b'\r\n', b'\n'):
                        break
                    key, value = line.decode().split(':', 1)
                    headers[key.lower()] = value.strip()
                messages.put(json.loads(process.stdout.read(int(headers['content-length']))))
        except Exception as error:
            messages.put({'type': 'read_error', 'error': str(error)})

    threading.Thread(target=read_messages, daemon=True).start()

    def send(command, arguments):
        global sequence
        sequence += 1
        body = json.dumps(dict(seq=sequence, type='request', command=command, arguments=arguments)).encode()
        process.stdin.write(f'Content-Length: {len(body)}\r\n\r\n'.encode() + body)
        process.stdin.flush()

    def record(message):
        log.write(json.dumps(message) + '\n')
        log.flush()

    started = configured = False
    stopped = stack = failure = run_start = None
    observed_seconds = 0
    deadline = time.monotonic() + args.seconds + 30
    send('initialize', dict(clientID='e2-launch-probe', adapterID='cppdbg', pathFormat='path',
                           linesStartAt1=True, columnsStartAt1=True,
                           supportsRunInTerminalRequest=False))
    try:
        while time.monotonic() < deadline:
            if run_start and not stopped:
                observed_seconds = time.monotonic() - run_start
                if observed_seconds >= args.seconds:
                    break
            try:
                message = messages.get(timeout=.25)
            except queue.Empty:
                continue
            record(message)
            kind = message.get('type')
            command = message.get('command')
            event = message.get('event')
            if kind == 'response' and not message.get('success'):
                failure = message
                break
            if kind == 'response' and command == 'initialize':
                send('launch', launch)
                started = True
            elif kind == 'event' and event == 'initialized' and not configured:
                send('configurationDone', {})
                configured = True
            elif kind == 'response' and command == 'launch':
                run_start = time.monotonic()
            elif kind == 'event' and event == 'stopped':
                stopped = message
                send('stackTrace', dict(threadId=message['body']['threadId'], startFrame=0, levels=30))
            elif kind == 'response' and command == 'stackTrace':
                stack = message
                break
            elif kind == 'event' and event in ('exited', 'terminated'):
                failure = message
                break
            elif kind in ('request', 'read_error', 'adapter_eof'):
                failure = message
                break
        else:
            failure = {'error': 'adapter startup/stack capture timeout'}
    finally:
        try:
            send('disconnect', dict(restart=False, terminateDebuggee=True))
            end = time.monotonic() + 5
            while time.monotonic() < end:
                try:
                    message = messages.get(timeout=.2)
                except queue.Empty:
                    continue
                record(message)
                if message.get('type') == 'response' and message.get('command') == 'disconnect':
                    break
        except OSError:
            pass
        try:
            process.wait(timeout=3)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGTERM)
            process.wait(timeout=3)

report = dict(adapter=str(adapter), program=launch['program'], cwd=launch['cwd'], args=launch['args'],
              started=started, configured=configured, observed_seconds=round(observed_seconds, 2),
              stopped=stopped, stack=stack, failure=failure)
Path(str(prefix) + '.json').write_text(json.dumps(report, indent=2))
success = started and configured and run_start and not stopped and not failure
print(f'{"PASS" if success else "FAIL"}: launch.json via cppdbg; observed {observed_seconds:.2f} seconds')
print(f'Evidence: {prefix}.json, {prefix}.jsonl and {prefix}-adapter.log')
raise SystemExit(0 if success else 1)
