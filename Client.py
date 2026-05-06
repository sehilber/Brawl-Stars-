import socket
import threading
import json
import pygame
import math
import os
 
SERVER_IP = "192.168.0.100"
PORT = 5555
 
client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
 
pygame.init()
pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
 
# ─── FULLSCREEN SETUP ─────────────────────────────────────────────────────────
info = pygame.display.Info()
SCREEN_W = info.current_w
SCREEN_H = info.current_h
screen = pygame.display.set_mode((SCREEN_W, SCREEN_H), pygame.FULLSCREEN)
pygame.display.set_caption("Brawl Game")
clock = pygame.time.Clock()
 
# Map dimensions (must match server)
MAP_W = 3840
MAP_H = 2160
 
# Camera
cam_x = 0.0
cam_y = 0.0
 
def world_to_screen(x, y):
    return int(x - cam_x), int(y - cam_y)
 
def screen_to_world(sx, sy):
    return sx + cam_x, sy + cam_y
 
def update_camera(px, py):
    global cam_x, cam_y
    cam_x = px - SCREEN_W / 2
    cam_y = py - SCREEN_H / 2
    cam_x = max(0, min(cam_x, MAP_W - SCREEN_W))
    cam_y = max(0, min(cam_y, MAP_H - SCREEN_H))
 
# ─── FONTS ────────────────────────────────────────────────────────────────────
font_big   = pygame.font.SysFont("consolas", 48, bold=True)
font_med   = pygame.font.SysFont("consolas", 26, bold=True)
font_small = pygame.font.SysFont("consolas", 18)
font_tiny  = pygame.font.SysFont("consolas", 14)
 
# ─── COLORS ───────────────────────────────────────────────────────────────────
C_BG      = (14,  16,  22)
C_PANEL   = (22,  26,  42)
C_ACCENT  = (255, 200,  40)
C_BLUE    = (70,  150, 255)
C_GREEN   = (70,  210, 110)
C_RED     = (255,  70,  70)
C_GRAY    = (110, 115, 135)
C_WHITE   = (235, 238, 255)
C_DARK    = ( 8,   9,  15)
C_GRASS   = ( 34,  85,  34)
C_GRASS2  = ( 45, 110,  45)
 
# ─── SOUND SYSTEM ─────────────────────────────────────────────────────────────
SOUND_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sounds")
 
sounds = {}
 
def load_sound(name, filename, volume=1.0):
    path = os.path.join(SOUND_DIR, filename)

    if not os.path.exists(path):
        print(f"  ⚠️ Missing sound file: {path}")
        sounds[name] = None
        return

    try:
        snd = pygame.mixer.Sound(path)
        snd.set_volume(volume)
        sounds[name] = snd
        print(f"  ✅ Loaded sound: {name}")
    except Exception as e:
        print(f"  ⚠️ Could not load sound '{name}': {e}")
        sounds[name] = None
 
def play_sound(name):
    snd = sounds.get(name)
    if snd:
        snd.play()
 
def play_music(name, loops=-1):
    snd = sounds.get(name)
    if snd:
        pygame.mixer.stop()
        snd.play(loops=loops)
 
def stop_music():
    pygame.mixer.stop()
 
# Load all sounds
load_sound("startup",    "ps4-startup.mp3",                                          volume=0.7)
load_sound("menu",       "brawl-stars-menu-start-sounds-sound-effect-brawl-stars-hd-sound-effects_01web.mp3", volume=0.5)
load_sound("shoot",      "gun-sniper-rifle-shot.mp3",                       volume=0.5)
load_sound("hit",        "fortnite-shield-break-sound__1_.mp3",                      volume=0.7)
load_sound("death",      "fortnite-death-sound.mp3",                                 volume=0.8)
 
# ─── BUSHES (scaled for 3840x2160 map) ───────────────────────────────────────
BUSHES = [
    # Top-left zone
    {"x": 300,  "y": 200,  "r": 40},
    {"x": 380,  "y": 220,  "r": 32},
    {"x": 200,  "y": 460,  "r": 28},
    {"x": 260,  "y": 760,  "r": 36},
    {"x": 520,  "y": 610,  "r": 30},
    # Top-right zone
    {"x": 1100, "y": 180,  "r": 38},
    {"x": 1170, "y": 210,  "r": 30},
    {"x": 1680, "y": 310,  "r": 32},
    {"x": 1500, "y": 700,  "r": 38},
    # Center
    {"x": 760,  "y": 490,  "r": 34},
    {"x": 820,  "y": 520,  "r": 28},
    {"x": 960,  "y": 900,  "r": 34},
    {"x": 1350, "y": 830,  "r": 36},
    {"x": 1760, "y": 810,  "r": 36},
    # NEW - right half (x > 1920)
    {"x": 2200, "y": 200,  "r": 40},
    {"x": 2300, "y": 240,  "r": 32},
    {"x": 2500, "y": 460,  "r": 36},
    {"x": 2650, "y": 700,  "r": 30},
    {"x": 3000, "y": 300,  "r": 38},
    {"x": 3100, "y": 180,  "r": 34},
    {"x": 3400, "y": 420,  "r": 32},
    {"x": 3600, "y": 200,  "r": 40},
    {"x": 3700, "y": 600,  "r": 30},
    # NEW - bottom half (y > 1080)
    {"x": 300,  "y": 1200, "r": 40},
    {"x": 500,  "y": 1400, "r": 32},
    {"x": 800,  "y": 1300, "r": 36},
    {"x": 1100, "y": 1600, "r": 34},
    {"x": 1500, "y": 1200, "r": 30},
    {"x": 1800, "y": 1500, "r": 38},
    {"x": 2000, "y": 1100, "r": 36},
    {"x": 2200, "y": 1400, "r": 32},
    {"x": 2600, "y": 1300, "r": 40},
    {"x": 2900, "y": 1600, "r": 34},
    {"x": 3200, "y": 1200, "r": 30},
    {"x": 3500, "y": 1400, "r": 36},
    {"x": 3700, "y": 1800, "r": 32},
    {"x": 960,  "y": 1900, "r": 34},
    {"x": 1920, "y": 1080, "r": 40},  # center of full map
    {"x": 2800, "y": 1900, "r": 36},
]
 
def in_bush(x, y):
    for b in BUSHES:
        if math.hypot(x - b["x"], y - b["y"]) < b["r"] + 10:
            return True
    return False
 
# ─── BRAWLER DATA ─────────────────────────────────────────────────────────────
BRAWLERS = {
    "sniper": {
        "weapon": "sniper",  "cooldown": 800, "bullet_speed": 22, "damage": 80,
        "color":  (80, 200, 255), "accent": (200, 240, 255),
        "desc": "Long range, high damage. Starpower: piercing bullets.",
    },
    "minigun": {
        "weapon": "minigun", "cooldown": 100, "bullet_speed": 10, "damage": 10,
        "color":  (255, 130, 40), "accent": (255, 210, 100),
        "desc": "Rapid fire spray. Starpower: insane fire rate boost.",
    },
    "mage": {
        "weapon": "magic",   "cooldown": 400, "bullet_speed": 14, "damage": 35,
        "color":  (170, 70, 255), "accent": (220, 160, 255),
        "desc": "Magic projectiles. Starpower: turn invisible!",
    },
}
 
WEAPON_TO_BRAWLER = {"sniper": "sniper", "minigun": "minigun", "magic": "mage", "ak47": "sniper"}
 
# ─── DRAW BRAWLER SHAPE ───────────────────────────────────────────────────────
def draw_brawler(surf, brawler_name, x, y, alpha=255, scale=1.0, starpower=False, alive=True):
    bdata  = BRAWLERS.get(brawler_name, BRAWLERS["sniper"])
    color  = (80, 80, 90)  if not alive else bdata["color"]
    accent = (60, 60, 70)  if not alive else bdata["accent"]
    r      = int(14 * scale)
    tmp = pygame.Surface((80, 80), pygame.SRCALPHA)
    cx = cy = 40
 
    def ac(col, a=alpha):
        return (*col, min(255, a))
 
    if brawler_name == "sniper":
        pts = [(cx, cy-r), (int(cx+r*0.65), cy), (cx, cy+r), (int(cx-r*0.65), cy)]
        pygame.draw.polygon(tmp, ac(color), pts)
        pygame.draw.polygon(tmp, ac(accent), pts, 2)
        pygame.draw.circle(tmp, ac(accent), (cx + r//2, cy - r//3), 4)
        pygame.draw.circle(tmp, ac((20,20,30)), (cx + r//2, cy - r//3), 2)
        pygame.draw.line(tmp, ac(accent), (cx, cy), (int(cx + r*1.1), int(cy - r*0.5)), 2)
 
    elif brawler_name == "minigun":
        pts = [(int(cx + r*math.cos(math.radians(60*i-30))),
                int(cy + r*math.sin(math.radians(60*i-30)))) for i in range(6)]
        pygame.draw.polygon(tmp, ac(color), pts)
        pygame.draw.polygon(tmp, ac(accent), pts, 2)
        now = pygame.time.get_ticks()
        for i in range(3):
            ang = math.radians(120*i + now * 0.4)
            dx2 = int(cx + r*0.48*math.cos(ang))
            dy2 = int(cy + r*0.48*math.sin(ang))
            pygame.draw.circle(tmp, ac(accent), (dx2, dy2), 3)
        pygame.draw.circle(tmp, ac(accent), (cx, cy), 4)
        pygame.draw.circle(tmp, ac(color),  (cx, cy), 2)
 
    elif brawler_name == "mage":
        pts = []
        for i in range(10):
            ang = math.radians(36*i - 90)
            rad = r if i % 2 == 0 else int(r * 0.44)
            pts.append((int(cx + rad*math.cos(ang)), int(cy + rad*math.sin(ang))))
        pygame.draw.polygon(tmp, ac(color), pts)
        pygame.draw.polygon(tmp, ac(accent), pts, 2)
        now = pygame.time.get_ticks()
        if starpower:
            pulse = int(5 + 3*math.sin(now * 0.008))
            pygame.draw.circle(tmp, ac(accent, min(alpha, 220)), (cx, cy), pulse)
        else:
            pygame.draw.circle(tmp, ac(accent), (cx, cy), 4)
    else:
        pygame.draw.circle(tmp, ac(color), (cx, cy), r)
        pygame.draw.circle(tmp, ac(accent), (cx, cy), r, 2)
 
    surf.blit(tmp, (x - 40, y - 40))
 
# ─── SHARED STATE ─────────────────────────────────────────────────────────────
server_players    = {}
server_bullets    = []
server_walls      = []
 
phase      = "startup"   # start with startup sound
phase_lock = threading.Lock()
 
my_name           = ""
my_brawler        = None
lobby_player_list = []
winner_name       = ""
 
# Track previous bullet list to detect new hits
prev_bullet_ids   = set()
# Track my alive state for death sound
was_alive         = True
# Track if kicked
was_kicked        = False
 
def set_phase(p):
    global phase
    with phase_lock:
        phase = p
 
def get_phase():
    with phase_lock:
        return phase
 
# ─── STARTUP SOUND SEQUENCE ───────────────────────────────────────────────────
startup_done = False
startup_start = pygame.time.get_ticks()
 
def check_startup():
    global startup_done
    if startup_done:
        return
    now = pygame.time.get_ticks()
    elapsed = now - startup_start
    # PS4 startup is about 4-5s; switch to name entry + menu music after
    if elapsed > 4500:
        startup_done = True
        set_phase("name_entry")
        play_music("menu")
 
# ─── NETWORK ──────────────────────────────────────────────────────────────────
def receive():
    global server_players, server_bullets, server_walls, lobby_player_list, winner_name
    global was_alive, was_kicked
    while True:
        try:
            data, _ = client.recvfrom(65535)
            msg = json.loads(data.decode())
            p_msg = msg.get("phase", "")
 
            if p_msg == "kicked":
                was_kicked = True
                set_phase("lobby")
                play_music("menu")
                lobby_player_list = []
                server_players = {}
                server_bullets = []
 
            elif p_msg == "lobby":
                lobby_player_list = msg.get("players_in_lobby", [])
 
            elif p_msg == "start":
                if get_phase() in ("lobby", "name_entry"):
                    set_phase("brawler_select")
                    stop_music()
 
            elif p_msg == "running":
                prev_alive = {addr: p.get("alive", True) for addr, p in server_players.items()}
                server_players = msg.get("players", {})
                server_bullets = msg.get("bullets", [])
                server_walls   = msg.get("walls", [])
 
                # Detect newly killed players → play hit sound
                for addr, p in server_players.items():
                    if addr in prev_alive and prev_alive[addr] and not p.get("alive", True):
                        if p.get("name") == my_name:
                            play_sound("death")
                            was_alive = False
                        else:
                            play_sound("hit")
 
            elif p_msg == "game_over":
                winner_name = msg.get("winner", "Nobody")
                set_phase("game_over")
                play_music("menu")
 
        except:
            pass
 
threading.Thread(target=receive, daemon=True).start()
 
def send(obj):
    try:
        client.sendto(json.dumps(obj).encode(), (SERVER_IP, PORT))
    except:
        pass
 
def join_lobby():
    send({"type": "join_lobby", "name": my_name})
 
def send_weapon_select():
    send({"type": "weapon_select", "weapon": BRAWLERS[my_brawler]["weapon"], "brawler": my_brawler})
 
# ─── STARPOWER ────────────────────────────────────────────────────────────────
starpower_active   = False
starpower_start    = 0
starpower_duration = 5000
starpower_cooldown = 10000
last_starpower     = -10000
last_shot          = 0
 
def activate_starpower():
    global starpower_active, starpower_start, last_starpower
    now = pygame.time.get_ticks()
    if now - last_starpower > starpower_cooldown:
        starpower_active = True
        starpower_start  = now
        last_starpower   = now
        send({"type": "starpower", "brawler": my_brawler, "active": True})
 
def update_starpower():
    global starpower_active
    if starpower_active and pygame.time.get_ticks() - starpower_start > starpower_duration:
        starpower_active = False
        send({"type": "starpower", "brawler": my_brawler, "active": False})
 
# ─── UI HELPERS ───────────────────────────────────────────────────────────────
def draw_panel(x, y, w, h, color=C_PANEL, border=C_ACCENT, radius=10):
    pygame.draw.rect(screen, color,  (x, y, w, h), border_radius=radius)
    pygame.draw.rect(screen, border, (x, y, w, h), 2, border_radius=radius)
 
def centered(text, font, color, cy, x=None, shadow=True):
    if x is None:
        x = SCREEN_W // 2
    if shadow:
        s = font.render(text, True, C_DARK)
        screen.blit(s, (x - s.get_width()//2 + 2, cy + 2))
    s = font.render(text, True, color)
    screen.blit(s, (x - s.get_width()//2, cy))
 
def draw_bg():
    screen.fill(C_BG)
    for i in range(0, SCREEN_W, 40):
        pygame.draw.line(screen, (20, 22, 34), (i, 0), (i, SCREEN_H))
    for j in range(0, SCREEN_H, 40):
        pygame.draw.line(screen, (20, 22, 34), (0, j), (SCREEN_W, j))
 
# ─── SCREEN: STARTUP ─────────────────────────────────────────────────────────
def draw_startup():
    screen.fill((0, 0, 0))
    now = pygame.time.get_ticks()
    elapsed = now - startup_start
    # Fade in logo
    alpha = min(255, int(elapsed / 1500 * 255))
    alpha = min(alpha, max(0, int((4500 - elapsed) / 500 * 255)))
    s = font_big.render("BRAWL  GAME", True, C_ACCENT)
    tmp = pygame.Surface(s.get_size(), pygame.SRCALPHA)
    tmp.blit(s, (0, 0))
    tmp.set_alpha(alpha)
    screen.blit(tmp, (SCREEN_W//2 - s.get_width()//2, SCREEN_H//2 - s.get_height()//2))
 
# ─── SCREEN: NAME ENTRY ───────────────────────────────────────────────────────
name_input = ""
 
def draw_name_entry():
    draw_bg()
    pygame.draw.rect(screen, (16, 18, 32), (0, 0, SCREEN_W, 88))
    pygame.draw.line(screen, C_ACCENT, (0, 88), (SCREEN_W, 88), 2)
    centered("BRAWL  GAME", font_big, C_ACCENT, 18)
 
    base = SCREEN_W // 2
    for i, (bname, bdata) in enumerate(BRAWLERS.items()):
        bx = base - 200 + i * 200
        preview = pygame.Surface((80, 80), pygame.SRCALPHA)
        draw_brawler(preview, bname, 40, 40, scale=2.2)
        screen.blit(preview, (bx - 40, 108))
        s = font_tiny.render(bname.upper(), True, bdata["color"])
        screen.blit(s, (bx - s.get_width()//2, 190))
 
    centered("Enter your name to join", font_small, C_GRAY, 230)
    draw_panel(base - 180, 256, 360, 52, border=C_BLUE)
    cursor = "|" if (pygame.time.get_ticks()//500)%2 else " "
    s = font_med.render(name_input + cursor, True, C_WHITE)
    screen.blit(s, (base - s.get_width()//2, 269))
    centered("Press ENTER to continue  |  ESC to quit", font_small, C_GRAY, 330)
 
# ─── SCREEN: LOBBY ────────────────────────────────────────────────────────────
def draw_lobby():
    draw_bg()
    cx = SCREEN_W // 2
    pygame.draw.rect(screen, (16, 18, 32), (0, 0, SCREEN_W, 78))
    pygame.draw.line(screen, C_ACCENT, (0, 78), (SCREEN_W, 78), 2)
    centered("LOBBY", font_big, C_ACCENT, 12)
    dots = "." * (1 + (pygame.time.get_ticks()//500) % 3)
    centered(f"Waiting for host to start{dots}", font_small, C_GRAY, 83)
    panel_x = cx - 320
    draw_panel(panel_x, 100, 640, 400)
    cnt = font_small.render(f"Players  ({len(lobby_player_list)} / 10)", True, C_GRAY)
    screen.blit(cnt, (panel_x + 20, 112))
    pygame.draw.line(screen, C_ACCENT, (panel_x + 20, 134), (panel_x + 620, 134), 1)
    for i, pname in enumerate(lobby_player_list):
        y = 146 + i * 34
        if y > 476:
            break
        if i % 2 == 0:
            pygame.draw.rect(screen, (28, 30, 52), (panel_x + 2, y-3, 636, 28), border_radius=5)
        col = list(BRAWLERS.values())[i % 3]["color"]
        pygame.draw.circle(screen, col, (panel_x + 24, y+10), 6)
        s = font_small.render(pname, True, C_WHITE)
        screen.blit(s, (panel_x + 38, y+1))
    centered(f"You:  {my_name}", font_small, C_BLUE, 514)
 
    global was_kicked
    if was_kicked:
        centered("You were kicked. Wait for the next game.", font_small, C_RED, 540)
    else:
        centered("Host starts from the server console  [ENTER]", font_tiny, (55, 60, 80), 540)
 
# ─── SCREEN: BRAWLER SELECT ───────────────────────────────────────────────────
def draw_brawler_select():
    draw_bg()
    cx = SCREEN_W // 2
    pygame.draw.rect(screen, (16, 18, 32), (0, 0, SCREEN_W, 78))
    pygame.draw.line(screen, C_ACCENT, (0, 78), (SCREEN_W, 78), 2)
    centered("CHOOSE  YOUR  BRAWLER", font_big, C_ACCENT, 12)
    centered("Click a card to play", font_small, C_GRAY, 62)
    mx, mpy = pygame.mouse.get_pos()
    rects = {}
    card_w, card_h = 220, 310
    names   = list(BRAWLERS.keys())
    total_w = len(names)*card_w + (len(names)-1)*32
    sx      = cx - total_w // 2
    card_y  = (SCREEN_H - card_h) // 2 - 20
    for i, bname in enumerate(names):
        bdata  = BRAWLERS[bname]
        bx     = sx + i*(card_w+32)
        hov    = bx <= mx <= bx+card_w and card_y <= mpy <= card_y+card_h
        rects[bname] = (bx, card_y, card_w, card_h)
        bg  = (32, 36, 58) if hov else C_PANEL
        bdr = bdata["color"] if hov else (40, 44, 70)
        draw_panel(bx, card_y, card_w, card_h, color=bg, border=bdr, radius=14)
        if hov:
            glow = pygame.Surface((card_w, card_h), pygame.SRCALPHA)
            pygame.draw.rect(glow, (*bdata["color"], 20), (0, 0, card_w, card_h), border_radius=14)
            screen.blit(glow, (bx, card_y))
        draw_brawler(screen, bname, bx + card_w//2, card_y + 80, scale=2.8)
        ns = font_med.render(bname.upper(), True, bdata["color"] if hov else C_WHITE)
        screen.blit(ns, (bx + card_w//2 - ns.get_width()//2, card_y + 130))
        pygame.draw.line(screen, (40, 44, 70), (bx+14, card_y+160), (bx+card_w-14, card_y+160), 1)
        stats = [("DMG", str(bdata["damage"])),
                 ("SPD", str(bdata["bullet_speed"])),
                 ("CD",  f"{bdata['cooldown']}ms")]
        for j, (lbl, val) in enumerate(stats):
            ls = font_tiny.render(lbl, True, C_GRAY)
            vs = font_tiny.render(val, True, C_WHITE)
            screen.blit(ls, (bx+14, card_y+172+j*22))
            screen.blit(vs, (bx+card_w-vs.get_width()-14, card_y+172+j*22))
        words = bdata["desc"].split()
        lines, line = [], ""
        for w in words:
            test = line + w + " "
            if font_tiny.size(test)[0] > card_w - 18:
                lines.append(line.strip()); line = w + " "
            else:
                line = test
        if line: lines.append(line.strip())
        for j, l in enumerate(lines[:3]):
            ls = font_tiny.render(l, True, C_GRAY)
            screen.blit(ls, (bx+10, card_y+248+j*16))
        if hov:
            hs = font_tiny.render("[ click to select ]", True, bdata["color"])
            screen.blit(hs, (bx + card_w//2 - hs.get_width()//2, card_y+card_h-18))
    return rects
 
# ─── BUSH DRAWING ─────────────────────────────────────────────────────────────
def draw_bushes_back():
    for b in BUSHES:
        sx, sy = world_to_screen(b["x"], b["y"])
        r = b["r"]
        if -r < sx < SCREEN_W + r and -r < sy < SCREEN_H + r:
            pygame.draw.circle(screen, C_GRASS,  (sx, sy), r)
            pygame.draw.circle(screen, C_GRASS2, (sx, sy), int(r*0.62))
 
def draw_bushes_front():
    for b in BUSHES:
        sx, sy = world_to_screen(b["x"], b["y"])
        r = b["r"]
        if -r < sx < SCREEN_W + r and -r < sy < SCREEN_H + r:
            s = pygame.Surface((r*2+6, r*2+6), pygame.SRCALPHA)
            c = r+3
            pygame.draw.circle(s, (*C_GRASS,  210), (c, c),           r)
            pygame.draw.circle(s, (*C_GRASS2, 190), (c-r//3, c-r//3), int(r*0.54))
            pygame.draw.circle(s, (*C_GRASS2, 170), (c+r//4, c-r//4), int(r*0.48))
            pygame.draw.circle(s, (*C_GRASS,  230), (c, c-r//2),      int(r*0.44))
            screen.blit(s, (sx-r-3, sy-r-3))
 
# ─── MAP BORDER ───────────────────────────────────────────────────────────────
def draw_map_border():
    bx, by = world_to_screen(0, 0)
    pygame.draw.rect(screen, (160, 50, 50), (bx - 4, by - 4, MAP_W + 8, MAP_H + 8), 4)
    if bx > 0:
        pygame.draw.rect(screen, (6, 6, 10), (0, 0, bx, SCREEN_H))
    if by > 0:
        pygame.draw.rect(screen, (6, 6, 10), (0, 0, SCREEN_W, by))
    right = bx + MAP_W
    if right < SCREEN_W:
        pygame.draw.rect(screen, (6, 6, 10), (right, 0, SCREEN_W - right, SCREEN_H))
    bottom = by + MAP_H
    if bottom < SCREEN_H:
        pygame.draw.rect(screen, (6, 6, 10), (0, bottom, SCREEN_W, SCREEN_H - bottom))
 
# ─── CROSSHAIR ────────────────────────────────────────────────────────────────
def draw_crosshair(mx, my, color):
    size, gap = 13, 4
    pygame.draw.line(screen, C_DARK, (mx - size, my), (mx - gap, my), 3)
    pygame.draw.line(screen, C_DARK, (mx + gap,  my), (mx + size, my), 3)
    pygame.draw.line(screen, C_DARK, (mx, my - size), (mx, my - gap), 3)
    pygame.draw.line(screen, C_DARK, (mx, my + gap),  (mx, my + size), 3)
    pygame.draw.line(screen, color,  (mx - size, my), (mx - gap, my), 1)
    pygame.draw.line(screen, color,  (mx + gap,  my), (mx + size, my), 1)
    pygame.draw.line(screen, color,  (mx, my - size), (mx, my - gap), 1)
    pygame.draw.line(screen, color,  (mx, my + gap),  (mx, my + size), 1)
    pygame.draw.circle(screen, color, (mx, my), 3, 1)
 
# ─── GET MY WORLD POSITION ────────────────────────────────────────────────────
def get_my_pos():
    for addr, p in server_players.items():
        if p.get("name") == my_name:
            return float(p["x"]), float(p["y"])
    return float(MAP_W // 2), float(MAP_H // 2)
 
# ─── SHOOT TOWARD MOUSE ───────────────────────────────────────────────────────
def try_shoot():
    global last_shot
    if not my_brawler:
        return
    now = pygame.time.get_ticks()
    st  = BRAWLERS[my_brawler]
    cd  = 40 if (starpower_active and my_brawler == "minigun") else st["cooldown"]
    if now - last_shot <= cd:
        return
    my_wx, my_wy = get_my_pos()
    mx_s, my_s   = pygame.mouse.get_pos()
    target_wx, target_wy = screen_to_world(mx_s, my_s)
    ang = math.atan2(target_wy - my_wy, target_wx - my_wx)
    last_shot = now
    play_sound("shoot")
    send({
        "type":   "shoot",
        "dx":     math.cos(ang),
        "dy":     math.sin(ang),
        "speed":  st["bullet_speed"],
        "damage": st["damage"],
        "weapon": st["weapon"],
        "pierce": starpower_active and my_brawler == "sniper"
    })
 
# ─── SCREEN: PLAYING ──────────────────────────────────────────────────────────
def draw_game():
    screen.fill((30, 38, 28))
    tile = 48
    off_x = int(cam_x % tile)
    off_y = int(cam_y % tile)
    base_tx = int(cam_x // tile)
    base_ty = int(cam_y // tile)
    for ix in range(-1, SCREEN_W // tile + 2):
        for iy in range(-1, SCREEN_H // tile + 2):
            if ((base_tx + ix) + (base_ty + iy)) % 2 == 0:
                pygame.draw.rect(screen, (32, 40, 30),
                                 (ix*tile - off_x, iy*tile - off_y, tile, tile))
 
    update_starpower()
    draw_map_border()
 
    for w in server_walls:
        wx, wy = world_to_screen(w["x"], w["y"])
        # Only draw if on screen
        if wx + w["w"] < 0 or wx > SCREEN_W or wy + w["h"] < 0 or wy > SCREEN_H:
            continue
        pygame.draw.rect(screen, (65, 65, 80),    (wx+2, wy+2, w["w"], w["h"]))
        pygame.draw.rect(screen, (92, 92, 112),   (wx,   wy,   w["w"], w["h"]))
        pygame.draw.rect(screen, (128, 128, 152), (wx,   wy,   w["w"], w["h"]), 2)
 
    draw_bushes_back()
 
    for addr, p in server_players.items():
        px_w, py_w = p["x"], p["y"]
        px, py = world_to_screen(int(px_w), int(py_w))
        is_me     = (p.get("name") == my_name)
        bname     = WEAPON_TO_BRAWLER.get(p.get("weapon", "ak47"), "sniper")
        invisible = p.get("invisible", False)
        sp_on     = p.get("starpower", False)
        alive     = p.get("alive", True)
 
        if not is_me:
            if invisible:
                continue
            if in_bush(px_w, py_w):
                continue
 
        if not alive:
            alpha = 80
        elif invisible and is_me:
            alpha = 85
        elif in_bush(px_w, py_w) and is_me:
            alpha = 150
        else:
            alpha = 255
 
        sh = pygame.Surface((32, 10), pygame.SRCALPHA)
        pygame.draw.ellipse(sh, (0,0,0,55), (0,0,32,10))
        screen.blit(sh, (px-16, py+13))
        draw_brawler(screen, bname, px, py, alpha=alpha, scale=1.0,
                     starpower=sp_on and is_me, alive=alive)
 
        if is_me and my_brawler:
            ring = pygame.Surface((38, 38), pygame.SRCALPHA)
            rc = BRAWLERS[my_brawler]["color"]
            pygame.draw.circle(ring, (*rc, 140), (19, 19), 18, 2)
            screen.blit(ring, (px-19, py-19))
 
        if not alive:
            continue
 
        nc = C_ACCENT if is_me else C_WHITE
        ns_sh = font_tiny.render(p.get("name","?"), True, C_DARK)
        ns    = font_tiny.render(p.get("name","?"), True, nc)
        screen.blit(ns_sh, (px - ns.get_width()//2+1, py-36+1))
        screen.blit(ns,    (px - ns.get_width()//2,   py-36))
 
        hp_pct = max(0, p["hp"]/100)
        hp_col = C_GREEN if hp_pct > 0.5 else (C_ACCENT if hp_pct > 0.25 else C_RED)
        pygame.draw.rect(screen, (35, 8, 8),  (px-18, py-26, 36, 5), border_radius=2)
        pygame.draw.rect(screen, hp_col,      (px-18, py-26, int(36*hp_pct), 5), border_radius=2)
 
        if sp_on:
            now = pygame.time.get_ticks()
            gr  = int(18 + 3*math.sin(now*0.006))
            gs  = pygame.Surface((gr*2+4, gr*2+4), pygame.SRCALPHA)
            sc  = BRAWLERS.get(bname, BRAWLERS["sniper"])["accent"]
            pygame.draw.circle(gs, (*sc, 55), (gr+2, gr+2), gr)
            screen.blit(gs, (px-gr-2, py-gr-2))
 
    for b in server_bullets:
        bx, by = world_to_screen(int(b["x"]), int(b["y"]))
        if bx < -20 or bx > SCREEN_W+20 or by < -20 or by > SCREEN_H+20:
            continue
        pierce = b.get("pierce", False)
        col    = (255, 80, 80) if pierce else (255, 215, 50)
        size   = 6 if pierce else 5
        pygame.draw.circle(screen, col, (bx, by), size)
        gs2 = pygame.Surface((22, 22), pygame.SRCALPHA)
        pygame.draw.circle(gs2, (*col, 55), (11, 11), 10)
        screen.blit(gs2, (bx-11, by-11))
 
    draw_bushes_front()
    draw_hud()
 
    mx, my_m = pygame.mouse.get_pos()
    ch_col = BRAWLERS[my_brawler]["color"] if my_brawler else C_WHITE
    draw_crosshair(mx, my_m, ch_col)
 
def draw_hud():
    now = pygame.time.get_ticks()
    if not my_brawler:
        return
    bdata = BRAWLERS[my_brawler]
    cx = SCREEN_W // 2
 
    # Brawler badge (top-left)
    draw_panel(6, 6, 200, 62, color=(10, 12, 22), border=(32, 36, 58))
    badge = pygame.Surface((80, 80), pygame.SRCALPHA)
    draw_brawler(badge, my_brawler, 40, 40, scale=1.3)
    screen.blit(badge, (12, 2))
    s1 = font_small.render(my_brawler.upper(), True, bdata["color"])
    screen.blit(s1, (66, 14))
    s2 = font_tiny.render("[F] Starpower | ESC quit", True, C_GRAY)
    screen.blit(s2, (66, 38))
 
    # Minimap (top-right)
    mm_w, mm_h = 192, 108
    mm_x = SCREEN_W - mm_w - 10
    mm_y = 10
    scale_x = mm_w / MAP_W
    scale_y = mm_h / MAP_H
    draw_panel(mm_x - 3, mm_y - 3, mm_w + 6, mm_h + 6, color=(8,10,18), border=(30,34,55), radius=5)
    pygame.draw.rect(screen, (20, 26, 18), (mm_x, mm_y, mm_w, mm_h))
    for w in server_walls:
        wx = mm_x + int(w["x"] * scale_x)
        wy = mm_y + int(w["y"] * scale_y)
        ww = max(2, int(w["w"] * scale_x))
        wh = max(2, int(w["h"] * scale_y))
        pygame.draw.rect(screen, (80, 80, 100), (wx, wy, ww, wh))
    for addr, p in server_players.items():
        mmx = mm_x + int(p["x"] * scale_x)
        mmy = mm_y + int(p["y"] * scale_y)
        is_me = p.get("name") == my_name
        col = C_ACCENT if is_me else C_RED
        pygame.draw.circle(screen, col, (mmx, mmy), 3 if is_me else 2)
    vx = mm_x + int(cam_x * scale_x)
    vy = mm_y + int(cam_y * scale_y)
    vw = max(1, int(SCREEN_W * scale_x))
    vh = max(1, int(SCREEN_H * scale_y))
    pygame.draw.rect(screen, (200, 200, 200), (vx, vy, vw, vh), 1)
 
    # Starpower bar (bottom center)
    bar_w = 340
    bx2, by2, bh = cx - bar_w//2, SCREEN_H - 36, 22
    draw_panel(bx2-3, by2-3, bar_w+6, bh+6, color=(8,10,18), border=(30,34,55), radius=7)
    if starpower_active:
        elapsed  = now - starpower_start
        progress = 1.0 - min(elapsed/starpower_duration, 1.0)
        col      = bdata["color"]
        label    = "STARPOWER  ACTIVE"
        pulse    = int(bar_w * progress)
        pygame.draw.rect(screen, (18,8,38),  (bx2, by2, bar_w, bh), border_radius=5)
        pygame.draw.rect(screen, col,        (bx2, by2, pulse, bh), border_radius=5)
        shim = pygame.Surface((max(1,pulse), bh), pygame.SRCALPHA)
        sa   = int(55 + 35*math.sin(now*0.012))
        pygame.draw.rect(shim, (255,255,255,sa), (0, 0, max(1,pulse), bh//2))
        screen.blit(shim, (bx2, by2))
    elif now - last_starpower < starpower_cooldown:
        elapsed  = now - last_starpower
        progress = elapsed / starpower_cooldown
        col      = C_GRAY
        secs_left = int((starpower_cooldown - elapsed)/1000)+1
        label    = f"COOLDOWN  {secs_left}s"
        pygame.draw.rect(screen, (18,18,28), (bx2, by2, bar_w, bh), border_radius=5)
        pygame.draw.rect(screen, col,        (bx2, by2, int(bar_w*progress), bh), border_radius=5)
    else:
        col   = C_ACCENT
        label = "STARPOWER  READY  [F]"
        blink = (now//600)%2
        pygame.draw.rect(screen, (28,24,8) if blink else (18,18,10), (bx2, by2, bar_w, bh), border_radius=5)
        if blink:
            pygame.draw.rect(screen, col, (bx2, by2, bar_w, bh), border_radius=5)
    ls = font_tiny.render(label, True, col)
    screen.blit(ls, (cx - ls.get_width()//2, by2+4))
 
    # Bush indicator
    for addr, p in server_players.items():
        if p.get("name") == my_name and in_bush(p["x"], p["y"]):
            bi  = font_small.render("  IN BUSH - HIDDEN  ", True, C_GRASS2)
            bib = font_small.render("  IN BUSH - HIDDEN  ", True, C_DARK)
            screen.blit(bib, (cx - bi.get_width()//2+1, SCREEN_H - 66))
            screen.blit(bi,  (cx - bi.get_width()//2,   SCREEN_H - 66))
            break
 
# ─── SCREEN: DEAD ─────────────────────────────────────────────────────────────
def draw_dead_screen():
    draw_game()
    ov = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
    ov.fill((0, 0, 0, 155))
    screen.blit(ov, (0, 0))
    cy = SCREEN_H // 2 - 60
    centered("YOU  DIED", font_big, C_RED, cy)
    centered("Waiting for round to end...", font_small, C_GRAY, cy + 80)
    centered("You will return to the lobby soon.", font_small, (75, 78, 98), cy + 112)
 
# ─── SCREEN: GAME OVER ────────────────────────────────────────────────────────
go_timer = 0
 
def draw_game_over():
    draw_bg()
    cx = SCREEN_W // 2
    cy = SCREEN_H // 2 - 140
    centered("ROUND  OVER", font_big, C_ACCENT, cy)
    pygame.draw.polygon(screen, C_ACCENT, [
        (cx,   cy+80),(cx+16,cy+104),(cx+38,cy+104),(cx+22,cy+120),
        (cx+28,cy+144),(cx,cy+128),(cx-28,cy+144),(cx-22,cy+120),
        (cx-38,cy+104),(cx-16,cy+104)
    ])
    centered(f"Winner:   {winner_name}", font_med, C_GREEN, cy+156)
    centered("Returning to lobby...", font_small, C_GRAY, cy+196)
    elapsed = pygame.time.get_ticks() - go_timer
    bw = int(500 * min(elapsed/4000, 1.0))
    pygame.draw.rect(screen, (28,30,50), (cx - 250, cy+240, 500, 14), border_radius=7)
    pygame.draw.rect(screen, C_ACCENT,  (cx - 250, cy+240, bw,  14), border_radius=7)
 
# ─── MAIN LOOP ────────────────────────────────────────────────────────────────
running       = True
brawler_rects = {}
mouse_held    = False
 
pygame.mouse.set_visible(False)
 
# Play startup sound immediately
play_sound("startup")
 
while running:
    cur_phase = get_phase()
 
    # Handle startup transition
    if cur_phase == "startup":
        check_startup()
 
    if cur_phase in ("playing", "dead_screen"):
        px, py = get_my_pos()
        update_camera(px, py)
 
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
 
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            running = False
 
        if cur_phase == "name_entry":
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN and name_input.strip():
                    my_name = name_input.strip()
                    join_lobby()
                    set_phase("lobby")
                elif event.key == pygame.K_BACKSPACE:
                    name_input = name_input[:-1]
                elif len(name_input) < 16 and event.unicode.isprintable():
                    name_input += event.unicode
 
        elif cur_phase == "brawler_select":
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mx, mpy = event.pos
                for bname, rect in brawler_rects.items():
                    rx, ry, rw, rh = rect
                    if rx <= mx <= rx+rw and ry <= mpy <= ry+rh:
                        my_brawler = bname
                        last_shot  = 0
                        was_alive  = True
                        send_weapon_select()
                        set_phase("playing")
                        break
 
        elif cur_phase == "playing":
            if event.type == pygame.KEYDOWN and event.key == pygame.K_f:
                activate_starpower()
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mouse_held = True
                try_shoot()
            if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                mouse_held = False
 
    # Hold-to-shoot (minigun)
    if cur_phase == "playing" and mouse_held and my_brawler in ("minigun",):
        try_shoot()
 
    # Minigun starpower continuous fire
    if cur_phase == "playing" and my_brawler and starpower_active and my_brawler == "minigun":
        try_shoot()
 
    # Death detection
    if cur_phase == "playing" and server_players:
        for addr, p in server_players.items():
            if p.get("name") == my_name and not p["alive"]:
                set_phase("dead_screen")
                break
 
    # Movement
    if cur_phase == "playing":
        keys = pygame.key.get_pressed()
        send({"type":"move",
              "up":   bool(keys[pygame.K_w]),
              "down": bool(keys[pygame.K_s]),
              "left": bool(keys[pygame.K_a]),
              "right":bool(keys[pygame.K_d])})
 
    if cur_phase == "game_over":
        if go_timer == 0:
            go_timer = pygame.time.get_ticks()
        if pygame.time.get_ticks() - go_timer > 4000:
            go_timer = 0; my_brawler = None; was_kicked = False
            set_phase("lobby"); join_lobby()
 
    if cur_phase == "lobby":
        now_ms = pygame.time.get_ticks()
        if now_ms - getattr(draw_lobby, "_last_hb", 0) > 1000:
            draw_lobby._last_hb = now_ms
            join_lobby()
 
    cur_phase = get_phase()
    if   cur_phase == "startup":        draw_startup()
    elif cur_phase == "name_entry":     draw_name_entry()
    elif cur_phase == "lobby":          draw_lobby()
    elif cur_phase == "brawler_select": brawler_rects = draw_brawler_select()
    elif cur_phase == "playing":        draw_game()
    elif cur_phase == "dead_screen":    draw_dead_screen()
    elif cur_phase == "game_over":      draw_game_over()
 
    pygame.display.flip()
    clock.tick(60)
 
pygame.mouse.set_visible(True)
pygame.quit()