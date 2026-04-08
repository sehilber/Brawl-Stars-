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

INACTIVE_TIMEOUT = 10
 
players = {}

bullets = []
 
MAP_WALLS = [

    {"x": 300, "y": 200, "w": 200, "h": 20},

    {"x": 100, "y": 400, "w": 20, "h": 150},

    {"x": 500, "y": 350, "w": 150, "h": 20},

]
 
WEAPONS = {

    "ak47": {"damage": 20, "bullet_speed": 12, "fire_rate": 0.12, "mag_size": 30, "reload_time": 1.5},

    "minigun": {"damage": 5, "bullet_speed": 14, "fire_rate": 0.05, "mag_size": 100, "reload_time": 3.0},

    "sniper": {"damage": 80, "bullet_speed": 20, "fire_rate": 1.2, "mag_size": 3, "reload_time": 2.5},

    "magic": {"damage": 35, "bullet_speed": 12, "fire_rate": 0.4, "mag_size": 10, "reload_time": 1.5}

}
 
def new_player():

    weapon_name = "ak47"

    w = WEAPONS[weapon_name]

    return {

        "x": 100,

        "y": 100,

        "hp": 100,

        "alive": True,

        "weapon": weapon_name,

        "ammo": w["mag_size"],

        "last_shot": 0.0,

        "reloading": False,

        "last_activity": time.time(),

        "invisible": False,

        "starpower": False

    }
 
def collide_wall(x, y):

    for w in MAP_WALLS:

        if (x > w["x"] and x < w["x"] + w["w"] and

            y > w["y"] and y < w["y"] + w["h"]):

            return True

    return False
 
def finish_reload(addr):

    if addr not in players:

        return

    p = players[addr]

    w = WEAPONS[p["weapon"]]

    p["ammo"] = w["mag_size"]

    p["reloading"] = False
 
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

            players[addr] = new_player()

            print("Spieler verbunden:", addr)
 
        p = players[addr]

        p["last_activity"] = time.time()
 
        if not p["alive"]:

            continue
 
        # 🏃 Movement

        if msg["type"] == "move":

            speed = 4

            dx = (-speed if msg.get("left") else 0) + (speed if msg.get("right") else 0)

            dy = (-speed if msg.get("up") else 0) + (speed if msg.get("down") else 0)
 
            nx = p["x"] + dx

            ny = p["y"] + dy
 
            if not collide_wall(nx, ny):

                p["x"] = nx

                p["y"] = ny
 
        # 🔫 Weapon wählen

        elif msg["type"] == "weapon_select":

            wname = msg.get("weapon")

            if wname in WEAPONS:

                w = WEAPONS[wname]

                p["weapon"] = wname

                p["ammo"] = w["mag_size"]

                p["reloading"] = False

                p["last_shot"] = 0.0
 
        # ⭐ STARPOWER

        elif msg["type"] == "starpower":

            active = msg.get("active", False)

            brawler = msg.get("brawler")
 
            p["starpower"] = active
 
            if brawler == "mage":

                p["invisible"] = active  # 🧙 Unsichtbar
 
        # 🔫 Schießen

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

                "x": p["x"],

                "y": p["y"],

                "dx": msg["dx"],

                "dy": msg["dy"],

                "speed": msg.get("speed", weapon["bullet_speed"]),

                "damage": msg.get("damage", weapon["damage"]),

                "owner": str(addr),

                "pierce": msg.get("pierce", False)  # 🎯 Sniper Starpower

            })
 
def respawn(addr):

    if addr in players:

        players[addr] = new_player()
 
def check_inactive_players():

    while True:

        now = time.time()
 
        for addr in list(players.keys()):

            p = players[addr]

            if now - p["last_activity"] > INACTIVE_TIMEOUT:

                print("❌ KICK:", addr)

                del players[addr]
 
        time.sleep(2)
 
def game_loop():

    while True:

        for b in bullets[:]:

            b["x"] += b["dx"] * b["speed"]

            b["y"] += b["dy"] * b["speed"]
 
            # 🎯 Wand-Kollision (nur wenn NICHT pierce)

            if not b.get("pierce") and collide_wall(b["x"], b["y"]):

                bullets.remove(b)

                continue
 
            for addr, p in list(players.items()):

                if str(addr) == b["owner"] or not p["alive"]:

                    continue
 
                dist = math.hypot(p["x"] - b["x"], p["y"] - b["y"])
 
                if dist < 15:

                    p["hp"] -= b["damage"]
 
                    if p["hp"] <= 0:

                        p["alive"] = False

                        threading.Timer(3, respawn, args=[addr]).start()
 
                    # 🎯 Wenn kein Pierce → Bullet löschen

                    if not b.get("pierce") and b in bullets:

                        bullets.remove(b)
 
                    break
 
        state = {

            "players": {str(addr): p for addr, p in players.items()},

            "bullets": bullets,

            "walls": MAP_WALLS

        }
 
        encoded = json.dumps(state).encode()
 
        for addr in players:

            server.sendto(encoded, addr)
 
        time.sleep(1/60)
 
threading.Thread(target=handle, daemon=True).start()

threading.Thread(target=game_loop, daemon=True).start()

threading.Thread(target=check_inactive_players, daemon=True).start()
 
print("Server läuft...")
 
while True:

    time.sleep(1)
 