import socket
import threading
import json
import pygame
import math

SERVER_IP = "192.168.0.100"
PORT = 5555

client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

pygame.init()
screen = pygame.display.set_mode((800, 600))
pygame.display.set_caption("Brawl Game")
clock = pygame.time.Clock()

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

# ─── BUSHES ───────────────────────────────────────────────────────────────────
BUSHES = [
    {"x": 180, "y": 150, "r": 32},
    {"x": 228, "y": 162, "r": 26},
    {"x": 600, "y": 130, "r": 30},
    {"x": 648, "y": 148, "r": 24},
    {"x": 150, "y": 460, "r": 28},
    {"x": 680, "y": 440, "r": 30},
    {"x": 390, "y": 290, "r": 26},
    {"x": 418, "y": 312, "r": 22},
    {"x": 560, "y": 480, "r": 28},
    {"x": 240, "y": 320, "r": 24},
]

def in_bush(x, y):
    for b in BUSHES:
        if math.hypot(x - b["x"], y - b["y"]) < b["r"] + 10:
            return True
    return False

# ─── BRAWLER DATA ─────────────────────────────────────────────────────────────
BRAWLERS = {
    "sniper": {
        "weapon": "sniper",  "cooldown": 800, "bullet_speed": 18, "damage": 80,
        "color":  (80, 200, 255), "accent": (200, 240, 255),
        "desc": "Long range, high damage. Starpower: piercing bullets.",
    },
    "minigun": {
        "weapon": "minigun", "cooldown": 100, "bullet_speed": 8,  "damage": 10,
        "color":  (255, 130, 40), "accent": (255, 210, 100),
        "desc": "Rapid fire spray. Starpower: insane fire rate boost.",
    },
    "mage": {
        "weapon": "magic",   "cooldown": 400, "bullet_speed": 12, "damage": 35,
        "color":  (170, 70, 255), "accent": (220, 160, 255),
        "desc": "Magic projectiles. Starpower: turn invisible!",
    },
}

WEAPON_TO_BRAWLER = {"sniper": "sniper", "minigun": "minigun", "magic": "mage", "ak47": "sniper"}

# ─── DRAW BRAWLER SHAPE ───────────────────────────────────────────────────────
def draw_brawler(surf, brawler_name, x, y, alpha=255, scale=1.0, starpower=False, alive=True):
    bdata  = BRAWLERS.get(brawler_name, BRAWLERS["sniper"])
    color  = (80, 80, 90)   if not alive else bdata["color"]
    accent = (60, 60, 70)   if not alive else bdata["accent"]
    r      = int(14 * scale)

    tmp = pygame.Surface((80, 80), pygame.SRCALPHA)
    cx = cy = 40

    def ac(col, a=alpha):
        return (*col, min(255, a))

    if brawler_name == "sniper":
        # Slim diamond
        pts = [(cx, cy-r), (int(cx+r*0.65), cy), (cx, cy+r), (int(cx-r*0.65), cy)]
        pygame.draw.polygon(tmp, ac(color), pts)
        pygame.draw.polygon(tmp, ac(accent), pts, 2)
        # Scope lens
        pygame.draw.circle(tmp, ac(accent), (cx + r//2, cy - r//3), 4)
        pygame.draw.circle(tmp, ac((20,20,30)), (cx + r//2, cy - r//3), 2)
        # Barrel
        pygame.draw.line(tmp, ac(accent), (cx, cy), (int(cx + r*1.1), int(cy - r*0.5)), 2)

    elif brawler_name == "minigun":
        # Chunky hexagon
        pts = [(int(cx + r*math.cos(math.radians(60*i-30))),
                int(cy + r*math.sin(math.radians(60*i-30)))) for i in range(6)]
        pygame.draw.polygon(tmp, ac(color), pts)
        pygame.draw.polygon(tmp, ac(accent), pts, 2)
        # Spinning barrel dots
        now = pygame.time.get_ticks()
        for i in range(3):
            ang = math.radians(120*i + now * 0.4)
            dx2 = int(cx + r*0.48*math.cos(ang))
            dy2 = int(cy + r*0.48*math.sin(ang))
            pygame.draw.circle(tmp, ac(accent), (dx2, dy2), 3)
        # Center bolt
        pygame.draw.circle(tmp, ac(accent), (cx, cy), 4)
        pygame.draw.circle(tmp, ac(color),  (cx, cy), 2)

    elif brawler_name == "mage":
        # 5-point star
        pts = []
        for i in range(10):
            ang = math.radians(36*i - 90)
            rad = r if i % 2 == 0 else int(r * 0.44)
            pts.append((int(cx + rad*math.cos(ang)), int(cy + rad*math.sin(ang))))
        pygame.draw.polygon(tmp, ac(color), pts)
        pygame.draw.polygon(tmp, ac(accent), pts, 2)
        # Pulsing core
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

phase      = "name_entry"
phase_lock = threading.Lock()

my_name           = ""
my_brawler        = None
lobby_player_list = []
winner_name       = ""

def set_phase(p):
    global phase
    with phase_lock:
        phase = p

def get_phase():
    with phase_lock:
        return phase

# ─── NETWORK ──────────────────────────────────────────────────────────────────
def receive():
    global server_players, server_bullets, server_walls, lobby_player_list, winner_name
    while True:
        try:
            data, _ = client.recvfrom(65535)
            msg = json.loads(data.decode())
            p = msg.get("phase", "")
            if p == "lobby":
                lobby_player_list = msg.get("players_in_lobby", [])
            elif p == "start":
                if get_phase() in ("lobby", "name_entry"):
                    set_phase("brawler_select")
            elif p == "running":
                server_players = msg.get("players", {})
                server_bullets = msg.get("bullets", [])
                server_walls   = msg.get("walls", [])
            elif p == "game_over":
                winner_name = msg.get("winner", "Nobody")
                set_phase("game_over")
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

def centered(text, font, color, cy, x=400, shadow=True):
    if shadow:
        s = font.render(text, True, C_DARK)
        screen.blit(s, (x - s.get_width()//2 + 2, cy + 2))
    s = font.render(text, True, color)
    screen.blit(s, (x - s.get_width()//2, cy))

def draw_bg():
    screen.fill(C_BG)
    for i in range(0, 800, 40):
        pygame.draw.line(screen, (20, 22, 34), (i, 0), (i, 600))
    for j in range(0, 600, 40):
        pygame.draw.line(screen, (20, 22, 34), (0, j), (800, j))

# ─── SCREEN: NAME ENTRY ───────────────────────────────────────────────────────
name_input = ""

def draw_name_entry():
    draw_bg()
    pygame.draw.rect(screen, (16, 18, 32), (0, 0, 800, 88))
    pygame.draw.line(screen, C_ACCENT, (0, 88), (800, 88), 2)
    centered("BRAWL  GAME", font_big, C_ACCENT, 18)

    # Mini brawler previews
    for i, (bname, bdata) in enumerate(BRAWLERS.items()):
        bx = 200 + i * 200
        preview = pygame.Surface((80, 80), pygame.SRCALPHA)
        draw_brawler(preview, bname, 40, 40, scale=2.2)
        screen.blit(preview, (bx - 40, 108))
        s = font_tiny.render(bname.upper(), True, bdata["color"])
        screen.blit(s, (bx - s.get_width()//2, 190))

    centered("Enter your name to join", font_small, C_GRAY, 230)
    draw_panel(220, 256, 360, 52, border=C_BLUE)
    cursor = "|" if (pygame.time.get_ticks()//500)%2 else " "
    s = font_med.render(name_input + cursor, True, C_WHITE)
    screen.blit(s, (400 - s.get_width()//2, 269))
    centered("Press  ENTER  to continue", font_small, C_GRAY, 330)

# ─── SCREEN: LOBBY ────────────────────────────────────────────────────────────
def draw_lobby():
    draw_bg()
    pygame.draw.rect(screen, (16, 18, 32), (0, 0, 800, 78))
    pygame.draw.line(screen, C_ACCENT, (0, 78), (800, 78), 2)
    centered("LOBBY", font_big, C_ACCENT, 12)

    dots = "." * (1 + (pygame.time.get_ticks()//500) % 3)
    centered(f"Waiting for host to start{dots}", font_small, C_GRAY, 83)

    draw_panel(80, 100, 640, 400)
    cnt = font_small.render(f"Players  ({len(lobby_player_list)} / 10)", True, C_GRAY)
    screen.blit(cnt, (100, 112))
    pygame.draw.line(screen, C_ACCENT, (100, 134), (700, 134), 1)

    for i, pname in enumerate(lobby_player_list):
        y = 146 + i * 34
        if y > 476:
            break
        if i % 2 == 0:
            pygame.draw.rect(screen, (28, 30, 52), (82, y-3, 636, 28), border_radius=5)
        col = list(BRAWLERS.values())[i % 3]["color"]
        pygame.draw.circle(screen, col, (104, y+10), 6)
        s = font_small.render(pname, True, C_WHITE)
        screen.blit(s, (118, y+1))

    centered(f"You:  {my_name}", font_small, C_BLUE, 514)
    centered("Host starts from the server console  [ENTER]", font_tiny, (55, 60, 80), 540)

# ─── SCREEN: BRAWLER SELECT ───────────────────────────────────────────────────
def draw_brawler_select():
    draw_bg()
    pygame.draw.rect(screen, (16, 18, 32), (0, 0, 800, 78))
    pygame.draw.line(screen, C_ACCENT, (0, 78), (800, 78), 2)
    centered("CHOOSE  YOUR  BRAWLER", font_big, C_ACCENT, 12)
    centered("Click a card to play", font_small, C_GRAY, 62)

    mx, mpy = pygame.mouse.get_pos()
    rects = {}
    card_w, card_h = 196, 280
    names   = list(BRAWLERS.keys())
    total_w = len(names)*card_w + (len(names)-1)*28
    sx      = (800 - total_w)//2

    for i, bname in enumerate(names):
        bdata  = BRAWLERS[bname]
        cx     = sx + i*(card_w+28)
        cy     = 118
        hov    = cx <= mx <= cx+card_w and cy <= mpy <= cy+card_h
        rects[bname] = (cx, cy, card_w, card_h)

        bg  = (32, 36, 58) if hov else C_PANEL
        bdr = bdata["color"] if hov else (40, 44, 70)
        draw_panel(cx, cy, card_w, card_h, color=bg, border=bdr, radius=14)

        if hov:
            glow = pygame.Surface((card_w, card_h), pygame.SRCALPHA)
            pygame.draw.rect(glow, (*bdata["color"], 20), (0, 0, card_w, card_h), border_radius=14)
            screen.blit(glow, (cx, cy))

        # Big brawler shape
        draw_brawler(screen, bname, cx + card_w//2, cy + 70, scale=2.6)

        ns = font_med.render(bname.upper(), True, bdata["color"] if hov else C_WHITE)
        screen.blit(ns, (cx + card_w//2 - ns.get_width()//2, cy + 116))

        pygame.draw.line(screen, (40, 44, 70), (cx+14, cy+144), (cx+card_w-14, cy+144), 1)

        stats = [("DMG", str(bdata["damage"])),
                 ("SPD", str(bdata["bullet_speed"])),
                 ("CD",  f"{bdata['cooldown']}ms")]
        for j, (lbl, val) in enumerate(stats):
            ls = font_tiny.render(lbl, True, C_GRAY)
            vs = font_tiny.render(val, True, C_WHITE)
            screen.blit(ls, (cx+14, cy+154+j*22))
            screen.blit(vs, (cx+card_w-vs.get_width()-14, cy+154+j*22))

        # Description wrapped
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
            screen.blit(ls, (cx+10, cy+225+j*16))

        if hov:
            hs = font_tiny.render("[ click to select ]", True, bdata["color"])
            screen.blit(hs, (cx + card_w//2 - hs.get_width()//2, cy+card_h-18))

    return rects

# ─── BUSH DRAWING ─────────────────────────────────────────────────────────────
def draw_bushes_back():
    for b in BUSHES:
        pygame.draw.circle(screen, C_GRASS,  (b["x"], b["y"]), b["r"])
        pygame.draw.circle(screen, C_GRASS2, (b["x"], b["y"]), int(b["r"]*0.62))

def draw_bushes_front():
    for b in BUSHES:
        x, y, r = b["x"], b["y"], b["r"]
        s = pygame.Surface((r*2+6, r*2+6), pygame.SRCALPHA)
        c = r+3
        pygame.draw.circle(s, (*C_GRASS,  210), (c, c),           r)
        pygame.draw.circle(s, (*C_GRASS2, 190), (c-r//3, c-r//3), int(r*0.54))
        pygame.draw.circle(s, (*C_GRASS2, 170), (c+r//4, c-r//4), int(r*0.48))
        pygame.draw.circle(s, (*C_GRASS,  230), (c, c-r//2),      int(r*0.44))
        screen.blit(s, (x-r-3, y-r-3))

# ─── SCREEN: PLAYING ──────────────────────────────────────────────────────────
def draw_game():
    # Tiled grass floor
    screen.fill((30, 38, 28))
    for ix in range(0, 800, 48):
        for iy in range(0, 600, 48):
            if (ix//48 + iy//48) % 2 == 0:
                pygame.draw.rect(screen, (32, 40, 30), (ix, iy, 48, 48))

    update_starpower()

    # Walls
    for w in server_walls:
        pygame.draw.rect(screen, (65, 65, 80),   (w["x"]+2, w["y"]+2, w["w"], w["h"]))
        pygame.draw.rect(screen, (92, 92, 112),  (w["x"],   w["y"],   w["w"], w["h"]))
        pygame.draw.rect(screen, (128, 128, 152),(w["x"],   w["y"],   w["w"], w["h"]), 2)

    draw_bushes_back()

    # ── Players ──────────────────────────────────────────────────────────────
    for addr, p in server_players.items():
        px, py  = int(p["x"]), int(p["y"])
        is_me   = (p.get("name") == my_name)
        bname   = WEAPON_TO_BRAWLER.get(p.get("weapon", "ak47"), "sniper")
        invisible = p.get("invisible", False)
        sp_on   = p.get("starpower", False)
        alive   = p.get("alive", True)

        # Visibility rules
        if not is_me:
            if invisible:
                continue          # mage invis: nobody else sees them
            if in_bush(px, py):
                continue          # enemy in bush: hidden

        # Alpha for self
        if not alive:
            alpha = 80
        elif invisible and is_me:
            alpha = 85            # mage sees self as very dim ghost
        elif in_bush(px, py) and is_me:
            alpha = 150           # self in bush: semi-transparent
        else:
            alpha = 255

        # Drop shadow
        sh = pygame.Surface((32, 10), pygame.SRCALPHA)
        pygame.draw.ellipse(sh, (0,0,0,55), (0,0,32,10))
        screen.blit(sh, (px-16, py+13))

        # Brawler shape
        draw_brawler(screen, bname, px, py, alpha=alpha, scale=1.0,
                     starpower=sp_on and is_me, alive=alive)

        # My player ring
        if is_me and my_brawler:
            ring = pygame.Surface((38, 38), pygame.SRCALPHA)
            rc = BRAWLERS[my_brawler]["color"]
            pygame.draw.circle(ring, (*rc, 140), (19, 19), 18, 2)
            screen.blit(ring, (px-19, py-19))

        if not alive:
            continue

        # Name tag
        nc = C_ACCENT if is_me else C_WHITE
        ns_sh = font_tiny.render(p.get("name","?"), True, C_DARK)
        ns    = font_tiny.render(p.get("name","?"), True, nc)
        screen.blit(ns_sh, (px - ns.get_width()//2+1, py-36+1))
        screen.blit(ns,    (px - ns.get_width()//2,   py-36))

        # HP bar
        hp_pct = max(0, p["hp"]/100)
        hp_col = C_GREEN if hp_pct > 0.5 else (C_ACCENT if hp_pct > 0.25 else C_RED)
        pygame.draw.rect(screen, (35, 8, 8),  (px-16, py-24, 32, 5), border_radius=2)
        pygame.draw.rect(screen, hp_col,      (px-16, py-24, int(32*hp_pct), 5), border_radius=2)

        # Starpower glow
        if sp_on:
            now = pygame.time.get_ticks()
            gr  = int(18 + 3*math.sin(now*0.006))
            gs  = pygame.Surface((gr*2+4, gr*2+4), pygame.SRCALPHA)
            sc  = BRAWLERS.get(bname, BRAWLERS["sniper"])["accent"]
            pygame.draw.circle(gs, (*sc, 55), (gr+2, gr+2), gr)
            screen.blit(gs, (px-gr-2, py-gr-2))

    # Bullets
    for b in server_bullets:
        bx, by = int(b["x"]), int(b["y"])
        pierce = b.get("pierce", False)
        col    = (255, 80, 80) if pierce else (255, 215, 50)
        size   = 6 if pierce else 5
        pygame.draw.circle(screen, col, (bx, by), size)
        gs2 = pygame.Surface((22, 22), pygame.SRCALPHA)
        pygame.draw.circle(gs2, (*col, 55), (11, 11), 10)
        screen.blit(gs2, (bx-11, by-11))

    draw_bushes_front()
    draw_hud()

def draw_hud():
    now = pygame.time.get_ticks()
    if not my_brawler:
        return

    bdata = BRAWLERS[my_brawler]

    # ── Top-left: brawler badge ──
    draw_panel(6, 6, 194, 58, color=(10, 12, 22), border=(32, 36, 58))
    badge = pygame.Surface((80, 80), pygame.SRCALPHA)
    draw_brawler(badge, my_brawler, 40, 40, scale=1.3)
    screen.blit(badge, (12, 2))
    s1 = font_small.render(my_brawler.upper(), True, bdata["color"])
    screen.blit(s1, (62, 12))
    s2 = font_tiny.render("[F] Starpower", True, C_GRAY)
    screen.blit(s2, (62, 36))

    # ── Starpower bar (bottom center) ──
    bx, by2, bw, bh = 248, 566, 304, 22
    draw_panel(bx-3, by2-3, bw+6, bh+6, color=(8,10,18), border=(30,34,55), radius=7)

    if starpower_active:
        elapsed  = now - starpower_start
        progress = 1.0 - min(elapsed/starpower_duration, 1.0)
        col      = bdata["color"]
        label    = "STARPOWER  ACTIVE"
        pulse    = int(bw * progress)
        pygame.draw.rect(screen, (18,8,38),  (bx, by2, bw, bh), border_radius=5)
        pygame.draw.rect(screen, col,        (bx, by2, pulse, bh), border_radius=5)
        # Shimmer overlay
        shim = pygame.Surface((pulse, bh), pygame.SRCALPHA)
        sa   = int(55 + 35*math.sin(now*0.012))
        pygame.draw.rect(shim, (255,255,255,sa), (0, 0, pulse, bh//2))
        screen.blit(shim, (bx, by2))
    elif now - last_starpower < starpower_cooldown:
        elapsed  = now - last_starpower
        progress = elapsed / starpower_cooldown
        col      = C_GRAY
        secs_left = int((starpower_cooldown - elapsed)/1000)+1
        label    = f"COOLDOWN  {secs_left}s"
        pygame.draw.rect(screen, (18,18,28), (bx, by2, bw, bh), border_radius=5)
        pygame.draw.rect(screen, col,        (bx, by2, int(bw*progress), bh), border_radius=5)
    else:
        col   = C_ACCENT
        label = "STARPOWER  READY  [F]"
        blink = (now//600)%2
        pygame.draw.rect(screen, (28,24,8) if blink else (18,18,10), (bx, by2, bw, bh), border_radius=5)
        if blink:
            pygame.draw.rect(screen, col, (bx, by2, bw, bh), border_radius=5)

    ls = font_tiny.render(label, True, col)
    screen.blit(ls, (bx + bw//2 - ls.get_width()//2, by2+4))

    # ── Bush indicator ──
    for addr, p in server_players.items():
        if p.get("name") == my_name and in_bush(p["x"], p["y"]):
            bi = font_small.render("  IN BUSH - HIDDEN  ", True, C_GRASS2)
            bib = font_small.render("  IN BUSH - HIDDEN  ", True, C_DARK)
            screen.blit(bib, (400 - bi.get_width()//2+1, 543))
            screen.blit(bi,  (400 - bi.get_width()//2,   543))
            break

# ─── SCREEN: DEAD ─────────────────────────────────────────────────────────────
def draw_dead_screen():
    draw_game()
    ov = pygame.Surface((800, 600), pygame.SRCALPHA)
    ov.fill((0, 0, 0, 155))
    screen.blit(ov, (0, 0))
    centered("YOU  DIED", font_big, C_RED, 192)
    centered("Waiting for round to end...", font_small, C_GRAY, 272)
    centered("You will return to the lobby soon.", font_small, (75, 78, 98), 304)

# ─── SCREEN: GAME OVER ────────────────────────────────────────────────────────
go_timer = 0

def draw_game_over():
    draw_bg()
    centered("ROUND  OVER", font_big, C_ACCENT, 126)
    # Trophy polygon
    pygame.draw.polygon(screen, C_ACCENT, [
        (400,182),(416,206),(438,206),(422,222),(428,246),
        (400,230),(372,246),(378,222),(362,206),(384,206)
    ])
    centered(f"Winner:   {winner_name}", font_med, C_GREEN, 258)
    centered("Returning to lobby...", font_small, C_GRAY, 302)
    elapsed = pygame.time.get_ticks() - go_timer
    bw = int(500 * min(elapsed/4000, 1.0))
    pygame.draw.rect(screen, (28,30,50), (150, 348, 500, 14), border_radius=7)
    pygame.draw.rect(screen, C_ACCENT,  (150, 348, bw,  14), border_radius=7)

# ─── MAIN LOOP ────────────────────────────────────────────────────────────────
running       = True
brawler_rects = {}

while running:
    cur_phase = get_phase()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
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
                        send_weapon_select()
                        set_phase("playing")
                        break

        elif cur_phase == "playing":
            if event.type == pygame.KEYDOWN and event.key == pygame.K_f:
                activate_starpower()
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and my_brawler:
                now = pygame.time.get_ticks()
                st  = BRAWLERS[my_brawler]
                cd  = 40 if (starpower_active and my_brawler=="minigun") else st["cooldown"]
                if now - last_shot > cd:
                    last_shot = now
                    mx, mpy = pygame.mouse.get_pos()
                    ang = math.atan2(mpy - 300, mx - 400)
                    send({"type":"shoot","dx":math.cos(ang),"dy":math.sin(ang),
                          "speed":st["bullet_speed"],"damage":st["damage"],
                          "weapon":st["weapon"],"pierce":starpower_active and my_brawler=="sniper"})

    # Per-frame
    if cur_phase == "playing" and server_players:
        for addr, p in server_players.items():
            if p.get("name") == my_name and not p["alive"]:
                set_phase("dead_screen")
                break

    if cur_phase == "playing" and my_brawler and starpower_active and my_brawler == "minigun":
        now = pygame.time.get_ticks()
        if now - last_shot > 40:
            last_shot = now
            mx, mpy = pygame.mouse.get_pos()
            ang = math.atan2(mpy - 300, mx - 400)
            send({"type":"shoot","dx":math.cos(ang),"dy":math.sin(ang),
                  "speed":BRAWLERS["minigun"]["bullet_speed"],
                  "damage":BRAWLERS["minigun"]["damage"],"weapon":"minigun"})

    if cur_phase == "playing":
        keys = pygame.key.get_pressed()
        send({"type":"move","up":bool(keys[pygame.K_w]),"down":bool(keys[pygame.K_s]),
              "left":bool(keys[pygame.K_a]),"right":bool(keys[pygame.K_d])})

    if cur_phase == "game_over":
        if go_timer == 0:
            go_timer = pygame.time.get_ticks()
        if pygame.time.get_ticks() - go_timer > 4000:
            go_timer = 0; my_brawler = None
            set_phase("lobby"); join_lobby()

    if cur_phase == "lobby":
        now_ms = pygame.time.get_ticks()
        if now_ms - getattr(draw_lobby, "_last_hb", 0) > 1000:
            draw_lobby._last_hb = now_ms
            join_lobby()

    # Draw
    cur_phase = get_phase()
    if   cur_phase == "name_entry":    draw_name_entry()
    elif cur_phase == "lobby":         draw_lobby()
    elif cur_phase == "brawler_select":brawler_rects = draw_brawler_select()
    elif cur_phase == "playing":       draw_game()
    elif cur_phase == "dead_screen":   draw_dead_screen()
    elif cur_phase == "game_over":     draw_game_over()

    pygame.display.flip()
    clock.tick(60)

pygame.quit()