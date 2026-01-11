#PYTHON Snake3D

#-----------------------------------------------------------------------
# Snake3D v1.1 - Isometric 3D Snake for HP Prime
# Copyright (C) 2026 ArcticDogsInc
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <https://www.gnu.org/licenses/>.
#-----------------------------------------------------------------------

import hpprime as h
import graphic
import urandom as random

# Constants
SCREEN_W = 320
SCREEN_H = 240
OFFSET_X = 10
OFFSET_Y = 15

# Global timer
millis = 1000

# Global score for the game - (high scores are shared between game modes)
score = 0

# Settings
GAME_DIMENSIONS = 3 # 2D or 3D
SHADOWS_EN = 0 # 0 - no shadows, 1 - only on floor, 2 - on floor and walls
FILLING_STEPS = 10 # more is fuller, less is faster
PERIMETERS = 2 # 0 - no perimeters, 1 - only prey's, 2 - snake and prey
MAP_SIZE = 2 # 1 - small , 2 - medium, 3 - large
SF = MAP_SIZE # scaling factor
GAME_SPEED = 2 # 1 - slow, 2 - medium, 3 - fast
BASE_REFRESH_T_MS = 1000
SNAKE_COLOR = 0x00FF00
SNAKE_OUTLINE_COLOR = 0x000000
PREY_COLOR = 0xFF00FF
PREY_OUTLINE_COLOR = 0xFFFFFF

MIN_X, MIN_Y, MIN_Z = 5 * SF, -2 * SF, -2 * SF # Isometric Settings
MAX_X, MAX_Y, MAX_Z = 13 * SF, 5 * SF, 2 * SF
TILE_W = 20 / SF
TILE_H = 10 / SF

def show_settings_menu():
    global GAME_DIMENSIONS, SHADOWS_EN, FILLING_STEPS, PERIMETERS, MAP_SIZE, SF, GAME_SPEED
    
    # game dimensions
    h.eval("N := " + str(GAME_DIMENSIONS - 1))
    res = h.eval('CHOOSE(N, "Game Mode", "Classic", "3D")')
    if res:
        GAME_DIMENSIONS = int(h.eval("N")) + 1

    # shadows
    if GAME_DIMENSIONS > 2:
        res = h.eval('CHOOSE(N, "Shadows", "None", "Floor only", "Floor and walls")')
        if res: 
            SHADOWS_EN = int(h.eval("N")) - 1
    
    # map size
    res = h.eval('CHOOSE(N, "Map size", "Small", "Normal", "Large")')
    if res:
        choice = int(h.eval("N"))
        MAP_SIZE = choice
        SF = MAP_SIZE
        # Update dependent globals
        global MIN_X, MIN_Y, MIN_Z, MAX_X, MAX_Y, MAX_Z, TILE_W, TILE_H
        MIN_X, MIN_Y, MIN_Z = 5 * SF, -2 * SF, ((-2 * SF) if GAME_DIMENSIONS == 3 else 0)
        MAX_X, MAX_Y, MAX_Z = 13 * SF, 5 * SF, ((2 * SF) if GAME_DIMENSIONS == 3 else 1)
        TILE_W = int(20 / SF)
        TILE_H = int(10 / SF)

    # game speed
    h.eval("N := " + str(GAME_SPEED))
    if MAP_SIZE < 3:
        res = h.eval('CHOOSE(N, "Game speed", "Slow", "Normal", "Fast")')
    else:
        res = h.eval('CHOOSE(N, "Game speed", "Slow", "Normal")')
    if res: GAME_SPEED = int(h.eval("N"))
           
def wait(t_s):
    h.eval('WAIT({})'.format(t_s))

def get_hiscore_var_name():
    d = str(GAME_DIMENSIONS) + "D"
    s = ["S", "M", "L"][MAP_SIZE - 1]
    v = ["S", "N", "F"][GAME_SPEED - 1]
    return "SNAKE3D_HI_{}_{}_{}".format(d, s, v)

def get_high_score():
    hiscore_var = get_hiscore_var_name()
    try:
        res = h.eval(str(hiscore_var))
        if res == None:
            return -1
        return int(res)
    except:
        return -1

def save_high_score(new_score):
    hiscore_var = get_hiscore_var_name()
    h.eval(hiscore_var + ":=" + str(int(new_score)))

class Snake():
    def __init__(self):
        self.size = 2
        self.outline = SNAKE_OUTLINE_COLOR
        self.color = SNAKE_COLOR
        self.velocity = [1, 0, 0]
        self.body = [[MIN_X, MIN_Y, 0], [MIN_X + 1, MIN_Y, 0]]
        
    def head(self):
        return self.body[-1]

    def tail(self):
        return self.body[0]
    
    def move(self):
        new_head = [self.head()[i] + self.velocity[i] for i in range(3)]
        if new_head[0] > MAX_X-1:
            new_head[0] = MIN_X
        if new_head[1] > MAX_Y-1:
            new_head[1] = MIN_Y
        if new_head[2] > MAX_Z-1:
            new_head[2] = MIN_Z
        if new_head[0] < MIN_X:
            new_head[0] = MAX_X-1
        if new_head[1] < MIN_Y:
            new_head[1] = MAX_Y-1
        if new_head[2] < MIN_Z:
            new_head[2] = MAX_Z-1
        self.body.pop(0)
        self.body.append(new_head)

    def grow(self):
        self.body.insert(0, self.tail())

class Prey():
    color = PREY_COLOR
    outline = PREY_OUTLINE_COLOR
    body = [0]

    def __init__(self):
        self.spawn(None)

    def spawn(self, snake):
        width = MAX_X - MIN_X
        height = MAX_Y - MIN_Y
        depth = MAX_Z - MIN_Z
        total_cells = width * height * depth

        if not snake:
            self.body = [
                random.randint(MIN_X, MAX_X-1), 
                random.randint(MIN_Y, MAX_Y-1), 
                random.randint(MIN_Z, MAX_Z-1)]
            return

        occupied_indices = set()
        for p in snake.body:
            idx = (p[0] - MIN_X) + (p[1] - MIN_Y) * width + (p[2] - MIN_Z) * width * height
            occupied_indices.add(idx)

        all_indices = range(total_cells)
        allowed_indices = [i for i in all_indices if i not in occupied_indices]

        if not allowed_indices:
            self.body = [] # WIN
            return

        choice = random.choice(allowed_indices)
        
        z = choice // (width * height)
        rem = choice % (width * height)
        y = rem // width
        x = rem % width

        self.body = [x + MIN_X, y + MIN_Y, z + MIN_Z]

class World():
    def __init__(self):
        self.main_buffer = {} 

    def iso_to_2d(self, x, y, z):
        sx = OFFSET_X + (x - y) * TILE_W
        sy = OFFSET_Y + (x + y) * TILE_H - (z * TILE_H * 2)
        return (int(sx), int(sy))
    
    def load_buffer(self, snake: Snake, prey: Prey):
        self.main_buffer = {}
        for snake_block in snake.body:
            self.main_buffer[tuple(snake_block)] = [snake.color, snake.outline]

        self.main_buffer[tuple(prey.body)] = [prey.color, prey.outline]

    def draw_horizontal_perimeter(self, z, color_hex, outer_en):
        c1 = self.iso_to_2d(MIN_X, MIN_Y, z)
        c2 = self.iso_to_2d(MAX_X, MIN_Y, z)
        c3 = self.iso_to_2d(MAX_X, MAX_Y, z)
        c4 = self.iso_to_2d(MIN_X, MAX_Y, z)

        b0 = self.iso_to_2d(MIN_X, MIN_Y, MIN_Z) # null point

        if outer_en:
            points = [c1, c2, c3, c4, c1]
            for i in range(len(points)-1):
                h.line(1, points[i][0], points[i][1], points[i+1][0], points[i+1][1], color_hex)
            return

        points = [c4, c1, c2] # just the back ones
        for i in range(len(points)-1):
            h.line(1, points[i][0], points[i][1], points[i+1][0], points[i+1][1], color_hex)

    def draw_grid_cube(self):
        b1 = self.iso_to_2d(MIN_X, MIN_Y, MIN_Z) # bottom face
        b2 = self.iso_to_2d(MAX_X, MIN_Y, MIN_Z)
        b3 = self.iso_to_2d(MAX_X, MAX_Y, MIN_Z)
        b4 = self.iso_to_2d(MIN_X, MAX_Y, MIN_Z)
        
        t1 = self.iso_to_2d(MIN_X, MIN_Y, MAX_Z) # top face
        t2 = self.iso_to_2d(MAX_X, MIN_Y, MAX_Z)
        t3 = self.iso_to_2d(MAX_X, MAX_Y, MAX_Z)
        t4 = self.iso_to_2d(MIN_X, MAX_Y, MAX_Z)

        b0 = self.iso_to_2d(MIN_X, MIN_Y, MIN_Z) # null point

        # define the 12 edges as pairs of points
        edges = [
            # bottom face
            (b1, b2), (b2, b3), (b3, b4), (b4, b1), 
            # top face
            # (t1, t2), (t2, t3), (t3, t4), (t4, t1),
            (t1, t2), (b0, b0), (b0, b0), (t4, t1),
            # vertical pillars connecting bottom to top
            # (b1, t1), (b2, t2), (b3, t3), (b4, t4)
            (b1, t1), (b2, t2), (b0, b0), (b4, t4)
        ]

        # draw the lines
        for p1, p2 in edges:
            h.line(1, p1[0], p1[1], p2[0], p2[1], 0xFFFFFF)

    def draw_cube(self, center_xyz, color, outlines_en):
            x, y, z = center_xyz[0], center_xyz[1], center_xyz[2]
            
            p1 = self.iso_to_2d(x, y, z + 1) # top face vertices
            p2 = self.iso_to_2d(x + 1, y, z + 1)
            p3 = self.iso_to_2d(x + 1, y + 1, z + 1)
            p4 = self.iso_to_2d(x, y + 1, z + 1)
            
            p2_b = self.iso_to_2d(x + 1, y, z) # bottom face vertices
            p3_b = self.iso_to_2d(x + 1, y + 1, z)
            p4_b = self.iso_to_2d(x, y + 1, z)

            self.fill_isometric_rect(p1, p2, p3, p4, color) # top face fill
            
            if GAME_DIMENSIONS > 2:
                self.fill_isometric_rect(p2, p3, p3_b, p2_b, sum(int((color >> s & 0xFF) * (z - MIN_Z) / (MAX_Z - MIN_Z or 1)) << s for s in (16, 8, 0)))  # right face fill - dimmed by z
            else:
                self.fill_isometric_rect(p2, p3, p3_b, p2_b, color & 0xB0B0B0) # right face fill
            self.fill_isometric_rect(p3, p4, p4_b, p3_b, color) # left face fill

            out_col = 0xFFFF if outlines_en else 0x0000
            
            h.line(1, p1[0], p1[1], p2[0], p2[1], out_col) # top face edges
            h.line(1, p2[0], p2[1], p3[0], p3[1], out_col)
            h.line(1, p3[0], p3[1], p4[0], p4[1], out_col)
            h.line(1, p4[0], p4[1], p1[0], p1[1], out_col)
            
            h.line(1, p2[0], p2[1], p2_b[0], p2_b[1], out_col) # vertical edges
            h.line(1, p3[0], p3[1], p3_b[0], p3_b[1], out_col)
            h.line(1, p4[0], p4[1], p4_b[0], p4_b[1], out_col)
            
            h.line(1, p2_b[0], p2_b[1], p3_b[0], p3_b[1], out_col) # bottom edges
            h.line(1, p3_b[0], p3_b[1], p4_b[0], p4_b[1], out_col)

    def fill_isometric_rect(self, a, b, c, d, color):
        global FILLING_STEPS
        
        for i in range(FILLING_STEPS + 1):
            f = i / FILLING_STEPS
            # linear interpolation between points
            x_start = int(a[0] + (d[0] - a[0]) * f)
            y_start = int(a[1] + (d[1] - a[1]) * f)
            x_end = int(b[0] + (c[0] - b[0]) * f)
            y_end = int(b[1] + (c[1] - b[1]) * f)
            h.line(1, x_start, y_start, x_end, y_end, color)

    def draw_floor_grid(self):
        grid_color = 0x222222 # dark grey
        for x in range(MIN_X, MAX_X + 1):
            p1 = self.iso_to_2d(x, MIN_Y, MIN_Z)
            p2 = self.iso_to_2d(x, MAX_Y, MIN_Z)
            h.line(1, p1[0], p1[1], p2[0], p2[1], grid_color)
        for y in range(MIN_Y, MAX_Y + 1):
            p1 = self.iso_to_2d(MIN_X, y, MIN_Z)
            p2 = self.iso_to_2d(MAX_X, y, MIN_Z)
            h.line(1, p1[0], p1[1], p2[0], p2[1], grid_color)

    def game_over_animation(self, win):
        for x in range(MIN_X, MAX_X):
            for z in range(MIN_Z, MAX_Z):
                for y in range(MIN_Y, MAX_Y):
                    if win:
                        self.draw_cube([x,y,z], random.randint(0x333333, 0xFFFFFF), False)
                    else:
                        self.draw_cube([x,y,z], 0xFF0000, False)
            h.blit(0, 0, 0, 1)
            if MAP_SIZE < 3:
                wait(0.001)
        if win:
            h.eval('TEXTOUT_P("YOU WIN!!!", G1, 100, 110, 6, 65535, 200, 0')
        else:
            h.eval('TEXTOUT_P("GAME OVER", G1, 100, 110, 6, 65535, 200, 0')
        if score > get_high_score():
            save_high_score(score)
            h.eval('TEXTOUT_P("HIGH SCORE!!!", G1, 90, 160, 6, 0, 200, 16776960)')
        h.blit(0, 0, 0, 1)

    def draw_shadows(self, coords_xyz, color):
        global SHADOWS_EN
        if not SHADOWS_EN:
            return
        
        if SHADOWS_EN >= 1:
            # floor - XY plane at MIN_Z
            f1 = self.iso_to_2d(coords_xyz[0], coords_xyz[1], MIN_Z)
            f2 = self.iso_to_2d(coords_xyz[0] + 1, coords_xyz[1], MIN_Z)
            f3 = self.iso_to_2d(coords_xyz[0] + 1, coords_xyz[1] + 1, MIN_Z)
            f4 = self.iso_to_2d(coords_xyz[0], coords_xyz[1] + 1, MIN_Z)
            self.fill_isometric_rect(f1, f2, f3, f4, color)
        
        if SHADOWS_EN == 2:
            # right wall - YZ plane at MIN_X
            r1 = self.iso_to_2d(MIN_X, coords_xyz[1], coords_xyz[2])
            r2 = self.iso_to_2d(MIN_X, coords_xyz[1] + 1, coords_xyz[2])
            r3 = self.iso_to_2d(MIN_X, coords_xyz[1] + 1, coords_xyz[2] + 1)
            r4 = self.iso_to_2d(MIN_X, coords_xyz[1], coords_xyz[2] + 1)
            self.fill_isometric_rect(r1, r2, r3, r4, color)

            # left wall - XZ plane at MIN_Y
            l1 = self.iso_to_2d(coords_xyz[0], MIN_Y, coords_xyz[2])
            l2 = self.iso_to_2d(coords_xyz[0] + 1, MIN_Y, coords_xyz[2])
            l3 = self.iso_to_2d(coords_xyz[0] + 1, MIN_Y, coords_xyz[2] + 1)
            l4 = self.iso_to_2d(coords_xyz[0], MIN_Y, coords_xyz[2] + 1)
            self.fill_isometric_rect(l1, l2, l3, l4, color)

    def render(self, game):

        if game.state == game.State.GAME_OVER:
            return
        
        if game.state == game.State.PAUSED:
            return
        
        ###### World render START
        h.fillrect(1, 0, 0, SCREEN_W, SCREEN_H, 0x000000, 0x000000) 

        # decorations
        self.draw_floor_grid()
        self.draw_grid_cube()

        # snake and prey z levels
        if PERIMETERS > 0 and GAME_DIMENSIONS > 2:
            if game.snake.head()[2] == game.prey.body[2]:
                self.draw_horizontal_perimeter(game.snake.head()[2], 0x0000FF, False)
            else:
                if PERIMETERS == 2:
                    self.draw_horizontal_perimeter(game.snake.head()[2], 0x00FF00, False)
                self.draw_horizontal_perimeter(game.prey.body[2], 0xFF00FF, False)

        # render shadows
        self.draw_shadows(game.prey.body, 0xFF00FF)
        for snake_block in game.snake.body:
            self.draw_shadows(snake_block, 0x555555)
        
        # render entities
        items = list(self.main_buffer.items())
        items.sort(key=lambda item: (item[0][2], item[0][1], item[0][0]))
        for coords_xyz, entity in items:
            self.draw_cube(coords_xyz, entity[0], entity[1])
        ###### World render END

        # UI overlay
        # TEXTOUT(text, GROB*, x, y, font size*, text color*, width*, background color*) 
        if game.state == game.State.READY:
            h.eval('TEXTOUT_P("READY - press any key", G1, 60, 140, 5, 65535, 200, 0')

        if game.state == game.State.RUN:
            global score
            s_msg = "Score: " + str(score)
            h.eval('TEXTOUT_P("' + s_msg + '", G1, 10, 10, 3, 65535)')

            hiscore = get_high_score()
            if get_high_score() > 0:
                s_msg = "High score: " + str(hiscore)
                h.eval('TEXTOUT_P("' + s_msg + '", G1, 10, 215, 3, 65535)')

        # h.blit(target, dx, dy, source)
        h.blit(0, 0, 0, 1) 

class Config:
    def __init__(self):
        pass

class Game: 
    class State:
        RESET = 0
        INIT = 1
        READY = 2
        RUN = 3
        PAUSED = 4
        GAME_OVER = 5

    state = State.RESET

    def __init__(self, world, snake, prey):
        self.world = world
        self.snake = snake
        self.prey = prey

    def get_key(self):
        return int(h.eval("GETKEY"))
    
    KEY_UP = 2
    KEY_DOWN = 12
    KEY_LEFT = 7
    KEY_RIGHT = 8
    KEY_8 = 33
    KEY_2 = 43
    KEY_4 = 37
    KEY_6 = 39
    KEY_ENTER = 30
    KEY_9 = 34
    KEY_7 = 32
    def update_direction(self, key, velocity):

        if key == self.KEY_LEFT or key == self.KEY_4:
            if abs(velocity[2]) == 1:
                velocity[:] = [0, 1, 0]
            else:
                velocity[:] = [velocity[1], -velocity[0], 0]
            return

        if key == self.KEY_RIGHT or key == self.KEY_6:
            if abs(velocity[2]) == 1:
                velocity[:] = [0, -1, 0]
            else:
                velocity[:] = [-velocity[1], velocity[0], 0]
            return

        if GAME_DIMENSIONS < 3:
            return
        
        if key == self.KEY_UP or key == self.KEY_8:
            if abs(velocity[2]) == 1:
                velocity[:] = [-1, 0, 0]
            else:
                velocity[:] = [0, 0, 1]
        if key == self.KEY_DOWN or key == self.KEY_2:
            if abs(velocity[2]) == 1:
                velocity[:] = [1, 0, 0]
            else:
                velocity[:] = [0, 0, -1]

    def update(self):
        global score

        if self.state == self.State.RESET: 
            h.fillrect(1, 0, 0, SCREEN_W, SCREEN_H, 0x000000, 0x000000) 
            h.blit(0, 0, 0, 1) # h.blit(target, dx, dy, source)
            self.state = self.State.INIT
            return

        if self.state ==  self.State.INIT: 
            score = 0
            self.snake = Snake()
            self.prey = Prey()
            self.world.load_buffer(self.snake, self.prey)
            self.state = self.State.READY
            return

        if self.state ==  self.State.PAUSED:
            key = self.get_key()
            if key == self.KEY_ENTER:
                self.state = self.State.RUN
            return

        if self.state ==  self.State.READY:
            key = self.get_key()
            if key > 0:
                self.state = self.State.RUN
            return

        if self.state ==  self.State.GAME_OVER:
            key = self.get_key()
            if key > 0:
                score = 0
                self.snake = Snake()
                self.prey = Prey()
                self.world.load_buffer(self.snake, self.prey)
                self.state = self.State.READY
            return
        
        if self.state == self.State.RUN:
            key = self.get_key()
            if key == self.KEY_ENTER:
                h.eval('TEXTOUT_P("PAUSED - press ENTER", G1, 60, 140, 5, 65535, 200, 0)')
                h.blit(0, 0, 0, 1) 
                self.state = self.State.PAUSED
                return
            self.update_direction(key, self.snake.velocity)
            self.snake.move()

            if self.snake.head() == self.prey.body:
                score += 1
                self.snake.grow()
                self.prey.spawn(self.snake)
                if self.prey.body == []:
                    self.world.game_over_animation(True)
                    self.state = self.State.GAME_OVER 
            
            for snake_block in self.snake.body[:-1]:
                if self.snake.head() == snake_block: # game over
                    self.world.game_over_animation(False)
                    self.state = self.State.GAME_OVER 

            self.world.load_buffer(self.snake, self.prey)
            return

        self.state = self.State.RESET

    def draw(self):
        self.world.render(self)

class Snake3D:
    def __enter__(self):
        self.separator = int(h.eval('HSeparator')) # Save the current separator state and set it to 0
        h.eval('HSeparator := 0')

        show_settings_menu() # prompt user game settings
        if get_high_score() < 0: save_high_score(0) # init hiscore var if needed

        h.dimgrob(1, SCREEN_W, SCREEN_H, 0x0000) # init G1

        # init game objects
        self.world = World() 
        self.snake = Snake()
        self.prey = Prey()
        self.game = Game(self.world, self.snake, self.prey)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        h.eval('HSeparator := ' + repr(self.separator)) # reset separator
        return exc_type is KeyboardInterrupt

    def run(self):
        with self:
            global millis
            h.eval('RECT()')
            
            while True:
                wait(0.010)
                millis += 10
                if millis >= BASE_REFRESH_T_MS / GAME_SPEED:
                    millis = 0
                    self.game.update()
                    self.game.draw()
                    
Snake3D().run()
#END

EXPORT SNAKE_3D()
BEGIN
    PYTHON(Snake3D);
    FREEZE;
END;