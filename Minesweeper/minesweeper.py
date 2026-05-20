import numpy as np
import numpy.typing as npt
import pygame as pg
import time
import sys
import os

pg.init()
os.chdir(os.path.dirname(os.path.abspath(__file__))) #set working directory to location of this file
clock = pg.time.Clock()
rng = np.random.default_rng()
BOMB_AMOUNT = 100

#constants
MINE = 9
MINE_RED = 10
FLAG = 11
FLAG_WRONG = 12
UNPRESSED = 13

#board size: 30x16 (width x height)
window = pg.display.set_mode((1500, 900), pg.RESIZABLE)

width, height = pg.Surface.get_size(window)
info_screen = mine_field = pg.Surface.subsurface(window, (0, 0, width, height/8))
tile_size = int(width/30) if width/30 <= height*7/8/16 else int(height*7/8/16)
mine_field = pg.Surface.subsurface(window, (0, height/8, 30*tile_size, 16*tile_size))


board = np.full((1, BOMB_AMOUNT), MINE)
board.resize((16, 30))
board = rng.permuted(board)

view_board = np.full((16,30), UNPRESSED)

#loading images
file_names: list[int | str] = [0,1,2,3,4,5,6,7,8, "mine", "mine_red", "flag", "flag_wrong", "unpressed"]
images: list[pg.Surface] = [pg.transform.smoothscale(pg.image.load(f'Tiles/{name}.png' ), (tile_size, tile_size)) for name in file_names]

#caption
pg.display.set_caption("Minesweeper")
pg.display.set_icon(images[MINE])

#variables
first_click: bool = True
dead: bool = False
win: bool = False
bomb_count = np.count_nonzero(board == MINE)
flag_count = 0
start_time = end_time = 0
button_rect: pg.Rect | None = None

def set_sizes():
    global width, height, info_screen, mine_field, tile_size, x_offset
    width, height = pg.Surface.get_size(window)
    tile_size = int(width/30) if width/30 <= height*7/8/16 else int(height*7/8/16)
    x_offset = (width - 30 * tile_size) // 2
    info_screen = pg.Surface.subsurface(window, (x_offset, 0, 30*tile_size, 2*tile_size))
    mine_field = pg.Surface.subsurface(window, (x_offset, 2*tile_size, 30*tile_size, 16*tile_size))
    for img in range(len(images)):
        images[img] = pg.transform.smoothscale(images[img], (tile_size, tile_size))

def calc_numbers(board: npt.NDArray[np.int16]) -> npt.NDArray[np.int16]:
    for x in range(16):
        for y in range(30):
            count = 0
            if board[x][y] == MINE:
                continue
            else:
                for i in range(-1, 2):
                    for j in range(-1, 2):
                        if 0 <= x+i < 16 and 0 <= y+j < 30 and board[x+i][y+j] == MINE:
                            count += 1
                board[x][y] = count
    return board

def draw_board(board: npt.NDArray[np.int16]):
    for x in range(16):
        for y in range(30):
            img: pg.Surface = images[int(board[x][y])]
            mine_field.blit(img, (y*tile_size, x*tile_size))

def reveal_tile(tile: tuple[int, int]):
    x, y = tile
    if not (0 <= x < 30 and 0 <= y < 16) or view_board[y][x] != UNPRESSED:
        return
    
    view_board[y][x] = board[y][x] # Reveal the current tile
    if board[y][x] == MINE:
        death(tile)
        global dead, end_time
        dead = True
        end_time = time.perf_counter() - start_time
        return

    if board[y][x] == 0: # If it's a blank tile, reveal adjacent tiles
        for i in range(-1, 2):
            for j in range(-1, 2):
                if (i != 0 or j != 0):
                    reveal_tile((x + i, y + j))

def death(tile: tuple[int, int]):
    x, y = tile
    view_board[y][x] = MINE_RED

    for x in range(16):
        for y in range(30):
            if board[x][y] == MINE: 
                if view_board[x][y] == UNPRESSED: view_board[x][y] = MINE
            elif view_board[x][y] == UNPRESSED: view_board[x][y] = board[x][y]
            elif view_board[x][y] == FLAG: view_board[x][y] = FLAG_WRONG

def win_show():
    for x in range(16):
        for y in range(30):
            if board[x][y] == MINE: 
                if view_board[x][y] == UNPRESSED: view_board[x][y] = MINE
            elif view_board[x][y] == UNPRESSED: view_board[x][y] = board[x][y]
            elif view_board[x][y] == FLAG: view_board[x][y] = FLAG_WRONG

def count_surrounding(tile: tuple[int, int]) -> int:
    x, y = tile
    count = 0
    for i in range(-1, 2):
        for j in range(-1, 2):
            if 0 <= x+i < 30 and 0 <= y+j < 16 and view_board[y+j][x+i] == FLAG:
                count += 1
    return count

def info():
    font = pg.font.SysFont("verdana", int(1.5*tile_size))
    win_text = font.render("You win!" if win else ("You lose!" if dead else ""), True, (0,0,0))
    win_rect = win_text.get_rect(center = (15*tile_size, tile_size))
    flag_text = font.render(str(bomb_count-flag_count), True, (0,0,0))
    flag_rect = flag_text.get_rect(center = (2*tile_size, tile_size))
    time_text = font.render("0" if first_click else (str(int(end_time))) if win or dead else str(int(time.perf_counter() - start_time)), True, (0,0,0))
    time_rect = time_text.get_rect(center = (28*tile_size, tile_size))
    
    if win or dead:
        global button_rect
        button_rect = win_rect.inflate(tile_size/3, 0)
        pg.draw.rect(info_screen, (150,10, 150), button_rect, 0, 15)
    
    info_screen.blits(((win_text, win_rect), (flag_text, flag_rect), (time_text, time_rect)))
    

set_sizes()

while True:
    clock.tick(120)
    mouse = pg.mouse.get_pos()

    if (width, height) != pg.Surface.get_size(window): set_sizes()
    window.fill((30,30,30))
    info_screen.fill((180,30,200))
    draw_board(view_board)
    info()
    pg.display.update()
    
    for event in pg.event.get():
        if event.type == pg.QUIT:
            pg.quit()
            sys.exit()

        if event.type == pg.MOUSEBUTTONDOWN:
            if pg.Rect((pg.Surface.get_abs_offset(mine_field)), pg.Surface.get_size(mine_field)).collidepoint(mouse):
                tile = ((mouse[0]-x_offset)//tile_size, (mouse[1]-2*tile_size)//tile_size)
                
                if event.button == 1 and view_board[tile[1]][tile[0]] != FLAG:
                    if first_click:
                        for i in range(-1, 2):
                            for j in range(-1, 2):
                                if 0 <= tile[1]+i < 16 and 0 <= tile[0]+j < 30: board[tile[1]+i][tile[0]+j] = 0
                        board = calc_numbers(board)
                        bomb_count = np.count_nonzero(board == MINE)
                        start_time = time.perf_counter()
                        first_click = False
                    
                    if view_board[tile[1]][tile[0]] == UNPRESSED:
                        reveal_tile(tile)
                        
                    elif board[tile[1]][tile[0]] == count_surrounding(tile):
                        for i in range(-1, 2):
                            for j in range(-1, 2): 
                                reveal_tile((tile[0]+i, tile[1]+j))

                if event.button == 3 and view_board[tile[1]][tile[0]] in (FLAG, UNPRESSED):
                    view_board[tile[1]][tile[0]] = FLAG if view_board[tile[1]][tile[0]] != FLAG else UNPRESSED
                    flag_count = np.count_nonzero(view_board == FLAG)
                
                if not dead and np.array_equal(np.isin(view_board, [0,1,2,3,4,5,6,7,8]), np.isin(board, [0,1,2,3,4,5,6,7,8])):
                    win = True
                    end_time = time.perf_counter() - start_time
                    win_show() 
                    
            elif button_rect != None and button_rect.collidepoint(mouse):
                if win or dead:
                    view_board = np.full((16,30), UNPRESSED)
                    board = np.full((1, BOMB_AMOUNT), MINE)
                    board.resize((16, 30))
                    board = rng.permuted(board)
                    first_click = True
                    dead = win = False
                    flag_count = start_time = end_time = 0
                    button_rect = None
            
