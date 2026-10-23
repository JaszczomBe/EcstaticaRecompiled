#!/usr/bin/env python3
"""Verify tree maintenance, orphan/broken-link detection and upstream preservation."""
import importlib.util
from pathlib import Path
import tempfile

spec=importlib.util.spec_from_file_location('e2_docs_tree',Path(__file__).with_name('check-docs-tree.py'))
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
with tempfile.TemporaryDirectory(prefix='e2-docs-contract-') as temporary:
    root=Path(temporary);module.ROOT=root
    files={
        'README.md':'# Project\n',
        'docs/README.md':'# Docs\n',
        'docs/start.md':'# Start\n\n```text\n[example](not-a-real-target.md)\n```\n',
        'dep/README.md':'# Dependencies\n',
        'docs/dependencies/README.md':'# Upstream docs\n',
        'dep/SDL/README.md':'# Vendor\n\n[Upstream convention](missing-upstream-target.md)\n',
        'docs/templates/README.md':'# Templates\n',
        'docs/templates/example.md':'# Template\n\n[Slot](../<document>.md)\n',
    }
    for name,text in files.items():
        path=root/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_text(text)
    paths=module.documents(root);parents={p:module.parent(p) for p in paths}
    assert module.check(paths,parents),'Unlinked documents accepted'
    module.update(paths,parents);assert not module.check(paths,parents)
    before={p:(root/p).read_bytes() for p in paths}
    module.update(paths,parents)
    assert before=={p:(root/p).read_bytes() for p in paths},'Navigation updates are not idempotent'
    assert (root/'dep/SDL/README.md').read_text()==files['dep/SDL/README.md']
    (root/'docs/new.md').write_text('# Unlinked\n')
    paths=module.documents(root);parents={p:module.parent(p) for p in paths}
    assert any('missing child link' in e for e in module.check(paths,parents))
    module.update(paths,parents);assert not module.check(paths,parents)
    with (root/'docs/start.md').open('a') as stream:stream.write('\n[Broken](lost.md)\n')
    errors=module.check(paths,parents)
    assert any('lost.md' in e for e in errors) and not any('not-a-real-target' in e for e in errors)
    parents[Path('README.md')]=Path('docs/README.md')
    assert any('cycle' in e for e in module.check(paths,parents))
print('PASS: parent/child/root ownership, orphan and broken-target detection, cycles, template/fence handling, idempotence, unchanged upstream files')
