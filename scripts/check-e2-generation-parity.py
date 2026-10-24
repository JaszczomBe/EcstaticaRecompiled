#!/usr/bin/env python3
"""Regenerate in scratch and compare all four artifacts without overwriting C."""
import argparse
import difflib
import json
from pathlib import Path
import subprocess
import tempfile

ROOT=Path(__file__).resolve().parent.parent


def check(output):
    output.mkdir(parents=True,exist_ok=False)
    with tempfile.TemporaryDirectory(prefix='e2-suite-generation-') as temporary:
        tree=Path(temporary)/'E2Recomp'
        tree.mkdir()
        for name in ('src','metadata'):
            (tree/name).symlink_to(ROOT/'E2Recomp'/name,target_is_directory=True)
        subprocess.run(['node','--check',str(ROOT/'E2Recomp/tools/GenerateRecon.js')],check=True,timeout=30)
        subprocess.run(['node',str(ROOT/'E2Recomp/tools/GenerateRecon.js'),temporary],check=True,timeout=60)
        mismatches=[]
        for name in ('E2Recomp_recon.c','E2Recomp_recon.h','E2Recomp_globals.c','E2Recomp_names.tsv'):
            actual=(ROOT/'E2Recomp/reconstructed'/name).read_bytes()
            generated=(tree/'reconstructed'/name).read_bytes()
            if actual!=generated:
                mismatches.append(name)
                patch=''.join(difflib.unified_diff(actual.decode().splitlines(True),generated.decode().splitlines(True),
                    fromfile='current/'+name,tofile='generated/'+name))
                (output/(name+'.patch')).write_text(patch)
        (output/'result.json').write_text(json.dumps(dict(passed=not mismatches,mismatches=mismatches),indent=2)+'\n')
        if mismatches:
            print('FAIL: generator drift in '+', '.join(mismatches)+'; preserved current files; diffs in '+str(output))
            return 1
        print('PASS: all four scratch-generated artifacts match')
        return 0


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path)
    args=parser.parse_args()
    if args.output:
        raise SystemExit(check(args.output.resolve()))
    with tempfile.TemporaryDirectory(prefix='e2-generation-evidence-') as temporary:
        raise SystemExit(check(Path(temporary)/'result'))
