import pygame
import sys
import os
import math
import random
import time

# Initialize PyGame
pygame.init()
pygame.mixer.init()

# Screen Settings
WIDTH, HEIGHT = 800, 600
win = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Zombie Survival Game")
clock = pygame.time.Clock()

# Load assets
ASSETS = os.path.join(os.path.dirname(__file__), "assets")
PLAYER_IMAGE = pygame.image.load(os.path.join(ASSETS, "player.png"))
PLAYER_IMAGE = pygame.transform.scale(PLAYER_IMAGE, (50, 50))

ZOMBIE_NORMAL_IMAGE = pygame.image.load(os.path.join(ASSETS, "zombie.png"))
ZOMBIE_NORMAL_IMAGE = pygame.transform.scale(ZOMBIE_NORMAL_IMAGE, (50, 50))

ZOMBIE_FAST_IMAGE = pygame.image.load(os.path.join(ASSETS, "zombie_fast.png"))
ZOMBIE_FAST_IMAGE = pygame.transform.scale(ZOMBIE_FAST_IMAGE, (50, 50))

ZOMBIE_TANK_IMAGE = pygame.image.load(os.path.join(ASSETS, "zombie_tank.png"))
ZOMBIE_TANK_IMAGE = pygame.transform.scale(ZOMBIE_TANK_IMAGE, (50, 50))

ZOMBIE_BOSS_IMAGE = pygame.image.load(os.path.join(ASSETS, "zombie_boss.png"))
ZOMBIE_BOSS_IMAGE = pygame.transform.scale(ZOMBIE_BOSS_IMAGE, (80, 80))

BULLET_IMAGE = pygame.image.load(os.path.join(ASSETS, "bullet.png"))
BULLET_IMAGE = pygame.transform.scale(BULLET_IMAGE, (15, 15))

# Sounds
shoot_sound = pygame.mixer.Sound("assets/sounds/shoot.mp3")
zombie_hit_sound = pygame.mixer.Sound("assets/sounds/zombie_hit.wav")
player_hit_sound = pygame.mixer.Sound("assets/sounds/player_hit.wav")
game_over_sound = pygame.mixer.Sound("assets/sounds/game_over.wav")

shoot_sound.set_volume(0.5)
zombie_hit_sound.set_volume(0.6)
player_hit_sound.set_volume(0.6)
game_over_sound.set_volume(0.7)

# Background music
pygame.mixer.music.load("assets/sounds/background.mp3")
pygame.mixer.music.play(-1)  # Loop forever
pygame.mixer.music.set_volume(0.4)

POWER_HEALTH_IMAGE = pygame.image.load(os.path.join(ASSETS, "heart.png"))
POWER_HEALTH_IMAGE = pygame.transform.scale(POWER_HEALTH_IMAGE, (20, 20))

POWER_SPEED_IMAGE = pygame.image.load(os.path.join(ASSETS, "speed.png"))
POWER_SPEED_IMAGE = pygame.transform.scale(POWER_SPEED_IMAGE, (20, 20))


# Player Setup
player_pos = [WIDTH // 2, HEIGHT // 2]
player_speed = 5
bullet_speed = 10
zombie_speed = 1.2
bullets = []
zombies = []
powerups = []
powerup_timer = 0
player_speed_boost_timer = 0
score = 0
splatters = []
start_time = time.time()

wave_number = 1
last_wave_time = time.time()
in_shop = False
shop_options = []
coins = 0  # Acts as currency

# Day/Night Cycle
day_duration = 60  # total seconds for full cycle (30s day, 30s night)
overlay_surface = pygame.Surface((WIDTH, HEIGHT))

current_weapon = "pistol"
WEAPONS = {
    "pistol": {"fire_rate": 0.3, "spread": 0, "bullets": 1},
    "shotgun": {"fire_rate": 0.9, "spread": 0.3, "bullets": 5}
}
last_shot_time = 0
font = pygame.font.SysFont("Arial", 28)
big_font = pygame.font.SysFont("Arial", 60)

player_health = 100
game_over = False
zombie_spawn_timer = 0
bullet_damage = 1

health_button = None
speed_button = None
bullet_button = None


ZOMBIE_TYPES = [
    {"name": "normal", "speed": 1.2, "health": 1},
    {"name": "fast", "speed": 2.0, "health": 1},
    {"name": "tank", "speed": 0.8, "health": 3},
    {"name": "boss", "speed": 0.5, "health": 10}
]

last_boss_spawn_time = 0  # Track when the last boss was spawned


#Create Shop options
def generate_shop():
    return [
        {"name": "Health Refill (+50)", "cost": 10, "effect": "health"},
        {"name": "Increase Speed", "cost": 15, "effect": "speed"},
        {"name": "Faster Fire Rate", "cost": 20, "effect": "fire_rate"},
        {"name": "Unlock Shotgun", "cost": 25, "effect": "shotgun"},
    ]


# Spawn Zombie at random edge
def spawn_zombie():
    edge = random.choice(['top', 'bottom', 'left', 'right'])
    if edge == 'top':
        pos = [random.randint(0, WIDTH), -50]
    elif edge == 'bottom':
        pos = [random.randint(0, WIDTH), HEIGHT + 50]
    elif edge == 'left':
        pos = [-50, random.randint(0, HEIGHT)]
    else:
        pos = [WIDTH + 50, random.randint(0, HEIGHT)]

    zombie_type = random.choice(ZOMBIE_TYPES)
    return {
        "pos": pos,
        "last_attack": 0,
        "speed": zombie_type["speed"],
        "health": zombie_type["health"],
        "type": zombie_type["name"]
    }

# Function to calculate direction
def get_direction(source, target):
    dx = target[0] - source[0]
    dy = target[1] - source[1]
    dist = math.hypot(dx, dy)
    if dist == 0:
        return 0, 0
    return dx / dist, dy / dist

def get_day_night_overlay():
    elapsed = (time.time() - start_time) % day_duration
    ratio = elapsed / (day_duration / 2)

    if ratio <= 1:
        # Day to night: darkening
        alpha = int(150 * ratio)
    else:
        # Night to day: lightening
        alpha = int(150 * (2 - ratio))

    overlay_surface.set_alpha(alpha)
    overlay_surface.fill((0, 0, 50))  # Dark blue tint
    return overlay_surface




# Main Loop
running = True
while running:
    clock.tick(60)
    win.fill((30, 30, 30))

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.MOUSEBUTTONDOWN and in_shop:
            mouse_pos = pygame.mouse.get_pos()

            if health_button and health_button.collidepoint(mouse_pos) and coins >= 10:
                player_health += 10
                coins -= 10

            if speed_button and speed_button.collidepoint(mouse_pos) and coins >= 10:
                player_speed += 1
                coins -= 10

            if bullet_button and bullet_button.collidepoint(mouse_pos) and coins >= 10:
                bullet_damage += 1
                coins -= 10

        # Fire Bullet
        if not game_over and event.type == pygame.KEYDOWN:

            if in_shop:
                if event.key == pygame.K_1 and len(shop_options) > 0:
                    upgrade = shop_options[0]
                elif event.key == pygame.K_2 and len(shop_options) > 1:
                    upgrade = shop_options[1]
                elif event.key == pygame.K_3 and len(shop_options) > 2:
                    upgrade = shop_options[2]
                elif event.key == pygame.K_4 and len(shop_options) > 3:
                    upgrade = shop_options[3]
                elif event.key == pygame.K_ESCAPE:
                    in_shop = False
                    continue

                if 'upgrade' in locals():
                    if coins >= upgrade["cost"]:
                        coins -= upgrade["cost"]
                        effect = upgrade["effect"]

                        if effect == "health":
                            player_health = min(100, player_health + 50)
                        elif effect == "speed":
                            player_speed += 1
                        elif effect == "fire_rate":
                            for w in WEAPONS:
                                WEAPONS[w]["fire_rate"] = max(0.1, WEAPONS[w]["fire_rate"] - 0.05)
                        elif effect == "shotgun":
                            current_weapon = "shotgun"

                        shop_options.remove(upgrade)
                        del upgrade


            if event.key == pygame.K_q:
                current_weapon = "shotgun" if current_weapon == "pistol" else "pistol"

            if event.key == pygame.K_SPACE:
                now = time.time()
                weapon = WEAPONS[current_weapon]
                if now - last_shot_time >= weapon["fire_rate"]:
                    shoot_sound.play()
                    base_dir = get_direction(player_pos, pygame.mouse.get_pos())
                    angle = math.atan2(base_dir[1], base_dir[0])

                    for _ in range(weapon["bullets"]):
                        spread_angle = angle + random.uniform(-weapon["spread"], weapon["spread"])
                        dir_x = math.cos(spread_angle)
                        dir_y = math.sin(spread_angle)
                        bullets.append({
                            "pos": [player_pos[0] + 20, player_pos[1] + 20],
                            "dir": (dir_x, dir_y)
                        })
                    last_shot_time = now

    if not game_over and not in_shop:
        # Player movement
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT]:
            player_pos[0] -= player_speed
        if keys[pygame.K_RIGHT]:
            player_pos[0] += player_speed
        if keys[pygame.K_UP]:
            player_pos[1] -= player_speed
        if keys[pygame.K_DOWN]:
            player_pos[1] += player_speed

        # Zombie spawn logic
        zombie_spawn_timer += 1
        elapsed_time = time.time() - start_time
        if time.time() - last_wave_time > 30:
            in_shop = True
            shop_options = generate_shop()
            last_wave_time = time.time()
            wave_number += 1

            # Initialize dummy buttons for mouse collision checks
            health_button = pygame.Rect(150, 140, 500, 60)
            speed_button = pygame.Rect(150, 220, 500, 60)
            bullet_button = pygame.Rect(150, 300, 500, 60)

        spawn_interval = max(30, 90 - int(elapsed_time // 10))
        if zombie_spawn_timer >= 90:
            zombies.append(spawn_zombie())
            zombie_spawn_timer = 0

            #Boss Zombie spawn logic
        # Boss Zombie spawn every 5 seconds
        if time.time() - last_boss_spawn_time > 5 and not any(z["type"] == "boss" for z in zombies):
            boss = spawn_zombie()
            boss["type"] = "boss"
            boss["speed"] = 0.5
            boss["health"] = 10
            zombies.append(boss)
            last_boss_spawn_time = time.time()

        # Power Ups
        powerup_timer += 1
        if powerup_timer > 600:  # Every 10 seconds
            powerup_timer = 0
            kind = random.choice(["health", "speed"])
            x = random.randint(50, WIDTH - 50)
            y = random.randint(50, HEIGHT - 50)
            powerups.append({"type": kind, "pos": [x, y]})

        # Move zombies toward player
        for zombie in zombies:
            zx, zy = zombie["pos"]
            dx, dy = get_direction([zx, zy], player_pos)
            zombie["pos"][0] += dx * zombie["speed"]
            zombie["pos"][1] += dy * zombie["speed"]

        # Move bullets
        for bullet in bullets:
            bullet["pos"][0] += bullet["dir"][0] * bullet_speed
            bullet["pos"][1] += bullet["dir"][1] * bullet_speed

        # Remove off-screen bullets
        bullets = [b for b in bullets if 0 <= b["pos"][0] <= WIDTH and 0 <= b["pos"][1] <= HEIGHT]

        # Collision: Bullet hits zombie
        for bullet in bullets[:]:
            for zombie in zombies[:]:
                bx, by = bullet["pos"]
                zx, zy = zombie["pos"]
                if abs(bx - zx) < 30 and abs(by - zy) < 30:
                    zombie_hit_sound.play()
                    zombie["health"] -= bullet_damage
                    if zombie["health"] <= 0:
                        coins += 5
                        splatters.append((zx + 25, zy + 25, time.time()))
                        zombies.remove(zombie)
                        score += 1
                    bullets.remove(bullet)
                    break

        # Check for zombie-player collision
        current_time = time.time()
        player_rect = pygame.Rect(player_pos[0], player_pos[1], 50, 50)

        for p in powerups[:]:
            powerup_rect = pygame.Rect(p["pos"][0] - 10, p["pos"][1] - 10, 20, 20)
            if player_rect.colliderect(powerup_rect):
                if p["type"] == "health":
                    player_health = min(100, player_health + 30)
                elif p["type"] == "speed":
                    player_speed_boost_timer = time.time()
                    player_speed = 8
                powerups.remove(p)

        # Reset speed after boost ends
        if player_speed_boost_timer and time.time() - player_speed_boost_timer > 5:
            player_speed = 5
            player_speed_boost_timer = 0

        for zombie in zombies:
            zombie_rect = pygame.Rect(zombie["pos"][0], zombie["pos"][1], 50, 50)
            if player_rect.colliderect(zombie_rect):
                if current_time - zombie["last_attack"] > 0.8:  # cooldown in seconds
                    player_health -= 10
                    zombie["last_attack"] = current_time
                    player_hit_sound.play()

        if player_health <= 0 and not game_over:
            game_over_sound.play()
            game_over = True

    # Draw player, zombie, bullets
    win.blit(PLAYER_IMAGE, player_pos)

    for zombie in zombies:
        if zombie["type"] == "fast":
            img = ZOMBIE_FAST_IMAGE
        elif zombie["type"] == "tank":
            img = ZOMBIE_TANK_IMAGE
        elif zombie["type"] == "boss":
            img = ZOMBIE_BOSS_IMAGE
        else:
            img = ZOMBIE_NORMAL_IMAGE
        win.blit(img, zombie["pos"])

    for bullet in bullets:
        win.blit(BULLET_IMAGE, bullet["pos"])

    for p in powerups:
        if p["type"] == "health":
            win.blit(POWER_HEALTH_IMAGE, (p["pos"][0] - 10, p["pos"][1] - 10))
        elif p["type"] == "speed":
            win.blit(POWER_SPEED_IMAGE, (p["pos"][0] - 10, p["pos"][1] - 10))

    # Draw Score
    score_text = font.render(f"Score: {score}", True, (255, 255, 255))
    win.blit(score_text, (10, 10))

    #Show Current Weapon on HUD
    weapon_text = font.render(f"Weapon: {current_weapon.upper()}", True, (200, 200, 50))
    win.blit(weapon_text, (10, 110))

    # Draw Health Bar
    pygame.draw.rect(win, (255, 0, 0), (10, 50, 200, 20))
    pygame.draw.rect(win, (0, 255, 0), (10, 50, max(0, int(2 * player_health)), 20))
    health_text = font.render(f"Health: {int(player_health)}", True, (255, 255, 255))
    win.blit(health_text, (220, 48))

    # Show wave number
    wave_text = font.render(f"Wave: {wave_number}", True, (255, 255, 255))
    win.blit(wave_text, (10, 140))

    # Time Bar
    if player_speed_boost_timer:
        remaining = max(0, 5 - (time.time() - player_speed_boost_timer))
        pygame.draw.rect(win, (0, 200, 255), (10, 80, int((remaining / 5) * 200), 10))
        speed_text = font.render("Speed Boost!", True, (0, 200, 255))
        win.blit(speed_text, (220, 75))

    # Game Over screen
    if game_over:
        over_text = big_font.render("GAME OVER", True, (255, 50, 50))
        win.blit(over_text, (WIDTH // 2 - 160, HEIGHT // 2 - 40))
        retry_text = font.render("Press R to Restart or ESC to Quit", True, (200, 200, 200))
        win.blit(retry_text, (WIDTH // 2 - 180, HEIGHT // 2 + 30))

        keys = pygame.key.get_pressed()
        if keys[pygame.K_r]:
            # Reset game
            pygame.mouse.set_pos(WIDTH // 2, HEIGHT // 2)
            player_pos = [WIDTH // 2, HEIGHT // 2]
            player_health = 100
            score = 0
            zombies.clear()
            bullets.clear()
            game_over = False
        elif keys[pygame.K_ESCAPE]:
            running = False

    # Draw blood splatters
    for splatter in splatters[:]:
        x,y,t = splatter
        if time.time() - t < 1.0:
            pygame.draw.circle(win, (139, 0, 0), (int(x), int(y)), 25)
        else:
            splatters.remove(splatter)

    # Draw Day/Night overlay
    win.blit(get_day_night_overlay(), (0, 0))

    # Draw the Shop
    if in_shop:
        win.fill((20, 20, 20))
        shop_title = big_font.render("UPGRADE SHOP", True, (255, 255, 0))
        win.blit(shop_title, (WIDTH // 2 - 180, 40))

        coin_text = font.render(f"Coins: {coins}", True, (255, 255, 255))
        win.blit(coin_text, (WIDTH - 200, 10))

        for i, option in enumerate(shop_options):
            y = 140 + i * 80
            pygame.draw.rect(win, (50, 50, 50), (150, y, 500, 60))
            name = option["name"]
            cost = option["cost"]
            text = font.render(f"{i + 1}. {name} - {cost} coins", True, (255, 255, 255))
            win.blit(text, (160, y + 15))



        exit_text = font.render("Press ESC to Continue", True, (150, 150, 150))
        win.blit(exit_text, (WIDTH // 2 - 140, HEIGHT - 60))

    pygame.display.update()

pygame.quit()
sys.exit()
