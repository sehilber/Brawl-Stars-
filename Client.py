import socket
import threading
import json
import pygame
import math
import os

SERVER_IP = "192.168.0.101"
PORT = 5555

client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

pygame.init()
pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)

# ─── FULLSCREEN SETUP ─────────────────────────────────────────────────────────
GAME_TITLE = "Brawl Stars"

info = pygame.display.Info()
SCREEN_W = info.current_w
SCREEN_H = info.current_h
screen = pygame.display.set_mode((SCREEN_W, SCREEN_H), pygame.FULLSCREEN)
pygame.display.set_caption(GAME_TITLE)
clock = pygame.time.Clock()

MAP_W = 3840
MAP_H = 2160

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
font_huge  = pygame.font.SysFont("impact", 72, bold=False)
font_big   = pygame.font.SysFont("impact", 52, bold=False)
font_med   = pygame.font.SysFont("consolas", 28, bold=False)
font_small = pygame.font.SysFont("consolas", 20)
font_tiny  = pygame.font.SysFont("consolas", 15)

# ─── COLORS ───────────────────────────────────────────────────────────────────
C_BG       = (10,  12,  20)
C_PANEL    = (18,  22,  38)
C_PANEL2   = (24,  28,  48)
C_ACCENT   = (255, 200,  30)
C_ACCENT2  = (255, 140,  20)
C_BLUE     = (60,  140, 255)
C_GREEN    = (50,  220, 100)
C_RED      = (255,  60,  60)
C_PURPLE   = (180,  70, 255)
C_GRAY     = (100, 108, 130)
C_WHITE    = (240, 244, 255)
C_DARK     = ( 6,   7,  13)
C_GRASS    = ( 30,  80,  30)
C_GRASS2   = ( 42, 105,  42)

# ─── SOUND SYSTEM ─────────────────────────────────────────────────────────────
SOUND_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sounds")
sounds = {}

def load_sound(name, filename, volume=1.0):
    path = os.path.join(SOUND_DIR, filename)
    if not os.path.exists(path):
        sounds[name] = None; return
    try:
        snd = pygame.mixer.Sound(path)
        snd.set_volume(volume)
        sounds[name] = snd
    except:
        sounds[name] = None

def play_sound(name):
    snd = sounds.get(name)
    if snd: snd.play()

def play_music(name, loops=-1):
    snd = sounds.get(name)
    if snd:
        pygame.mixer.stop()
        snd.play(loops=loops)

def stop_music():
    pygame.mixer.stop()

load_sound("startup", "ps4-startup.mp3",                                                             volume=0.7)
load_sound("menu",    "brawl-stars-menu-start-sounds-sound-effect-brawl-stars-hd-sound-effects_01web.mp3", volume=0.5)
load_sound("shoot",   "gun-sniper-rifle-shot.mp3",                                                   volume=0.5)
load_sound("hit",     "fortnite-shield-break-sound__1_.mp3",                                         volume=0.7)
load_sound("death",   "fortnite-death-sound.mp3",                                                    volume=0.8)

# ─── BUSHES ───────────────────────────────────────────────────────────────────
BUSHES = [
    {"x": 300,  "y": 200,  "r": 40}, {"x": 380,  "y": 220,  "r": 32},
    {"x": 200,  "y": 460,  "r": 28}, {"x": 260,  "y": 760,  "r": 36},
    {"x": 520,  "y": 610,  "r": 30}, {"x": 1100, "y": 180,  "r": 38},
    {"x": 1170, "y": 210,  "r": 30}, {"x": 1680, "y": 310,  "r": 32},
    {"x": 1500, "y": 700,  "r": 38}, {"x": 760,  "y": 490,  "r": 34},
    {"x": 820,  "y": 520,  "r": 28}, {"x": 960,  "y": 900,  "r": 34},
    {"x": 1350, "y": 830,  "r": 36}, {"x": 1760, "y": 810,  "r": 36},
    {"x": 2200, "y": 200,  "r": 40}, {"x": 2300, "y": 240,  "r": 32},
    {"x": 2500, "y": 460,  "r": 36}, {"x": 2650, "y": 700,  "r": 30},
    {"x": 3000, "y": 300,  "r": 38}, {"x": 3100, "y": 180,  "r": 34},
    {"x": 3400, "y": 420,  "r": 32}, {"x": 3600, "y": 200,  "r": 40},
    {"x": 3700, "y": 600,  "r": 30}, {"x": 300,  "y": 1200, "r": 40},
    {"x": 500,  "y": 1400, "r": 32}, {"x": 800,  "y": 1300, "r": 36},
    {"x": 1100, "y": 1600, "r": 34}, {"x": 1500, "y": 1200, "r": 30},
    {"x": 1800, "y": 1500, "r": 38}, {"x": 2000, "y": 1100, "r": 36},
    {"x": 2200, "y": 1400, "r": 32}, {"x": 2600, "y": 1300, "r": 40},
    {"x": 2900, "y": 1600, "r": 34}, {"x": 3200, "y": 1200, "r": 30},
    {"x": 3500, "y": 1400, "r": 36}, {"x": 3700, "y": 1800, "r": 32},
    {"x": 960,  "y": 1900, "r": 34}, {"x": 1920, "y": 1080, "r": 40},
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
        "emoji": "🎯",
        "desc":  "Long range, high damage.",
        "star":  "Piercing bullets!",
        "tag":   "MARKSMAN",
    },
    "minigun": {
        "weapon": "minigun", "cooldown": 100, "bullet_speed": 10, "damage": 10,
        "color":  (255, 130, 40), "accent": (255, 210, 100),
        "emoji": "🔥",
        "desc":  "Rapid fire spray.",
        "star":  "Insane fire rate!",
        "tag":   "SHARPSHOOTER",
    },
    "mage": {
        "weapon": "magic",   "cooldown": 400, "bullet_speed": 14, "damage": 35,
        "color":  (180, 70, 255), "accent": (220, 160, 255),
        "emoji": "✨",
        "desc":  "Magic projectiles.",
        "star":  "Turn invisible!",
        "tag":   "MYSTIC",
    },
}

WEAPON_TO_BRAWLER = {"sniper": "sniper", "minigun": "minigun", "magic": "mage", "ak47": "sniper"}

# ─── PARTICLE SYSTEM ──────────────────────────────────────────────────────────
particles = []

def spawn_particles(x, y, color, count=8, speed=3):
    for _ in range(count):
        ang = math.radians(360 * _ / count + (pygame.time.get_ticks() % 360))
        spd = speed * (0.5 + 0.5 * (_ % 3) / 3)
        particles.append({
            "x": x, "y": y,
            "dx": math.cos(ang) * spd,
            "dy": math.sin(ang) * spd,
            "life": 1.0, "decay": 0.035,
            "r": 4, "color": color,
        })

def update_draw_particles(surf):
    for p in particles[:]:
        p["x"] += p["dx"]
        p["y"] += p["dy"]
        p["life"] -= p["decay"]
        p["dy"] += 0.08
        if p["life"] <= 0:
            particles.remove(p)
            continue
        a = int(p["life"] * 255)
        r = max(1, int(p["r"] * p["life"]))
        s = pygame.Surface((r*2, r*2), pygame.SRCALPHA)
        pygame.draw.circle(s, (*p["color"], a), (r, r), r)
        surf.blit(s, (int(p["x"]) - r, int(p["y"]) - r))

# ─── DRAW BRAWLER SHAPE ───────────────────────────────────────────────────────
def draw_brawler(surf, brawler_name, x, y, alpha=255, scale=1.0, starpower=False, alive=True):
    bdata  = BRAWLERS.get(brawler_name, BRAWLERS["sniper"])
    color  = (80, 80, 90) if not alive else bdata["color"]
    accent = (60, 60, 70) if not alive else bdata["accent"]
    r      = int(14 * scale)
    tmp    = pygame.Surface((80, 80), pygame.SRCALPHA)
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

phase      = "startup"
phase_lock = threading.Lock()

my_name           = ""
my_brawler        = "sniper"   # default; changeable in lobby
lobby_data        = {}         # full lobby state from server
winner_name       = ""
was_kicked        = False
spectate_msg      = ""

# Animation state
lobby_anim_t      = 0
selected_brawler  = "sniper"   # local selection in lobby
ready_local       = False      # local ready state
last_ready_send   = 0

def set_phase(p):
    global phase
    with phase_lock:
        phase = p

def get_phase():
    with phase_lock:
        return phase

# ─── STARTUP ──────────────────────────────────────────────────────────────────
startup_done  = False
startup_start = pygame.time.get_ticks()

def check_startup():
    global startup_done
    if startup_done: return
    if pygame.time.get_ticks() - startup_start > 4500:
        startup_done = True
        set_phase("name_entry")
        play_music("menu")

# ─── NETWORK ──────────────────────────────────────────────────────────────────
def receive():
    global server_players, server_bullets, server_walls
    global lobby_data, winner_name, was_kicked, spectate_msg
    global ready_local

    while True:
        try:
            data, _ = client.recvfrom(65535)
            msg = json.loads(data.decode())
            p_msg = msg.get("phase", "")

            if p_msg == "kicked":
                was_kicked = True
                ready_local = False
                set_phase("lobby")
                play_music("menu")
                server_players = {}; server_bullets = []

            elif p_msg == "lobby":
                lobby_data = msg
                # If we were in game and now game is done, switch to lobby view
                cur = get_phase()
                if cur in ("dead_screen", "brawler_select"):
                    # Round ended while we were dead/selecting
                    pass

            elif p_msg == "lobby_spectate":
                spectate_msg = msg.get("msg", "")
                lobby_data = {}
                set_phase("lobby")
                play_music("menu")

            elif p_msg == "start":
                cur = get_phase()
                if cur in ("lobby", "name_entry", "brawler_select"):
                    my_brawler_to_use = selected_brawler
                    set_phase("playing")
                    stop_music()

            elif p_msg == "running":
                prev_alive = {addr: p.get("alive", True) for addr, p in server_players.items()}
                server_players = msg.get("players", {})
                server_bullets = msg.get("bullets", [])
                server_walls   = msg.get("walls", [])

                # Death detection
                for addr, p in server_players.items():
                    if addr in prev_alive and prev_alive[addr] and not p.get("alive", True):
                        if p.get("name") == my_name:
                            play_sound("death")

                # Am I dead?
                cur = get_phase()
                if cur == "playing":
                    for addr, p in server_players.items():
                        if p.get("name") == my_name and not p.get("alive", True):
                            set_phase("dead_screen")
                            break

            elif p_msg == "game_over":
                winner_name = msg.get("winner", "Nobody")
                ready_local = False
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

def send_brawler_select(bname):
    weapon = BRAWLERS[bname]["weapon"]
    send({"type": "brawler_select", "brawler": bname, "weapon": weapon})

def send_ready(state):
    send({"type": "set_ready", "ready": state})

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
def draw_panel(surf, x, y, w, h, color=None, border=None, radius=10, alpha=255):
    if color is None: color = C_PANEL
    if border is None: border = C_ACCENT
    if alpha < 255:
        s = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.rect(s, (*color, alpha), (0, 0, w, h), border_radius=radius)
        pygame.draw.rect(s, (*border, min(255, alpha+40)), (0, 0, w, h), 2, border_radius=radius)
        surf.blit(s, (x, y))
    else:
        pygame.draw.rect(surf, color,  (x, y, w, h), border_radius=radius)
        pygame.draw.rect(surf, border, (x, y, w, h), 2, border_radius=radius)

def centered(text, font, color, cy, x=None, shadow=True, surf=None):
    if surf is None: surf = screen
    if x is None: x = SCREEN_W // 2
    if shadow:
        s = font.render(text, True, C_DARK)
        surf.blit(s, (x - s.get_width()//2 + 2, cy + 2))
    s = font.render(text, True, color)
    surf.blit(s, (x - s.get_width()//2, cy))

def draw_bg_grid():
    screen.fill(C_BG)
    t = pygame.time.get_ticks() * 0.0003
    for i in range(0, SCREEN_W, 60):
        alpha = int(15 + 8 * math.sin(i * 0.05 + t))
        pygame.draw.line(screen, (alpha, alpha+4, alpha+14), (i, 0), (i, SCREEN_H))
    for j in range(0, SCREEN_H, 60):
        alpha = int(15 + 8 * math.sin(j * 0.05 + t))
        pygame.draw.line(screen, (alpha, alpha+4, alpha+14), (0, j), (SCREEN_W, j))

def draw_floating_stars(t):
    """Draw animated star particles in the background."""
    for i in range(18):
        x = (SCREEN_W * ((i * 173 + 50) % 997) // 997)
        y_base = (SCREEN_H * ((i * 293 + 100) % 883) // 883)
        y = y_base + int(12 * math.sin(t * 0.8 + i * 0.7))
        a = int(60 + 40 * math.sin(t * 1.2 + i * 1.1))
        r = 2 + (i % 3)
        s = pygame.Surface((r*2+2, r*2+2), pygame.SRCALPHA)
        pygame.draw.circle(s, (255, 220, 80, a), (r+1, r+1), r)
        screen.blit(s, (x - r - 1, y - r - 1))

# ─── SCREEN: STARTUP ──────────────────────────────────────────────────────────
def draw_startup():
    screen.fill((0, 0, 0))
    now = pygame.time.get_ticks()
    elapsed = now - startup_start

    # Background pulse
    pulse = int(8 + 6 * math.sin(elapsed * 0.003))
    bg_surf = pygame.Surface((SCREEN_W, SCREEN_H))
    bg_surf.fill((pulse, pulse//2, 0))
    screen.blit(bg_surf, (0, 0))

    # Radiating rings
    for i in range(5):
        r = int(50 + i * 80 + (elapsed * 0.06) % 400)
        a = max(0, 120 - i * 22 - int((elapsed * 0.06) % 400) // 4)
        s = pygame.Surface((r*2, r*2), pygame.SRCALPHA)
        pygame.draw.circle(s, (255, 200, 30, a), (r, r), r, 2)
        screen.blit(s, (SCREEN_W//2 - r, SCREEN_H//2 - r))

    alpha = min(255, int(elapsed / 1200 * 255))
    alpha = min(alpha, max(0, int((4500 - elapsed) / 600 * 255)))

    # Main logo with outline effect
    for dx2, dy2 in [(-3,0),(3,0),(0,-3),(0,3)]:
        s = font_huge.render(GAME_TITLE, True, (40, 20, 0))
        tmp = pygame.Surface(s.get_size(), pygame.SRCALPHA)
        tmp.blit(s, (0, 0)); tmp.set_alpha(alpha)
        screen.blit(tmp, (SCREEN_W//2 - s.get_width()//2 + dx2, SCREEN_H//2 - s.get_height()//2 + dy2))

    s = font_huge.render(GAME_TITLE, True, C_ACCENT)
    tmp = pygame.Surface(s.get_size(), pygame.SRCALPHA)
    tmp.blit(s, (0, 0)); tmp.set_alpha(alpha)
    screen.blit(tmp, (SCREEN_W//2 - s.get_width()//2, SCREEN_H//2 - s.get_height()//2))

    # Subtitle
    if elapsed > 1500:
        sub_a = min(255, int((elapsed - 1500) / 800 * 255))
        sub_a = min(sub_a, alpha)
        s2 = font_small.render("THE ULTIMATE ARENA EXPERIENCE", True, C_ACCENT2)
        tmp2 = pygame.Surface(s2.get_size(), pygame.SRCALPHA)
        tmp2.blit(s2, (0, 0)); tmp2.set_alpha(sub_a)
        screen.blit(tmp2, (SCREEN_W//2 - s2.get_width()//2, SCREEN_H//2 + 60))

# ─── SCREEN: NAME ENTRY ───────────────────────────────────────────────────────
name_input = ""

def draw_name_entry():
    draw_bg_grid()
    t = pygame.time.get_ticks() * 0.001
    draw_floating_stars(t)

    cx = SCREEN_W // 2

    # Title banner
    banner_h = 110
    banner = pygame.Surface((SCREEN_W, banner_h), pygame.SRCALPHA)
    for i in range(banner_h):
        a = int(200 * (1 - i / banner_h))
        pygame.draw.line(banner, (10, 12, 30, a), (0, i), (SCREEN_W, i))
    screen.blit(banner, (0, 0))
    pygame.draw.line(screen, C_ACCENT, (0, banner_h), (SCREEN_W, banner_h), 2)

    # Animated title
    shake = int(2 * math.sin(t * 3))
    centered(GAME_TITLE, font_big, C_ACCENT, 22 + shake)
    centered("SELECT YOUR NAME", font_small, C_GRAY, 82)

    # Brawler preview row
    for i, (bname, bdata) in enumerate(BRAWLERS.items()):
        bx = cx - 180 + i * 190
        by = 135
        # Hover glow
        bob = int(6 * math.sin(t * 2 + i * 1.2))
        preview = pygame.Surface((70, 70), pygame.SRCALPHA)
        draw_brawler(preview, bname, 35, 35, scale=2.0)
        screen.blit(preview, (bx - 35, by + bob))
        s = font_tiny.render(bname.upper(), True, bdata["color"])
        screen.blit(s, (bx - s.get_width()//2, by + 52 + bob))

    # Input panel
    panel_x = cx - 220
    draw_panel(screen, panel_x, 220, 440, 60, color=(16, 20, 36), border=C_BLUE, radius=12)
    cursor = "|" if (pygame.time.get_ticks()//500)%2 else " "
    disp = name_input + cursor if name_input else cursor
    if not name_input:
        ph = font_med.render("Enter your name...", True, (55, 65, 90))
        screen.blit(ph, (cx - ph.get_width()//2, 233))
    else:
        s = font_med.render(disp, True, C_WHITE)
        screen.blit(s, (cx - s.get_width()//2, 233))

    # Enter hint
    if name_input.strip():
        pulse_a = int(180 + 70 * math.sin(t * 4))
        hint_col = (min(255, C_GREEN[0]), min(255, C_GREEN[1] - 30 + pulse_a//8), min(255, C_GREEN[2]))
        draw_panel(screen, cx - 120, 300, 240, 46, color=(8, 28, 14), border=C_GREEN, radius=10)
        centered("PRESS ENTER  ▶", font_small, C_GREEN, 314)
    else:
        centered("Type your name to join", font_tiny, C_GRAY, 312)

    centered("ESC to quit", font_tiny, (50, 55, 75), 368)

# ─── LOBBY SCREEN ─────────────────────────────────────────────────────────────
# Layout: left = player list, center = brawler cards, right = status/ready

lobby_hover_brawler = None   # which card is hovered

def draw_lobby():
    global lobby_hover_brawler
    draw_bg_grid()
    t = pygame.time.get_ticks() * 0.001
    draw_floating_stars(t)

    cx = SCREEN_W // 2
    now_ms = pygame.time.get_ticks()

    ld = lobby_data  # current lobby state from server

    # ── HEADER ──
    pygame.draw.rect(screen, (8, 10, 22), (0, 0, SCREEN_W, 80))
    pygame.draw.line(screen, C_ACCENT, (0, 80), (SCREEN_W, 80), 2)

    # Animated title
    shake = int(1.5 * math.sin(t * 2.5))
    centered(GAME_TITLE, font_big, C_ACCENT, 8 + shake)

    game_running = ld.get("game_running", False)
    if game_running:
        status_txt = "⚔  GAME IN PROGRESS  —  Waiting for next round..."
        status_col = C_RED
    else:
        ready_c   = ld.get("ready_count", 0)
        total_a   = ld.get("total_active", 0)
        can_start = ld.get("can_start", False)
        if total_a < 2:
            status_txt = f"Waiting for players...  ({total_a}/2 minimum)"
            status_col = C_GRAY
        elif can_start:
            status_txt = "✅  All ready! Starting now..."
            status_col = C_GREEN
        else:
            status_txt = f"Ready up!  ({ready_c}/{total_a} ready)"
            status_col = C_ACCENT

    centered(status_txt, font_small, status_col, 52)

    # ── LAYOUT PANELS ──
    left_w   = 280
    right_w  = 260
    center_w = SCREEN_W - left_w - right_w - 40
    left_x   = 10
    right_x  = SCREEN_W - right_w - 10
    center_x = left_x + left_w + 10
    panel_y  = 92
    panel_h  = SCREEN_H - panel_y - 10

    # ── LEFT: Player list ──
    draw_panel(screen, left_x, panel_y, left_w, panel_h,
               color=(12, 14, 26), border=(30, 36, 60), radius=12)

    s = font_small.render("PLAYERS", True, C_ACCENT)
    screen.blit(s, (left_x + 14, panel_y + 14))
    lobby_ps = ld.get("lobby_players", [])
    pc = font_tiny.render(f"{len(lobby_ps)} / 10", True, C_GRAY)
    screen.blit(pc, (left_x + left_w - pc.get_width() - 12, panel_y + 17))
    pygame.draw.line(screen, (30, 34, 60), (left_x + 10, panel_y + 40),
                     (left_x + left_w - 10, panel_y + 40), 1)

    for i, pdata in enumerate(lobby_ps[:10]):
        ry = panel_y + 50 + i * 48
        if ry + 46 > panel_y + panel_h - 6:
            break

        is_me     = pdata.get("name") == my_name
        is_ready  = pdata.get("ready", False)
        is_spec   = pdata.get("spectating", False)
        bname_p   = pdata.get("brawler", "sniper")
        bdata_p   = BRAWLERS.get(bname_p, BRAWLERS["sniper"])

        row_col  = (20, 24, 48) if is_me else (14, 16, 34)
        row_bdr  = bdata_p["color"] if is_me else (30, 34, 58)
        pygame.draw.rect(screen, row_col, (left_x + 6, ry, left_w - 12, 42), border_radius=8)
        pygame.draw.rect(screen, row_bdr, (left_x + 6, ry, left_w - 12, 42), 1, border_radius=8)

        # Mini brawler icon
        icon = pygame.Surface((44, 44), pygame.SRCALPHA)
        draw_brawler(icon, bname_p, 22, 22, scale=1.1)
        screen.blit(icon, (left_x + 8, ry))

        # Name
        nc = C_ACCENT if is_me else C_WHITE
        ns = font_tiny.render(pdata.get("name", "?"), True, nc)
        screen.blit(ns, (left_x + 54, ry + 6))

        # Status tag
        if is_spec:
            tag_col = C_GRAY
            tag_txt = "SPECTATING"
        elif is_ready:
            tag_col = C_GREEN
            tag_txt = "✓ READY"
        else:
            tag_col = (120, 110, 50)
            tag_txt = "NOT READY"
        ts = font_tiny.render(tag_txt, True, tag_col)
        screen.blit(ts, (left_x + 54, ry + 24))

    # ── CENTER: Brawler selection ──
    draw_panel(screen, center_x, panel_y, center_w, panel_h,
               color=(10, 12, 24), border=(28, 32, 58), radius=12)
    centered("CHOOSE YOUR BRAWLER", font_med, C_WHITE, panel_y + 16, x=center_x + center_w//2)

    brawler_names = list(BRAWLERS.keys())
    card_w  = min(200, (center_w - 40) // len(brawler_names) - 12)
    card_h  = min(320, panel_h - 80)
    cards_total_w = len(brawler_names) * card_w + (len(brawler_names)-1) * 14
    card_start_x  = center_x + (center_w - cards_total_w) // 2
    card_y  = panel_y + 52

    mx_now, my_now = pygame.mouse.get_pos()
    brawler_rects  = {}
    hover_b        = None

    for i, bname in enumerate(brawler_names):
        bdata = BRAWLERS[bname]
        bx    = card_start_x + i * (card_w + 14)
        hov   = bx <= mx_now <= bx + card_w and card_y <= my_now <= card_y + card_h
        sel   = (selected_brawler == bname)

        if hov: hover_b = bname
        brawler_rects[bname] = (bx, card_y, card_w, card_h)

        # Card background
        if sel:
            bg_col  = (28, 22, 50)
            bdr_col = bdata["color"]
            bdr_w   = 3
        elif hov:
            bg_col  = (22, 20, 44)
            bdr_col = bdata["accent"]
            bdr_w   = 2
        else:
            bg_col  = (14, 16, 32)
            bdr_col = (32, 36, 64)
            bdr_w   = 1

        # Glow for selected
        if sel:
            glow = pygame.Surface((card_w + 20, card_h + 20), pygame.SRCALPHA)
            gc   = bdata["color"]
            ga   = int(40 + 20 * math.sin(t * 3))
            pygame.draw.rect(glow, (*gc, ga), (0, 0, card_w+20, card_h+20), border_radius=14)
            screen.blit(glow, (bx - 10, card_y - 10))

        pygame.draw.rect(screen, bg_col,  (bx, card_y, card_w, card_h), border_radius=12)
        pygame.draw.rect(screen, bdr_col, (bx, card_y, card_w, card_h), bdr_w, border_radius=12)

        # Brawler art
        bob = int(5 * math.sin(t * 2 + i * 1.1)) if (hov or sel) else 0
        art = pygame.Surface((100, 100), pygame.SRCALPHA)
        draw_brawler(art, bname, 50, 50, scale=2.6, starpower=sel)
        screen.blit(art, (bx + card_w//2 - 50, card_y + 16 + bob))

        # Tag badge
        tag_s = font_tiny.render(bdata["tag"], True, bdata["color"])
        tb_x  = bx + card_w//2 - tag_s.get_width()//2 - 6
        pygame.draw.rect(screen, (10, 8, 20), (tb_x, card_y+108, tag_s.get_width()+12, 20), border_radius=4)
        screen.blit(tag_s, (tb_x + 6, card_y + 109))

        # Name
        ns = font_med.render(bname.upper(), True, bdata["color"] if (hov or sel) else C_WHITE)
        screen.blit(ns, (bx + card_w//2 - ns.get_width()//2, card_y + 132))

        pygame.draw.line(screen, (28, 32, 60), (bx + 12, card_y + 162), (bx + card_w - 12, card_y + 162), 1)

        # Stats
        stats = [("DMG", str(bdata["damage"])), ("SPD", str(bdata["bullet_speed"])), ("CD", f"{bdata['cooldown']}ms")]
        for j, (lbl, val) in enumerate(stats):
            ls = font_tiny.render(lbl, True, C_GRAY)
            vs = font_tiny.render(val, True, C_WHITE)
            screen.blit(ls, (bx + 12, card_y + 172 + j * 22))
            screen.blit(vs, (bx + card_w - vs.get_width() - 12, card_y + 172 + j * 22))

        # Desc
        desc_y = card_y + 172 + 3*22 + 6
        pygame.draw.line(screen, (28, 32, 60), (bx + 12, desc_y), (bx + card_w - 12, desc_y), 1)
        ds = font_tiny.render(bdata["desc"], True, C_GRAY)
        screen.blit(ds, (bx + card_w//2 - ds.get_width()//2, desc_y + 6))
        star_s = font_tiny.render("★ " + bdata["star"], True, C_ACCENT)
        screen.blit(star_s, (bx + card_w//2 - star_s.get_width()//2, desc_y + 24))

        # Selected badge
        if sel:
            sel_s = font_tiny.render("✓ SELECTED", True, C_GREEN)
            screen.blit(sel_s, (bx + card_w//2 - sel_s.get_width()//2, card_y + card_h - 22))

    lobby_hover_brawler = hover_b

    # ── RIGHT: Ready panel ──
    draw_panel(screen, right_x, panel_y, right_w, panel_h,
               color=(10, 12, 24), border=(28, 32, 58), radius=12)

    # Current brawler summary
    cur_bdata = BRAWLERS.get(selected_brawler, BRAWLERS["sniper"])
    art2 = pygame.Surface((100, 100), pygame.SRCALPHA)
    draw_brawler(art2, selected_brawler, 50, 50, scale=2.6, starpower=ready_local)
    screen.blit(art2, (right_x + right_w//2 - 50, panel_y + 16))

    bname_s = font_med.render(selected_brawler.upper(), True, cur_bdata["color"])
    screen.blit(bname_s, (right_x + right_w//2 - bname_s.get_width()//2, panel_y + 114))

    # Kicked / spectating notice
    if was_kicked:
        centered("You were kicked!", font_small, C_RED, panel_y + 152, x=right_x + right_w//2)
        centered("Wait for next game.", font_tiny, C_GRAY, panel_y + 176, x=right_x + right_w//2)
        return brawler_rects

    spec_self = False
    for lp in lobby_data.get("lobby_players", []):
        if lp.get("name") == my_name and lp.get("spectating", False):
            spec_self = True

    if spec_self or game_running:
        centered("SPECTATING", font_med, C_GRAY, panel_y + 152, x=right_x + right_w//2)
        centered("Waiting for next round", font_tiny, (90, 95, 110), panel_y + 180, x=right_x + right_w//2)
        # Animated dots
        dots = "." * (1 + (now_ms // 500) % 3)
        ds2 = font_small.render(dots, True, C_GRAY)
        screen.blit(ds2, (right_x + right_w//2 - ds2.get_width()//2, panel_y + 204))
        return brawler_rects

    # Ready button
    btn_y   = panel_y + 158
    btn_x   = right_x + 16
    btn_w   = right_w - 32
    btn_h   = 56

    btn_hov = btn_x <= mx_now <= btn_x + btn_w and btn_y <= my_now <= btn_y + btn_h

    if ready_local:
        btn_col = (8, 38, 16)
        btn_bdr = C_GREEN
        btn_txt = "✓  READY!"
        btn_tc  = C_GREEN
    else:
        pulse_b = int(40 * math.sin(now_ms * 0.005))
        btn_col = (28 + pulse_b//4, 24, 8)
        btn_bdr = C_ACCENT
        btn_txt = "READY UP  ▶"
        btn_tc  = C_ACCENT

    if btn_hov:
        btn_col = tuple(min(255, c + 15) for c in btn_col)

    pygame.draw.rect(screen, btn_col, (btn_x, btn_y, btn_w, btn_h), border_radius=12)
    pygame.draw.rect(screen, btn_bdr, (btn_x, btn_y, btn_w, btn_h), 2, border_radius=12)
    bs = font_med.render(btn_txt, True, btn_tc)
    screen.blit(bs, (btn_x + btn_w//2 - bs.get_width()//2, btn_y + btn_h//2 - bs.get_height()//2))

    # Progress toward all ready
    pygame.draw.line(screen, (24, 28, 50), (right_x + 14, panel_y + 228), (right_x + right_w - 14, panel_y + 228), 1)
    rc   = ld.get("ready_count", 0)
    ta   = max(1, ld.get("total_active", 1))
    prog = rc / ta
    bar_bx = right_x + 14
    bar_bw = right_w - 28
    pygame.draw.rect(screen, (20, 22, 40), (bar_bx, panel_y + 236, bar_bw, 14), border_radius=7)
    pygame.draw.rect(screen, C_GREEN,      (bar_bx, panel_y + 236, int(bar_bw * prog), 14), border_radius=7)
    prog_s = font_tiny.render(f"{rc}/{ta} ready", True, C_GRAY)
    screen.blit(prog_s, (right_x + right_w//2 - prog_s.get_width()//2, panel_y + 254))

    if ta < 2:
        need_s = font_tiny.render("Need 2+ players to start", True, (90, 80, 50))
        screen.blit(need_s, (right_x + right_w//2 - need_s.get_width()//2, panel_y + 272))

    # My info
    pygame.draw.line(screen, (24, 28, 50), (right_x + 14, panel_y + panel_h - 70),
                     (right_x + right_w - 14, panel_y + panel_h - 70), 1)
    me_s = font_tiny.render(f"You:  {my_name}", True, C_BLUE)
    screen.blit(me_s, (right_x + right_w//2 - me_s.get_width()//2, panel_y + panel_h - 58))
    tip_s = font_tiny.render("ESC to quit", True, (50, 55, 75))
    screen.blit(tip_s, (right_x + right_w//2 - tip_s.get_width()//2, panel_y + panel_h - 34))

    return brawler_rects

# ─── SCREEN: DEAD / SPECTATING ────────────────────────────────────────────────
def draw_dead_screen():
    draw_game()
    ov = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
    ov.fill((0, 0, 0, 160))
    screen.blit(ov, (0, 0))

    t  = pygame.time.get_ticks() * 0.001
    cy = SCREEN_H // 2 - 90

    # Animated skull icon
    skull_bob = int(8 * math.sin(t * 2))
    skull_s = font_huge.render("💀", True, C_RED)
    screen.blit(skull_s, (SCREEN_W//2 - skull_s.get_width()//2, cy + skull_bob))

    centered("YOU  DIED", font_big, C_RED, cy + 90)

    pygame.draw.line(screen, (80, 20, 20), (SCREEN_W//2 - 200, cy + 148), (SCREEN_W//2 + 200, cy + 148), 1)

    centered("Spectating until the round ends...", font_small, C_GRAY, cy + 160)
    centered("You'll return to the lobby when it's over.", font_small, (75, 78, 98), cy + 192)

    # Watching who's left
    alive_ps = [p for p in server_players.values() if p.get("alive", True) and not p.get("spectating", False)]
    if alive_ps:
        centered(f"⚔  {len(alive_ps)} player{'s' if len(alive_ps)>1 else ''} still fighting...", font_small, C_ACCENT, cy + 232)
    else:
        centered("Round ending...", font_small, C_GREEN, cy + 232)

# ─── SCREEN: GAME OVER ────────────────────────────────────────────────────────
go_timer = 0

def draw_game_over():
    draw_bg_grid()
    t = pygame.time.get_ticks() * 0.001
    draw_floating_stars(t)
    cx = SCREEN_W // 2
    cy = SCREEN_H // 2 - 160

    # Trophy
    now_ms = pygame.time.get_ticks()
    trophy_bob = int(10 * math.sin(t * 2))
    for dx2, dy2 in [(-2,0),(2,0),(0,-2),(0,2)]:
        s = font_huge.render("🏆", True, (60, 40, 0))
        screen.blit(s, (cx - s.get_width()//2 + dx2, cy + trophy_bob + dy2))
    trophy_s = font_huge.render("🏆", True, C_ACCENT)
    screen.blit(trophy_s, (cx - trophy_s.get_width()//2, cy + trophy_bob))

    centered("ROUND  OVER!", font_big, C_ACCENT, cy + 80)

    pygame.draw.line(screen, (60, 50, 10), (cx - 240, cy + 130), (cx + 240, cy + 130), 1)

    centered("WINNER", font_small, C_GRAY, cy + 142)
    centered(winner_name, font_big, C_GREEN, cy + 166)

    # Returning bar
    elapsed = now_ms - go_timer if go_timer else 0
    bw = int(480 * min(elapsed / 4000, 1.0))
    pygame.draw.rect(screen, (20, 24, 40), (cx - 240, cy + 240, 480, 18), border_radius=9)
    pygame.draw.rect(screen, C_ACCENT,     (cx - 240, cy + 240, bw,  18), border_radius=9)
    centered("Returning to lobby...", font_small, C_GRAY, cy + 268)

    # Particle bursts
    if elapsed < 200 and elapsed > 10:
        for _ in range(3):
            px2 = cx + ((_ * 120) - 120)
            spawn_particles(px2, cy + 100, C_ACCENT, count=6, speed=4)
    update_draw_particles(screen)

# ─── GAME MAP / DRAWING ───────────────────────────────────────────────────────
def draw_bushes_back():
    for b in BUSHES:
        sx, sy = world_to_screen(b["x"], b["y"])
        r = b["r"]
        if -r < sx < SCREEN_W+r and -r < sy < SCREEN_H+r:
            pygame.draw.circle(screen, C_GRASS,  (sx, sy), r)
            pygame.draw.circle(screen, C_GRASS2, (sx, sy), int(r*0.62))

def draw_bushes_front():
    for b in BUSHES:
        sx, sy = world_to_screen(b["x"], b["y"])
        r = b["r"]
        if -r < sx < SCREEN_W+r and -r < sy < SCREEN_H+r:
            s2 = pygame.Surface((r*2+6, r*2+6), pygame.SRCALPHA)
            c2 = r+3
            pygame.draw.circle(s2, (*C_GRASS,  210), (c2, c2),             r)
            pygame.draw.circle(s2, (*C_GRASS2, 190), (c2-r//3, c2-r//3), int(r*0.54))
            pygame.draw.circle(s2, (*C_GRASS2, 170), (c2+r//4, c2-r//4), int(r*0.48))
            pygame.draw.circle(s2, (*C_GRASS,  230), (c2, c2-r//2),      int(r*0.44))
            screen.blit(s2, (sx-r-3, sy-r-3))

def draw_map_border():
    bx2, by2 = world_to_screen(0, 0)
    pygame.draw.rect(screen, (160, 50, 50), (bx2 - 4, by2 - 4, MAP_W + 8, MAP_H + 8), 4)
    if bx2 > 0:
        pygame.draw.rect(screen, (6, 6, 10), (0, 0, bx2, SCREEN_H))
    if by2 > 0:
        pygame.draw.rect(screen, (6, 6, 10), (0, 0, SCREEN_W, by2))
    right = bx2 + MAP_W
    if right < SCREEN_W:
        pygame.draw.rect(screen, (6, 6, 10), (right, 0, SCREEN_W - right, SCREEN_H))
    bottom = by2 + MAP_H
    if bottom < SCREEN_H:
        pygame.draw.rect(screen, (6, 6, 10), (0, bottom, SCREEN_W, SCREEN_H - bottom))

def draw_crosshair(mxp, myp, color):
    size, gap = 14, 5
    pygame.draw.line(screen, C_DARK, (mxp-size, myp), (mxp-gap, myp), 3)
    pygame.draw.line(screen, C_DARK, (mxp+gap,  myp), (mxp+size, myp), 3)
    pygame.draw.line(screen, C_DARK, (mxp, myp-size), (mxp, myp-gap), 3)
    pygame.draw.line(screen, C_DARK, (mxp, myp+gap),  (mxp, myp+size), 3)
    pygame.draw.line(screen, color,  (mxp-size, myp), (mxp-gap, myp), 1)
    pygame.draw.line(screen, color,  (mxp+gap,  myp), (mxp+size, myp), 1)
    pygame.draw.line(screen, color,  (mxp, myp-size), (mxp, myp-gap), 1)
    pygame.draw.line(screen, color,  (mxp, myp+gap),  (mxp, myp+size), 1)
    pygame.draw.circle(screen, color, (mxp, myp), 3, 1)

def get_my_pos():
    for addr, p in server_players.items():
        if p.get("name") == my_name:
            return float(p["x"]), float(p["y"])
    return float(MAP_W // 2), float(MAP_H // 2)

def try_shoot():
    global last_shot
    if not my_brawler: return
    now = pygame.time.get_ticks()
    st  = BRAWLERS[my_brawler]
    cd  = 40 if (starpower_active and my_brawler == "minigun") else st["cooldown"]
    if now - last_shot <= cd: return
    my_wx, my_wy = get_my_pos()
    mx_s, my_s   = pygame.mouse.get_pos()
    twx, twy = screen_to_world(mx_s, my_s)
    ang = math.atan2(twy - my_wy, twx - my_wx)
    last_shot = now
    play_sound("shoot")
    send({
        "type":   "shoot",
        "dx":     math.cos(ang),
        "dy":     math.sin(ang),
        "speed":  st["bullet_speed"],
        "damage": st["damage"],
        "weapon": st["weapon"],
        "pierce": starpower_active and my_brawler == "sniper",
    })

def draw_game():
    screen.fill((30, 38, 28))
    tile   = 48
    off_x  = int(cam_x % tile)
    off_y  = int(cam_y % tile)
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
        wx2, wy2 = world_to_screen(w["x"], w["y"])
        if wx2 + w["w"] < 0 or wx2 > SCREEN_W or wy2 + w["h"] < 0 or wy2 > SCREEN_H:
            continue
        pygame.draw.rect(screen, (65, 65, 80),    (wx2+2, wy2+2, w["w"], w["h"]))
        pygame.draw.rect(screen, (92, 92, 112),   (wx2,   wy2,   w["w"], w["h"]))
        pygame.draw.rect(screen, (128, 128, 152), (wx2,   wy2,   w["w"], w["h"]), 2)

    draw_bushes_back()

    for addr, p in server_players.items():
        px_w, py_w = p["x"], p["y"]
        px, py   = world_to_screen(int(px_w), int(py_w))
        is_me    = (p.get("name") == my_name)
        bname_p  = WEAPON_TO_BRAWLER.get(p.get("weapon", "ak47"), "sniper")
        invisible = p.get("invisible", False)
        sp_on    = p.get("starpower", False)
        alive    = p.get("alive", True)
        spec     = p.get("spectating", False)

        if spec and not is_me:
            continue

        if not is_me:
            if invisible: continue
            if in_bush(px_w, py_w): continue

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
        draw_brawler(screen, bname_p, px, py, alpha=alpha, scale=1.0,
                     starpower=sp_on and is_me, alive=alive)

        if is_me and my_brawler:
            ring = pygame.Surface((38, 38), pygame.SRCALPHA)
            rc2  = BRAWLERS[my_brawler]["color"]
            pygame.draw.circle(ring, (*rc2, 140), (19, 19), 18, 2)
            screen.blit(ring, (px-19, py-19))

        if not alive: continue

        nc = C_ACCENT if is_me else C_WHITE
        ns_sh = font_tiny.render(p.get("name","?"), True, C_DARK)
        ns    = font_tiny.render(p.get("name","?"), True, nc)
        screen.blit(ns_sh, (px - ns.get_width()//2+1, py-36+1))
        screen.blit(ns,    (px - ns.get_width()//2,   py-36))

        hp_pct = max(0, p["hp"] / 100)
        hp_col = C_GREEN if hp_pct > 0.5 else (C_ACCENT if hp_pct > 0.25 else C_RED)
        pygame.draw.rect(screen, (35, 8, 8),  (px-18, py-26, 36, 5), border_radius=2)
        pygame.draw.rect(screen, hp_col,      (px-18, py-26, int(36*hp_pct), 5), border_radius=2)

        if sp_on:
            now_t = pygame.time.get_ticks()
            gr    = int(18 + 3*math.sin(now_t*0.006))
            gs    = pygame.Surface((gr*2+4, gr*2+4), pygame.SRCALPHA)
            sc2   = BRAWLERS.get(bname_p, BRAWLERS["sniper"])["accent"]
            pygame.draw.circle(gs, (*sc2, 55), (gr+2, gr+2), gr)
            screen.blit(gs, (px-gr-2, py-gr-2))

    for b in server_bullets:
        bx2, by2 = world_to_screen(int(b["x"]), int(b["y"]))
        if bx2 < -20 or bx2 > SCREEN_W+20 or by2 < -20 or by2 > SCREEN_H+20:
            continue
        pierce = b.get("pierce", False)
        col    = (255, 80, 80) if pierce else (255, 215, 50)
        size   = 6 if pierce else 5
        pygame.draw.circle(screen, col, (bx2, by2), size)
        gs2 = pygame.Surface((22, 22), pygame.SRCALPHA)
        pygame.draw.circle(gs2, (*col, 55), (11, 11), 10)
        screen.blit(gs2, (bx2-11, by2-11))

    draw_bushes_front()
    draw_hud()

    mxp, myp = pygame.mouse.get_pos()
    ch_col = BRAWLERS[my_brawler]["color"] if my_brawler else C_WHITE
    draw_crosshair(mxp, myp, ch_col)

def draw_hud():
    now_ms = pygame.time.get_ticks()
    if not my_brawler: return
    bdata = BRAWLERS[my_brawler]
    cxh   = SCREEN_W // 2

    # Brawler badge
    draw_panel(screen, 6, 6, 210, 64, color=(10,12,22), border=(32,36,58))
    badge = pygame.Surface((80, 80), pygame.SRCALPHA)
    draw_brawler(badge, my_brawler, 40, 40, scale=1.3)
    screen.blit(badge, (10, 2))
    s1 = font_small.render(my_brawler.upper(), True, bdata["color"])
    screen.blit(s1, (68, 14))
    s2 = font_tiny.render("[F] Starpower | ESC quit", True, C_GRAY)
    screen.blit(s2, (68, 38))

    # Minimap
    mm_w, mm_h = 192, 108
    mm_x = SCREEN_W - mm_w - 10
    mm_y = 10
    scale_x = mm_w / MAP_W
    scale_y = mm_h / MAP_H
    draw_panel(screen, mm_x-3, mm_y-3, mm_w+6, mm_h+6, color=(8,10,18), border=(30,34,55), radius=5)
    pygame.draw.rect(screen, (20, 26, 18), (mm_x, mm_y, mm_w, mm_h))
    for w in server_walls:
        wx2 = mm_x + int(w["x"] * scale_x)
        wy2 = mm_y + int(w["y"] * scale_y)
        ww2 = max(2, int(w["w"] * scale_x))
        wh2 = max(2, int(w["h"] * scale_y))
        pygame.draw.rect(screen, (80,80,100), (wx2, wy2, ww2, wh2))
    for addr, p in server_players.items():
        mmx = mm_x + int(p["x"] * scale_x)
        mmy = mm_y + int(p["y"] * scale_y)
        is_me2 = p.get("name") == my_name
        col = C_ACCENT if is_me2 else C_RED
        if not p.get("alive", True): col = C_GRAY
        pygame.draw.circle(screen, col, (mmx, mmy), 3 if is_me2 else 2)
    vx = mm_x + int(cam_x * scale_x)
    vy = mm_y + int(cam_y * scale_y)
    vw = max(1, int(SCREEN_W * scale_x))
    vh = max(1, int(SCREEN_H * scale_y))
    pygame.draw.rect(screen, (200,200,200), (vx, vy, vw, vh), 1)

    # Starpower bar
    bar_w2 = 340
    bx3, by3, bh3 = cxh - bar_w2//2, SCREEN_H - 36, 22
    draw_panel(screen, bx3-3, by3-3, bar_w2+6, bh3+6, color=(8,10,18), border=(30,34,55), radius=7)
    if starpower_active:
        elapsed2 = now_ms - starpower_start
        progress = 1.0 - min(elapsed2/starpower_duration, 1.0)
        col2  = bdata["color"]
        label = "STARPOWER  ACTIVE"
        pulse2 = int(bar_w2 * progress)
        pygame.draw.rect(screen, (18,8,38),  (bx3, by3, bar_w2, bh3), border_radius=5)
        pygame.draw.rect(screen, col2,       (bx3, by3, pulse2,  bh3), border_radius=5)
        shim = pygame.Surface((max(1,pulse2), bh3), pygame.SRCALPHA)
        sa   = int(55 + 35*math.sin(now_ms*0.012))
        pygame.draw.rect(shim, (255,255,255,sa), (0,0,max(1,pulse2),bh3//2))
        screen.blit(shim, (bx3, by3))
    elif now_ms - last_starpower < starpower_cooldown:
        elapsed2 = now_ms - last_starpower
        progress = elapsed2 / starpower_cooldown
        col2  = C_GRAY
        secs_left = int((starpower_cooldown - elapsed2)/1000)+1
        label = f"COOLDOWN  {secs_left}s"
        pygame.draw.rect(screen, (18,18,28), (bx3, by3, bar_w2, bh3), border_radius=5)
        pygame.draw.rect(screen, col2,       (bx3, by3, int(bar_w2*progress), bh3), border_radius=5)
    else:
        col2  = C_ACCENT
        label = "STARPOWER  READY  [F]"
        blink = (now_ms//600)%2
        pygame.draw.rect(screen, (28,24,8) if blink else (18,18,10), (bx3, by3, bar_w2, bh3), border_radius=5)
        if blink:
            pygame.draw.rect(screen, col2, (bx3, by3, bar_w2, bh3), border_radius=5)
    ls = font_tiny.render(label, True, col2)
    screen.blit(ls, (cxh - ls.get_width()//2, by3+4))

    # Bush indicator
    for addr, p in server_players.items():
        if p.get("name") == my_name and in_bush(p["x"], p["y"]):
            bi  = font_small.render("  IN BUSH — HIDDEN  ", True, C_GRASS2)
            bib = font_small.render("  IN BUSH — HIDDEN  ", True, C_DARK)
            screen.blit(bib, (cxh - bi.get_width()//2+1, SCREEN_H - 66))
            screen.blit(bi,  (cxh - bi.get_width()//2,   SCREEN_H - 66))
            break

# ─── MAIN LOOP ────────────────────────────────────────────────────────────────
running      = True
lobby_rects  = {}
mouse_held   = False

pygame.mouse.set_visible(True)
play_sound("startup")

while running:
    cur_phase = get_phase()

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

        # ── NAME ENTRY ──
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

        # ── LOBBY (brawler select + ready) ──
        elif cur_phase == "lobby":
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mx_e, my_e = event.pos
                # Check brawler card clicks
                for bname, rect in lobby_rects.items():
                    rx, ry, rw, rh = rect
                    if rx <= mx_e <= rx+rw and ry <= my_e <= ry+rh:
                        if selected_brawler != bname:
                            selected_brawler = bname
                            my_brawler = bname
                            send_brawler_select(bname)
                            spawn_particles(mx_e, my_e, BRAWLERS[bname]["color"], count=10, speed=5)
                        break

                # Check ready button (approx right panel area)
                right_x = SCREEN_W - 260 - 10
                right_w_btn = 260
                panel_y_btn = 92
                btn_y = panel_y_btn + 158
                btn_x = right_x + 16
                btn_w_sz = right_w_btn - 32
                btn_h_sz = 56

                # Check not spectating
                spec_self2 = False
                game_running2 = lobby_data.get("game_running", False)
                for lp in lobby_data.get("lobby_players", []):
                    if lp.get("name") == my_name and lp.get("spectating", False):
                        spec_self2 = True

                if not was_kicked and not spec_self2 and not game_running2:
                    if btn_x <= mx_e <= btn_x + btn_w_sz and btn_y <= my_e <= btn_y + btn_h_sz:
                        ready_local = not ready_local
                        send_ready(ready_local)
                        if ready_local:
                            spawn_particles(btn_x + btn_w_sz//2, btn_y + btn_h_sz//2, C_GREEN, count=12, speed=4)

        # ── PLAYING ──
        elif cur_phase == "playing":
            if event.type == pygame.KEYDOWN and event.key == pygame.K_f:
                activate_starpower()
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mouse_held = True
                try_shoot()
            if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                mouse_held = False

    # Hold-to-shoot (minigun)
    if cur_phase == "playing" and mouse_held and my_brawler == "minigun":
        try_shoot()
    if cur_phase == "playing" and my_brawler and starpower_active and my_brawler == "minigun":
        try_shoot()

    # Movement
    if cur_phase == "playing":
        keys = pygame.key.get_pressed()
        send({"type": "move",
              "up":    bool(keys[pygame.K_w]),
              "down":  bool(keys[pygame.K_s]),
              "left":  bool(keys[pygame.K_a]),
              "right": bool(keys[pygame.K_d])})

    # Game over auto-return
    if cur_phase == "game_over":
        if go_timer == 0:
            go_timer = pygame.time.get_ticks()
        if pygame.time.get_ticks() - go_timer > 4000:
            go_timer     = 0
            ready_local  = False
            was_kicked   = False
            my_brawler   = selected_brawler
            set_phase("lobby")
            join_lobby()

    # Lobby heartbeat
    if cur_phase == "lobby":
        now_ms_hb = pygame.time.get_ticks()
        if now_ms_hb - getattr(draw_lobby, "_last_hb", 0) > 1000:
            draw_lobby._last_hb = now_ms_hb
            join_lobby()

    # ── DRAW ──
    cur_phase = get_phase()
    update_draw_particles(screen)  # always update

    if   cur_phase == "startup":     draw_startup()
    elif cur_phase == "name_entry":  draw_name_entry()
    elif cur_phase == "lobby":       lobby_rects = draw_lobby()
    elif cur_phase == "playing":     draw_game()
    elif cur_phase == "dead_screen": draw_dead_screen()
    elif cur_phase == "game_over":   draw_game_over()

    pygame.display.flip()
    clock.tick(60)

pygame.mouse.set_visible(True)
pygame.quit()