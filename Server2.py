import socket

import threading

import json

import time

import math
 
HOST = "0.0.0.0"

PORT = 5555
 
server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

server.bind((HOST, PORT))
 
MAX_PLAYERS = 5
 
players = {}  # addr -> player

bullets = []
 
MAP_WALLS = [

    {"x": 300, "y": 200, "w": 200, "h": 20},

    {"x": 100, "y": 400, "w": 20, "h": 150},

    {"x": 500, "y": 350, "w": 150, "h": 20},

]
 
def new_player():

    return {

        "x": 100,

        "y": 100,

        "hp": 100,

        "alive": True

    }
 
def collide_wall(x, y):

    for w in MAP_WALLS:

        if (x > w["x"] and x < w["x"] + w["w"] and

            y > w["y"] and y < w["y"] + w["h"]):

            return True

    return False
 
def handle():

    while True:

        data, addr = server.recvfrom(1024)

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
 
        if not p["alive"]:

            continue
 
        if msg["type"] == "move":

            speed = 4
 
            dx = (-speed if msg.get("left") else 0) + (speed if msg.get("right") else 0)

            dy = (-speed if msg.get("up") else 0) + (speed if msg.get("down") else 0)
 
            nx = p["x"] + dx

            ny = p["y"] + dy
 
            if not collide_wall(nx, ny):

                p["x"] = nx

                p["y"] = ny
 
        if msg["type"] == "shoot":

            bullets.append({

                "x": p["x"],

                "y": p["y"],

                "dx": msg["dx"],

                "dy": msg["dy"],

                "owner": str(addr)

            })
 
def respawn(addr):

    if addr in players:

        players[addr] = new_player()
 
def game_loop():

    while True:

        for b in bullets[:]:

            b["x"] += b["dx"] * 10

            b["y"] += b["dy"] * 10
 
            if collide_wall(b["x"], b["y"]):

                bullets.remove(b)

                continue
 
            for addr, p in players.items():

                if str(addr) == b["owner"] or not p["alive"]:

                    continue
 
                dist = math.hypot(p["x"] - b["x"], p["y"] - b["y"])

                if dist < 15:

                    p["hp"] -= 20

                    if p["hp"] <= 0:

                        p["alive"] = False

                        threading.Timer(3, respawn, args=[addr]).start()

                    bullets.remove(b)

                    break
 
        state = json.dumps({

            "players": {str(addr): p for addr, p in players.items()},

            "bullets": bullets,

            "walls": MAP_WALLS

        })
 
        for addr in players:

            server.sendto(state.encode(), addr)
 
        time.sleep(1/60)
 
threading.Thread(target=handle, daemon=True).start()

threading.Thread(target=game_loop, daemon=True).start()
 
print("Server läuft...")

while True:

    time.sleep(1)
 

 
