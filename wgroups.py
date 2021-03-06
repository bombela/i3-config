#!/usr/bin/env python
import i3
import os
import sys
from pprint import pprint

I3_CFG_DIR = '~/.i3'
I3_CFG_DIR = os.path.expanduser(I3_CFG_DIR)
WGROUP_FIFO = os.path.join(I3_CFG_DIR, 'wgroups.fifo')

SELF_MOD = sys.modules[__name__]

LRU_WNUM_PER_GROUPS = {}

def daemon():
    if not os.path.exists(WGROUP_FIFO):
        print 'mkdiro:', WGROUP_FIFO
        os.mkfifo(WGROUP_FIFO)

    print 'fifo:', WGROUP_FIFO
    while True:
        for cmd in open(WGROUP_FIFO):
            args = filter(None, map(str.strip, cmd.split()))
            if len(args) < 1:
                continue
            cmd, args = args[0], args[1:]
            try:
                run_cmd(cmd, *args)
            except BaseException as e:
                print 'error:', e

def run_cmd(cmd, *args):
    print 'run cmd', cmd, args
    f = getattr(SELF_MOD, 'cmd_' + cmd)
    return f(*args)

class WDest(object):
    num = 1
    down = 2
    up = 3

def parse_wmove(w):
    try:
        n = int(w)
        return (WDest.num, n)
    except ValueError:
        pass
    try:
        return (getattr(WDest, w), None)
    except Exception:
        raise Exception('Invalid workspace move {0}'.format(w))

def get_wgroup(ws):
    focused = filter(lambda x: x.get('focused'), ws)
    if len(focused) != 1:
        raise Exception('Unable to get current workspace {0}'.format(
            focused))
    focused = focused[0]
    wid = focused.get('num')
    group = wid / 10
    wnum = wid % 10
    print 'wgroup', wid, '->', group, wnum
    return group, wnum

def wroundid(group, wnum):
    wid = (max(group, 0) * 10) + (wnum % 10)
    print 'wid', group, wnum, '->', wid
    return wid

def wclosest(ws, group_, wnum_):
    group = max(group_, 0)
    ws = filter(lambda x: (x.get('num') / 10 == group), ws)
    if len(ws) == 0:
        wid = wroundid(group, wnum_)
        print 'wclosest', group_, wnum_, '->', wid
        return group, wid
    wnum = LRU_WNUM_PER_GROUPS.get(group, wnum_)
    ws.sort(key=lambda x: abs((x.get('num') % 10) - wnum))
    wid = ws[0].get('num')
    print 'wclosest', group_, wnum_, '->', wid
    return group, wid

def dest_wid(w):
    wmove, wnum_dest = parse_wmove(w)
    ws = i3.get_workspaces()
    group, wnum = get_wgroup(ws)
    if wmove == WDest.num:
        wid = wroundid(group, wnum_dest)
    elif wmove == WDest.up:
        LRU_WNUM_PER_GROUPS[group] = wnum
        group, wid = wclosest(ws, group + 1, wnum)
    elif wmove == WDest.down:
        LRU_WNUM_PER_GROUPS[group] = wnum
        group, wid = wclosest(ws, group - 1, wnum)
    else:
        raise NotImplementedError()
    LRU_WNUM_PER_GROUPS[group] = wid % 10
    return wid

def cmd_focus(wmove):
    wid = dest_wid(wmove)
    print 'focus', wmove, '->', wid
    i3.workspace(str(wid))

def cmd_move(wmove):
    wid = dest_wid(wmove)
    print 'move', wmove, '->', wid
    i3.move('workspace', str(wid))

def cmd_move_and_focus(wmove):
    wid = dest_wid(wmove)
    print 'move & focus', wmove, '->', wid
    wid = str(wid)
    i3.move('workspace', wid)
    i3.workspace(wid)

def wids_by_furthest(ws, group, wnum):
    ws = [w for w in ws if w.get('num') / 10 == group]
    ws.sort(key=lambda x: abs((x.get('num') % 10) - wnum), reverse=True)
    wids = [w.get('num') for w in ws]
    assert len(wids) > 0
    return wids

def cmd_move_group_output(output):
    ws = i3.get_workspaces()
    group, current_wnum = get_wgroup(ws)
    wids = wids_by_furthest(ws, group, current_wnum)
    print 'move_group_output', output, '->', wids
    i3_move_args = ['workspace', 'to', output]
    for wid in wids:
        i3.workspace(str(wid))
        i3.move(*i3_move_args)

def find_closest_empty_group(ws, starting_group, up):
    groups = set(w.get('num') / 10 for w in ws)
    groups = sorted((g for g in groups
            if (g > starting_group if up else g < starting_group)),
            reverse=not up)
    prev_group = starting_group
    empty_group = None
    for g in groups:
        maybe_empty_group = g + (-1 if up else 1)
        if maybe_empty_group != prev_group:
            empty_group = maybe_empty_group
            break
        prev_group = g
    if empty_group is None:
        print 'prev_group', prev_group
        empty_group = prev_group + (1 if up else -1)
    print 'closest_empty_group', starting_group, groups, '->', empty_group
    return empty_group

def cmd_move_group(direction):
    ws = i3.get_workspaces()
    group, current_wnum = get_wgroup(ws)
    if direction == 'up':
        empty_group = find_closest_empty_group(ws, group, True)
        pass
    elif direction == 'down':
        empty_group = find_closest_empty_group(ws, group, False)
        pass
    else:
        raise Exception('Invalid direction: {0}'.format(direction))
    if empty_group < 0:
        return
    current_wids = wids_by_furthest(ws, group, current_wnum)
    wids = [wroundid(empty_group, wid % 10) for wid in current_wids]
    print 'move_group', direction, current_wids, '->', wids
    collisions = set(wids).intersection(set(w.get('num') for w in ws))
    if collisions:
        raise Exception('Can\'t move, there would be collisions: {0}'.format(
            sorted(collisions)))
    for cur_wid, new_wid in zip(current_wids, wids):
        i3.rename('workspace', str(cur_wid), 'to', str(new_wid))

if len(sys.argv) < 2:
    print 'daemon mode'
    daemon()
else:
    print 'direct cmd'
    cmd, args = sys.argv[1], sys.argv[2:]
    run_cmd(cmd, *args)
