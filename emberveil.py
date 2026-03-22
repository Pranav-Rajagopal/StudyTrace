"""
EMBERVEIL CHRONICLES  v4.0
Hero: Pranav  |  Class: Warrior
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Controls:
  WASD / Arrows   Move
  SPACE           Sword attack
  E               Interact (NPC / Chest / Door)
  I               Inventory  (mouse click to use/equip)
  Q               Use potion
  F5              Save game
  F9              Load game
  F11             Fullscreen
  ESC             Pause
"""

import pygame, sys, math, random, json, os

pygame.init()
pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)

WIN_W, WIN_H = 1280, 720
TILE = 48
FPS  = 60

screen    = pygame.display.set_mode((WIN_W, WIN_H), pygame.RESIZABLE)
pygame.display.set_caption("Emberveil Chronicles  v4  —  Pranav's Quest")
clock = pygame.time.Clock()
fullscreen = False
SAVE_FILE  = "emberveil_save.json"

# ═══════════════════════════════════════════
#  COLOURS
# ═══════════════════════════════════════════
BG       = (8,   8,  14)
WHITE    = (238,238,252)
GREY     = (100,100,120)
DGREY    = (28,  28, 48)
BLACK    = (0,   0,   0)

GRASS1   = (32,  78, 32);  GRASS2 = (40, 90, 40)
WALL_C   = (55,  55, 75);  WALLT  = (75, 75,100)
WATER1   = (18,  55,115);  WATER2 = (22, 65,135)
PATH_C   = (130,100, 60)
LAVA1    = (200, 60, 10);  LAVA2  = (220, 90, 20)
DARK1    = (35,  15,  5);  DARK2  = (45,  20,  8)
SAND1    = (180,155, 90);  SAND2  = (195,170,105)

PLAYER_C = (100,180,255);  PLAYER_D = (55,115,195)
SWORD_C  = (215,215,255)
DEMON_C  = (215, 55, 55);  DEMON_D  = (155, 25, 25)
SKEL_C   = (220,210,180);  SKEL_D   = (160,150,120)
BOSS_C   = (160, 20,200);  BOSS_D   = (100, 10,140)

HP_C = (55,195,75); HP_BG = (55,25,25)
XP_C = (95,135,255);XP_BG = (18,28,58)
MP_C = (60,100,240);MP_BG = (15,20,60)

YELLOW  = (255,215, 55)
ORANGE  = (255,135, 25)
RED     = (230, 50, 50)
GREEN   = (60, 200, 80)
GOLD    = (255,165, 30)
PURPLE  = (175, 80,255)
NPC_C   = (175,135,255); NPC_D = (115,75,195)
CHEST_C = (175,135, 38); CHEST_O = (215,175,75)
DOOR_C  = (140, 90, 40)
LOCKED  = (180, 50, 50)

RARITY_COL = {
    "common":   (180,180,180),
    "rare":     (80,140,255),
    "epic":     (175,80,255),
    "legendary":(255,165,30),
}

# ═══════════════════════════════════════════
#  FONTS
# ═══════════════════════════════════════════
def F(sz, bold=True):
    return pygame.font.SysFont("DejaVu Sans", sz, bold=bold)

F48=F(48); F32=F(32); F24=F(24); F20=F(20)
F18=F(18); F16=F(16); F14=F(14); F13=F(13); F12=F(12)

# ═══════════════════════════════════════════
#  SOUND  (pure generated tones, no files)
# ═══════════════════════════════════════════
def make_sound(freq=440, dur=0.08, vol=0.3, wave="sq", decay=True):
    import array, math as _m
    sr=44100; n=int(sr*dur)
    buf=array.array('h',[0]*(n*2))
    for i in range(n):
        t=i/sr
        if   wave=="sq":    raw=1.0 if _m.sin(2*_m.pi*freq*t)>=0 else -1.0
        elif wave=="noise": raw=random.uniform(-1.0,1.0)
        else:               raw=_m.sin(2*_m.pi*freq*t)
        env=(1.0-i/n)**1.5 if decay else 1.0
        v=max(-32768,min(32767,int(raw*env*vol*32767)))
        buf[i*2]=v; buf[i*2+1]=v
    return pygame.sndarray.make_sound(buf)

try:
    SND_SWORD  = make_sound(220, 0.10, 0.25, "sq")
    SND_HIT    = make_sound(150, 0.12, 0.30, "noise")
    SND_CHEST  = make_sound(660, 0.18, 0.20, "sin")
    SND_DOOR   = make_sound(330, 0.22, 0.20, "sin")
    SND_LEVEL  = make_sound(880, 0.30, 0.25, "sin")
    SND_DEATH  = make_sound(110, 0.35, 0.28, "noise")
    SND_OK     = True
    print("Sound OK")
except Exception as e:
    print(f"Sound disabled: {e}")
    SND_SWORD=SND_HIT=SND_CHEST=SND_DOOR=SND_LEVEL=SND_DEATH=None
    SND_OK = False

def play(snd):
    if SND_OK and snd is not None:
        try: snd.play()
        except: pass

# ═══════════════════════════════════════════
#  MUSIC  (simple looping tone sequence)
# ═══════════════════════════════════════════
music_notes = []
music_idx   = 0
music_timer = 0
MUSIC_INTERVAL = 28   # frames between notes
VILLAGE_MELODY = [262,294,330,349,392,349,330,294]
FOREST_MELODY  = [220,247,262,220,196,220,247,196]
VOLCANO_MELODY = [165,175,196,165,147,165,175,147]
cur_melody = VILLAGE_MELODY

def tick_music():
    global music_idx, music_timer, music_notes
    music_timer += 1
    if music_timer >= MUSIC_INTERVAL:
        music_timer = 0
        freq = cur_melody[music_idx % len(cur_melody)]
        music_idx += 1
        try:
            if SND_OK:
                snd = make_sound(freq, 0.18, 0.08, "sin", decay=True)
                snd.play()
        except: pass

# ═══════════════════════════════════════════
#  MAPS  (bigger: 50 cols x 28 rows each)
# ═══════════════════════════════════════════
VILLAGE_TILES = [
    "11111111111111111111111111111111111111111111111111",
    "10000000000000000000000100000000000000000000000001",
    "10030000000000000000000100000000000000000000003001",
    "10000001111100000000000100001111100000000000000001",
    "10000001000010000000000100001000010000000000000001",
    "10333301000013333000000100001000010000000033333001",
    "10000001000010000000000100001000010000000000000001",
    "10000001111100000000000100001111100000000000000001",
    "10000000000000000000000100000000000000000000000001",
    "10000000000000000000000100000000000000000000000001",
    "11111111111000000000000100000001111111111111111111",
    "10000000000000000000000100000000000000000000000001",
    "10000002220000000000000100000000000000000000000001",
    "10000222222000000000000100000000000000000000000001",
    "10000222222000000000000100000000000000000000000001",
    "10000002220000000000000100000000000000000000000001",
    "10000000000000000000000100000000000000000000000001",
    "10000000000000000000000100000000000000000000000001",
    "10000000000000000000000000000000000000000000000001",
    "10000000000000000000000000000000000000000000000001",
    "10000000000000000000000000000000000000000000000001",
    "10000000000001111111111111111111000000000000000001",
    "10000000000001000000000000000010000000000000000001",
    "10000000000001000000000000000010000000000000000001",
    "10000000000001000000000000000010000000000000000001",
    "10000000000001000000000000000010000000000000000001",
    "10000000000000000000000000000000000000000000000001",
    "11111111111111111111111D111111111111111111111111111",
]

FOREST_TILES = [
    "11111111111111111111111111111111111111111111111111",
    "10000000000000000000000000000000000000000000000001",
    "10000001110000000000000000000001110000000000000001",
    "10000001110000000000000000000001110000000000000001",
    "10000000000003333000000000000000000000000000000001",
    "10000000000000000000000000000000000000000000000001",
    "10000000000000000000000000000000000000000000000001",
    "10001110000000000000000000000000000011100000000001",
    "10001110000000000000000000000000000011100000000001",
    "10000000000000000000000000000000000000000000000001",
    "10000000003333333333333333330000000000000000000001",
    "10000000000000000000000000000000000000000000000001",
    "10000000000000000000000000000000000000000000000001",
    "10000001110000000000000000000001110000000000000001",
    "10000001110000000222220000000001110000000000000001",
    "10000000000000002222222000000000000000000000000001",
    "10000000000000000222220000000000000000000000000001",
    "10000000000000000000000000000000000000000000000001",
    "10000000000000000000000000000000000000000000000001",
    "10000000000000000000000000000000000000000000000001",
    "10000000000001111111111111111100000000000000000001",
    "10000000000001000000000000000100000000000000000001",
    "10000000000001000000000000000100000000000000000001",
    "10000000000001000000000000000100000000000000000001",
    "10000000000001000000000000000100000000000000000001",
    "10000000000000000000000000000000000000000000000001",
    "10000000000000000000000000000000000000000000000001",
    "1D111111111111111111111111111111111111111111111D11",
]

VOLCANO_TILES = [
    "11111111111111111111111111111111111111111111111111",
    "10000000000000000000000000000000000000000000000001",
    "10000000000000000000000000000000000000000000000001",
    "10000220000000000000000000000000000000002200000001",
    "10002222000000000000000000000000000000022220000001",
    "10000220000000000000000000000000000000002200000001",
    "10000000000000000000000000000000000000000000000001",
    "10000000000000000000000000000000000000000000000001",
    "10000000000000000011111111111110000000000000000001",
    "10000000000000000010000000000010000000000000000001",
    "10000000000000000010000000000010000000000000000001",
    "10000000000000000010000B000000100000000000000000001",
    "10000000000000000010000000000010000000000000000001",
    "10000000000000000011111111111110000000000000000001",
    "10000000000000000000000000000000000000000000000001",
    "10000220000000000000000000000000000000002200000001",
    "10002222000000000000000000000000000000022220000001",
    "10000220000000000000000000000000000000002200000001",
    "10000000000000000000000000000000000000000000000001",
    "10000000000000000000000000000000000000000000000001",
    "10000000000001111111111111111100000000000000000001",
    "10000000000001000000000000000100000000000000000001",
    "10000000000001000000000000000100000000000000000001",
    "10000000000001000000000000000100000000000000000001",
    "10000000000000000000000000000000000000000000000001",
    "10000000000000000000000000000000000000000000000001",
    "10000000000000000000000000000000000000000000000001",
    "1D111111111111111111111111111111111111111111111111",
]

MAP_DATA = {
    "village": {
        "tiles":  VILLAGE_TILES,
        "style":  "grass",
        "name":   "Emberveil Village",
        "start":  (3, 3),
        "melody": VILLAGE_MELODY,
        "doors":  {(23,27):"forest"},
        "quest":  {
            "id":    "village_clear",
            "title": "Clear the Village",
            "desc":  "Elder Maren: Kill all demons in the village to unlock the forest path.",
            "goal":  "kill_all",
            "unlock_door": (23,27),
            "key_item": None,
        },
        "enemies": [
            (8, 5,"demon", 45,1.3),(14, 8,"demon", 55,1.5),
            (6,14,"demon", 40,1.2),(20, 4,"demon", 65,1.6),
            (28,6,"skeleton",50,1.4),(32,12,"skeleton",60,1.5),
            (40,8,"demon", 50,1.3),(44,15,"skeleton",55,1.4),
            (36,20,"demon", 45,1.3),(42,22,"skeleton",50,1.4),
        ],
        "chests": [
            (10, 3,25,"Iron Sword",   "rare"),
            (22,16,20,"Health Potion","common"),
            (35, 5,15,"Iron Ore",     "common"),
            (44,10,30,"Leather Armor","common"),
        ],
        "npcs": [
            (5,2,"Elder Maren",[
                "Welcome, Pranav! Our village is overrun by demons.",
                "Kill ALL demons here and the forest path will open.",
                "Check your inventory with [I] — click items to equip.",
                "Press [Q] to use a potion. Good luck, warrior!",
            ]),
            (30,3,"Blacksmith Doran",[
                "Bring me Iron Ore and I can forge great weapons.",
                "Check your inventory — click an item to equip it!",
            ]),
        ],
    },
    "forest": {
        "tiles":  FOREST_TILES,
        "style":  "grass",
        "name":   "Darkwood Forest",
        "start":  (2, 26),
        "melody": FOREST_MELODY,
        "doors":  {(1,27):"village", (46,27):"volcano"},
        "quest":  {
            "id":    "forest_key",
            "title": "Find the Forest Key",
            "desc":  "Ranger: Find the Silver Key in the deep chest AND kill the mini-boss.",
            "goal":  "key_and_boss",
            "unlock_door": (46,27),
            "key_item": "Silver Key",
            "miniboss_idx": 0,
        },
        "enemies": [
            (5, 5,"demon",   60,1.5),(12, 7,"skeleton",70,1.6),
            (20, 5,"demon",   55,1.4),(28, 9,"skeleton",80,1.7),
            (35, 5,"demon",   65,1.5),(8, 13,"demon",   75,1.6),
            (25,13,"skeleton",85,1.8),(38, 3,"skeleton", 70,1.5),
            (44,10,"demon",   80,1.6),(40,20,"skeleton", 90,1.7),
            (15,20,"demon",   70,1.5),(30,20,"skeleton", 75,1.6),
        ],
        "miniboss": (23,11,"Forest Wraith",220,1.3),
        "chests": [
            (15, 4,35,"Fire Sword",  "epic"),
            (30,16,50,"Steel Armor", "rare"),
            (38,10,20,"Silver Key",  "rare"),
            (44, 3,25,"Iron Ore",    "common"),
        ],
        "npcs": [
            (20,10,"Lost Ranger",[
                "The Volcano lies east. But the path is locked!",
                "Find the Silver Key in the deep forest chest.",
                "AND defeat the Forest Wraith lurking near the lake.",
                "Only then will the volcano gate open.",
            ]),
        ],
    },
    "volcano": {
        "tiles":  VOLCANO_TILES,
        "style":  "lava",
        "name":   "Volcano of Ash",
        "start":  (2, 26),
        "melody": VOLCANO_MELODY,
        "doors":  {(1,27):"forest"},
        "quest":  {
            "id":    "slay_zareth",
            "title": "Slay Dragon Zareth",
            "desc":  "Defeat Dragon Zareth to save Emberveil!",
            "goal":  "slay_boss",
            "unlock_door": None,
            "key_item": None,
        },
        "enemies": [
            (5, 3,"demon",  100,1.8),(35, 3,"demon",  100,1.8),
            (5,15,"skeleton",110,1.9),(35,15,"skeleton",110,1.9),
            (10, 8,"demon",   90,1.7),(30, 8,"demon",   90,1.7),
            (44, 5,"skeleton",100,1.8),(44,20,"demon",  100,1.8),
            (8, 22,"skeleton",95,1.7),(38,22,"demon",   95,1.7),
        ],
        "boss": (24,11,"Dragon Zareth",600,1.1),
        "chests": [
            (8, 10,80,"Emberblade",  "legendary"),
            (38,10,60,"Dragon Scale","legendary"),
            (22, 5,40,"Mana Crystal","rare"),
        ],
        "npcs": [],
    },
}

ITEM_DB = {
    "Health Potion": {"type":"consumable","effect":"hp","value":40, "rarity":"common", "desc":"Restores 40 HP"},
    "Mana Crystal":  {"type":"consumable","effect":"mp","value":30, "rarity":"rare",   "desc":"Restores 30 MP"},
    "Iron Ore":      {"type":"material",                             "rarity":"common", "desc":"Crafting material"},
    "Silver Key":    {"type":"key",                                  "rarity":"rare",   "desc":"Opens the volcano path"},
    "Dragon Fang":   {"type":"material",                             "rarity":"epic",   "desc":"Rare drop from boss"},
    "Iron Sword":    {"type":"weapon","atk":10, "rarity":"rare",     "desc":"+10 Attack"},
    "Fire Sword":    {"type":"weapon","atk":22, "rarity":"epic",     "desc":"+22 Attack, fire dmg"},
    "Emberblade":    {"type":"weapon","atk":45, "rarity":"legendary","desc":"+45 Attack, Dragon slayer"},
    "Leather Armor": {"type":"armor", "def":8,  "rarity":"common",   "desc":"+8 Defense"},
    "Steel Armor":   {"type":"armor", "def":18, "rarity":"rare",     "desc":"+18 Defense"},
    "Dragon Scale":  {"type":"armor", "def":35, "rarity":"legendary","desc":"+35 Defense, Fire resist"},
}

# ═══════════════════════════════════════════
#  MAP STATE
# ═══════════════════════════════════════════
cur_map_key = "village"
raw_map     = MAP_DATA[cur_map_key]["tiles"]
MAP_ROWS    = len(raw_map)
MAP_COLS    = len(raw_map[0])

def load_map_tiles(key):
    global cur_map_key,raw_map,MAP_ROWS,MAP_COLS,cur_melody
    cur_map_key = key
    raw_map     = MAP_DATA[key]["tiles"]
    MAP_ROWS    = len(raw_map)
    MAP_COLS    = max(len(r) for r in raw_map)
    cur_melody  = MAP_DATA[key]["melody"]

def tile_char(c,r):
    c,r=int(c),int(r)
    if 0<=r<MAP_ROWS and 0<=c<MAP_COLS:
        row=raw_map[r]
        return row[c] if c<len(row) else '1'
    return '1'

def tile_int(c,r):
    ch=tile_char(c,r)
    if ch in ('D','B'): return 0
    try: return int(ch)
    except: return 1

def walkable(px,py,sz=20):
    h=sz//2
    for dx,dy in [(-h,-h),(h,-h),(-h,h),(h,h)]:
        if tile_int((px+dx)//TILE,(py+dy)//TILE) in (1,2):
            return False
    return True

# ═══════════════════════════════════════════
#  PARTICLES & FLOAT TEXT
# ═══════════════════════════════════════════
particles  = []
floattexts = []

class Particle:
    __slots__=['x','y','vx','vy','col','life','ml','sz']
    def __init__(self,x,y,col,vx,vy,life=28,sz=4):
        self.x,self.y=float(x),float(y)
        self.vx,self.vy=vx,vy
        self.col=col[:3]; self.life=self.ml=life; self.sz=sz
    def update(self):
        self.x+=self.vx; self.y+=self.vy
        self.vy+=0.1; self.vx*=0.91; self.life-=1
    def draw(self,surf,cx,cy):
        s=max(1,int(self.sz*self.life/self.ml))
        pygame.draw.circle(surf,self.col,(int(self.x-cx),int(self.y-cy)),s)

def burst(x,y,col,n=12,sz=4,sp=4):
    for _ in range(n):
        a=random.uniform(0,math.tau); sp2=random.uniform(1,sp)
        particles.append(Particle(x,y,col,math.cos(a)*sp2,math.sin(a)*sp2,life=32,sz=sz))

class FloatText:
    def __init__(self,x,y,text,col,sz=18):
        self.x,self.y=float(x),float(y)
        self.text=text; self.col=col; self.sz=sz
        self.life=65; self._f=F(sz)
    def update(self): self.y-=1.0; self.life-=1
    def draw(self,surf,cx,cy):
        img=self._f.render(self.text,True,self.col)
        img.set_alpha(max(0,int(255*self.life/65)))
        surf.blit(img,(int(self.x-cx)-img.get_width()//2,int(self.y-cy)))

def ft(x,y,text,col,sz=18): floattexts.append(FloatText(x,y,text,col,sz))

# ═══════════════════════════════════════════
#  SCREEN SHAKE
# ═══════════════════════════════════════════
shake_frames = 0
shake_mag    = 0

def shake(mag=6,frames=8):
    global shake_frames, shake_mag
    shake_frames=frames; shake_mag=mag

def get_shake_offset():
    if shake_frames>0:
        return (random.randint(-shake_mag,shake_mag),
                random.randint(-shake_mag,shake_mag))
    return (0,0)

# ═══════════════════════════════════════════
#  CHEST
# ═══════════════════════════════════════════
class Chest:
    def __init__(self,tx,ty,gold,item,rarity="common"):
        self.x=tx*TILE+TILE//2; self.y=ty*TILE+TILE//2
        self.gold=gold; self.item=item; self.rarity=rarity
        self.opened=False; self._g=0; self._gd=1
    def update(self):
        self._g+=self._gd*3
        if self._g>=60 or self._g<=0: self._gd*=-1
    def draw(self,surf,cx,cy):
        sx,sy=int(self.x-cx),int(self.y-cy)
        rc=RARITY_COL.get(self.rarity,WHITE)
        col=CHEST_O if self.opened else CHEST_C
        if not self.opened:
            g=pygame.Surface((56,56),pygame.SRCALPHA)
            pygame.draw.rect(g,(*rc,self._g),(0,0,56,56),border_radius=8)
            surf.blit(g,(sx-28,sy-28))
        pygame.draw.rect(surf,col,(sx-18,sy-13,36,26),border_radius=4)
        pygame.draw.rect(surf,BLACK,(sx-18,sy-13,36,26),2,border_radius=4)
        if not self.opened:
            pygame.draw.rect(surf,rc,(sx-5,sy-5,10,10),border_radius=3)

# ═══════════════════════════════════════════
#  DOOR
# ═══════════════════════════════════════════
class Door:
    def __init__(self,tx,ty,dest,locked=True):
        self.x=tx*TILE+TILE//2; self.y=ty*TILE+TILE//2
        self.dest=dest; self.locked=locked
        self._g=0; self._gd=1
    def update(self):
        self._g+=self._gd*2
        if self._g>=50 or self._g<=0: self._gd*=-1
    def draw(self,surf,cx,cy):
        sx,sy=int(self.x-cx),int(self.y-cy)
        col=LOCKED if self.locked else DOOR_C
        glowcol=RED if self.locked else YELLOW
        g=pygame.Surface((52,62),pygame.SRCALPHA)
        pygame.draw.rect(g,(*glowcol,self._g),(0,0,52,62),border_radius=6)
        surf.blit(g,(sx-26,sy-34))
        pygame.draw.rect(surf,col,(sx-20,sy-30,40,52),border_radius=5)
        pygame.draw.rect(surf,glowcol,(sx-20,sy-30,40,52),2,border_radius=5)
        pygame.draw.circle(surf,glowcol,(sx+12,sy-4),4)
        lbl=F12.render("LOCKED" if self.locked else self.dest.upper(),True,glowcol)
        surf.blit(lbl,(sx-lbl.get_width()//2,sy+26))

# ═══════════════════════════════════════════
#  NPC
# ═══════════════════════════════════════════
class NPC:
    def __init__(self,tx,ty,name,lines):
        self.x=tx*TILE+TILE//2; self.y=ty*TILE+TILE//2
        self.name=name; self.lines=lines
        self.talking=False; self.line_idx=0
        self._b=0.0; self._bd=1
    def update(self):
        self._b+=self._bd*0.05
        if abs(self._b)>3: self._bd*=-1
    def draw(self,surf,cx,cy):
        sx=int(self.x-cx); sy=int(self.y-cy+self._b)
        pygame.draw.ellipse(surf,BLACK,(sx-14,sy+16,28,10))
        pygame.draw.polygon(surf,NPC_C,[(sx,sy-22),(sx-14,sy+18),(sx+14,sy+18)])
        pygame.draw.polygon(surf,NPC_D,[(sx,sy-22),(sx-14,sy+18),(sx+14,sy+18)],2)
        pygame.draw.circle(surf,NPC_C,(sx,sy-26),11)
        pygame.draw.circle(surf,NPC_D,(sx,sy-26),11,2)
        pygame.draw.polygon(surf,NPC_D,[(sx,sy-46),(sx-10,sy-34),(sx+10,sy-34)])
        lbl=F12.render("[E]",True,YELLOW)
        surf.blit(lbl,(sx-lbl.get_width()//2,sy-62))

# ═══════════════════════════════════════════
#  ENEMY
# ═══════════════════════════════════════════
class Enemy:
    def __init__(self,tx,ty,kind="demon",hp=40,speed=1.4,is_miniboss=False,is_boss=False):
        self.x=float(tx*TILE+TILE//2); self.y=float(ty*TILE+TILE//2)
        self.kind=kind; self.hp=self.max_hp=hp; self.speed=speed
        self.is_miniboss=is_miniboss; self.is_boss=is_boss
        self.alive=True; self.death_timer=0
        self.state="patrol"; self.pt=(self.x,self.y); self.ptimer=0
        self.atk_cd=0; self.hurt_timer=0; self.angle=0.0
        self.atk_dmg=12 if is_boss else (10 if is_miniboss else 8)
        self.detect=360 if is_boss else (300 if is_miniboss else 260)
        self._b=0.0; self._bd=1

    def update(self,px,py):
        if not self.alive: self.death_timer+=1; return
        self._b+=self._bd*0.07
        if abs(self._b)>4: self._bd*=-1
        if self.hurt_timer>0: self.hurt_timer-=1
        if self.atk_cd>0: self.atk_cd-=1
        dx=px-self.x; dy=py-self.y; dist=math.hypot(dx,dy)
        if dist>0: self.angle=math.atan2(dy,dx)
        if dist<self.detect: self.state="chase"
        elif dist>self.detect+80: self.state="patrol"
        if self.state=="chase" and dist>1:
            nx=self.x+dx/dist*self.speed; ny=self.y+dy/dist*self.speed
            if walkable(nx,self.y,26): self.x=nx
            if walkable(self.x,ny,26): self.y=ny
        else:
            self.ptimer-=1
            if self.ptimer<=0:
                self.ptimer=random.randint(60,180)
                self.pt=(self.x+random.randint(-120,120),
                         self.y+random.randint(-120,120))
            tdx=self.pt[0]-self.x; tdy=self.pt[1]-self.y
            td=math.hypot(tdx,tdy)
            if td>4:
                nx=self.x+tdx/td*(self.speed*0.5)
                ny=self.y+tdy/td*(self.speed*0.5)
                if walkable(nx,self.y,26): self.x=nx
                if walkable(self.x,ny,26): self.y=ny

    def hurt(self,dmg):
        self.hp-=dmg; self.hurt_timer=14
        ft(self.x,self.y-32,f"-{dmg}",ORANGE,16)
        col=BOSS_C if self.is_boss else DEMON_C
        burst(self.x,self.y,col,10,4,3)
        play(SND_HIT)
        if self.hp<=0:
            self.alive=False
            burst(self.x,self.y,col,22,5,5)
            play(SND_DEATH)
            shake(5,6)

    def draw(self,surf,cx,cy):
        if not self.alive: return
        sx=int(self.x-cx); sy=int(self.y-cy+self._b)
        flash=self.hurt_timer>0 and self.hurt_timer%2==0
        if   self.is_boss:     self._draw_boss(surf,sx,sy,flash)
        elif self.is_miniboss: self._draw_miniboss(surf,sx,sy,flash)
        elif self.kind=="skeleton": self._draw_skel(surf,sx,sy,flash)
        else:                       self._draw_demon(surf,sx,sy,flash)
        bw=52 if self.is_boss else (44 if self.is_miniboss else 36)
        bx=sx-bw//2; by=sy-46 if self.is_boss else sy-42
        pygame.draw.rect(surf,HP_BG,(bx,by,bw,6),border_radius=2)
        fill=int(bw*max(0,self.hp)/self.max_hp)
        if fill>0:
            c=BOSS_C if self.is_boss else (PURPLE if self.is_miniboss else (195,35,35))
            pygame.draw.rect(surf,c,(bx,by,fill,6),border_radius=2)

    def _draw_demon(self,surf,sx,sy,flash):
        col=(255,160,160) if flash else DEMON_C
        pygame.draw.ellipse(surf,BLACK,(sx-16,sy+18,32,10))
        pygame.draw.circle(surf,col,(sx,sy),18)
        pygame.draw.circle(surf,DEMON_D,(sx,sy),18,2)
        ex=int(sx+math.cos(self.angle)*8); ey=int(sy+math.sin(self.angle)*8)
        pygame.draw.circle(surf,YELLOW,(ex-4,ey-3),4)
        pygame.draw.circle(surf,YELLOW,(ex+4,ey-3),4)
        pygame.draw.circle(surf,BLACK,(ex-4,ey-3),2)
        pygame.draw.circle(surf,BLACK,(ex+4,ey-3),2)
        pygame.draw.polygon(surf,DEMON_D,[(sx-10,sy-16),(sx-16,sy-30),(sx-4,sy-18)])
        pygame.draw.polygon(surf,DEMON_D,[(sx+10,sy-16),(sx+16,sy-30),(sx+4,sy-18)])

    def _draw_skel(self,surf,sx,sy,flash):
        col=(255,255,255) if flash else SKEL_C
        pygame.draw.ellipse(surf,BLACK,(sx-14,sy+18,28,9))
        for i in range(4):
            pygame.draw.line(surf,col,(sx-10,sy-4+i*6),(sx+10,sy-4+i*6),2)
        pygame.draw.circle(surf,col,(sx,sy-22),12)
        pygame.draw.circle(surf,SKEL_D,(sx,sy-22),12,2)
        pygame.draw.circle(surf,BLACK,(sx-4,sy-24),3)
        pygame.draw.circle(surf,BLACK,(sx+4,sy-24),3)
        pygame.draw.line(surf,SKEL_D,(sx-5,sy-16),(sx+5,sy-16),2)

    def _draw_miniboss(self,surf,sx,sy,flash):
        col=(200,100,255) if flash else PURPLE
        pygame.draw.ellipse(surf,BLACK,(sx-20,sy+22,40,12))
        pygame.draw.polygon(surf,(80,0,150),[(sx-22,sy-5),(sx-45,sy-20),(sx-30,sy+15)])
        pygame.draw.polygon(surf,(80,0,150),[(sx+22,sy-5),(sx+45,sy-20),(sx+30,sy+15)])
        pygame.draw.circle(surf,col,(sx,sy),22)
        pygame.draw.circle(surf,(100,0,160),(sx,sy),22,3)
        ex=int(sx+math.cos(self.angle)*9); ey=int(sy+math.sin(self.angle)*9)
        pygame.draw.circle(surf,YELLOW,(ex-5,ey-2),5)
        pygame.draw.circle(surf,YELLOW,(ex+5,ey-2),5)
        pygame.draw.circle(surf,BLACK,(ex-5,ey-2),2)
        pygame.draw.circle(surf,BLACK,(ex+5,ey-2),2)
        pygame.draw.polygon(surf,(60,0,120),[(sx-12,sy-20),(sx-18,sy-38),(sx-5,sy-22)])
        pygame.draw.polygon(surf,(60,0,120),[(sx+12,sy-20),(sx+18,sy-38),(sx+5,sy-22)])
        lbl=F12.render("WRAITH",True,PURPLE)
        surf.blit(lbl,(sx-lbl.get_width()//2,sy-50))

    def _draw_boss(self,surf,sx,sy,flash):
        col=(255,100,255) if flash else BOSS_C
        pygame.draw.ellipse(surf,BLACK,(sx-28,sy+28,56,16))
        pygame.draw.polygon(surf,(80,0,120),[(sx-26,sy),(sx-62,sy-32),(sx-40,sy+18)])
        pygame.draw.polygon(surf,(80,0,120),[(sx+26,sy),(sx+62,sy-32),(sx+40,sy+18)])
        pygame.draw.ellipse(surf,col,(sx-26,sy-22,52,50))
        pygame.draw.ellipse(surf,BOSS_D,(sx-26,sy-22,52,50),3)
        pygame.draw.circle(surf,col,(sx,sy-30),20)
        pygame.draw.circle(surf,BOSS_D,(sx,sy-30),20,3)
        ex=int(sx+math.cos(self.angle)*10); ey=int(sy-30+math.sin(self.angle)*10)
        pygame.draw.circle(surf,YELLOW,(ex-6,ey-2),6)
        pygame.draw.circle(surf,YELLOW,(ex+6,ey-2),6)
        pygame.draw.circle(surf,BLACK,(ex-6,ey-2),3)
        pygame.draw.circle(surf,BLACK,(ex+6,ey-2),3)
        pygame.draw.polygon(surf,BOSS_D,[(sx-12,sy-46),(sx-22,sy-70),(sx-4,sy-48)])
        pygame.draw.polygon(surf,BOSS_D,[(sx+12,sy-46),(sx+22,sy-70),(sx+4,sy-48)])
        lbl=F14.render("ZARETH",True,GOLD)
        surf.blit(lbl,(sx-lbl.get_width()//2,sy-92))

# ═══════════════════════════════════════════
#  PLAYER
# ═══════════════════════════════════════════
class Player:
    def __init__(self):
        self.x=float(3*TILE+TILE//2); self.y=float(3*TILE+TILE//2)
        self.spd=3.2
        self.hp=self.max_hp=120
        self.xp=0; self.xp_next=50; self.level=1
        self.base_atk=20; self.base_def=0
        self.gold=0
        self.inventory=[]
        self.weapon=None
        self.armor=None
        self.potions=3
        self.atk_timer=0; self.atk_cd=20
        self.atk_range=55
        self.invinc=0; self.hurt_timer=0
        self.dir=0.0
        self._b=0.0; self._bd=1

    @property
    def atk(self):
        w=self.weapon
        return self.base_atk+(ITEM_DB[w].get("atk",0) if w and w in ITEM_DB else 0)

    @property
    def defense(self):
        a=self.armor
        return self.base_def+(ITEM_DB[a].get("def",0) if a and a in ITEM_DB else 0)

    def move(self,keys):
        dx=dy=0
        if keys[pygame.K_w] or keys[pygame.K_UP]:   dy-=1
        if keys[pygame.K_s] or keys[pygame.K_DOWN]:  dy+=1
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:  dx-=1
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]: dx+=1
        if dx or dy:
            l=math.hypot(dx,dy)
            self.dir=math.atan2(dy/l,dx/l)
            nx=self.x+dx/l*self.spd; ny=self.y+dy/l*self.spd
            if walkable(nx,self.y,22): self.x=nx
            if walkable(self.x,ny,22): self.y=ny
        self.x=max(TILE,min(MAP_COLS*TILE-TILE,self.x))
        self.y=max(TILE,min(MAP_ROWS*TILE-TILE,self.y))
        if dx or dy:
            self._b+=self._bd*0.15
            if abs(self._b)>4: self._bd*=-1
        else: self._b*=0.8

    def tick(self,enemies):
        global shake_frames
        if self.atk_timer>0: self.atk_timer-=1
        if self.invinc>0: self.invinc-=1
        if self.hurt_timer>0: self.hurt_timer-=1
        if shake_frames>0: shake_frames-=1
        if self.invinc==0:
            for e in enemies:
                if e.alive and math.hypot(e.x-self.x,e.y-self.y)<34 and e.atk_cd==0:
                    dmg=max(1,e.atk_dmg-self.defense//2)
                    self.hp=max(0,self.hp-dmg)
                    self.invinc=45; self.hurt_timer=18; e.atk_cd=55
                    ft(self.x,self.y-42,f"-{dmg}",RED)
                    burst(self.x,self.y,PLAYER_C,8,3,3)
                    shake(4,5)

    def sword(self,enemies):
        if self.atk_timer>0: return
        self.atk_timer=self.atk_cd
        play(SND_SWORD)
        ax=self.x+math.cos(self.dir)*self.atk_range
        ay=self.y+math.sin(self.dir)*self.atk_range
        for e in enemies:
            if e.alive and math.hypot(e.x-ax,e.y-ay)<52:
                e.hurt(self.atk)
                if not e.alive:
                    xp=15+self.level*3+(40 if e.is_boss else (25 if e.is_miniboss else 0))
                    gld=random.randint(5,15)+(80 if e.is_boss else (30 if e.is_miniboss else 0))
                    self.xp+=xp; self.gold+=gld
                    ft(e.x,e.y-50,f"+{xp}XP",XP_C,15)
                    ft(e.x+20,e.y-30,f"+{gld}g",YELLOW,14)
                    if random.random()<0.4:
                        drop=random.choice(["Iron Ore","Dragon Fang","Health Potion"])
                        self.inventory.append(drop)
                        ft(e.x,e.y-70,f"{drop}!",WHITE,13)
                    self._levelup()
        burst(ax,ay,SWORD_C,6,3,2)

    def _levelup(self):
        while self.xp>=self.xp_next:
            self.xp-=self.xp_next; self.level+=1
            self.xp_next=int(self.xp_next*1.4)
            self.max_hp+=20; self.hp=min(self.hp+30,self.max_hp)
            self.base_atk+=4
            ft(self.x,self.y-80,f"LEVEL UP! Lv.{self.level}",YELLOW,22)
            play(SND_LEVEL)
            burst(self.x,self.y,YELLOW,20,5,5)

    def potion(self):
        if self.potions>0 and self.hp<self.max_hp:
            h=min(40,self.max_hp-self.hp)
            self.hp+=h; self.potions-=1
            ft(self.x,self.y-50,f"+{h}HP",HP_C)

    def use_item(self,name):
        if name not in self.inventory: return
        if name not in ITEM_DB: return
        item=ITEM_DB[name]
        t=item["type"]
        if t=="consumable":
            if item["effect"]=="hp":
                self.hp=min(self.max_hp,self.hp+item["value"])
                ft(self.x,self.y-50,f"+{item['value']}HP",HP_C)
            elif item["effect"]=="mp":
                ft(self.x,self.y-50,f"+{item['value']}MP — No MP system for Warrior",GREY,13)
            self.inventory.remove(name)
        elif t=="weapon":
            if self.weapon: self.inventory.append(self.weapon)
            self.weapon=name; self.inventory.remove(name)
            ft(self.x,self.y-50,f"Equipped {name}",YELLOW)
        elif t=="armor":
            if self.armor: self.inventory.append(self.armor)
            self.armor=name; self.inventory.remove(name)
            ft(self.x,self.y-50,f"Equipped {name}",YELLOW)
        elif t in ("material","key"):
            ft(self.x,self.y-50,f"{name}: kept in inventory",GREY,13)

    def to_dict(self):
        return {"x":self.x,"y":self.y,"hp":self.hp,"max_hp":self.max_hp,
                "xp":self.xp,"xp_next":self.xp_next,"level":self.level,
                "base_atk":self.base_atk,"base_def":self.base_def,
                "gold":self.gold,"inventory":self.inventory,
                "weapon":self.weapon,"armor":self.armor,"potions":self.potions}

    def from_dict(self,d):
        self.x=d["x"]; self.y=d["y"]; self.hp=d["hp"]; self.max_hp=d["max_hp"]
        self.xp=d["xp"]; self.xp_next=d["xp_next"]; self.level=d["level"]
        self.base_atk=d["base_atk"]; self.base_def=d["base_def"]
        self.gold=d["gold"]; self.inventory=d["inventory"]
        self.weapon=d["weapon"]; self.armor=d["armor"]; self.potions=d["potions"]

    def draw(self,surf,cx,cy):
        sx=int(self.x-cx); sy=int(self.y-cy+self._b)
        flash=self.hurt_timer>0 and self.hurt_timer%3==0
        col=(255,255,255) if flash else PLAYER_C
        pygame.draw.ellipse(surf,BLACK,(sx-14,sy+18,28,9))
        cdx=-math.cos(self.dir)*10; cdy=-math.sin(self.dir)*10
        pygame.draw.polygon(surf,(55,15,15),
            [(sx+int(cdx)-10,sy+int(cdy)),(sx+int(cdx)+10,sy+int(cdy)),
             (sx-int(cdx*0.5)+8,sy-int(cdy*0.5)+20),
             (sx-int(cdx*0.5)-8,sy-int(cdy*0.5)+20)])
        pygame.draw.circle(surf,col,(sx,sy),16)
        pygame.draw.circle(surf,PLAYER_D,(sx,sy),16,2)
        if self.armor:
            pygame.draw.circle(surf,(60,60,110),(sx,sy),14,3)
        pygame.draw.arc(surf,PLAYER_D,(sx-12,sy-12,24,20),-0.4,0.4,3)
        prog=self.atk_timer/self.atk_cd if self.atk_timer>0 else 0
        sa=self.dir+math.pi*0.4*prog
        s1=(int(sx+math.cos(sa)*22),int(sy+math.sin(sa)*22))
        s2=(int(sx+math.cos(sa)*54),int(sy+math.sin(sa)*54))
        pygame.draw.line(surf,SWORD_C,s1,s2,4)
        pygame.draw.circle(surf,WHITE,s2,3)
        if self.atk_timer>0:
            ax=int(sx+math.cos(self.dir)*self.atk_range)
            ay=int(sy+math.sin(self.dir)*self.atk_range)
            gs=pygame.Surface((80,80),pygame.SRCALPHA)
            a=int(90*self.atk_timer/self.atk_cd)
            pygame.draw.circle(gs,(*SWORD_C,a),(40,40),28)
            surf.blit(gs,(ax-40,ay-40))

# ═══════════════════════════════════════════
#  MAP RENDERER
# ═══════════════════════════════════════════
_wanim=0.0
def draw_map(surf,cx,cy,W,H):
    global _wanim; _wanim+=0.04
    style=MAP_DATA[cur_map_key]["style"]
    sc=max(0,int(cx)//TILE); ec=min(MAP_COLS,sc+W//TILE+2)
    sr=max(0,int(cy)//TILE); er=min(MAP_ROWS,sr+H//TILE+2)
    for r in range(sr,er):
        for c in range(sc,ec):
            t=tile_int(c,r)
            sx=c*TILE-int(cx); sy=r*TILE-int(cy)
            rect=(sx,sy,TILE,TILE)
            if style=="lava":
                if t==0:   pygame.draw.rect(surf,DARK1 if (r+c)%2==0 else DARK2,rect)
                elif t==1: pygame.draw.rect(surf,(55,30,30),rect); pygame.draw.rect(surf,(70,40,40),(sx,sy,TILE,TILE//4))
                elif t==2:
                    w=math.sin(_wanim+c*0.5+r*0.3)
                    pygame.draw.rect(surf,LAVA1 if w>0 else LAVA2,rect)
                    pygame.draw.line(surf,(240,120,30),(sx+4,sy+TILE//2+int(w*3)),(sx+TILE-4,sy+TILE//2+int(w*3)),2)
                elif t==3: pygame.draw.rect(surf,(100,60,20),rect)
            else:
                if t==0:   pygame.draw.rect(surf,GRASS1 if (r+c)%2==0 else GRASS2,rect)
                elif t==1: pygame.draw.rect(surf,WALL_C,rect); pygame.draw.rect(surf,WALLT,(sx,sy,TILE,TILE//5)); pygame.draw.rect(surf,(38,38,55),rect,1)
                elif t==2:
                    w=math.sin(_wanim+c*0.5+r*0.3)
                    pygame.draw.rect(surf,WATER1 if w>0 else WATER2,rect)
                    pygame.draw.line(surf,(38,95,175),(sx+4,sy+TILE//2+int(w*3)),(sx+TILE-4,sy+TILE//2+int(w*3)),2)
                elif t==3: pygame.draw.rect(surf,PATH_C,rect)

# ═══════════════════════════════════════════
#  HUD
# ═══════════════════════════════════════════
def draw_hud(surf,player,quest_status,W,H):
    panel=pygame.Surface((300,155),pygame.SRCALPHA)
    panel.fill((8,8,20,190))
    pygame.draw.rect(panel,(55,55,100),(0,0,300,155),1,border_radius=8)
    surf.blit(panel,(14,14))
    surf.blit(F18.render(f"Pranav  Lv.{player.level}",True,WHITE),(26,20))
    surf.blit(F12.render(MAP_DATA[cur_map_key]["name"],True,GREY),(26,42))
    def bar(y,label,val,mx,col,bg):
        surf.blit(F14.render(label,True,col),(26,y))
        pygame.draw.rect(surf,bg,(58,y+2,188,12),border_radius=4)
        f=int(188*max(0,val)/max(1,mx))
        if f>0: pygame.draw.rect(surf,col,(58,y+2,f,12),border_radius=4)
        surf.blit(F12.render(f"{val}/{mx}",True,WHITE),(252,y))
    bar(58,"HP",player.hp,player.max_hp,HP_C,HP_BG)
    bar(76,"XP",player.xp,player.xp_next,XP_C,XP_BG)
    pc=GREEN if player.potions>0 else RED
    surf.blit(F14.render(f"Gold:{player.gold}g",True,YELLOW),(26,96))
    surf.blit(F14.render(f"Pot:{player.potions}[Q]",True,pc),(145,96))
    surf.blit(F14.render(f"ATK:{player.atk}  DEF:{player.defense}",True,WHITE),(26,114))
    # Quest
    if quest_status:
        surf.blit(F13.render(f"Quest: {quest_status}",True,GOLD),(26,134))
    hints=["WASD Move","SPACE Attack","E Interact","I Inventory","F5 Save","F9 Load","F11 Full"]
    for i,h in enumerate(hints):
        surf.blit(F12.render(h,True,(65,65,95)),(W-120,H-22-(len(hints)-i)*16))

def draw_dialogue(surf,npc,W,H):
    if not npc or not npc.talking: return
    idx=npc.line_idx%len(npc.lines)
    box=pygame.Surface((W-80,105),pygame.SRCALPHA)
    box.fill((8,8,26,235)); pygame.draw.rect(box,(95,75,195),(0,0,W-80,105),2,border_radius=8)
    surf.blit(box,(40,H-125))
    surf.blit(F18.render(npc.name,True,NPC_C),(58,H-120))
    surf.blit(F16.render(npc.lines[idx],True,WHITE),(58,H-96))
    surf.blit(F12.render(f"[E] Next ({idx+1}/{len(npc.lines)})  [ESC] Close",True,(90,90,130)),(W-260,H-28))

def draw_boss_bar(surf,boss,W,H):
    if not boss or not boss.alive: return
    bw=500; bx=(W-bw)//2; by=H-52
    pygame.draw.rect(surf,(20,5,30),(bx-2,by-2,bw+4,26),border_radius=8)
    pygame.draw.rect(surf,HP_BG,(bx,by,bw,22),border_radius=6)
    f=int(bw*max(0,boss.hp)/boss.max_hp)
    if f>0: pygame.draw.rect(surf,BOSS_C,(bx,by,f,22),border_radius=6)
    lbl=F14.render(f"Dragon Zareth  {boss.hp}/{boss.max_hp}",True,WHITE)
    surf.blit(lbl,(bx+bw//2-lbl.get_width()//2,by+3))

def draw_miniboss_bar(surf,mb,W,H):
    if not mb or not mb.alive: return
    bw=360; bx=(W-bw)//2; by=H-52
    pygame.draw.rect(surf,(10,0,20),(bx-2,by-2,bw+4,26),border_radius=8)
    pygame.draw.rect(surf,HP_BG,(bx,by,bw,22),border_radius=6)
    f=int(bw*max(0,mb.hp)/mb.max_hp)
    if f>0: pygame.draw.rect(surf,PURPLE,(bx,by,f,22),border_radius=6)
    lbl=F14.render(f"Forest Wraith  {mb.hp}/{mb.max_hp}",True,WHITE)
    surf.blit(lbl,(bx+bw//2-lbl.get_width()//2,by+3))

# ═══════════════════════════════════════════
#  INVENTORY  (mouse-click UI)
# ═══════════════════════════════════════════
INV_COLS=6; INV_SZ=72; INV_GAP=8

def inv_slot_rect(i, px, py):
    col_=i%INV_COLS; row_=i//INV_COLS
    sx=px+16+col_*(INV_SZ+INV_GAP)
    sy=py+130+row_*(INV_SZ+INV_GAP)
    return pygame.Rect(sx,sy,INV_SZ,INV_SZ)

def draw_inventory(surf,player,hover_idx,W,H):
    ov=pygame.Surface((W,H),pygame.SRCALPHA); ov.fill((0,0,0,175)); surf.blit(ov,(0,0))
    pw,ph=740,520; px=(W-pw)//2; py=(H-ph)//2
    bg=pygame.Surface((pw,ph),pygame.SRCALPHA)
    bg.fill((8,8,22,248)); pygame.draw.rect(bg,(70,70,130),(0,0,pw,ph),2,border_radius=10)
    surf.blit(bg,(px,py))
    surf.blit(F24.render("INVENTORY",True,WHITE),(px+pw//2-70,py+12))
    surf.blit(F13.render("[I] or [ESC] to close  |  Click item to use/equip",True,GREY),(px+14,py+44))
    wc=RARITY_COL.get((ITEM_DB[player.weapon].get("rarity","") if player.weapon and player.weapon in ITEM_DB else ""),GREY)
    ac=RARITY_COL.get((ITEM_DB[player.armor].get("rarity","")  if player.armor  and player.armor  in ITEM_DB else ""),GREY)
    surf.blit(F14.render(f"Weapon: {player.weapon or 'None'}",True,wc),(px+14,py+66))
    surf.blit(F14.render(f"Armor:  {player.armor  or 'None'}",True,ac),(px+14,py+86))
    surf.blit(F14.render(f"ATK:{player.atk}  DEF:{player.defense}  Potions:{player.potions}",True,WHITE),(px+14,py+106))

    for i,name in enumerate(player.inventory[:24]):
        r=inv_slot_rect(i,px,py)
        item=ITEM_DB.get(name,{}) if isinstance(ITEM_DB.get(name),dict) else {}
        rc=RARITY_COL.get(item.get("rarity","common"),WHITE)
        hovered=i==hover_idx
        bg2=(80,80,150) if hovered else (28,28,48)
        pygame.draw.rect(surf,bg2,r,border_radius=6)
        pygame.draw.rect(surf,rc,r,2,border_radius=6)
        # Item name wrapped
        words=name.split(); lines=[]
        cur=""; 
        for w in words:
            if len(cur+" "+w)>8 and cur: lines.append(cur); cur=w
            else: cur=(cur+" "+w).strip()
        if cur: lines.append(cur)
        for li,ln in enumerate(lines[:2]):
            lbl=F12.render(ln,True,rc)
            surf.blit(lbl,(r.x+INV_SZ//2-lbl.get_width()//2,r.y+10+li*16))
        if hovered:
            desc=item.get("desc","")
            surf.blit(F14.render(f"{name}: {desc}",True,WHITE),(px+14,py+ph-56))
            surf.blit(F13.render("Click to use / equip",True,YELLOW),(px+14,py+ph-36))

    if len(player.inventory)==0:
        surf.blit(F18.render("Inventory is empty",True,GREY),(px+pw//2-100,py+200))

def get_inv_hover(player,mouse_pos,W,H):
    pw,ph=740,520; px=(W-pw)//2; py=(H-ph)//2
    for i in range(min(len(player.inventory),24)):
        r=inv_slot_rect(i,px,py)
        if r.collidepoint(mouse_pos): return i
    return -1

# ═══════════════════════════════════════════
#  OVERLAY SCREENS
# ═══════════════════════════════════════════
def draw_overlay(surf,title,sub,W,H,tc,sc=None):
    if sc is None: sc=GREY
    ov=pygame.Surface((W,H),pygame.SRCALPHA); ov.fill((0,0,0,200)); surf.blit(ov,(0,0))
    t=F48.render(title,True,tc); surf.blit(t,(W//2-t.get_width()//2,H//2-60))
    s=F22.render(sub,True,sc);   surf.blit(s,(W//2-s.get_width()//2,H//2+20))

# ═══════════════════════════════════════════
#  SAVE / LOAD
# ═══════════════════════════════════════════
def save_game(player,map_key,quest_states):
    data={"map":map_key,"player":player.to_dict(),"quests":quest_states}
    with open(SAVE_FILE,"w") as f: json.dump(data,f,indent=2)
    ft(player.x,player.y-80,"Game Saved!",GREEN,18)

def load_game(player,float_texts_ref):
    if not os.path.exists(SAVE_FILE): 
        ft(player.x,player.y-80,"No save found!",RED,18)
        return None,None
    with open(SAVE_FILE) as f: data=json.load(f)
    player.from_dict(data["player"])
    ft(player.x,player.y-80,"Game Loaded!",GREEN,18)
    return data["map"], data.get("quests",{})

# ═══════════════════════════════════════════
#  LEVEL LOADER
# ═══════════════════════════════════════════
def load_level(key,player,quest_states):
    load_map_tiles(key)
    md=MAP_DATA[key]
    sx,sy=md["start"]
    player.x=float(sx*TILE+TILE//2); player.y=float(sy*TILE+TILE//2)

    enemies=[]
    for tx,ty,kind,hp,spd in md.get("enemies",[]):
        enemies.append(Enemy(tx,ty,kind,hp,spd))

    miniboss=None
    if "miniboss" in md:
        tx,ty,name,hp,spd=md["miniboss"]
        miniboss=Enemy(tx,ty,"demon",hp,spd,is_miniboss=True)

    boss=None
    if "boss" in md:
        tx,ty,name,hp,spd=md["boss"]
        boss=Enemy(tx,ty,"demon",hp,spd,is_boss=True)

    chests=[Chest(tx,ty,g,item,rar) for tx,ty,g,item,rar in md.get("chests",[])]
    npcs=[NPC(tx,ty,nm,lines) for tx,ty,nm,lines in md.get("npcs",[])]

    # Doors — locked based on quest state
    doors=[]
    quest=md.get("quest",{})
    for (tc,tr),dest in md.get("doors",{}).items():
        # Back-doors (going back) are always unlocked
        is_progress_door=(dest not in ["village"] if key=="forest" else
                          dest not in ["forest"]  if key=="volcano" else False)
        locked=is_progress_door and not quest_states.get(quest.get("id",""),False)
        doors.append(Door(tc,tr,dest,locked=locked))

    particles.clear(); floattexts.clear()
    return enemies,miniboss,boss,chests,npcs,doors

# ═══════════════════════════════════════════
#  QUEST CHECKER
# ═══════════════════════════════════════════
def check_quest(key,enemies,miniboss,boss,player,quest_states,doors):
    md=MAP_DATA[key]; quest=md.get("quest",{})
    qid=quest.get("id",""); goal=quest.get("goal","")
    if quest_states.get(qid,False): return "Done!"

    if goal=="kill_all":
        alive=[e for e in enemies if e.alive]
        if not alive:
            quest_states[qid]=True
            _unlock_doors(quest,doors)
            ft(player.x,player.y-100,"Quest Complete! Path unlocked!",GOLD,20)
            burst(player.x,player.y,GOLD,20,5,5)
            return "Done!"
        return f"Kill all enemies ({len(alive)} left)"

    elif goal=="key_and_boss":
        has_key="Silver Key" in player.inventory
        boss_dead=miniboss is not None and not miniboss.alive
        if has_key and boss_dead:
            quest_states[qid]=True
            _unlock_doors(quest,doors)
            ft(player.x,player.y-100,"Quest Complete! Volcano unlocked!",GOLD,20)
            burst(player.x,player.y,GOLD,20,5,5)
            return "Done!"
        parts=[]
        if not has_key: parts.append("Find Silver Key")
        if not boss_dead: parts.append("Defeat Forest Wraith")
        return " + ".join(parts)

    elif goal=="slay_boss":
        if boss and not boss.alive:
            quest_states[qid]=True
            return "VICTORY!"
        return "Slay Dragon Zareth"

    return ""

def _unlock_doors(quest,doors):
    uid=quest.get("unlock_door")
    if uid:
        for d in doors:
            dtc=int(d.x//TILE); dtr=int(d.y//TILE)
            if (dtc,dtr)==uid: d.locked=False
    else:
        for d in doors:
            if d.locked: d.locked=False

# ═══════════════════════════════════════════
#  MAIN
# ═══════════════════════════════════════════
def main():
    global screen, fullscreen, cur_melody

    player=Player()
    quest_states={}
    enemies,miniboss,boss,chests,npcs,doors=load_level("village",player,quest_states)

    state="play"
    active_npc=None
    inv_hover=-1

    while True:
        W,H=screen.get_size()
        clock.tick(FPS)

        # ── EVENTS ──────────────────────────
        for ev in pygame.event.get():
            if ev.type==pygame.QUIT: pygame.quit(); sys.exit()
            if ev.type==pygame.VIDEORESIZE and not fullscreen:
                screen=pygame.display.set_mode((ev.w,ev.h),pygame.RESIZABLE)

            # Mouse hover for inventory
            if ev.type==pygame.MOUSEMOTION and state=="inventory":
                inv_hover=get_inv_hover(player,ev.pos,W,H)

            # Mouse click for inventory
            if ev.type==pygame.MOUSEBUTTONDOWN and ev.button==1 and state=="inventory":
                idx=get_inv_hover(player,ev.pos,W,H)
                if idx>=0 and idx<len(player.inventory):
                    name=player.inventory[idx]
                    player.use_item(name)
                    inv_hover=-1

            if ev.type==pygame.KEYDOWN:
                k=ev.key

                # Fullscreen
                if k==pygame.K_F11:
                    fullscreen=not fullscreen
                    flags=pygame.FULLSCREEN if fullscreen else pygame.RESIZABLE
                    sz=(0,0) if fullscreen else (WIN_W,WIN_H)
                    screen=pygame.display.set_mode(sz,flags)

                # ── PLAY ──
                if state=="play":
                    if k==pygame.K_ESCAPE:
                        if active_npc and active_npc.talking:
                            active_npc.talking=False; active_npc=None
                        else: state="pause"
                    elif k==pygame.K_i:
                        state="inventory"; inv_hover=-1
                    elif k==pygame.K_SPACE:
                        if not (active_npc and active_npc.talking):
                            all_e = list(enemies)
                            if miniboss and miniboss.alive: all_e.append(miniboss)
                            if boss and boss.alive: all_e.append(boss)
                            player.sword(all_e)
                    elif k==pygame.K_q: player.potion()
                    elif k==pygame.K_F5: save_game(player,cur_map_key,quest_states)
                    elif k==pygame.K_F9:
                        mkey,qs=load_game(player,floattexts)
                        if mkey:
                            if qs: quest_states=qs
                            enemies,miniboss,boss,chests,npcs,doors=load_level(mkey,player,quest_states)
                            active_npc=None
                    elif k==pygame.K_e:
                        # NPC
                        for npc in npcs:
                            if math.hypot(npc.x-player.x,npc.y-player.y)<65:
                                if npc.talking:
                                    npc.line_idx+=1
                                    if npc.line_idx>=len(npc.lines):
                                        npc.talking=False; active_npc=None
                                else:
                                    npc.talking=True; active_npc=npc; break
                        # Chest
                        for ch in chests:
                            if not ch.opened and math.hypot(ch.x-player.x,ch.y-player.y)<58:
                                ch.opened=True; player.gold+=ch.gold
                                if ch.item=="Health Potion": player.potions+=1
                                else: player.inventory.append(ch.item)
                                ft(ch.x,ch.y-32,f"+{ch.gold}g  {ch.item}",RARITY_COL.get(ch.rarity,WHITE),15)
                                burst(ch.x,ch.y,YELLOW,14,4,4)
                                play(SND_CHEST)
                        # Door
                        for d in doors:
                            if math.hypot(d.x-player.x,d.y-player.y)<64:
                                if d.locked:
                                    ft(player.x,player.y-60,"Door locked! Complete the quest first.",RED,14)
                                else:
                                    play(SND_DOOR)
                                    enemies,miniboss,boss,chests,npcs,doors=load_level(d.dest,player,quest_states)
                                    active_npc=None
                                    ft(player.x,player.y-60,f"Entering {MAP_DATA[d.dest]['name']}...",YELLOW,16)
                                break

                # ── PAUSE ──
                elif state=="pause":
                    if k==pygame.K_ESCAPE: state="play"
                    elif k==pygame.K_q: pygame.quit(); sys.exit()
                    elif k==pygame.K_F5: save_game(player,cur_map_key,quest_states)

                # ── INVENTORY ──
                elif state=="inventory":
                    if k in (pygame.K_ESCAPE,pygame.K_i): state="play"

                # ── GAMEOVER ──
                elif state=="gameover":
                    if k==pygame.K_r:
                        player=Player(); quest_states={}
                        enemies,miniboss,boss,chests,npcs,doors=load_level("village",player,quest_states)
                        active_npc=None; state="play"
                    elif k==pygame.K_ESCAPE: pygame.quit(); sys.exit()

                # ── VICTORY ──
                elif state=="victory":
                    if k==pygame.K_ESCAPE: pygame.quit(); sys.exit()

        # ── UPDATE ──────────────────────────
        if state=="play":
            if not (active_npc and active_npc.talking):
                keys=pygame.key.get_pressed()
                player.move(keys)

            all_e = list(enemies)
            if miniboss and miniboss.alive: all_e.append(miniboss)
            if boss and boss.alive: all_e.append(boss)
            player.tick(all_e)
            for e in all_e: e.update(player.x,player.y)
            for ch in chests: ch.update()
            for d in doors: d.update()
            for npc in npcs: npc.update()
            for p in particles[:]:
                p.update()
                if p.life<=0: particles.remove(p)
            for ftt in floattexts[:]:
                ftt.update()
                if ftt.life<=0: floattexts.remove(ftt)

            # Lava sparks
            if MAP_DATA[cur_map_key]["style"]=="lava" and random.random()<0.25:
                rx=random.randint(0,MAP_COLS*TILE); ry=random.randint(0,MAP_ROWS*TILE)
                if tile_int(rx//TILE,ry//TILE)==2:
                    particles.append(Particle(rx,ry,LAVA1,random.uniform(-1,1),random.uniform(-3,-1),life=35,sz=3))

            # Check quest
            quest_status=check_quest(cur_map_key,enemies,miniboss,boss,player,quest_states,doors)

            if player.hp<=0: state="gameover"
            if boss and not boss.alive and cur_map_key=="volcano": state="victory"

            tick_music()

        # ── CAMERA ──────────────────────────
        cx=player.x-W//2; cy=player.y-H//2
        cx=max(0,min(MAP_COLS*TILE-W,cx))
        cy=max(0,min(MAP_ROWS*TILE-H,cy))
        ox,oy=get_shake_offset()
        cx+=ox; cy+=oy

        # ── DRAW ────────────────────────────
        screen.fill(BG)
        draw_map(screen,cx,cy,W,H)
        for d  in doors:  d.draw(screen,cx,cy)
        for ch in chests: ch.draw(screen,cx,cy)
        for npc in npcs:  npc.draw(screen,cx,cy)
        all_e = list(enemies)
        if miniboss and miniboss.alive: all_e.append(miniboss)
        if boss and boss.alive: all_e.append(boss)
        for e in all_e: e.draw(screen,cx,cy)
        for p  in particles:  p.draw(screen,cx,cy)
        player.draw(screen,cx,cy)
        for ftt in floattexts: ftt.draw(screen,cx,cy)

        quest_status=check_quest(cur_map_key,enemies,miniboss,boss,player,quest_states,doors)
        draw_hud(screen,player,quest_status,W,H)

        if active_npc and active_npc.talking:
            draw_dialogue(screen,active_npc,W,H)
        if boss and boss.alive and cur_map_key=="volcano":
            draw_boss_bar(screen,boss,W,H)
        if miniboss and miniboss.alive and cur_map_key=="forest":
            draw_miniboss_bar(screen,miniboss,W,H)

        if   state=="inventory": draw_inventory(screen,player,inv_hover,W,H)
        elif state=="pause":
            draw_overlay(screen,"PAUSED","ESC Resume  |  Q Quit  |  F5 Save",W,H,WHITE)
        elif state=="gameover":
            draw_overlay(screen,"GAME OVER","R Restart  |  ESC Quit",W,H,RED)
        elif state=="victory":
            draw_overlay(screen,"VICTORY!","Pranav saved Emberveil!  ESC Quit",W,H,GOLD)

        mn=F14.render(MAP_DATA[cur_map_key]["name"],True,(40,40,65))
        screen.blit(mn,(W//2-mn.get_width()//2,6))

        pygame.display.flip()

if __name__=="__main__":
    main()