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

INACTIVE_TIMEOUT = 15
 
# ─── MAP DIMENSIONS ───────────────────────────────────────────────────────────

MAP_W = 1920

MAP_H = 1080

PLAYER_RADIUS = 14   # collision radius of each player
 
# ─── GAME STATE ───────────────────────────────────────────────────────────────

game_phase = "lobby"   # "lobby" | "running"
 
players = {}   # addr -> player dict

bullets = []
 
MAP_WALLS = [

    # Horizontal barriers

    {"x": 400,  "y": 250,  "w": 300, "h": 24},

    {"x": 1200, "y": 250,  "w": 300, "h": 24},

    {"x": 700,  "y": 500,  "w": 250, "h": 24},

    {"x": 980,  "y": 500,  "w": 250, "h": 24},

    {"x": 400,  "y": 780,  "w": 300, "h": 24},

    {"x": 1200, "y": 780,  "w": 300, "h": 24},

    # Vertical barriers

    {"x": 150,  "y": 300,  "w": 24,  "h": 200},

    {"x": 1746, "y": 300,  "w": 24,  "h": 200},

    {"x": 150,  "y": 600,  "w": 24,  "h": 200},

    {"x": 1746, "y": 600,  "w": 24,  "h": 200},

    # Center cross

    {"x": 860,  "y": 400,  "w": 200, "h": 24},

    {"x": 948,  "y": 300,  "w": 24,  "h": 200},

    # Corner blocks

    {"x": 280,  "y": 180,  "w": 120, "h": 120},

    {"x": 1520, "y": 180,  "w": 120, "h": 120},

    {"x": 280,  "y": 780,  "w": 120, "h": 120},

    {"x": 1520, "y": 780,  "w": 120, "h": 120},

]
 
WEAPONS = {

    "ak47":    {"damage": 20, "bullet_speed": 12, "fire_rate": 0.12, "mag_size": 30,  "reload_time": 1.5},

    "minigun": {"damage": 10, "bullet_speed": 10, "fire_rate": 0.05, "mag_size": 100, "reload_time": 3.0},

    "sniper":  {"damage": 80, "bullet_speed": 22, "fire_rate": 1.2,  "mag_size": 3,   "reload_time": 2.5},

    "magic":   {"damage": 35, "bullet_speed": 14, "fire_rate": 0.4,  "mag_size": 10,  "reload_time": 1.5},

}
 
SPAWN_POINTS = [

    (120,  120),  (1800, 120),  (120,  960),  (1800, 960),

    (960,  120),  (960,  960),  (120,  540),  (1800, 540),

    (480,  300),  (1440, 300),  (480,  780),  (1440, 780),

]
 
# ─── HELPERS ──────────────────────────────────────────────────────────────────

def get_spawn():

    idx = len(players) % len(SPAWN_POINTS)

    return SPAWN_POINTS[idx]
 
def new_player(name="Player", spawn=None):

    weapon_name = "ak47"

    w = WEAPONS[weapon_name]

    sx, sy = spawn if spawn else (100, 100)

    return {

        "x": float(sx), "y": float(sy),

        "hp": 100,

        "alive": True,

        "weapon": weapon_name,

        "ammo": w["mag_size"],

        "last_shot": 0.0,

        "reloading": False,

        "last_activity": time.time(),

        "invisible": False,

        "starpower": False,

        "name": name,

        "phase": "lobby",

    }
 
def collide_wall(x, y, r=PLAYER_RADIUS):

    for w in MAP_WALLS:

        # AABB vs circle (approximate)

        closest_x = max(w["x"], min(x, w["x"] + w["w"]))

        closest_y = max(w["y"], min(y, w["y"] + w["h"]))

        if math.hypot(x - closest_x, y - closest_y) < r:

            return True

    return False
 
def clamp_to_map(x, y, r=PLAYER_RADIUS):

    """Keep player within map boundaries."""

    x = max(r, min(x, MAP_W - r))

    y = max(r, min(y, MAP_H - r))

    return x, y
 
def bullet_hits_wall(bx, by):

    for w in MAP_WALLS:

        if w["x"] < bx < w["x"] + w["w"] and w["y"] < by < w["y"] + w["h"]:

            return True

    return False
 
def bullet_out_of_bounds(bx, by):

    return bx < 0 or bx > MAP_W or by < 0 or by > MAP_H
 
def finish_reload(addr):

    if addr not in players:

        return

    p = players[addr]

    p["ammo"] = WEAPONS[p["weapon"]]["mag_size"]

    p["reloading"] = False
 
# ─── LOBBY BROADCAST ──────────────────────────────────────────────────────────

def broadcast_lobby():

    lobby_names = [p["name"] for p in players.values()]

    msg = json.dumps({

        "phase": "lobby",

        "players_in_lobby": lobby_names,

        "player_count": len(players),

    }).encode()

    for addr in list(players.keys()):

        try:

            server.sendto(msg, addr)

        except:

            pass
 
def start_game():

    global game_phase, bullets

    game_phase = "running"

    bullets.clear()
 
    spawn_list = list(SPAWN_POINTS)

    for i, (addr, p) in enumerate(players.items()):

        sx, sy = spawn_list[i % len(spawn_list)]

        p["x"] = float(sx)

        p["y"] = float(sy)

        p["hp"] = 100

        p["alive"] = True

        p["phase"] = "playing"

        p["ammo"] = WEAPONS[p["weapon"]]["mag_size"]

        p["reloading"] = False

        p["last_shot"] = 0.0

        p["invisible"] = False

        p["starpower"] = False
 
    print(f"🎮 Game started with {len(players)} players!")
 
    msg = json.dumps({"phase": "start"}).encode()

    for addr in list(players.keys()):

        try:

            server.sendto(msg, addr)

        except:

            pass
 
def check_round_end():

    global game_phase

    if game_phase != "running":

        return
 
    alive = [addr for addr, p in players.items() if p["alive"]]
 
    if len(players) > 1 and len(alive) <= 1:

        winner_name = players[alive[0]]["name"] if alive else "Nobody"

        print(f"🏆 Round over! Winner: {winner_name}")

        game_phase = "lobby"
 
        for p in players.values():

            p["phase"] = "lobby"

            p["alive"] = True

            p["hp"] = 100
 
        msg = json.dumps({

            "phase": "game_over",

            "winner": winner_name,

        }).encode()

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
 
        if addr not in players:

            if len(players) >= MAX_PLAYERS:

                continue

            name = msg.get("name", f"Player{len(players)+1}")

            players[addr] = new_player(name=name, spawn=get_spawn())

            print(f"✅ {name} connected ({addr})")

            broadcast_lobby()

            continue
 
        p = players[addr]

        p["last_activity"] = time.time()
 
        if msg["type"] == "join_lobby":

            name = msg.get("name", p["name"])

            p["name"] = name

            p["phase"] = "lobby"

            broadcast_lobby()

            continue
 
        if game_phase == "lobby":

            continue
 
        if not p["alive"]:

            continue
 
        # Movement with boundary + wall collision

        if msg["type"] == "move":

            speed = 5

            dx = (-speed if msg.get("left") else 0) + (speed if msg.get("right") else 0)

            dy = (-speed if msg.get("up") else 0) + (speed if msg.get("down") else 0)
 
            # Try full move

            nx, ny = p["x"] + dx, p["y"] + dy

            nx, ny = clamp_to_map(nx, ny)
 
            if collide_wall(nx, ny):

                # Try X only

                nx_only, _ = clamp_to_map(p["x"] + dx, p["y"])

                if not collide_wall(nx_only, p["y"]):

                    p["x"] = nx_only

                else:

                    # Try Y only

                    _, ny_only = clamp_to_map(p["x"], p["y"] + dy)

                    if not collide_wall(p["x"], ny_only):

                        p["y"] = ny_only

                    # else: fully blocked

            else:

                p["x"], p["y"] = nx, ny
 
        elif msg["type"] == "weapon_select":

            wname = msg.get("weapon")

            if wname in WEAPONS:

                w = WEAPONS[wname]

                p["weapon"] = wname

                p["ammo"] = w["mag_size"]

                p["reloading"] = False

                p["last_shot"] = 0.0
 
        elif msg["type"] == "starpower":

            active  = msg.get("active", False)

            brawler = msg.get("brawler")

            p["starpower"] = active

            if brawler == "mage":

                p["invisible"] = active
 
        elif msg["type"] == "shoot":

            weapon = WEAPONS[p["weapon"]]

            if p["reloading"]:

                continue

            if p["ammo"] <= 0:

                p["reloading"] = True

                threading.Timer(weapon["reload_time"], finish_reload, args=[addr]).start()

                continue

            now = time.time()

            if now - p["last_shot"] < weapon["fire_rate"]:

                continue

            p["last_shot"] = now

            p["ammo"] -= 1

            bullets.append({

                "x": p["x"], "y": p["y"],

                "dx": msg["dx"], "dy": msg["dy"],

                "speed": msg.get("speed", weapon["bullet_speed"]),

                "damage": msg.get("damage", weapon["damage"]),

                "owner": str(addr),

                "pierce": msg.get("pierce", False),

            })
 
# ─── INACTIVE CLEANUP ─────────────────────────────────────────────────────────

def check_inactive_players():

    while True:

        now = time.time()

        for addr in list(players.keys()):

            if now - players[addr]["last_activity"] > INACTIVE_TIMEOUT:

                print(f"❌ KICK: {players[addr]['name']} ({addr})")

                del players[addr]

                if game_phase == "lobby":

                    broadcast_lobby()

        time.sleep(2)
 
# ─── GAME LOOP ────────────────────────────────────────────────────────────────

def game_loop():

    while True:

        if game_phase == "running":

            for b in bullets[:]:

                b["x"] += b["dx"] * b["speed"]

                b["y"] += b["dy"] * b["speed"]
 
                # Remove bullet if out of map bounds

                if bullet_out_of_bounds(b["x"], b["y"]):

                    if b in bullets:

                        bullets.remove(b)

                    continue
 
                # Remove bullet if it hits a wall (non-piercing)

                if not b.get("pierce") and bullet_hits_wall(b["x"], b["y"]):

                    if b in bullets:

                        bullets.remove(b)

                    continue
 
                for addr, p in list(players.items()):

                    if str(addr) == b["owner"] or not p["alive"]:

                        continue

                    if math.hypot(p["x"] - b["x"], p["y"] - b["y"]) < 18:

                        p["hp"] -= b["damage"]

                        if p["hp"] <= 0:

                            p["alive"] = False

                            p["phase"] = "lobby"

                            print(f"💀 {p['name']} died")

                            check_round_end()

                        if not b.get("pierce") and b in bullets:

                            bullets.remove(b)

                        break
 
            state = json.dumps({

                "phase": "running",

                "players": {str(addr): p for addr, p in players.items()},

                "bullets": bullets,

                "walls": MAP_WALLS,

            }).encode()
 
            for addr in list(players.keys()):

                try:

                    server.sendto(state, addr)

                except:

                    pass
 
        time.sleep(1 / 60)
 
# ─── SERVER CONSOLE ───────────────────────────────────────────────────────────

def server_console():

    print("\n╔══════════════════════════════╗")

    print("║   BRAWL SERVER  CONSOLE      ║")

    print("╠══════════════════════════════╣")

    print("║  [ENTER]  → Start game       ║")

    print("║  players  → List players     ║")

    print("║  kick <n> → Kick player      ║")

    print("╚══════════════════════════════╝\n")

    print(f"  Map: {MAP_W}x{MAP_H}  |  Max players: {MAX_PLAYERS}\n")
 
    while True:

        cmd = input().strip().lower()
 
        if cmd == "":

            if game_phase == "lobby":

                if len(players) == 0:

                    print("⚠️  No players connected yet.")

                else:

                    start_game()

            else:

                print("⚠️  Game already running. Wait for round to end.")
 
        elif cmd == "players":

            if not players:

                print("  (no players)")

            for addr, p in players.items():

                status = "🟢 alive" if p["alive"] else "💀 dead"

                phase_tag = f"[{p['phase']}]"

                print(f"  {p['name']:15s} {phase_tag:10s} {status}  {addr}")
 
        elif cmd.startswith("kick "):

            name = cmd[5:]

            kicked = [(a, p) for a, p in players.items() if p["name"].lower() == name]

            if kicked:

                addr, p = kicked[0]

                del players[addr]

                print(f"  Kicked {p['name']}")

                broadcast_lobby()

            else:

                print(f"  Player '{name}' not found.")
 
        else:

            print("  Unknown command. Use ENTER to start, 'players', or 'kick <name>'.")
 
 
# ─── START ────────────────────────────────────────────────────────────────────

threading.Thread(target=handle, daemon=True).start()

threading.Thread(target=game_loop, daemon=True).start()

threading.Thread(target=check_inactive_players, daemon=True).start()
 
print("🚀 Server running on port", PORT)

server_console()
 
 