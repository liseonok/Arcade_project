import math
import random

import arcade
from arcade import SpriteList
from arcade.gui import UIManager, UITextureButton, UILabel
from arcade.gui.widgets.layout import UIAnchorLayout, UIBoxLayout

SLOT_SIZE = 64
SLOT_MARGIN = 10
INVENTORY_Y = 50
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 1200
# Константы карты
TILE_SIZE = 32
MAP_WIDTH = 96  # 96 тайлов в ширину
MAP_HEIGHT = 96  # 96 тайлов в высоту
WORLD_WIDTH = MAP_WIDTH * TILE_SIZE  # 3072 пикселя
WORLD_HEIGHT = MAP_HEIGHT * TILE_SIZE  # 3072 пикселя
CAMERA_SPEED = 0.1
CAMERA_LERP = 0.12

MAX_ITEMS_ON_MAP = 100  # Максимум предметов на всей карте
ITEM_SPAWN_RATE = 0.05  # Шанс появления предмета за кадр
PICKUP_DISTANCE = 60
MIN_ITEMS_PER_CHUNK = 1  # Минимум предметов в чанке
MAX_ITEMS_PER_CHUNK = 5  # Максимум предметов в чанке
LEVEL = 1
TILE_SCALING = 2

class BackgroundSprite(arcade.Sprite):

    def __init__(self, texture_path, window):
        super().__init__(texture_path)
        self.window = window
        self.update_size()

    def update_size(self):
        self.width = self.window.width
        self.height = self.window.height
        self.center_x = self.window.width // 2
        self.center_y = self.window.height // 2


class StartMenu(arcade.View):

    def __init__(self):
        super().__init__()
        self.background_menu = BackgroundSprite("images/interface/background_menu.jpg", self.window)
        self.background = SpriteList()
        self.background.append(self.background_menu)

        self.manager = UIManager()
        self.manager.enable()
        self.anchor_layout = UIAnchorLayout()
        self.box_layout = UIBoxLayout(vertical=True, space_between=20)
        self.setup_widgets()
        self.anchor_layout.add(self.box_layout)
        self.manager.add(self.anchor_layout)

    def on_resize(self, width, height):
        if self.background:
            self.background_menu.update_size()

    def on_draw(self):
        self.clear()
        if self.background:
            self.background.draw()

        self.manager.draw()

    def setup_widgets(self):
        text = UILabel(text="ᗣᖇᙅᗣᙏᗣZᙓ", font_size=80, text_color=arcade.color.WHITE, width=300,
                       align="center")
        self.box_layout.add(text)
        texture_normal = arcade.load_texture("images/interface/start_game_button_2.jpg")
        texture_button = UITextureButton(texture=texture_normal, width=300, height=150)
        texture_button.on_click = self.button_press
        self.box_layout.add(texture_button)

    def button_press(self, *args, **kwargs):
        game_view = Game()
        self.window.show_view(game_view)
        return


class Character:
    def __init__(self, name, hp, damage, defense, speed, x, y, picture):
        self.name = name
        self.hp = hp
        self.damage = damage
        self.defence = defense
        self.picture = picture
        self.speed = speed
        self.x = x
        self.y = y

class Mobs:
    def __init__(self, name, hp, damage, speed, x, y, picture, type="good"):
        global LEVEL
        self.name = name
        self.hp = hp
        self.damage = damage
        self.speed = speed
        self.x = x
        self.y = y
        self.texture = picture
        self.type = type
        self.max_hp = hp

        self.state = "idle"  # idle, patrol, chase, flee, attack, return
        self.target_x = x
        self.target_y = y
        self.home_x = x  # Дом/спавн точка
        self.home_y = y
        self.angle = 0  # Направление взгляда

        self.detection_range = 300  # Дистанция обнаружения игрока
        self.attack_range = 50  # Дистанция атаки
        self.flee_range = 200  # Дистанция для бегства
        self.patrol_range = 150  # Радиус патрулирования

        self.state_timer = 0
        self.attack_cooldown = 0
        self.idle_time = random.uniform(1, 3)

        self.patrol_points = []
        self.current_patrol_point = 0
        self.generate_patrol_points()

        # Для нейтральных мобов
        self.was_attacked = False
        self.aggression_timer = 0

        # Визуальные эффекты
        self.hit_timer = 0
        self.is_hit = False

        # Размер для коллизий
        self.radius = 20



        if self.type == "good":
            self.STATE_IDLE = 0  # Стоит на месте
            self.STATE_WALKING = 1  # Идет
            self.STATE_WAITING = 2  # Короткая пауза

            self.state_timer = 0
            self.idle_time = random.uniform(1, 3)  # Время бездействия
            self.walk_time = random.uniform(3, 7)  # Время ходьбы
            self.wait_time = random.uniform(0.5, 2)  # Время ожидания
            self.walk_direction = None
            self.walk_speed = 2

    def generate_patrol_points(self):
        if self.type == "good":
            return

        num_points = random.randint(3, 5)
        self.patrol_points = []

        for i in range(num_points):
            angle = (i / num_points) * 2 * math.pi
            distance = random.uniform(self.patrol_range * 0.5, self.patrol_range)

            px = self.home_x + math.cos(angle) * distance
            py = self.home_y + math.sin(angle) * distance

            self.patrol_points.append((px, py))

        if self.patrol_points:
            self.target_x, self.target_y = self.patrol_points[0]

    def update(self, delta_time, player_x, player_y, walls=None):

        self.state_timer -= delta_time
        self.attack_cooldown -= delta_time
        self.hit_timer -= delta_time

        if self.hit_timer <= 0:
            self.is_hit = False

        if self.type == "aggressive":
            self.update_aggressive(delta_time, player_x, player_y, walls)
        elif self.type == "good":
            self.update_good(delta_time, player_x, player_y, walls)

        self.move_towards_target(delta_time, walls)

        dx = self.target_x - self.x
        dy = self.target_y - self.y
        if dx != 0 or dy != 0:
            self.angle = math.degrees(math.atan2(dy, dx))

    def update_aggressive(self, delta_time, player_x, player_y, walls):
        distance_to_player = math.sqrt((self.x - player_x) ** 2 + (self.y - player_y) ** 2)

        if distance_to_player <= self.detection_range:
            if distance_to_player <= self.attack_range:
                self.state = "attack"
                self.attack_player(player_x, player_y)
            else:
                self.state = "chase"
                self.target_x = player_x
                self.target_y = player_y
        else:

            if self.state != "patrol" and self.state != "idle":
                self.state = "return"
                self.target_x = self.home_x
                self.target_y = self.home_y

            if self.state == "return":
                distance_home = math.sqrt((self.x - self.home_x) ** 2 + (self.y - self.home_y) ** 2)
                if distance_home < 10:
                    self.state = "idle"
                    self.state_timer = self.idle_time
            if self.state == "idle" and self.state_timer <= 0:
                self.state = "patrol"
                self.set_next_patrol_point()

            if self.state == "patrol":
                distance_target = math.sqrt((self.x - self.target_x) ** 2 + (self.y - self.target_y) ** 2)
                if distance_target < 10:
                    self.set_next_patrol_point()

    def update_good(self, delta_time, player_x, player_y, walls):
        distance_to_player = math.sqrt((self.x - player_x) ** 2 + (self.y - player_y) ** 2)

        if distance_to_player < 100:
            self.state = "flee"
            dx = self.x - player_x
            dy = self.y - player_y
            length = math.sqrt(dx * dx + dy * dy)
            if length > 0:
                dx /= length
                dy /= length

            self.target_x = self.x + dx * 50
            self.target_y = self.y + dy * 50
        else:
            self.state = "return"
            self.target_x = self.home_x
            self.target_y = self.home_y

    def set_next_patrol_point(self):
        if not self.patrol_points:
            return

        self.current_patrol_point = (self.current_patrol_point + 1) % len(self.patrol_points)
        self.target_x, self.target_y = self.patrol_points[self.current_patrol_point]

    def move_towards_target(self, delta_time, walls):
        dx = self.target_x - self.x
        dy = self.target_y - self.y
        distance = math.sqrt(dx * dx + dy * dy)

        if distance > 0:
            dx /= distance
            dy /= distance

            move_distance = min(distance, self.speed * delta_time * 60)  # *60 для FPS 60

            new_x = self.x + dx * move_distance
            new_y = self.y + dy * move_distance

            if walls and self.check_collision_with_walls(new_x, new_y, walls):
                if abs(dx) > abs(dy):
                    if not self.check_collision_with_walls(self.x, new_y, walls):
                        self.y = new_y
                    elif not self.check_collision_with_walls(new_x, self.y, walls):
                        self.x = new_x
                else:
                    if not self.check_collision_with_walls(new_x, self.y, walls):
                        self.x = new_x
                    elif not self.check_collision_with_walls(self.x, new_y, walls):
                        self.y = new_y
            else:
                self.x = new_x
                self.y = new_y

    def check_collision_with_walls(self, x, y, walls):
        if callable(walls):
            return not walls(x, y, self.radius)
        elif isinstance(walls, list):
            for wall in walls:
                if hasattr(wall, 'collides_with'):
                    if wall.collides_with(x, y, self.radius):
                        return True
        return False

    def attack_player(self, player_x, player_y):
        if self.attack_cooldown <= 0:
            self.attack_cooldown = 1.0
            return self.damage
        return 0

    def take_damage(self, damage):
        self.hp -= damage
        self.is_hit = True
        self.hit_timer = 0.3

        if self.hp <= 0:
            return True
        return False

    def draw(self, camera_x=0, camera_y=0):
        if self.hp < self.max_hp:
            hp_percent = self.hp / self.max_hp
            hp_width = self.radius * 2 * hp_percent
            arcade.draw_rect_filled(arcade.LBWH(SCREEN_WIDTH, SCREEN_HEIGHT + self.radius + 10,
                                         self.radius * 2, 6), arcade.color.BLACK)
            hp_color = arcade.color.GREEN
            if hp_percent < 0.5:
                hp_color = arcade.color.YELLOW
            if hp_percent < 0.25:
                hp_color = arcade.color.RED

            arcade.draw_rect_filled(arcade.LBWH(SCREEN_WIDTH - self.radius + hp_width / 2,
                                         SCREEN_HEIGHT + self.radius + 10,
                                         hp_width, 4), hp_color)


class Item:  # предмет класс
    def __init__(self, name, item_type, texture, quantity=1, heal=0, damage=0, defence=0):
        self.name = name
        self.type = item_type
        self.texture = texture
        self.quantity = quantity
        self.heal = heal
        self.damage = damage
        self.defence = defence

        self.x = 0
        self.y = 0
        self.world_x = 0  # Глобальные координаты на карте
        self.world_y = 0

    def draw(self, camera_x, camera_y):
        screen_x = self.world_x - camera_x
        screen_y = self.world_y - camera_y

        if (-SLOT_SIZE <= screen_x <= SCREEN_WIDTH + SLOT_SIZE and
                -SLOT_SIZE <= screen_y <= SCREEN_HEIGHT + SLOT_SIZE):

            arcade.draw_texture_rect(self.texture, arcade.LBWH(screen_x, screen_y, SLOT_SIZE - 10, SLOT_SIZE - 10))

            if self.quantity > 1:
                arcade.draw_text(f"{self.quantity}", screen_x + 15, screen_y - 25,
                                 arcade.color.WHITE, 14, bold=True)

    def set_position(self, world_x, world_y):
        self.world_x = world_x
        self.world_y = world_y
        self.x = world_x
        self.y = world_y


# class Camera:  # камера
#
#     def __init__(self):
#         self.x = 0
#         self.y = 0
#         self.target_x = 0
#         self.target_y = 0
#
#     def update(self, player_x, player_y):
#         # Плавное движение камеры к игроку
#         self.target_x = player_x - SCREEN_WIDTH // 2
#         self.target_y = player_y - SCREEN_HEIGHT // 2
#
#         self.target_x = max(0, min(self.target_x, WORLD_WIDTH - SCREEN_WIDTH))
#         self.target_y = max(0, min(self.target_y, WORLD_HEIGHT - SCREEN_HEIGHT))
#
#         self.x += (self.target_x - self.x) * CAMERA_SPEED
#         self.y += (self.target_y - self.y) * CAMERA_SPEED
#
#     def get_screen_position(self, world_x, world_y):
#         return world_x - self.x, world_y - self.y
#
#     def get_world_position(self, screen_x, screen_y):
#         return screen_x + self.x, screen_y + self.y


class Game(arcade.View):
    def __init__(self):
        super().__init__()

        self.world_width = 96 * TILE_SIZE * TILE_SCALING
        self.world_height = 96 * TILE_SIZE * TILE_SCALING

        self.screen_width = self.window.width
        self.screen_height = self.window.height
        self.DEAD_ZONE_W = int(self.screen_width * 0.01)
        self.DEAD_ZONE_H = int(self.screen_height * 0.01)

        self.gamer = Character(name='Игрок', hp=100, damage=2, defense=0, picture=arcade.Sprite(":resources:images/animated_characters/female_person/femalePerson_idle.png", scale=0.5), speed=5, x=self.world_width//2, y=self.world_height//2)
        self.camera = arcade.Camera2D()
        self.camera.position = (self.gamer.x, self.gamer.y)

        self.inventory_slots = 4
        self.inventory = [None] * self.inventory_slots
        self.selected_slot = 0
        self.slot_color = arcade.color.GRAY
        self.selected_slot_color = arcade.color.GOLD
        self.mobs = []

        self.player_list = arcade.SpriteList()
        self.wall_list = arcade.SpriteList()
        self.floor_list = arcade.SpriteList()
        self.pos1 = arcade.SpriteList()
        self.pos2 = arcade.SpriteList()
        self.pos3 = arcade.SpriteList()

        map_name = "map_arcamaze7.tmx"
        try:
            tile_map = arcade.load_tilemap(map_name, scaling=TILE_SCALING)
            print(tile_map)
            if tile_map is None:
                raise ValueError("Не удалось загрузить карту")
        except Exception as e:
            print(f"Ошибка загрузки карты: {e}")
            print("Проблема с картой или тайлсетами.")
            return

        self.wall_list = tile_map.sprite_lists["walls"]
        self.collision_list = tile_map.sprite_lists["collisions"]
        self.floor_list = tile_map.sprite_lists["floor"]
        self.pos1 = tile_map.sprite_lists["plants and else"]
        self.pos2 = tile_map.sprite_lists["plants and else2"]
        self.pos3 = tile_map.sprite_lists["plants and else3"]

        self.player_sprite = self.gamer.picture
        self.player_sprite.center_x = self.gamer.x
        self.player_sprite.center_y = self.gamer.y
        self.player_list.append(self.player_sprite)

        self.physics_engine = arcade.PhysicsEngineSimple(
            self.player_sprite,
            self.collision_list
        )

        self.total_mobs_to_spawn = 20  # Общее количество мобов на карте
        self.mob_spawn_rate = 0.02  # Шанс спавна моба за кадр
        self.min_mob_distance_from_player = 200  # Минимальное расстояние от игрока
        self.max_spawn_attempts = 50  # Максимальное количество попыток спавна
        self.mob_database = self.create_mob_database()
        self.mobs = []
        # self.spawn_initial_mobs(10)

        self.item_database = self.create_item_database()
        self.items_on_map = []
        self.item_to_pickup = None
        self.can_pick_up = False

        self.move_up = False
        self.move_down = False
        self.move_left = False
        self.move_right = False

        self.chunk_size = 256
        self.chunks_initialized = set()

        # self.generate_items_for_all_chunks()

        self.distance_traveled = 0
        self.last_x = self.gamer.x
        self.last_y = self.gamer.y

    def create_item_database(self):
        return [{"name": "Меч", "type": "weapon", "texture": arcade.Sprite("images/things/thing_sword.jpg"), "min_qty": 1, "max_qty": 1,
                 "damage": 5, "heal": 0, "defence": 0},
                {"name": "Нож", "type": "weapon", "texture": arcade.Sprite("images/things/thing_knife.jpg"), "min_qty": 1, "max_qty": 2,
                 "damage": 3, "heal": 0, "defence": 0},
                {"name": "Щит", "type": "defense", "texture": arcade.Sprite("images/things/thing_shield.jpg"), "min_qty": 0, "max_qty": 1,
                 "defence": 5, "heal": 0, "damage": 0},
                {"name": "Каменный молоток", "type": "weapon", "texture": arcade.Sprite("images/things/thing_stone_molotok.jpg"), "min_qty": 0, "max_qty": 2,
                 "damage": 4, "heal": 0, "defence": 0},
                {"name": "Железный молоток", "type": "weapon", "texture": arcade.Sprite("images/things/thing_iron_molotok.jpg"), "min_qty": 0, "max_qty": 1,
                 "damage": 6, "heal": 0, "defence": 0},
                {"name": "Топор", "type": "weapon", "texture": arcade.Sprite("images/things/thing_axe.jpg"), "min_qty": 0, "max_qty": 1,
                 "damage": 10, "heal": 0, "defence": 0},
                {"name": "Картофель", "type": "food", "texture": arcade.Sprite("images/food/food_potato.jpg"), "min_qty": 2, "max_qty": 5,
                 "heal": 4, "defence": 0, "damage": 0},
                {"name": "Ягоды", "type": "food", "texture": arcade.Sprite("images/food/food_berries.jpg"), "min_qty": 5, "max_qty": 8,
                 "heal": 2, "defence": 0, "damage": 0},
                {"name": "Яблоко", "type": "food", "texture": arcade.Sprite("images/food/food_apple.jpg"), "min_qty": 2, "max_qty": 5,
                 "heal": 3, "defence": 0, "damage": 0},
                {"name": "Растение", "type": "food", "texture": arcade.Sprite("images/food/food_grass.jpg"), "min_qty": 10, "max_qty": 15,
                 "heal": 1, "defence": 0, "damage": 0},
                {"name": "Тухлое мясо", "type": "food", "texture": arcade.Sprite("images/food/food_bad_meat.jpg"), "min_qty": 6, "max_qty": 8,
                 "heal": random.randint(-10, 3), "defence": 0, "damage": 0},
                {"name": "Мясо", "type": "food", "texture": arcade.Sprite("images/food/food_meet.jpg"), "min_qty": 0, "max_qty": 1,
                 "heal": 10, "defence": 0, "damage": 0},
                {"name": "Рыба", "type": "food", "texture": arcade.Sprite("images/food/food_fish.jpg"), "min_qty": 0, "max_qty": 1,
                 "heal": 10, "defence": 0, "damage": 0},
                ]

    def create_mob_database(self):
        return [{"name": "Овечка", "hp": 50, "damage": 0, "speed": 10, "texture": arcade.Sprite("images/characters/img.png"), "type": "good"},
                {"name": "Рогач", "hp": 80, "damage": 0, "speed": 30, "texture": arcade.Sprite("images/characters/img.png"), "type": "good"},
                {"name": "Падальщик", "hp": 110, "damage": 0, "speed": 50, "texture": arcade.Sprite("images/characters/img.png"), "type": "agressive"},
                {"name": "Краб", "hp": 200, "damage": 0, "speed": 70, "texture": arcade.Sprite("images/characters/img.png"), "type": "agressive"},
                {"name": "Робот", "hp": 400, "damage": 0, "speed": 90, "texture": arcade.Sprite("images/characters/img.png"), "type": "agressive"}]

    # def spawn_initial_mobs(self, count):
    #     for _ in range(count):
    #         if len(self.mobs) >= self.total_mobs_to_spawn:
    #             break
    #         self.spawn_random_mob()
    #
    # def spawn_random_mob(self, max_attempts=50):
    #     for attempt in range(max_attempts):
    #         mob_data = random.choice(self.mob_database)
    #         x, y = self.find_free_spawn_position()
    #
    #         if x is not None and y is not None:
    #             mob = Mobs(
    #                 name=mob_data["name"],
    #                 hp=mob_data["hp"],
    #                 damage=mob_data["damage"],
    #                 speed=mob_data["speed"],
    #                 x=x,
    #                 y=y,
    #                 picture=mob_data["texture"],
    #                 type=mob_data["type"]
    #             )
    #
    #             too_close_to_other_mob = False
    #             for existing_mob in self.mobs:
    #                 distance = math.sqrt((x - existing_mob.x) ** 2 + (y - existing_mob.y) ** 2)
    #                 if distance < 100:
    #                     too_close_to_other_mob = True
    #                     break
    #
    #             if not too_close_to_other_mob:
    #                 self.mobs.append(mob)
    #                 return True
    #     return False
    #
    # def find_free_spawn_position(self):
    #     attempts = 0
    #     max_attempts = 100
    #
    #     while attempts < max_attempts:
    #         x = random.randint(100, WORLD_WIDTH - 100)
    #         y = random.randint(100, WORLD_HEIGHT - 100)
    #
    #         distance_to_player = math.sqrt((x - self.gamer.x) ** 2 + (y - self.gamer.y) ** 2)
    #         if distance_to_player < self.min_mob_distance_from_player:
    #             attempts += 1
    #             continue
    #
    #         if hasattr(self, 'is_position_free') and callable(self.is_position_free):
    #             if not self.is_position_free(world_x=x, world_y=y, radius=30):
    #                 attempts += 1
    #                 continue
    #         return x, y
    #
    #     return None, None
    #
    #
    # def generate_items_for_all_chunks(self):
    #     chunks_x = WORLD_WIDTH // self.chunk_size + 1
    #     chunks_y = WORLD_HEIGHT // self.chunk_size + 1
    #
    #     for chunk_x in range(chunks_x):
    #         for chunk_y in range(chunks_y):
    #             if len(self.items_on_map) >= MAX_ITEMS_ON_MAP:
    #                 return
    #             self.generate_items_for_chunk(chunk_x, chunk_y)
    #
    # def generate_items_for_chunk(self, chunk_x, chunk_y):
    #     chunk_key = (chunk_x, chunk_y)
    #     if chunk_key in self.chunks_initialized:
    #         return
    #
    #     self.chunks_initialized.add(chunk_key)
    #
    #     num_items = random.randint(MIN_ITEMS_PER_CHUNK, MAX_ITEMS_PER_CHUNK)
    #
    #     chunk_world_x = chunk_x * self.chunk_size
    #     chunk_world_y = chunk_y * self.chunk_size
    #
    #     items_spawned = 0
    #     attempts = 0
    #     max_total_attempts = num_items * 10
    #
    #     while items_spawned < num_items and attempts < max_total_attempts:
    #         if len(self.items_on_map) >= MAX_ITEMS_ON_MAP:
    #             break
    #
    #         item_x, item_y = self.find_free_position(chunk_world_x, chunk_world_y)
    #
    #         if item_x is not None and item_y is not None:
    #             item = self.generate_random_item()
    #             if item:
    #                 item.set_position(item_x, item_y)
    #                 self.items_on_map.append(item)
    #                 items_spawned += 1
    #
    #         attempts += 1
    #
    # def generate_random_item(self):
    #     if not self.item_database:
    #         return None
    #
    #     item_data = random.choice(self.item_database)
    #     quantity = random.randint(item_data["min_qty"], item_data["max_qty"])
    #
    #     item = Item(
    #         name=item_data["name"],
    #         item_type=item_data["type"],
    #         texture=item_data["texture"],
    #         quantity=quantity,
    #         heal=item_data["heal"],
    #         defence=item_data["defence"],
    #         damage=item_data["damage"],
    #     )
    #
    #     return item
    #
    # def get_chunk_coords(self, world_x, world_y):
    #     chunk_x = int(world_x // self.chunk_size)
    #     chunk_y = int(world_y // self.chunk_size)
    #     return chunk_x, chunk_y
    #
    # def is_position_free(self, world_x, world_y, radius=16):
    #     tile_x = int(world_x // TILE_SIZE)
    #     tile_y = int(world_y // TILE_SIZE)
    #
    #     if not (0 <= tile_x < MAP_WIDTH and 0 <= tile_y < MAP_HEIGHT):
    #         return False
    #
    #     if self.collision_list[tile_y][tile_x] == 0:
    #         return False
    #
    #     check_radius = max(1, int(radius // TILE_SIZE))
    #
    #     for dx in range(-check_radius, check_radius + 1):
    #         for dy in range(-check_radius, check_radius + 1):
    #             check_x = tile_x + dx
    #             check_y = tile_y + dy
    #
    #             if 0 <= check_x < MAP_WIDTH and 0 <= check_y < MAP_HEIGHT:
    #                 if self.collision_list[check_y][check_x] == 1:
    #
    #                     dist_x = abs(world_x - (check_x * TILE_SIZE + TILE_SIZE // 2))
    #                     dist_y = abs(world_y - (check_y * TILE_SIZE + TILE_SIZE // 2))
    #
    #                     if dist_x < radius and dist_y < radius:
    #                         return False
    #
    #     return True
    #
    # def find_free_position(self, chunk_world_x, chunk_world_y, max_attempts=20):
    #     for attempt in range(max_attempts):
    #         item_x = chunk_world_x + random.randint(50, self.chunk_size - 50)
    #         item_y = chunk_world_y + random.randint(50, self.chunk_size - 50)
    #
    #         item_x = max(50, min(item_x, WORLD_WIDTH - 50))
    #         item_y = max(50, min(item_y, WORLD_HEIGHT - 50))
    #
    #         if self.is_position_free(item_x, item_y):
    #             return item_x, item_y
    #
    #     return None, None

    def on_key_press(self, key, modifiers):
        if arcade.key.KEY_1 <= key <= arcade.key.KEY_4:
            slot_index = key - arcade.key.KEY_1
            if slot_index < self.inventory_slots:
                self.selected_slot = slot_index

        elif key == arcade.key.Q:
            if self.inventory[self.selected_slot] is not None:
                drop_x = self.gamer.x + 50
                drop_y = self.gamer.y + 50
                self.item_on_ground = self.inventory[self.selected_slot]
                self.item_on_ground_pos = (drop_x, drop_y)
                self.inventory[self.selected_slot] = None

        elif key == arcade.key.F:
            if self.can_pick_up and self.item_on_ground is not None:
                for i in range(self.inventory_slots):
                    if self.inventory[i] is None:
                        self.inventory[i] = self.item_on_ground
                        self.gamer.defence += self.inventory[i].defence
                        self.gamer.damage += self.inventory[i].damage
                        self.gamer.hp += self.inventory[i].heal
                        self.item_on_ground = None
                        self.can_pick_up = False


        elif key == arcade.key.W:
            self.move_up = True
        elif key == arcade.key.S:
            self.move_down = True
        elif key == arcade.key.A:
            self.move_left = True
        elif key == arcade.key.D:
            self.move_right = True

            # Стрелки
        elif key == arcade.key.UP:
            self.move_up = True
        elif key == arcade.key.DOWN:
            self.move_down = True
        elif key == arcade.key.LEFT:
            self.move_left = True
        elif key == arcade.key.RIGHT:
            self.move_right = True

    def on_key_release(self, key, modifiers):
        if key == arcade.key.W:
            self.move_up = False
        elif key == arcade.key.S:
            self.move_down = False
        elif key == arcade.key.A:
            self.move_left = False
        elif key == arcade.key.D:
            self.move_right = False
        elif key == arcade.key.UP:
            self.move_up = False
        elif key == arcade.key.DOWN:
            self.move_down = False
        elif key == arcade.key.LEFT:
            self.move_left = False
        elif key == arcade.key.RIGHT:
            self.move_right = False

    # def on_mouse_press(self, x: int, y: int, button: int, modifiers: int) -> bool | None:
    #     if button == arcade.MOUSE_BUTTON_RIGHT:
    #         if self.inventory[self.selected_slot] is not None and self.inventory[self.selected_slot].type == "food":
    #             self.gamer.hp += self.inventory[self.selected_slot].heal
    #
    #
    def draw_inventory(self):   # инвентарь

        SLOT_SIZE = 64
        SLOT_MARGIN = 10
        INVENTORY_Y = 50

        total_width = self.inventory_slots * SLOT_SIZE + (self.inventory_slots - 1) * SLOT_MARGIN
        start_x = (self.window.width - total_width) // 2
        arcade.draw_rect_filled(
            arcade.LBWH(self.window.width // 2,
            INVENTORY_Y + SLOT_SIZE // 2,
            total_width + 20,
            SLOT_SIZE + 20),
            (0, 0, 0, 150)
        )

        for i in range(self.inventory_slots):
            x = start_x + i * (SLOT_SIZE + SLOT_MARGIN) + SLOT_SIZE // 2
            y = INVENTORY_Y + SLOT_SIZE // 2
            if i == self.selected_slot:
                color = self.selected_slot_color
            else:
                color = self.slot_color
            arcade.draw_rect_outline(arcade.LBWH(x, y, SLOT_SIZE, SLOT_SIZE), color, 3)

            arcade.draw_rect_outline(
                arcade.LBWH(x, y,
                SLOT_SIZE, SLOT_SIZE),
                color, 3
            )

            if self.inventory[i] is not None:
                arcade.draw_texture_rect(self.inventory[i].texture, arcade.LBWH(x, y, SLOT_SIZE - 8, SLOT_SIZE - 8),)

            arcade.draw_text(
                str(i + 1),
                x - SLOT_SIZE // 2 + 5,
                y + SLOT_SIZE // 2 - 20,
                arcade.color.WHITE, 14
            )

    def draw_help(self):
        arcade.Text(f"Пройдено: {int(self.distance_traveled)} px",
                         10, self.window.height - 140, arcade.color.LIGHT_GREEN, 14)

        arcade.Text(f"Собрано частиц {6}/5)",
                         10, self.window.height - 170, arcade.color.LIGHT_GREEN, 14)
    #
    #     if self.can_pick_up and self.item_on_ground:
    #         arcade.draw_text("Нажмите F чтобы поднять предмет",
    #                          self.window.width // 2, self.window.height - 100,
    #                          arcade.color.YELLOW, 16, anchor_x="center")

    def on_show(self):
        pass


    def on_update(self, delta_time: float) -> bool | None:
        self.player_sprite.change_x = 0
        self.player_sprite.change_y = 0

        speed = self.gamer.speed

        if self.move_up:
            self.player_sprite.change_y = speed
        if self.move_down:
            self.player_sprite.change_y = -speed
        if self.move_left:
            self.player_sprite.change_x = -speed
        if self.move_right:
            self.player_sprite.change_x = speed

        if self.player_sprite.change_x != 0 and self.player_sprite.change_y != 0:
            self.player_sprite.change_x *= 0.7071
            self.player_sprite.change_y *= 0.7071

        self.physics_engine.update()

        self.gamer.x = self.player_sprite.center_x
        self.gamer.y = self.player_sprite.center_y

        self.gamer.x = max(50, min(self.gamer.x, self.world_width - 50))
        self.gamer.y = max(50, min(self.gamer.y, self.world_height - 50))
        self.player_sprite.center_x = self.gamer.x
        self.player_sprite.center_y = self.gamer.y
        # position = (
        #     self.gamer.x,
        #     self.gamer.y
        # )
        #
        # self.camera.position = arcade.math.lerp_2d(self.camera.position, position, 0.12)

        cam_x, cam_y = self.camera.position
        dz_left = cam_x - self.DEAD_ZONE_W // 2
        dz_right = cam_x + self.DEAD_ZONE_W // 2
        dz_bottom = cam_y - self.DEAD_ZONE_H // 2
        dz_top = cam_y + self.DEAD_ZONE_H // 2

        px, py = self.gamer.x, self.gamer.y
        target_x, target_y = cam_x, cam_y

        if px < dz_left:
            target_x = px + self.DEAD_ZONE_W // 2
        elif px > dz_right:
            target_x = px - self.DEAD_ZONE_W // 2
        if py < dz_bottom:
            target_y = py + self.DEAD_ZONE_H // 2
        elif py > dz_top:
            target_y = py - self.DEAD_ZONE_H // 2

        # Не показываем «пустоту» за краями карты
        half_w = self.camera.viewport_width / 2
        half_h = self.camera.viewport_height / 2
        target_x = max(half_w, min(self.world_width - half_w, target_x))
        target_y = max(half_h, min(self.world_height - half_h, target_y))

        # Плавно к цели, аналог arcade.math.lerp_2d, но руками
        smooth_x = (1 - CAMERA_LERP) * cam_x + CAMERA_LERP * target_x
        smooth_y = (1 - CAMERA_LERP) * cam_y + CAMERA_LERP * target_y
        self.cam_target = (smooth_x, smooth_y)

        self.camera.position = (self.cam_target[0], self.cam_target[1])
        # if self.item_on_ground:
        #     item_x, item_y = self.item_on_ground_pos
        #     distance = math.sqrt((self.gamer.x - item_x) ** 2 + (self.gamer.y - item_y) ** 2)
        #     self.can_pick_up = distance < 80
        #
        # for mob in self.mobs[:]:
        #     mob.update(delta_time, self.gamer.x, self.gamer.y, self.is_position_free)
        #
        #     if mob.hp <= 0:
        #         self.mobs.remove(mob)

    # def update_player(self):
    #     dx = 0
    #     dy = 0
    #
    #     if self.move_up:
    #         dy += self.gamer.speed
    #     if self.move_down:
    #         dy -= self.gamer.speed
    #     if self.move_left:
    #         dx -= self.gamer.speed
    #     if self.move_right:
    #         dx += self.gamer.speed
    #
    #     if dx != 0 and dy != 0:
    #         dx *= 0.7071  # 1/√2
    #         dy *= 0.7071
    #
    #     self.gamer.x += dx
    #     self.gamer.y += dy
    #
    #     self.distance_traveled += math.sqrt((self.gamer.x - self.last_x) ** 2 +
    #                                         (self.gamer.y - self.last_y) ** 2)
    #     self.last_x = self.gamer.x
    #     self.last_y = self.gamer.y
    #
    #     self.gamer.x = max(10, min(self.window.width - 10, self.gamer.x))
    #     self.gamer.y = max(10 + INVENTORY_Y + SLOT_SIZE,
    #                        min(self.window.height - 10, self.gamer.y))

    def on_draw(self):
        self.clear()

        self.camera.use()
        self.floor_list.draw()
        self.wall_list.draw()
        self.pos1.draw()
        self.pos2.draw()
        self.pos3.draw()
        self.player_list.draw()

        self.window.use()

        self.draw_inventory()
        # arcade.draw_rect_filled(arcade.LBWH(SCREEN_WIDTH // 2, INVENTORY_Y + SLOT_SIZE // 2,
        #                                     SCREEN_WIDTH, SLOT_SIZE + 20), arcade.color.DARK_GRAY)

        # self.draw_help()

        # view_left = self.camera.x - 200
        # view_right = self.camera.x + SCREEN_WIDTH + 200
        # view_bottom = self.camera.y - 200
        # view_top = self.camera.y + SCREEN_HEIGHT + 200

        # for item in self.items_on_map:
        #     if (view_left <= item.world_x <= view_right and
        #             view_bottom <= item.world_y <= view_top):
        #
        #         if item == self.item_to_pickup:
        #             screen_x, screen_y = self.camera.get_screen_position(item.world_x, item.world_y)
        #             arcade.draw_rect_outline(arcade.LBWH(screen_x, screen_y, SLOT_SIZE, SLOT_SIZE),
        #                                      arcade.color.YELLOW, 2)
        #
        #         item.draw(self.camera.x, self.camera.y)


window = arcade.Window(resizable=True, title='ᗣᖇᙅᗣᙏᗣZᙓ')
menu_view = StartMenu()
window.show_view(menu_view)
arcade.run()
