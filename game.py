import arcade
from arcade import SpriteList
from arcade.gui import UIManager, UITextureButton, UILabel
from arcade.gui.widgets.layout import UIAnchorLayout, UIBoxLayout


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


class Start_Menu(arcade.View):

    def __init__(self):
        super().__init__()
        self.background_menu = BackgroundSprite("background_menu.jpg", self.window)
        self.background = SpriteList()
        self.background.append(self.background_menu)

        self.manager = UIManager()
        self.manager.enable()
        self.anchor_layout = UIAnchorLayout()
        self.box_layout = UIBoxLayout(vertical=True, space_between=20)
        self.setup_widgets()
        self.anchor_layout.add(self.box_layout)  # Box в anchor
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
        texture_normal = arcade.load_texture("start_game_button_2.jpg")
        texture_button = UITextureButton(texture=texture_normal, width=300, height=150)
        texture_button.on_click = """TODO"""
        self.box_layout.add(texture_button)


window = arcade.Window(resizable=True, title='ᗣᖇᙅᗣᙏᗣZᙓ')
menu_view = Start_Menu()
window.show_view(menu_view)
arcade.run()
