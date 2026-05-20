import numpy as np
import numpy.typing as npt
import pygame as pg
import sys
import os

pg.init()
os.chdir(os.path.dirname(os.path.abspath(__file__))) #set working directory to location of this file
rng = np.random.default_rng()
clock = pg.time.Clock()

tile_size = 250
height = int(3*tile_size+10*4)
width = int(3*tile_size+10*4)
move = 0
matrix = np.zeros((3,3), int)
winner = False
restart_button = None

display = pg.display.set_mode((width, height))
display.fill((150,150,150))

def draw_rect_text(text:str, size_muliplier: tuple[float,float], position_multiplier: tuple[float,float], font_size_multiplier: float, rect_colour: tuple[int,int,int], text_colour: tuple[int,int,int]):
  font = pg.font.SysFont("verdana", int(tile_size*font_size_multiplier))
  text_render = font.render(text, True, text_colour)
  text_rect = text_render.get_rect(center = (int(width*position_multiplier[0]), int(height*position_multiplier[1])))
  rect = pg.Rect(0,0,int(tile_size*size_muliplier[0]), int(tile_size*size_muliplier[1]))
  rect.center = (int(width*position_multiplier[0]), int(height*position_multiplier[1]))
  pg.draw.rect(display, rect_colour, rect, 0, 7)
  display.blit(text_render, text_rect)
  return rect

#Draw the board
def board():
    display.fill((201,102,158))
    for y in range(3):
        for x in range(3):
            pg.draw.rect(display, (248,204,255), (x*tile_size+(x+1)*10, y*tile_size+(y+1)*10, tile_size, tile_size), 0, 7)
            if matrix[x][y] == 1: 
                pg.draw.line(display, (104,150,170), (x*tile_size+(x+1)*10+30, y*tile_size+(y+1)*10+30), ((x+1)*(tile_size+10)-30, (y+1)*(tile_size+10)-30), 10)
                pg.draw.line(display, (104,150,170), (x*tile_size+(x+1)*10+30, (y+1)*(tile_size+10)-30), ((x+1)*(tile_size+10)-30, y*tile_size+(y+1)*10+30), 10)
            if matrix[x][y] == 2: pg.draw.circle(display, (104,150,170), ((x+1)*10+x*tile_size+tile_size/2, (y+1)*10+y*tile_size+tile_size/2), tile_size/2.5, 8)

#Check if somebody wone the game
def winner_check(matrix: npt.NDArray[np.int32]):
    diagonal: list[int] = []
    for i in range(2):
        for y in range(3):
            diagonal.append(matrix[y][y])
        for row in matrix:
            if np.array_equal(row, [1,1,1]) or np.array_equal(diagonal, [1,1,1]): return 1
            elif np.array_equal(row, [2,2,2]) or np.array_equal(diagonal, [2,2,2]): return 2
        diagonal = []
        matrix = np.transpose(np.fliplr(matrix))
    return False
    
while True:
    clock.tick(60)
    pg.display.update()
    mouse = pg.mouse.get_pos()
    
    board()
    
    for event in pg.event.get():
        if event.type == pg.QUIT:
            pg.quit()
            sys.exit()
        if event.type == pg.MOUSEBUTTONDOWN:
            if restart_button != None and restart_button.collidepoint(mouse):
                matrix = np.zeros((3,3), int)
                restart_button = None
            else: 
                if mouse[0] <= width/3: row = 0
                elif mouse[0] >= width*2/3: row = 2
                else: row = 1
                
                if mouse[1] <= height/3: column = 0
                elif mouse[1] >= height*2/3: column = 2
                else: column = 1
                
                if move%2 == 0: matrix[row][column] = 1
                else: matrix[row][column] = 2
                move += 1
            
            winner = winner_check(matrix)
    if winner == 1: draw_rect_text("Crose wins", (2.2,.8), (.5,.5), .4, (145,62,250), (9,250, 137)); restart_button = draw_rect_text("Restart", (2,.7), (.5,.75), .4, (145,62,250), (9,250, 137))
    elif winner == 2: draw_rect_text("Circle wins", (2.2,.8), (.5,.5), .4, (145,62,250), (9,250, 137)); restart_button = draw_rect_text("Restart", (2.2,.8), (.5,.25), .4, (145,62,250), (9,250, 137))
    elif np.all(matrix): 
        draw_rect_text("Draw", (2.2,.8), (.5,.5), .4, (145,62,250), (9,250, 137))
        restart_button = draw_rect_text("Restart", (2.2,.8), (.5,.25), .4, (145,62,250), (9,250, 137))
            
