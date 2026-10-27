"""Read-only scene-floor interpretation and bounded test-route planning.

The packed grid/shape/height rules follow original 0x448744..0x448bdd.
This never calls the floor helper: its scripted branch can mutate an actor.
Plans are guidance; only observed SDL movement establishes reachability.
"""
from functools import lru_cache
import hashlib
import heapq
import math
import struct


def navigation_scripts(data):
    """Audit installed global bytecode; allow audio and scene loading only.

    Version 55 global FAN: eleven packed name pools, three empty ten-byte
    records, then the counted action-code table consumed by 0x444c10.
    Unknown opcodes, embedded strings and malformed arguments grant no access.
    """
    if data[:8]!=b'FANT\x007\x00\x00':raise ValueError('Unsupported global FAN script policy')
    cursor=34
    for _ in range(11):
        while data[cursor]:cursor=data.index(0,cursor)+1
        cursor+=1
    for _ in range(3):
        if data[cursor:cursor+2]!=b'\0\0':raise ValueError('Unexpected global FAN prefix record')
        cursor+=10
    def word():
        nonlocal cursor
        value=struct.unpack_from('>H',data,cursor)[0];cursor+=2
        return value
    count=word()
    if not 0<count<=4096:raise ValueError('Unbounded global script count')
    allowed={}
    for _ in range(count):
        identity=word();tokens=[]
        while True:
            token=word()
            if token==0:break
            tokens.append(token)
            if len(tokens)>4096:raise ValueError('Unbounded global bytecode')
            if token&0xf000==0xe000:
                for _ in range(((token&4095)+1)//2):tokens.append(word())
        children=word()
        if children>4096:raise ValueError('Unbounded global script strings')
        for _ in range(children):cursor=data.index(0,cursor)+1
        position=0;effects=[]
        while position<len(tokens):
            opcode=tokens[position];position+=1
            classes={7:(0x4000,),0x25:(0xf000,),0x70:(),0x6f:(0xa000,0xf000,0xf000,0xf000)}.get(opcode)
            if classes is None or position+len(classes)>len(tokens):break
            if any(tokens[position+i]&0xf000!=kind for i,kind in enumerate(classes)):break
            position+=len(classes);effects.append(opcode)
        else:
            allowed[identity+1]=dict(tokens=tokens,effects=sorted(set(effects)))
    return dict(source='installed version-55 global FAN bytecode; audio/scene-load opcodes only',
                sha256=hashlib.sha256(data).hexdigest(),allowed=allowed)


class SceneMap:
    def __init__(self, grid, descriptors, flags, shift, policy=None):
        if len(grid)!=32768 or not descriptors or len(descriptors)%12 or len(flags)!=256 or not 0<=shift<=7:
            raise ValueError('Invalid bounded scene map')
        self.grid=struct.unpack('<16384H',grid)
        self.descriptors=tuple(descriptors[i:i+12] for i in range(0,len(descriptors),12))
        self.flags,self.shift=flags,shift
        self.policy=policy or dict(allowed={})
        self.identity=hashlib.sha256(grid+descriptors+flags+bytes([shift])).hexdigest()

    @staticmethod
    def shape(shape,x,z):
        x,z=(x&511)-256,(z&511)-256
        if shape<6:return (False,True,z<=x,x<=-z,-z<x,x<z)[shape]
        return bool(shape & (2 if z<1 else 8) if x<1 else shape & (1 if z<1 else 4))

    @lru_cache(maxsize=200000)
    def floor(self,x,y,z):
        if not -32768<=x<=32767 or not -32768<=z<=32767:return None
        cell=self.grid[((z>>9)+64)*128+(x>>9)+64]
        if cell==65535:return None
        selected=None;priority=-1
        for index in range(cell,min(cell+256,len(self.descriptors))):
            row=self.descriptors[index]
            if self.shape(row[1],x,z) and row[5]<=(-y>>self.shift)+132 and row[0]>priority:
                selected=index;priority=row[0]
            if row[3]&128:break
        else:raise ValueError('Unterminated scene descriptor chain')
        if selected is None:return None
        row=self.descriptors[selected];surface=row[6]
        # Signed terrain indexes and scripted tiles require further semantics.
        if surface>=128 or self.flags[surface*2]&4:return None
        return dict(position=[x,(128-row[7])<<self.shift,z],surface=surface,
                    script=int.from_bytes(row[2:4],'little')&16383,
                    camera=int.from_bytes(row[8:10],'little'),descriptor=selected)

    @lru_cache(maxsize=100000)
    def safe(self,x,y,z,water,direction=None):
        row=self.step_floor(x,y,z)
        if row is None or not self.script_allowed(row) or row['surface']==7 and not water:return None
        height=row['position'][1]
        if not -256<=height-y<=256 and not (water and row['surface']==7 and 0<=height-y<=1024):return None
        # Conservative footprint sampling prevents shortcuts along a missing
        # floor or cliff. Actor collisions are still observed by the navigator.
        if direction is not None:
            # Original 0x448cb4: five forward floor probes, including the
            # forward-drop exception. A full circle would disconnect stairs.
            dx,dz=direction;heading=math.atan2(dx,dz);drop=False
            for index,offset in enumerate((0,math.pi/8,-math.pi/8,3*math.pi/8,-3*math.pi/8)):
                px=x-dx+round(math.sin(heading+offset)*256)
                pz=z-dz+round(math.cos(heading+offset)*256)
                side=self.step_floor(px,y,pz)
                if side is None or not self.script_allowed(side):return None
                delta=y-side['position'][1]
                if index==0:drop=delta < -256
                if delta>256 or index>=3 and delta < -256 and not drop:return None
            return row
        for dx,dz in ((-256,0),(256,0),(0,-256),(0,256)):
            side=self.step_floor(x+dx,height,z+dz)
            if side is None or not self.script_allowed(side):return None
            delta=side['position'][1]-height
            shoreline=water and (side['surface']==7 and 0<=delta<=1024 or row['surface']==7 and -1024<=delta<=0)
            if abs(delta)>256 and not shoreline:return None
        return row

    def step_floor(self,x,y,z):
        row=self.floor(x,y,z)
        # A nearby upper layer can become selected during an ordinary step.
        # Do not plan a water drop underneath such a reachable bank/overhang.
        for rise in (128,256):
            upper=self.floor(x,y-rise,z)
            if upper and -256<=upper['position'][1]-y<=0 and (row is None or upper['position'][1]<row['position'][1]):row=upper
        return row

    def script_allowed(self,row):
        return row['script']==0 or row['script'] in self.policy['allowed']

    def region_goal(self,start,camera,surface,height,minimum_distance=0,entry=False):
        candidates=[]
        for z in range(-32512,32768,512):
            for x in range(-32512,32768,512):
                row=self.floor(x,height,z)
                above=self.step_floor(x,height-1024,z) if entry else row
                separation=math.hypot(x-start[0],z-start[2])
                clear_entry=not entry or all((side:=self.step_floor(x+dx,height-1024,z+dz)) and side['surface']==surface
                    for dx,dz in ((0,0),(-256,0),(256,0),(0,-256),(0,256)))
                clear_camera=all((side:=self.floor(x+dx,height,z+dz)) and side['camera']==camera
                    for dx,dz in ((-512,0),(512,0),(0,-512),(0,512),(-362,-362),(-362,362),(362,-362),(362,362)))
                if row and above and above['surface']==surface and clear_entry and clear_camera and row['camera']==camera and row['surface']==surface and separation>=minimum_distance and self.safe(x,height,z,surface==7):
                    candidates.append((separation,x,z,row['position']))
        if not candidates:raise ValueError('Requested scene region has no conservative floor destination')
        return min(candidates)[-1]

    def plan(self,start,goal,water=False,max_nodes=40000,only_water=False,obstacles=()):
        """A* on a 128-unit lattice; fixed destination supplied by the scenario."""
        snap=lambda value:round((value-64)/128)*128+64
        first=self.floor(snap(start[0]),start[1],snap(start[2]))
        if first is None:raise ValueError('No observed start floor for scene navigation')
        initial=tuple(first['position']);destination=tuple(goal)
        def clear(a,b):
            dx,dz=b[0]-a[0],b[2]-a[2]
            length=dx*dx+dz*dz
            for obstacle in obstacles:
                x,y,z=obstacle['position'];radius=obstacle['clearance']
                if abs(a[1]-y)>=radius and abs(b[1]-y)>=radius:continue
                before=math.hypot(a[0]-x,a[2]-z);after=math.hypot(b[0]-x,b[2]-z)
                # An already crowded start may move out of the clearance disc.
                if before<radius and after>before:continue
                fraction=max(0,min(1,((x-a[0])*dx+(z-a[2])*dz)/length)) if length else 0
                if math.hypot(a[0]+fraction*dx-x,a[2]+fraction*dz-z)<radius:return False
            return True
        heuristic=lambda node:math.hypot(node[0]-goal[0],node[2]-goal[2])
        frontier=[(heuristic(initial),0,initial)];cost={initial:0};parent={};expanded=0;end=None
        while frontier:
            _,travel,node=heapq.heappop(frontier)
            if travel!=cost[node]:continue
            expanded+=1
            if expanded>max_nodes:raise ValueError('Scene planning node budget exhausted')
            if heuristic(node)<160 and abs(node[1]-goal[1])<=256:
                end=node;break
            for dx,dz in ((-128,0),(128,0),(0,-128),(0,128),(-128,-128),(-128,128),(128,-128),(128,128)):
                row=self.safe(node[0]+dx,node[1],node[2]+dz,water,direction=(dx,dz))
                if row is None or only_water and row['surface']!=7:continue
                next_node=tuple(row['position'])
                if not clear(node,next_node):continue
                price=travel+math.hypot(dx,dz)+abs(next_node[1]-node[1])*.2
                if price<cost.get(next_node,float('inf')):
                    cost[next_node]=price;parent[next_node]=node
                    heapq.heappush(frontier,(price+heuristic(next_node),price,next_node))
        if end is None:raise ValueError('No connected scene-floor plan within declared movement policy')
        raw=[end]
        while raw[-1]!=initial:raw.append(parent[raw[-1]])
        raw.reverse()
        # Keep turns, stairs and at most 512-unit straight segments. No recorded
        # session coordinates or input schedule participates in this plan.
        points=[list(raw[0])];last_direction=None
        for index,node in enumerate(raw[1:],1):
            before=raw[index-1];direction=(node[0]-before[0],node[1]-before[1],node[2]-before[2])
            if last_direction is not None and direction!=last_direction and points[-1]!=list(before):points.append(list(before))
            if math.hypot(node[0]-points[-1][0],node[2]-points[-1][2])>=512 or direction[1]:points.append(list(node))
            last_direction=direction
        if points[-1]!=list(end):points.append(list(end))
        last=self.safe(goal[0],end[1],goal[2],water)
        if last and last['position']==list(goal) and points[-1]!=list(goal) and clear(end,goal):points.append(list(goal))
        if only_water:
            # Swim toward the farthest clear point, rather than orbiting short
            # lattice bends. Every 64-unit sample must retain the water floor.
            def clear_water(a,b):
                if not clear(a,b):return False
                steps=max(1,math.ceil(math.hypot(a[0]-b[0],a[2]-b[2])/64))
                for step in range(steps+1):
                    x=round(a[0]+(b[0]-a[0])*step/steps);z=round(a[2]+(b[2]-a[2])*step/steps)
                    row=self.safe(x,a[1],z,True)
                    if row is None or row['surface']!=7 or row['position'][1]!=a[1]:return False
                return True
            smooth=[points[0]];index=0
            while index<len(points)-1:
                next_index=next((candidate for candidate in range(len(points)-1,index,-1)
                                 if clear_water(points[index],points[candidate])),index+1)
                smooth.append(points[next_index]);index=next_index
            points=smooth
        heights={index:[points[index-1][1],point[1]] for index,point in enumerate(points)
                 if index and water and point[1]-points[index-1][1]>256 and self.floor(*point)['surface']==7}
        if heights and not only_water:
            entry_height=min(bounds[0] for bounds in heights.values())
            heights.update({index:[entry_height,point[1]] for index,point in enumerate(points)
                            if point[1]>entry_height and self.floor(*point)['surface']==7})
        return dict(source='live scene grid; original 0x448744/0x448a48 layout',map_sha256=self.identity,
                    script_policy_sha256=self.policy.get('sha256'),
                    start=start,goal=list(destination),water=water,expanded=expanded,max_nodes=max_nodes,
                    lattice=128,footprint=256,forward_probes=5,path=points,raw_nodes=len(raw),height_ranges=heights,only_water=only_water,
                    observed_actor_clearance=list(obstacles))
