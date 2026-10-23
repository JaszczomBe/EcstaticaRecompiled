"""Run Clang's analysis-only diagnostics using the actual build configuration."""
import json
from pathlib import Path
import re
import shlex
import subprocess
import tempfile
from e2_recovery import ROOT, index


def diagnose(build: Path, function=None, limit=50):
    database = json.loads((build/'compile_commands.json').read_text())
    entry = next((e for e in database if Path(e['file']).name == 'E2Recomp_recon.c'), None)
    if entry is None:
        raise ValueError('Build database contains no reconstructed C compilation')
    # Only invoke the configured Clang compiler, using an argv vector. No command
    # from the database is passed to a shell, and no build output is overwritten.
    command = entry.get('arguments') or shlex.split(entry['command'])
    if not Path(command[0]).name.startswith('clang'):
        raise ValueError('Targeted diagnostics currently require Clang')
    filtered, skip = [], False
    for argument in command:
        if skip:
            skip = False
            continue
        if argument in ('-o', '-MF', '-MT', '-MQ'):
            skip = True
        elif argument not in ('-c', '-w', '-MD', '-MMD', '-MP'):
            filtered.append(argument)
    filtered += ['-fsyntax-only', '-fno-color-diagnostics', '-Wno-error',
                 '-Wuninitialized', '-Wsometimes-uninitialized', '-Wreturn-type']
    functions = sorted(index()['functions'], key=lambda f:f['line'])
    selected = None
    if function:
        address = function.lower().removeprefix('fun_').removeprefix('0x').zfill(8)
        selected = next((f for f in functions if f['address'] == '0x'+address), None)
        if selected is None:
            raise ValueError('Unknown function address')
    with tempfile.TemporaryFile() as output:
        result = subprocess.run(filtered, cwd=entry['directory'], stdout=output, stderr=output, timeout=60)
        output.seek(0)
        text = output.read(32*1024*1024).decode(errors='replace')
    diagnostics = []
    for match in re.finditer(r'^(.+?):(\d+):(\d+): (warning|error): (.*)$', text, re.M):
        file, line, column, severity, message = match.groups()
        line = int(line)
        owner = None
        if Path(file).name == 'E2Recomp_recon.c':
            owner = next((f for f in reversed(functions) if f['line'] <= line), None)
        if selected and (owner is None or owner['address'] != selected['address']):
            continue
        diagnostics.append(dict(file=file, line=line, column=int(column), severity=severity,
                                message=message, function=owner['name'] if owner else None))
    return dict(schema='e2debug.diagnostics.1', compiler_returncode=result.returncode,
                diagnostic_count=len(diagnostics), diagnostics=diagnostics[:limit],
                scope='Analysis-only warnings using current source and build flags; decompiler placeholders require original-code investigation')
