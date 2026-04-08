import socket
import threading
import json
import pygame
import math

SERVER_IP = "192.168.0.100"
PORT = 5555

client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

pygame.init()
screen = pygame.display.set_mode((800, 600))
clock = pygame.time.Clock()
font = pygame.font.SysFont(None, 32)

players = {}
bullets = []
walls = []

# 🧠 Brawler System
BRAWLERS = {
    "sniper": {
        "weapon": "sniper",
        "cooldown": 800,
        "bullet_speed": 18,
        "damage": 80,
    },
    "minigun": {
        "weapon": "minigun",
        "cooldown": 100,
        "bullet_speed": 8,
        "damage": 10,
    },
    "mage": {
        "weapon": "magic",
        "cooldown": 400,
        "bullet_speed": 12,
        "damage": 35,
    }
}

# 🎮 Auswahl GUI
def select_brawler():
    selecting = True
    selected = None

    while selecting:
        screen.fill((30, 30, 30))

        title = font.render("Wähle deinen Brawler", True, (255, 255, 255))
        screen.blit(title, (260, 120))

        options = ["1: Sniper", "2: Minigun", "3: Magier"]

        for i, text in enumerate(options):
            t = font.render(text, True, (200, 200, 200))
            screen.blit(t, (300, 220 + i * 60))

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_1:
                    selected = "sniper"
                    selecting = False
                elif event.key == pygame.K_2:
                    selected = "minigun"
                    selecting = False
                elif event.key == pygame.K_3:
                    selected = "mage"
                    selecting = False

    return selected


# 👉 Auswahl
my_brawler = select_brawler()
stats = BRAWLERS[my_brawler]

my_weapon = stats["weapon"]
shoot_cooldown = stats["cooldown"]
bullet_speed = stats["bullet_speed"]
damage = stats["damage"]

last_shot = 0

# ⭐ STARPOWER
starpower_active = False
starpower_start = 0
starpower_duration = 5000
starpower_cooldown = 10000
last_starpower = -10000


def activate_starpower():
    global starpower_active, starpower_start, last_starpower

    now = pygame.time.get_ticks()

    if now - last_starpower > starpower_cooldown:
        starpower_active = True
        starpower_start = now
        last_starpower = now

        msg = json.dumps({
            "type": "starpower",
            "brawler": my_brawler,
            "active": True
        })
        client.sendto(msg.encode(), (SERVER_IP, PORT))


def update_starpower():
    global starpower_active

    if starpower_active:
        now = pygame.time.get_ticks()
        if now - starpower_start > starpower_duration:
            starpower_active = False

            msg = json.dumps({
                "type": "starpower",
                "brawler": my_brawler,
                "active": False
            })
            client.sendto(msg.encode(), (SERVER_IP, PORT))


def send_weapon_select():
    msg = json.dumps({
        "type": "weapon_select",
        "weapon": my_weapon,
        "brawler": my_brawler
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
send_weapon_select()

running = True
while running:
    screen.fill((40, 40, 40))

    update_starpower()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        # ⭐ F drücken
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_f:
                activate_starpower()

        # 🔫 Schießen
        if event.type == pygame.MOUSEBUTTONDOWN:
            now = pygame.time.get_ticks()

            current_cooldown = shoot_cooldown
            current_speed = bullet_speed

            # ⭐ Minigun Boost
            if starpower_active and my_brawler == "minigun":
                current_cooldown = 40

            if now - last_shot > current_cooldown:
                last_shot = now

                mx, my = pygame.mouse.get_pos()
                px, py = 400, 300

                angle = math.atan2(my - py, mx - px)

                msg = json.dumps({
                    "type": "shoot",
                    "dx": math.cos(angle),
                    "dy": math.sin(angle),
                    "speed": current_speed,
                    "damage": damage,
                    "weapon": my_weapon,
                    "pierce": starpower_active and my_brawler == "sniper"
                })

                client.sendto(msg.encode(), (SERVER_IP, PORT))

    # 🔫 AUTO FIRE Minigun
    if starpower_active and my_brawler == "minigun":
        now = pygame.time.get_ticks()
        if now - last_shot > 40:
            last_shot = now

            mx, my = pygame.mouse.get_pos()
            px, py = 400, 300
            angle = math.atan2(my - py, mx - px)

            msg = json.dumps({
                "type": "shoot",
                "dx": math.cos(angle),
                "dy": math.sin(angle),
                "speed": bullet_speed,
                "damage": damage,
                "weapon": my_weapon
            })

            client.sendto(msg.encode(), (SERVER_IP, PORT))

    # Movement
    keys = pygame.key.get_pressed()
    msg = json.dumps({
        "type": "move",
        "up": keys[pygame.K_w],
        "down": keys[pygame.K_s],
        "left": keys[pygame.K_a],
        "right": keys[pygame.K_d]
    })
    client.sendto(msg.encode(), (SERVER_IP, PORT))

    # Zeichnen
    for w in walls:
        pygame.draw.rect(screen, (100, 100, 100),
                         (w["x"], w["y"], w["w"], w["h"]))

    for addr, p in players.items():
        if p.get("invisible"):  # 👈 Magier unsichtbar
            continue

        color = (0, 200, 255) if p["alive"] else (100, 100, 100)
        pygame.draw.circle(screen, color,
                           (int(p["x"]), int(p["y"])), 12)

        pygame.draw.rect(screen, (255, 0, 0),
                         (p["x"] - 15, p["y"] - 25, 30, 5))
        pygame.draw.rect(screen, (0, 255, 0),
                         (p["x"] - 15, p["y"] - 25,
                          30 * (p["hp"] / 100), 5))

    for b in bullets:
        pygame.draw.circle(screen, (255, 200, 0),
                           (int(b["x"]), int(b["y"])), 5)

    # HUD
    status = "READY"
    if starpower_active:
        status = "ACTIVE"
    elif pygame.time.get_ticks() - last_starpower < starpower_cooldown:
        status = "COOLDOWN"

    hud1 = font.render(f"Brawler: {my_brawler}", True, (255, 255, 255))
    hud2 = font.render(f"Starpower: {status}", True, (255, 255, 0))

    screen.blit(hud1, (10, 10))
    screen.blit(hud2, (10, 40))

    pygame.display.flip()
    clock.tick(60)

pygame.quit()