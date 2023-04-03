#!/usr/bin/env python

import time
import sys
import math
import arcade
import pygame
import os
import tkinter as tk

# --- Constants ---
SPRITE_SCALING_PLAYER = 0.25
SPRITE_SCALING_ENEMY = 0.4

TILE_SCALING = 1.0

SCREEN_WIDTH = 1600
SCREEN_HEIGHT = 900
PLAYER_START_X = 50
PLAYER_START_Y = SCREEN_HEIGHT - 100
SCREEN_TITLE = "Adventures of Ordux"
#PLAYER_MOVEMENT_SPEED = 7
#GRAVITY = 0.1 #1
#PLAYER_JUMP_SPEED = 1 #24
BULLET_SPEED = 5


##### feedback form stuff #####

def fetch(entries):
    for entry in entries:
        field = entry[0]
        text = entry[1].get()
        print('%s: "%s"' % (field, text))
    sys.exit()


def makeform(root, fields):
    entries = []
    for field in fields:
        row = tk.Frame(root)
        lab = tk.Label(row, width=15, text=field, anchor='w')
        ent = tk.Entry(row)
        row.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)
        lab.pack(side=tk.LEFT)
        ent.pack(side=tk.RIGHT, expand=tk.YES, fill=tk.X)
        entries.append((field, ent))
    return entries


def feedback_form():
    root = tk.Tk()
    fields = 'Name', 'Feedback'
    ents = makeform(root, fields)
    root.bind('<Return>', (lambda event, e=ents: fetch(e)))
    b1 = tk.Button(root, text='Submit',
                   command=(lambda e=ents: fetch(e)))
    b1.pack(side=tk.LEFT, padx=5, pady=5)
    root.mainloop()

##### END feedback form stuff ######


class GameWindow(arcade.Window):

    def __init__(self):
        # Call the parent class initializer
        super().__init__(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE)

        self.intro = 1
        self.intro_count = 0
        self.win_count = 0
        self.win_frame = 0

        self.background = None
        self.frame_count = 0

        self.heart = arcade.load_texture(os.path.join("assets", "life.png"))

        self.gameoverimage = arcade.load_texture(os.path.join("assets",
                                                              "gameover.jpeg"))

        # Set the working directory (where we expect to find files) to the same
        # directory this .py file is in.
        file_path = os.path.dirname(os.path.abspath(__file__))
        os.chdir(file_path)

        # Set up the player info
        self.player_sprite = None
        self.score = 0
        self.player_dead = False
        self.level_complete = False

        # Score and lives and level
        self.score = 0
        self.lives = 5

        # Don't show the mouse cursor
        self.set_mouse_visible(False)

    def create_grassy_block(self, x0, x1, y0, y1, moving=False):
        for x in range(x0, x1, 25):
            for y in range(y0, y1, 25):
                wall = arcade.Sprite(os.path.join("assets", str(self.level), "block.png"), TILE_SCALING)
                wall.center_x = x
                wall.center_y = y
                self.wall_list.append(wall)
                if moving:
                    wall.change_y = 1
                    self.moving_wall_list.append(wall)

            if not moving:
                wall = arcade.Sprite(os.path.join("assets", str(self.level), "top.png"), TILE_SCALING)
                wall.center_x = x
                wall.center_y = y1
                self.wall_list.append(wall)

    def create_enemy(self, x, y, vx, vy, image, shooter=False):
        # Create some enemies
        enemy = arcade.Sprite(image,
                              SPRITE_SCALING_ENEMY)
        enemy.center_x = x
        enemy.center_y = y
        enemy.change_x = vx
        enemy.change_y = vy
        if shooter is True:
            self.enemy_shooters_list.append(enemy)
        else:
            self.enemy_list.append(enemy)

    def setup(self, level):
        """ Set up the game and initialize the variables.
            This stuff is common to all levels           """
        self.level = level

        # intro images
        self.intro_ims = []
        for i in range(1, 6):
            self.intro_ims.append(arcade.load_texture(os.path.join("assets", "intro", str(i) + ".jpeg")))

        # win images
        self.win_images = []
        for i in range(1, 5):
            self.win_images.append(arcade.load_texture(os.path.join("assets", "win", str(i) + ".jpeg")))
        self.won_game = False

        # Sprite lists
        self.player_list = arcade.SpriteList()
        self.enemy_list = arcade.SpriteList()
        self.enemy_shooters_list = arcade.SpriteList()
        self.bullet_list = arcade.SpriteList()
        self.coin_list = arcade.SpriteList()
        self.diamond_list = arcade.SpriteList()
        self.wall_list = arcade.SpriteList()
        self.moving_wall_list = arcade.SpriteList()

        # Set up the player
        self.player_sprite = arcade.Sprite(os.path.join("assets", str(level), "cat.png"), SPRITE_SCALING_PLAYER)
        self.player_sprite.center_x = PLAYER_START_X
        self.player_sprite.center_y = PLAYER_START_Y
        self.player_list.append(self.player_sprite)

        """ Set up the level-specific stuff """

        self.background = arcade.load_texture(os.path.join("assets",
                                                            str(level),
                                                            "background.jpg"))
        if level == 1:
            # set up the diamond
            self.diamond = arcade.Sprite(os.path.join("assets", "diamante.png"), 0.05)
            self.diamond.center_x = SCREEN_WIDTH - 100
            self.diamond.center_y = SCREEN_HEIGHT - 250

            # create some blocks of earth with grass on the top
            self.create_grassy_block(0, SCREEN_WIDTH, -25, 0)
            self.create_grassy_block(0, SCREEN_WIDTH+25, SCREEN_HEIGHT, SCREEN_HEIGHT)
            self.create_grassy_block(0, 25, 0, SCREEN_HEIGHT)
            self.create_grassy_block(300, 1000, 0, 50)
            self.create_grassy_block(500, 800, 200, 225)
            self.create_grassy_block(650, 900, 325, 350)
            self.create_grassy_block(750, 1100, 450, 475)
            self.create_grassy_block(950, 1200, 600, 625)
            self.create_grassy_block(SCREEN_WIDTH-250, SCREEN_WIDTH + 25, 0, SCREEN_HEIGHT-300)

            # create physics engine to take care of player movement
            self.PLAYER_MOVEMENT_SPEED = 3
            self.GRAVITY = 0.002
            self.PLAYER_JUMP_SPEED = 1
            self.PLAYER_DOWN_SPEED = 0.5
            self.physics_engine = arcade.PhysicsEnginePlatformer(self.player_sprite,
                                                                 self.wall_list,
                                                                 self.GRAVITY)
            self.physics_engine.enable_multi_jump(1) # number doesn't matter for this

            # Create some enemies
            self.create_enemy(SCREEN_WIDTH - 350, 140, 5, 0, os.path.join("assets", str(1), "enemy1.png"))
            self.create_enemy(300, 600, 0, 5, os.path.join("assets", str(1), "enemy2.png"))
            self.create_enemy(850, 800, 0, 5, os.path.join("assets", str(1), "enemy2.png"))

            # create the coins
            coordinate_list = [[350, 100],
                               [400, 100],
                               [450, 100],
                               [500, 100],
                               [550, 100],
                               [600, 100],
                               [650, 100],
                               [700, 275],
                               [600, 275],
                               [650, 275],
                               [700, 400],
                               [750, 400],
                               [800, 400],
                               [1000, 675],
                               [1050, 675],
                               [1100, 675],
                               ]

            for coordinate in coordinate_list:
                coin = arcade.Sprite(os.path.join("assets", "coin.png"), 0.05)
                coin.position = coordinate
                self.coin_list.append(coin)
        elif level == 2:
            # set up the diamond
            self.diamond = arcade.Sprite(os.path.join("assets", "diamante.png"), 0.05)
            self.diamond.center_x = SCREEN_WIDTH - 200
            self.diamond.center_y = 130

            # set up floor and obstacles
            self.wall_list = arcade.SpriteList()


            # create some grassy blocks of earth with grass on the top
            self.create_grassy_block(0, 200, 0, 400)
            self.create_grassy_block(200, 500, 0, 500)
            self.create_grassy_block(700, 900, 0, 400)
            self.create_grassy_block(SCREEN_WIDTH-500, SCREEN_WIDTH-400, 0, 300)
            self.create_grassy_block(SCREEN_WIDTH-400, SCREEN_WIDTH, 0, 100)
            self.create_grassy_block(SCREEN_WIDTH-300, SCREEN_WIDTH, 500, 540)



            # create physics engine to take care of player movement
            self.PLAYER_MOVEMENT_SPEED = 7
            self.GRAVITY = 1
            self.PLAYER_JUMP_SPEED = 23
            self.PLAYER_DOWN_SPEED = 0
            self.physics_engine = arcade.PhysicsEnginePlatformer(self.player_sprite,
                                                                 self.wall_list,
                                                                 self.GRAVITY)
            # Create some enemies
            self.create_enemy(SCREEN_WIDTH - 250, 590, 0, 0, os.path.join("assets", str(2), "enemy_wolf.png"), shooter=True)
            self.create_enemy(700, 450, 0, 0, os.path.join("assets", str(2), "enemy_plant.png"))
            self.create_enemy(1000, 100, 8, 0, os.path.join("assets", str(2), "enemy_squid.png"))

            # create the coins
            coordinate_list = [[550, 640],
                               [600, 640],
                               [650, 640],
                               [SCREEN_WIDTH - 500, 400],
                               [SCREEN_WIDTH - 450, 400],
                               [SCREEN_WIDTH - 400, 400]]

            for coordinate in coordinate_list:
                coin = arcade.Sprite(os.path.join("assets", "coin.png"), 0.05)
                coin.position = coordinate
                self.coin_list.append(coin)
        elif level == 3:
            # set up the diamond
            self.diamond = arcade.Sprite(os.path.join("assets", "diamante.png"), 0.05)
            self.diamond.center_x = SCREEN_WIDTH - 100
            self.diamond.center_y = 130

            # set up floor and obstacles
            self.wall_list = arcade.SpriteList()

            # create some blocks

            self.create_grassy_block(0, SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_HEIGHT+10)
            self.create_grassy_block(0, 330, 400, 450)
            self.create_grassy_block(400, 450, 700, 900)
            self.create_grassy_block(400, 570, 270, 300, moving=True)
            self.create_grassy_block(400, 570, -10, 0)
            self.create_grassy_block(520, 670, 500, 530)
            self.create_grassy_block(690, 870, 600, 630)
            self.create_grassy_block(970, 1100, 400, 430, moving=True)
            self.create_grassy_block(970, 1100, -10, 0)
            self.create_grassy_block(1300, 1340, 0, 480)
            self.create_grassy_block(1300, SCREEN_WIDTH, 0, 100)
            self.create_grassy_block(1250, SCREEN_WIDTH, 700, 730)


            # create physics engine to take care of player movement
            self.PLAYER_MOVEMENT_SPEED = 7
            self.GRAVITY = 1
            self.PLAYER_JUMP_SPEED = 23
            self.PLAYER_DOWN_SPEED = 0
            self.physics_engine = arcade.PhysicsEnginePlatformer(self.player_sprite,
                                                                 self.wall_list,
                                                                 self.GRAVITY)
            # Create some enemies
            self.create_enemy(SCREEN_WIDTH - 250, 790, 0, 0, os.path.join("assets", str(3), "dragon.png"), shooter=True)
            self.create_enemy(780, 700, 0, 2, os.path.join("assets", str(3), "bat.png"))

            # create the coins
            coordinate_list = [
                               [410, 30],
                               [460, 30],
                               [510, 30],
                               [540, 620],
                               [590, 620],
                               [640, 620],
                               [440, 330],
                               [490, 330],
                               [540, 330],
                               [SCREEN_WIDTH - 610, 460],
                               [SCREEN_WIDTH - 560, 460],
                               [SCREEN_WIDTH - 510, 460]]

            for coordinate in coordinate_list:
                coin = arcade.Sprite(os.path.join("assets", "coin.png"), 0.05)
                coin.position = coordinate
                self.coin_list.append(coin)
            pass

    def on_draw(self):
        arcade.start_render()

        if self.intro:
            self.intro_count += 1
            if self.intro_count % 200 == 0:
                self.intro += 1
            if self.intro > 5:
                self.intro = False
            arcade.draw_lrwh_rectangle_textured(0, 0,
                                                SCREEN_WIDTH, SCREEN_HEIGHT,
                                                self.intro_ims[self.intro - 1])
            return



        # draw background
        arcade.draw_lrwh_rectangle_textured(0, 0,
                                            SCREEN_WIDTH, SCREEN_HEIGHT,
                                            self.background)

        # Put the text on the screen.
        arcade.draw_text("Score: " + str(self.score), 30, SCREEN_HEIGHT - 40, arcade.color.WHITE, 25)
        arcade.draw_text("Lives:", SCREEN_WIDTH - 300, SCREEN_HEIGHT - 40, arcade.color.WHITE, 25)
        for i in range(self.lives):
            arcade.draw_scaled_texture_rectangle(SCREEN_WIDTH - 150 + i * 20, SCREEN_HEIGHT - 20, self.heart, 0.1, 0)

        if self.player_dead:
            arcade.draw_lrwh_rectangle_textured(0, 0,
                                                SCREEN_WIDTH, SCREEN_HEIGHT,
                                                self.gameoverimage)
            pygame.mixer.music.stop()
        elif self.level_complete:
            if self.level == 3:
                self.win_count += 1
                if self.win_count % 200 == 0:
                    self.win_frame += 1
                if self.win_frame > 3:
                    feedback_form()
                else:
                    arcade.draw_lrwh_rectangle_textured(0, 0,
                                                SCREEN_WIDTH, SCREEN_HEIGHT,
                                                self.win_images[self.win_frame])
            else:
                arcade.draw_text("Level " + str(self.level) + " Complete", 80, SCREEN_HEIGHT - 200, arcade.color.WHITE, 120)
                arcade.draw_text("Press Enter to continue...", 80, SCREEN_HEIGHT - 400, arcade.color.WHITE, 60)
        else:
            """ Draw everything """
            self.enemy_list.draw()
            self.enemy_shooters_list.draw()
            self.player_list.draw()
            self.wall_list.draw()
            self.coin_list.draw()
            self.diamond.draw()
            self.bullet_list.draw()


    def on_key_press(self, key, modifiers):
        """Called whenever a key is pressed. """

        if key == arcade.key.UP or key == arcade.key.W:
            if self.physics_engine.can_jump():
                self.player_sprite.change_y = self.PLAYER_JUMP_SPEED
        if key == arcade.key.DOWN or key == arcade.key.S:
             self.player_sprite.change_y = -self.PLAYER_DOWN_SPEED
        elif key == arcade.key.LEFT or key == arcade.key.A:
            self.player_sprite.change_x = -self.PLAYER_MOVEMENT_SPEED
        elif key == arcade.key.RIGHT or key == arcade.key.D:
            self.player_sprite.change_x = self.PLAYER_MOVEMENT_SPEED
        elif key == arcade.key.ENTER and self.level_complete:
            self.level_complete = False
            self.setup(self.level + 1)

    def on_key_release(self, key, modifiers):
        """Called when the user releases a key. """

        if key == arcade.key.LEFT or key == arcade.key.A:
            self.player_sprite.change_x = 0
        elif key == arcade.key.RIGHT or key == arcade.key.D:
            self.player_sprite.change_x = 0

    def on_update(self, delta_time):
        """ Movement and game logic """

        self.frame_count += 1

        for shooter in self.enemy_shooters_list:
# Position the start at the enemy's current location
            start_x = shooter.center_x
            start_y = shooter.center_y

            # Get the destination location for the bullet
            dest_x = self.player_sprite.center_x
            dest_y = self.player_sprite.center_y

            # Do math to calculate how to get the bullet to the destination.
            # Calculation the angle in radians between the start points
            # and end points. This is the angle the bullet will travel.
            x_diff = dest_x - start_x
            y_diff = dest_y - start_y
            angle = math.atan2(y_diff, x_diff)

            # Set the enemy to face the player.
            shooter.angle = math.degrees(angle)-180

            # Shoot every 60 frames change of shooting each frame
            if self.frame_count % 200 == 0:
                bullet = arcade.Sprite(os.path.join("assets", str(self.level), "bullet.png"), 0.1)
                bullet.center_x = start_x
                bullet.center_y = start_y

                # Angle the bullet sprite
                bullet.angle = math.degrees(angle)

                # Taking into account the angle, calculate our change_x
                # and change_y. Velocity is how fast the bullet travels.
                bullet.change_x = math.cos(angle) * BULLET_SPEED
                bullet.change_y = math.sin(angle) * BULLET_SPEED

                self.bullet_list.append(bullet)

        # Get rid of the bullet when it flies off-screen
        for bullet in self.bullet_list:
            if bullet.top < 0:
                bullet.remove_from_sprite_lists()
        self.bullet_list.update()

        # Call update on all moving sprites
        self.enemy_list.update()
        self.physics_engine.update()

        # check for moving wall collision with other walls
        for wall in self.moving_wall_list:
            wall_collision_list = arcade.check_for_collision_with_list(wall, self.wall_list)
            if len(wall_collision_list) > 0:
                wall.change_x *= -1
                wall.change_y *= -1

        # check for enemy collisions with scenery
        for enemy in self.enemy_list:
            enemy_wall_collision_list = arcade.check_for_collision_with_list(enemy, self.wall_list)
            if len(enemy_wall_collision_list) > 0:
                enemy.change_x *= -1
                enemy.change_y *= -1

        # Call update on all sprites
        self.enemy_list.update()
        self.physics_engine.update()

        # check for player/coin collisions
        coin_collision_list = arcade.check_for_collision_with_list(self.player_sprite, self.coin_list)
        for coin in coin_collision_list:
            coin.remove_from_sprite_lists()
            self.score += 1

        # check for player/enemy collisions
        enemy_collision_list = arcade.check_for_collision_with_list(self.player_sprite, self.enemy_list)
        for enemy in enemy_collision_list:
            self.die()
        enemy_collision_list = arcade.check_for_collision_with_list(self.player_sprite, self.enemy_shooters_list)
        for enemy in enemy_collision_list:
            self.die()

        # check for bullet collisions
        bullet_collision_list = arcade.check_for_collision_with_list(self.player_sprite, self.bullet_list)
        for bullet in bullet_collision_list:
            self.die()

        if arcade.check_for_collision(self.player_sprite, self.diamond):
            self.win()


        # check if player has fallen down
        if self.player_sprite.center_y < 0:
            self.die()

    def win(self):
        self.level_complete = True

    def die(self):
        self.player_sprite.center_x = PLAYER_START_X
        self.player_sprite.center_y = PLAYER_START_Y
        self.lives -= 1
        if self.lives <= 0:
            self.player_dead = True


def main():

    # play background music

    pygame.mixer.init()
    pygame.mixer.music.load("mario.mp3")
    pygame.mixer.music.play()

    # open game
    window = GameWindow()
    window.setup(1)  # start on level 1
    arcade.run()


if __name__ == "__main__":
    main()
