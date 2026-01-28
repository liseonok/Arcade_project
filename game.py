import math
import random

import arcade
from arcade import SpriteList
from arcade.examples.camera_platform import TILE_SCALING
from arcade.gui import UIManager, UITextureButton, UILabel
from arcade.gui.widgets.layout import UIAnchorLayout, UIBoxLayout
from pyglet.graphics import Batch
from pyglet.resource import texture

SLOT_SIZE = 64
SLOT_MARGIN = 10
INVENTORY_Y = 50
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 1200
# Константы карты
TILE_SIZE = 32
MAP_WIDTH = 96  # 96 тайлов в ширину
MAP_HEIGHT = 96  # 96 тайлов в высоту
TILE_SCALING = 2
WORLD_WIDTH = MAP_WIDTH * TILE_SIZE * TILE_SCALING  # 3072 пикселя
WORLD_HEIGHT = MAP_HEIGHT * TILE_SIZE * TILE_SCALING  # 3072 пикселя
CAMERA_SPEED = 0.1
CAMERA_LERP = 0.12

MAX_ITEMS_ON_MAP = 100  # Максимум предметов на всей карте
ITEM_SPAWN_RATE = 0.05  # Шанс появления предмета за кадр
PICKUP_DISTANCE = 60
MIN_ITEMS_PER_CHUNK = 1  # Минимум предметов в чанке
MAX_ITEMS_PER_CHUNK = 5  # Максимум предметов в чанке
LEVEL = 1


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
        self.hungry = 100

GAMER = Character(name='Игрок', hp=100, damage=2, defense=0, picture=arcade.Sprite(":resources:images/animated_characters/female_person/femalePerson_idle.png", scale=0.5), speed=5, x=WORLD_WIDTH//2, y=WORLD_HEIGHT//2)


class Inventory_View(arcade.View):
    def __init__(self):
        super().__init__()
        self.picture = arcade.Sprite("images/interface/inventory_text.jpg", scale=0.5)
        self.picture.center_x = self.window.width // 2
        self.picture.center_y = self.window.height - 100
        self.load = arcade.SpriteList()
        self.load.append(self.picture)
        self.batch = Batch()
        self.hp_text = arcade.Text(text=f"{GAMER.hp}", x=WORLD_WIDTH//2, y=WORLD_HEIGHT - 200, batch=self.batch, font_size=50)
        self.hungry_text = arcade.Text(text=f"{GAMER.hungry}", x=WORLD_WIDTH//2, y=WORLD_HEIGHT - 300, batch=self.batch, font_size=50)

    def on_key_press(self, symbol: int, modifiers: int) -> bool | None:
        if symbol == arcade.key.SPACE:
            game_view = Game()
            self.window.show_view(game_view)

    def on_draw(self):
        self.clear()
        self.load.draw()
        self.batch.draw()


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


class Item:  # предмет класс
    def __init__(self, name, item_type, texture, quantity=1, heal=0, damage=0, defence=0):
        self.name = name
        self.type_st = item_type
        self.texture = texture
        self.quantity = quantity
        self.heal = heal
        self.damage = damage
        self.defence = defence
        self.inventory_position = None

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


class GameOver(arcade.View):
    def __init__(self):
        super().__init__()

    def on_draw(self) -> bool | None:
        self.clear()


class Game(arcade.View):
    def __init__(self):
        super().__init__()

        self.world_width = 96 * TILE_SIZE * TILE_SCALING
        self.world_height = 96 * TILE_SIZE * TILE_SCALING

        self.screen_width = self.window.width
        self.screen_height = self.window.height
        self.DEAD_ZONE_W = int(self.screen_width * 0.01)
        self.DEAD_ZONE_H = int(self.screen_height * 0.01)

        self.gamer = GAMER
        self.camera = arcade.Camera2D()
        self.gui_camera = arcade.camera.Camera2D()


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
        self.mobs = []

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

        self.distance_traveled = 0
        self.last_x = self.gamer.x
        self.last_y = self.gamer.y

        self.items_sprite_list = arcade.SpriteList()
        self.items = self.create_item_database()
        self.collection = []
        self.put_item()


    def create_item_database(self):
        return [{"name": "Меч", "type": "weapon", "texture": "images/things/thing_sword.jpg", "quantity": 1,
                 "damage": 5, "heal": 0, "defence": 0},
                {"name": "Нож", "type": "weapon", "texture": "images/things/thing_knife.jpg", "quantity": 2,
                 "damage": 3, "heal": 0, "defence": 0},
                {"name": "Щит", "type": "defense", "texture": "images/things/thing_shield.jpg", "quantity": 1,
                 "defence": 5, "heal": 0, "damage": 0},
                {"name": "Каменный молоток", "type": "weapon", "texture": "images/things/thing_stone_molotok.jpg", "quantity": 2,
                 "damage": 4, "heal": 0, "defence": 0},
                {"name": "Железный молоток", "type": "weapon", "texture": "images/things/thing_iron_molotok.jpg", "quantity": 1,
                 "damage": 6, "heal": 0, "defence": 0},
                {"name": "Топор", "type": "weapon", "texture": "images/things/thing_axe.jpg", "quantity": 2,
                 "damage": 10, "heal": 0, "defence": 0},
                {"name": "Картофель", "type": "food", "texture": "images/food/food_potato.jpg", "quantity": 5,
                 "heal": 4, "defence": 0, "damage": 0},
                {"name": "Ягоды", "type": "food", "texture": "images/food/food_berries.jpg", "quantity": 8,
                 "heal": 2, "defence": 0, "damage": 0},
                {"name": "Яблоко", "type": "food", "texture": "images/food/food_apple.jpg", "quantity": 5,
                 "heal": 3, "defence": 0, "damage": 0},
                {"name": "Растение", "type": "food", "texture": "images/food/food_grass.jpg", "quantity": 15,
                 "heal": 1, "defence": 0, "damage": 0},
                {"name": "Тухлое мясо", "type": "food", "texture": "images/food/food_bad_meat.jpg", "quantity": 8,
                 "heal": random.randint(-10, 3), "defence": 0, "damage": 0},
                {"name": "Мясо", "type": "food", "texture": "images/food/food_meet.jpg", "quantity": 1,
                 "heal": 10, "defence": 0, "damage": 0},
                {"name": "Рыба", "type": "food", "texture": "images/food/food_fish.jpg", "quantity": 1,
                 "heal": 10, "defence": 0, "damage": 0},
                ]

    def put_item(self):
        max_try = 10
        amount = 30
        item = None

        def in_square(x, y):
            if ((32 * TILE_SIZE * TILE_SCALING < x < 59 * TILE_SIZE * TILE_SCALING) and
                    (37 * TILE_SIZE * TILE_SCALING < y < 66 * TILE_SIZE * TILE_SCALING)):
                return False
            return True

        for i in range(amount):
            num = random.randint(0, 12)
            if self.items[num]["quantity"] == 0:
                continue
            texture_name = self.items[num]["texture"]
            item = Item(name=self.items[num]["name"],
                             item_type=self.items[num]["type"],
                             texture=arcade.Sprite(texture_name, scale=0.2),
                             quantity=self.items[num]["quantity"],
                             heal=self.items[num]["heal"],
                             damage=self.items[num]["damage"],
                             defence=self.items[num]["defence"])
            for j in range(max_try):
                item.texture.x = random.randint(0, self.world_width * TILE_SCALING * TILE_SIZE)
                item.texture.y = random.randint(0, self.world_height * TILE_SCALING * TILE_SIZE)
                if in_square(item.texture.x, item.texture.y) and arcade.check_for_collision_with_list(item.texture,
                                                                                                      self.collision_list)\
                        and item.texture not in self.items_sprite_list:
                    self.items_sprite_list.append(item.texture)
                    self.collection.append(item)
                    self.items[num]["quantity"] -= 1

    def on_key_press(self, key, modifiers):
        if key == arcade.key.W:
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

        elif key == arcade.key.SPACE:
            game_inter = Inventory_View()
            self.window.show_view(game_inter)

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

    def draw_help(self):
        arcade.Text(f"Пройдено: {int(self.distance_traveled)} px",
                         10, self.window.height - 140, arcade.color.LIGHT_GREEN, 14)

        arcade.Text(f"Собрано частиц {6}/5)",
                         10, self.window.height - 170, arcade.color.LIGHT_GREEN, 14)

    def on_show(self):
        pass


    def on_update(self, delta_time: float) -> bool | None:
        if self.gamer.hp <= 0:
            game_over = GameOver()
            self.gamer = Character(name='Игрок', hp=100, damage=2, defense=0, picture=arcade.Sprite(":resources:images/animated_characters/female_person/femalePerson_idle.png", scale=0.5), speed=5, x=self.world_width//2, y=self.world_height//2)
            self.window.show_view(game_over)

        self.player_sprite.change_x = 0
        self.player_sprite.change_y = 0

        if self.gamer.hungry == 0:
            self.gamer.hp -= 0.02
        else:
            self.gamer.hungry -= 0.002

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

    def on_resize(self, width: int, height: int) -> bool | None:
        self.camera.match_window()
        self.gui_camera.match_window()


    def on_draw(self):
        self.clear()

        self.camera.use()

        self.floor_list.draw()
        self.wall_list.draw()
        self.pos1.draw()
        self.player_list.draw()
        self.pos2.draw()
        self.pos3.draw()
        self.items_sprite_list.draw()
        self.gui_camera.use()



window = arcade.Window(resizable=True, title='ᗣᖇᙅᗣᙏᗣZᙓ')
menu_view = StartMenu()
window.show_view(menu_view)
arcade.run()
