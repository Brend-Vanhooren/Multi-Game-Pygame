import numpy as np  # pyright: ignore [reportMissingImports]
import numpy.typing as npt  # pyright: ignore [reportMissingImports]
import pygame as pg  # pyright: ignore [reportMissingImports]
import sys
import os

pg.init()

os.chdir(os.path.dirname(os.path.abspath(__file__))) #set working directory to location of this file
clock = pg.time.Clock()
rng = np.random.default_rng()

window = pg.display.set_mode((1000, 1000), pg.RESIZABLE)

I, J, L, O, S, T, Z = range(1, 8)

global tile_size, small_tile_size, background, play_surf, hold_surf, next_surf, pressed_keys, info_surf, transparent_play_surf

images: list[pg.Surface] = [pg.image.load(f'Sprites/{name}.png') for name in ["I", "J", "L", "O", "S", "T", "Z", "Background"]]
big_images: list[pg.Surface] = [images[1]]*8
small_images: list[pg.Surface] = [images[1]]*7

#caption
pg.display.set_caption("Tetris")
pg.display.set_icon(images[0])

#variables
background_ratio = 987/775 #background height/width
pieces: dict[str, list[list[int]]] = {"I": [[I,I,I,I]], "J": [[J,0,0], [J,J,J]], "L": [[0,0,L], [L,L,L]], "O": [[O,O], [O,O]], "S": [[0,S,S], [S,S,0]], "T": [[0,T,0], [T,T,T]], "Z": [[Z,Z,0], [0,Z,Z]]}
time = prev_time = pg.time.get_ticks()
prev_move_time: dict[int, int] = {pg.K_DOWN: time, pg.K_LEFT: time, pg.K_RIGHT: time, pg.K_q: time, pg.K_d: time}
delta_time = 0
POINTS = [0, 100, 300, 500, 800] #Amount of point given based on lines cleared
prev_lines = 0

def text_with_outline(surface: pg.Surface, text: str, color_text: tuple[int,int,int], color_outline: tuple[int,int,int], position: tuple[float, float], size: int) -> pg.Rect:
    font = pg.font.SysFont("Verdana",  size)
    text_render = font.render(text, True, color_text)
    text_rect = text_render.get_rect(center=position)
    outline = font.render(text, True, color_outline)
    outline_rects: list[pg.Rect] = []

    offset = 1
    outline_rects.append(outline.get_rect(center=np.add(position, (-offset, 0))))
    outline_rects.append(outline.get_rect(center=np.add(position, (offset, 0))))
    outline_rects.append(outline.get_rect(center=np.add(position, (0, -offset))))
    outline_rects.append(outline.get_rect(center=np.add(position, (0, offset))))
    
    surface.blits([(outline, outline_rects[0]), (outline, outline_rects[1]), (outline, outline_rects[2]), (outline, outline_rects[3]), (text_render, text_rect)])
    return text_rect
    
class Order:
    def __init__(self) -> None:
        self.list = [rng.permuted(list(pieces.keys())), rng.permuted(list(pieces.keys()))]
        self.step: int = 0

    def __str__(self) -> str:
        return str(self.list)

    def __next__(self) -> str:
        piece = str(self.list[0][self.step])
        self.step += 1
        if self.step == 7:
            self.step = 0
            self.list[0] = rng.permuted(self.list[0])
            self.list = np.roll(self.list, 1, axis=0)
        return piece
    
    def following(self) -> list[str]:
        following: list[str] = []
        step = self.step
        for _ in range(5):
            if step >= 7: dest = (1, step-7)
            else: dest = (0, step)
            following.append(str(self.list[dest[0]][dest[1]]))
            step += 1
        return following

piece_order = Order()

class Board:
    def __init__(self) -> None:
        self.move_board: npt.NDArray[np.int16] = np.zeros((22, 10), dtype=int) #Board used for actively moving piece
        self.static_board: npt.NDArray[np.int16] = np.zeros((22, 10), dtype=int) #Used for the locked pieces
        self.piece_name: str | None = None #Name of active piece
        self.hold_piece: str | None = None #Piece in hold
        self.hold_used: bool = False 
        self.dead: bool = False
        self.paused: bool = False
        self.score: int = 0
        self.level: int = 0
        self.prev_lines: int = 0
        self.total_lines: int = 0
        self.level: int = 1
        self.following = piece_order.following()
        self.spawn_piece()

    def __str__(self) -> str:
        return str(self.move_board + self.static_board)
    
    def draw(self) -> pg.Rect | None:
        view_board = self.move_board + self.static_board
        for i in range(2,22):
            for j in range(10):
                if 0 < view_board[i][j] < 8:
                    play_surf.blit(big_images[int(view_board[i][j]) - 1], (j * tile_size, (i - 2) * tile_size))

        multiply_list: list[float] = [1/10, 3/10, 5/10, 7/10, 9/10]
        for piece_number in range(5):
            piece_name = self.following[piece_number]
            piece = np.array(pieces[piece_name], dtype=int)
            shape = piece.shape
            x_offset = next_surf.get_width()/2-shape[1]/2*small_tile_size
            y_offset = next_surf.get_height()*multiply_list[piece_number]-shape[0]/2*small_tile_size
            for i in range(shape[0]):
                for j in range(shape[1]):
                    if 0 < piece[i][j] < 8:
                        next_surf.blit(small_images[int(piece[i][j]-1)], (x_offset + j*small_tile_size, y_offset +  i*small_tile_size))

        text_size = int(min(info_surf.get_size())/max(len(f"Level: {self.level}"), len(f"Score: {self.score}"), len(f"Level: {self.level}")) * 2)

        text_with_outline(info_surf, f"Level: {self.level}", (0,0,0), (0,0,0), (info_surf.get_width()/2, info_surf.get_height()/3), text_size)
        text_with_outline(info_surf, f"Score: {self.score}", (0,0,0), (0,0,0), (info_surf.get_width()/2, info_surf.get_height()/3+text_size), text_size)

        if self.hold_piece is not None:
            hold_piece = np.array(pieces[self.hold_piece], dtype=int)
            hold_shape = hold_piece.shape

            x_offset = hold_surf.get_width()/2-hold_shape[1]/2*small_tile_size
            y_offset = hold_surf.get_height()/2-hold_shape[0]/2*small_tile_size
        
            for i in range(hold_shape[0]):
                for j in range(hold_shape[1]):
                    if 0 < hold_piece[i][j] < 8:
                        hold_surf.blit(small_images[int(hold_piece[i][j]-1)], (x_offset + j*small_tile_size, y_offset +  i*small_tile_size))

        if self.paused:
            paused_rect = text_with_outline(play_surf,"Paused", (14, 135, 133), (4, 77, 75), (play_surf.get_width()/2, play_surf.get_height()/3), int(1.6*tile_size))
            continue_rect = text_with_outline(play_surf, "Continue", (14, 135, 133), (4, 77, 75), (play_surf.get_width()/2, play_surf.get_height()/3+1.5*tile_size), int(tile_size))
            return paused_rect.union(continue_rect)

        return None

    def spawn_piece(self, piece_name: str | None = None):
        if np.any(self.static_board[1, 3:6]):
            self.dead = True
        if self.dead:
            return
        if piece_name is None:
            self.full_lines()
            piece_name = next(piece_order)
        self.move_board.fill(0)
        piece = np.array(pieces[piece_name], dtype=int)
        piece_height, piece_width = piece.shape

        start_col = (10 - piece_width) // 2

        self.move_board[2-piece_height : 2, start_col : start_col + piece_width] = piece
        self.piece_name = piece_name
        self.following = piece_order.following()

    def move(self, direction: int) -> None:
        shift = -1 if direction == pg.K_LEFT else 1
        axis = 0 if direction == pg.K_DOWN else 1
        self.move_board = np.roll(self.move_board, shift, axis=axis)

    def rotate(self, direction: int) -> None:
        if self.piece_name == "O": return

        rows, cols = np.nonzero(self.move_board)
        top, bottem = min(rows), max(rows)
        left, right = min(cols), max(cols)
        piece = self.move_board[top:bottem+1, left:right+1]
        piece_height, piece_width = np.shape(piece)

        axes = (1,0) if direction == pg.K_d else (0,1)
        piece = np.rot90(piece, axes=axes)
        new_height, new_width = piece_width, piece_height

        new_top = top + piece_height // 2 - new_height // 2
        new_left = left + piece_width // 2 - new_width // 2

        # Check if the rotated piece goes out of bounds or collides with static_board
        if new_top >= 0 and new_left >= 0 and new_top + new_height < 22 and new_left + new_width < 10:
            for pos in np.argwhere(piece):
                pos = pos+(new_top, new_left)
                if self.static_board[pos[0]][pos[1]] != 0:
                    return
            self.move_board = np.zeros((22, 10), dtype=int)
            self.move_board[new_top:new_top+new_height, new_left:new_left+new_width] = piece

    def lock_piece(self):
        self.hold_used = False
        self.score += len(np.argwhere(self.move_board))
        self.static_board += self.move_board
        self.spawn_piece()

    def check_collision(self, direction: int) -> bool:
        for y in range(22):
            for x in range(10):
                if self.move_board[y, x] != 0 and direction == pg.K_DOWN and (y == 21 or self.static_board[y + 1, x] != 0):
                        return True
                if self.move_board[y, x] != 0 and direction == pg.K_LEFT and (x == 0 or self.static_board[y, x - 1] != 0):
                        return True
                if self.move_board[y, x] != 0 and direction == pg.K_RIGHT and (x == 9 or self.static_board[y, x + 1] != 0):
                        return True
        return False

    def full_lines(self):
        row, lines = 21, 0
        while row >= 2:
            if np.all(self.static_board[row] != 0):
                self.static_board[2:row+1] = self.static_board[1:row]
                self.static_board[1] = np.zeros((1,10), int)
                lines += 1
            else: 
                row -= 1
        self.score += int(POINTS[lines] * self.level * (1.5 if self.prev_lines == 4 else 1))
        self.prev_lines = lines
        self.total_lines += lines
        self.level = self.total_lines // 10 + 1

    def hold(self):
        if self.hold_used: return
        self.hold_used = True

        if self.hold_piece is None:
            self.hold_piece = self.piece_name
            self.spawn_piece()
        else:
            piece_name = self.piece_name
            self.spawn_piece(self.hold_piece)
            self.hold_piece = piece_name

    def death(self) -> pg.Rect:
        pg.mouse.set_visible(True)
        game_over_rect = text_with_outline(play_surf,f"Game Over", (14, 135, 133), (4, 77, 75), (play_surf.get_width()/2, play_surf.get_height()/3), int(1.6*tile_size))
        score_rect = text_with_outline(play_surf,f"Score: {self.score}", (14, 135, 133), (4, 77, 75), (play_surf.get_width()/2, play_surf.get_height()/3+2*tile_size), int(1.2*tile_size))
        return game_over_rect.union(score_rect)

    def pause(self):
        if self.paused:
            self.paused = False
            pg.mouse.set_visible(False)
            pg.mouse.set_pos((window.get_width() / 2, window.get_height() / 3))
        else:
            self.paused = True
            pg.mouse.set_pos((window.get_width() / 2, window.get_height() / 3))
            pg.mouse.set_visible(True)

def set_sizes():
    global tile_size, small_tile_size, background, play_surf, hold_surf, next_surf, info_surf, transparent_play_surf
    width, height = pg.Surface.get_size(window)
    background_width = width if width*background_ratio <= height else height/background_ratio
    background_height = height if width*background_ratio > height else width*background_ratio
    background = pg.Surface.subsurface(window, ((width-background_width)/2, 0, background_width, background_height))

    play_surf = pg.Surface.subsurface(background, (background_width*(129/675), background_height*(9/857),background_width*(424/674), background_height*(836/857)))
    transparent_play_surf = pg.Surface(play_surf.get_size(), pg.SRCALPHA)
    transparent_play_surf.fill((0,0,0,0))
    tile_size = int((play_surf.get_width()/10 + play_surf.get_height()/20)/2)
    small_tile_size = int(tile_size/1.65)

    hold_surf = pg.Surface.subsurface(background, (background_width*(10/675), background_height*(30/857), background_width*(111/674), background_width*(130/674)))
    next_surf = pg.Surface.subsurface(background, (background_width*(557/675), background_height*(30/857), background_width*(111/674), background_width*(472/674)))
    info_surf = pg.Surface.subsurface(background, (background_width*(557/675), background_height*(400/674), background_width*(111/674), background_width*(100/674)))

    for i in range(7):
        big_images[i] = pg.transform.smoothscale(images[i], (tile_size, tile_size))
        small_images[i] = pg.transform.smoothscale(images[i], (small_tile_size, small_tile_size))
    big_images[7] = pg.transform.smoothscale(images[7], (background_width, background_height))

def key_outputs():
    global pressed_keys
    pressed_keys = pg.key.get_pressed()
    key_intervals: dict[int, int] = {pg.K_DOWN: 100, pg.K_LEFT: 150, pg.K_RIGHT: 150, pg.K_q: 225, pg.K_d: 225}

    for key in [pg.K_DOWN, pg.K_LEFT, pg.K_RIGHT, pg.K_SPACE, pg.K_q, pg.K_d]:
        if not pressed_keys[key]: continue
        if board.check_collision(key):
            if key == pg.K_DOWN:
                board.lock_piece()
                prev_move_time[key] = time
                return
            else: continue
        if key in [pg.K_DOWN, pg.K_LEFT, pg.K_RIGHT] and time - prev_move_time[key] > key_intervals[key]:
            board.move(key)
            prev_move_time[key] = time
        elif key in [pg.K_q, pg.K_d] and time - prev_move_time[key] > key_intervals[key]:
            board.rotate(key)
            prev_move_time[key] = time

        elif key == pg.K_SPACE: board.hold()


set_sizes()
board = Board()
pg.mouse.set_visible(False)

while True:
    clock.tick(120)
    pg.display.update()
    window.fill((0,0,0))
    background.blit(big_images[7], (0,0))

    play_surf.blit(transparent_play_surf, (0,0))
    continue_button = board.draw()
    if board.dead: game_over_button = board.death()
    else:
        if not board.paused: key_outputs()
        game_over_button = None

    for event in pg.event.get():
        if event.type == pg.QUIT:
            pg.quit()
            sys.exit()
        elif event.type == pg.VIDEORESIZE:
            set_sizes()

        elif event.type == pg.MOUSEBUTTONDOWN:
            if game_over_button is not None and game_over_button.collidepoint(event.pos):
                pg.mouse.set_visible(False)
                pg.mouse.set_pos((window.get_width()/2, window.get_height()/3))
                piece_order = Order()
                board = Board()
                delta_time = 0
                prev_time = time
            elif continue_button is not None and continue_button.collidepoint(event.pos):
                board.pause()

        elif event.type == pg.KEYDOWN:
            if event.key in (pg.K_p, pg.K_ESCAPE) : board.pause()

    time = pg.time.get_ticks()
    if board.paused:
        prev_time = time
    else:
        delta_time += time - prev_time
        prev_time = time
    
    if delta_time > (.8-((board.level-1)*.007))**(board.level-1)*1000 and not (board.dead or board.paused):
        if board.check_collision(pg.K_DOWN): board.lock_piece()
        elif not pressed_keys[pg.K_DOWN]: board.move(pg.K_DOWN)
        delta_time = 0
        prev_time = time
