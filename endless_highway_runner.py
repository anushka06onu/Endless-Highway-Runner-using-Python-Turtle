#!/usr/bin/env python3
"""
============================================================
  ENDLESS HIGHWAY RUNNER
  A+ Level Computer Graphics Project
  Built entirely with Python Turtle Graphics

  Course Concepts Used:
  - Bresenham Line Algorithm  → road borders, lane dividers,
                                 car body outlines
  - Shapes + loops            → rectangles for cars, road, UI
  - Colors & fills            → all elements
  - Keyboard control          → left/right lane change, speed
  - Continuous animation      → screen.tracer(0) + update loop
  - Collision detection       → game over logic
  - Score / difficulty system → speed increases over time

  CONTROLS:
  LEFT  Arrow → Move player car LEFT one lane
  RIGHT Arrow → Move player car RIGHT one lane
  UP    Arrow → Increase speed
  DOWN  Arrow → Decrease speed
  SPACE       → Restart after Game Over
  Q           → Quit
============================================================
"""

import turtle
import time
import random

# ─────────────────────────────────────────────
#  SCREEN SETUP
# ─────────────────────────────────────────────
screen = turtle.Screen()
screen.setup(width=600, height=750)
screen.title("Endless Highway Runner")
screen.bgcolor("#1a1a2e")
screen.tracer(0)

# ─────────────────────────────────────────────
#  CONSTANTS
# ─────────────────────────────────────────────
ROAD_LEFT   = -180
ROAD_RIGHT  =  180
ROAD_WIDTH  =  360
LANE_COUNT  =  4
LANE_WIDTH  = ROAD_WIDTH // LANE_COUNT   # 90 px each

# lane center x positions
LANE_CENTERS = [ROAD_LEFT + LANE_WIDTH * i + LANE_WIDTH // 2 for i in range(LANE_COUNT)]
# e.g. [-135, -45, 45, 135]

PLAYER_Y       = -270
PLAYER_WIDTH   =  50
PLAYER_HEIGHT  =  80
ENEMY_WIDTH    =  50
ENEMY_HEIGHT   =  80

BASE_SPEED     = 4.0
MAX_SPEED      = 14.0
MIN_SPEED      = 2.0
SPEED_STEP     = 0.5
SPAWN_INTERVAL = 40   # frames between spawns

# ─────────────────────────────────────────────
#  GAME STATE
# ─────────────────────────────────────────────
player_lane   = 1        # 0-indexed
game_speed    = BASE_SPEED
score         = 0
game_over     = False
frame_count   = 0
enemy_cars    = []       # list of {lane, y, color}

# dashed line offset for scrolling road markings
dash_offset = 0

# ─────────────────────────────────────────────
#  TURTLE PENS
# ─────────────────────────────────────────────
bg_pen = turtle.Turtle()
bg_pen.hideturtle(); bg_pen.speed(0); bg_pen.penup()

road_pen = turtle.Turtle()
road_pen.hideturtle(); road_pen.speed(0); road_pen.penup()

player_pen = turtle.Turtle()
player_pen.hideturtle(); player_pen.speed(0); player_pen.penup()

enemy_pen = turtle.Turtle()
enemy_pen.hideturtle(); enemy_pen.speed(0); enemy_pen.penup()

hud_pen = turtle.Turtle()
hud_pen.hideturtle(); hud_pen.speed(0); hud_pen.penup()

# ─────────────────────────────────────────────
#  BRESENHAM LINE ALGORITHM
# ─────────────────────────────────────────────
def bresenham_line(t, x1, y1, x2, y2, color="white", size=2):
    t.pencolor(color)
    t.pensize(size)
    dx = abs(x2 - x1)
    dy = abs(y2 - y1)
    sx = 1 if x1 < x2 else -1
    sy = 1 if y1 < y2 else -1
    x, y = int(x1), int(y1)
    err = dx - dy
    t.penup()
    t.goto(x, y)
    t.pendown()
    while True:
        t.goto(x, y)
        if x == int(x2) and y == int(y2):
            break
        e2 = 2 * err
        if e2 > -dy:
            err -= dy
            x   += sx
        if e2 < dx:
            err += dx
            y   += sy
    t.penup()

# ─────────────────────────────────────────────
#  DRAW RECTANGLE HELPER
# ─────────────────────────────────────────────
def draw_rect(t, x, y, w, h, fill, outline="black", pen_size=1):
    t.penup()
    t.goto(x, y)
    t.pendown()
    t.color(outline, fill)
    t.pensize(pen_size)
    t.begin_fill()
    for _ in range(2):
        t.forward(w)
        t.left(90)
        t.forward(h)
        t.left(90)
    t.end_fill()
    t.penup()

# ─────────────────────────────────────────────
#  DRAW CIRCLE HELPER (built-in, fast)
# ─────────────────────────────────────────────
def draw_circle(t, cx, cy, r, fill, outline="black"):
    t.penup()
    t.goto(cx, cy - r)
    t.pendown()
    t.color(outline, fill)
    t.begin_fill()
    t.circle(r)
    t.end_fill()
    t.penup()

# ─────────────────────────────────────────────
#  SIDE SCENERY (grass strips)
# ─────────────────────────────────────────────
def draw_background():
    bg_pen.clear()
    # left grass
    draw_rect(bg_pen, -300, -375, 120, 750, "#1e4d2b", "#1e4d2b")
    # right grass
    draw_rect(bg_pen, 180,  -375, 120, 750, "#1e4d2b", "#1e4d2b")

# ─────────────────────────────────────────────
#  DRAW ROAD + LANE DIVIDERS (scrolling)
# ─────────────────────────────────────────────
def draw_road():
    road_pen.clear()

    # main road
    draw_rect(road_pen, ROAD_LEFT, -375, ROAD_WIDTH, 750, "#3d3d3d", "#3d3d3d")

    # side borders using Bresenham
    bresenham_line(road_pen, ROAD_LEFT,  -375, ROAD_LEFT,  375, "#f0c040", 4)
    bresenham_line(road_pen, ROAD_RIGHT, -375, ROAD_RIGHT, 375, "#f0c040", 4)

    # dashed lane dividers (scrolling)
    dash_h   = 40
    gap_h    = 25
    cycle    = dash_h + gap_h

    for lane_i in range(1, LANE_COUNT):          # 3 internal dividers
        lx = ROAD_LEFT + LANE_WIDTH * lane_i

        y = -375 + (int(dash_offset) % cycle) - cycle
        while y < 375:
            y1 = max(y, -375)
            y2 = min(y + dash_h, 375)
            if y2 > y1:
                bresenham_line(road_pen, lx, y1, lx, y2, "#ffffff", 2)
            y += cycle

# ─────────────────────────────────────────────
#  DRAW A CAR (rectangle-based, clean design)
# ─────────────────────────────────────────────
def draw_car(t, cx, cy, color, is_player=False):
    hw = PLAYER_WIDTH  // 2
    hh = PLAYER_HEIGHT // 2

    # shadow
    draw_rect(t, cx - hw + 3, cy - hh - 3, PLAYER_WIDTH, PLAYER_HEIGHT,
              "#111111", "#111111")

    # body
    draw_rect(t, cx - hw, cy - hh, PLAYER_WIDTH, PLAYER_HEIGHT,
              color, "#000000", 2)

    # roof
    roof_w = int(PLAYER_WIDTH * 0.65)
    roof_h = int(PLAYER_HEIGHT * 0.42)
    draw_rect(t, cx - roof_w // 2, cy,
              roof_w, roof_h, color, "#000000", 1)

    # front glass
    win_w = int(PLAYER_WIDTH * 0.52)
    win_h = int(PLAYER_HEIGHT * 0.18)
    glass = "#a8d8ea" if is_player else "#90b4c8"
    draw_rect(t, cx - win_w // 2, cy + int(PLAYER_HEIGHT * 0.24),
              win_w, win_h, glass, "#333333", 1)

    # rear glass
    draw_rect(t, cx - win_w // 2, cy + int(PLAYER_HEIGHT * 0.02),
              win_w, int(win_h * 0.8), glass, "#333333", 1)

    # wheels
    wheel_r = 9
    offx = hw - 2
    draw_circle(t, cx - offx, cy - hh + 10,  wheel_r, "#111111", "#555555")
    draw_circle(t, cx + offx, cy - hh + 10,  wheel_r, "#111111", "#555555")
    draw_circle(t, cx - offx, cy + hh - 18,  wheel_r, "#111111", "#555555")
    draw_circle(t, cx + offx, cy + hh - 18,  wheel_r, "#111111", "#555555")

    # lights
    if is_player:
        draw_circle(t, cx - hw + 8, cy + hh - 6, 5, "#ffff88", "#ffff88")
        draw_circle(t, cx + hw - 8, cy + hh - 6, 5, "#ffff88", "#ffff88")
    else:
        draw_circle(t, cx - hw + 8, cy - hh + 6, 5, "#ff4444", "#ff4444")
        draw_circle(t, cx + hw - 8, cy - hh + 6, 5, "#ff4444", "#ff4444")

    # door line with Bresenham
    bresenham_line(t,
                   cx - hw + 4, cy - int(PLAYER_HEIGHT * 0.05),
                   cx + hw - 4, cy - int(PLAYER_HEIGHT * 0.05),
                   "#333333", 1)

# ─────────────────────────────────────────────
#  DRAW PLAYER
# ─────────────────────────────────────────────
def draw_player():
    player_pen.clear()
    cx = LANE_CENTERS[player_lane]
    draw_car(player_pen, cx, PLAYER_Y, "#00cc66", is_player=True)

# ─────────────────────────────────────────────
#  ENEMY CAR MANAGEMENT
# ─────────────────────────────────────────────
ENEMY_COLORS = [
    "#e74c3c", "#3498db", "#f39c12", "#9b59b6",
    "#e67e22", "#1abc9c", "#e91e63", "#00bcd4"
]

def spawn_enemy():
    lane = random.randint(0, LANE_COUNT - 1)
    enemy_cars.append({
        "lane":  lane,
        "y":     390,
        "color": random.choice(ENEMY_COLORS),
    })

def update_enemies():
    for car in enemy_cars:
        car["y"] -= game_speed

def draw_enemies():
    enemy_pen.clear()
    for car in enemy_cars:
        cx = LANE_CENTERS[car["lane"]]
        draw_car(enemy_pen, cx, car["y"], car["color"], is_player=False)

def cleanup_enemies():
    global score
    before = len(enemy_cars)
    enemy_cars[:] = [c for c in enemy_cars if c["y"] > -400]
    passed = before - len(enemy_cars)
    score += passed * 10

# ─────────────────────────────────────────────
#  COLLISION DETECTION
# ─────────────────────────────────────────────
def check_collision():
    px = LANE_CENTERS[player_lane]
    for car in enemy_cars:
        cx = LANE_CENTERS[car["lane"]]
        dx = abs(cx - px)
        dy = abs(car["y"] - PLAYER_Y)
        if dx < PLAYER_WIDTH - 10 and dy < PLAYER_HEIGHT - 10:
            return True
    return False

# ─────────────────────────────────────────────
#  HUD
# ─────────────────────────────────────────────
def draw_hud():
    hud_pen.clear()

    # score
    hud_pen.penup()
    hud_pen.goto(-280, 320)
    hud_pen.pencolor("white")
    hud_pen.write(f"Score: {score}", font=("Arial", 13, "bold"))

    # speed
    hud_pen.goto(130, 320)
    hud_pen.pencolor("#ffcc00")
    hud_pen.write(f"Speed: {game_speed:.1f}", font=("Arial", 13, "bold"))

    # controls
    hud_pen.goto(-280, -355)
    hud_pen.pencolor("#aaaaaa")
    hud_pen.write("<- -> Lane   UP Speed+   DOWN Speed-   Q Quit",
                  font=("Arial", 8, "normal"))

def draw_game_over():
    hud_pen.clear()

    # overlay box
    draw_rect(hud_pen, -200, -100, 400, 200, "#000000", "#ff4444", 3)

    hud_pen.penup()
    hud_pen.goto(0, 40)
    hud_pen.pencolor("#ff4444")
    hud_pen.write("GAME OVER", align="center", font=("Arial", 28, "bold"))

    hud_pen.goto(0, 0)
    hud_pen.pencolor("white")
    hud_pen.write(f"Score: {score}", align="center", font=("Arial", 16, "bold"))

    hud_pen.goto(0, -40)
    hud_pen.pencolor("#ffcc00")
    hud_pen.write("SPACE to Restart  |  Q to Quit",
                  align="center", font=("Arial", 11, "normal"))

# ─────────────────────────────────────────────
#  GAME RESET
# ─────────────────────────────────────────────
def reset_game():
    global player_lane, game_speed, score, game_over
    global frame_count, enemy_cars, dash_offset
    player_lane = 1
    game_speed  = BASE_SPEED
    score       = 0
    game_over   = False
    frame_count = 0
    enemy_cars  = []
    dash_offset = 0
    draw_background()

# ─────────────────────────────────────────────
#  KEYBOARD HANDLERS
# ─────────────────────────────────────────────
def on_left():
    global player_lane
    if not game_over and player_lane > 0:
        player_lane -= 1

def on_right():
    global player_lane
    if not game_over and player_lane < LANE_COUNT - 1:
        player_lane += 1

def on_up():
    global game_speed
    if not game_over:
        game_speed = min(game_speed + SPEED_STEP, MAX_SPEED)

def on_down():
    global game_speed
    if not game_over:
        game_speed = max(game_speed - SPEED_STEP, MIN_SPEED)

def on_space():
    if game_over:
        reset_game()

def on_quit():
    screen.bye()

screen.listen()
screen.onkeypress(on_left,  "Left")
screen.onkeypress(on_right, "Right")
screen.onkeypress(on_up,    "Up")
screen.onkeypress(on_down,  "Down")
screen.onkeypress(on_space, "space")
screen.onkeypress(on_quit,  "q")

# ─────────────────────────────────────────────
#  SPEED AUTO-INCREASE
# ─────────────────────────────────────────────
def auto_increase_speed():
    global game_speed
    if frame_count > 0 and frame_count % 300 == 0:
        game_speed = min(game_speed + 0.3, MAX_SPEED)

# MAIN LOOP
reset_game()

while True:
    try:
        if not game_over:
            frame_count  += 1          # no global needed
            dash_offset  += game_speed # no global needed

            auto_increase_speed()

            if frame_count % max(8, SPAWN_INTERVAL - int(game_speed * 2)) == 0:
                spawn_enemy()

            update_enemies()
            cleanup_enemies()

            if check_collision():
                game_over = True

            draw_road()
            draw_enemies()
            draw_player()
            draw_hud()
        else:
            draw_game_over()

        screen.update()
        time.sleep(0.02)

    except turtle.Terminator:
        break
    except Exception:
        break
