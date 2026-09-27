"""Tiny Train Village: 30 editable procedural Blender assets.

Run in Blender's Scripting workspace, or:
    blender --background --python build_catalog.py
Builds a new scene. Save your current work before running.
All dimensions are meters; +Z is up and rail vehicles face -X.
"""
import bpy, bmesh, math, random, json, os, sys
from pathlib import Path
from mathutils import Vector
from math import sin, cos, pi

OUT = Path(os.environ.get('TINY_TRAIN_OUTPUT', str(Path(__file__).resolve().parent)))
OUT.mkdir(parents=True, exist_ok=True)
(OUT/'models').mkdir(exist_ok=True)
(OUT/'previews').mkdir(exist_ok=True)
random.seed(2481)
bpy.ops.wm.read_factory_settings(use_empty=True)
SCENE = bpy.context.scene
SCENE.unit_settings.system = 'METRIC'
SCENE.unit_settings.scale_length = 1.0
MAT = {}
ASSETS = []
CURRENT = None
ROOT = None

def mat(name, color, metal=0, rough=.6, emission=0):
    c = tuple(int(color[i:i+2],16)/255 for i in (0,2,4))
    c = tuple(v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4 for v in c)
    m=bpy.data.materials.new(name); m.use_nodes=True
    p=m.node_tree.nodes.get('Principled BSDF')
    p.inputs['Base Color'].default_value=(*c,1)
    p.inputs['Roughness'].default_value=rough
    p.inputs['Metallic'].default_value=metal
    if emission:
        p.inputs['Emission Color'].default_value=(*c,1)
        p.inputs['Emission Strength'].default_value=emission
    m.diffuse_color=(*c,1); MAT[name]=m
    return m

for args in [
 ('Wood','A9733B'),('WoodLight','C49457'),('WoodDark','6B472B'),
 ('WoodEnd','BB8748'),('Bark','725339'),('Olive','5D6947'),
 ('Red','A23B2D'),('RoofRed','B86642'),('RoofLight','CF8052'),
 ('Iron','353A39',.65,.38),('Steel','869693',.65,.34),
 ('Brass','B69044',.72,.3),('Cream','E5D6B7'),('Plaster','D3C4A5'),
 ('Stone','B4AA8D'),('StoneLight','CEC3A5'),('StoneDark','8F8973'),
 ('Leaf','557C32'),('LeafLight','7D9D40'),('LeafDark','3A6032'),
 ('Grass','849855'),('Soil','4F3F2C'),('Terracotta','B96C43'),
 ('White','F1E8CE'),('Yellow','E8B942'),('Orange','D87C2A'),
 ('Tomato','C34632'),('FlowerPink','BA748A'),('Water','508E94',.12,.22),
 ('Foam','CADDD2',0,.35),('Window','466261',.15,.2),
 ('Amber','FFD78B',0,.3,1.4),('Fire','F8A328',0,.4,1.7),
 ('Black','262C2C'),('Backdrop','E8E1D3')
]: mat(*args)

def new_asset(num, title, category):
    global CURRENT, ROOT
    slug=f'{num:02d}_'+title.lower().replace(' ','_').replace('&','and')
    CURRENT=bpy.data.collections.new(slug)
    SCENE.collection.children.link(CURRENT)
    ROOT=bpy.data.objects.new(slug+'_ROOT',None); CURRENT.objects.link(ROOT)
    ROOT.empty_display_type='PLAIN_AXES'; ROOT.empty_display_size=.25
    ROOT['catalog_number']=num; ROOT['title']=title; ROOT['category']=category
    ROOT['reference']='Tiny Train Village selected object catalog'
    ROOT['style']='Stylized procedural interpretation; unrigged'
    CURRENT.asset_mark(); CURRENT.asset_data.description=f'{num:02d}. {title} | Tiny Train Village'
    a={'number':num,'name':title,'slug':slug,'category':category,'collection':CURRENT,'root':ROOT}
    ASSETS.append(a)
    return a

def mesh(name, verts, faces, material, smooth=False, bevel=0):
    d=bpy.data.meshes.new(name+'_mesh'); d.from_pydata(verts,[],faces); d.update()
    o=bpy.data.objects.new(name,d); CURRENT.objects.link(o); o.parent=ROOT
    d.materials.append(MAT[material] if isinstance(material,str) else material)
    for p in d.polygons: p.use_smooth=smooth
    if bevel:
        b=o.modifiers.new('Soft crafted edges','BEVEL'); b.width=bevel; b.segments=2
        b.limit_method='ANGLE'
        n=o.modifiers.new('Weighted corner normals','WEIGHTED_NORMAL'); n.keep_sharp=True
    return o

def box(name,p,s,m='Wood',bevel=.025,rot=None):
    x,y,z=[v/2 for v in s]
    v=[(-x,-y,-z),(-x,-y,z),(-x,y,-z),(-x,y,z),(x,-y,-z),(x,-y,z),(x,y,-z),(x,y,z)]
    f=[(0,4,6,2),(1,3,7,5),(0,1,5,4),(2,6,7,3),(0,2,3,1),(4,5,7,6)]
    o=mesh(name,v,f,m,bevel=min(bevel,min(s)*.25)); o.location=p
    if rot:o.rotation_euler=rot
    return o

def orient(o,axis):
    o.rotation_euler=Vector(axis).to_track_quat('Z','Y').to_euler()
    return o

def lathe(name,p,profile,m='Wood',n=24,axis=(0,0,1),smooth=True):
    v=[(r*cos(2*pi*i/n),r*sin(2*pi*i/n),z) for r,z in profile for i in range(n)]
    f=[]
    for j in range(len(profile)-1):
        for i in range(n):
            a=j*n+i;b=j*n+(i+1)%n
            f.append((a,b,b+n,a+n))
    f.extend([tuple(range(n-1,-1,-1)),tuple((len(profile)-1)*n+i for i in range(n))])
    o=mesh(name,v,f,m,smooth);o.location=p;orient(o,axis);return o

def cyl(name,p,r,h,m='Iron',axis=(0,0,1),n=24,r2=None):
    return lathe(name,p,[(r,-h/2),(r if r2 is None else r2,h/2)],m,n,axis)

def ring(name,p,outer,inner,h,m='Iron',axis=(0,0,1),n=24):
    return lathe(name,p,[(inner,-h/2),(outer,-h/2),(outer,h/2),(inner,h/2),(inner,-h/2)],m,n,axis)

def ball(name,p,s,m='Leaf',seg=12,rings=6,faceted=False):
    prof=[(max(.0001,sin(pi*j/rings)),-cos(pi*j/rings)) for j in range(rings+1)]
    o=lathe(name,p,prof,m,seg,smooth=not faceted);o.scale=s;return o

def rod(name,a,b,r=.025,m='Iron',n=12):
    a,b=Vector(a),Vector(b);return cyl(name,(a+b)/2,r,(b-a).length,m,b-a,n)

def beam(name,a,b,w=.08,d=None,m='Wood',bevel=.012):
    a,b=Vector(a),Vector(b);o=box(name,(a+b)/2,(w,d or w,(b-a).length),m,bevel)
    orient(o,b-a);return o

def tube(name,points,r,m='Iron',n=8):
    pts=[Vector(p) for p in points];v=[]
    for j,p in enumerate(pts):
        tangent=(pts[min(j+1,len(pts)-1)]-pts[max(j-1,0)]).normalized()
        ref=Vector((0,0,1)) if abs(tangent.z)<.95 else Vector((1,0,0))
        u=tangent.cross(ref).normalized();w=tangent.cross(u).normalized()
        v.extend([p+r*(u*cos(2*pi*k/n)+w*sin(2*pi*k/n)) for k in range(n)])
    f=[]
    for j in range(len(pts)-1):
        for i in range(n):
            a=j*n+i;b=j*n+(i+1)%n;f.append((a,b,b+n,a+n))
    f.extend([tuple(range(n-1,-1,-1)),tuple((len(pts)-1)*n+i for i in range(n))])
    return mesh(name,v,f,m,True)

def label(text,p,size=.18,m='Cream',rot=(pi/2,0,0)):
    d=bpy.data.curves.new('Label','FONT');d.body=text;d.align_x='CENTER';d.align_y='CENTER'
    d.size=size;d.extrude=.0015;d.resolution_u=3
    o=bpy.data.objects.new('Label_'+text,d);CURRENT.objects.link(o);o.parent=ROOT
    o.location=p;o.rotation_euler=rot;d.materials.append(MAT[m]);return o

def bolt(p,r=.024,axis=(0,-1,0),m='Brass'):
    return cyl('Fastener',p,r,.022,m,axis,n=8)

def leaf(p,angle,length=.24,width=.095,m='Leaf',rise=.1):
    v=[(0,0,0),(.32*length,-width,0),(.72*length,-width*.75,rise*.55),(length,0,rise),
       (.72*length,width*.75,rise*.55),(.32*length,width,0),(.5*length,0,rise*.65+.025)]
    f=[(0,1,6),(1,2,6),(2,3,6),(3,4,6),(4,5,6),(5,0,6)]
    o=mesh('Leaf',v,f,m);o.location=p;o.rotation_euler.z=angle
    s=o.modifiers.new('Leaf thickness','SOLIDIFY');s.thickness=.008
    return o

def sprout(p,scale=1,fruit=False):
    x,y,z=p
    rod('Stem',(x,y,z),(x,y,z+.32*scale),.014*scale,'LeafDark',8)
    for k in range(5):
        leaf((x,y,z+(.055+k*.043)*scale),k*2.4,.22*scale,.082*scale,
             ['Leaf','LeafLight','LeafDark'][k%3],.07*scale)
    if fruit:
        for k in range(3):
            a=k*2.1;ball('Tomato',(x+.12*scale*cos(a),y+.12*scale*sin(a),z+.14*scale),(.065*scale,)*3,'Tomato')

def flower(p,scale=1,petal='White'):
    x,y,z=p;h=.32*scale
    rod('Flower stem',p,(x,y,z+h),.012*scale,'LeafDark',8)
    leaf((x,y,z+h*.3),.6,.14*scale,.045*scale,'Leaf')
    for i in range(5):
        a=i*2*pi/5;ball('Petal',(x+.072*scale*cos(a),y+.072*scale*sin(a),z+h),(.059*scale,.045*scale,.025*scale),petal,10,4)
    ball('Flower center',(x,y,z+h+.012*scale),(.038*scale,.038*scale,.025*scale),'Yellow',10,4)

def planter(p=(0,0,0),s=(1.5,.65,.5),plants=True):
    x,y,z=p;w,d,h=s
    box('Planter bottom',(x,y,z+.06),(w-.06,d-.06,.12),'WoodDark')
    for side in (-1,1):
        for level in range(3):
            box('Planter plank',(x,y+side*(d/2-.035),z+(level+.5)*h/3),(w,.075,h/3-.012),'Wood' if level%2 else 'WoodLight')
        box('End plank',(x+side*(w/2-.035),y,z+h/2),(.075,d-.08,h),'Wood')
        for sy in (-1,1):
            box('Planter post',(x+side*(w/2-.08),y+sy*(d/2-.04),z+h/2),(.10,.11,h+.04),'WoodDark')
            bolt((x+side*(w/2-.08),y+sy*(d/2+.022),z+h*.75),.019,axis=(0,sy,0),m='Iron')
    box('Soil',(x,y,z+h-.07),(w-.18,d-.16,.08),'Soil',.015)
    if plants:
        for i in range(max(2,int(w/.35))):
            for j in (-1,1):sprout((x-w*.32+i*w*.64/max(1,int(w/.35)-1),y+j*d*.21,z+h-.035),.68)

def pot(p=(0,0,0),r=.25,h=.4,flowers=True):
    x,y,z=p
    lathe('Terracotta pot',(x,y,z),[(r*.67,0),(r,h*.85),(r*1.06,h*.86),(r*1.06,h),(r*.85,h),(r*.75,.09)],'Terracotta',20)
    cyl('Pot soil',(x,y,z+h-.06),r*.83,.03,'Soil',n=18)
    if flowers:
        for dx,dy,sz in [(-.08,0,.8),(.08,.03,1.1),(0,-.09,.9)]:
            sprout((x+dx,y+dy,z+h-.03),.7)
            flower((x+dx,y+dy,z+h+.07),sz)

def crate(p=(0,0,0),s=.65):
    x,y,z=p
    box('Crate core',(x,y,z+s/2),(s*.93,s*.93,s*.93),'WoodDark',.015)
    for side in (-1,1):
        for i in range(4):
            box('Crate face plank',(x,y+side*s*.48,z+s*(i+.5)/4),(s,.055*s,s*.24),'WoodLight' if i%2 else 'Wood',.01)
            box('Crate side plank',(x+side*s*.48,y,z+s*(i+.5)/4),(.055*s,s,s*.24),'Wood',.01)
        for a in (-1,1):
            box('Crate edging',(x+a*s*.41,y+side*s*.515,z+s*.5),(s*.13,s*.075,s),'WoodLight',.008)
        beam('Crate diagonal',(x-s*.32,y+side*s*.52,z+s*.13),(x+s*.32,y+side*s*.52,z+s*.88),s*.115,s*.06,'WoodLight',.009)
        for a in (-1,1):
            for b in (.12,.88):bolt((x+a*s*.4,y+side*s*.56,z+s*b),s*.026,(0,side,0),'Iron')
    for i in range(4):box('Crate lid',(x-s*.375+i*s*.25,y,z+s),(s*.24,s,.05*s),'WoodLight',.009)

def barrel(p=(0,0,0),r=.42,h=1.05):
    x,y,z=p;n=16;profile=[(r*.8,0),(r*.93,h*.18),(r,h*.5),(r*.93,h*.82),(r*.8,h)]
    for k in range(n):
        a=2*pi*k/n+.013;b=2*pi*(k+1)/n-.013
        v=[(x+rr*cos(t),y+rr*sin(t),z+zz) for rr,zz in profile for t in (a,b)]
        f=[(j*2,j*2+1,j*2+3,j*2+2) for j in range(len(profile)-1)]
        mesh('Barrel stave',v,f,['Wood','WoodLight','WoodEnd'][k%3],bevel=.007)
    for zz,rr in [(.10,.865),(.29,.97),(.71,.97),(.9,.865)]:ring('Barrel hoop',(x,y,z+h*zz),r*rr+.018,r*rr-.015,h*.063,'Iron',n=24)
    cyl('Barrel lid',(x,y,z+h-.022),r*.79,.04,'WoodEnd',n=24)
    for offset in (-.4,0,.4):
        xx=r*offset;length=2*math.sqrt((r*.76)**2-xx**2)
        box('Lid seam',(x+xx,y,z+h+.0005),(.012,length,.003),'WoodDark',0)

def table(p=(0,0,0),w=1.45,d=.8,h=.88):
    x,y,z=p
    for i in range(4):box('Table top plank',(x,y-d/2+(i+.5)*d/4,z+h),(w,d/4-.01,.10),'WoodLight' if i%2 else 'Wood')
    for a in (-1,1):
        box('Table apron',(x,y+a*(d/2-.06),z+h-.15),(w-.16,.09,.18),'Wood')
        for b in (-1,1):box('Table leg',(x+b*(w/2-.14),y+a*(d/2-.13),z+h/2-.05),(.13,.13,h-.1),'WoodDark')

def chair(p=(0,0,0),s=1):
    x,y,z=p;w=.55*s;h=.48*s
    for i in range(3):box('Seat plank',(x-w/2+(i+.5)*w/3,y,z+h),(w/3-.012,w,.075*s),'WoodLight',.015)
    for a in (-1,1):
        for b in (-1,1):
            hh=1.07*s if b==1 else h
            box('Chair post',(x+a*w*.38,y+b*w*.38,z+hh/2),(.07*s,.07*s,hh),'Wood',.014)
        box('Back board',(x,y+w*.38,z+.72*s+a*.14*s),(w,.07*s,.19*s),'WoodLight',.018)

def bowl(p=(0,0,0),r=.2,m='White'):
    return lathe('Bowl',p,[(r*.4,0),(r*.75,r*.15),(r,r*.7),(r*.97,r*.76),(r*.87,r*.73),(r*.60,r*.2),(r*.32,r*.1)],m,24)

def dishes(p=(0,0,0),s=1):
    x,y,z=p
    for i in range(3):lathe('Plate',(x-.26*s,y-.05*s,z+.018*s*i),[(0,0),(.13*s,0),(.22*s,.035*s),(.23*s,.055*s),(.20*s,.068*s),(.12*s,.025*s),(0,.025*s)],'White',24)
    bowl((x+.24*s,y,z),.22*s,'WoodEnd');bowl((x-.20*s,y+.50*s,z),.24*s,'White')

def stove(p=(0,0,0),s=1):
    x,y,z=p
    for a in (-1,1):
        for b in (-1,1):box('Stove foot',(x+a*.26*s,y+b*.20*s,z+.10*s),(.075*s,.075*s,.20*s),'Iron')
    box('Stove body',(x,y,z+.48*s),(.68*s,.55*s,.7*s),'Iron',.05*s)
    box('Stove top',(x,y,z+.86*s),(.77*s,.63*s,.09*s),'Iron')
    box('Firebox trim',(x,y-.292*s,z+.49*s),(.49*s,.065*s,.48*s),'Brass',.055*s)
    box('Firebox',(x,y-.333*s,z+.49*s),(.40*s,.025*s,.39*s),'Black',.06*s)
    for i in range(3):
        ball('Flame',(x+(i-1)*.09*s,y-.355*s,z+.42*s),(.075*s,.03*s,(.12+.03*(i%2))*s),'Fire',12,6)
    rod('Door handle',(x+.23*s,y-.36*s,z+.54*s),(x+.23*s,y-.36*s,z+.38*s),.024*s,'Brass')
    cyl('Flue',(x,y+.1*s,z+1.22*s),.115*s,.72*s,'Iron',n=20)
    ring('Flue collar',(x,y+.1*s,z+.92*s),.16*s,.105*s,.08*s,'Iron')
    ring('Flue lip',(x,y+.1*s,z+1.60*s),.14*s,.10*s,.045*s,'Iron')

def wheel(x,y,z=.34,r=.34):
    ring('Wheel tyre',(x,y,z),r,r*.78,r*.43,'Iron',(0,1,0),24)
    ring('Wheel rim',(x,y,z),r*.82,r*.73,r*.40,'Steel',(0,1,0),24)
    cyl('Wheel hub',(x,y,z),r*.25,r*.55,'Brass',(0,1,0),16)
    for i in range(8):
        a=i*pi/4
        beam('Wheel spoke',(x+r*.17*cos(a),y,z+r*.17*sin(a)),(x+r*.76*cos(a),y,z+r*.76*sin(a)),r*.115,r*.27,'Iron',.006)

def train_chassis(length=3.45,width=1.4):
    box('Underframe',(0,0,.47),(length,width*.82,.22),'Iron')
    for i in range(10):box('Floorboard',(-length/2+(i+.5)*length/10,0,.66),(length/10-.012,width,.15),'WoodLight',.012)
    for side in (-1,1):
        box('Olive side sill',(0,side*(width/2+.01),.60),(length+.10,.12,.26),'Olive')
        box('Brass body trim',(0,side*(width/2+.078),.69),(length,.012,.026),'Brass',.003)
        for x in (-1.20,-.86,.86,1.20):wheel(x,side*.63,.24,.23)
        for x in (-1.02,1.02):box('Bogie housing',(x,side*.65,.38),(.72,.16,.20),'Iron',.03)
    for x in (-length/2-.17,length/2+.17):
        rod('Coupler stem',(x-.12,0,.43),(x+.12,0,.43),.08,'Iron')
        ring('Coupling loop',(x,0,.43),.15,.095,.085,'Iron',n=16)

def carriage_sign(word):
    box('Sign trim',(0,-.79,.91),(1.36,.055,.32),'Brass',.04)
    box('Wood nameplate',(0,-.825,.91),(1.29,.04,.26),'WoodDark',.03)
    label(word,(0,-.852,.91),.18)

def locomotive():
    new_asset(1,'Steam locomotive','Train')
    box('Red main running board',(0,0,.65),(3.45,1.40,.18),'Red')
    box('Steel chassis',(0,0,.46),(3.10,1.10,.20),'Iron')
    for y in (-.66,.66):
        for x in (-1.08,.02,1.10):wheel(x,y)
        side=1 if y>0 else -1
        beam('Drive rod',(-1.08,y+side*.14,.42),(1.10,y+side*.14,.42),.065,.095,'Brass')
        for x in (-1.08,.02,1.10):bolt((x,y+side*.20,.42),.055,(0,side,0))
    cyl('Boiler',(-.56,0,1.23),.46,1.95,'Iron',(1,0,0),32)
    for x in (-1.48,-.93,-.18,.37):ring('Boiler brass band',(x,0,1.23),.479,.452,.055,'Brass',(1,0,0),32)
    cyl('Boiler front',(-1.57,0,1.23),.44,.12,'Black',(-1,0,0),32)
    for i in range(12):
        a=i*2*pi/12;bolt((-1.64,.374*cos(a),1.23+.374*sin(a)),.024,(-1,0,0))
    cyl('Headlamp casing',(-1.72,0,1.32),.20,.23,'Brass',(-1,0,0),24)
    cyl('Headlamp lens',(-1.845,0,1.32),.153,.025,'Amber',(-1,0,0),24)
    lathe('Smokestack',(-1.10,0,1.63),[(.13,0),(.14,.14),(.11,.48),(.19,.66),(.185,.75),(.12,.76),(.105,.69)],'Iron',24)
    ring('Chimney brass rim',(-1.10,0,2.36),.194,.135,.055,'Brass')
    lathe('Steam dome',(-.25,0,1.58),[(.15,0),(.17,.08),(.16,.23),(.11,.31),(.02,.34)],'Brass',24)
    box('Cab floor',(1.06,0,.82),(1.25,1.35,.14),'WoodDark')
    for sy in (-1,1):
        y=sy*.64
        box('Cab lower panel',(1.02,y,1.18),(1.23,.09,.63),'Red',.025)
        box('Cab panel inset',(1.02,y+sy*.055,1.20),(.94,.025,.39),'Brass',.03)
        box('Cab panel red inset',(1.02,y+sy*.074,1.20),(.89,.023,.34),'Red',.03)
        for x in (.45,1.60):
            box('Cab window post',(x,y,1.88),(.11,.11,.81),'Red')
            box('Window gold frame',(x+.035*(-1 if x>1 else 1),y+sy*.055,1.89),(.025,.028,.64),'Brass',.005)
        box('Cab header',(1.02,y,2.26),(1.25,.12,.14),'Red')
        box('Window lower frame',(1.02,y+sy*.04,1.51),(1.12,.055,.04),'Brass')
    box('Cab rear lower panel',(1.62,0,1.14),(.10,1.25,.55),'Red')
    for y in (-.57,.57):box('Rear corner pillar',(1.62,y,1.89),(.10,.12,.82),'Red')
    box('Rear top rail',(1.62,0,2.26),(.1,1.25,.14),'Red')
    roofpts=[(-.82+i*1.64/16,2.29+.17*cos((-pi/2)+i*pi/16)) for i in range(17)]
    v=[(x,y,z+dz) for dz in (0,.07) for x in (.30,1.79) for y,z in roofpts]
    f=[];n=17
    for j in range(n-1):
        f.extend([(j,j+1,n+j+1,n+j),(2*n+j,3*n+j,3*n+j+1,2*n+j+1),
                  (j,2*n+j,2*n+j+1,j+1),(n+j,n+j+1,3*n+j+1,3*n+j)])
    f.extend([(0,n,3*n,2*n),(n-1,2*n-1,4*n-1,3*n-1)])
    mesh('Curved cab roof',v,f,'Iron',bevel=.012)
    box('Control console',(.61,0,1.19),(.16,.60,.53),'Iron')
    ring('Driver valve',(.72,-.18,1.49),.13,.10,.024,'Red',(1,0,0),20)
    for sy in (-1,1):
        beam('Hand rail',(-1.31,sy*.39,1.59),(.30,sy*.39,1.59),.025,.025,'Brass')
        cyl('Piston casing',(-1.23,sy*.56,.70),.12,.47,'Iron',(1,0,0),20)
        box('Cab step',(1.26,sy*.80,.44),(.62,.27,.075),'Iron')
    beam('Cowcatcher top',(-1.73,-.63,.70),(-1.73,.63,.70),.11,.09,'Red')
    beam('Cowcatcher toe',(-2.17,-.69,.17),(-2.17,.69,.17),.09,.09,'Red')
    for y in (-.6,-.4,-.2,0,.2,.4,.6):beam('Cowcatcher slat',(-1.73,y,.69),(-2.17,y*1.13,.20),.07,.055,'Red')
    for y in (-.43,.43):cyl('Front buffer',(-1.83,y,.78),.10,.14,'Brass',(-1,0,0),16)
    rod('Rear coupler',(1.64,0,.49),(1.96,0,.49),.08,'Iron')

def greenhouse():
    new_asset(2,'Greenhouse carriage','Train');train_chassis()
    for y in (-.65,.65):box('Greenhouse sill',(0,y,.88),(3.30,.08,.33),'Wood')
    for x in (-1.61,1.61):box('Greenhouse end sill',(x,0,.88),(.09,1.38,.33),'Olive')
    for x in (-1.60,-.80,0,.80,1.60):
        points=[(x,-.69,.86),(x,-.69,1.46)]
        points.extend([(x,-.69*cos(i*pi/12),1.46+.70*sin(i*pi/12)) for i in range(13)])
        points.append((x,.69,.86));tube('Greenhouse arch',points,.025,'Steel',8)
    for y,z in [(-.69,1.45),(.69,1.45),(0,2.16)]:rod('Greenhouse longitudinal rib',(-1.62,y,z),(1.62,y,z),.025,'Steel')
    for x in (-.96,.55):
        for y in (-.34,.34):planter((x,y,.75),(1.22,.53,.30),True)
    pot((1.40,0,.75),.17,.27,False);sprout((1.40,0,1.02),1.6,True)
    carriage_sign('GREENHOUSE')

def kitchen():
    new_asset(3,'Kitchen carriage','Train');train_chassis()
    for i in range(6):box('Back wall board',(-1.40+i*.56,.68,1.33),(.55,.12,1.25),'WoodLight')
    box('Back wall cap',(0,.68,1.98),(3.43,.16,.09),'Wood')
    for x in (-1.68,1.68):box('End half wall',(x,0,1.16),(.12,1.44,.93),'Wood')
    stove((1.10,.28,.75),.77)
    table((-.46,-.03,.75),1.29,.62,.62)
    for x in (-.98,.12):chair((x,-.48,.75),.64)
    box('Kitchen shelf',(-.85,.48,1.70),(1.24,.40,.07),'WoodDark')
    for x in (-1.24,-.88,-.51):bowl((x,.43,1.75),.13,'White')
    for x in (-1.30,-.96,-.62):
        rod('Utensil handle',(x,.55,1.46),(x,.55,1.25),.017,'Steel')
        ball('Utensil spoon',(x,.55,1.22),(.045,.018,.065),'Steel')
    for x in (-.83,-.13):
        bowl((x,-.04,1.43),.12,'White')
        ball('Meal',(x,-.04,1.51),(.08,.08,.028),'Orange')
    box('Kitchen rug',(-.40,-.10,.756),(1.7,1.0,.012),'Red',.015)
    pot((-1.39,.37,.76),.14,.23)
    carriage_sign('KITCHEN')

def tool_rack(p=(0,0,0),w=1.5,h=.75):
    x,y,z=p
    for j in range(3):box('Rack backboard',(x,y,z+h*(j+.5)/3),(w,.10,h/3-.008),'WoodLight')
    for k in range(4):
        xx=x-w*.34+k*w*.225;yy=y-.08
        if k<3:
            rod('Wrench handle',(xx,yy,z+h*.22),(xx,yy,z+h*.65),.032,'Steel')
            ring('Wrench ring',(xx,yy,z+h*.20),.083,.045,.04,'Steel',(0,1,0),16)
            # An open jaw, made from a partial circular tube.
            points=[(xx+.088*cos(.35*pi+i*1.3*pi/12),yy,z+h*.72+.088*sin(.35*pi+i*1.3*pi/12)) for i in range(13)]
            tube('Wrench jaw',points,.034,'Steel',8)
        else:
            rod('Hammer handle',(xx,yy,z+h*.20),(xx,yy,z+h*.75),.036,'WoodDark')
            box('Hammer head',(xx,yy,z+h*.74),(.26,.13,.12),'Iron')
        bolt((xx,yy-.008,z+h*.89),.022,m='Iron')

def workbench(p=(0,0,0),w=1.5,d=.66,h=.82):
    x,y,z=p;table(p,w,d,h)
    box('Workbench shelf',(x,y,z+.20),(w-.23,d-.12,.08),'Wood')
    box('Drawer',(x+w*.26,y,z+h*.58),(w*.34,d*.9,h*.43),'WoodLight')
    rod('Drawer handle',(x+w*.19,y-d*.48,z+h*.62),(x+w*.34,y-d*.48,z+h*.62),.019,'Iron')
    box('Vice fixed jaw',(x-w*.30,y-d*.49,z+h+.055),(.22,.08,.18),'Steel')
    box('Vice moving jaw',(x-w*.30,y-d*.68,z+h+.025),(.22,.07,.16),'Steel')
    rod('Vice screw',(x-w*.30,y-d*.85,z+h-.01),(x-w*.30,y-d*.37,z+h-.01),.025,'Iron')
    rod('Vice handle',(x-w*.30,y-d*.84,z+h-.15),(x-w*.30,y-d*.84,z+h+.09),.018,'Steel')

def workshop():
    new_asset(4,'Workshop carriage','Train');train_chassis()
    for i in range(6):box('Workshop backboard',(-1.40+i*.56,.68,1.29),(.55,.12,1.16),'WoodLight')
    box('Back wall trim',(0,.68,1.9),(3.46,.16,.08),'Wood')
    for x in (-1.68,1.68):box('Workshop end',(x,0,1.13),(.12,1.44,.84),'Olive')
    tool_rack((.47,.59,1.24),1.78,.57)
    workbench((.99,.20,.75),.92,.55,.47)
    crate((-.95,-.24,.75),.61);crate((-.83,.34,.75),.56)
    crate((-.88,.23,1.32),.42);crate((.05,-.29,.75),.69)
    carriage_sign('WORKSHOP')

def track(p=(0,0,0),length=3.9,width=1.40):
    x,y,z=p
    for i in range(9):
        xx=x-length/2+(i+.5)*length/9
        box('Railway sleeper',(xx,y,z+.10),(.20,width+.45,.20),'WoodDark')
        for sy in (-1,1):
            box('Tie plate',(xx,y+sy*.54,z+.215),(.20,.23,.04),'Iron',.007)
            for sx in (-1,1):bolt((xx+sx*.07,y+sy*.54+.07,z+.255),.02,(0,0,1),'Iron')
    for sy in (-1,1):
        box('Rail foot',(x,y+sy*.54,z+.25),(length,.18,.06),'Iron',.012)
        box('Rail web',(x,y+sy*.54,z+.32),(length,.075,.12),'Steel',.009)
        box('Rail head',(x,y+sy*.54,z+.41),(length,.15,.08),'Steel',.012)

def fence(p=(0,0,0),length=2.25):
    x,y,z=p
    for xx in (-length/2,0,length/2):box('Fence post',(x+xx,y,z+.59),(.14,.16,1.18),'Wood',.025)
    for zz in (.41,.87):box('Fence rail',(x,y-.04,z+zz),(length+.13,.085,.15),'WoodLight',.018)
    for xx in (-length/2,0,length/2):
        for zz in (.41,.87):bolt((x+xx,y-.095,z+zz),.024,m='Iron')

def bench(p=(0,0,0),length=1.6):
    x,y,z=p
    for xx in (-length*.34,length*.34):
        for yy in (-.19,.19):box('Bench foot',(x+xx,y+yy,z+.25),(.085,.085,.50),'Iron')
        beam('Bench back support',(x+xx,y+.20,z+.34),(x+xx,y+.27,z+1.05),.065,.07,'Iron')
        box('Seat bracket',(x+xx,y,z+.43),(.085,.57,.075),'Iron')
    for j in range(4):box('Bench seat slat',(x,y-.24+(j+.5)*.12,z+.51),(length,.105,.065),'WoodLight')
    for j in range(3):box('Bench back slat',(x,y+.25,z+.70+j*.145),(length,.07,.12),'WoodLight')

def clock(p=(0,0,0),r=.47,stand=True):
    x,y,z=p
    if stand:
        cyl('Clock support',(x+r+.18,y+.1,z+r+.10),.045,2*r+.2,'Iron',n=12)
        rod('Clock bracket',(x+r+.18,y+.1,z+r+.52),(x,y+.1,z+r+.52),.045,'Iron')
        ring('Clock hanger',(x,y+.06,z+2*r+.025),.060,.035,.035,'Iron',(0,1,0),16)
    cyl('Clock casing',(x,y,z+r),r,.13,'Iron',(0,1,0),32)
    cyl('Clock dial',(x,y-.079,z+r),r*.88,.025,'Cream',(0,1,0),32)
    for i in range(12):
        a=i*pi/6
        beam('Clock hour mark',(x+r*.69*sin(a),y-.098,z+r+r*.69*cos(a)),(x+r*.79*sin(a),y-.098,z+r+r*.79*cos(a)),.025,.018,'Iron',.003)
    rod('Clock hour hand',(x,y-.125,z+r),(x-r*.15,y-.125,z+r+r*.36),.024,'Iron')
    rod('Clock minute hand',(x,y-.132,z+r),(x+r*.53,y-.132,z+r-r*.24),.018,'Iron')
    bolt((x,y-.15,z+r),r*.06,m='Brass')

def signboard(p=(0,0,0),w=1.7):
    x,y,z=p
    for xx in (-w*.36,w*.36):box('Sign post',(x+xx,y,z+.80),(.11,.12,1.60),'WoodDark')
    for j in range(3):box('Sign plank',(x,y-.04,z+.93+j*.20),(w,.105,.19),'WoodLight')
    for xx in (-w*.40,w*.40):
        for zz in (.93,1.33):bolt((x+xx,y-.105,z+zz),.028,m='Iron')

def lamp(p=(0,0,0),height=2.6):
    x,y,z=p
    lathe('Lamp base',p,[(.21,0),(.21,.07),(.16,.12),(.13,.17),(.11,.38),(.062,.45),(.055,height-.28)],'Iron',20)
    pts=[(x,y,z+height-.3),(x,y,z+height-.05),(x+.08,y,z+height+.12),(x+.24,y,z+height+.16),
         (x+.43,y,z+height+.10),(x+.49,y,z+height-.05),(x+.49,y,z+height-.18)]
    tube('Lamp curved arm',pts,.035,'Iron',10)
    lx=x+.49;lz=z+height-.51
    box('Lantern glow',(lx,y,lz),(.22,.22,.35),'Amber',.015)
    for xx in (-.13,.13):
        for yy in (-.13,.13):beam('Lantern corner',(lx+xx,y+yy,lz-.21),(lx+xx*.79,y+yy*.79,lz+.20),.025,.025,'Iron')
    box('Lantern base',(lx,y,lz-.23),(.33,.33,.07),'Iron')
    cyl('Lantern roof',(lx,y,lz+.27),.27,.16,'Iron',n=4,r2=.09)
    cyl('Lantern cap',(lx,y,lz+.40),.043,.12,'Iron',n=12)

def window(p,w=.6,h=.85):
    x,y,z=p
    box('Recessed window',(x,y,z),(w,.075,h),'WoodDark')
    box('Window glass',(x,y-.048,z),(w-.10,.025,h-.10),'Window',.018)
    for xx in (-w/2,w/2):box('Window jamb',(x+xx,y-.065,z),(.075,.065,h+.08),'WoodLight')
    for zz in (-h/2,h/2):box('Window lintel',(x,y-.065,z+zz),(w+.10,.07,.075),'WoodLight')
    box('Window mullion',(x,y-.075,z),(.035,.04,h),'WoodLight',.005)
    box('Window transom',(x,y-.075,z),(w,.04,.035),'WoodLight',.005)
    box('Window sill',(x,y-.12,z-h/2-.06),(w+.21,.23,.08),'StoneLight')

def tiled_roof(p=(0,0,0),w=3.6,d=2.55,rise=.82):
    x,y,z=p
    for side in (-1,1):
        v=[(x-w/2,y,z+rise),(x+w/2,y,z+rise),(x+w/2,y+side*d/2,z),(x-w/2,y+side*d/2,z)]
        o=mesh('Roof underlay',v,[(0,1,2,3)],'WoodDark')
        so=o.modifiers.new('Roof thickness','SOLIDIFY');so.thickness=.07
        nx=max(5,round(w/.33));ny=5
        for j in range(ny):
            ya=(j-.02)*d/(2*ny);yb=(j+1.16)*d/(2*ny)
            for i in range(nx):
                cx=x-w/2+(i+.5)*w/nx;tw=w/nx*.96
                vv=[]
                for dist in (ya,yb):
                    for k in range(7):
                        dx=-tw/2+k*tw/6
                        zz=z+rise*(1-dist/(d/2))+.055+.035*sin(k*pi/6)
                        vv.append((cx+dx,y+side*dist,zz))
                ff=[(k,k+1,k+8,k+7) for k in range(6)]
                t=mesh('Terracotta roof tile',vv,ff,'RoofLight' if (i+j)%4==0 else 'RoofRed',True)
                so=t.modifiers.new('Tile thickness','SOLIDIFY');so.thickness=.035
        beam('Eave fascia',(x-w/2,y+side*d/2,z-.045),(x+w/2,y+side*d/2,z-.045),.09,.12,'WoodDark')
    for i in range(max(5,round(w/.3))):
        xx=x-w/2+(i+.5)*w/max(5,round(w/.3))
        cyl('Ridge tile',(xx,y,z+rise+.07),.13,w/max(5,round(w/.3))*.95,'RoofRed',(1,0,0),12)

def building(station=False):
    if station:new_asset(6,'Station building','Buildings')
    else:new_asset(8,'Village cottage','Buildings')
    w,d,h=(3.20,2.05,1.90) if station else (1.95,1.75,1.60)
    base=.20;rise=.88
    box('Foundation',(0,0,.10),(w+.48,d+.70,.20),'Stone',.06)
    box('Plaster walls',(0,0,base+h/2),(w,d,h),'Plaster',.035)
    # Gable ends beneath the roof, no invisible open cavity.
    v=[(-w/2,-d/2,base+h),(-w/2,d/2,base+h),(-w/2,0,base+h+rise),
       (w/2,-d/2,base+h),(w/2,d/2,base+h),(w/2,0,base+h+rise)]
    mesh('Gable walls',v,[(0,2,1),(3,4,5),(0,3,5,2),(1,2,5,4),(0,1,4,3)],'Plaster')
    for xx in (-w/2,w/2):
        for yy in (-d/2,d/2):
            for j in range(7):box('Corner masonry',(xx,yy,base+(j+.5)*h/7),(.22,.22,h/7-.025),'StoneLight',.015)
    front=-d/2-.025
    doorx=0 if station else -.35
    box('Door surround',(doorx,front,base+.70),(.70,.13,1.40),'WoodDark')
    for j in range(4):box('Door plank',(doorx-.26+(j+.5)*.13,front-.085,base+.67),(.125,.07,1.30),'Wood',.009)
    box('Door window',(doorx,front-.13,base+.96),(.38,.025,.38),'Window')
    box('Door window divider',(doorx,front-.15,base+.96),(.025,.02,.40),'WoodLight',.003)
    bolt((doorx+.18,front-.155,base+.58),.035,m='Brass')
    box('Door step',(doorx,front-.26,.15),(.86,.53,.16),'StoneLight')
    if station:
        window((-1.07,front,base+.94),.59,.80)
        window((1.07,front,base+.94),.59,.80)
        box('Station sign frame',(0,front-.06,base+1.68),(2.38,.12,.29),'WoodDark')
        box('Station sign',(0,front-.13,base+1.68),(2.26,.04,.22),'Cream',.016)
        label('MEADOWVALE',(0,front-.157,base+1.68),.157,'WoodDark')
        bench((1.0,front-.47,.21),1.07)
        pot((-1.25,front-.43,.20),.24,.34)
        # Clock on the left gable side.
        before=set(CURRENT.objects)
        clock((0,0,0),.27,False)
        anchor=Vector((-w/2-.065,-.23,base+1.55))
        from mathutils import Matrix
        rot=Matrix.Rotation(-pi/2,4,'Z')
        for o in set(CURRENT.objects)-before:
            o.matrix_basis=rot@o.matrix_basis;o.location+=anchor
    else:
        window((.58,front,.96),.43,.64)
        pot((.61,front-.35,.20),.20,.28)
    tiled_roof((0,0,base+h),w+.46,d+.50,rise)
    chimx=w*.27;chimy=.40
    box('Chimney',(chimx,chimy,base+h+rise-.02),(.35,.34,.81),'Stone')
    for j in range(5):box('Chimney mortar',(chimx,chimy,base+h+rise-.35+j*.145),(.36,.35,.018),'StoneLight',.002)
    box('Chimney cap',(chimx,chimy,base+h+rise+.40),(.47,.46,.09),'RoofRed')
    for yy in (-d/2,d/2):
        box('Wall timber beam',(0,yy,base+h-.09),(w+.06,.12,.12),'WoodDark')

def bridge():
    new_asset(7,'Stone bridge','Buildings')
    length=5.35;halfwidth=.70;spring=.48;r=.95;top=1.83
    for x in (-2.49,0,2.49):
        for j in range(3):box('Bridge pier',(x,0,(j+.5)*.25),(.46,1.42,.24),'Stone' if j%2 else 'StoneLight',.025)
    for center in (-1.245,1.245):
        # Solid spandrel strips above each arch opening.
        n=16
        for i in range(n):
            a=pi*i/n;b=pi*(i+1)/n
            xa=center+r*cos(a);xb=center+r*cos(b)
            za=spring+r*sin(a);zb=spring+r*sin(b)
            v=[(xa,y,zz) for y in (-halfwidth,halfwidth) for zz in (za,top)]
            v.extend([(xb,y,zz) for y in (-halfwidth,halfwidth) for zz in (zb,top)])
            mesh('Arch spandrel',v,[(0,4,5,1),(2,3,7,6),(0,2,6,4),(1,5,7,3),(0,1,3,2),(4,6,7,5)],'Stone')
        for side in (-1,1):
            for i in range(13):
                a=pi*i/13+.012;b=pi*(i+1)/13-.012
                v=[(center+rr*cos(t),side*.722+yy,spring+rr*sin(t)) for yy in (-.028,.028) for rr in (r,1.18) for t in (a,b)]
                mesh('Arch voussoir',v,[(0,1,3,2),(4,6,7,5),(0,4,5,1),(2,3,7,6),(0,2,6,4),(1,5,7,3)],'StoneLight' if i%3 else 'StoneDark',bevel=.012)
    box('Bridge road base',(0,0,1.89),(length,1.53,.14),'Stone',.025)
    for i in range(13):
        for j in range(3):box('Road cobble',(-length/2+(i+.5)*length/13,-.50+j*.50,1.98),(length/13-.019,.475,.07),'StoneLight' if (i+j)%3 else 'Stone',.012)
    for side in (-1,1):
        for j in range(2):
            for i in range(10):box('Parapet block',(-length/2+(i+.5)*length/10,side*.76,2.10+j*.21),(length/10-.018,.25,.195),'Stone' if (i+j)%3 else 'StoneLight',.022)
        box('Parapet cap',(0,side*.76,2.45),(length+.04,.30,.10),'StoneLight',.025)

def pine(p=(0,0,0),s=1):
    x,y,z=p;cyl('Pine trunk',(x,y,z+.74*s),.105*s,1.48*s,'Bark',n=10,r2=.06*s)
    for tier,(zz,r,h) in enumerate([(.60,.70,.88),(1.05,.59,.85),(1.48,.46,.74),(1.86,.32,.65),(2.17,.20,.54)]):
        n=10;v=[]
        for j,(rr,hh) in enumerate([(r,0),(r*.81,h*.20),(r*.46,h*.61),(.014,h)]):
            for i in range(n):
                a=2*pi*i/n+(tier%2)*.16
                v.append((x+s*rr*cos(a),y+s*rr*sin(a),z+s*(zz+hh-(.06 if j==0 and i%2 else 0))))
        f=[tuple(range(n-1,-1,-1))]
        for j in range(3):
            for i in range(n):f.append((j*n+i,j*n+(i+1)%n,(j+1)*n+(i+1)%n,(j+1)*n+i))
        o=mesh('Pine foliage tier',v,f,['LeafDark','Leaf','LeafLight'][tier%3])

def leafy_tree(p=(0,0,0),s=1):
    x,y,z=p
    rod('Tree trunk',(x,y,z),(x+.06*s,y,z+1.61*s),.13*s,'Bark',12)
    for i in range(7):
        a=i*2.4;r=.42 if i<6 else 0
        xx=x+r*s*cos(a);yy=y+r*s*sin(a);zz=z+(1.60+.26*(i%3))*s
        rod('Tree branch',(x,y,z+.89*s),(xx,yy,zz),.06*s,'Bark',10)
        ball('Leafy crown',(xx,yy,zz),(.55*s,.52*s,.53*s),['Leaf','LeafLight','LeafDark'][i%3],12,7,True)
        for k in range(3):
            aa=a+k*2.1
            ball('Crown detail',(xx+.30*s*cos(aa),yy+.30*s*sin(aa),zz+.28*s),(.22*s,.23*s,.18*s),'LeafLight',10,5,True)

def rock(p=(0,0,0),s=(.7,.5,.6),m='StoneDark'):
    o=ball('Boulder',(p[0],p[1],p[2]+s[2]*.67),s,m,9,5,True)
    for v in o.data.vertices:
        v.co.x*=random.uniform(.88,1.12);v.co.y*=random.uniform(.88,1.12)
        v.co.z=max(-.67,v.co.z*random.uniform(.92,1.1))
    return o

def bush_flowers(p=(0,0,0),s=1):
    x,y,z=p
    for i in range(6):
        a=i*2.4;r=.25+random.random()*.15
        ball('Bush',(x+r*s*cos(a),y+r*s*sin(a),z+.19*s),(.27*s,.24*s,.24*s),['Leaf','LeafLight','LeafDark'][i%3],10,5,True)
    for i in range(8):
        a=i*2.4;r=.24+random.random()*.30
        flower((x+r*s*cos(a),y+r*s*sin(a),z+.17*s),(.65+.4*random.random())*s,['White','FlowerPink','Yellow'][i%3])

def waterfall_tile():
    new_asset(30,'River and waterfall','Landscape')
    box('Terrain tile',(0,0,.11),(3.8,3.8,.22),'Stone',.14)
    box('River pool',(0,-.35,.235),(3.30,2.75,.06),'Water',.25)
    for i in range(7):
        xx=-1.61+i*.54
        rock((xx,1.26,.21),(.44,.49,.65+random.random()*.25),'StoneDark')
    for side in (-1,1):
        for j in range(6):rock((side*1.65,-1.45+j*.53,.18),(.22,.30,.22),'StoneLight')
    box('Upper pool',(0,1.29,1.56),(1.25,1.0,.055),'Water',.12)
    # Curved stream ribbon comes over the cliff, falls, then curls into the basin.
    path=[(.88,1.56),(.62,1.53),(.48,1.41),(.38,1.10),(.29,.76),(.12,.42),(-.08,.27),(-.42,.255)]
    v=[(x,y,z) for y,z in path for x in (-.52,.52)]
    f=[(2*i,2*i+1,2*i+3,2*i+2) for i in range(len(path)-1)]
    mesh('Waterfall sheet',v,f,'Water',True)
    for i in range(9):
        xx=-.44+i*.11
        tube('Falling water streak',[(xx+.025*sin(j*2+i),y-.018,z+.016) for j,(y,z) in enumerate(path[:-1])],.018 if i%2 else .03,'Foam',6)
    for i in range(14):
        a=i*2.4
        ball('Foam at fall',(cos(a)*(.2+i*.027),-.19+sin(a)*.26,.29),(.11,.075,.025),'Foam',10,4)
    for y in (-.66,-1.06,-1.39):
        tube('Surface ripple',[(-.55+i*.13,y+.03*sin(i),.278) for i in range(9)],.013,'Foam',6)
    pine((-1.20,1.20,.83),.52);pine((1.17,1.39,.89),.48)
    bush_flowers((-1.42,-1.30,.28),.45)

def cooking_utensils():
    new_asset(21,'Cooking utensils','Kitchen props')
    box('Hanging rail',(0,.04,1.08),(1.4,.10,.16),'Wood')
    for i in range(4):
        x=-.49+i*.33
        rod('Utensil handle',(x,-.02,.95),(x,-.02,.44),.033,'WoodDark' if i<2 else 'Steel')
        ring('Hanging loop',(x,-.02,1.01),.045,.026,.028,'Steel',(0,1,0),12)
        if i==0:
            lathe('Frying pan',(x,-.01,.27),[(.01,-.02),(.14,-.02),(.20,.015),(.21,.08),(.185,.09),(.15,.035),(.01,.028)],'Iron',24,(0,-1,0))
        elif i==2:
            ball('Skimmer head',(x,-.015,.29),(.125,.025,.155),'Steel',16,6)
            for row in range(3):
                for col in range(3):cyl('Skimmer perforation',(x+(col-1)*.057,-.043,.29+(row-1)*.07),.012,.003,'Iron',(0,1,0),8)
        else:ball('Spoon head',(x,-.02,.28),(.115,.045,.16),'Steel',16,6)

def all_assets():
    locomotive();greenhouse();kitchen();workshop()
    new_asset(5,'Railway track','Train');track()
    building(True);bridge();building(False)
    new_asset(9,'Wooden fence','Outdoor props');fence()
    new_asset(10,'Signboard','Outdoor props');signboard()
    new_asset(11,'Lamp post','Outdoor props');lamp()
    new_asset(12,'Station bench','Outdoor props');bench()
    new_asset(13,'Station clock','Outdoor props');clock()
    new_asset(14,'Wooden crate','Storage');crate(s=.9)
    new_asset(15,'Barrel','Storage');barrel()
    new_asset(16,'Wood stove','Kitchen props');stove()
    new_asset(17,'Dining table','Furniture');table()
    new_asset(18,'Wooden chair','Furniture');chair()
    new_asset(19,'Workbench','Workshop props');workbench()
    new_asset(20,'Tool rack','Workshop props');tool_rack()
    cooking_utensils()
    new_asset(22,'Bowls and plates','Kitchen props');dishes(s=1.7)
    new_asset(23,'Planter box','Garden');planter()
    new_asset(24,'Flower pot','Garden');pot(r=.32,h=.46)
    new_asset(25,'Vegetable crops','Garden')
    box('Vegetable soil bed',(0,0,.055),(1.20,1.10,.11),'Soil',.12)
    for i in range(3):
        for j in range(3):
            x=(i-1)*.35;y=(j-1)*.32;sprout((x,y,.10),.9,(i+j)%3==0)
            if (i+j)%3==1:lathe('Carrot',(x,y,.10),[(.01,0),(.057,.035),(.073,.13),(.045,.20)],'Orange',12)
    new_asset(26,'Pine tree','Landscape');pine()
    new_asset(27,'Leafy tree','Landscape');leafy_tree()
    new_asset(28,'Bushes and flowers','Landscape');bush_flowers()
    new_asset(29,'Boulders','Landscape')
    rock((-.28,.12,0),(.65,.52,.80),'StoneDark')
    rock((.43,-.25,0),(.42,.34,.39),'Stone')
    rock((-.52,-.40,0),(.28,.23,.24),'StoneLight')
    waterfall_tile()

def bounds(objects):
    pts=[o.matrix_world@Vector(p) for o in objects if o.type=='MESH' for p in o.bound_box]
    return Vector(tuple(min(p[i] for p in pts) for i in range(3))),Vector(tuple(max(p[i] for p in pts) for i in range(3)))

def aim(obj,target):
    obj.rotation_euler=(Vector(target)-obj.location).to_track_quat('-Z','Y').to_euler()

def setup_studio():
    global CURRENT,ROOT
    CURRENT=bpy.data.collections.new('STUDIO');SCENE.collection.children.link(CURRENT)
    ROOT=bpy.data.objects.new('STUDIO_ROOT',None);CURRENT.objects.link(ROOT)
    box('Studio ground',(0,0,-.09),(220,220,.12),'Backdrop',0)
    for name,p,power,size in [('Key',(-4,-6,8),1300,5),('Fill',(6,-2,5),700,5),('Rim',(0,5,7),1100,4)]:
        d=bpy.data.lights.new(name,'AREA');d.energy=power;d.shape='DISK';d.size=size
        o=bpy.data.objects.new(name,d);CURRENT.objects.link(o);o.location=p;aim(o,(0,0,0))
    d=bpy.data.cameras.new('Asset camera');o=bpy.data.objects.new('Asset camera',d);CURRENT.objects.link(o)
    d.type='ORTHO';d.lens=50;d.clip_end=500;o.location=(6,-8,6);aim(o,(0,0,.8));SCENE.camera=o
    world=bpy.data.worlds.new('Warm studio');SCENE.world=world;world.use_nodes=True
    world.node_tree.nodes['Background'].inputs['Color'].default_value=(.62,.67,.71,1)
    world.node_tree.nodes['Background'].inputs['Strength'].default_value=.65
    SCENE.render.engine='CYCLES';SCENE.cycles.device='CPU';SCENE.cycles.samples=24
    SCENE.cycles.use_denoising=True
    SCENE.render.threads_mode='FIXED';SCENE.render.threads=8
    SCENE.render.resolution_x=480;SCENE.render.resolution_y=480;SCENE.render.resolution_percentage=100
    SCENE.render.image_settings.file_format='PNG';SCENE.render.image_settings.color_mode='RGB'
    SCENE.view_settings.view_transform='AgX'
    SCENE.render.film_transparent=False
    return CURRENT

def fit_camera(lo,hi):
    center=(lo+hi)/2;span=(hi-lo).length
    cam=SCENE.camera;cam.location=center+Vector((-6,-8,5.5)).normalized()*max(5,span*3)
    aim(cam,center);bpy.context.view_layer.update()
    inv=cam.matrix_world.inverted()
    corners=[inv@Vector((x,y,z)) for x in (lo.x,hi.x) for y in (lo.y,hi.y) for z in (lo.z,hi.z)]
    width=max(v.x for v in corners)-min(v.x for v in corners)
    height=max(v.y for v in corners)-min(v.y for v in corners)
    cam.data.ortho_scale=max(width,height)*1.22

def run():
    print('BUILD: constructing all 30 catalog objects',flush=True)
    all_assets();bpy.context.view_layer.update()
    # Convert lettering into real mesh geometry for portable GLB files.
    bpy.ops.object.select_all(action='DESELECT')
    fonts=[o for a in ASSETS for o in a['collection'].objects if o.type=='FONT']
    if fonts:
        for o in fonts:o.select_set(True)
        bpy.context.view_layer.objects.active=fonts[0];bpy.ops.object.convert(target='MESH')
    bpy.ops.object.select_all(action='DESELECT');bpy.context.view_layer.update()
    for a in ASSETS:
        for obj in a['collection'].objects:
            if obj.type=='MESH':
                bm=bmesh.new();bm.from_mesh(obj.data)
                bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
                bm.to_mesh(obj.data);bm.free()
    manifest=[]
    for a in ASSETS:
        coll=a['collection'];root=a['root'];lo,hi=bounds(coll.objects)
        # Ground every asset while retaining a common centered root at (0,0,0).
        for o in list(coll.objects):
            if o!=root:o.location.z-=lo.z
        bpy.context.view_layer.update();lo,hi=bounds(coll.objects)
        dims=[round(v,4) for v in hi-lo]
        meshes=[o for o in coll.objects if o.type=='MESH']
        for o in coll.objects:o.select_set(True)
        bpy.context.view_layer.objects.active=root
        file=OUT/'models'/f"{a['slug']}.glb"
        bpy.ops.export_scene.gltf(filepath=str(file),export_format='GLB',use_selection=True,
            export_apply=True,export_yup=True,export_cameras=False,export_lights=False,
            export_extras=True,export_materials='EXPORT')
        bpy.ops.object.select_all(action='DESELECT')
        entry={k:a[k] for k in ('number','name','slug','category')}
        entry.update(file=f"models/{file.name}",dimensions_m=dims,
            mesh_parts=len(meshes),base_vertices=sum(len(o.data.vertices) for o in meshes),
            has_materials=all(len(o.data.materials)>0 for o in meshes))
        manifest.append(entry)
        col=(a['number']-1)%5;row=(a['number']-1)//5
        root.location=(col*6.5,-row*5.9,0)
        print(f"EXPORTED {a['number']:02d}/30: {a['name']} ({len(meshes)} mesh parts)",flush=True)
    (OUT/'catalog_manifest.json').write_text(json.dumps({'generator':'Blender '+bpy.app.version_string,
        'units':'meters','source':'Selected Tiny Train Village object catalog',
        'asset_count':len(manifest),'assets':manifest},indent=2))
    setup_studio();bpy.context.view_layer.update()
    lo,hi=bounds([o for a in ASSETS for o in a['collection'].objects]);fit_camera(lo,hi)
    # Start the saved file with a useful material-colored overview.
    for screen in bpy.data.screens:
        for area in screen.areas:
            if area.type=='VIEW_3D':
                space=area.spaces.active;space.shading.type='MATERIAL'
                space.region_3d.view_distance=36;space.region_3d.view_location=(13,-14,0)
                space.region_3d.view_rotation=SCENE.camera.rotation_euler.to_quaternion()
    SCENE['catalog']='30 objects; one asset collection and named root per object'
    SCENE['geometry_note']='Stylized approximations, not automatic photogrammetry. No characters.'
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'Tiny_Train_Village.blend'),compress=True)
    print('SAVED Tiny_Train_Village.blend',flush=True)

if __name__=='__main__':run()
