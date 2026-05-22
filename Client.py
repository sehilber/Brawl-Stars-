import socket
import threading
import json
import pygame
import math
import os
import random

SERVER_IP = "10.165.234.133"
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
C_DARK     = (  6,   7,  13)
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

load_sound("startup", "ps4-startup.mp3", volume=0.7)
load_sound("menu",    "brawl-stars-menu-start-sounds-sound-effect-brawl-stars-hd-sound-effects_01web.mp3", volume=0.5)
load_sound("shoot",   "gun-sniper-rifle-shot.mp3", volume=0.5)
load_sound("hit",     "fortnite-shield-break-sound__1_.mp3", volume=0.7)
load_sound("death",   "fortnite-death-sound.mp3", volume=0.8)

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

# ─── BRAWLER DISPLAY DATA ─────────────────────────────────────────────────────
BRAWLERS = {
    "sniper": {
        "weapon": "sniper",
        "color":  (80,  200, 255), "accent": (200, 240, 255),
        "skin_color": (255, 200, 140),
        "hair_color": (60, 40, 20),
        "outfit_color": (40, 80, 160),
        "emoji": "🎯",
        "desc":  "Long range, high damage.",
        "star":  "Piercing bullets!",
        "tag":   "MARKSMAN",
        "stat_labels": [("DMG", "80"), ("SPD", "22"), ("RATE", "Slow")],
    },
    "minigun": {
        "weapon": "minigun",
        "color":  (255, 130,  40), "accent": (255, 210, 100),
        "skin_color": (255, 185, 120),
        "hair_color": (200, 50, 50),
        "outfit_color": (180, 60, 20),
        "emoji": "🔥",
        "desc":  "Rapid fire spray.",
        "star":  "Insane fire rate!",
        "tag":   "SHARPSHOOTER",
        "stat_labels": [("DMG", "10"), ("SPD", "10"), ("RATE", "Rapid")],
    },
    "mage": {
        "weapon": "magic",
        "color":  (180,  70, 255), "accent": (220, 160, 255),
        "skin_color": (240, 210, 180),
        "hair_color": (200, 100, 255),
        "outfit_color": (80, 20, 140),
        "emoji": "✨",
        "desc":  "Magic projectiles.",
        "star":  "Turn invisible!",
        "tag":   "MYSTIC",
        "stat_labels": [("DMG", "35"), ("SPD", "14"), ("RATE", "Med")],
    },
    "tank": {
        "weapon": "shotgun",
        "color":  (200,  80,  40), "accent": (255, 160, 100),
        "skin_color": (220, 170, 100),
        "hair_color": (60, 40, 20),
        "outfit_color": (100, 50, 20),
        "emoji": "💥",
        "desc":  "5-pellet shotgun blast.",
        "star":  "Place a shield wall!",
        "tag":   "BRUISER",
        "stat_labels": [("DMG", "22x5"), ("SPD", "8"), ("RATE", "Slow")],
    },
    "ninja": {
        "weapon": "shuriken",
        "color":  ( 40, 200, 160), "accent": (150, 255, 220),
        "skin_color": (255, 200, 140),
        "hair_color": (20, 20, 20),
        "outfit_color": (20, 80, 60),
        "emoji": "🌀",
        "desc":  "Fast shurikens, moves quickly.",
        "star":  "Teleport forward!",
        "tag":   "ASSASSIN",
        "stat_labels": [("DMG", "18"), ("SPD", "16"), ("RATE", "Fast")],
    },
    "healer": {
        "weapon": "orb",
        "color":  (100, 220,  80), "accent": (180, 255, 140),
        "skin_color": (255, 220, 180),
        "hair_color": (50, 150, 50),
        "outfit_color": (30, 120, 30),
        "emoji": "💚",
        "desc":  "Regen 2 HP/sec passively.",
        "star":  "Invincible 3 seconds!",
        "tag":   "SUPPORT",
        "stat_labels": [("DMG", "28"), ("SPD", "12"), ("RATE", "Med")],
    },
    # ── NEW BRAWLERS ──────────────────────────────────────────────────────────
    "berserker": {
        "weapon": "cannon",
        "color":  (220,  50,  50), "accent": (255, 120,  80),
        "skin_color": (210, 150,  80),
        "hair_color": (180,  20,  20),
        "outfit_color": (100,  20,  20),
        "emoji": "⚡",
        "desc":  "Dual-barrel cannon. Short range.",
        "star":  "RAGE: speed + dmg boost!",
        "tag":   "BERSERKER",
        "stat_labels": [("DMG", "55x3"), ("SPD", "10"), ("RATE", "Med")],
    },
    "ghost": {
        "weapon": "phantom",
        "color":  (140, 180, 255), "accent": (200, 220, 255),
        "skin_color": (200, 210, 240),
        "hair_color": (100, 120, 200),
        "outfit_color": (40,  50, 100),
        "emoji": "👻",
        "desc":  "Slow orbs that freeze enemies.",
        "star":  "Shots pierce all walls!",
        "tag":   "PHANTOM",
        "stat_labels": [("DMG", "30"), ("SPD", "8"), ("RATE", "Med")],
    },
    "bomber": {
        "weapon": "bomb",
        "color":  (255, 180,  20), "accent": (255, 220, 100),
        "skin_color": (230, 185, 110),
        "hair_color": ( 80,  50,  10),
        "outfit_color": (80,  60,  10),
        "emoji": "💣",
        "desc":  "Lobbed bombs with AoE blast.",
        "star":  "Mega bombs — huge blast!",
        "tag":   "DEMOLITION",
        "stat_labels": [("DMG", "45 AoE"), ("SPD", "12"), ("RATE", "Slow")],
    },
}

WEAPON_TO_BRAWLER = {
    "sniper":   "sniper",
    "minigun":  "minigun",
    "magic":    "mage",
    "shotgun":  "tank",
    "shuriken": "ninja",
    "orb":      "healer",
    "cannon":   "berserker",
    "phantom":  "ghost",
    "bomb":     "bomber",
    "ak47":     "sniper",
}

# ─── ANIMATION STATE ──────────────────────────────────────────────────────────
player_anims = {}

def get_anim(addr):
    if addr not in player_anims:
        player_anims[addr] = {
            "walk_t": 0.0,
            "shoot_t": 0.0,
            "face_dir": 0.0,
            "last_x": 0,
            "last_y": 0,
            "hurt_t": 0,
            "shoot_flash": 0,
            "teleport_flash": 0,
        }
    return player_anims[addr]

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

def spawn_hit_particles(x, y, color):
    for _ in range(6):
        ang = random.uniform(0, math.pi * 2)
        spd = random.uniform(2, 5)
        particles.append({
            "x": x, "y": y,
            "dx": math.cos(ang) * spd,
            "dy": math.sin(ang) * spd,
            "life": 0.7, "decay": 0.06,
            "r": random.randint(3, 7), "color": color,
        })

def spawn_explosion_particles(x, y, radius=80):
    count = 16
    for i in range(count):
        ang = random.uniform(0, math.pi * 2)
        spd = random.uniform(3, 8)
        col = random.choice([(255, 180, 30), (255, 100, 20), (255, 60, 10), (200, 200, 80)])
        particles.append({
            "x": x, "y": y,
            "dx": math.cos(ang) * spd,
            "dy": math.sin(ang) * spd,
            "life": 1.0, "decay": 0.025,
            "r": random.randint(4, 10), "color": col,
        })
    # Smoke ring
    for i in range(8):
        ang = math.pi * 2 / 8 * i
        dist = radius * 0.6
        particles.append({
            "x": x + math.cos(ang) * dist,
            "y": y + math.sin(ang) * dist,
            "dx": math.cos(ang) * 1.5,
            "dy": math.sin(ang) * 1.5,
            "life": 0.8, "decay": 0.015,
            "r": random.randint(6, 12), "color": (80, 80, 80),
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

# ─── DETAILED BRAWLER DRAWING ─────────────────────────────────────────────────
def draw_brawler_detailed(surf, brawler_name, cx, cy, alpha=255, scale=1.0,
                           starpower=False, alive=True, face_angle=0.0,
                           walk_phase=0.0, shoot_flash=0, hurt_flash=0,
                           invincible=False, rage=False, wallpierce=False,
                           teleport_flash=0):
    bdata = BRAWLERS.get(brawler_name, BRAWLERS["sniper"])

    if not alive:
        tmp = pygame.Surface((80, 80), pygame.SRCALPHA)
        col = (80, 80, 90, min(255, alpha))
        pygame.draw.line(tmp, col, (10, 10), (70, 70), 6)
        pygame.draw.line(tmp, col, (70, 10), (10, 70), 6)
        surf.blit(tmp, (cx - 40, cy - 40))
        return

    skin   = bdata["skin_color"]
    hair   = bdata["hair_color"]
    outfit = bdata["outfit_color"]
    accent_c = bdata["accent"]
    main_c   = bdata["color"]

    # Special state overrides
    if invincible:
        now_t = pygame.time.get_ticks()
        shield_pulse = int(40 + 30 * math.sin(now_t * 0.01))
        glow_s = pygame.Surface((80, 80), pygame.SRCALPHA)
        pygame.draw.circle(glow_s, (100, 200, 255, shield_pulse), (40, 40), 38)
        surf.blit(glow_s, (cx - 40, cy - 40))

    if rage:
        now_t = pygame.time.get_ticks()
        ra = int(60 + 40 * math.sin(now_t * 0.008))
        gs = pygame.Surface((80, 80), pygame.SRCALPHA)
        pygame.draw.circle(gs, (255, 60, 20, ra), (40, 40), 38)
        surf.blit(gs, (cx - 40, cy - 40))
        outfit = tuple(min(255, c + 60) for c in outfit)

    if wallpierce:
        now_t = pygame.time.get_ticks()
        wa = int(40 + 30 * math.sin(now_t * 0.012))
        gs2 = pygame.Surface((80, 80), pygame.SRCALPHA)
        pygame.draw.circle(gs2, (140, 180, 255, wa), (40, 40), 38)
        surf.blit(gs2, (cx - 40, cy - 40))

    if teleport_flash > 0:
        tf_a = min(220, teleport_flash * 20)
        gst = pygame.Surface((80, 80), pygame.SRCALPHA)
        pygame.draw.circle(gst, (40, 255, 180, tf_a), (40, 40), 36)
        surf.blit(gst, (cx - 40, cy - 40))

    if hurt_flash > 0:
        blend = min(1.0, hurt_flash / 8)
        skin = tuple(int(s + (255 - s) * blend * 0.6) for s in skin)
        outfit = tuple(int(min(255, o + 80 * blend)) for o in outfit)

    if shoot_flash > 0:
        blend = min(1.0, shoot_flash / 6)
        outfit = tuple(int(min(255, o + 60 * blend)) for o in outfit)

    R = int(18 * scale)
    tmp = pygame.Surface((int(R*6), int(R*6)), pygame.SRCALPHA)
    ox = R * 3
    oy = R * 3

    bob = int(math.sin(walk_phase) * 2 * scale)
    leg_swing = math.sin(walk_phase) * 0.4

    def ac(col, a=alpha):
        return (*col[:3], min(255, a))

    def draw_shadow():
        sh = pygame.Surface((R*4, R*2), pygame.SRCALPHA)
        pygame.draw.ellipse(sh, (0, 0, 0, 55), (0, 0, R*4, R*2))
        tmp.blit(sh, (ox - R*2, oy + R + 2))

    def draw_outline_circle(x, y, r, color, width=2):
        pygame.draw.circle(tmp, (20, 15, 10, min(255, alpha)), (x, y), r + width)
        pygame.draw.circle(tmp, ac(color), (x, y), r)

    def draw_outline_rect(rect, color, radius=3, border=2):
        x, y, w, h = rect
        pygame.draw.rect(tmp, (20, 15, 10, min(255, alpha)),
                         (x-border, y-border, w+border*2, h+border*2), border_radius=radius+border)
        pygame.draw.rect(tmp, ac(color), rect, border_radius=radius)

    draw_shadow()

    if brawler_name == "sniper":
        lx1 = ox - int(R * 0.5) + int(leg_swing * R * 0.6)
        lx2 = ox + int(R * 0.5) - int(leg_swing * R * 0.6)
        boot_col = (40, 30, 20)
        for lx in [lx1, lx2]:
            pygame.draw.rect(tmp, (20, 15, 10, alpha), (lx - R//2 - 1, oy + R - 1, R, R + 3), border_radius=4)
            pygame.draw.rect(tmp, ac(outfit), (lx - R//2, oy + R, R, R), border_radius=3)
            pygame.draw.rect(tmp, ac(boot_col), (lx - R//2, oy + R*2 - 2, R, 6), border_radius=3)
        draw_outline_rect((ox - R, oy - R//2 + bob, R*2, int(R*1.5)), outfit)
        pygame.draw.rect(tmp, ac((80, 60, 30)), (ox - R, oy + R//2 + bob, R*2, R//3))
        arm_ang = math.radians(face_angle)
        gun_len = int(R * 1.4)
        gx = ox + int(math.cos(arm_ang) * gun_len)
        gy = oy + bob + int(math.sin(arm_ang) * gun_len * 0.5)
        pygame.draw.line(tmp, (20, 15, 10, alpha), (ox, oy + bob), (gx, gy), R//2 + 2)
        pygame.draw.line(tmp, ac(skin), (ox, oy + bob), (gx, gy), R//2)
        rifle_end_x = ox + int(math.cos(arm_ang) * R * 2.2)
        rifle_end_y = oy + bob + int(math.sin(arm_ang) * R * 0.8)
        pygame.draw.line(tmp, (15, 10, 5, alpha),
                         (ox + int(math.cos(arm_ang) * R * 0.6), oy + bob + int(math.sin(arm_ang) * R * 0.3)),
                         (rifle_end_x, rifle_end_y), R//3 + 2)
        pygame.draw.line(tmp, ac((100, 90, 80)),
                         (ox + int(math.cos(arm_ang) * R * 0.6), oy + bob + int(math.sin(arm_ang) * R * 0.3)),
                         (rifle_end_x, rifle_end_y), R//3)
        scope_x = ox + int(math.cos(arm_ang) * R * 1.4)
        scope_y = oy + bob + int(math.sin(arm_ang) * R * 0.5)
        pygame.draw.circle(tmp, ac((60, 200, 255)), (scope_x, scope_y), R//4)
        back_ang = arm_ang + math.pi * 0.8
        bax = ox + int(math.cos(back_ang) * R * 0.7)
        bay = oy + bob + int(math.sin(back_ang) * R * 0.4)
        pygame.draw.line(tmp, (20, 15, 10, alpha), (ox, oy + bob), (bax, bay), R//2 + 2)
        pygame.draw.line(tmp, ac(skin), (ox, oy + bob), (bax, bay), R//2)
        head_y = oy - R + bob
        draw_outline_circle(ox, head_y, int(R * 0.9), skin)
        cap_pts = [(ox - R, head_y), (ox - R, head_y - R//2), (ox + int(R*0.3), head_y - R), (ox + R, head_y - R//2), (ox + R, head_y)]
        pygame.draw.polygon(tmp, (20, 15, 10, alpha), [(x+2, y+2) for x, y in cap_pts])
        pygame.draw.polygon(tmp, ac(hair), cap_pts)
        eye_x = ox + int(math.cos(arm_ang) * R * 0.4)
        pygame.draw.circle(tmp, ac((20, 15, 10)), (eye_x, head_y), R//5)
        pygame.draw.circle(tmp, ac((255, 255, 255)), (eye_x, head_y), R//5 - 1)
        pygame.draw.circle(tmp, ac((20, 15, 10)), (eye_x + 1, head_y), R//8)
        if starpower:
            pygame.draw.circle(tmp, ac((60, 200, 255)), (eye_x, head_y), R//5 + 2, 1)

    elif brawler_name == "minigun":
        lx1 = ox - int(R * 0.55) + int(leg_swing * R * 0.5)
        lx2 = ox + int(R * 0.55) - int(leg_swing * R * 0.5)
        boot_col = (50, 35, 20)
        for lx in [lx1, lx2]:
            pygame.draw.rect(tmp, (20, 15, 10, alpha), (lx - R//2 - 1, oy + R//2 - 1, int(R*1.1), int(R*1.3)), border_radius=5)
            pygame.draw.rect(tmp, ac(outfit), (lx - R//2, oy + R//2, int(R*1.1), int(R*1.2)), border_radius=4)
            pygame.draw.rect(tmp, ac(boot_col), (lx - R//2, oy + R*2 - 5, int(R*1.1), 8), border_radius=3)
        draw_outline_rect((ox - int(R*1.1), oy - R//2 + bob, int(R*2.2), int(R*1.6)), outfit)
        draw_outline_rect((ox - int(R*0.7), oy - R//3 + bob, int(R*1.4), int(R*0.8)), (120, 90, 50))
        pygame.draw.line(tmp, ac((80, 60, 30)), (ox - R, oy - R//3 + bob), (ox + R, oy + R//2 + bob), 3)
        pygame.draw.line(tmp, ac((80, 60, 30)), (ox + R, oy - R//3 + bob), (ox - R, oy + R//2 + bob), 3)
        arm_ang = math.radians(face_angle)
        gun_base_x = ox + int(math.cos(arm_ang) * R * 0.5)
        gun_base_y = oy + bob + int(math.sin(arm_ang) * R * 0.3)
        now_t = pygame.time.get_ticks() * 0.01 if starpower else pygame.time.get_ticks() * 0.004
        for barrel in range(3):
            b_ang = arm_ang + math.radians(barrel * 120 + now_t * 40)
            b_off_x = int(math.cos(b_ang) * R * 0.25)
            b_off_y = int(math.sin(b_ang) * R * 0.25)
            bx1 = gun_base_x + b_off_x
            by1 = gun_base_y + b_off_y
            bx2 = bx1 + int(math.cos(arm_ang) * R * 1.8)
            by2 = by1 + int(math.sin(arm_ang) * R * 0.8)
            pygame.draw.line(tmp, (20, 15, 10, alpha), (bx1, by1), (bx2, by2), R//3 + 2)
            pygame.draw.line(tmp, ac((150, 140, 120)), (bx1, by1), (bx2, by2), R//3)
        pygame.draw.circle(tmp, (20, 15, 10, alpha), (gun_base_x, gun_base_y), R//2 + 2)
        pygame.draw.circle(tmp, ac((180, 160, 100)), (gun_base_x, gun_base_y), R//2)
        pygame.draw.line(tmp, (20, 15, 10, alpha), (ox, oy + bob), (gun_base_x, gun_base_y), R//2 + 2)
        pygame.draw.line(tmp, ac(skin), (ox, oy + bob), (gun_base_x, gun_base_y), R//2)
        head_y = oy - int(R * 1.05) + bob
        draw_outline_circle(ox, head_y, int(R * 1.0), skin)
        cap_col = bdata["hair_color"]
        cap_pts = [(ox - R, head_y - 2), (ox - int(R*0.8), head_y - R), (ox, head_y - int(R*1.2)), (ox + int(R*0.8), head_y - R), (ox + R, head_y - 2)]
        pygame.draw.polygon(tmp, (20, 15, 10, alpha), [(x+2, y+2) for x, y in cap_pts])
        pygame.draw.polygon(tmp, ac(cap_col), cap_pts)
        pygame.draw.rect(tmp, (20, 15, 10, alpha), (ox - R + 1, head_y - 3, R*2 - 2, R//3 + 2))
        pygame.draw.rect(tmp, ac((60, 80, 100)), (ox - R + 2, head_y - 2, R*2 - 4, R//3))
        eye_x = ox + int(math.cos(math.radians(face_angle)) * R * 0.3)
        pygame.draw.circle(tmp, ac((255, 255, 255)), (eye_x - 2, head_y + 2), R//3)
        pygame.draw.circle(tmp, ac((20, 15, 10)), (eye_x - 2, head_y + 2), R//4)
        pygame.draw.circle(tmp, ac((255, 255, 255)), (eye_x - 1, head_y + 1), R//8)
        smile_pts = [(ox - R//2, head_y + R//3), (ox, head_y + R//2), (ox + R//2, head_y + R//3)]
        for i in range(len(smile_pts) - 1):
            pygame.draw.line(tmp, ac((60, 20, 20)), smile_pts[i], smile_pts[i+1], 2)

    elif brawler_name == "mage":
        robe_pts = [(ox - R, oy + R + 4), (ox - int(R*1.3), oy + int(R*2.2)), (ox + int(R*1.3), oy + int(R*2.2)), (ox + R, oy + R + 4)]
        pygame.draw.polygon(tmp, (20, 15, 10, alpha), [(x+2, y+2) for x, y in robe_pts])
        pygame.draw.polygon(tmp, ac(outfit), robe_pts)
        pygame.draw.polygon(tmp, ac(accent_c), robe_pts, 2)
        draw_outline_rect((ox - R, oy - R//2 + bob, R*2, int(R*1.5)), outfit)
        for i in range(3):
            rx = ox - R//2 + i * R//2
            ry = oy + bob + 2
            pygame.draw.circle(tmp, ac(accent_c), (rx, ry), 2)
        arm_ang = math.radians(face_angle)
        staff_tip_x = ox + int(math.cos(arm_ang) * R * 2.2)
        staff_tip_y = oy + bob - R + int(math.sin(arm_ang) * R * 1.0)
        staff_base_x = ox - int(math.cos(arm_ang) * R * 0.3)
        staff_base_y = oy + bob + R + int(math.sin(arm_ang) * R * 0.2)
        pygame.draw.line(tmp, (20, 15, 10, alpha), (staff_base_x, staff_base_y), (staff_tip_x, staff_tip_y), R//3 + 2)
        pygame.draw.line(tmp, ac((120, 90, 60)), (staff_base_x, staff_base_y), (staff_tip_x, staff_tip_y), R//3)
        orb_pulse = int(R//3 + 2 * math.sin(pygame.time.get_ticks() * 0.005))
        now_t = pygame.time.get_ticks()
        orb_col = (200, 150, 255) if starpower else (255, 120, 20)
        glow_s = pygame.Surface((orb_pulse*4, orb_pulse*4), pygame.SRCALPHA)
        ga = int(80 + 40 * math.sin(now_t * 0.006))
        pygame.draw.circle(glow_s, (*orb_col, ga), (orb_pulse*2, orb_pulse*2), orb_pulse*2)
        tmp.blit(glow_s, (staff_tip_x - orb_pulse*2, staff_tip_y - orb_pulse*2))
        pygame.draw.circle(tmp, (20, 15, 10, alpha), (staff_tip_x, staff_tip_y), orb_pulse + 2)
        pygame.draw.circle(tmp, ac(orb_col), (staff_tip_x, staff_tip_y), orb_pulse)
        pygame.draw.circle(tmp, ac((255, 255, 200)), (staff_tip_x - 1, staff_tip_y - 1), orb_pulse//2)
        arm_mid_x = ox + int(math.cos(arm_ang) * R * 0.8)
        arm_mid_y = oy + bob + int(math.sin(arm_ang) * R * 0.4)
        pygame.draw.line(tmp, (20, 15, 10, alpha), (ox, oy + bob), (arm_mid_x, arm_mid_y), R//2 + 2)
        pygame.draw.line(tmp, ac(skin), (ox, oy + bob), (arm_mid_x, arm_mid_y), R//2)
        head_y = oy - R + bob
        draw_outline_circle(ox, head_y, int(R * 0.9), skin)
        hair_col = bdata["hair_color"]
        for i in range(5):
            h_ang = math.radians(-120 + i * 50)
            hx = ox + int(math.cos(h_ang) * R)
            hy = head_y + int(math.sin(h_ang) * R)
            pygame.draw.circle(tmp, (20, 15, 10, alpha), (hx, hy), R//3 + 1)
            pygame.draw.circle(tmp, ac(hair_col), (hx, hy), R//3)
        eye_off = int(math.cos(math.radians(face_angle)) * R * 0.3)
        for ex, ew in [(ox + eye_off - R//3, R//4), (ox + eye_off + R//3, R//4)]:
            pygame.draw.circle(tmp, ac((255, 255, 255)), (ex, head_y), ew)
            pygame.draw.circle(tmp, ac((100, 40, 200)), (ex, head_y), ew - 1)
            pygame.draw.circle(tmp, ac((255, 255, 200)), (ex - 1, head_y - 1), ew//3)
        if starpower:
            shim = pygame.Surface(tmp.get_size(), pygame.SRCALPHA)
            pygame.draw.circle(shim, (180, 120, 255, 60), (ox, oy), R * 2)
            tmp.blit(shim, (0, 0))

    elif brawler_name == "tank":
        lx1 = ox - int(R * 0.6) + int(leg_swing * R * 0.4)
        lx2 = ox + int(R * 0.6) - int(leg_swing * R * 0.4)
        for lx in [lx1, lx2]:
            pygame.draw.rect(tmp, (20, 15, 10, alpha), (lx - R//2 - 2, oy + R//2 - 1, int(R*1.2), int(R*1.4) + 2), border_radius=4)
            pygame.draw.rect(tmp, ac(outfit), (lx - R//2, oy + R//2, int(R*1.2), int(R*1.4)), border_radius=3)
            pygame.draw.circle(tmp, ac(accent_c), (lx, oy + R*2 - 4), 3)
        draw_outline_rect((ox - int(R*1.2), oy - int(R*0.8) + bob, int(R*2.4), int(R*2.0)), outfit)
        for sx_off in [-int(R*1.3), int(R*0.5)]:
            draw_outline_rect((ox + sx_off, oy - int(R*0.6) + bob, int(R*0.8), int(R*0.8)), (150, 120, 60), radius=4)
        draw_outline_rect((ox - int(R*0.8), oy - int(R*0.6) + bob, int(R*1.6), int(R*1.2)), (160, 130, 70), radius=4)
        for rix, riy in [(-R//2, 0), (R//2, 0), (0, R//2)]:
            pygame.draw.circle(tmp, ac((200, 170, 80)), (ox + rix, oy + riy + bob), 3)
        arm_ang = math.radians(face_angle)
        gun_x = ox + int(math.cos(arm_ang) * R * 0.7)
        gun_y = oy + bob + int(math.sin(arm_ang) * R * 0.3)
        for barrel_off in [-R//4, 0, R//4]:
            perp_ang = arm_ang + math.pi/2
            bx1 = gun_x + int(math.cos(perp_ang) * barrel_off)
            by1 = gun_y + int(math.sin(perp_ang) * barrel_off)
            bx2 = bx1 + int(math.cos(arm_ang) * R * 1.5)
            by2 = by1 + int(math.sin(arm_ang) * R * 0.6)
            pygame.draw.line(tmp, (20, 15, 10, alpha), (bx1, by1), (bx2, by2), R//3 + 2)
            pygame.draw.line(tmp, ac((180, 150, 100)), (bx1, by1), (bx2, by2), R//3)
        pygame.draw.line(tmp, (20, 15, 10, alpha), (ox, oy + bob), (gun_x, gun_y), R//2 + 2 + 2)
        pygame.draw.line(tmp, ac(skin), (ox, oy + bob), (gun_x, gun_y), R//2 + 2)
        head_y = oy - int(R * 1.0) + bob
        draw_outline_circle(ox, head_y, int(R * 1.05), skin)
        helm_pts = [(ox - R, head_y - 2), (ox - R, head_y - int(R*0.8)), (ox, head_y - int(R*1.1)), (ox + R, head_y - int(R*0.8)), (ox + R, head_y - 2)]
        pygame.draw.polygon(tmp, (20, 15, 10, alpha), [(x+2, y+2) for x, y in helm_pts])
        pygame.draw.polygon(tmp, ac(outfit), helm_pts)
        pygame.draw.polygon(tmp, ac(accent_c), helm_pts, 2)
        eye_x = ox + int(math.cos(math.radians(face_angle)) * R * 0.3)
        pygame.draw.line(tmp, ac((60, 30, 10)), (eye_x - R//2, head_y - R//4), (eye_x, head_y - R//6), 3)
        pygame.draw.circle(tmp, ac((20, 15, 10)), (eye_x, head_y + 2), R//4 + 1)
        pygame.draw.circle(tmp, ac((200, 50, 20)), (eye_x, head_y + 2), R//4)
        pygame.draw.circle(tmp, ac((255, 200, 50)), (eye_x, head_y + 2), R//6)
        pygame.draw.line(tmp, ac((120, 60, 40)), (eye_x - R//3, head_y - R//2), (eye_x, head_y + R//3), 2)

    elif brawler_name == "ninja":
        lx1 = ox - int(R * 0.45) + int(leg_swing * R * 0.7)
        lx2 = ox + int(R * 0.45) - int(leg_swing * R * 0.7)
        for lx in [lx1, lx2]:
            pygame.draw.rect(tmp, (20, 15, 10, alpha), (lx - R//2 - 1, oy + R//2 - 1, R, int(R*1.3) + 1), border_radius=3)
            pygame.draw.rect(tmp, ac(outfit), (lx - R//2, oy + R//2, R, int(R*1.3)), border_radius=2)
        draw_outline_rect((ox - int(R*0.9), oy - R//2 + bob, int(R*1.8), int(R*1.5)), outfit)
        pygame.draw.rect(tmp, ac((60, 30, 20)), (ox - R, oy + R//3 + bob, R*2, R//3))
        arm_ang = math.radians(face_angle)
        throw_x = ox + int(math.cos(arm_ang) * R * 1.4)
        throw_y = oy + bob + int(math.sin(arm_ang) * R * 0.5)
        pygame.draw.line(tmp, (20, 15, 10, alpha), (ox, oy + bob), (throw_x, throw_y), R//2 + 2)
        pygame.draw.line(tmp, ac(skin), (ox, oy + bob), (throw_x, throw_y), R//2)
        now_t = pygame.time.get_ticks()
        shur_ang = now_t * 0.008 if starpower else now_t * 0.004
        sh_s = pygame.Surface((R, R), pygame.SRCALPHA)
        sh_cx = R//2; sh_cy = R//2
        for si in range(4):
            sa = shur_ang + math.pi/4 * si * 2
            pygame.draw.polygon(sh_s, ac(accent_c), [
                (sh_cx, sh_cy),
                (int(sh_cx + math.cos(sa) * R//2), int(sh_cy + math.sin(sa) * R//2)),
                (int(sh_cx + math.cos(sa + math.pi/4) * R//4), int(sh_cy + math.sin(sa + math.pi/4) * R//4)),
            ])
        pygame.draw.circle(sh_s, ac((200, 220, 200)), (sh_cx, sh_cy), 3)
        tmp.blit(sh_s, (throw_x - R//2, throw_y - R//2))
        head_y = oy - int(R * 0.9) + bob
        draw_outline_circle(ox, head_y, int(R * 0.85), skin)
        mask_pts = [(ox - R, head_y + 2), (ox - R, head_y + int(R*0.7)), (ox + R, head_y + int(R*0.7)), (ox + R, head_y + 2)]
        pygame.draw.polygon(tmp, (20, 15, 10, alpha), [(x+1, y+1) for x, y in mask_pts])
        pygame.draw.polygon(tmp, ac(outfit), mask_pts)
        pygame.draw.rect(tmp, (20, 15, 10, alpha), (ox - R + 1, head_y - R//4 - 1, R*2 - 2, R//3 + 2), border_radius=2)
        pygame.draw.rect(tmp, ac(accent_c), (ox - R + 2, head_y - R//4, R*2 - 4, R//3), border_radius=2)
        eye_x = ox + int(math.cos(math.radians(face_angle)) * R * 0.3)
        for ex in [eye_x - R//3, eye_x + R//3]:
            pygame.draw.rect(tmp, ac((20, 15, 10)), (ex - R//4, head_y - 3, R//2, R//4))
            pygame.draw.rect(tmp, ac((60, 200, 160)), (ex - R//4 + 1, head_y - 2, R//2 - 2, R//4 - 2))

    elif brawler_name == "healer":
        robe_pts = [(ox - R, oy + R), (ox - int(R*1.2), oy + int(R*2.1)), (ox + int(R*1.2), oy + int(R*2.1)), (ox + R, oy + R)]
        pygame.draw.polygon(tmp, (20, 15, 10, alpha), [(x+2, y+2) for x, y in robe_pts])
        pygame.draw.polygon(tmp, ac(outfit), robe_pts)
        pygame.draw.rect(tmp, ac((200, 255, 150)), (ox - R//6, oy + int(R*0.8), R//3, int(R*0.8)), border_radius=2)
        pygame.draw.rect(tmp, ac((200, 255, 150)), (ox - R//2, oy + int(R*1.0), R, R//3), border_radius=2)
        draw_outline_rect((ox - R, oy - R//2 + bob, R*2, int(R*1.5)), outfit)
        arm_ang = math.radians(face_angle)
        orb_x = ox + int(math.cos(arm_ang) * R * 1.6)
        orb_y = oy + bob + int(math.sin(arm_ang) * R * 0.7)
        now_t = pygame.time.get_ticks()
        orb_r = int(R * 0.5 + R * 0.15 * math.sin(now_t * 0.004))
        glow_s = pygame.Surface((orb_r*4, orb_r*4), pygame.SRCALPHA)
        ga = int(60 + 30 * math.sin(now_t * 0.003))
        pygame.draw.circle(glow_s, (100, 255, 100, ga), (orb_r*2, orb_r*2), orb_r*2)
        tmp.blit(glow_s, (orb_x - orb_r*2, orb_y - orb_r*2))
        pygame.draw.circle(tmp, (20, 15, 10, alpha), (orb_x, orb_y), orb_r + 2)
        pygame.draw.circle(tmp, ac(main_c), (orb_x, orb_y), orb_r)
        pygame.draw.circle(tmp, ac((200, 255, 200)), (orb_x - orb_r//3, orb_y - orb_r//3), orb_r//3)
        for si in range(3):
            s_ang = now_t * 0.003 + math.pi * 2/3 * si
            sx2 = orb_x + int(math.cos(s_ang) * orb_r * 1.5)
            sy2 = orb_y + int(math.sin(s_ang) * orb_r * 1.5)
            pygame.draw.circle(tmp, ac(accent_c), (sx2, sy2), 3)
        pygame.draw.line(tmp, (20, 15, 10, alpha), (ox, oy + bob), (orb_x, orb_y), R//2 + 2)
        pygame.draw.line(tmp, ac(skin), (ox, oy + bob), (orb_x, orb_y), R//2)
        head_y = oy - R + bob
        draw_outline_circle(ox, head_y, int(R * 0.9), skin)
        hat_base_pts = [(ox - R, head_y - 2), (ox + R, head_y - 2), (ox + int(R*0.6), head_y - R), (ox - int(R*0.6), head_y - R)]
        hat_tip_pts  = [(ox - int(R*0.6), head_y - R), (ox + int(R*0.6), head_y - R), (ox + int(R*0.2), head_y - int(R*2.1)), (ox - int(R*0.2), head_y - int(R*2.1))]
        for pts in [hat_base_pts, hat_tip_pts]:
            pygame.draw.polygon(tmp, (20, 15, 10, alpha), [(x+2, y+2) for x, y in pts])
            pygame.draw.polygon(tmp, ac(outfit), pts)
        pygame.draw.rect(tmp, ac(accent_c), (ox - int(R*0.65), head_y - R - 2, int(R*1.3), R//4))
        eye_x = ox + int(math.cos(math.radians(face_angle)) * R * 0.25)
        for ex in [eye_x - R//3, eye_x + R//3]:
            pygame.draw.circle(tmp, ac((255, 255, 255)), (ex, head_y + 2), R//4)
            pygame.draw.circle(tmp, ac((30, 160, 30)), (ex, head_y + 2), R//4 - 1)
            pygame.draw.circle(tmp, ac((20, 15, 10)), (ex, head_y + 2), R//5)
            pygame.draw.circle(tmp, ac((255, 255, 255)), (ex + 1, head_y + 1), 2)
        pygame.draw.circle(tmp, ac((200, 220, 255)), (eye_x - R//3, head_y + 2), R//4, 1)
        pygame.draw.circle(tmp, ac((200, 220, 255)), (eye_x + R//3, head_y + 2), R//4, 1)
        pygame.draw.line(tmp, ac((150, 170, 200)), (eye_x - R//3 + R//4, head_y + 2), (eye_x + R//3 - R//4, head_y + 2), 1)
        if invincible:
            for i in range(4):
                sa = pygame.time.get_ticks() * 0.002 + math.pi/2 * i
                sx2 = ox + int(math.cos(sa) * R * 1.5)
                sy2 = oy + bob + int(math.sin(sa) * R * 0.7)
                pygame.draw.circle(tmp, ac((100, 220, 255)), (sx2, sy2), 5)

    # ── BERSERKER ─────────────────────────────────────────────────────────────
    elif brawler_name == "berserker":
        # Thick legs, stomping
        lx1 = ox - int(R * 0.55) + int(leg_swing * R * 0.55)
        lx2 = ox + int(R * 0.55) - int(leg_swing * R * 0.55)
        for lx in [lx1, lx2]:
            pygame.draw.rect(tmp, (20, 15, 10, alpha), (lx - R//2 - 2, oy + R//2, int(R*1.2), int(R*1.3) + 2), border_radius=4)
            pygame.draw.rect(tmp, ac((80, 20, 20)), (lx - R//2, oy + R//2, int(R*1.2), int(R*1.3)), border_radius=3)
            pygame.draw.rect(tmp, ac((40, 10, 10)), (lx - R//2, oy + R*2 - 4, int(R*1.2), 7), border_radius=3)
        # Big barrel chest
        draw_outline_rect((ox - int(R*1.2), oy - int(R*0.7) + bob, int(R*2.4), int(R*1.8)), (100, 20, 20))
        # Abs lines
        for i in range(2):
            pygame.draw.line(tmp, ac((60, 10, 10)), (ox - int(R*0.8), oy + i*R//3 + bob), (ox + int(R*0.8), oy + i*R//3 + bob), 2)
        # Shoulder spikes
        for sx_off, side in [(-int(R*1.4), -1), (int(R*0.6), 1)]:
            pygame.draw.rect(tmp, ac((60, 60, 60)), (ox + sx_off, oy - int(R*0.5) + bob, int(R*0.8), int(R*0.8)), border_radius=3)
            spike_x = ox + sx_off + R//4 + (0 if side < 0 else int(R*0.4))
            pygame.draw.polygon(tmp, ac((140, 140, 140)), [
                (spike_x, oy - int(R*0.5) + bob),
                (spike_x - R//5, oy - int(R*1.1) + bob),
                (spike_x + R//5, oy - int(R*1.1) + bob),
            ])
        # Dual cannons
        arm_ang = math.radians(face_angle)
        perp = arm_ang + math.pi/2
        for off in [-R//3, R//3]:
            c_bx = ox + int(math.cos(perp) * off) + int(math.cos(arm_ang) * R*0.4)
            c_by = oy + bob + int(math.sin(perp) * off) + int(math.sin(arm_ang) * R*0.2)
            c_ex = c_bx + int(math.cos(arm_ang) * R * 1.8)
            c_ey = c_by + int(math.sin(arm_ang) * R * 0.8)
            pygame.draw.line(tmp, (20, 15, 10, alpha), (c_bx, c_by), (c_ex, c_ey), R//3 + 2)
            pygame.draw.line(tmp, ac((160, 60, 60)), (c_bx, c_by), (c_ex, c_ey), R//3)
            # Muzzle
            pygame.draw.circle(tmp, ac((80, 40, 40)), (c_ex, c_ey), R//4 + 1)
            pygame.draw.circle(tmp, ac((30, 10, 10)), (c_ex, c_ey), R//4)
        # Arms
        arm_mid_x = ox + int(math.cos(arm_ang) * R * 0.6)
        arm_mid_y = oy + bob + int(math.sin(arm_ang) * R * 0.3)
        pygame.draw.line(tmp, (20, 15, 10, alpha), (ox, oy + bob), (arm_mid_x, arm_mid_y), R//2 + 3)
        pygame.draw.line(tmp, ac(skin), (ox, oy + bob), (arm_mid_x, arm_mid_y), R//2 + 1)
        # Big round head
        head_y = oy - int(R * 1.05) + bob
        draw_outline_circle(ox, head_y, int(R * 1.0), skin)
        # Mohawk
        for i in range(4):
            hx = ox - int(R*0.3) + i * R//3
            hy = head_y - int(R*0.5) - (R//3 if i % 2 == 0 else 0)
            pygame.draw.circle(tmp, (20, 15, 10, alpha), (hx, hy), R//4 + 1)
            pygame.draw.circle(tmp, ac((180, 20, 20)), (hx, hy), R//4)
        # Snarl mouth
        pygame.draw.rect(tmp, ac((20, 10, 10)), (ox - R//2, head_y + R//4, R, R//3), border_radius=2)
        pygame.draw.rect(tmp, ac((200, 50, 50)), (ox - R//3, head_y + R//4 + 2, R//1, R//4), border_radius=1)
        # Angry eyes
        eye_x = ox + int(math.cos(math.radians(face_angle)) * R * 0.3)
        for ex in [eye_x - R//3, eye_x + R//3]:
            pygame.draw.circle(tmp, ac((20, 15, 10)), (ex, head_y), R//4 + 1)
            pygame.draw.circle(tmp, ac((255, 80, 20)), (ex, head_y), R//4)
            pygame.draw.circle(tmp, ac((255, 220, 50)), (ex, head_y), R//6)
        # Rage glow around eyes
        if rage:
            now_t = pygame.time.get_ticks()
            ra_e = int(80 + 40 * math.sin(now_t * 0.01))
            pygame.draw.circle(tmp, (255, 60, 0, ra_e), (ox, head_y), R + 2, 2)

    # ── GHOST ─────────────────────────────────────────────────────────────────
    elif brawler_name == "ghost":
        now_t = pygame.time.get_ticks()
        # Floating body — ghost has no legs, just a wispy trail
        wisp_alpha = int(160 + 60 * math.sin(now_t * 0.003))
        for i in range(4):
            wy = oy + R + int(i * R * 0.5)
            wa = max(10, wisp_alpha - i * 40)
            wr = max(2, R - i * R//4)
            wsh = pygame.Surface((wr*2, wr), pygame.SRCALPHA)
            pygame.draw.ellipse(wsh, (*outfit, wa), (0, 0, wr*2, wr))
            tmp.blit(wsh, (ox - wr, wy))
        # Body robe
        ghost_body_pts = [
            (ox - R, oy + R//2),
            (ox - int(R*1.1), oy + int(R*1.8)),
            (ox - int(R*0.6), oy + int(R*1.4)),
            (ox, oy + int(R*1.8)),
            (ox + int(R*0.6), oy + int(R*1.4)),
            (ox + int(R*1.1), oy + int(R*1.8)),
            (ox + R, oy + R//2),
        ]
        pygame.draw.polygon(tmp, (20, 15, 10, alpha), [(x+1, y+1) for x, y in ghost_body_pts])
        pygame.draw.polygon(tmp, ac(outfit), ghost_body_pts)
        # Shimmering overlay
        shim_s = pygame.Surface((R*4, R*3), pygame.SRCALPHA)
        shim_a = int(30 + 20 * math.sin(now_t * 0.004))
        pygame.draw.ellipse(shim_s, (160, 200, 255, shim_a), (0, 0, R*4, R*3))
        tmp.blit(shim_s, (ox - R*2, oy - R//2 + bob))
        # Torso
        draw_outline_rect((ox - int(R*0.9), oy - R//3 + bob, int(R*1.8), int(R*1.2)), outfit)
        # Phantom orb weapon
        arm_ang = math.radians(face_angle)
        orb_dist = R * 1.8
        orb_x = ox + int(math.cos(arm_ang) * orb_dist)
        orb_y = oy + bob + int(math.sin(arm_ang) * orb_dist * 0.6)
        orb_r = int(R * 0.55 + R * 0.1 * math.sin(now_t * 0.005))
        # Outer glow
        glow_s = pygame.Surface((orb_r*5, orb_r*5), pygame.SRCALPHA)
        ga = int(50 + 20 * math.sin(now_t * 0.004))
        pygame.draw.circle(glow_s, (140, 180, 255, ga), (orb_r*2, orb_r*2), orb_r*2)
        tmp.blit(glow_s, (orb_x - orb_r*2, orb_y - orb_r*2))
        # Orb swirls
        for si in range(3):
            s_ang = now_t * 0.004 + math.pi * 2/3 * si
            sx2 = orb_x + int(math.cos(s_ang) * orb_r * 0.7)
            sy2 = orb_y + int(math.sin(s_ang) * orb_r * 0.7)
            pygame.draw.circle(tmp, ac((200, 220, 255)), (sx2, sy2), orb_r//3)
        pygame.draw.circle(tmp, (20, 15, 10, alpha), (orb_x, orb_y), orb_r + 2)
        pygame.draw.circle(tmp, ac(main_c), (orb_x, orb_y), orb_r)
        pygame.draw.circle(tmp, ac((240, 248, 255)), (orb_x - orb_r//3, orb_y - orb_r//3), orb_r//3)
        # Arm
        pygame.draw.line(tmp, (20, 15, 10, alpha), (ox, oy + bob), (orb_x, orb_y), R//2 + 2)
        pygame.draw.line(tmp, ac(skin), (ox, oy + bob), (orb_x, orb_y), R//2)
        # Head — translucent, ethereal
        head_y = oy - int(R * 0.95) + bob
        head_surf = pygame.Surface((R*3, R*3), pygame.SRCALPHA)
        head_a = min(alpha, 200)
        pygame.draw.circle(head_surf, (*skin[:3], head_a), (R*3//2, R*3//2), int(R * 0.9))
        # Dark hair/crown
        crown_pts = []
        for i in range(5):
            cr_ang = math.radians(-100 + i * 50)
            cr_r = R if i % 2 == 0 else int(R * 0.7)
            crown_pts.append((R*3//2 + int(math.cos(cr_ang) * cr_r), R*3//2 + int(math.sin(cr_ang) * cr_r)))
        pygame.draw.polygon(head_surf, (*hair, min(alpha, 220)), crown_pts)
        tmp.blit(head_surf, (ox - R*3//2, head_y - R*3//2))
        # Glowing eye sockets
        eye_x = ox + int(math.cos(math.radians(face_angle)) * R * 0.3)
        for ex in [eye_x - R//3, eye_x + R//3]:
            pygame.draw.circle(tmp, ac((20, 20, 40)), (ex, head_y), R//4 + 1)
            # Eerie glow
            glow_eye = pygame.Surface((R, R), pygame.SRCALPHA)
            eye_ga = int(150 + 80 * math.sin(now_t * 0.005))
            pygame.draw.circle(glow_eye, (140, 200, 255, eye_ga), (R//2, R//2), R//3)
            tmp.blit(glow_eye, (ex - R//2, head_y - R//2))
        if wallpierce:
            # Phase shimmer — bright outline
            pygame.draw.ellipse(tmp, ac((140, 180, 255)), (ox - R, oy + bob - R, R*2, R*3), 2)

    # ── BOMBER ────────────────────────────────────────────────────────────────
    elif brawler_name == "bomber":
        now_t = pygame.time.get_ticks()
        # Legs with big boots
        lx1 = ox - int(R * 0.5) + int(leg_swing * R * 0.5)
        lx2 = ox + int(R * 0.5) - int(leg_swing * R * 0.5)
        for lx in [lx1, lx2]:
            pygame.draw.rect(tmp, (20, 15, 10, alpha), (lx - R//2 - 2, oy + R//2, int(R*1.2), int(R*1.3)), border_radius=4)
            pygame.draw.rect(tmp, ac((60, 50, 10)), (lx - R//2, oy + R//2, int(R*1.2), int(R*1.3)), border_radius=3)
            pygame.draw.rect(tmp, ac((100, 80, 20)), (lx - R//2, oy + R*2 - 5, int(R*1.2), 8), border_radius=3)
        # Bomber jacket body
        draw_outline_rect((ox - int(R*1.05), oy - int(R*0.6) + bob, int(R*2.1), int(R*1.7)), (60, 50, 10))
        # Jacket zips and pockets
        pygame.draw.line(tmp, ac((120, 100, 30)), (ox, oy - int(R*0.5) + bob), (ox, oy + int(R*0.8) + bob), 3)
        for py_off in [0, R//2]:
            pygame.draw.rect(tmp, ac((100, 80, 20)), (ox - R + R//4, oy + py_off + bob, R//2, R//3), border_radius=2)
            pygame.draw.rect(tmp, ac((100, 80, 20)), (ox + R//4, oy + py_off + bob, R//2, R//3), border_radius=2)
        # Bomb bag on back (visible as bump)
        bag_s = pygame.Surface((R*2, R*2), pygame.SRCALPHA)
        pygame.draw.ellipse(bag_s, (*((80, 60, 10)), min(alpha, 180)), (0, 0, R*2, R*2))
        pygame.draw.ellipse(bag_s, (*((40, 30, 5)), min(alpha, 180)), (0, 0, R*2, R*2), 2)
        arm_ang_back = math.radians(face_angle) + math.pi
        back_x = ox + int(math.cos(arm_ang_back) * R * 0.7)
        back_y = oy + bob + int(math.sin(arm_ang_back) * R * 0.3)
        tmp.blit(bag_s, (back_x - R, back_y - R))
        # Throwing arm with bomb
        arm_ang = math.radians(face_angle)
        throw_x = ox + int(math.cos(arm_ang) * R * 1.5)
        throw_y = oy + bob + int(math.sin(arm_ang) * R * 0.7)
        pygame.draw.line(tmp, (20, 15, 10, alpha), (ox, oy + bob), (throw_x, throw_y), R//2 + 2)
        pygame.draw.line(tmp, ac(skin), (ox, oy + bob), (throw_x, throw_y), R//2)
        # Bomb in hand
        starpower_active_local = starpower
        bomb_r = R//2 + (R//4 if starpower_active_local else 0)
        pygame.draw.circle(tmp, (20, 15, 10, alpha), (throw_x, throw_y), bomb_r + 2)
        pygame.draw.circle(tmp, ac((40, 40, 10)), (throw_x, throw_y), bomb_r)
        # Fuse spark
        fuse_ang = now_t * 0.008
        fx = throw_x + int(math.cos(fuse_ang) * bomb_r)
        fy = throw_y - bomb_r + int(math.sin(fuse_ang) * bomb_r * 0.3)
        pygame.draw.line(tmp, ac((140, 100, 20)), (throw_x, throw_y - bomb_r), (fx, fy), 2)
        spark_a = int(150 + 100 * math.sin(now_t * 0.02))
        spark_col = (255, 200, 50) if not starpower_active_local else (255, 100, 20)
        pygame.draw.circle(tmp, (*spark_col, spark_a), (fx, fy), 3)
        # Head with goggles and bandana
        head_y = oy - R + bob
        draw_outline_circle(ox, head_y, int(R * 0.92), skin)
        # Bandana / helmet
        pygame.draw.rect(tmp, (20, 15, 10, alpha), (ox - R + 1, head_y - R//3, R*2 - 2, R//2 + 2), border_radius=4)
        pygame.draw.rect(tmp, ac((100, 80, 20)), (ox - R + 2, head_y - R//3, R*2 - 4, R//2), border_radius=3)
        # Goggles
        for ex in [ox - R//3, ox + R//3]:
            pygame.draw.circle(tmp, (20, 15, 10, alpha), (ex, head_y + R//6), R//3 + 2)
            pygame.draw.circle(tmp, ac((60, 160, 80)), (ex, head_y + R//6), R//3)
            pygame.draw.circle(tmp, ac((100, 220, 120)), (ex - 1, head_y + R//6 - 1), R//5)
        pygame.draw.line(tmp, ac((120, 100, 30)), (ox - R//3 + R//3, head_y + R//6), (ox + R//3 - R//3, head_y + R//6), 2)
        # Grin below bandana
        smile_pts2 = [(ox - R//2, head_y + R//2), (ox - R//4, head_y + int(R*0.65)), (ox, head_y + int(R*0.7)), (ox + R//4, head_y + int(R*0.65)), (ox + R//2, head_y + R//2)]
        for i in range(len(smile_pts2) - 1):
            pygame.draw.line(tmp, ac((40, 20, 5)), smile_pts2[i], smile_pts2[i+1], 2)
        # Mega-bomb glow
        if starpower_active_local:
            mg = pygame.Surface(tmp.get_size(), pygame.SRCALPHA)
            ma = int(40 + 20 * math.sin(now_t * 0.01))
            pygame.draw.circle(mg, (255, 180, 20, ma), (ox, oy), R * 2)
            tmp.blit(mg, (0, 0))

    else:
        draw_outline_circle(ox, oy + bob, R, main_c)
        draw_outline_circle(ox, oy - R + bob, int(R*0.8), skin)

    # Shoot flash
    if shoot_flash > 0:
        arm_ang = math.radians(face_angle)
        flash_x = ox + int(math.cos(arm_ang) * R * 2)
        flash_y = oy + bob + int(math.sin(arm_ang) * R)
        flash_s = pygame.Surface((R*3, R*3), pygame.SRCALPHA)
        fa = min(255, shoot_flash * 30)
        pygame.draw.circle(flash_s, (*main_c, fa), (R*3//2, R*3//2), R*3//2)
        pygame.draw.circle(flash_s, (255, 255, 200, fa), (R*3//2, R*3//2), R)
        tmp.blit(flash_s, (flash_x - R*3//2, flash_y - R*3//2))

    surf.blit(tmp, (cx - ox, cy - oy))

def draw_brawler(surf, brawler_name, x, y, alpha=255, scale=1.0, starpower=False, alive=True):
    draw_brawler_detailed(surf, brawler_name, x, y, alpha=alpha, scale=scale,
                          starpower=starpower, alive=alive)

# ─── BULLET VISUALS PER WEAPON ────────────────────────────────────────────────
BULLET_STYLE = {
    "sniper":   {"color": (100, 220, 255), "size": 8,  "glow": (80,  200, 255), "trail": True},
    "minigun":  {"color": (255, 200,  50), "size": 5,  "glow": (255, 160,  30), "trail": False},
    "magic":    {"color": (220, 100, 255), "size": 7,  "glow": (180,  60, 255), "trail": True},
    "shotgun":  {"color": (255, 120,  40), "size": 6,  "glow": (255,  80,  20), "trail": False},
    "shuriken": {"color": (100, 255, 200), "size": 7,  "glow": ( 60, 220, 160), "trail": True},
    "orb":      {"color": (120, 255, 100), "size": 8,  "glow": ( 80, 200,  60), "trail": True},
    "ak47":     {"color": (255, 215,  50), "size": 5,  "glow": (255, 180,  20), "trail": False},
    # NEW
    "cannon":   {"color": (220,  60,  40), "size": 9,  "glow": (255, 100,  60), "trail": True},
    "phantom":  {"color": (160, 200, 255), "size": 8,  "glow": (120, 160, 255), "trail": True},
    "bomb":     {"color": ( 60,  60,  20), "size": 12, "glow": (100, 100,  30), "trail": False},
}

# ─── SHARED STATE ─────────────────────────────────────────────────────────────
server_players    = {}
server_bullets    = []
server_walls      = []
server_dyn_walls  = []   # dynamic walls from server

phase      = "startup"
phase_lock = threading.Lock()

my_name           = ""
my_brawler        = "sniper"
lobby_data        = {}
winner_name       = ""
was_kicked        = False
spectate_msg      = ""

lobby_anim_t      = 0
selected_brawler  = "sniper"
ready_local       = False
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
prev_hp = {}
prev_bomb_bullets = set()  # track bomb bullet ids to detect explosions

def receive():
    global server_players, server_bullets, server_walls, server_dyn_walls
    global lobby_data, winner_name, was_kicked, spectate_msg
    global ready_local, prev_hp

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
                cur = get_phase()

            elif p_msg == "lobby_spectate":
                spectate_msg = msg.get("msg", "")
                lobby_data = {}
                set_phase("lobby")
                play_music("menu")

            elif p_msg == "start":
                cur = get_phase()
                if cur in ("lobby", "name_entry", "brawler_select"):
                    set_phase("playing")
                    stop_music()

            elif p_msg == "running":
                new_players = msg.get("players", {})
                for addr, p in new_players.items():
                    old_hp = prev_hp.get(addr, 100)
                    new_hp = p.get("hp", 100)
                    if new_hp < old_hp and p.get("alive", True):
                        anim = get_anim(addr)
                        anim["hurt_t"] = 10
                        play_sound("hit")
                    prev_hp[addr] = new_hp

                prev_alive = {addr: p.get("alive", True) for addr, p in server_players.items()}
                server_players  = new_players
                server_bullets  = msg.get("bullets", [])
                server_walls    = msg.get("walls", [])
                server_dyn_walls = msg.get("dynamic_walls", [])

                for addr, p in server_players.items():
                    if addr in prev_alive and prev_alive[addr] and not p.get("alive", True):
                        if p.get("name") == my_name:
                            play_sound("death")

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
    send({"type": "brawler_select", "brawler": bname})

def send_ready(state):
    send({"type": "set_ready", "ready": state})

# ─── STARPOWER ────────────────────────────────────────────────────────────────
starpower_active   = False
starpower_start    = 0
starpower_duration = 5000
starpower_cooldown = 12000
last_starpower     = -20000
last_shot          = 0

def activate_starpower():
    global starpower_active, starpower_start, last_starpower
    now = pygame.time.get_ticks()
    if now - last_starpower < starpower_cooldown:
        return

    # Get current aim direction
    my_wx, my_wy = get_my_pos()
    mx_s, my_s = pygame.mouse.get_pos()
    twx, twy = screen_to_world(mx_s, my_s)
    ang = math.atan2(twy - my_wy, twx - my_wx)
    dx = math.cos(ang)
    dy = math.sin(ang)

    starpower_active = True
    starpower_start  = now
    last_starpower   = now
    send({"type": "starpower", "brawler": my_brawler, "active": True, "dx": dx, "dy": dy})

    # Instant-use abilities — auto-deactivate locally
    if my_brawler in ("tank", "ninja"):
        starpower_active = False

def update_starpower():
    global starpower_active
    if not starpower_active:
        return
    now = pygame.time.get_ticks()
    # Duration-based for mage/healer/berserker/ghost/bomber
    if my_brawler in ("tank", "ninja"):
        starpower_active = False
        return
    if now - starpower_start > starpower_duration:
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
    pulse = int(8 + 6 * math.sin(elapsed * 0.003))
    bg_surf = pygame.Surface((SCREEN_W, SCREEN_H))
    bg_surf.fill((pulse, pulse//2, 0))
    screen.blit(bg_surf, (0, 0))
    for i in range(5):
        r = int(50 + i * 80 + (elapsed * 0.06) % 400)
        a = max(0, 120 - i * 22 - int((elapsed * 0.06) % 400) // 4)
        s = pygame.Surface((r*2, r*2), pygame.SRCALPHA)
        pygame.draw.circle(s, (255, 200, 30, a), (r, r), r, 2)
        screen.blit(s, (SCREEN_W//2 - r, SCREEN_H//2 - r))
    alpha = min(255, int(elapsed / 1200 * 255))
    alpha = min(alpha, max(0, int((4500 - elapsed) / 600 * 255)))
    for dx2, dy2 in [(-3,0),(3,0),(0,-3),(0,3)]:
        s = font_huge.render(GAME_TITLE, True, (40, 20, 0))
        tmp = pygame.Surface(s.get_size(), pygame.SRCALPHA)
        tmp.blit(s, (0, 0)); tmp.set_alpha(alpha)
        screen.blit(tmp, (SCREEN_W//2 - s.get_width()//2 + dx2, SCREEN_H//2 - s.get_height()//2 + dy2))
    s = font_huge.render(GAME_TITLE, True, C_ACCENT)
    tmp = pygame.Surface(s.get_size(), pygame.SRCALPHA)
    tmp.blit(s, (0, 0)); tmp.set_alpha(alpha)
    screen.blit(tmp, (SCREEN_W//2 - s.get_width()//2, SCREEN_H//2 - s.get_height()//2))
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
    banner_h = 110
    banner = pygame.Surface((SCREEN_W, banner_h), pygame.SRCALPHA)
    for i in range(banner_h):
        a = int(200 * (1 - i / banner_h))
        pygame.draw.line(banner, (10, 12, 30, a), (0, i), (SCREEN_W, i))
    screen.blit(banner, (0, 0))
    pygame.draw.line(screen, C_ACCENT, (0, banner_h), (SCREEN_W, banner_h), 2)
    shake = int(2 * math.sin(t * 3))
    centered(GAME_TITLE, font_big, C_ACCENT, 22 + shake)
    centered("SELECT YOUR NAME", font_small, C_GRAY, 82)
    spacing = min(180, (SCREEN_W - 40) // len(BRAWLERS))
    total_w = spacing * len(BRAWLERS)
    start_x = cx - total_w // 2 + spacing // 2
    for i, (bname, bdata) in enumerate(BRAWLERS.items()):
        bx = start_x + i * spacing
        by = 155
        bob = int(6 * math.sin(t * 2 + i * 1.2))
        face_ang = 30 + i * 10
        preview = pygame.Surface((90, 100), pygame.SRCALPHA)
        draw_brawler_detailed(preview, bname, 45, 55, scale=1.8, face_angle=face_ang)
        screen.blit(preview, (bx - 45, by + bob))
        s = font_tiny.render(bname.upper(), True, bdata["color"])
        screen.blit(s, (bx - s.get_width()//2, by + 78 + bob))
    panel_x = cx - 220
    draw_panel(screen, panel_x, 240, 440, 60, color=(16, 20, 36), border=C_BLUE, radius=12)
    cursor = "|" if (pygame.time.get_ticks()//500)%2 else " "
    disp = name_input + cursor if name_input else cursor
    if not name_input:
        ph = font_med.render("Enter your name...", True, (55, 65, 90))
        screen.blit(ph, (cx - ph.get_width()//2, 253))
    else:
        s = font_med.render(disp, True, C_WHITE)
        screen.blit(s, (cx - s.get_width()//2, 253))
    if name_input.strip():
        draw_panel(screen, cx - 120, 320, 240, 46, color=(8, 28, 14), border=C_GREEN, radius=10)
        centered("PRESS ENTER  ▶", font_small, C_GREEN, 334)
    else:
        centered("Type your name to join", font_tiny, C_GRAY, 332)
    centered("ESC to quit", font_tiny, (50, 55, 75), 388)

# ─── LOBBY SCREEN ─────────────────────────────────────────────────────────────
lobby_hover_brawler = None

def draw_lobby():
    global lobby_hover_brawler
    draw_bg_grid()
    t = pygame.time.get_ticks() * 0.001
    draw_floating_stars(t)
    cx = SCREEN_W // 2
    now_ms = pygame.time.get_ticks()
    ld = lobby_data
    pygame.draw.rect(screen, (8, 10, 22), (0, 0, SCREEN_W, 80))
    pygame.draw.line(screen, C_ACCENT, (0, 80), (SCREEN_W, 80), 2)
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

    left_w   = 260
    right_w  = 240
    center_w = SCREEN_W - left_w - right_w - 40
    left_x   = 10
    right_x  = SCREEN_W - right_w - 10
    center_x = left_x + left_w + 10
    panel_y  = 92
    panel_h  = SCREEN_H - panel_y - 10

    # ── LEFT: Player list ──
    draw_panel(screen, left_x, panel_y, left_w, panel_h, color=(12, 14, 26), border=(30, 36, 60), radius=12)
    s = font_small.render("PLAYERS", True, C_ACCENT)
    screen.blit(s, (left_x + 14, panel_y + 14))
    lobby_ps = ld.get("lobby_players", [])
    pc = font_tiny.render(f"{len(lobby_ps)} / 10", True, C_GRAY)
    screen.blit(pc, (left_x + left_w - pc.get_width() - 12, panel_y + 17))
    pygame.draw.line(screen, (30, 34, 60), (left_x + 10, panel_y + 40), (left_x + left_w - 10, panel_y + 40), 1)
    for i, pdata in enumerate(lobby_ps[:10]):
        ry = panel_y + 50 + i * 52
        if ry + 50 > panel_y + panel_h - 6:
            break
        is_me    = pdata.get("name") == my_name
        is_ready = pdata.get("ready", False)
        is_spec  = pdata.get("spectating", False)
        bname_p  = pdata.get("brawler", "sniper")
        bdata_p  = BRAWLERS.get(bname_p, BRAWLERS["sniper"])
        row_col = (20, 24, 48) if is_me else (14, 16, 34)
        row_bdr = bdata_p["color"] if is_me else (30, 34, 58)
        pygame.draw.rect(screen, row_col, (left_x + 6, ry, left_w - 12, 46), border_radius=8)
        pygame.draw.rect(screen, row_bdr, (left_x + 6, ry, left_w - 12, 46), 1, border_radius=8)
        icon = pygame.Surface((54, 54), pygame.SRCALPHA)
        draw_brawler_detailed(icon, bname_p, 27, 32, scale=0.9, face_angle=20)
        screen.blit(icon, (left_x + 6, ry - 4))
        nc = C_ACCENT if is_me else C_WHITE
        ns = font_tiny.render(pdata.get("name", "?"), True, nc)
        screen.blit(ns, (left_x + 62, ry + 6))
        if is_spec:
            tag_col, tag_txt = C_GRAY, "SPECTATING"
        elif is_ready:
            tag_col, tag_txt = C_GREEN, "✓ READY"
        else:
            tag_col, tag_txt = (120, 110, 50), "NOT READY"
        ts = font_tiny.render(tag_txt, True, tag_col)
        screen.blit(ts, (left_x + 62, ry + 26))

    # ── CENTER: Brawler selection ──
    draw_panel(screen, center_x, panel_y, center_w, panel_h, color=(10, 12, 24), border=(28, 32, 58), radius=12)
    centered("CHOOSE YOUR BRAWLER", font_med, C_WHITE, panel_y + 16, x=center_x + center_w//2)
    brawler_names = list(BRAWLERS.keys())
    cols = min(len(brawler_names), 3)
    rows = math.ceil(len(brawler_names) / cols)
    card_w = min(200, (center_w - 20 - (cols-1)*10) // cols)
    card_h = min(280, (panel_h - 60 - (rows-1)*10) // rows)
    cards_total_w = cols * card_w + (cols-1) * 10
    card_start_x  = center_x + (center_w - cards_total_w) // 2
    mx_now, my_now = pygame.mouse.get_pos()
    brawler_rects = {}
    hover_b       = None

    for idx, bname in enumerate(brawler_names):
        col_i = idx % cols
        row_i = idx // cols
        bdata = BRAWLERS[bname]
        bx    = card_start_x + col_i * (card_w + 10)
        card_y = panel_y + 52 + row_i * (card_h + 10)
        hov   = bx <= mx_now <= bx + card_w and card_y <= my_now <= card_y + card_h
        sel   = (selected_brawler == bname)
        if hov: hover_b = bname
        brawler_rects[bname] = (bx, card_y, card_w, card_h)
        if sel:
            bg_col, bdr_col, bdr_w = (28, 22, 50), bdata["color"], 3
        elif hov:
            bg_col, bdr_col, bdr_w = (22, 20, 44), bdata["accent"], 2
        else:
            bg_col, bdr_col, bdr_w = (14, 16, 32), (32, 36, 64), 1
        if sel:
            glow = pygame.Surface((card_w + 20, card_h + 20), pygame.SRCALPHA)
            gc   = bdata["color"]
            ga   = int(40 + 20 * math.sin(t * 3))
            pygame.draw.rect(glow, (*gc, ga), (0, 0, card_w+20, card_h+20), border_radius=14)
            screen.blit(glow, (bx - 10, card_y - 10))
        pygame.draw.rect(screen, bg_col,  (bx, card_y, card_w, card_h), border_radius=12)
        pygame.draw.rect(screen, bdr_col, (bx, card_y, card_w, card_h), bdr_w, border_radius=12)
        bob_amt = int(5 * math.sin(t * 2 + idx * 1.1)) if (hov or sel) else 0
        art_size = 110
        art = pygame.Surface((art_size, art_size + 10), pygame.SRCALPHA)
        face_ang = 20 + math.sin(t + idx) * 15
        draw_brawler_detailed(art, bname, art_size//2, art_size//2 + 5,
                              scale=2.0, starpower=sel, face_angle=face_ang,
                              walk_phase=t * 3 if (hov or sel) else 0)
        screen.blit(art, (bx + card_w//2 - art_size//2, card_y + 8 + bob_amt))
        tag_s = font_tiny.render(bdata["tag"], True, bdata["color"])
        tb_x  = bx + card_w//2 - tag_s.get_width()//2 - 4
        pygame.draw.rect(screen, (10, 8, 20), (tb_x, card_y + 106, tag_s.get_width()+8, 18), border_radius=3)
        screen.blit(tag_s, (tb_x + 4, card_y + 107))
        ns = font_small.render(bname.upper(), True, bdata["color"] if (hov or sel) else C_WHITE)
        screen.blit(ns, (bx + card_w//2 - ns.get_width()//2, card_y + 126))
        pygame.draw.line(screen, (28, 32, 60), (bx + 10, card_y + 148), (bx + card_w - 10, card_y + 148), 1)
        for j, (lbl, val) in enumerate(bdata["stat_labels"]):
            ls = font_tiny.render(lbl, True, C_GRAY)
            vs = font_tiny.render(val, True, C_WHITE)
            screen.blit(ls, (bx + 10, card_y + 155 + j*20))
            screen.blit(vs, (bx + card_w - vs.get_width() - 10, card_y + 155 + j*20))
        desc_y = card_y + 155 + 3*20 + 4
        pygame.draw.line(screen, (28, 32, 60), (bx + 10, desc_y), (bx + card_w - 10, desc_y), 1)
        ds = font_tiny.render(bdata["desc"], True, C_GRAY)
        screen.blit(ds, (bx + card_w//2 - ds.get_width()//2, desc_y + 4))
        star_s = font_tiny.render("★ " + bdata["star"], True, C_ACCENT)
        screen.blit(star_s, (bx + card_w//2 - star_s.get_width()//2, desc_y + 20))
        if sel:
            sel_s = font_tiny.render("✓ SELECTED", True, C_GREEN)
            screen.blit(sel_s, (bx + card_w//2 - sel_s.get_width()//2, card_y + card_h - 18))

    lobby_hover_brawler = hover_b

    # ── RIGHT: Ready panel ──
    draw_panel(screen, right_x, panel_y, right_w, panel_h, color=(10, 12, 24), border=(28, 32, 58), radius=12)
    art2 = pygame.Surface((110, 120), pygame.SRCALPHA)
    face_ang2 = 15 + math.sin(t * 0.5) * 10
    draw_brawler_detailed(art2, selected_brawler, 55, 65, scale=2.2,
                          starpower=ready_local, face_angle=face_ang2,
                          walk_phase=t * 2 if ready_local else 0)
    screen.blit(art2, (right_x + right_w//2 - 55, panel_y + 10))
    cur_bdata = BRAWLERS.get(selected_brawler, BRAWLERS["sniper"])
    bname_s = font_med.render(selected_brawler.upper(), True, cur_bdata["color"])
    screen.blit(bname_s, (right_x + right_w//2 - bname_s.get_width()//2, panel_y + 118))

    if was_kicked:
        centered("You were kicked!", font_small, C_RED, panel_y + 148, x=right_x + right_w//2)
        centered("Wait for next game.", font_tiny, C_GRAY, panel_y + 172, x=right_x + right_w//2)
        return brawler_rects

    spec_self = any(lp.get("name") == my_name and lp.get("spectating", False)
                    for lp in lobby_data.get("lobby_players", []))
    if spec_self or game_running:
        centered("SPECTATING", font_med, C_GRAY, panel_y + 148, x=right_x + right_w//2)
        centered("Waiting for next round", font_tiny, (90, 95, 110), panel_y + 173, x=right_x + right_w//2)
        dots = "." * (1 + (now_ms // 500) % 3)
        ds2 = font_small.render(dots, True, C_GRAY)
        screen.blit(ds2, (right_x + right_w//2 - ds2.get_width()//2, panel_y + 196))
        return brawler_rects

    btn_y   = panel_y + 155
    btn_x   = right_x + 14
    btn_w   = right_w - 28
    btn_h   = 52
    btn_hov = btn_x <= mx_now <= btn_x + btn_w and btn_y <= my_now <= btn_y + btn_h
    if ready_local:
        btn_col, btn_bdr, btn_txt, btn_tc = (8, 38, 16), C_GREEN, "✓  READY!", C_GREEN
    else:
        pulse_b = int(40 * math.sin(now_ms * 0.005))
        btn_col = (28 + pulse_b//4, 24, 8)
        btn_bdr, btn_txt, btn_tc = C_ACCENT, "READY UP  ▶", C_ACCENT
    if btn_hov:
        btn_col = tuple(min(255, c + 15) for c in btn_col)
    pygame.draw.rect(screen, btn_col, (btn_x, btn_y, btn_w, btn_h), border_radius=12)
    pygame.draw.rect(screen, btn_bdr, (btn_x, btn_y, btn_w, btn_h), 2, border_radius=12)
    bs = font_med.render(btn_txt, True, btn_tc)
    screen.blit(bs, (btn_x + btn_w//2 - bs.get_width()//2, btn_y + btn_h//2 - bs.get_height()//2))
    pygame.draw.line(screen, (24, 28, 50), (right_x + 12, panel_y + 218), (right_x + right_w - 12, panel_y + 218), 1)
    rc   = ld.get("ready_count", 0)
    ta   = max(1, ld.get("total_active", 1))
    prog = rc / ta
    bar_bx = right_x + 12
    bar_bw = right_w - 24
    pygame.draw.rect(screen, (20, 22, 40), (bar_bx, panel_y + 226, bar_bw, 12), border_radius=6)
    pygame.draw.rect(screen, C_GREEN,      (bar_bx, panel_y + 226, int(bar_bw * prog), 12), border_radius=6)
    prog_s = font_tiny.render(f"{rc}/{ta} ready", True, C_GRAY)
    screen.blit(prog_s, (right_x + right_w//2 - prog_s.get_width()//2, panel_y + 242))
    if ta < 2:
        need_s = font_tiny.render("Need 2+ players", True, (90, 80, 50))
        screen.blit(need_s, (right_x + right_w//2 - need_s.get_width()//2, panel_y + 260))
    pygame.draw.line(screen, (24, 28, 50), (right_x + 12, panel_y + panel_h - 60), (right_x + right_w - 12, panel_y + panel_h - 60), 1)
    me_s = font_tiny.render(f"You:  {my_name}", True, C_BLUE)
    screen.blit(me_s, (right_x + right_w//2 - me_s.get_width()//2, panel_y + panel_h - 50))
    tip_s = font_tiny.render("ESC to quit", True, (50, 55, 75))
    screen.blit(tip_s, (right_x + right_w//2 - tip_s.get_width()//2, panel_y + panel_h - 28))
    return brawler_rects

# ─── SCREEN: DEAD ─────────────────────────────────────────────────────────────
def draw_dead_screen():
    draw_game()
    ov = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
    ov.fill((0, 0, 0, 160))
    screen.blit(ov, (0, 0))
    t  = pygame.time.get_ticks() * 0.001
    cy = SCREEN_H // 2 - 90
    skull_bob = int(8 * math.sin(t * 2))
    skull_s = font_huge.render("💀", True, C_RED)
    screen.blit(skull_s, (SCREEN_W//2 - skull_s.get_width()//2, cy + skull_bob))
    centered("YOU  DIED", font_big, C_RED, cy + 90)
    pygame.draw.line(screen, (80, 20, 20), (SCREEN_W//2 - 200, cy + 148), (SCREEN_W//2 + 200, cy + 148), 1)
    centered("Spectating until the round ends...", font_small, C_GRAY, cy + 160)
    centered("You'll return to the lobby when it's over.", font_small, (75, 78, 98), cy + 192)
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
    now_ms = pygame.time.get_ticks()
    trophy_bob = int(10 * math.sin(t * 2))
    trophy_s = font_huge.render("🏆", True, C_ACCENT)
    screen.blit(trophy_s, (cx - trophy_s.get_width()//2, cy + trophy_bob))
    centered("ROUND  OVER!", font_big, C_ACCENT, cy + 80)
    pygame.draw.line(screen, (60, 50, 10), (cx - 240, cy + 130), (cx + 240, cy + 130), 1)
    centered("WINNER", font_small, C_GRAY, cy + 142)
    centered(winner_name, font_big, C_GREEN, cy + 166)
    elapsed = now_ms - go_timer if go_timer else 0
    bw = int(480 * min(elapsed / 4000, 1.0))
    pygame.draw.rect(screen, (20, 24, 40), (cx - 240, cy + 240, 480, 18), border_radius=9)
    pygame.draw.rect(screen, C_ACCENT,     (cx - 240, cy + 240, bw,  18), border_radius=9)
    centered("Returning to lobby...", font_small, C_GRAY, cy + 268)
    if elapsed < 200 and elapsed > 10:
        for _ in range(3):
            px2 = cx + ((_ * 120) - 120)
            spawn_particles(px2, cy + 100, C_ACCENT, count=6, speed=4)
    update_draw_particles(screen)

# ─── TILE MAP GRAPHICS ────────────────────────────────────────────────────────
_tile_cache = {}

def get_tile_surface(tile_type, size=48):
    key = (tile_type, size)
    if key in _tile_cache:
        return _tile_cache[key]
    s = pygame.Surface((size, size))
    if tile_type == "grass_a":
        s.fill((58, 90, 42))
        for _ in range(4):
            gx = random.randint(4, size-4)
            gy = random.randint(4, size-4)
            pygame.draw.line(s, (80, 120, 50), (gx, gy), (gx-2, gy-5), 1)
            pygame.draw.line(s, (80, 120, 50), (gx+1, gy), (gx+3, gy-5), 1)
    elif tile_type == "grass_b":
        s.fill((52, 82, 38))
        for _ in range(2):
            gx = random.randint(4, size-4)
            gy = random.randint(4, size-4)
            pygame.draw.circle(s, (45, 75, 32), (gx, gy), 3)
    elif tile_type == "sand":
        s.fill((210, 185, 130))
        for _ in range(6):
            gx = random.randint(2, size-2)
            gy = random.randint(2, size-2)
            pygame.draw.circle(s, (225, 200, 145), (gx, gy), 1)
    _tile_cache[key] = s
    return s

random.seed(42)
TILE_PATTERN = [[random.choice(["grass_a", "grass_a", "grass_b"]) for _ in range(MAP_W // 48 + 2)]
                for _ in range(MAP_H // 48 + 2)]

def draw_ground_tiles():
    tile = 48
    off_x = int(cam_x % tile)
    off_y = int(cam_y % tile)
    base_tx = int(cam_x // tile)
    base_ty = int(cam_y // tile)
    for ix in range(-1, SCREEN_W // tile + 2):
        for iy in range(-1, SCREEN_H // tile + 2):
            tx = base_tx + ix
            ty = base_ty + iy
            if tx < 0 or ty < 0 or tx >= len(TILE_PATTERN[0]) or ty >= len(TILE_PATTERN):
                pygame.draw.rect(screen, (15, 20, 12), (ix*tile - off_x, iy*tile - off_y, tile, tile))
            else:
                tile_type = TILE_PATTERN[ty][tx]
                t_surf = get_tile_surface(tile_type, tile)
                screen.blit(t_surf, (ix*tile - off_x, iy*tile - off_y))

# ─── BUSH DRAWING ─────────────────────────────────────────────────────────────
_bush_cache = {}

def get_bush_surface(r, front=False):
    key = (r, front)
    if key in _bush_cache:
        return _bush_cache[key]
    size = r * 2 + 16
    s = pygame.Surface((size, size), pygame.SRCALPHA)
    cx = cy = size // 2
    if not front:
        sh = pygame.Surface((r*2 + 4, r + 6), pygame.SRCALPHA)
        pygame.draw.ellipse(sh, (0, 0, 0, 40), (0, 0, r*2+4, r+6))
        s.blit(sh, (cx - r - 2, cy + r//2))
        pygame.draw.circle(s, (20, 60, 15, 220), (cx, cy), r)
        pygame.draw.circle(s, (35, 85, 25, 220), (cx, cy - r//5), int(r * 0.85))
    else:
        for i in range(5):
            ang = math.pi * 2 / 5 * i + 0.3
            ox2 = int(math.cos(ang) * r * 0.4)
            oy2 = int(math.sin(ang) * r * 0.3)
            pygame.draw.circle(s, (45, 110, 30, 215), (cx + ox2, cy + oy2), int(r * 0.6))
        pygame.draw.circle(s, (65, 140, 40, 200), (cx, cy - r//3), int(r * 0.5))
        pygame.draw.circle(s, (80, 160, 50, 180), (cx - r//5, cy - r//2), int(r * 0.3))
        for i in range(8):
            ang = math.pi * 2 / 8 * i
            lx = cx + int(math.cos(ang) * r * 0.7)
            ly = cy + int(math.sin(ang) * r * 0.65)
            pygame.draw.circle(s, (55, 125, 35, 190), (lx, ly), max(3, r // 5))
        pygame.draw.circle(s, (90, 170, 55, 140), (cx - r//6, cy - r//2), r // 4)
    _bush_cache[key] = s
    return s

def draw_bushes_back():
    for b in BUSHES:
        sx, sy = world_to_screen(b["x"], b["y"])
        r = b["r"]
        if -r*2 < sx < SCREEN_W + r*2 and -r*2 < sy < SCREEN_H + r*2:
            bush_s = get_bush_surface(r, front=False)
            screen.blit(bush_s, (sx - r - 8, sy - r - 8))

def draw_bushes_front():
    for b in BUSHES:
        sx, sy = world_to_screen(b["x"], b["y"])
        r = b["r"]
        if -r*2 < sx < SCREEN_W + r*2 and -r*2 < sy < SCREEN_H + r*2:
            bush_s = get_bush_surface(r, front=True)
            screen.blit(bush_s, (sx - r - 8, sy - r - 8))

# ─── WALL DRAWING ─────────────────────────────────────────────────────────────
_wall_cache = {}

def draw_wall_detailed(w, wx2, wy2):
    ww, wh = w["w"], w["h"]
    key = (ww, wh)
    if key not in _wall_cache:
        s = pygame.Surface((ww + 8, wh + 8), pygame.SRCALPHA)
        pygame.draw.rect(s, (0, 0, 0, 60), (4, 6, ww, wh), border_radius=4)
        pygame.draw.rect(s, (90, 85, 100), (0, 0, ww, wh), border_radius=4)
        pygame.draw.rect(s, (115, 110, 128), (0, 0, ww, wh - 4), border_radius=4)
        pygame.draw.rect(s, (140, 135, 155), (2, 2, ww - 4, max(4, wh // 4)), border_radius=3)
        if ww > 40:
            brick_h = max(12, wh // 2)
            for row in range(0, wh, brick_h):
                offset = (row // brick_h % 2) * (ww // 3)
                for bx_start in range(-offset, ww, ww // 3):
                    if 0 < bx_start + ww // 3 < ww:
                        pygame.draw.line(s, (70, 65, 82), (bx_start + ww // 3, row + 2), (bx_start + ww // 3, min(wh - 2, row + brick_h - 2)), 1)
                pygame.draw.line(s, (70, 65, 82), (2, row + brick_h), (ww - 2, row + brick_h), 1)
        for i in range(max(1, ww // 40)):
            mx2 = int(ww * (0.2 + 0.6 * i / max(1, ww // 40 - 1))) if ww // 40 > 1 else ww // 2
            pygame.draw.circle(s, (50, 100, 40, 120), (mx2, wh - 4), max(3, ww // 20))
        pygame.draw.rect(s, (50, 45, 60), (0, 0, ww, wh), 2, border_radius=4)
        _wall_cache[key] = s
    screen.blit(_wall_cache[key], (wx2 - 4, wy2 - 2))

def draw_dynamic_wall(dw):
    """Draw a tank-placed wall with an HP bar above it."""
    sx, sy = world_to_screen(dw["x"], dw["y"])
    ww, wh = dw["w"], dw["h"]

    if sx + ww < -20 or sx > SCREEN_W + 20 or sy + wh < -20 or sy > SCREEN_H + 20:
        return

    hp_pct = max(0, dw["hp"] / dw["max_hp"])

    # Tint the wall orange/yellow to distinguish from static walls
    surf = pygame.Surface((ww + 8, wh + 8), pygame.SRCALPHA)
    # Shadow
    pygame.draw.rect(surf, (0, 0, 0, 60), (4, 6, ww, wh), border_radius=4)
    # Base — warm brown/orange stone
    base_col = (160, 120, 60)
    mid_col  = (180, 140, 80)
    top_col  = (200, 165, 100)
    pygame.draw.rect(surf, base_col, (0, 0, ww, wh), border_radius=4)
    pygame.draw.rect(surf, mid_col,  (0, 0, ww, wh - 4), border_radius=4)
    pygame.draw.rect(surf, top_col,  (2, 2, ww - 4, max(4, wh // 4)), border_radius=3)
    # Crack lines based on damage
    if hp_pct < 0.75:
        crack_col = (80, 55, 20, int(200 * (1 - hp_pct)))
        pygame.draw.line(surf, crack_col, (ww//3, 2), (ww//4, wh - 2), 2)
    if hp_pct < 0.4:
        pygame.draw.line(surf, crack_col, (ww*2//3, 2), (ww*3//4, wh - 2), 2)
        pygame.draw.line(surf, crack_col, (ww//2, wh//3), (ww//3, wh*2//3), 1)
    # Outline — orange glow
    glow_a = int(180 + 60 * math.sin(pygame.time.get_ticks() * 0.004))
    pygame.draw.rect(surf, (255, 180, 40, glow_a), (0, 0, ww, wh), 2, border_radius=4)
    screen.blit(surf, (sx - 4, sy - 2))

    # ── HP bar above the wall ──
    bar_w  = ww
    bar_h  = 8
    bar_x  = sx
    bar_y  = sy - 16
    # Background
    pygame.draw.rect(screen, (30, 10, 10), (bar_x - 1, bar_y - 1, bar_w + 2, bar_h + 2), border_radius=3)
    pygame.draw.rect(screen, (60, 20, 20), (bar_x, bar_y, bar_w, bar_h), border_radius=2)
    # Fill
    fill_w = int(bar_w * hp_pct)
    if fill_w > 0:
        hp_col = C_GREEN if hp_pct > 0.5 else (C_ACCENT if hp_pct > 0.25 else C_RED)
        pygame.draw.rect(screen, hp_col, (bar_x, bar_y, fill_w, bar_h), border_radius=2)
        # Shine
        pygame.draw.rect(screen, tuple(min(255, c + 60) for c in hp_col),
                         (bar_x, bar_y, fill_w, 3), border_radius=2)
    # HP text
    hp_txt = font_tiny.render(f"{int(dw['hp'])}/{dw['max_hp']}", True, C_WHITE)
    screen.blit(hp_txt, (bar_x + bar_w//2 - hp_txt.get_width()//2, bar_y - 14))

    # Owner label
    owner_txt = font_tiny.render(f"🧱 {dw.get('owner_name','')}", True, (220, 180, 80))
    screen.blit(owner_txt, (bar_x + bar_w//2 - owner_txt.get_width()//2, bar_y + bar_h + 2))

# ─── MAP BORDER ───────────────────────────────────────────────────────────────
def draw_map_border():
    bx2, by2 = world_to_screen(0, 0)
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
    for thickness, col in [(6, (60, 40, 20)), (4, (140, 100, 40)), (2, (200, 160, 60))]:
        pygame.draw.rect(screen, col, (bx2 - thickness, by2 - thickness, MAP_W + thickness*2, MAP_H + thickness*2), thickness)

# ─── CROSSHAIR ────────────────────────────────────────────────────────────────
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
    my_wx, my_wy = get_my_pos()
    mx_s, my_s   = pygame.mouse.get_pos()
    twx, twy = screen_to_world(mx_s, my_s)
    ang = math.atan2(twy - my_wy, twx - my_wx)
    now = pygame.time.get_ticks()
    if now - last_shot < 50:
        return
    last_shot = now
    play_sound("shoot")
    my_addr = None
    for addr, p in server_players.items():
        if p.get("name") == my_name:
            my_addr = addr
            break
    if my_addr:
        anim = get_anim(my_addr)
        anim["shoot_flash"] = 8
        anim["face_dir"] = math.degrees(ang)
    send({"type": "shoot", "dx": math.cos(ang), "dy": math.sin(ang)})

# ─── AoE EXPLOSION VISUAL ─────────────────────────────────────────────────────
# Track bombs to detect when they disappear (explode)
prev_bomb_set = set()

def draw_game():
    global prev_bomb_set

    draw_ground_tiles()
    update_starpower()
    draw_map_border()

    # Static walls
    for w in server_walls:
        wx2, wy2 = world_to_screen(w["x"], w["y"])
        if wx2 + w["w"] < -8 or wx2 > SCREEN_W + 8 or wy2 + w["h"] < -8 or wy2 > SCREEN_H + 8:
            continue
        draw_wall_detailed(w, wx2, wy2)

    # Dynamic walls (tank walls) — draw before bushes so they're behind characters
    for dw in server_dyn_walls:
        draw_dynamic_wall(dw)

    draw_bushes_back()

    # Detect bomb explosions: bomb bullet that disappeared = exploded
    cur_bomb_set = set()
    for b in server_bullets:
        if b.get("is_bomb"):
            bid = (round(b["x"]), round(b["y"]))
            cur_bomb_set.add(bid)
    for old_bomb in prev_bomb_set:
        if old_bomb not in cur_bomb_set:
            # It exploded — spawn visual
            bsx, bsy = world_to_screen(old_bomb[0], old_bomb[1])
            spawn_explosion_particles(bsx, bsy, radius=80)
    prev_bomb_set = cur_bomb_set

    sorted_players = sorted(server_players.items(), key=lambda kv: kv[1].get("y", 0))

    for addr, p in sorted_players:
        px_w, py_w = p["x"], p["y"]
        px, py   = world_to_screen(int(px_w), int(py_w))
        is_me    = (p.get("name") == my_name)
        bname_p  = WEAPON_TO_BRAWLER.get(p.get("weapon", "ak47"), "sniper")
        invisible = p.get("invisible", False)
        sp_on    = p.get("starpower", False)
        alive    = p.get("alive", True)
        spec     = p.get("spectating", False)
        invincible = p.get("invincible", False)
        rage     = p.get("rage", False)
        wallpierce = p.get("wallpierce", False)

        if spec and not is_me:
            continue
        if not is_me and invisible:
            continue
        if not is_me and in_bush(px_w, py_w):
            continue

        if not alive:
            alpha = 80
        elif invisible and is_me:
            alpha = 85
        elif in_bush(px_w, py_w) and is_me:
            alpha = 150
        else:
            alpha = 255

        anim = get_anim(addr)
        dx_move = px_w - anim["last_x"]
        dy_move = py_w - anim["last_y"]
        move_dist = math.hypot(dx_move, dy_move)
        if move_dist > 0.5:
            anim["walk_t"] += move_dist * 0.15
            anim["face_dir"] = math.degrees(math.atan2(dy_move, dx_move))
        anim["last_x"] = px_w
        anim["last_y"] = py_w

        if is_me:
            mx_s, my_s = pygame.mouse.get_pos()
            twx, twy = screen_to_world(mx_s, my_s)
            anim["face_dir"] = math.degrees(math.atan2(twy - py_w, twx - px_w))

        if anim["shoot_flash"] > 0:
            anim["shoot_flash"] -= 1
        if anim["hurt_t"] > 0:
            anim["hurt_t"] -= 1
        if anim.get("teleport_flash", 0) > 0:
            anim["teleport_flash"] -= 1

        sh = pygame.Surface((36, 12), pygame.SRCALPHA)
        pygame.draw.ellipse(sh, (0, 0, 0, 60), (0, 0, 36, 12))
        screen.blit(sh, (px - 18, py + 16))

        draw_brawler_detailed(
            screen, bname_p, px, py,
            alpha=alpha, scale=1.0,
            starpower=sp_on and is_me,
            alive=alive,
            face_angle=anim["face_dir"],
            walk_phase=anim["walk_t"],
            shoot_flash=anim["shoot_flash"],
            hurt_flash=anim["hurt_t"],
            invincible=invincible,
            rage=rage,
            wallpierce=wallpierce,
            teleport_flash=anim.get("teleport_flash", 0),
        )

        if is_me and my_brawler:
            ring = pygame.Surface((42, 42), pygame.SRCALPHA)
            rc2  = BRAWLERS[my_brawler]["color"]
            now_t2 = pygame.time.get_ticks()
            ring_a = int(160 + 60 * math.sin(now_t2 * 0.004))
            pygame.draw.circle(ring, (*rc2, ring_a), (21, 21), 20, 2)
            screen.blit(ring, (px - 21, py - 21))

        if not alive:
            continue

        nc = C_ACCENT if is_me else C_WHITE
        ns_sh = font_tiny.render(p.get("name","?"), True, C_DARK)
        ns    = font_tiny.render(p.get("name","?"), True, nc)
        name_y = py - 42
        screen.blit(ns_sh, (px - ns.get_width()//2 + 1, name_y + 1))
        screen.blit(ns,    (px - ns.get_width()//2,   name_y))

        hp_pct = max(0, p["hp"] / 100)
        hp_col = C_GREEN if hp_pct > 0.5 else (C_ACCENT if hp_pct > 0.25 else C_RED)
        # Healer invincible — golden bar
        if invincible:
            hp_col = (255, 215, 0)
        bar_w3 = 40
        bar_x3 = px - bar_w3 // 2
        bar_y3 = py - 30
        pygame.draw.rect(screen, (20, 8, 8),  (bar_x3 - 1, bar_y3 - 1, bar_w3 + 2, 7), border_radius=3)
        pygame.draw.rect(screen, (40, 15, 15),  (bar_x3, bar_y3, bar_w3, 5), border_radius=2)
        fill_w = int(bar_w3 * hp_pct)
        if fill_w > 0:
            pygame.draw.rect(screen, hp_col, (bar_x3, bar_y3, fill_w, 5), border_radius=2)
            pygame.draw.rect(screen, tuple(min(255, c + 60) for c in hp_col), (bar_x3, bar_y3, fill_w, 2), border_radius=2)

        if sp_on and is_me:
            now_t3 = pygame.time.get_ticks()
            gr    = int(20 + 4 * math.sin(now_t3 * 0.006))
            gs    = pygame.Surface((gr*2+6, gr*2+6), pygame.SRCALPHA)
            sc2   = BRAWLERS.get(bname_p, BRAWLERS["sniper"])["accent"]
            pygame.draw.circle(gs, (*sc2, 50), (gr+3, gr+3), gr)
            screen.blit(gs, (px - gr - 3, py - gr - 3))

    # ── Bullets ──
    for b in server_bullets:
        bx2, by2 = world_to_screen(int(b["x"]), int(b["y"]))
        if bx2 < -30 or bx2 > SCREEN_W + 30 or by2 < -30 or by2 > SCREEN_H + 30:
            continue
        style = BULLET_STYLE.get(b.get("weapon", "ak47"), BULLET_STYLE["ak47"])
        pierce = b.get("pierce", False)
        wall_p = b.get("wall_pierce", False)
        col  = (255, 80, 80) if pierce else style["color"]
        if wall_p:
            col = tuple(min(255, c + 80) for c in col)
        size = style["size"]

        # Bomb special drawing — dark round bomb with fuse
        if b.get("is_bomb"):
            bomb_r = size
            is_mega = b.get("aoe_radius", 100) > 100
            if is_mega:
                bomb_r = int(size * 1.5)
                # Big glow
                gs_b = pygame.Surface((bomb_r*4, bomb_r*4), pygame.SRCALPHA)
                pygame.draw.circle(gs_b, (255, 150, 20, 60), (bomb_r*2, bomb_r*2), bomb_r*2)
                screen.blit(gs_b, (bx2 - bomb_r*2, by2 - bomb_r*2))
            pygame.draw.circle(screen, (20, 20, 5), (bx2, by2), bomb_r + 2)
            pygame.draw.circle(screen, (50, 50, 10), (bx2, by2), bomb_r)
            # Fuse spark
            now_fuse = pygame.time.get_ticks()
            fuse_ang = now_fuse * 0.008
            fx = bx2 + int(math.cos(fuse_ang) * bomb_r)
            fy = by2 - bomb_r + int(math.sin(fuse_ang) * bomb_r * 0.3)
            pygame.draw.line(screen, (140, 100, 20), (bx2, by2 - bomb_r), (fx, fy), 2)
            spark_a = int(150 + 100 * math.sin(now_fuse * 0.02))
            pygame.draw.circle(screen, (255, 200, 50), (fx, fy), 3)
            continue

        # Ghost slow orb special
        if b.get("weapon") == "phantom":
            orb_r = size
            now_orb = pygame.time.get_ticks()
            # Pulsing slow orb
            pulse_r = int(orb_r + 3 * math.sin(now_orb * 0.01))
            gs_orb = pygame.Surface((pulse_r*4, pulse_r*4), pygame.SRCALPHA)
            pygame.draw.circle(gs_orb, (100, 140, 255, 50), (pulse_r*2, pulse_r*2), pulse_r*2)
            screen.blit(gs_orb, (bx2 - pulse_r*2, by2 - pulse_r*2))
            pygame.draw.circle(screen, (200, 220, 255), (bx2, by2), orb_r + 2, 2)
            pygame.draw.circle(screen, col, (bx2, by2), orb_r)
            # Snowflake-like slow indicator
            for si in range(6):
                s_ang = math.pi / 3 * si + now_orb * 0.002
                sx_sp = bx2 + int(math.cos(s_ang) * orb_r)
                sy_sp = by2 + int(math.sin(s_ang) * orb_r)
                pygame.draw.line(screen, (200, 220, 255), (bx2, by2), (sx_sp, sy_sp), 1)
            continue

        if style.get("trail"):
            trail_len = 3
            dx_t = b.get("dx", 0)
            dy_t = b.get("dy", 0)
            for ti in range(trail_len):
                trail_x = bx2 - int(dx_t * b.get("speed", 8) * (ti + 1))
                trail_y = by2 - int(dy_t * b.get("speed", 8) * (ti + 1) * 0.4)
                ta2 = max(0, 100 - ti * 35)
                tr2 = max(1, size - ti * 2)
                ts2 = pygame.Surface((tr2*2, tr2*2), pygame.SRCALPHA)
                pygame.draw.circle(ts2, (*col, ta2), (tr2, tr2), tr2)
                screen.blit(ts2, (trail_x - tr2, trail_y - tr2))

        glow_r = size + 5
        gs3 = pygame.Surface((glow_r*2 + 4, glow_r*2 + 4), pygame.SRCALPHA)
        gcol = style["glow"]
        pygame.draw.circle(gs3, (*gcol, 70), (glow_r+2, glow_r+2), glow_r)
        pygame.draw.circle(gs3, (*gcol, 100), (glow_r+2, glow_r+2), glow_r - 2)
        screen.blit(gs3, (bx2 - glow_r - 2, by2 - glow_r - 2))
        pygame.draw.circle(screen, (255, 255, 255), (bx2, by2), max(2, size - 3))
        pygame.draw.circle(screen, col, (bx2, by2), size)

    draw_bushes_front()
    update_draw_particles(screen)
    draw_hud()
    mxp, myp = pygame.mouse.get_pos()
    ch_col = BRAWLERS[my_brawler]["color"] if my_brawler else C_WHITE
    draw_crosshair(mxp, myp, ch_col)

def draw_hud():
    now_ms = pygame.time.get_ticks()
    if not my_brawler: return
    bdata = BRAWLERS[my_brawler]
    cxh   = SCREEN_W // 2

    # Brawler info panel
    draw_panel(screen, 6, 6, 260, 68, color=(10,12,22), border=(32,36,58))
    badge = pygame.Surface((68, 68), pygame.SRCALPHA)
    draw_brawler_detailed(badge, my_brawler, 34, 38, scale=1.2,
                          face_angle=20, walk_phase=pygame.time.get_ticks() * 0.002)
    screen.blit(badge, (6, 2))
    s1 = font_small.render(my_brawler.upper(), True, bdata["color"])
    screen.blit(s1, (76, 12))
    s2 = font_tiny.render("[F] Starpower: " + bdata["star"], True, C_GRAY)
    screen.blit(s2, (76, 36))

    # Active ability status indicators
    my_p = None
    for addr, p in server_players.items():
        if p.get("name") == my_name:
            my_p = p
            break

    if my_p:
        status_items = []
        if my_p.get("invincible"):
            status_items.append(("🛡 INVINCIBLE", (100, 220, 255)))
        if my_p.get("rage"):
            status_items.append(("⚡ RAGE!", (255, 80, 20)))
        if my_p.get("wallpierce"):
            status_items.append(("👻 PHASE", (140, 180, 255)))
        for si, (txt, col) in enumerate(status_items):
            ts = font_small.render(txt, True, col)
            ax = SCREEN_W - ts.get_width() - 12
            ay = SCREEN_H - 80 - si * 28
            pygame.draw.rect(screen, (8, 10, 20), (ax - 6, ay - 3, ts.get_width() + 12, 24), border_radius=6)
            screen.blit(ts, (ax, ay))

    # Minimap
    mm_w, mm_h = 192, 108
    mm_x = SCREEN_W - mm_w - 10
    mm_y = 10
    scale_x = mm_w / MAP_W
    scale_y = mm_h / MAP_H
    draw_panel(screen, mm_x-3, mm_y-3, mm_w+6, mm_h+6, color=(8,10,18), border=(30,34,55), radius=5)
    pygame.draw.rect(screen, (40, 60, 30), (mm_x, mm_y, mm_w, mm_h))
    for w in server_walls:
        wx2 = mm_x + int(w["x"] * scale_x)
        wy2 = mm_y + int(w["y"] * scale_y)
        ww2 = max(2, int(w["w"] * scale_x))
        wh2 = max(2, int(w["h"] * scale_y))
        pygame.draw.rect(screen, (100, 95, 115), (wx2, wy2, ww2, wh2))
    # Dynamic walls on minimap
    for dw in server_dyn_walls:
        dwx = mm_x + int(dw["x"] * scale_x)
        dwy = mm_y + int(dw["y"] * scale_y)
        dww = max(2, int(dw["w"] * scale_x))
        dwh = max(2, int(dw["h"] * scale_y))
        pygame.draw.rect(screen, (220, 160, 60), (dwx, dwy, dww, dwh))
    for addr, p in server_players.items():
        mmx = mm_x + int(p["x"] * scale_x)
        mmy = mm_y + int(p["y"] * scale_y)
        is_me2 = p.get("name") == my_name
        col = C_ACCENT if is_me2 else C_RED
        if not p.get("alive", True): col = C_GRAY
        r_mm = 4 if is_me2 else 3
        pygame.draw.circle(screen, (0,0,0), (mmx, mmy), r_mm + 1)
        pygame.draw.circle(screen, col, (mmx, mmy), r_mm)
    vx = mm_x + int(cam_x * scale_x)
    vy = mm_y + int(cam_y * scale_y)
    vw = max(1, int(SCREEN_W * scale_x))
    vh = max(1, int(SCREEN_H * scale_y))
    pygame.draw.rect(screen, (200,200,200), (vx, vy, vw, vh), 1)

    # Starpower bar
    bar_w2 = 340
    bx3, by3, bh3 = cxh - bar_w2//2, SCREEN_H - 36, 22
    draw_panel(screen, bx3-3, by3-3, bar_w2+6, bh3+6, color=(8,10,18), border=(30,34,55), radius=7)

    # Get SP cooldown from server
    sp_cd_left = 0.0
    if my_p:
        sp_cd_left = float(my_p.get("sp_cd_left", 0.0))

    if starpower_active:
        elapsed2 = now_ms - starpower_start
        progress = 1.0 - min(elapsed2 / starpower_duration, 1.0)
        col2  = bdata["color"]
        label = "STARPOWER  ACTIVE"
        pulse2 = int(bar_w2 * progress)
        pygame.draw.rect(screen, (18,8,38), (bx3, by3, bar_w2, bh3), border_radius=5)
        if pulse2 > 0:
            pygame.draw.rect(screen, col2, (bx3, by3, pulse2, bh3), border_radius=5)
        shim = pygame.Surface((max(1, pulse2), bh3), pygame.SRCALPHA)
        sa = int(55 + 35*math.sin(now_ms*0.012))
        pygame.draw.rect(shim, (255,255,255,sa), (0,0,max(1,pulse2),bh3//2))
        screen.blit(shim, (bx3, by3))
    elif sp_cd_left > 0.1:
        # Show cooldown based on server-reported remaining time
        progress = 1.0 - (sp_cd_left / 12.0)
        col2  = C_GRAY
        secs_left = int(sp_cd_left) + 1
        label = f"COOLDOWN  {secs_left}s"
        pygame.draw.rect(screen, (18,18,28), (bx3, by3, bar_w2, bh3), border_radius=5)
        pygame.draw.rect(screen, col2, (bx3, by3, int(bar_w2 * progress), bh3), border_radius=5)
    else:
        col2  = C_ACCENT
        label = "STARPOWER  READY  [F]"
        blink = (now_ms//600)%2
        pygame.draw.rect(screen, (28,24,8) if blink else (18,18,10), (bx3, by3, bar_w2, bh3), border_radius=5)
        if blink:
            pygame.draw.rect(screen, col2, (bx3, by3, bar_w2, bh3), border_radius=5)

    ls = font_tiny.render(label, True, col2)
    screen.blit(ls, (cxh - ls.get_width()//2, by3+4))

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

        elif cur_phase == "lobby":
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mx_e, my_e = event.pos
                for bname, rect in lobby_rects.items():
                    rx, ry, rw, rh = rect
                    if rx <= mx_e <= rx+rw and ry <= my_e <= ry+rh:
                        if selected_brawler != bname:
                            selected_brawler = bname
                            my_brawler = bname
                            send_brawler_select(bname)
                            spawn_particles(mx_e, my_e, BRAWLERS[bname]["color"], count=10, speed=5)
                        break
                right_x = SCREEN_W - 240 - 10
                right_w_btn = 240
                panel_y_btn = 92
                btn_y = panel_y_btn + 155
                btn_x = right_x + 14
                btn_w_sz = right_w_btn - 28
                btn_h_sz = 52
                spec_self2   = any(lp.get("name") == my_name and lp.get("spectating", False)
                                   for lp in lobby_data.get("lobby_players", []))
                game_running2 = lobby_data.get("game_running", False)
                if not was_kicked and not spec_self2 and not game_running2:
                    if btn_x <= mx_e <= btn_x + btn_w_sz and btn_y <= my_e <= btn_y + btn_h_sz:
                        ready_local = not ready_local
                        send_ready(ready_local)
                        if ready_local:
                            spawn_particles(btn_x + btn_w_sz//2, btn_y + btn_h_sz//2, C_GREEN, count=12, speed=4)

        elif cur_phase == "playing":
            if event.type == pygame.KEYDOWN and event.key == pygame.K_f:
                activate_starpower()
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mouse_held = True
                try_shoot()
            if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                mouse_held = False

    if cur_phase == "playing" and mouse_held:
        try_shoot()

    if cur_phase == "playing":
        keys = pygame.key.get_pressed()
        send({"type": "move",
              "up":    bool(keys[pygame.K_w]),
              "down":  bool(keys[pygame.K_s]),
              "left":  bool(keys[pygame.K_a]),
              "right": bool(keys[pygame.K_d])})

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

    if cur_phase == "lobby":
        now_ms_hb = pygame.time.get_ticks()
        if now_ms_hb - getattr(draw_lobby, "_last_hb", 0) > 1000:
            draw_lobby._last_hb = now_ms_hb
            join_lobby()

    cur_phase = get_phase()

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
