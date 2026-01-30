import math
import random

import arcade
from PIL.ImageOps import scale
from arcade import SpriteList
from arcade.examples.camera_platform import TILE_SCALING
from arcade.gui import UIManager, UITextureButton, UILabel
from arcade.gui.widgets.layout import UIAnchorLayout, UIBoxLayout

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
LEFT_CATCHING = 10
ITEMS = [{"name": "Картофель", "type": "food", "texture": "images/food/food_potato.jpg", "quantity": 5,
                 "heal": 4, "hunger": 2},
                {"name": "Ягоды", "type": "food", "texture": "images/food/food_berries.jpg", "quantity": 8,
                 "heal": 2, "hunger": - 1},
                {"name": "Яблоко", "type": "food", "texture": "images/food/food_apple.jpg", "quantity": 5,
                 "heal": 3, "hunger": - 3},
                {"name": "Растение", "type": "food", "texture": "images/food/food_grass.jpg", "quantity": 15,
                 "heal": 1, "hunger": -4},
                {"name": "Тухлое мясо", "type": "food", "texture": "images/food/food_bad_meet.jpg", "quantity": 8,
                 "heal": random.randint(-10, 3), "hunger": 2},
                {"name": "Мясо", "type": "food", "texture": "images/food/food_meet.jpg", "quantity": 1,
                 "heal": 10, "hunger": 10},
                {"name": "Рыба", "type": "food", "texture": "images/food/food_fish.jpg", "quantity": 1,
                 "heal": 10, "hunger": 10},
                ]

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
        self.timer = 0

GAMER = Character(name='Игрок', hp=100, damage=2, defense=0, picture=arcade.Sprite(":resources:images/animated_characters/female_adventurer/femaleAdventurer_idle.png", scale=0.5), speed=5, x=WORLD_WIDTH//2, y=WORLD_HEIGHT//2)


class Inventory:
    def __init__(self):
        self.free_slots = ["Empty" for _ in range(4)]

    def remove_from_invent(self, pos):
        self.free_slots[pos] = "Empty"

    def add_to_invent(self, pos, item):
        self.free_slots[pos] = item


INVENTORY = Inventory()


class Inventory_View(arcade.View):
    def __init__(self, game_view):
        super().__init__()
        self.game_view = game_view
        self.screen_width = self.window.width
        self.screen_height = self.window.height
        self.selected_slot = 2
        self.ui_manager = UIManager()
        self.ui_manager.enable()
        self.setup_widgets()
        self.background_color = arcade.color.COOL_GREY

    def setup_widgets(self):
        self.ui_manager.clear()
        self.v_box = UIBoxLayout(vertical=True, space_between=10, x=200,
                                 y=self.screen_height // 2 - self.screen_height // 2 * 0.5)
        self.v_box_2 = UIBoxLayout(vertical=True, space_between=10, x=self.screen_width // 2,
                                   y=self.screen_height // 2 - self.screen_height // 2 * 0.5)
        hp = UITextureButton(texture=arcade.load_texture("images/interface/hp.jpg"), scale=0.3)
        hunger = UITextureButton(texture=arcade.load_texture("images/interface/hunger.jpg"), scale=0.3)
        eat = UITextureButton(texture=arcade.load_texture("images/interface/eat.jpg"), scale=0.3,
                              texture_hovered=arcade.load_texture("images/interface/eat_hovered.jpg"),
                              texture_pressed=arcade.load_texture("images/interface/eat_pressed.jpg"))
        time = UITextureButton(texture=arcade.load_texture("images/interface/time.jpg"), scale=0.3)
        left = UITextureButton(texture=arcade.load_texture("images/interface/left.jpg"), scale=0.3)
        if self.selected_slot == 1:
            slot_1_texture = arcade.load_texture("images/interface/1_slot_chosen.jpg")
        else:
            slot_1_texture = arcade.load_texture("images/interface/1_slot.jpg")
        slot1 = UITextureButton(texture=slot_1_texture,
                                scale=0.2)
        if self.selected_slot == 2:
            slot_2_texture = arcade.load_texture("images/interface/2_slot_chosen.jpg")
        else:
            slot_2_texture = arcade.load_texture("images/interface/2_slot.jpg")
        slot2 = UITextureButton(texture=slot_2_texture,
                                scale=0.2)
        if self.selected_slot == 3:
            slot_3_texture = arcade.load_texture("images/interface/3_slot_chosen.jpg")
        else:
            slot_3_texture = arcade.load_texture("images/interface/3_slot.jpg")
        slot3 = UITextureButton(texture=slot_3_texture,
                                scale=0.2)
        if self.selected_slot == 4:
            slot_4_texture = arcade.load_texture("images/interface/4_slot_chosen.jpg")
        else:
            slot_4_texture = arcade.load_texture("images/interface/4_slot.jpg")
        slot4 = UITextureButton(texture=slot_4_texture,
                                scale=0.2)


        label_hp = UILabel(text=f"{GAMER.hp}/100", text_color=(0, 0, 0))
        x1 = UIBoxLayout(vertical=False, space_between=20)
        x1.add(hp)
        x1.add(label_hp)
        self.v_box.add(x1)
        label_hunger = UILabel(text=f"{GAMER.hungry}/100", text_color=(0, 0, 0))
        x2 = UIBoxLayout(vertical=False, space_between=20)
        x2.add(hunger)
        x2.add(label_hunger)
        self.v_box.add(x2)
        label_time = UILabel(text="15", text_color=(0, 0, 0))
        x3 = UIBoxLayout(vertical=False, space_between=20)
        x3.add(time)
        x3.add(label_time)
        self.v_box.add(x3)
        label1 = UILabel(text=INVENTORY.free_slots[0], text_color=(0, 0, 0))
        y1 = UIBoxLayout(vertical=False, space_between=20)
        y1.add(slot1)
        y1.add(label1)
        self.v_box_2.add(y1)
        label2= UILabel(text=INVENTORY.free_slots[1], text_color=(0, 0, 0))
        y2 = UIBoxLayout(vertical=False, space_between=20)
        y2.add(slot2)
        y2.add(label2)
        self.v_box_2.add(y2)
        label3 = UILabel(text=INVENTORY.free_slots[2], text_color=(0, 0, 0))
        y3 = UIBoxLayout(vertical=False, space_between=20, text_color=(255, 255, 255))
        y3.add(slot3)
        y3.add(label3)
        self.v_box_2.add(y3)
        label4 = UILabel(text=INVENTORY.free_slots[3], text_color=(0, 0, 0))
        y4 = UIBoxLayout(vertical=False, space_between=20)
        y4.add(slot4)
        y4.add(label4)
        self.v_box_2.add(y4)
        self.v_box.add(eat)
        label_left = UILabel(text=f"{LEFT_CATCHING} / 10", text_color=(0, 0, 0))
        x4 = UIBoxLayout(vertical=False, space_between=20)
        x4.add(left)
        x4.add(label_left)
        self.v_box.add(x4)

        eat.on_click = self.do_stuff

        self.ui_manager.add(self.v_box)
        self.ui_manager.add(self.v_box_2)  # Всё в manager

    def do_stuff(self, *args):
        if INVENTORY.free_slots[self.selected_slot - 1] != "Empty":
            INVENTORY.free_slots[self.selected_slot - 1] = "Empty"
            sound1 = arcade.load_sound("sounds/eating.mp3")
            sound1.play()
            for elem in ITEMS:
                if elem["name"] == INVENTORY.free_slots[self.selected_slot - 1]:
                    GAMER.hp += elem["heal"]
                    GAMER.hungry += elem["hunger"]
        else:
            sound2 = arcade.load_sound("sounds/loser.mp3")
            sound2.play()
        self.setup_widgets()
        return

    def on_key_press(self, symbol: int, modifiers: int) -> bool | None:
        if symbol == arcade.key.SPACE:
            self.window.show_view(self.game_view)

        elif symbol == arcade.key.Q:
            INVENTORY.remove_from_invent(self.selected_slot - 1)

        elif symbol == arcade.key.KEY_1:
            self.selected_slot = 1

        elif symbol == arcade.key.KEY_2:
            self.selected_slot = 2

        elif symbol == arcade.key.KEY_3:
            self.selected_slot = 3

        elif symbol == arcade.key.KEY_4:
            self.selected_slot = 4

        self.setup_widgets()

    def on_resize(self, width: int, height: int) -> bool | None:
        self.screen_width = width
        self.screen_height = height
        self.setup_widgets()
        return True

    def on_draw(self):
        self.clear()
        self.ui_manager.draw()


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
        text = UILabel(text="ᗣᖇᙅᗣᙏᗣZᙓ", font_size=80, text_color=arcade.color.MODE_BEIGE, width=300,
                       align="center")
        self.box_layout.add(text)
        create_game = UITextureButton(texture=arcade.load_texture("images/interface/create_game.jpg"), scale=0.5,
                                      texture_hovered=arcade.load_texture("images/interface/create_game_hovered.jpg"),
                                      texture_pressed=arcade.load_texture("images/interface/create_game_pressed.jpg"))
        choose_level = UITextureButton(texture=arcade.load_texture("images/interface/choose_level.jpg"), scale=0.5,
                                       texture_hovered=arcade.load_texture("images/interface/choose_level_hovered.jpg"),
                                       texture_pressed=arcade.load_texture("images/interface/choose_level_pressed.jpg"))
        lid_tab = UITextureButton(texture=arcade.load_texture("images/interface/lid_tab.jpg"), scale=0.5,
                                  texture_hovered=arcade.load_texture("images/interface/lid_tab_hovered.jpg"),
                                  texture_pressed=arcade.load_texture("images/interface/lid_tab_pressed.jpg"))
        sign_up = UITextureButton(texture=arcade.load_texture("images/interface/sign_up.jpg"), scale=0.5,
                                  texture_hovered=arcade.load_texture("images/interface/sign_up_hovered.jpg"),
                                  texture_pressed=arcade.load_texture("images/interface/sign_up_pressed.jpg"))
        self.box_layout.add(create_game)
        self.box_layout.add(choose_level)
        self.box_layout.add(lid_tab)
        self.box_layout.add(sign_up)

        create_game.on_click = self.button_press

    def button_press(self, *args, **kwargs):
        game_view = Game()
        self.window.show_view(game_view)
        return


class Item:  # предмет класс
    def __init__(self, name, item_type, texture, quantity=1, heal=0, hunger=0):
        self.name = name
        self.type_st = item_type
        self.texture = texture
        self.quantity = quantity
        self.heal = heal
        self.hunger = hunger
        self.inventory_position = None

        self.x = 0
        self.y = 0
        self.world_x = 0  # Глобальные координаты на карте
        self.world_y = 0

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
        global LEFT_CATCHING

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

        self.to_win_list = arcade.SpriteList()
        k = 0
        while k != 10:
            win = arcade.Sprite(arcade.load_texture("images/things/to_win.jpg"), scale=0.1)
            win.center_x = arcade.math.rand_in_circle((WORLD_WIDTH // 2, WORLD_HEIGHT // 2), WORLD_WIDTH // 2)[0]
            win.center_y = arcade.math.rand_in_circle((WORLD_WIDTH // 2, WORLD_HEIGHT // 2), WORLD_HEIGHT // 2)[1]
            if not arcade.check_for_collision_with_list(win, self.collision_list):
                self.to_win_list.append(win)
                k += 1

        self.left = 10

        self.player_sprite = self.gamer.picture
        self.player_sprite.center_x = self.gamer.x
        self.player_sprite.center_y = self.gamer.y
        self.player_list.append(self.player_sprite)

        self.physics_engine = arcade.PhysicsEngineSimple(
            self.player_sprite,
            self.collision_list
        )

        self.move_up = False
        self.move_down = False
        self.move_left = False
        self.move_right = False

        self.distance_traveled = 0
        self.last_x = self.gamer.x
        self.last_y = self.gamer.y

        self.items_sprite_list = arcade.SpriteList()
        self.items = self.create_item_database()
        self.collection = []
        self.put_item()


    def create_item_database(self):
        return ITEMS

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
            num = random.randint(0, 6)
            if self.items[num]["quantity"] == 0:
                continue
            texture_name = self.items[num]["texture"]
            item = Item(name=self.items[num]["name"],
                             item_type=self.items[num]["type"],
                             texture=arcade.Sprite(texture_name, scale=0.5, center_x=0, center_y=0),
                             quantity=self.items[num]["quantity"],
                             heal=self.items[num]["heal"],
                            hunger=self.items[num]["hunger"])
            for j in range(max_try):
                item.texture.center_x = random.randint(0, self.world_width * TILE_SCALING * TILE_SIZE)
                item.texture.center_y = random.randint(0, self.world_height * TILE_SCALING * TILE_SIZE)
                print(arcade.check_for_collision_with_list(item.texture, self.collision_list))
                if in_square(item.texture.center_x, item.texture.center_y) and not arcade.check_for_collision_with_list(item.texture,
                                                                                                      self.collision_list)\
                        and item.texture not in self.items_sprite_list:
                    self.items_sprite_list.append(item.texture)
                    self.collection.append(item)
                    self.items[num]["quantity"] -= 1
                    # print(item.texture.center_x, item.texture.center_y)
                    # print(item.name, item.quantity) #debug

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
            game_inter = Inventory_View(self)
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
        global LEFT_CATCHING
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

        self.gamer.timer += delta_time

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

        hitted = arcade.check_for_collision_with_list(self.player_sprite, self.items_sprite_list)

        for item in hitted:
            item.remove_from_sprite_lists()
            for i in range(4):
                if INVENTORY.free_slots[i] == "Empty":
                    for elem in self.collection:
                        if elem.texture == item:
                            INVENTORY.free_slots[i] = elem.name

        to_win_catch = arcade.check_for_collision_with_list(self.player_sprite, self.to_win_list)
        for elem in to_win_catch:
            elem.remove_from_sprite_lists()
            self.left -= 1
            LEFT_CATCHING = self.left




    def on_resize(self, width: int, height: int) -> bool | None:
        self.camera.match_window()
        self.gui_camera.match_window()


    def on_draw(self):
        self.clear()

        self.camera.use()

        self.floor_list.draw()
        self.wall_list.draw()
        self.pos1.draw()
        self.pos2.draw()
        self.pos3.draw()
        self.items_sprite_list.draw()
        self.to_win_list.draw()
        self.player_list.draw()
        self.gui_camera.use()



window = arcade.Window(resizable=True, title='ᗣᖇᙅᗣᙏᗣZᙓ')
menu_view = StartMenu()
window.show_view(menu_view)
arcade.run()
