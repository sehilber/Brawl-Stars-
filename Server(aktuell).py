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
INACTIVE_TIMEOUT = 60   # generous — dead spectators send a heartbeat every 2s

# ─── MAP DIMENSIONS ──────────────────────────────────────────────────────────
MAP_W = 3840
MAP_H = 2160

PLAYER_RADIUS = 14

# ─── GAME STATE ───────────────────────────────────────────────────────────────
game_phase = "lobby"

players     = {}   # addr -> player dict
bullets     = []
kicked_names = set()

MAP_WALLS = [
    # ── TOP-LEFT QUADRANT (0-1920, 0-1080) ──
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

    # ── TOP-RIGHT QUADRANT (1920-3840, 0-1080) ──
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

    # ── BOTTOM-LEFT QUADRANT (0-1920, 1080-2160) ──
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

    # ── BOTTOM-RIGHT QUADRANT (1920-3840, 1080-2160) ──
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

    # ── ABSOLUTE CENTER CROSS ──
    {"x": 1760, "y": 1040, "w": 320, "h": 24},
    {"x": 1908, "y": 900,  "w": 24,  "h": 360},
]

WEAPONS = {
    "ak47":    {"damage": 20, "bullet_speed": 12, "fire_rate": 0.12, "mag_size": 30,  "reload_time": 1.5},
    "minigun": {"damage": 10, "bullet_speed": 10, "fire_rate": 0.05, "mag_size": 100, "reload_time": 3.0},
    "sniper":  {"damage": 80, "bullet_speed": 22, "fire_rate": 1.2,  "mag_size": 3,   "reload_time": 2.5},
    "magic":   {"damage": 35, "bullet_speed": 14, "fire_rate": 0.4,  "mag_size": 10,  "reload_time": 1.5},
}

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

def new_player(name="Player", spawn=None):
    weapon_name = "ak47"
    w = WEAPONS[weapon_name]
    sx, sy = spawn if spawn else (100, 100)
    return {
        "x": float(sx), "y": float(sy),
        "hp": 100,
        "alive": True,
        "weapon": weapon_name,
        "brawler": "sniper",
        "ammo": w["mag_size"],
        "last_shot": 0.0,
        "reloading": False,
        "last_activity": time.time(),
        "invisible": False,
        "starpower": False,
        "name": name,
        "phase": "lobby",
        "ready": False,
        "spectating": False,   # died this round / joined mid-game; waiting for next
        "in_game": False,      # True = was dealt into this round (alive or dead)
    }

def collide_wall(x, y, r=PLAYER_RADIUS):
    for w in MAP_WALLS:
        closest_x = max(w["x"], min(x, w["x"] + w["w"]))
        closest_y = max(w["y"], min(y, w["y"] + w["h"]))
        if math.hypot(x - closest_x, y - closest_y) < r:
            return True
    return False

def clamp_to_map(x, y, r=PLAYER_RADIUS):
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
def build_lobby_state():
    """Build the full lobby state to send to all clients."""
    lobby_players = []
    for addr, p in players.items():
        lobby_players.append({
            "name":    p["name"],
            "brawler": p.get("brawler", "sniper"),
            "ready":   p.get("ready", False),
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
    """Auto-start if all lobby players (min 2, not kicked) are ready."""
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

    spawn_list = list(SPAWN_POINTS)
    participating = [
        (addr, p) for addr, p in players.items()
        if not p.get("spectating", False)
    ]

    # Reset everyone first
    for addr, p in players.items():
        p["in_game"]    = False
        p["spectating"] = False

    for i, (addr, p) in enumerate(participating):
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
        p["ready"] = False
        p["spectating"] = False
        p["in_game"] = True    # dealt into this round

    print(f"🎮 Game started with {len(participating)} players!")

    msg = json.dumps({"phase": "start"}).encode()
    for addr, p in players.items():
        if p["phase"] == "playing":
            try:
                server.sendto(msg, addr)
            except:
                pass
        else:
            # Send them a lobby update so they know game started
            try:
                server.sendto(json.dumps({"phase": "lobby_spectate",
                                          "msg": "Game started without you. Wait for next round!"}).encode(), addr)
            except:
                pass

def check_round_end():
    global game_phase
    if game_phase != "running":
        return

    # Count players who were dealt into this round
    in_game_all  = [addr for addr, p in players.items() if p.get("in_game", False)]
    in_game_alive = [addr for addr in in_game_all if players[addr]["alive"]]

    # Round ends when only 0 or 1 in-game player remains alive (need at least 2 to have started)
    if len(in_game_all) >= 2 and len(in_game_alive) <= 1:
        winner_name = players[in_game_alive[0]]["name"] if in_game_alive else "Nobody"
        print(f"🏆 Round over! Winner: {winner_name}")
        game_phase = "lobby"

        for p in players.values():
            p["phase"] = "lobby"
            p["alive"] = True
            p["hp"] = 100
            p["ready"] = False
            p["spectating"] = False
            p["in_game"] = False

        msg = json.dumps({
            "phase":  "game_over",
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

            if game_phase == "running" and name in kicked_names:
                try:
                    server.sendto(json.dumps({"phase": "kicked"}).encode(), addr)
                except:
                    pass
                continue

            spawn = get_spawn()
            players[addr] = new_player(name=name, spawn=spawn)

            # If game is running, mark as spectating (can't join mid-game)
            if game_phase == "running":
                players[addr]["spectating"] = True
                players[addr]["phase"] = "lobby"
                try:
                    server.sendto(json.dumps({
                        "phase": "lobby_spectate",
                        "msg":   "A game is in progress. You'll join next round!"
                    }).encode(), addr)
                except:
                    pass
            else:
                broadcast_lobby()

            print(f"✅ {name} connected ({addr}) | spectating={game_phase == 'running'}")
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

            # If joining mid-game, mark spectating
            if game_phase == "running" and p["phase"] != "playing":
                p["spectating"] = True
                p["phase"] = "lobby"
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

        # ── BRAWLER SELECT (in lobby) ──
        if msg.get("type") == "brawler_select":
            if game_phase == "lobby":
                brawler = msg.get("brawler", "sniper")
                weapon  = msg.get("weapon", "ak47")
                p["brawler"] = brawler
                if weapon in WEAPONS:
                    p["weapon"] = weapon
                    p["ammo"]   = WEAPONS[weapon]["mag_size"]
                broadcast_lobby()
            continue

        # ── READY TOGGLE ──
        if msg.get("type") == "set_ready":
            if game_phase == "lobby" and not p.get("spectating", False) and p["name"] not in kicked_names:
                p["ready"] = msg.get("ready", False)
                broadcast_lobby()
                check_all_ready()
            continue

        # ── GAME ACTIONS ──
        if game_phase == "lobby":
            continue

        if p["name"] in kicked_names:
            continue

        # Spectators and dead players can't act
        if p.get("spectating", False):
            continue

        if not p["alive"]:
            continue

        if msg.get("type") == "move":
            speed = 5
            dx = (-speed if msg.get("left") else 0) + (speed if msg.get("right") else 0)
            dy = (-speed if msg.get("up") else 0) + (speed if msg.get("down") else 0)

            nx, ny = p["x"] + dx, p["y"] + dy
            nx, ny = clamp_to_map(nx, ny)

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

        elif msg.get("type") == "weapon_select":
            wname = msg.get("weapon")
            if wname in WEAPONS:
                w = WEAPONS[wname]
                p["weapon"]   = wname
                p["ammo"]     = w["mag_size"]
                p["reloading"] = False
                p["last_shot"] = 0.0

        elif msg.get("type") == "starpower":
            active  = msg.get("active", False)
            brawler = msg.get("brawler")
            p["starpower"] = active
            if brawler == "mage":
                p["invisible"] = active

        elif msg.get("type") == "shoot":
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
                "x":      p["x"], "y": p["y"],
                "dx":     msg["dx"], "dy": msg["dy"],
                "speed":  msg.get("speed", weapon["bullet_speed"]),
                "damage": msg.get("damage", weapon["damage"]),
                "owner":  str(addr),
                "pierce": msg.get("pierce", False),
            })

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
                            p["alive"] = False
                            p["spectating"] = True   # dead → spectate, can't rejoin this round
                            # Keep phase="playing" and in_game=True so check_round_end counts correctly
                            print(f"💀 {p['name']} died → spectating until round ends")
                            check_round_end()
                        if not b.get("pierce") and b in bullets:
                            bullets.remove(b)
                        break

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
    print("╚══════════════════════════════════════╝\n")
    print(f"  Map: {MAP_W}x{MAP_H}  |  Max players: {MAX_PLAYERS}")
    print("  NOTE: Game auto-starts when all players (min 2) are ready.\n")

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
                print("⚠️  Game already running. Wait for round to end.")

        elif cmd == "players":
            if not players:
                print("  (no players)")
            for addr, p in players.items():
                status    = "🟢 alive" if p["alive"] else "💀 dead"
                phase_tag = f"[{p['phase']}]"
                ready_tag = " [READY]"     if p.get("ready") else ""
                spec_tag  = " [SPECTATING]" if p.get("spectating") else ""
                kick_tag  = " [KICKED]"    if p["name"] in kicked_names else ""
                print(f"  {p['name']:15s} {phase_tag:10s} {status}{ready_tag}{spec_tag}{kick_tag}  {addr}")

        elif cmd.startswith("kick "):
            name = cmd[5:].strip()
            kicked_matches = [(a, p) for a, p in players.items() if p["name"].lower() == name.lower()]
            if kicked_matches:
                addr, p = kicked_matches[0]
                pname = p["name"]
                kicked_names.add(pname)
                p["alive"] = False
                p["spectating"] = True
                # Don't change phase/in_game — let check_round_end handle it
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
            print("  Unknown command. Use ENTER to force-start, 'players', or 'kick <name>'.")


# ─── START ────────────────────────────────────────────────────────────────────
threading.Thread(target=handle, daemon=True).start()
threading.Thread(target=game_loop, daemon=True).start()
threading.Thread(target=check_inactive_players, daemon=True).start()

print("🚀 Server running on port", PORT)
server_console()
