import socket
import threading
import json
import time
import math

HOST = "0.0.0.0"
PORT = 5555

server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server.bind((HOST, PORT))

MAX_PLAYERS = 10
INACTIVE_TIMEOUT = 60

MAP_W = 3840
MAP_H = 2160

PLAYER_RADIUS = 20

# ─── AUTHORITATIVE BRAWLER STATS ─────────────────────────────────────────────
BRAWLER_STATS = {
    "sniper": {
        "weapon":       "sniper",
        "damage":       80,
        "bullet_speed": 32,
        "cooldown":     0.7,
        "pierce":       False,
        "spread":       0,
        "spread_angle": 0,
        "range":        900,   # max bullet travel distance in pixels
    },
    "minigun": {
        "weapon":       "minigun",
        "damage":       14,
        "bullet_speed": 16,
        "cooldown":     0.08,
        "pierce":       False,
        "spread":       0,
        "spread_angle": 0,
        "range":        380,
    },
    "mage": {
        "weapon":       "magic",
        "damage":       40,
        "bullet_speed": 18,
        "cooldown":     0.35,
        "pierce":       False,
        "spread":       0,
        "spread_angle": 0,
        "range":        520,
    },
    "tank": {
        "weapon":       "shotgun",
        "damage":       28,
        "bullet_speed": 14,
        "cooldown":     1.0,
        "pierce":       False,
        "spread":       4,
        "spread_angle": 15,
        "range":        260,
    },
    "ninja": {
        "weapon":       "shuriken",
        "damage":       22,
        "bullet_speed": 22,
        "cooldown":     0.15,
        "pierce":       False,
        "spread":       0,
        "spread_angle": 0,
        "range":        450,
    },
    "healer": {
        "weapon":       "orb",
        "damage":       32,
        "bullet_speed": 18,
        "cooldown":     0.45,
        "pierce":       False,
        "spread":       0,
        "spread_angle": 0,
        "range":        480,
    },
    "berserker": {
        "weapon":       "cannon",
        "damage":       55,
        "bullet_speed": 10,
        "cooldown":     0.5,
        "pierce":       False,
        "spread":       2,
        "spread_angle": 10,
        "range":        320,
    },
    "ghost": {
        "weapon":       "phantom",
        "damage":       30,
        "bullet_speed": 8,
        "cooldown":     0.6,
        "pierce":       False,
        "spread":       0,
        "spread_angle": 0,
        "range":        400,
    },
    "bomber": {
        "weapon":       "bomb",
        "damage":       45,
        "bullet_speed": 12,
        "cooldown":     1.2,
        "pierce":       False,
        "spread":       0,
        "spread_angle": 0,
        "range":        350,
    },
}

BRAWLER_SPEED = {
    "sniper":    5,
    "minigun":   4,
    "mage":      5,
    "tank":      3,
    "ninja":     7,
    "healer":    5,
    "berserker": 4,
    "ghost":     6,
    "bomber":    4,
}

# ─── REGENERATION CONFIG ─────────────────────────────────────────────────────
# Time after last hit before regen starts (seconds)
REGEN_DELAY      = 3.0
# HP regenerated per second
REGEN_RATE       = 8.0
# Regen tick interval
REGEN_TICK       = 0.1

# ─── GAME STATE ───────────────────────────────────────────────────────────────
game_phase   = "lobby"
players      = {}
bullets      = []
kicked_names = set()

dynamic_walls = []
_dwall_id_counter = 0

MAP_WALLS = [
    # ── TOP-LEFT QUADRANT ──
    {"x": 400,  "y": 250,  "w": 300, "h": 24},
    {"x": 1200, "y": 250,  "w": 300, "h": 24},
    {"x": 700,  "y": 500,  "w": 250, "h": 24},
    {"x": 980,  "y": 500,  "w": 250, "h": 24},
    {"x": 400,  "y": 780,  "w": 300, "h": 24},
    {"x": 1200, "y": 780,  "w": 300, "h": 24},
    {"x": 150,  "y": 300,  "w": 24,  "h": 200},
    {"x": 1746, "y": 300,  "w": 24,  "h": 200},
    {"x": 150,  "y": 600,  "w": 24,  "h": 200},
    {"x": 1746, "y": 600,  "w": 24,  "h": 200},
    {"x": 860,  "y": 400,  "w": 200, "h": 24},
    {"x": 948,  "y": 300,  "w": 24,  "h": 200},
    {"x": 280,  "y": 180,  "w": 120, "h": 120},
    {"x": 1520, "y": 180,  "w": 120, "h": 120},
    {"x": 280,  "y": 780,  "w": 120, "h": 120},
    {"x": 1520, "y": 780,  "w": 120, "h": 120},
    # ── TOP-RIGHT QUADRANT ──
    {"x": 2320, "y": 250,  "w": 300, "h": 24},
    {"x": 3120, "y": 250,  "w": 300, "h": 24},
    {"x": 2620, "y": 500,  "w": 250, "h": 24},
    {"x": 2900, "y": 500,  "w": 250, "h": 24},
    {"x": 2320, "y": 780,  "w": 300, "h": 24},
    {"x": 3120, "y": 780,  "w": 300, "h": 24},
    {"x": 2070, "y": 300,  "w": 24,  "h": 200},
    {"x": 3666, "y": 300,  "w": 24,  "h": 200},
    {"x": 2070, "y": 600,  "w": 24,  "h": 200},
    {"x": 3666, "y": 600,  "w": 24,  "h": 200},
    {"x": 2780, "y": 400,  "w": 200, "h": 24},
    {"x": 2868, "y": 300,  "w": 24,  "h": 200},
    {"x": 2100, "y": 180,  "w": 120, "h": 120},
    {"x": 3440, "y": 180,  "w": 120, "h": 120},
    {"x": 2100, "y": 780,  "w": 120, "h": 120},
    {"x": 3440, "y": 780,  "w": 120, "h": 120},
    # ── BOTTOM-LEFT QUADRANT ──
    {"x": 400,  "y": 1330, "w": 300, "h": 24},
    {"x": 1200, "y": 1330, "w": 300, "h": 24},
    {"x": 700,  "y": 1580, "w": 250, "h": 24},
    {"x": 980,  "y": 1580, "w": 250, "h": 24},
    {"x": 400,  "y": 1860, "w": 300, "h": 24},
    {"x": 1200, "y": 1860, "w": 300, "h": 24},
    {"x": 150,  "y": 1380, "w": 24,  "h": 200},
    {"x": 1746, "y": 1380, "w": 24,  "h": 200},
    {"x": 150,  "y": 1680, "w": 24,  "h": 200},
    {"x": 1746, "y": 1680, "w": 24,  "h": 200},
    {"x": 860,  "y": 1480, "w": 200, "h": 24},
    {"x": 948,  "y": 1380, "w": 24,  "h": 200},
    {"x": 280,  "y": 1160, "w": 120, "h": 120},
    {"x": 1520, "y": 1160, "w": 120, "h": 120},
    {"x": 280,  "y": 1860, "w": 120, "h": 120},
    {"x": 1520, "y": 1860, "w": 120, "h": 120},
    # ── BOTTOM-RIGHT QUADRANT ──
    {"x": 2320, "y": 1330, "w": 300, "h": 24},
    {"x": 3120, "y": 1330, "w": 300, "h": 24},
    {"x": 2620, "y": 1580, "w": 250, "h": 24},
    {"x": 2900, "y": 1580, "w": 250, "h": 24},
    {"x": 2320, "y": 1860, "w": 300, "h": 24},
    {"x": 3120, "y": 1860, "w": 300, "h": 24},
    {"x": 2070, "y": 1380, "w": 24,  "h": 200},
    {"x": 3666, "y": 1380, "w": 24,  "h": 200},
    {"x": 2070, "y": 1680, "w": 24,  "h": 200},
    {"x": 3666, "y": 1680, "w": 24,  "h": 200},
    {"x": 2780, "y": 1480, "w": 200, "h": 24},
    {"x": 2868, "y": 1380, "w": 24,  "h": 200},
    {"x": 2100, "y": 1160, "w": 120, "h": 120},
    {"x": 3440, "y": 1160, "w": 120, "h": 120},
    {"x": 2100, "y": 1860, "w": 120, "h": 120},
    {"x": 3440, "y": 1860, "w": 120, "h": 120},
    # ── CENTER DIVIDERS ──
    {"x": 600,  "y": 1060, "w": 200, "h": 20},
    {"x": 1100, "y": 1060, "w": 200, "h": 20},
    {"x": 2520, "y": 1060, "w": 200, "h": 20},
    {"x": 3020, "y": 1060, "w": 200, "h": 20},
    {"x": 1900, "y": 300,  "w": 20,  "h": 200},
    {"x": 1900, "y": 900,  "w": 20,  "h": 200},
    {"x": 1900, "y": 1380, "w": 20,  "h": 200},
    {"x": 1900, "y": 1800, "w": 20,  "h": 200},
    # ── CENTER CROSS ──
    {"x": 1760, "y": 1040, "w": 320, "h": 24},
    {"x": 1908, "y": 900,  "w": 24,  "h": 360},
]

SPAWN_POINTS = [
    (120,  120),  (3720, 120),  (120,  2040), (3720, 2040),
    (1920, 120),  (1920, 2040), (120,  1080), (3720, 1080),
    (960,  540),  (2880, 540),  (960,  1620), (2880, 1620),
    (480,  300),  (3360, 300),  (480,  1860), (3360, 1860),
    (1920, 1080), (700,  1080), (3140, 1080), (1920, 600),
]

def get_spawn():
    idx = len(players) % len(SPAWN_POINTS)
    return SPAWN_POINTS[idx]

def new_player(name="Player", spawn=None, brawler="sniper"):
    sx, sy = spawn if spawn else (100, 100)
    stats = BRAWLER_STATS.get(brawler, BRAWLER_STATS["sniper"])
    return {
        "x": float(sx), "y": float(sy),
        "hp": 100,
        "alive": True,
        "brawler": brawler,
        "weapon": stats["weapon"],
        "last_shot": 0.0,
        "last_activity": time.time(),
        "invisible": False,
        "starpower": False,
        "name": name,
        "phase": "lobby",
        "ready": False,
        "spectating": False,
        "in_game": False,
        "last_heal_tick": time.time(),
        "sp_cooldown_end": 0.0,
        "invincible_until": 0.0,
        "rage_until": 0.0,
        "wallpierce_until": 0.0,
        "face_dx": 1.0,
        "face_dy": 0.0,
        # ── Regen state ──
        "last_hit_time": 0.0,       # timestamp of last damage taken
        "regen_accumulator": 0.0,   # fractional HP accumulator for smooth regen
        "slow_until": 0.0,
    }

# ─── WALL HELPERS ─────────────────────────────────────────────────────────────
def all_walls():
    return list(MAP_WALLS) + [dw for dw in dynamic_walls]

def collide_wall(x, y, r=PLAYER_RADIUS, wall_list=None):
    if wall_list is None:
        wall_list = all_walls()
    for w in wall_list:
        closest_x = max(w["x"], min(x, w["x"] + w["w"]))
        closest_y = max(w["y"], min(y, w["y"] + w["h"]))
        if math.hypot(x - closest_x, y - closest_y) < r:
            return True
    return False

def clamp_to_map(x, y, r=PLAYER_RADIUS):
    return max(r, min(x, MAP_W - r)), max(r, min(y, MAP_H - r))

def bullet_hits_wall(bx, by, wall_list=None):
    if wall_list is None:
        wall_list = all_walls()
    for w in wall_list:
        if w["x"] < bx < w["x"] + w["w"] and w["y"] < by < w["y"] + w["h"]:
            return w
    return None

def bullet_out_of_bounds(bx, by):
    return bx < 0 or bx > MAP_W or by < 0 or by > MAP_H

# ─── TANK: PLACE DYNAMIC WALL ─────────────────────────────────────────────────
TANK_WALL_W   = 120
TANK_WALL_H   = 24
TANK_WALL_HP  = 150
TANK_WALL_DIST = 60
TANK_WALL_MAX_PER_PLAYER = 2

def place_tank_wall(p):
    global _dwall_id_counter
    owner_name = p["name"]
    existing = [dw for dw in dynamic_walls if dw.get("owner_name") == owner_name]
    if len(existing) >= TANK_WALL_MAX_PER_PLAYER:
        oldest = existing[0]
        if oldest in dynamic_walls:
            dynamic_walls.remove(oldest)
    fdx = p.get("face_dx", 1.0)
    fdy = p.get("face_dy", 0.0)
    length = math.hypot(fdx, fdy)
    if length == 0:
        fdx, fdy = 1.0, 0.0
    else:
        fdx /= length
        fdy /= length
    cx = p["x"] + fdx * TANK_WALL_DIST
    cy = p["y"] + fdy * TANK_WALL_DIST
    wx = cx - TANK_WALL_W / 2
    wy = cy - TANK_WALL_H / 2
    wx = max(PLAYER_RADIUS, min(wx, MAP_W - TANK_WALL_W - PLAYER_RADIUS))
    wy = max(PLAYER_RADIUS, min(wy, MAP_H - TANK_WALL_H - PLAYER_RADIUS))
    for sw in MAP_WALLS:
        margin = 10
        if (wx < sw["x"] + sw["w"] + margin and
            wx + TANK_WALL_W > sw["x"] - margin and
            wy < sw["y"] + sw["h"] + margin and
            wy + TANK_WALL_H > sw["y"] - margin):
            wx2 = wx + fdx * (TANK_WALL_W + 10)
            wy2 = wy + fdy * (TANK_WALL_H + 10)
            wx2 = max(PLAYER_RADIUS, min(wx2, MAP_W - TANK_WALL_W - PLAYER_RADIUS))
            wy2 = max(PLAYER_RADIUS, min(wy2, MAP_H - TANK_WALL_H - PLAYER_RADIUS))
            wx, wy = wx2, wy2
            break
    _dwall_id_counter += 1
    dw = {
        "x":          wx,
        "y":          wy,
        "w":          TANK_WALL_W,
        "h":          TANK_WALL_H,
        "hp":         TANK_WALL_HP,
        "max_hp":     TANK_WALL_HP,
        "owner_name": owner_name,
        "id":         _dwall_id_counter,
        "is_dynamic": True,
        "expires":    time.time() + 12.0,
    }
    dynamic_walls.append(dw)
    print(f"🧱 {owner_name} placed wall at ({int(wx)},{int(wy)})")

# ─── GHOST: SLOW EFFECT ───────────────────────────────────────────────────────
GHOST_SLOW_DURATION = 2.0
GHOST_SLOW_FACTOR   = 0.4

# ─── BOMBER: AOE EXPLOSION ────────────────────────────────────────────────────
BOMB_AOE_RADIUS = 100

def trigger_explosion(bx, by, damage, owner_addr, aoe_radius=BOMB_AOE_RADIUS):
    hit_any = False
    for addr, p in list(players.items()):
        if str(addr) == str(owner_addr):
            continue
        if not p["alive"] or p.get("spectating", False):
            continue
        dist = math.hypot(p["x"] - bx, p["y"] - by)
        if dist < aoe_radius:
            falloff = 1.0 - (dist / aoe_radius) * 0.5
            actual_dmg = int(damage * falloff)
            if time.time() < p.get("invincible_until", 0):
                continue
            p["hp"] -= actual_dmg
            p["last_hit_time"] = time.time()   # reset regen timer
            hit_any = True
            if p["hp"] <= 0:
                p["alive"]      = False
                p["spectating"] = True
                print(f"💀 {p['name']} killed by explosion")
                check_round_end()
    return hit_any

def build_lobby_state():
    lobby_players = []
    for addr, p in players.items():
        lobby_players.append({
            "name":       p["name"],
            "brawler":    p.get("brawler", "sniper"),
            "ready":      p.get("ready", False),
            "spectating": p.get("spectating", False),
        })
    active_lobby = [p for p in players.values()
                    if not p.get("spectating", False) and p["name"] not in kicked_names]
    total_active = len(active_lobby)
    ready_count  = sum(1 for p in active_lobby if p.get("ready", False))
    can_start    = total_active >= 2 and ready_count == total_active
    return {
        "phase":         "lobby",
        "lobby_players": lobby_players,
        "player_count":  len(players),
        "ready_count":   ready_count,
        "total_active":  total_active,
        "can_start":     can_start,
        "game_running":  game_phase == "running",
    }

def broadcast_lobby():
    msg = json.dumps(build_lobby_state()).encode()
    for addr in list(players.keys()):
        try:
            server.sendto(msg, addr)
        except:
            pass

def check_all_ready():
    if game_phase != "lobby":
        return
    active = [p for p in players.values()
              if p["phase"] == "lobby" and p["name"] not in kicked_names]
    if len(active) < 2:
        return
    if all(p.get("ready", False) for p in active):
        start_game()

def start_game():
    global game_phase, bullets, kicked_names
    game_phase = "running"
    bullets.clear()
    dynamic_walls.clear()
    kicked_names.clear()
    participating = [(addr, p) for addr, p in players.items()
                     if not p.get("spectating", False)]
    for addr, p in players.items():
        p["in_game"]    = False
        p["spectating"] = False
    spawn_list = list(SPAWN_POINTS)
    for i, (addr, p) in enumerate(participating):
        sx, sy = spawn_list[i % len(spawn_list)]
        brawler = p.get("brawler", "sniper")
        stats   = BRAWLER_STATS.get(brawler, BRAWLER_STATS["sniper"])
        p["x"]               = float(sx)
        p["y"]               = float(sy)
        p["hp"]              = 100
        p["alive"]           = True
        p["phase"]           = "playing"
        p["weapon"]          = stats["weapon"]
        p["last_shot"]       = 0.0
        p["invisible"]       = False
        p["starpower"]       = False
        p["ready"]           = False
        p["spectating"]      = False
        p["in_game"]         = True
        p["last_heal_tick"]  = time.time()
        p["invincible_until"]  = 0.0
        p["rage_until"]        = 0.0
        p["wallpierce_until"]  = 0.0
        p["sp_cooldown_end"]   = 0.0
        p["slow_until"]        = 0.0
        p["face_dx"]           = 1.0
        p["face_dy"]           = 0.0
        p["last_hit_time"]     = 0.0
        p["regen_accumulator"] = 0.0
    print(f"🎮 Game started with {len(participating)} players!")
    msg = json.dumps({"phase": "start"}).encode()
    for addr, p in players.items():
        try:
            if p["phase"] == "playing":
                server.sendto(msg, addr)
            else:
                server.sendto(json.dumps({
                    "phase": "lobby_spectate",
                    "msg":   "Game started without you. Wait for next round!"
                }).encode(), addr)
        except:
            pass

def check_round_end():
    global game_phase
    if game_phase != "running":
        return
    in_game_all   = [addr for addr, p in players.items() if p.get("in_game", False)]
    in_game_alive = [addr for addr in in_game_all if players[addr]["alive"]]
    if len(in_game_all) >= 2 and len(in_game_alive) <= 1:
        winner_name = players[in_game_alive[0]]["name"] if in_game_alive else "Nobody"
        print(f"🏆 Round over! Winner: {winner_name}")
        game_phase = "lobby"
        dynamic_walls.clear()
        for p in players.values():
            p["phase"]      = "lobby"
            p["alive"]      = True
            p["hp"]         = 100
            p["ready"]      = False
            p["spectating"] = False
            p["in_game"]    = False
        msg = json.dumps({"phase": "game_over", "winner": winner_name}).encode()
        for addr in list(players.keys()):
            try:
                server.sendto(msg, addr)
            except:
                pass

def handle():
    while True:
        data, addr = server.recvfrom(2048)
        try:
            msg = json.loads(data.decode())
        except:
            continue

        if addr not in players:
            if len(players) >= MAX_PLAYERS:
                continue
            name = msg.get("name", f"Player{len(players)+1}")
            if game_phase == "running" and name in kicked_names:
                try:
                    server.sendto(json.dumps({"phase": "kicked"}).encode(), addr)
                except:
                    pass
                continue
            players[addr] = new_player(name=name, spawn=get_spawn())
            if game_phase == "running":
                players[addr]["spectating"] = True
                players[addr]["phase"]      = "lobby"
                try:
                    server.sendto(json.dumps({
                        "phase": "lobby_spectate",
                        "msg":   "A game is in progress. You'll join next round!"
                    }).encode(), addr)
                except:
                    pass
            else:
                broadcast_lobby()
            print(f"✅ {name} connected ({addr})")
            continue

        p = players[addr]
        p["last_activity"] = time.time()

        if msg.get("type") == "join_lobby":
            name = msg.get("name", p["name"])
            p["name"] = name
            if game_phase == "running" and name in kicked_names:
                try:
                    server.sendto(json.dumps({"phase": "kicked"}).encode(), addr)
                except:
                    pass
                continue
            if game_phase == "running" and p["phase"] != "playing":
                p["spectating"] = True
                p["phase"]      = "lobby"
                try:
                    server.sendto(json.dumps({
                        "phase": "lobby_spectate",
                        "msg":   "A game is in progress. You'll join next round!"
                    }).encode(), addr)
                except:
                    pass
            else:
                if game_phase == "lobby":
                    p["phase"] = "lobby"
                    broadcast_lobby()
            continue

        if msg.get("type") == "brawler_select":
            if game_phase == "lobby":
                brawler = msg.get("brawler", "sniper")
                if brawler not in BRAWLER_STATS:
                    brawler = "sniper"
                p["brawler"] = brawler
                p["weapon"]  = BRAWLER_STATS[brawler]["weapon"]
                broadcast_lobby()
            continue

        if msg.get("type") == "set_ready":
            if game_phase == "lobby" and not p.get("spectating", False) and p["name"] not in kicked_names:
                p["ready"] = msg.get("ready", False)
                broadcast_lobby()
                check_all_ready()
            continue

        if game_phase == "lobby":
            continue
        if p["name"] in kicked_names:
            continue
        if p.get("spectating", False) or not p["alive"]:
            continue

        brawler = p.get("brawler", "sniper")
        stats   = BRAWLER_STATS.get(brawler, BRAWLER_STATS["sniper"])
        speed   = BRAWLER_SPEED.get(brawler, 5)
        now = time.time()

        if now < p.get("slow_until", 0):
            speed = max(1, int(speed * GHOST_SLOW_FACTOR))
        if brawler == "berserker" and now < p.get("rage_until", 0):
            speed = int(speed * 1.6)

        if msg.get("type") == "move":
            dx = (-speed if msg.get("left") else 0) + (speed if msg.get("right") else 0)
            dy = (-speed if msg.get("up")   else 0) + (speed if msg.get("down")  else 0)
            nx, ny = clamp_to_map(p["x"] + dx, p["y"] + dy)
            walls_now = all_walls()
            if collide_wall(nx, ny, wall_list=walls_now):
                nx_only, _ = clamp_to_map(p["x"] + dx, p["y"])
                if not collide_wall(nx_only, p["y"], wall_list=walls_now):
                    p["x"] = nx_only
                else:
                    _, ny_only = clamp_to_map(p["x"], p["y"] + dy)
                    if not collide_wall(p["x"], ny_only, wall_list=walls_now):
                        p["y"] = ny_only
            else:
                p["x"], p["y"] = nx, ny

        elif msg.get("type") == "starpower":
            active = msg.get("active", False)
            raw_dx = msg.get("dx", p.get("face_dx", 1.0))
            raw_dy = msg.get("dy", p.get("face_dy", 0.0))
            length = math.hypot(raw_dx, raw_dy)
            if length > 0:
                p["face_dx"] = raw_dx / length
                p["face_dy"] = raw_dy / length
            sp_cd = p.get("sp_cooldown_end", 0)
            if now < sp_cd and active:
                continue
            p["starpower"] = active
            if active:
                SP_COOLDOWN = 12.0
                if brawler == "mage":
                    p["invisible"] = True
                elif brawler == "tank":
                    place_tank_wall(p)
                    p["starpower"] = False
                    p["sp_cooldown_end"] = now + SP_COOLDOWN
                elif brawler == "ninja":
                    TELEPORT_DIST = 160
                    fdx = p.get("face_dx", 1.0)
                    fdy = p.get("face_dy", 0.0)
                    tx = p["x"] + fdx * TELEPORT_DIST
                    ty = p["y"] + fdy * TELEPORT_DIST
                    tx, ty = clamp_to_map(tx, ty)
                    walls_now = all_walls()
                    if not collide_wall(tx, ty, wall_list=walls_now):
                        p["x"] = tx
                        p["y"] = ty
                    else:
                        for step in [120, 80, 40]:
                            tx2 = p["x"] + fdx * step
                            ty2 = p["y"] + fdy * step
                            tx2, ty2 = clamp_to_map(tx2, ty2)
                            if not collide_wall(tx2, ty2, wall_list=walls_now):
                                p["x"] = tx2
                                p["y"] = ty2
                                break
                    p["starpower"] = False
                    p["sp_cooldown_end"] = now + SP_COOLDOWN
                elif brawler == "healer":
                    p["invincible_until"] = now + 3.0
                    p["sp_cooldown_end"]  = now + SP_COOLDOWN
                elif brawler == "berserker":
                    p["rage_until"]      = now + 4.0
                    p["sp_cooldown_end"] = now + SP_COOLDOWN
                elif brawler == "ghost":
                    p["wallpierce_until"] = now + 4.0
                    p["sp_cooldown_end"]  = now + SP_COOLDOWN
                elif brawler == "bomber":
                    p["mega_bomb_shots"]  = 3
                    p["sp_cooldown_end"]  = now + SP_COOLDOWN
            else:
                if brawler == "mage":
                    p["invisible"] = False

        elif msg.get("type") == "shoot":
            shoot_now = time.time()
            cd = stats["cooldown"]
            if p.get("starpower") and brawler == "minigun":
                cd *= 0.4
            if shoot_now - p["last_shot"] < cd:
                continue
            p["last_shot"] = shoot_now
            raw_dx = msg.get("dx", 0)
            raw_dy = msg.get("dy", 0)
            length = math.hypot(raw_dx, raw_dy)
            if length == 0:
                continue
            dx_n = raw_dx / length
            dy_n = raw_dy / length
            p["face_dx"] = dx_n
            p["face_dy"] = dy_n
            pierce = stats["pierce"]
            if brawler == "sniper" and p.get("starpower"):
                pierce = True
            wall_pierce = shoot_now < p.get("wallpierce_until", 0)
            dmg = stats["damage"]
            if brawler == "berserker" and shoot_now < p.get("rage_until", 0):
                dmg = int(dmg * 1.5)
            aoe_r = BOMB_AOE_RADIUS
            if brawler == "bomber" and p.get("mega_bomb_shots", 0) > 0:
                aoe_r = int(BOMB_AOE_RADIUS * 1.8)
                dmg   = int(dmg * 1.4)
                p["mega_bomb_shots"] -= 1
                if p["mega_bomb_shots"] <= 0:
                    p["starpower"] = False
            slow_bullet = (brawler == "ghost")
            bullet_range = stats.get("range", 600)
            # Sniper range doubles with starpower
            if brawler == "sniper" and p.get("starpower"):
                bullet_range = int(bullet_range * 1.5)

            spread_count = stats["spread"]
            if spread_count > 0:
                total_pellets = spread_count + 1
                half = spread_count / 2.0
                base_ang = math.atan2(dy_n, dx_n)
                ang_step = math.radians(stats["spread_angle"])
                for i in range(total_pellets):
                    ang = base_ang + ang_step * (i - half)
                    b_entry = {
                        "x":          p["x"],
                        "y":          p["y"],
                        "dx":         math.cos(ang),
                        "dy":         math.sin(ang),
                        "speed":      stats["bullet_speed"],
                        "damage":     dmg,
                        "owner":      str(addr),
                        "pierce":     pierce,
                        "wall_pierce": wall_pierce,
                        "weapon":     stats["weapon"],
                        "slow":       slow_bullet,
                        "is_bomb":    (brawler == "bomber"),
                        "aoe_radius": aoe_r,
                        "range":      bullet_range,
                        "traveled":   0.0,
                        "spawn_x":    p["x"],
                        "spawn_y":    p["y"],
                    }
                    bullets.append(b_entry)
            else:
                b_entry = {
                    "x":          p["x"],
                    "y":          p["y"],
                    "dx":         dx_n,
                    "dy":         dy_n,
                    "speed":      stats["bullet_speed"],
                    "damage":     dmg,
                    "owner":      str(addr),
                    "pierce":     pierce,
                    "wall_pierce": wall_pierce,
                    "weapon":     stats["weapon"],
                    "slow":       slow_bullet,
                    "is_bomb":    (brawler == "bomber"),
                    "aoe_radius": aoe_r,
                    "range":      bullet_range,
                    "traveled":   0.0,
                    "spawn_x":    p["x"],
                    "spawn_y":    p["y"],
                }
                bullets.append(b_entry)

def check_inactive_players():
    while True:
        now = time.time()
        for addr in list(players.keys()):
            if now - players[addr]["last_activity"] > INACTIVE_TIMEOUT:
                print(f"❌ TIMEOUT: {players[addr]['name']} ({addr})")
                del players[addr]
                if game_phase == "lobby":
                    broadcast_lobby()
        time.sleep(2)

def game_loop():
    last_regen_tick = time.time()

    while True:
        if game_phase == "running":
            now = time.time()

            # ── Expire dynamic walls ──────────────────────────────────────────
            for dw in list(dynamic_walls):
                if now > dw.get("expires", now + 1):
                    dynamic_walls.remove(dw)

            # ── Healer passive regen ──────────────────────────────────────────
            for addr, p in players.items():
                if p.get("brawler") == "healer" and p["alive"] and not p.get("spectating"):
                    regen = 2
                    if p.get("starpower"):
                        regen = 4
                    if now - p.get("last_heal_tick", now) >= 1.0:
                        p["hp"] = min(100, p["hp"] + regen)
                        p["last_heal_tick"] = now

            # ── Universal HP Regeneration (Brawl Stars style) ─────────────────
            # Runs every REGEN_TICK seconds
            if now - last_regen_tick >= REGEN_TICK:
                last_regen_tick = now
                for addr, p in players.items():
                    if not p["alive"] or p.get("spectating", False):
                        continue
                    if p["hp"] >= 100:
                        p["regen_accumulator"] = 0.0
                        continue
                    # Don't regen if recently hit or is healer (has own system)
                    time_since_hit = now - p.get("last_hit_time", 0.0)
                    if time_since_hit < REGEN_DELAY:
                        p["regen_accumulator"] = 0.0
                        continue
                    if p.get("brawler") == "healer":
                        continue   # healer uses its own regen above
                    # Accumulate fractional HP
                    p["regen_accumulator"] += REGEN_RATE * REGEN_TICK
                    regen_int = int(p["regen_accumulator"])
                    if regen_int >= 1:
                        p["hp"] = min(100, p["hp"] + regen_int)
                        p["regen_accumulator"] -= regen_int

            # ── Auto-deactivate starpowers ────────────────────────────────────
            for addr, p in players.items():
                b = p.get("brawler")
                if b == "healer" and p.get("starpower"):
                    if now >= p.get("invincible_until", 0):
                        p["starpower"] = False
                elif b == "berserker" and p.get("starpower"):
                    if now >= p.get("rage_until", 0):
                        p["starpower"] = False
                elif b == "ghost" and p.get("starpower"):
                    if now >= p.get("wallpierce_until", 0):
                        p["starpower"] = False

            # ── Bullet movement & collision ───────────────────────────────────
            HIT_RADIUS = 24
            walls_now  = all_walls()

            for b in bullets[:]:
                step_dist = b["speed"]
                b["x"] += b["dx"] * step_dist
                b["y"] += b["dy"] * step_dist
                b["traveled"] = b.get("traveled", 0.0) + step_dist

                # Range check — remove bullet if it exceeded its max range
                if b["traveled"] >= b.get("range", 99999):
                    # For bombs, trigger a faded explosion at range limit
                    if b.get("is_bomb"):
                        trigger_explosion(b["x"], b["y"], b["damage"] // 2,
                                          b["owner"], aoe_radius=b.get("aoe_radius", BOMB_AOE_RADIUS))
                    if b in bullets:
                        bullets.remove(b)
                    continue

                if bullet_out_of_bounds(b["x"], b["y"]):
                    if b in bullets:
                        bullets.remove(b)
                    continue

                # Wall collision
                if not b.get("wall_pierce", False):
                    hit_wall = bullet_hits_wall(b["x"], b["y"], wall_list=walls_now)
                    if hit_wall:
                        if b.get("is_bomb"):
                            trigger_explosion(b["x"], b["y"], b["damage"], b["owner"],
                                              aoe_radius=b.get("aoe_radius", BOMB_AOE_RADIUS))
                        if hit_wall.get("is_dynamic"):
                            hit_wall["hp"] -= b["damage"]
                            if hit_wall["hp"] <= 0 and hit_wall in dynamic_walls:
                                dynamic_walls.remove(hit_wall)
                                print(f"🧱 Dynamic wall destroyed!")
                        if b in bullets:
                            bullets.remove(b)
                        continue

                # Player collision
                hit_player = False
                for addr, p in list(players.items()):
                    if str(addr) == b["owner"] or not p["alive"]:
                        continue
                    if p.get("spectating", False):
                        continue
                    if math.hypot(p["x"] - b["x"], p["y"] - b["y"]) < HIT_RADIUS:
                        if now < p.get("invincible_until", 0):
                            if not b.get("pierce"):
                                hit_player = True
                                break
                            continue

                        if b.get("is_bomb"):
                            trigger_explosion(b["x"], b["y"], b["damage"], b["owner"],
                                              aoe_radius=b.get("aoe_radius", BOMB_AOE_RADIUS))
                        else:
                            p["hp"] -= b["damage"]
                            p["last_hit_time"] = now      # reset regen delay
                            p["regen_accumulator"] = 0.0  # clear accumulator

                        if b.get("slow"):
                            p["slow_until"] = now + GHOST_SLOW_DURATION

                        if p["hp"] <= 0:
                            p["alive"]      = False
                            p["spectating"] = True
                            print(f"💀 {p['name']} died → spectating")
                            check_round_end()

                        if not b.get("pierce"):
                            hit_player = True
                            break

                if hit_player and b in bullets:
                    bullets.remove(b)

            # ── Broadcast game state ──────────────────────────────────────────
            players_out = {}
            for addr, p in players.items():
                entry = dict(p)
                entry["invincible"] = now < p.get("invincible_until", 0)
                entry["rage"]       = now < p.get("rage_until", 0)
                entry["wallpierce"] = now < p.get("wallpierce_until", 0)
                sp_cd_left = max(0.0, p.get("sp_cooldown_end", 0) - now)
                entry["sp_cd_left"] = round(sp_cd_left, 1)
                # Time until regen starts (for client display)
                time_since_hit = now - p.get("last_hit_time", 0.0)
                regen_delay_left = max(0.0, REGEN_DELAY - time_since_hit)
                entry["regen_delay_left"] = round(regen_delay_left, 2)
                entry["is_regenning"] = (
                    regen_delay_left <= 0.0 and
                    p["hp"] < 100 and
                    p["alive"] and
                    not p.get("spectating", False) and
                    p.get("brawler") != "healer"
                )
                players_out[str(addr)] = entry

            # Only send range info in bullets (not spawn coords, save bandwidth)
            bullets_out = []
            for b in bullets:
                bo = dict(b)
                bullets_out.append(bo)

            state = json.dumps({
                "phase":         "running",
                "players":       players_out,
                "bullets":       bullets_out,
                "walls":         MAP_WALLS,
                "dynamic_walls": dynamic_walls,
            }).encode()
            for addr in list(players.keys()):
                try:
                    server.sendto(state, addr)
                except:
                    pass

        time.sleep(1 / 60)

def server_console():
    print("\n╔══════════════════════════════════════╗")
    print("║   BRAWL SERVER  CONSOLE              ║")
    print("╠══════════════════════════════════════╣")
    print("║  [ENTER]  → Force-start game         ║")
    print("║  players  → List players             ║")
    print("║  kick <n> → Kick player (mid-game)   ║")
    print("║  stats    → Show brawler stats       ║")
    print("╚══════════════════════════════════════╝\n")
    print(f"  Map: {MAP_W}x{MAP_H}  |  Max players: {MAX_PLAYERS}")
    print(f"  Brawlers: {', '.join(BRAWLER_STATS.keys())}")
    print(f"  Hit radius: 24px | Player radius: {PLAYER_RADIUS}px")
    print(f"  Regen: {REGEN_RATE} HP/s after {REGEN_DELAY}s delay")
    print("  NOTE: All damage/speed/range values are server-authoritative.\n")

    while True:
        cmd = input().strip().lower()
        if cmd == "":
            if game_phase == "lobby":
                active = [p for p in players.values() if not p.get("spectating", False)]
                if len(active) == 0:
                    print("⚠️  No players connected yet.")
                elif len(active) < 2:
                    print("⚠️  Need at least 2 players to start.")
                else:
                    print("  Force-starting game...")
                    start_game()
            else:
                print("⚠️  Game already running.")
        elif cmd == "players":
            if not players:
                print("  (no players)")
            for addr, p in players.items():
                status    = "🟢 alive" if p["alive"] else "💀 dead"
                phase_tag = f"[{p['phase']}]"
                ready_tag = " [READY]"      if p.get("ready") else ""
                spec_tag  = " [SPECTATING]" if p.get("spectating") else ""
                kick_tag  = " [KICKED]"     if p["name"] in kicked_names else ""
                print(f"  {p['name']:15s} {p['brawler']:12s} {phase_tag:10s} {status}{ready_tag}{spec_tag}{kick_tag}  {addr}")
        elif cmd == "stats":
            print("\n  BRAWLER STATS (authoritative):")
            for bname, s in BRAWLER_STATS.items():
                spd = BRAWLER_SPEED.get(bname, 5)
                print(f"  {bname:12s}  dmg={s['damage']:3d}  bspd={s['bullet_speed']:3d}  "
                      f"cd={s['cooldown']:.2f}s  move={spd}  spread={s['spread']}  range={s['range']}")
            print()
        elif cmd.startswith("kick "):
            name = cmd[5:].strip()
            matches = [(a, p) for a, p in players.items() if p["name"].lower() == name.lower()]
            if matches:
                addr, p = matches[0]
                pname = p["name"]
                kicked_names.add(pname)
                p["alive"]      = False
                p["spectating"] = True
                try:
                    server.sendto(json.dumps({"phase": "kicked"}).encode(), addr)
                except:
                    pass
                print(f"  ⛔ Kicked {pname}")
                broadcast_lobby()
                if game_phase == "running":
                    check_round_end()
            else:
                print(f"  Player '{name}' not found.")
        else:
            print("  Unknown command.")

threading.Thread(target=handle, daemon=True).start()
threading.Thread(target=game_loop, daemon=True).start()
threading.Thread(target=check_inactive_players, daemon=True).start()

print("🚀 Server running on port", PORT)
server_console()


