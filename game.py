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

MAX_ITEMS_ON_MAP = 100  # Максимум предметов на всей карте
ITEM_SPAWN_RATE = 0.05  # Шанс появления предмета за кадр
PICKUP_DISTANCE = 60
MIN_ITEMS_PER_CHUNK = 1  # Минимум предметов в чанке
MAX_ITEMS_PER_CHUNK = 5  # Максимум предметов в чанке


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
        self.background_menu = BackgroundSprite("images/background_menu.jpg", self.window)
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
        texture_normal = arcade.load_texture("images/start_game_button_2.jpg")
        texture_button = UITextureButton(texture=texture_normal, width=300, height=150)
        texture_button.on_click = """TODO"""
        self.box_layout.add(texture_button)


class Character:
    def __init__(self, name, hp, damage, defense, speed, x, y, picture: arcade.Sprite):
        self.name = name
        self.hp = hp
        self.damage = damage
        self.defence = defense
        self.picture = picture
        self.speed = speed
        self.x = x
        self.y = y


class Item:  # предмет класс
    def __init__(self, name, item_type, texture, quantity=1, value=1):
        self.name = name
        self.type = item_type
        self.texture = texture
        self.quantity = quantity
        self.value = value
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
        # Для обратной совместимости
        self.x = world_x
        self.y = world_y


class Camera:  # камера

    def __init__(self):
        self.x = 0
        self.y = 0
        self.target_x = 0
        self.target_y = 0

    def update(self, player_x, player_y):
        # Плавное движение камеры к игроку
        self.target_x = player_x - SCREEN_WIDTH // 2
        self.target_y = player_y - SCREEN_HEIGHT // 2

        self.target_x = max(0, min(self.target_x, WORLD_WIDTH - SCREEN_WIDTH))
        self.target_y = max(0, min(self.target_y, WORLD_HEIGHT - SCREEN_HEIGHT))

        self.x += (self.target_x - self.x) * CAMERA_SPEED
        self.y += (self.target_y - self.y) * CAMERA_SPEED

    def get_screen_position(self, world_x, world_y):
        return world_x - self.x, world_y - self.y

    def get_world_position(self, screen_x, screen_y):
        return screen_x + self.x, screen_y + self.y


class Game(arcade.View):
    def __init__(self):
        super().__init__()
        global SCREEN_HEIGHT, SCREEN_WIDTH
        SCREEN_HEIGHT = self.window.height
        SCREEN_WIDTH = self.window.width
        self.gamer = Character(name='Игрок', hp=100, damage=2, defense=0, picture=arcade.Sprite("""TODO"""), speed=30)
        self.inventory_slots = 4
        self.inventory = [None] * self.inventory_slots
        self.selected_slot = 0
        self.slot_color = arcade.color.GRAY
        self.selected_slot_color = arcade.color.GOLD
        self.camera = Camera()

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

        self.generate_items_for_all_chunks()

        self.distance_traveled = 0
        self.last_x = self.gamer.x
        self.last_y = self.gamer.y

    def create_item_database(self):
        return [{"name": "Меч", "type": "weapon", "texture": """TODO""", "min_qty": 1, "max_qty": 1,
                 "power": 5},
                {"name": "Нож", "type": "weapon", "texture": """TODO""", "min_qty": 1, "max_qty": 2,
                 "power": 3},
                {"name": "Щит", "type": "defense", "texture": """TODO""", "min_qty": 0, "max_qty": 1,
                 "def": 5},
                {"name": "Каменный молоток", "type": "weapon", "texture": """TODO""", "min_qty": 0, "max_qty": 2,
                 "power": 4},
                {"name": "Железный молоток", "type": "weapon", "texture": """TODO""", "min_qty": 0, "max_qty": 1,
                 "power": 6},
                {"name": "Топор", "type": "weapon", "texture": """TODO""", "min_qty": 0, "max_qty": 1,
                 "power": 10},
                {"name": "Картофель", "type": "food", "texture": """TODO""", "min_qty": 2, "max_qty": 5,
                 "heal": 4},
                {"name": "Ягоды", "type": "food", "texture": """TODO""", "min_qty": 5, "max_qty": 8,
                 "heal": 2},
                {"name": "Яблоко", "type": "food", "texture": """TODO""", "min_qty": 2, "max_qty": 5,
                 "heal": 3},
                {"name": "Растение", "type": "food", "texture": """TODO""", "min_qty": 10, "max_qty": 15,
                 "heal": 1},
                {"name": "Тухлое мясо", "type": "food", "texture": """TODO""", "min_qty": 6, "max_qty": 8,
                 "heal": random.randint(-10, 3)},
                {"name": "Мясо", "type": "food", "texture": """TODO""", "min_qty": 0, "max_qty": 1,
                 "heal": 10},
                {"name": "Рыба", "type": "food", "texture": """TODO""", "min_qty": 0, "max_qty": 1,
                 "heal": 10},
                ]

    def generate_items_for_all_chunks(self):
        chunks_x = WORLD_WIDTH // self.chunk_size + 1
        chunks_y = WORLD_HEIGHT // self.chunk_size + 1

        for chunk_x in range(chunks_x):
            for chunk_y in range(chunks_y):
                if len(self.items_on_map) >= MAX_ITEMS_ON_MAP:
                    return
                self.generate_items_for_chunk(chunk_x, chunk_y)

    def generate_items_for_chunk(self, chunk_x, chunk_y):
        chunk_key = (chunk_x, chunk_y)
        if chunk_key in self.chunks_initialized:
            return

        self.chunks_initialized.add(chunk_key)

        num_items = random.randint(MIN_ITEMS_PER_CHUNK, MAX_ITEMS_PER_CHUNK)

        chunk_world_x = chunk_x * self.chunk_size
        chunk_world_y = chunk_y * self.chunk_size

        items_spawned = 0
        attempts = 0
        max_total_attempts = num_items * 10

        while items_spawned < num_items and attempts < max_total_attempts:
            if len(self.items_on_map) >= MAX_ITEMS_ON_MAP:
                break

            item_x, item_y = self.find_free_position(chunk_world_x, chunk_world_y)

            if item_x is not None and item_y is not None:
                item = self.generate_random_item()
                if item:
                    item.set_position(item_x, item_y)
                    self.items_on_map.append(item)
                    items_spawned += 1

            attempts += 1

    def generate_random_item(self):
        if not self.item_database:
            return None

        item_data = random.choice(self.item_database)
        quantity = random.randint(item_data["min_qty"], item_data["max_qty"])

        item = Item(
            name=item_data["name"],
            item_type=item_data["type"],
            texture=item_data["texture"],
            quantity=quantity,
            value=item_data["value"]
        )

        return item

    def get_chunk_coords(self, world_x, world_y):
        chunk_x = int(world_x // self.chunk_size)
        chunk_y = int(world_y // self.chunk_size)
        return chunk_x, chunk_y

    def is_position_free(self, world_x, world_y, item_radius=16):
        tile_x = int(world_x // TILE_SIZE)
        tile_y = int(world_y // TILE_SIZE)

        #   позиция в пределах карты
        if not (0 <= tile_x < MAP_WIDTH and 0 <= tile_y < MAP_HEIGHT):
            return False

        #   сам тайл
        if self.collision_list[tile_y][tile_x] == 1:
            return False

        #   соседние тайлы (чтобы предмет не задел стену)
        check_radius = max(1, int(item_radius // TILE_SIZE))

        for dx in range(-check_radius, check_radius + 1):
            for dy in range(-check_radius, check_radius + 1):
                check_x = tile_x + dx
                check_y = tile_y + dy

                if 0 <= check_x < MAP_WIDTH and 0 <= check_y < MAP_HEIGHT:
                    if self.collision_list[check_y][check_x] == 1:

                        dist_x = abs(world_x - (check_x * TILE_SIZE + TILE_SIZE // 2))
                        dist_y = abs(world_y - (check_y * TILE_SIZE + TILE_SIZE // 2))

                        if dist_x < item_radius and dist_y < item_radius:
                            return False

        return True

    def find_free_position(self, chunk_world_x, chunk_world_y, max_attempts=20):
        for attempt in range(max_attempts):
            # позиция внутри чанка
            item_x = chunk_world_x + random.randint(50, self.chunk_size - 50)
            item_y = chunk_world_y + random.randint(50, self.chunk_size - 50)

            item_x = max(50, min(item_x, WORLD_WIDTH - 50))
            item_y = max(50, min(item_y, WORLD_HEIGHT - 50))

            if self.is_position_free(item_x, item_y):
                return item_x, item_y

        return None, None


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

    def draw_inventory(self):  # инвентарь
        start_x = (self.window.width - (self.inventory_slots * (SLOT_SIZE + SLOT_MARGIN))) // 2

        for i in range(self.inventory_slots):
            # Позиция слота
            x = start_x + i * (SLOT_SIZE + SLOT_MARGIN) + SLOT_SIZE // 2
            y = INVENTORY_Y + SLOT_SIZE // 2

            color = self.selected_slot_color if i == self.selected_slot else self.slot_color
            arcade.draw_rect_outline(arcade.LBWH(x, y, SLOT_SIZE, SLOT_SIZE), color, 3)

            if self.inventory[i] is not None:
                self.inventory[i].draw(x, y)

            arcade.draw_text(str(i + 1), x - 25, y + 30,
                             arcade.color.WHITE, 16, bold=True)

    def draw_help(self):
        arcade.draw_text(f"Пройдено: {int(self.distance_traveled)} px",
                         10, self.window.height - 140, arcade.color.LIGHT_GREEN, 14)

        arcade.draw_text(f"Собрано частиц {"""TODO"""}/5)",
                         10, self.window.height - 170, arcade.color.LIGHT_GREEN, 14)

        if self.can_pick_up and self.item_on_ground:
            arcade.draw_text("Нажмите F чтобы поднять предмет",
                             self.window.width // 2, self.window.height - 100,
                             arcade.color.YELLOW, 16, anchor_x="center")

    def on_show(self):
        pass

    def setup(self):
        self.player_list = arcade.SpriteList()
        self.wall_list = arcade.SpriteList()

        map_name = "карта_arcade_map.tmx"
        tile_map = arcade.load_tilemap(map_name, scaling=1.0)
        self.wall_list = tile_map.sprite_lists["walls"]

        self.collision_list = tile_map.sprite_lists["collision"]
        self.player_sprite = self.gamer.picture
        self.player_sprite.center_x = self.gamer.x
        self.player_sprite.center_y = self.gamer.y
        self.player_list.append(self.player_sprite)

        self.physics_engine = arcade.PhysicsEngineSimple(
            self.player_sprite, self.collision_list
        )

    def on_update(self, delta_time: float) -> bool | None:
        self.update_player()

        if self.item_on_ground:
            item_x, item_y = self.item_on_ground_pos
            distance = math.sqrt((self.gamer.x - item_x) ** 2 + (self.gamer.y - item_y) ** 2)
            self.can_pick_up = distance < 80

    def update_player(self):
        dx = 0
        dy = 0

        if self.move_up:
            dy += self.gamer.speed
        if self.move_down:
            dy -= self.gamer.speed
        if self.move_left:
            dx -= self.gamer.speed
        if self.move_right:
            dx += self.gamer.speed

        if dx != 0 and dy != 0:
            dx *= 0.7071  # 1/√2
            dy *= 0.7071

        self.gamer.x += dx
        self.gamer.y += dy

        self.distance_traveled += math.sqrt((self.gamer.x - self.last_x) ** 2 +
                                            (self.gamer.y - self.last_y) ** 2)
        self.last_x = self.gamer.x
        self.last_y = self.gamer.y

        self.gamer.x = max(10, min(self.window.width - 10, self.gamer.x))
        self.gamer.y = max(10 + INVENTORY_Y + SLOT_SIZE,
                           min(self.window.height - 10, self.gamer.y))

    def on_draw(self):
        self.clear()
        self.wall_list.draw()
        self.player_list.draw()

        arcade.draw_rect_filled(arcade.LBWH(SCREEN_WIDTH // 2, INVENTORY_Y + SLOT_SIZE // 2,
                                            SCREEN_WIDTH, SLOT_SIZE + 20), arcade.color.DARK_GRAY)
        self.draw_inventory()
        self.draw_help()

        view_left = self.camera.x - 200
        view_right = self.camera.x + SCREEN_WIDTH + 200
        view_bottom = self.camera.y - 200
        view_top = self.camera.y + SCREEN_HEIGHT + 200

        for item in self.items_on_map:
            if (view_left <= item.world_x <= view_right and
                    view_bottom <= item.world_y <= view_top):

                if item == self.item_to_pickup:
                    screen_x, screen_y = self.camera.get_screen_position(item.world_x, item.world_y)
                    arcade.draw_rect_outline(arcade.LBWH(screen_x, screen_y, SLOT_SIZE, SLOT_SIZE),
                                             arcade.color.YELLOW, 2)

                item.draw(self.camera.x, self.camera.y)


window = arcade.Window(resizable=True, title='ᗣᖇᙅᗣᙏᗣZᙓ')
menu_view = StartMenu()
window.show_view(menu_view)
arcade.run()
