"""Bounded real-SDL Enter/Escape checks at stopped native update boundaries."""
import hashlib
import json
from pathlib import Path

import gdb


def observe(journey):
    """Memory-only observation, also safe inside serializer breakpoint callbacks."""
    bits = bytes(gdb.selected_inferior().read_memory(0xac4b00, 150))
    pool = journey.value('_DAT_006366bc')
    names = bytes(gdb.selected_inferior().read_memory(pool, 20000)).split(b'\0')
    items = []
    for name in ('ringicon', 'amuicon1', 'lampicon', 'shdicon1', 'shdicon2',
                 'scrlicon', 'amuicon2', 'kingicon', 'elder1', 'elder2', 'elder3',
                 'elder4', 'elder5', 'elder6', 'elder7'):
        index = next((i for i, value in enumerate(names) if value.lower() == name.encode()), -1)
        items.append(int(index >= 0 and bool(journey.value(f'*(unsigned char*){0x670c38 + index * 2}') & 8)))
    return dict(items=items, timer=journey.value('DAT_0047ab20'), timer_total=journey.value('DAT_0047ab24'),
                power=journey.value('*(int*)0x47ab28'), kills=journey.value('*(int*)0x47ab18'),
                gold=journey.value('*(int*)0x47ab14') * 10,
                progress=min(99, sum(x.bit_count() for x in bits) * 100 // 1001))


def snapshot(journey):
    gdb.execute('set $inventory_state=(E2R_InventoryState*)calloc(1,sizeof(E2R_InventoryState))', to_string=True)
    gdb.execute('call E2R_GetInventoryState($inventory_state)', to_string=True)
    state = gdb.parse_and_eval('*$inventory_state')
    row = {name: int(state[name]) for name in ('timer', 'timer_total', 'power', 'kills', 'gold', 'progress')}
    row['items'] = [int(state['items'][i]) for i in range(15)]
    gdb.execute('call (void)free($inventory_state)', to_string=True)
    journey.require(row == observe(journey), 'Status state differs from original live memory/formula')
    return row


def check(journey, label, switches=True):
    from e2_hud_steps import HudChecks
    checks = HudChecks(journey)
    rows = journey.details.setdefault('inventory', [])
    mode = journey.value('E2R_DebugOverlaySelected()')
    geometry = journey.value('E2R_GeometryMode()')
    before = snapshot(journey)
    journey.frame.enabled = False
    journey.menu = gdb.Breakpoint('FUN_0041ba7c', internal=True)
    journey.key(13, True)
    journey.pump(1)
    journey.require(journey.value('E2R_InventoryPageActive()') == 1, 'Real Enter did not open the original status page')
    journey.key(13, False)
    journey.pump(3)
    journey.require(journey.value('*(unsigned char*)0x4c39ac') == 0, 'Enter queue was not consumed')
    opened = snapshot(journey)
    journey.require(opened == before, 'Opening the page changed inventory statistics')
    # Additional Enter downs while modal must not toggle/close or survive dismissal.
    for _ in range(2):
        journey.key(13, True)
        journey.pump(1)
    journey.key(13, False)
    journey.pump(1)
    journey.require(journey.value('E2R_InventoryPageActive()') == 1, 'Repeated Enter changed the modal lifecycle')
    # Actor simulation must not advance while the original synchronous input pump runs.
    actor = journey.value('*(unsigned int*)0x630b60')
    simulation = bytes(gdb.selected_inferior().read_memory(actor, 0x18c))
    pages = checks.page_bytes()
    first = checks.capture('inventory-' + label, False)
    journey.require(journey.value('e2r_hud_pixels != 0'), 'No indexed status page was composed')
    size = journey.value('_DAT_006401ec * _DAT_006401d4')
    indexed = bytes(gdb.selected_inferior().read_memory(journey.value('e2r_hud_pixels'), size))
    Path(journey.prefix + '-inventory-' + label + '.pgm').write_bytes(b'P5\n640 480\n255\n' + indexed)
    if switches:
        for selection in (1, 0, mode):
            checks.select(selection, label)
            journey.require(checks.capture('inventory-' + label + '-hud-' + str(selection), False) == first,
                            'F1/F2 obscured or changed the original status page')
        for selection in ((geometry + 1) % 3, (geometry + 2) % 3, geometry):
            checks.select(selection, label, geometry=True)
            journey.require(checks.capture('inventory-' + label + '-geometry-' + str(selection), False) == first,
                            'F3 obscured the original status page')
    journey.pump(12)
    journey.require(bytes(gdb.selected_inferior().read_memory(actor, 0x18c)) == simulation,
                    'Actor simulation advanced inside the status page')
    journey.require(checks.page_bytes() == pages, 'Status presentation changed gameplay buffers')
    journey.require(snapshot(journey) == opened, 'Status values changed while paused')
    journey.key(27, True)
    journey.key(27, False)
    journey.menu.delete()
    journey.menu = None
    journey.frame.enabled = True
    journey.step(3)
    journey.require(not journey.value('E2R_InventoryPageActive()'), 'Escape did not dismiss the status page')
    journey.require(journey.value('_DAT_00643650') == 0 and
                    journey.value('*(unsigned short*)((char*)&DAT_0047a45e+2)') == 0,
                    'Closing status accidentally opened a requester')
    journey.require(journey.value('DAT_00636844') == 0 and
                    journey.value('*(unsigned char*)0x4c39ac') == 0, 'Status dismissal left stale input')
    checks.check_mode(mode)
    rows.append(dict(label=label, state=opened, indexed_sha256=hashlib.sha256(indexed).hexdigest(),
                     presented_sha256=hashlib.sha256(first).hexdigest(), paused=True,
                     gameplay_pages_unchanged=True, display_switches=switches, dismissed=True))
    journey.save()
    return opened
