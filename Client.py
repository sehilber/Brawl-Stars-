import socket
import threading
import json
import pygame
import math

SERVER_IP = "127.0.0.1"  # LAN IP ändern!
PORT = 5555

client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

pygame.init()
screen = pygame.display.set_mode((800, 600))
clock = pygame.time.Clock()

players = {}
bullets = []
walls = []

def receive():
    global players, bullets, walls
    while True:
        try:
            data, _ = client.recvfrom(4096)
            state = json.loads(data.decode())
            players = state["players"]
            bullets = state["bullets"]
            walls = state["walls"]
        except:
            pass

threading.Thread(target=receive, daemon=True).start()

running = True

while running:
    screen.fill((40, 40, 40))

    dx, dy = 0, 0

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.MOUSEBUTTONDOWN:
            mx, my = pygame.mouse.get_pos()
            px, py = 400, 300

            angle = math.atan2(my - py, mx - px)
            msg = json.dumps({
                "type": "shoot",
                "dx": math.cos(angle),
                "dy": math.sin(angle)
            })
            client.sendto(msg.encode(), (SERVER_IP, PORT))

    keys = pygame.key.get_pressed()
    if keys[pygame.K_w]: dy = -4
    if keys[pygame.K_s]: dy = 4
    if keys[pygame.K_a]: dx = -4
    if keys[pygame.K_d]: dx = 4

    msg = json.dumps({"type": "move", "dx": dx, "dy": dy})
    client.sendto(msg.encode(), (SERVER_IP, PORT))

    # Wände
    for w in walls:
        pygame.draw.rect(screen, (100, 100, 100),
                         (w["x"], w["y"], w["w"], w["h"]))

    # Spieler
    for addr, p in players.items():
        color = (0, 200, 255) if p["alive"] else (100, 100, 100)
        pygame.draw.circle(screen, color, (int(p["x"]), int(p["y"])), 12)

        # HP
        pygame.draw.rect(screen, (255,0,0),
                         (p["x"]-15, p["y"]-25, 30, 5))
        pygame.draw.rect(screen, (0,255,0),
                         (p["x"]-15, p["y"]-25, 30*(p["hp"]/100), 5))

    # Bullets
    for b in bullets:
        pygame.draw.circle(screen, (255, 200, 0),
                           (int(b["x"]), int(b["y"])), 5)

    pygame.display.flip()
    clock.tick(60)

pygame.quit()