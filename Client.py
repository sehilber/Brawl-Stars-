import socket
import threading
import json
import pygame
import math
SERVER_IP = "192.168.0.100"  # qanpassen
PORT = 5555
client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
pygame.init()
screen = pygame.display.set_mode((800, 600))
clock = pygame.time.Clock()
font = pygame.font.SysFont(None, 24)
players = {}
bullets = []
walls = []
my_weapon = "ak47"   # default
def send_weapon_select():
    msg = json.dumps({
        "type": "weapon_select",
        "weapon": my_weapon
    })
    client.sendto(msg.encode(), (SERVER_IP, PORT))
def receive():
    global players, bullets, walls
    while True:
        try:
            data, _ = client.recvfrom(65535)
            state = json.loads(data.decode())
            players = state["players"]
            bullets = state["bullets"]
            walls = state["walls"]
        except Exception as e:
            print("Receive error:", e)
threading.Thread(target=receive, daemon=True).start()
# einmal initial Waffe senden
send_weapon_select()
running = True
while running:
    screen.fill((40, 40, 40))
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_1:
                my_weapon = "ak47"
                send_weapon_select()
            elif event.key == pygame.K_2:
                my_weapon = "minigun"
                send_weapon_select()
            elif event.key == pygame.K_3:
                my_weapon = "sniper"
                send_weapon_select()
        if event.type == pygame.MOUSEBUTTONDOWN:
            mx, my = pygame.mouse.get_pos()
            px, py = 400, 300  # eigene Sicht zentriert
            angle = math.atan2(my - py, mx - px)
            msg = json.dumps({
                "type": "shoot",
                "dx": math.cos(angle),
                "dy": math.sin(angle)
            })
            client.sendto(msg.encode(), (SERVER_IP, PORT))
    keys = pygame.key.get_pressed()
    msg = json.dumps({
        "type": "move",
        "up": keys[pygame.K_w],
        "down": keys[pygame.K_s],
        "left": keys[pygame.K_a],
        "right": keys[pygame.K_d]
    })
    client.sendto(msg.encode(), (SERVER_IP, PORT))
    for w in walls:
        pygame.draw.rect(screen, (100, 100, 100),
                         (w["x"], w["y"], w["w"], w["h"]))
    for addr, p in players.items():
        color = (0, 200, 255) if p["alive"] else (100, 100, 100)
        pygame.draw.circle(screen, color, (int(p["x"]), int(p["y"])), 12)
        pygame.draw.rect(screen, (255, 0, 0),
                         (p["x"] - 15, p["y"] - 25, 30, 5))
        pygame.draw.rect(screen, (0, 255, 0),
                         (p["x"] - 15, p["y"] - 25, 30 * (p["hp"] / 100), 5))
    for b in bullets:
        pygame.draw.circle(screen, (255, 200, 0),
                           (int(b["x"]), int(b["y"])), 5)
    # HUD: einfache Anzeige für eigene Waffe + Ammo, falls bekannt
    # wir suchen irgendeinen Player als "mich" gibt's hier noch nicht eindeutig,
    # also zeigen wir nur die aktuelle Waffe an
    weapon_text = font.render(f"Weapon: {my_weapon}", True, (255, 255, 255))
    screen.blit(weapon_text, (10, 10))
    pygame.display.flip()
    clock.tick(60)
pygame.quit()