import socket
import threading
import json
import time
import math

HOST = "0.0.0.0"
PORT = 5555

server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 262144)   # 256 KB send buffer
server.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 262144)   # 256 KB recv buffer
server.bind((HOST, PORT))

MAX_PLAYERS      = 10
INACTIVE_TIMEOUT = 15

MAP_W         = 1920
MAP_H         = 1080
PLAYER_RADIUS = 14

game_phase = "lobby"

players = {}
bullets = []

# Pre-serialise walls once – they never change
MAP_WALLS = [
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
]
WALLS_JSON = json.dumps(MAP_WALLS)   # serialised once

WEAPONS = {
    "ak47":    {"damage": 20, "bullet_speed": 12, "fire_rate": 0.12, "mag_size": 30,  "reload_time": 1.5},
    "minigun": {"damage": 10, "bullet_speed": 10, "fire_rate": 0.05, "mag_size": 100, "reload_time": 3.0},
    "sniper":  {"damage": 80, "bullet_speed": 22, "fire_rate": 1.2,  "mag_size": 3,   "reload_time": 2.5},
    "magic":   {"damage": 35, "bullet_speed": 14, "fire_rate": 0.4,  "mag_size": 10,  "reload_time": 1.5},
}

SPAWN_POINTS = [
    (120,  120), (1800, 120), (120,  960), (1800, 960),
    (960,  120), (960,  960), (120,  540), (1800, 540),
    (480,  300), (1440, 300), (480,  780), (1440, 780),
]

# ─── WALL LOOKUP GRID for fast collision ──────────────────────────────────────
# Cell size 64px → 30×17 grid for 1920×1080
_CELL = 64
_GRID_W = math.ceil(MAP_W / _CELL)
_GRID_H = math.ceil(MAP_H / _CELL)
_wall_grid = [[[] for _ in range(_GRID_H)] for _ in range(_GRID_W)]

def _build_wall_grid():
    for w in MAP_WALLS:
        cx0 = max(0, int(w["x"]) // _CELL)
        cy0 = max(0, int(w["y"]) // _CELL)
        cx1 = min(_GRID_W - 1, (int(w["x"]) + int(w["w"])) // _CELL)
        cy1 = min(_GRID_H - 1, (int(w["y"]) + int(w["h"])) // _CELL)
        for cx in range(cx0, cx1 + 1):
            for cy in range(cy0, cy1 + 1):
                _wall_grid[cx][cy].append(w)

_build_wall_grid()

def _candidate_walls(x, y, r=PLAYER_RADIUS):
    cx0 = max(0, int(x - r) // _CELL)
    cy0 = max(0, int(y - r) // _CELL)
    cx1 = min(_GRID_W - 1, int(x + r) // _CELL)
    cy1 = min(_GRID_H - 1, int(y + r) // _CELL)
    seen = set()
    result = []
    for cx in range(cx0, cx1 + 1):
        for cy in range(cy0, cy1 + 1):
            for w in _wall_grid[cx][cy]:
                wid = id(w)
                if wid not in seen:
                    seen.add(wid)
                    result.append(w)
    return result

def collide_wall(x, y, r=PLAYER_RADIUS):
    for w in _candidate_walls(x, y, r):
        closest_x = max(w["x"], min(x, w["x"] + w["w"]))
        closest_y = max(w["y"], min(y, w["y"] + w["h"]))
        if math.hypot(x - closest_x, y - closest_y) < r:
            return True
    return False

def clamp_to_map(x, y, r=PLAYER_RADIUS):
    return max(r, min(x, MAP_W - r)), max(r, min(y, MAP_H - r))

def bullet_hits_wall(bx, by):
    cx = int(bx) // _CELL
    cy = int(by) // _CELL
    if 0 <= cx < _GRID_W and 0 <= cy < _GRID_H:
        for w in _wall_grid[cx][cy]:
            if w["x"] < bx < w["x"] + w["w"] and w["y"] < by < w["y"] + w["h"]:
                return True
    return False

def bullet_out_of_bounds(bx, by):
    return bx < 0 or bx > MAP_W or by < 0 or by > MAP_H

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
        "hp": 100, "alive": True,
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

def finish_reload(addr):
    if addr not in players:
        return
    p = players[addr]
    p["ammo"] = WEAPONS[p["weapon"]]["mag_size"]
    p["reloading"] = False

# ─── BROADCASTS ───────────────────────────────────────────────────────────────
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
        except Exception:
            pass

def start_game():
    global game_phase, bullets
    game_phase = "running"
    bullets.clear()
    spawn_list = list(SPAWN_POINTS)
    for i, (addr, p) in enumerate(players.items()):
        sx, sy = spawn_list[i % len(spawn_list)]
        p["x"] = float(sx); p["y"] = float(sy)
        p["hp"] = 100; p["alive"] = True; p["phase"] = "playing"
        p["ammo"] = WEAPONS[p["weapon"]]["mag_size"]
        p["reloading"] = False; p["last_shot"] = 0.0
        p["invisible"] = False; p["starpower"] = False
    print(f"🎮 Game started with {len(players)} players!")
    msg = json.dumps({"phase": "start"}).encode()
    for addr in list(players.keys()):
        try:
            server.sendto(msg, addr)
        except Exception:
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
            p["phase"] = "lobby"; p["alive"] = True; p["hp"] = 100
        msg = json.dumps({"phase": "game_over", "winner": winner_name}).encode()
        for addr in list(players.keys()):
            try:
                server.sendto(msg, addr)
            except Exception:
                pass

# ─── RECEIVE HANDLER ──────────────────────────────────────────────────────────
def handle():
    while True:
        try:
            data, addr = server.recvfrom(2048)
        except Exception:
            continue
        try:
            msg = json.loads(data.decode())
        except Exception:
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

        msg_type = msg.get("type", "")

        if msg_type == "join_lobby":
            p["name"] = msg.get("name", p["name"])
            p["phase"] = "lobby"
            broadcast_lobby()
            continue

        if game_phase == "lobby":
            continue

        if not p["alive"]:
            continue

        if msg_type == "move":
            speed = 5
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

        elif msg_type == "weapon_select":
            wname = msg.get("weapon")
            if wname in WEAPONS:
                w = WEAPONS[wname]
                p["weapon"] = wname
                p["ammo"] = w["mag_size"]
                p["reloading"] = False
                p["last_shot"] = 0.0

        elif msg_type == "starpower":
            active  = msg.get("active", False)
            brawler = msg.get("brawler")
            p["starpower"] = active
            if brawler == "mage":
                p["invisible"] = active

        elif msg_type == "shoot":
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
# Build state payload efficiently: reuse as much serialisation as possible.
# Walls are sent only on first tick per connection via a flag; thereafter
# we strip them from the regular broadcast to cut ~70% of packet size.

_client_has_walls = {}   # addr -> bool

def game_loop():
    global bullets
    TICK = 1 / 60
    while True:
        t0 = time.perf_counter()

        if game_phase == "running":
            # --- Bullet physics ---
            surviving = []
            for b in bullets:
                b["x"] += b["dx"] * b["speed"]
                b["y"] += b["dy"] * b["speed"]

                if bullet_out_of_bounds(b["x"], b["y"]):
                    continue
                if not b.get("pierce") and bullet_hits_wall(b["x"], b["y"]):
                    continue

                hit = False
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
                        if not b.get("pierce"):
                            hit = True
                            break

                if not hit:
                    surviving.append(b)
            bullets = surviving

            # --- Build compact player dict ---
            players_out = {}
            for addr, p in players.items():
                players_out[str(addr)] = {
                    "x": round(p["x"], 1), "y": round(p["y"], 1),
                    "hp": p["hp"], "alive": p["alive"],
                    "weapon": p["weapon"], "name": p["name"],
                    "invisible": p["invisible"], "starpower": p["starpower"],
                }

            bullets_out = [
                {"x": round(b["x"], 1), "y": round(b["y"], 1),
                 "pierce": b.get("pierce", False)}
                for b in bullets
            ]

            # Build two variants: with walls (first send) and without
            base = {"phase": "running",
                    "players": players_out,
                    "bullets": bullets_out}
            base_with_walls = dict(base)
            base_with_walls["walls"] = MAP_WALLS

            msg_no_walls   = json.dumps(base).encode()
            msg_with_walls = json.dumps(base_with_walls).encode()

            for addr in list(players.keys()):
                try:
                    if not _client_has_walls.get(addr, False):
                        server.sendto(msg_with_walls, addr)
                        _client_has_walls[addr] = True
                    else:
                        server.sendto(msg_no_walls, addr)
                except Exception:
                    pass

        elapsed = time.perf_counter() - t0
        sleep_t = TICK - elapsed
        if sleep_t > 0:
            time.sleep(sleep_t)

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
                if not players:
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
                print(f"  {p['name']:15s} [{p['phase']:8s}] {status}  {addr}")
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
            print("  Unknown command.")

# ─── START ────────────────────────────────────────────────────────────────────
threading.Thread(target=handle,                 daemon=True).start()
threading.Thread(target=game_loop,              daemon=True).start()
threading.Thread(target=check_inactive_players, daemon=True).start()

print("🚀 Server running on port", PORT)
server_console()

