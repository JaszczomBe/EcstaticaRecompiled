#!/usr/bin/env python3
"""Maintain and verify the Markdown ownership tree rooted at README.md."""
from __future__ import annotations
import argparse
from collections import defaultdict
import os
from pathlib import Path
import re
import sys
from urllib.parse import unquote,urlsplit

ROOT = Path(__file__).resolve().parent.parent
NAV = re.compile(r'\n<!-- docs-tree:parent -->.*?<!-- /docs-tree:parent -->\n',re.S)
CHILDREN = re.compile(r'\n<!-- docs-tree:children -->.*?<!-- /docs-tree:children -->\n',re.S)
EXCLUDED = {'.git','build','.tmp','__pycache__','data'}


def documents(root=ROOT):
    # Include ignored-but-present vendored docs, while avoiding build/scratch trees.
    result=[]
    for directory,dirs,files in os.walk(root):
        dirs[:] = sorted(d for d in dirs if d not in EXCLUDED and not (Path(directory)/d).is_symlink())
        for name in sorted(files):
            path=Path(directory)/name
            if path.suffix.lower() in ('.md','.markdown') and not path.is_symlink():
                result.append(path.relative_to(root))
    return sorted(result)


def owned(path):
    return not path.as_posix().startswith('dep/SDL/')


def parent(path):
    name=path.as_posix()
    if name=='README.md':return None
    if not owned(path):return Path('docs/dependencies/README.md')
    direct={
        'AGENTS.md':'README.md','CONTRIBUTING.md':'README.md','CODE_OF_CONDUCT.md':'README.md',
        'docs/README.md':'README.md','E2Recomp/README.md':'README.md','dep/README.md':'README.md',
        'E2Recomp/reconstructed/README.md':'E2Recomp/README.md',
        'src/log/include/Log/README.md':'docs/debugging.md',
        'docs/dependencies/README.md':'dep/README.md',
        'docs/journal/journal.md':'docs/README.md',
    }
    if name in direct:return Path(direct[name])
    if name.startswith('docs/journal/entries/'):return Path('docs/journal/journal.md')
    if name.startswith('docs/templates/implementation-workflow.template/'):
        return Path('docs/templates/implementation-workflow.template.md')
    if name.startswith('docs/implementations/') and name!='docs/implementations/README.md':
        base=Path(*path.parts[:3])
        implementation=base/(base.name+'.md')
        if len(path.parts)==4:return Path('docs/implementations/README.md')
        if 'tasks' in path.parts:
            step=path.parent.parent
            matches=sorted((ROOT/step).glob('step-*.md'))
            if len(matches)!=1:raise ValueError(f'Expected one step owner for {path}')
            return matches[0].relative_to(ROOT)
        return implementation
    if path.parent==Path('docs'):return Path('docs/README.md')
    if path.name=='README.md':return Path('docs/README.md')
    index=path.parent/'README.md'
    if (ROOT/index).is_file():return index
    raise ValueError(f'No documentation parent assigned: {path}')


def stripped(text):
    return re.sub(r'^\s*(`{3,}|~{3,}).*?^\s*\1\s*$', '',text,flags=re.M|re.S)


def links(path,text):
    text=stripped(text)
    urls=re.findall(r'!?\[[^\]\n]*\]\((<[^>]+>|[^)]+)\)',text)
    urls+=re.findall(r'^\[[^\]]+\]:\s*(\S+)',text,re.M)
    targets=[]
    for raw in urls:
        raw=raw.strip().strip('<>')
        raw=re.split(r'\s+[\"\']',raw,maxsplit=1)[0]
        if urlsplit(raw).scheme or raw.startswith(('#','//')):continue
        target=unquote(raw.split('#',1)[0].split('?',1)[0])
        if not target:continue
        if path.as_posix().startswith('docs/templates/') and re.search(r'<[^>]+>',target):continue
        absolute=Path(os.path.normpath(ROOT/path.parent/target))
        try:relative=absolute.relative_to(ROOT)
        except ValueError:
            # Absolute local evidence paths in historical journals are not repository links.
            if not target.startswith('/'):raise ValueError(f'Link escapes repository: {path}: {target}')
            continue
        targets.append(relative)
    return targets


def label(path):
    match=re.search(r'^#\s+(.+)$',(ROOT/path).read_text(),re.M)
    return match[1].strip() if match else path.name


def relative(source,target):
    return Path(os.path.relpath(target,source.parent)).as_posix()


def update(paths,parents):
    children=defaultdict(list)
    for child,owner in parents.items():
        if owner is not None:children[owner].append(child)
    for path in paths:
        if not owned(path):continue
        text=(ROOT/path).read_text()
        text=NAV.sub('\n',CHILDREN.sub('\n',text)).rstrip()+'\n'
        owner=parents[path]
        if owner:
            crumbs=f'[Project README]({relative(path,Path("README.md"))})'
            if owner!=Path('README.md'):
                crumbs+=f' · [Parent: {label(owner)}]({relative(path,owner)})'
            block=f'\n<!-- docs-tree:parent -->\n{crumbs}\n<!-- /docs-tree:parent -->\n'
            title=re.search(r'^# .+\n',text,re.M)
            position=title.end() if title else 0
            text=text[:position]+block+'\n'+text[position:].lstrip('\n')
        outgoing=set(links(path,text))
        missing=[child for child in sorted(children[path]) if child not in outgoing]
        if missing:
            text+='\n<!-- docs-tree:children -->\n## Related documents\n\n'
            for child in missing:
                text+=f'- [{label(child)}]({relative(path,child)})\n'
            text+='<!-- /docs-tree:children -->\n'
        if text!=(ROOT/path).read_text():(ROOT/path).write_text(text)


def check(paths,parents):
    errors=[]
    outgoing={}
    for path in paths:
        if not owned(path):continue
        outgoing[path]=set(links(path,(ROOT/path).read_text()))
        for target in outgoing[path]:
            if not (ROOT/target).exists():errors.append(f'{path}: missing target {target}')
    for path,owner in parents.items():
        if owner is None:continue
        if owner not in outgoing:errors.append(f'{path}: missing parent {owner}')
        elif path not in outgoing[owner]:errors.append(f'{owner}: missing child link to {path}')
        if owned(path) and owner not in outgoing.get(path,set()):errors.append(f'{path}: missing parent backlink to {owner}')
        seen={path}
        while owner is not None:
            if owner in seen:
                errors.append(f'{path}: cycle through {owner}');break
            seen.add(owner)
            if owner not in parents:
                errors.append(f'{path}: parent is not indexed: {owner}');break
            owner=parents[owner]
        if Path('README.md') not in seen:errors.append(f'{path}: does not reach README.md')
    return errors


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--update',action='store_true',help='Refresh project breadcrumbs and missing child links')
    args=parser.parse_args()
    paths=documents()
    try:
        parents={p:parent(p) for p in paths}
        if args.update:update(paths,parents)
        errors=check(paths,parents)
    except ValueError as error:errors=[str(error)]
    if errors:
        print('\n'.join(errors),file=sys.stderr);return 1
    print(f'PASS: {len(paths)} Markdown documents connect to README.md; parent links and project local targets resolve')
    return 0


if __name__=='__main__':raise SystemExit(main())
