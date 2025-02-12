import pygame
import sys
import heapq
import random

# Inicializar Pygame
pygame.init()
# Inicializar el mixer para manejar la música
pygame.mixer.init()
# Cargar la música de fondo
pygame.mixer.music.load("musicafondo.mp3")  # Asegúrate de que el nombre del archivo coincida
# Reproducir la música en bucle
pygame.mixer.music.play(-1)  # Reproducir en bucle (-1 para bucle infinito)
# Inicializar joystick
pygame.joystick.init()
joystick = None
if pygame.joystick.get_count() > 0:
    joystick = pygame.joystick.Joystick(0)
    joystick.init()

# Configuración de la ventana
screen_width = 1000
screen_height = 1000
screen = pygame.display.set_mode((screen_width, screen_height))
pygame.display.set_caption("Juego con A* y Árbol de Comportamiento")

# Número total de imágenes en las animaciones
PLAYER_N = 8
ENEMY_N = 6

# Cargar los sprites del personaje principal y escalarlos
player_images = [pygame.transform.scale(pygame.image.load(f"walk{i}.png").convert_alpha(),
               (100, 100)) for i in range(1, PLAYER_N + 1)]  # Tamaño aumentado a 100x100

# Cargar los sprites del enemigo y escalarlos
enemy_images = [pygame.transform.scale(pygame.image.load(f"enemy_{i}.png").convert_alpha(),
              (150, 150)) for i in range(1, ENEMY_N + 1)]  # Tamaño aumentado a 150x150

# Cargar los sprites de los obstáculos
obstacle_images = [pygame.image.load(f"obstacle{i}.png").convert_alpha() for i in range(1, 28)]

# Clase para representar los nodos del gráfico
class Node:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.g = 0
        self.h = 0
        self.f = 0
        self.parent = None

    def __lt__(self, other):
        return self.f < other.f

def astar(start, end, grid):
    open_list = []
    closed_list = set()
    heapq.heappush(open_list, (start.f, start))

    while open_list:
        _, current = heapq.heappop(open_list)
        closed_list.add((current.x, current.y))

        if current.x == end.x and current.y == end.y:
            path = []
            while current:
                path.append((current.x, current.y))
                current = current.parent
            return path[::-1]

        neighbors = get_neighbors(current, grid)
        for neighbor in neighbors:
            if (neighbor.x, neighbor.y) in closed_list:
                continue

            tentative_g = current.g + 1
            if any(open_node[1] == neighbor and tentative_g >= neighbor.g for open_node in open_list):
                continue

            neighbor.g = tentative_g
            neighbor.h = abs(neighbor.x - end.x) + abs(neighbor.y - end.y)
            neighbor.f = neighbor.g + neighbor.h
            neighbor.parent = current
            heapq.heappush(open_list, (neighbor.f, neighbor))

    return []

def get_neighbors(node, grid):
    neighbors = []
    directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
    for dx, dy in directions:
        x, y = node.x + dx, node.y + dy
        if 0 <= x < len(grid[0]) and 0 <= y < len(grid) and grid[y][x] == 0:
            neighbors.append(Node(x, y))
    return neighbors

class BehaviorTree:
    def __init__(self, root):
        self.root = root

    def run(self):
        self.root.run()

class BTNode:
    def run(self):
        pass

class Sequence(BTNode):
    def __init__(self, nodes):
        self.nodes = nodes

    def run(self):
        for node in self.nodes:
            if not node.run():
                return False
        return True

class Selector(BTNode):
    def __init__(self, nodes):
        self.nodes = nodes

    def run(self):
        for node in self.nodes:
            if node.run():
                return True
        return False

class Action(BTNode):
    def __init__(self, action):
        self.action = action

    def run(self):
        return self.action()
# Variables para la animación y movimiento
player_frame = 0
enemy_frame = 0
enemy_frame_counter = 0
clock = pygame.time.Clock()
speed = 5
ENEMY_ANIMATION_SPEED = 5

grid_width = screen_width // player_images[0].get_width()
grid_height = screen_height // player_images[0].get_height()
grid = [[0 for _ in range(grid_width)] for _ in range(grid_height)]

obstacles = []
for _ in range(27):
    while True:
        obs_x = random.randint(0, screen_width - obstacle_images[0].get_width())
        obs_y = random.randint(0, screen_height - obstacle_images[0].get_height())
        if grid[obs_y // player_images[0].get_height()][obs_x // player_images[0].get_width()] == 0:
            obstacles.append((obs_x, obs_y))
            grid[obs_y // player_images[0].get_height()][obs_x // player_images[0].get_width()] = 1
            break

player_x = screen_width - player_images[0].get_width()
player_y = screen_height - player_images[0].get_height()
enemy_x = screen_width - enemy_images[0].get_width()
enemy_y = 0
player_health = 100
start_ticks = pygame.time.get_ticks()
game_time = 45

font = pygame.font.Font(None, 36)

def mostrar_salud(health):
    health_text = font.render(f'Salud: {health}', True, (255, 0, 0))
    screen.blit(health_text, (screen_width - health_text.get_width() - 10, 10))

def mostrar_temporizador(time_left):
    timer_text = font.render(f'Tiempo: {time_left}', True, (0, 0, 0))
    screen.blit(timer_text, (10, 10))

def move_enemy_towards_player():
    global enemy_x, enemy_y
    start = Node(int(enemy_x // player_images[0].get_width()), int(enemy_y // player_images[0].get_height()))
    end = Node(int(player_x // player_images[0].get_width()), int(player_y // player_images[0].get_height()))
    path = astar(start, end, grid)
    if path and len(path) > 1:
        next_node = path[1]
        target_x = next_node[0] * player_images[0].get_width()
        target_y = next_node[1] * player_images[0].get_height()

        dx = target_x - enemy_x
        dy = target_y - enemy_y

        move_factor = 0.75

        new_enemy_x = enemy_x + dx * move_factor
        new_enemy_y = enemy_y + dy * move_factor

        if can_move_to(int(new_enemy_x), int(new_enemy_y)):
            enemy_x = new_enemy_x
            enemy_y = new_enemy_y
    return True

def attack_player():
    global player_health
    if abs(enemy_x - player_x) < player_images[0].get_width() and abs(enemy_y - player_y) < player_images[0].get_height():
        player_health -= 2
        print("Jugador atacado! Salud restante:", player_health)
        if player_health <= 0:
            mostrar_game_over()
    return True

bt = BehaviorTree(Sequence([
    Action(move_enemy_towards_player),
    Action(attack_player)
]))

def can_move_to(x, y):
    grid_x = x // player_images[0].get_width()
    grid_y = y // player_images[0].get_height()
    if 0 <= grid_x < len(grid[0]) and 0 <= grid_y < len(grid):
        return grid[grid_y][grid_x] == 0
    return False

def mostrar_game_over():
    while True:
        screen.fill((0, 0, 0))
        game_over_text = font.render("Game Over", True, (255, 0, 0))
        restart_text = font.render("Presiona R para reiniciar o Q para salir", True, (255, 255, 255))
        screen.blit(game_over_text, (screen_width // 2 - game_over_text.get_width() // 2, screen_height // 2 - game_over_text.get_height() // 2))
        screen.blit(restart_text, (screen_width // 2 - restart_text.get_width() // 2, screen_height // 2 + game_over_text.get_height() // 2))

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    main()
                elif event.key == pygame.K_q:
                    pygame.quit()
                    sys.exit()

def mostrar_ganaste():
    while True:
        screen.fill((0, 0, 0))
        ganaste_text = font.render("¡Ganaste!", True, (0, 255, 0))
        restart_text = font.render("Presiona R para reiniciar o Q para salir", True, (255, 255, 255))
        screen.blit(ganaste_text, (screen_width // 2 - ganaste_text.get_width() // 2, screen_height // 2 - ganaste_text.get_height() // 2))
        screen.blit(restart_text, (screen_width // 2 - restart_text.get_width() // 2, screen_height // 2 + ganaste_text.get_height() // 2))

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    main()
                elif event.key == pygame.K_q:
                    pygame.quit()
                    sys.exit()

def main():
    global player_x, player_y, enemy_x, enemy_y, player_health, player_frame, enemy_frame, start_ticks, enemy_frame_counter
    player_x = screen_width - player_images[0].get_width()
    player_y = screen_height - player_images[0].get_height()
    enemy_x = screen_width - enemy_images[0].get_width()
    enemy_y = 0
    player_health = 100
    player_frame = 0
    enemy_frame = 0
    start_ticks = pygame.time.get_ticks()
    enemy_frame_counter = 0

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT] and can_move_to(player_x - speed, player_y):
            player_x -= speed
            player_frame = (player_frame + 1) % PLAYER_N
        if keys[pygame.K_RIGHT] and can_move_to(player_x + speed, player_y):
            player_x += speed
            player_frame = (player_frame + 1) % PLAYER_N
        if keys[pygame.K_UP] and can_move_to(player_x, player_y - speed):
            player_y -= speed
            player_frame = (player_frame + 1) % PLAYER_N
        if keys[pygame.K_DOWN] and can_move_to(player_x, player_y + speed):
            player_y += speed
            player_frame = (player_frame + 1) % PLAYER_N

        if joystick:
            axis_x = joystick.get_axis(0)
            axis_y = joystick.get_axis(1)
            if axis_x < -0.1 and can_move_to(player_x - speed, player_y):
                player_x -= speed
                player_frame = (player_frame + 1) % PLAYER_N
            if axis_x > 0.1 and can_move_to(player_x + speed, player_y):
                player_x += speed
                player_frame = (player_frame + 1) % PLAYER_N
            if axis_y < -0.1 and can_move_to(player_x, player_y - speed):
                player_y -= speed
                player_frame = (player_frame + 1) % PLAYER_N
            if axis_y > 0.1 and can_move_to(player_x, player_y + speed):
                player_y += speed
                player_frame = (player_frame + 1) % PLAYER_N

        enemy_frame_counter += 1
        if enemy_frame_counter >= ENEMY_ANIMATION_SPEED:
            enemy_frame = (enemy_frame + 1) % ENEMY_N
            enemy_frame_counter = 0

        bt.run()

        screen.fill((255, 255, 255))
        screen.blit(player_images[player_frame], (player_x, player_y))
        screen.blit(enemy_images[enemy_frame], (enemy_x, enemy_y))

        for i, (obs_x, obs_y) in enumerate(obstacles):
            screen.blit(obstacle_images[i % len(obstacle_images)], (obs_x, obs_y))

        mostrar_salud(player_health)

        seconds = (pygame.time.get_ticks() - start_ticks) / 1000
        time_left = game_time - int(seconds)
        mostrar_temporizador(time_left)

        if time_left <= 0:
            mostrar_ganaste()

        pygame.display.flip()
        clock.tick(30)

main()
