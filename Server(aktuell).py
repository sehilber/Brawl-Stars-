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
 
# ─── MAP DIMENSIONS ───────────────────────────────────────────────────────────

MAP_W = 3840

MAP_H = 2160
 
PLAYER_RADIUS = 14
 
# ─── AUTHORITATIVE BRAWLER STATS (clients CANNOT override these) ───────────────

# All damage, bullet_speed, cooldown, etc. live here only.

BRAWLER_STATS = {

    "sniper": {

        "weapon":       "sniper",

        "damage":       80,

        "bullet_speed": 22,

        "cooldown":     0.8,     # seconds between shots

        "pierce":       False,   # base; starpower overrides

        "spread":       0,       # number of extra bullets (shotgun spread)

        "spread_angle": 0,

    },

    "minigun": {

        "weapon":       "minigun",

        "damage":       10,

        "bullet_speed": 10,

        "cooldown":     0.1,

        "pierce":       False,

        "spread":       0,

        "spread_angle": 0,

    },

    "mage": {

        "weapon":       "magic",

        "damage":       35,

        "bullet_speed": 14,

        "cooldown":     0.4,

        "pierce":       False,

        "spread":       0,

        "spread_angle": 0,

    },

    # ── NEW BRAWLERS ──

    "tank": {

        # Fires a 5-pellet shotgun blast. Short range, massive close-up damage.

        "weapon":       "shotgun",

        "damage":       22,      # per pellet; 5 pellets = 110 max

        "bullet_speed": 8,

        "cooldown":     1.1,

        "pierce":       False,

        "spread":       4,       # 4 extra bullets (5 total)

        "spread_angle": 18,      # degrees between pellets

    },

    "ninja": {

        # Rapid shurikens, slightly faster player movement (handled via speed multiplier).

        "weapon":       "shuriken",

        "damage":       18,

        "bullet_speed": 16,

        "cooldown":     0.18,

        "pierce":       False,

        "spread":       0,

        "spread_angle": 0,

    },

    "healer": {

        # Moderate damage orbs. Passive: regenerates 2 HP/sec while alive (handled in game loop).

        "weapon":       "orb",

        "damage":       28,

        "bullet_speed": 12,

        "cooldown":     0.55,

        "pierce":       False,

        "spread":       0,

        "spread_angle": 0,

    },

}
 
# Movement speed per brawler (pixels per tick at 60 tps)

BRAWLER_SPEED = {

    "sniper":  5,

    "minigun": 4,

    "mage":    5,

    "tank":    3,

    "ninja":   7,

    "healer":  5,

}
 
# ─── GAME STATE ───────────────────────────────────────────────────────────────

game_phase   = "lobby"

players      = {}

bullets      = []

kicked_names = set()
 
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
 
# ─── HELPERS ──────────────────────────────────────────────────────────────────

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

        "last_heal_tick": time.time(),   # for healer passive

    }
 
def collide_wall(x, y, r=PLAYER_RADIUS):

    for w in MAP_WALLS:

        closest_x = max(w["x"], min(x, w["x"] + w["w"]))

        closest_y = max(w["y"], min(y, w["y"] + w["h"]))

        if math.hypot(x - closest_x, y - closest_y) < r:

            return True

    return False
 
def clamp_to_map(x, y, r=PLAYER_RADIUS):

    return max(r, min(x, MAP_W - r)), max(r, min(y, MAP_H - r))
 
def bullet_hits_wall(bx, by):

    for w in MAP_WALLS:

        if w["x"] < bx < w["x"] + w["w"] and w["y"] < by < w["y"] + w["h"]:

            return True

    return False
 
def bullet_out_of_bounds(bx, by):

    return bx < 0 or bx > MAP_W or by < 0 or by > MAP_H
 
def spawn_bullet(p, addr, dx, dy, stats, pierce_override=False):

    """Spawn one bullet using server-authoritative stats."""

    bullets.append({

        "x":      p["x"],

        "y":      p["y"],

        "dx":     dx,

        "dy":     dy,

        "speed":  stats["bullet_speed"],

        "damage": stats["damage"],

        "owner":  str(addr),

        "pierce": pierce_override or stats["pierce"],

        "weapon": stats["weapon"],

    })
 
# ─── LOBBY BROADCAST ──────────────────────────────────────────────────────────

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

        p["x"]          = float(sx)

        p["y"]          = float(sy)

        p["hp"]         = 100

        p["alive"]      = True

        p["phase"]      = "playing"

        p["weapon"]     = stats["weapon"]

        p["last_shot"]  = 0.0

        p["invisible"]  = False

        p["starpower"]  = False

        p["ready"]      = False

        p["spectating"] = False

        p["in_game"]    = True

        p["last_heal_tick"] = time.time()
 
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
 
# ─── RECEIVE HANDLER ──────────────────────────────────────────────────────────

def handle():

    while True:

        data, addr = server.recvfrom(2048)

        try:

            msg = json.loads(data.decode())

        except:

            continue
 
        # ── NEW CONNECTION ──

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
 
        # ── JOIN / RECONNECT ──

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
 
        # ── BRAWLER SELECT ──

        if msg.get("type") == "brawler_select":

            if game_phase == "lobby":

                brawler = msg.get("brawler", "sniper")

                if brawler not in BRAWLER_STATS:

                    brawler = "sniper"

                p["brawler"] = brawler

                p["weapon"]  = BRAWLER_STATS[brawler]["weapon"]

                broadcast_lobby()

            continue
 
        # ── READY TOGGLE ──

        if msg.get("type") == "set_ready":

            if game_phase == "lobby" and not p.get("spectating", False) and p["name"] not in kicked_names:

                p["ready"] = msg.get("ready", False)

                broadcast_lobby()

                check_all_ready()

            continue
 
        # ── GUARD: only playing, alive, non-spectator ──

        if game_phase == "lobby":

            continue

        if p["name"] in kicked_names:

            continue

        if p.get("spectating", False) or not p["alive"]:

            continue
 
        brawler = p.get("brawler", "sniper")

        stats   = BRAWLER_STATS.get(brawler, BRAWLER_STATS["sniper"])

        speed   = BRAWLER_SPEED.get(brawler, 5)
 
        # ── MOVE ──

        if msg.get("type") == "move":

            dx = (-speed if msg.get("left") else 0) + (speed if msg.get("right") else 0)

            dy = (-speed if msg.get("up")   else 0) + (speed if msg.get("down")  else 0)

            nx, ny = clamp_to_map(p["x"] + dx, p["y"] + dy)

            if collide_wall(nx, ny):

                nx_only, _ = clamp_to_map(p["x"] + dx, p["y"])

                if not collide_wall(nx_only, p["y"]):

                    p["x"] = nx_only

                else:

                    _, ny_only = clamp_to_map(p["x"], p["y"] + dy)

                    if not collide_wall(p["x"], ny_only):

                        p["y"] = ny_only

            else:

                p["x"], p["y"] = nx, ny
 
        # ── STARPOWER ──

        elif msg.get("type") == "starpower":

            active = msg.get("active", False)

            p["starpower"] = active

            # Mage: invisible while starpower active

            if brawler == "mage":

                p["invisible"] = active

            # Ninja: brief speed burst is handled by starpower flag client-side

            # Tank starpower: pierce pellets — handled at shoot time
 
        # ── SHOOT — all stats come from server's BRAWLER_STATS ──

        elif msg.get("type") == "shoot":

            now = time.time()

            # Starpower cooldown halving for minigun

            cd = stats["cooldown"]

            if p.get("starpower") and brawler == "minigun":

                cd *= 0.4

            if now - p["last_shot"] < cd:

                continue

            p["last_shot"] = now
 
            # Client only tells us direction (dx, dy); we ignore any damage/speed it sends

            raw_dx = msg.get("dx", 0)

            raw_dy = msg.get("dy", 0)

            length = math.hypot(raw_dx, raw_dy)

            if length == 0:

                continue

            dx_n = raw_dx / length

            dy_n = raw_dy / length
 
            # Sniper starpower: piercing

            pierce = stats["pierce"]

            if brawler == "sniper" and p.get("starpower"):

                pierce = True
 
            # Tank: fire spread pellets

            spread_count = stats["spread"]

            if spread_count > 0:

                total_pellets = spread_count + 1

                half = spread_count / 2.0

                base_ang = math.atan2(dy_n, dx_n)

                ang_step  = math.radians(stats["spread_angle"])

                for i in range(total_pellets):

                    ang = base_ang + ang_step * (i - half)

                    spawn_bullet(p, addr,

                                 math.cos(ang), math.sin(ang),

                                 stats, pierce_override=pierce)

            else:

                spawn_bullet(p, addr, dx_n, dy_n, stats, pierce_override=pierce)
 
# ─── INACTIVE CLEANUP ─────────────────────────────────────────────────────────

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
 
# ─── GAME LOOP ────────────────────────────────────────────────────────────────

def game_loop():

    while True:

        if game_phase == "running":

            now = time.time()
 
            # ── Healer passive regen (2 HP/sec) ──

            for addr, p in players.items():

                if p.get("brawler") == "healer" and p["alive"] and not p.get("spectating"):

                    if now - p.get("last_heal_tick", now) >= 1.0:

                        p["hp"] = min(100, p["hp"] + 2)

                        p["last_heal_tick"] = now
 
            # ── Bullet movement & collision ──

            for b in bullets[:]:

                b["x"] += b["dx"] * b["speed"]

                b["y"] += b["dy"] * b["speed"]
 
                if bullet_out_of_bounds(b["x"], b["y"]):

                    if b in bullets:

                        bullets.remove(b)

                    continue
 
                if not b.get("pierce") and bullet_hits_wall(b["x"], b["y"]):

                    if b in bullets:

                        bullets.remove(b)

                    continue
 
                for addr, p in list(players.items()):

                    if str(addr) == b["owner"] or not p["alive"]:

                        continue

                    if p.get("spectating", False):

                        continue

                    if math.hypot(p["x"] - b["x"], p["y"] - b["y"]) < 18:

                        p["hp"] -= b["damage"]

                        if p["hp"] <= 0:

                            p["alive"]      = False

                            p["spectating"] = True

                            print(f"💀 {p['name']} died → spectating")

                            check_round_end()

                        if not b.get("pierce") and b in bullets:

                            bullets.remove(b)

                        break
 
            # ── Broadcast game state ──

            state = json.dumps({

                "phase":   "running",

                "players": {str(addr): p for addr, p in players.items()},

                "bullets": bullets,

                "walls":   MAP_WALLS,

            }).encode()

            for addr in list(players.keys()):

                try:

                    server.sendto(state, addr)

                except:

                    pass
 
        time.sleep(1 / 60)
 
# ─── SERVER CONSOLE ───────────────────────────────────────────────────────────

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

    print("  NOTE: All damage/speed values are server-authoritative.\n")
 
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

                print(f"  {p['name']:15s} {p['brawler']:10s} {phase_tag:10s} {status}{ready_tag}{spec_tag}{kick_tag}  {addr}")
 
        elif cmd == "stats":

            print("\n  BRAWLER STATS (authoritative):")

            for bname, s in BRAWLER_STATS.items():

                spd = BRAWLER_SPEED.get(bname, 5)

                print(f"  {bname:10s}  dmg={s['damage']:3d}  spd={s['bullet_speed']:3d}  "

                      f"cd={s['cooldown']:.2f}s  move={spd}  spread={s['spread']}  "

                      f"weapon={s['weapon']}")

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
 
# ─── START ────────────────────────────────────────────────────────────────────

threading.Thread(target=handle, daemon=True).start()

threading.Thread(target=game_loop, daemon=True).start()

threading.Thread(target=check_inactive_players, daemon=True).start()
 
print("🚀 Server running on port", PORT)

server_console()
 
 