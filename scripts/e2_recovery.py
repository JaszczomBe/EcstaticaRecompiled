"""Queryable recovery evidence and decompiler-risk inventory, generated on demand."""
import csv
import hashlib
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parent.parent


def index(root=ROOT, observation=None):
    source = (root/'E2Recomp/reconstructed/E2Recomp_recon.c').read_text()
    markers = list(re.finditer(r'^/\* ([0-9a-fA-F]{8}) \*/$', source, re.M))
    evidence = {}
    files = list((root/'scripts').glob('check-e2-*.py')) + list((root/'docs/journal/entries').glob('*.md'))
    for path in files:
        for address in set(re.findall(r'\b(?:FUN_|0x)(004[0-9a-fA-F]{5})\b', path.read_text())):
            evidence.setdefault(address.lower(), []).append(str(path.relative_to(root)))
    generator = (root/'E2Recomp/tools/GenerateRecon.js').read_text()
    results = []
    for i, marker in enumerate(markers):
        address = marker[1].lower()
        body = source[marker.end():markers[i+1].start() if i+1 < len(markers) else len(source)]
        definition = re.search(r'^([^\n;]+\([^\n;]*\))\s*\{', body, re.M)
        if not definition:
            continue
        placeholders = sorted(set(re.findall(r'\b(?:in_[A-Z][A-Z0-9_]*|unaff_[A-Z][A-Z0-9_]*|extraout_[A-Z][A-Za-z0-9_]*)\b', body)))
        tests = [p for p in evidence.get(address, []) if p.startswith('scripts/')]
        journals = [p for p in evidence.get(address, []) if p.startswith('docs/')]
        results.append(dict(address='0x'+address, name='FUN_'+address, signature=definition[1].strip(),
                            source='E2Recomp/reconstructed/E2Recomp_recon.c',
                            line=source.count('\n',0,marker.start())+1,
                            placeholders=placeholders, placeholder_count=len(placeholders),
                            fixtures=tests, journals=journals,
                            generator_mentions=('FUN_'+address) in generator,
                            evidence_status='has referenced fixtures; inspect their intercepted dependencies' if tests
                            else 'no function-address fixture reference found',
                            heuristic_risk=len(placeholders)*(1 if tests else 2)))
    results.sort(key=lambda r:(-r['heuristic_risk'],r['address']))
    warnings = []
    for path in (root/'docs/implementations/playable-sdl-runtime/playable-sdl-runtime.md', root/'docs/replay.md'):
        for link in re.findall(r'\]\(([^)#]+)(?:#[^)]*)?\)', path.read_text()):
            if '://' not in link and not (path.parent/link).exists():
                warnings.append(dict(source=str(path.relative_to(root)),missing_target=link))
    return dict(schema='e2debug.recovery-index.1', source_sha256=hashlib.sha256(source.encode()).hexdigest(),
                scope='Textual references and placeholder counts are investigation hints, not verified coverage or correctness',
                warnings=warnings, functions=results)
