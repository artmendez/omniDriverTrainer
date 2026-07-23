from ursina import *
import math
import random

# --- INITIALIZE URSINA APP ---
app = Ursina(title="3D Perimeter Viewer", borderless=False)
window.color = color.rgb(17, 17, 22)

# --- GAME CONSTANTS ---
LENGTH = 14.0          # Inner floor length (Z-axis)
WIDTH = 9.5            # Inner floor width (X-axis)
WALL_HEIGHT = 0.6      # Perimeter wall height
WALL_THICKNESS = 0.075 # Wall thickness
EYE_HEIGHT = 1.6       # Camera POV height

MAX_SPEED = 2.0        # Vehicle max speed (m/s)
ACCELERATION = 2.0     # Acceleration/deceleration rate (m/s²)
ROTATION_SPEED = 2.0   # Yaw rotation speed (rad/s)

CANNON_SPEED = 2.5     # Elevation speed (rad/s)
MIN_CANNON_ANGLE = 0.0 # 0 degrees
MAX_CANNON_ANGLE = math.pi / 3  # 60 degrees in radians
LAUNCH_SPEED = 7.0     # Muzzle velocity (m/s)
GRAVITY = 9.81         # Gravity acceleration (m/s²)

MIN_FOOTPRINT = WIDTH * 0.10
MAX_FOOTPRINT = WIDTH * 0.30

# --- GAME STATE ---
score = 0
remaining_bars = 6
timer_seconds = 10.0
game_active = False
is_game_over = False
sequence_started = False

vx = 0.0
vz = 0.0
cannon_angle = 0.0

active_obstacles = []
active_explosions = []
active_projectile = None

# --- CAMERA POV POSITIONS ---
camera_z = -(LENGTH / 2) - WALL_THICKNESS - 0.2
pov_positions = {
    1: Vec3(-WIDTH / 2 + (WIDTH * (1 / 3)), EYE_HEIGHT, camera_z),
    2: Vec3(-WIDTH / 2 + (WIDTH * (1 / 2)), EYE_HEIGHT, camera_z),
    3: Vec3(-WIDTH / 2 + (WIDTH * (2 / 3)), EYE_HEIGHT, camera_z)
}

def set_pov(index):
    pos = pov_positions[index]
    camera.position = pos
    camera.rotation = Vec3(0, 0, 0)
    camera.look_at(Vec3(pos.x, 0.1, 1.0))

set_pov(2)

# --- ENVIRONMENT SETUP ---
# Dark Floor
floor = Entity(
    model='plane',
    scale=(WIDTH, 1, LENGTH),
    color=color.rgb(34, 34, 38)
)

# Perimeter Walls
wall_mat_color = color.rgb(224, 224, 224)

north_wall = Entity(model='cube', scale=(WIDTH + WALL_THICKNESS * 2, WALL_HEIGHT, WALL_THICKNESS),
                    position=(0, WALL_HEIGHT / 2, (LENGTH / 2) + (WALL_THICKNESS / 2)), color=wall_mat_color)
south_wall = Entity(model='cube', scale=(WIDTH + WALL_THICKNESS * 2, WALL_HEIGHT, WALL_THICKNESS),
                    position=(0, WALL_HEIGHT / 2, -(LENGTH / 2) - (WALL_THICKNESS / 2)), color=wall_mat_color)
east_wall  = Entity(model='cube', scale=(WALL_THICKNESS, WALL_HEIGHT, LENGTH),
                    position=((WIDTH / 2) + (WALL_THICKNESS / 2), WALL_HEIGHT / 2, 0), color=wall_mat_color)
west_wall  = Entity(model='cube', scale=(WALL_THICKNESS, WALL_HEIGHT, LENGTH),
                    position=(-(WIDTH / 2) - (WALL_THICKNESS / 2), WALL_HEIGHT / 2, 0), color=wall_mat_color)

# Lights
sun_light = DirectionalLight(shadows=True)
sun_light.look_at(Vec3(5, -15, 5))
AmbientLight(color=color.rgba(180, 180, 180, 255))

# --- VEHICLE MODEL ---
vehicle_radius = 0.45
initial_z = -(LENGTH / 2) + vehicle_radius + 0.3

vehicle = Entity(model='cube', scale=(0.69, 0.3, 0.9), color=color.rgb(40, 120, 220),
                 position=(0, 0.15, initial_z))

cannon_pivot = Entity(parent=vehicle, position=(0, 0.2, 0))
cannon = Entity(parent=cannon_pivot, model=Cylinder(resolution=16), scale=(0.08, 0.35, 0.08),
                color=color.yellow, position=(0, 0, 0.175), rotation=(90, 0, 0))

# --- HUD & UI OVERLAYS ---
hud_parent = Entity(parent=camera.ui)

# Top Bar Container background
hud_bg = Entity(parent=hud_parent, model='quad', scale=(0.85, 0.08), position=(0, 0.44), color=color.rgba(0, 0, 0, 200))

# Score
score_label = Text(parent=hud_parent, text='PTS: 0', position=(-0.38, 0.455), scale=1.2, color=color.green)

# 6-Bar Life Indicator
bar_entities = []
start_bar_x = -0.18
for b in range(6):
    bar_ent = Entity(
        parent=hud_parent,
        model='quad',
        scale=(0.012, 0.04),
        position=(start_bar_x + (b * 0.018), 0.44),
        color=color.cyan
    )
    bar_entities.append(bar_ent)

# Timer
timer_label = Text(parent=hud_parent, text='10.0s', position=(-0.04, 0.455), scale=1.3, color=color.white)

# Cannon Angle Display
cannon_label = Text(parent=hud_parent, text='0.0°', position=(0.12, 0.455), scale=1.2, color=color.yellow)

# Start / Game Over Screens
start_prompt = Entity(parent=camera.ui, model='quad', scale=(0.5, 0.2), color=color.rgba(0, 0, 0, 230))
start_text = Text(parent=start_prompt, text='CLICK / PRESS ANY KEY\nTO START', origin=(0, 0), scale=1.4, color=color.cyan)

gameover_overlay = Entity(parent=camera.ui, model='quad', scale=(0.6, 0.35), color=color.rgba(20, 0, 0, 240), enabled=False)
gameover_text = Text(parent=gameover_overlay, text='GAME OVER\n\nFINAL SCORE: 0\n\n[R] PLAY AGAIN', origin=(0, 0), scale=1.4, color=color.red)

def update_bars_hud():
    for i, bar in enumerate(bar_entities):
        if i < remaining_bars:
            bar.color = color.cyan
        else:
            bar.color = color.rgb(40, 40, 50)

# --- OBSTACLE SPAWNER ---
def spawn_obstacles():
    global active_obstacles
    for obs in active_obstacles:
        destroy(obs)
    active_obstacles.clear()

    # Red Object (Shot Target) & Blue Object (Vehicle Hit Target)
    targets = [
        {'color': color.rgb(238, 34, 34), 'type': 'red'},
        {'color': color.rgb(34, 102, 255), 'type': 'blue'}
    ]

    for item in targets:
        footprint = random.uniform(MIN_FOOTPRINT, MAX_FOOTPRINT)
        height = random.uniform(0.6, 1.8)
        radius = footprint / 2.0

        shape_mesh = Cylinder(resolution=16) if random.choice([True, False]) else 'cube'
        obs = Entity(
            model=shape_mesh,
            scale=(footprint, height, footprint),
            color=item['color'],
            position=(0, height / 2, 0)
        )
        obs.userData = {'radius': radius, 'height': height, 'type': item['type'], 'hit': False}

        max_x = (WIDTH / 2) - radius
        max_z = (LENGTH / 2) - radius
        valid_pos = False
        attempts = 0

        while not valid_pos and attempts < 100:
            attempts += 1
            px = random.uniform(-max_x, max_x)
            pz = random.uniform(-max_z, max_z)

            dist_v = math.hypot(px - vehicle.x, pz - vehicle.z)
            dist_o = min([math.hypot(px - o.x, pz - o.z) for o in active_obstacles], default=999)

            if dist_v > (radius + vehicle_radius + 1.2) and dist_o > (radius + 0.8):
                valid_pos = True
                obs.position = Vec3(px, height / 2, pz)

        active_obstacles.append(obs)

# --- EXPLOSION PARTICLES ---
def create_explosion(pos):
    Audio('bounce', pitch=0.5, volume=0.8)
    for _ in range(40):
        p = Entity(
            model='sphere',
            scale=0.08,
            color=random.choice([color.yellow, color.orange, color.white, color.red]),
            position=pos
        )
        vel = Vec3(
            random.uniform(-4, 4),
            random.uniform(2, 6),
            random.uniform(-4, 4)
        )
        active_explosions.append({'mesh': p, 'vel': vel, 'life': 0.6})

def update_explosions(dt):
    for exp in active_explosions[:]:
        exp['life'] -= dt
        if exp['life'] <= 0:
            destroy(exp['mesh'])
            active_explosions.remove(exp)
            continue

        exp['vel'].y -= GRAVITY * dt
        exp['mesh'].position += exp['vel'] * dt

# --- CANNON SHOOTING ---
def fire_cannon():
    global active_projectile
    if not game_active or is_game_over or active_projectile or not cannon.visible:
        return

    Audio('laser_default', pitch=0.8, volume=0.7)
    cannon.visible = False

    world_pos = cannon.world_position
    rot_rad_y = math.radians(vehicle.rotation_y)
    rot_rad_x = cannon_angle

    # Compute velocity vector from cannon orientation
    dir_x = math.sin(rot_rad_y) * math.cos(rot_rad_x)
    dir_y = math.sin(rot_rad_x)
    dir_z = math.cos(rot_rad_y) * math.cos(rot_rad_x)
    launch_dir = Vec3(dir_x, dir_y, dir_z).normalized()

    proj = Entity(
        model=Cylinder(resolution=16),
        scale=(0.08, 0.35, 0.08),
        color=color.yellow,
        position=world_pos,
        rotation_x=math.degrees(-cannon_angle),
        rotation_y=vehicle.rotation_y
    )

    active_projectile = {
        'mesh': proj,
        'vel': launch_dir * LAUNCH_SPEED,
        'radius': 0.08
    }

def check_field_cleared():
    global timer_seconds
    if len(active_obstacles) == 0 and game_active:
        # Instant target respawn without bar loss
        timer_seconds = 10.0
        spawn_obstacles()

def update_projectile(dt):
    global active_projectile, score
    if not active_projectile:
        return

    proj = active_projectile['mesh']
    active_projectile['vel'].y -= GRAVITY * dt
    proj.position += active_projectile['vel'] * dt

    pos = proj.position
    hit = False

    # Ground hit check
    if pos.y <= 0.05:
        hit = True

    # Red Object Hit Check
    if not hit:
        for obs in active_obstacles[:]:
            if obs.userData['type'] == 'red':
                r = obs.userData['radius']
                h = obs.userData['height']
                dx = pos.x - obs.x
                dy = pos.y - obs.y
                dz = pos.z - obs.z

                if math.hypot(dx, dz) < (active_projectile['radius'] + r) and abs(dy) < (h / 2 + 0.1):
                    hit = True
                    score += 10
                    score_label.text = f'PTS: {score}'
                    create_explosion(obs.position)

                    destroy(obs)
                    active_obstacles.remove(obs)
                    check_field_cleared()
                    break

    # Bounds check
    if abs(pos.x) > WIDTH / 2 + 1.0 or abs(pos.z) > LENGTH / 2 + 1.0:
        hit = True

    if hit:
        destroy(proj)
        active_projectile = None
        cannon.visible = True

# --- GAME CONTROLS & UPDATE LOOP ---
def input(key):
    global game_active, sequence_started, cannon_angle

    if not sequence_started and not is_game_over:
        start_game_sequence()
        return

    if is_game_over and key == 'r':
        restart_game()
        return

    # POV Switching: Ctrl + 1/2/3
    if held_keys['control']:
        if key == '1': set_pov(1)
        elif key == '2': set_pov(2)
        elif key == '3': set_pov(3)

    if key == 'space':
        fire_cannon()

def start_game_sequence():
    global sequence_started, game_active
    sequence_started = True
    start_prompt.enabled = False
    spawn_obstacles()
    game_active = True

def trigger_game_over():
    global game_active, is_game_over
    game_active = False
    is_game_over = True
    gameover_text.text = f'GAME OVER\n\nFINAL SCORE: {score}\n\n[R] PLAY AGAIN'
    gameover_overlay.enabled = True

def restart_game():
    global score, remaining_bars, timer_seconds, is_game_over, sequence_started, vx, vz
    gameover_overlay.enabled = False
    score = 0
    score_label.text = 'PTS: 0'
    remaining_bars = 6
    update_bars_hud()
    timer_seconds = 10.0
    is_game_over = False
    sequence_started = False
    vx = 0.0
    vz = 0.0

    vehicle.position = (0, 0.15, initial_z)
    vehicle.rotation_y = 0

    if active_projectile:
        destroy(active_projectile['mesh'])
        globals()['active_projectile'] = None
        cannon.visible = True

    start_game_sequence()

def update():
    global vx, vz, cannon_angle, timer_seconds, remaining_bars, score

    dt = time.dt
    if not game_active or is_game_over:
        return

    # 1. Update Timer & Life Bar Removal
    timer_seconds -= dt
    if timer_seconds <= 0.0:
        remaining_bars -= 1
        update_bars_hud()
        Audio('line_miss', pitch=0.6, volume=0.9)

        if remaining_bars <= 0:
            trigger_game_over()
            return
        else:
            timer_seconds = 10.0
            spawn_obstacles()

    timer_label.text = f'{max(0.0, timer_seconds):.1f}s'

    # 2. Cannon Pitch Controls (I / K Keys)
    if held_keys['i']:
        cannon_angle += CANNON_SPEED * dt
    if held_keys['k']:
        cannon_angle -= CANNON_SPEED * dt
    cannon_angle = min(MAX_CANNON_ANGLE, max(MIN_CANNON_ANGLE, cannon_angle))
    cannon_pivot.rotation_x = math.degrees(-cannon_angle)
    cannon_label.text = f'{(math.degrees(cannon_angle)):.1f}°'

    # 3. Vehicle Driving (W/A/S/D & J/L Keys)
    if held_keys['j']: vehicle.rotation_y += math.degrees(ROTATION_SPEED * dt)
    if held_keys['l']: vehicle.rotation_y -= math.degrees(ROTATION_SPEED * dt)

    dir_x = (1 if held_keys['a'] else 0) - (1 if held_keys['d'] else 0)
    dir_z = (1 if held_keys['w'] else 0) - (1 if held_keys['s'] else 0)

    input_len = math.hypot(dir_x, dir_z)
    target_vx = (dir_x / input_len * MAX_SPEED) if input_len > 0 else 0
    target_vz = (dir_z / input_len * MAX_SPEED) if input_len > 0 else 0

    step = ACCELERATION * dt
    vx = move_towards(vx, target_vx, step)
    vz = move_towards(vz, target_vz, step)

    vehicle.x += vx * dt
    vehicle.z += vz * dt

    # Vehicle Collision with Blue Object
    for obs in active_obstacles[:]:
        if obs.userData['type'] == 'blue':
            dist = math.hypot(vehicle.x - obs.x, vehicle.z - obs.z)
            if dist < (vehicle_radius + obs.userData['radius']):
                score += 20
                score_label.text = f'PTS: {score}'
                Audio('coin1', volume=0.8)

                destroy(obs)
                active_obstacles.remove(obs)
                check_field_cleared()

    # Perimeter Wall Boundaries Collision
    max_x = (WIDTH / 2) - vehicle_radius
    max_z = (LENGTH / 2) - vehicle_radius
    vehicle.x = clamp(vehicle.x, -max_x, max_x)
    vehicle.z = clamp(vehicle.z, -max_z, max_z)

    # 4. Update Physics Engines
    update_projectile(dt)
    update_explosions(dt)

# Run the Ursina App
app.run()