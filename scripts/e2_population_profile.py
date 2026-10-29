"""Audited opening-route population fixture and read-only GDB evidence."""
import json
import os
from pathlib import Path
import struct

NONCOMBAT_ACTORS = (284, 293, 602)  # Original gob3, gob3b, korc2; not marker labels.
NONCOMBAT_SCENARIOS = {'movement', 'courtyard', 'workshop', 'sword', 'attacks',
                       'unarmed', 'swimming', 'water-traversal','water-combat','armed-swimming',
                       'armed-water-traversal','armed-water-combat','menus', 'menu-matrix'}
LIVE_CHECKS = {'Combat.UnarmedContact', 'Combat.KillSmith', 'Combat.TakeDamage',
               'Interaction.DoorPassage', 'Interaction.DoorPassageDisplaced', 'Stability.MixedJourney'}


def profile_for(scenario, checks=()):
    if scenario == 'ladder':
        return 'noncombat-ladder'
    if scenario == 'shared':
        # Startup-only journeys retain the original populated opening. Sharing
        # a startup assertion with controlled movement proves only that assertion.
        if any(check in LIVE_CHECKS or check.startswith('Potion.') or
               check == 'Interaction.PotionThenSword' for check in checks):
            return 'live'
        return 'noncombat-opening' if any(not check.startswith('Startup.') for check in checks) else 'live'
    return 'noncombat-opening' if scenario in NONCOMBAT_SCENARIOS else 'live'


def observe(prefix, label):
    import gdb
    profile = os.environ.get('E2R_TEST_POPULATION', 'live')
    inferior = gdb.selected_inferior()
    slots = struct.unpack('<5000I', inferior.read_memory(0x630b60, 20000))
    flags = bytes(inferior.read_memory(0x64a178, 10000))
    loaded = [identity for identity, pointer in enumerate(slots) if pointer]
    generated = [identity for identity in loaded if flags[identity * 2] & 8]
    controlled = profile in ('noncombat-opening', 'noncombat-ladder')
    row = dict(label=label, profile=profile, suppressed_actors=list(NONCOMBAT_ACTORS) if controlled else [],
               loaded_actors=loaded, generated_actors=generated,
               blocked_requests_mask=int(gdb.parse_and_eval("E2R_test_suppressed_mask")) if profile != 'live' else 0)
    path = Path(prefix + '-population-profile.json')
    rows = json.loads(path.read_text()) if path.exists() else []
    rows.append(row)
    temporary = path.with_suffix('.json.tmp')
    temporary.write_text(json.dumps(rows, indent=2) + '\n')
    temporary.replace(path)
    if controlled:
        unexpected = set(loaded).intersection(NONCOMBAT_ACTORS)
        if unexpected or generated:
            raise gdb.GdbError(f'Noncombat fixture leaked actors: scripted={sorted(unexpected)}, terrain={generated}')
        if not slots[0]:
            raise gdb.GdbError('Noncombat fixture lost original Joe')
    return row
