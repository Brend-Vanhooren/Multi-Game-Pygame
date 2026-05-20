import numpy as np
import numpy.typing as npt
import pygame as pg
import sys
import json
import os

os.chdir(os.path.dirname(os.path.abspath(__file__))) #set working directory to location of this file
rng = np.random.default_rng()

tile_size = 212
height = int(4.5*tile_size)
width = int(4.1*tile_size)

pg.init()
display = pg.display.set_mode((width, height))
clock = pg.time.Clock()
display.fill((204, 192, 179))
icon = pg.image.load("Assets/2048.png")
pg.display.set_caption("2048")
pg.display.set_icon(icon)
score = 0
font = pg.font.SysFont("verdana", int(tile_size/6.5))
score_text = font.render("score: "+ str(score), True, (0,0,0))
dood = False
game_loop = False


sprites: list[pg.Surface] = []
for file in range(15):
  sprites.append(pg.transform.scale(pg.image.load(f'Assets/{2**(file+1)}.png'), (tile_size, tile_size)))
matrix = np.zeros((4,4), int)

def move_left(matrix: npt.NDArray[np.int32], score: int):
  left_matrix = np.zeros((4,4), np.int32)
  vorig = None
  row_index = 0

  for row in matrix:
    columb_index = 0
    for i in row:
      if i != 0:
        if i != vorig:
          left_matrix[row_index][columb_index] = i
          columb_index +=1
          vorig = i
        else:
          left_matrix[row_index][columb_index-1] *= 2
          score += left_matrix[row_index][columb_index-1]
          vorig = None
    row_index +=1
    vorig = None

  try:
    random_place = rng.choice(np.argwhere(left_matrix == 0))
    random_number = np.random.choice([2,4], p=[.9,.1])
    left_matrix[random_place[0]][random_place[1]] = random_number
  except: pass

  return left_matrix, score

def move_right(matrix: npt.NDArray[np.int32], score: int):
  matrix = np.fliplr(matrix)
  matrix, score = move_left(matrix, score)
  matrix = np.fliplr(matrix)
  return(matrix, score)
  
def move_up(matrix: npt.NDArray[np.int32], score: int):
  matrix = np.rot90(matrix)
  matrix, score = move_left(matrix, score)
  matrix = np.rot90(matrix, k=-1)
  return(matrix, score)
  
def move_down(matrix: npt.NDArray[np.int32], score: int):
  matrix = np.rot90(matrix, k=-1)
  matrix, score = move_left(matrix, score)
  matrix = np.rot90(matrix)
  return(matrix, score)

def game_over_check(matrix: npt.NDArray[np.int32]):
  for row in matrix:
    if 0 in row: return False
  
  for i in range(2): # type: ignore
    for row in matrix:
      if np.any(row[:-1] == row[1:]): return False
    matrix = np.transpose(matrix)      
  return True

def draw_rect_text(text:str, size_muliplier: tuple[float,float], position_multiplier: tuple[float,float], font_size_multiplier: float, rect_colour: tuple[int,int,int], text_colour: tuple[int,int,int]):
  font = pg.font.SysFont("verdana", int(tile_size*font_size_multiplier))
  text_render = font.render(text, True, text_colour)
  text_rect = text_render.get_rect(center = (int(width*position_multiplier[0]), int(height*position_multiplier[1])))
  rect = pg.Rect(0,0,int(tile_size*size_muliplier[0]), int(tile_size*size_muliplier[1]))
  rect.center = (int(width*position_multiplier[0]), int(height*position_multiplier[1]))
  pg.draw.rect(display, rect_colour, rect, 0, 7)
  display.blit(text_render, text_rect)
  return rect

def board(matrix: np.typing.NDArray[np.int32]):
  display.fill((186, 172, 159))
  for x in range(4):
      for y in range(4):
        if matrix[x][y] != 0:
          display.blit(sprites[int(np.log2(matrix[x][y])-1)],((tile_size+10)*y, (tile_size+10)*x))
        else:
          pg.draw.rect(display, (203, 191, 178), [(tile_size+10)*y, (tile_size+10)*x, tile_size, tile_size], 0, 6)
  score_text = font.render("score: "+ str(score), True, (0,0,0))
  high_score_text = font.render("highscore: "+str(high_score), True, (0,0,0))
  display.blit(score_text,(10, 4.3*tile_size))
  display.blit(high_score_text,(2*tile_size, 4.3*tile_size) )
  if dood:
    draw_rect_text("You Died :(", (2,.65), (.5,.25), 0.333, (135, 125, 116), (0,0,0))
    dood_button = draw_rect_text("Back to Menu", (1.5,.5), (.5,.5), .2, (135, 125, 116), (0,0,0))
    return dood_button                                                
  
def main_menu():
  display.fill((186, 172, 159))

  draw_rect_text("Main Menu", (2.8, 1), (.5,.2), .5, (203, 191, 178), (0,0,0))
  new_button = draw_rect_text("New Game", (1.5, .5), (.5,.42), .2, (203, 191, 178), (0,0,0))
  continue_button = draw_rect_text("Continue", (1.5, .5), (.5,.6), .2, (203, 191, 178), (0,0,0))
  
  return new_button, continue_button
 
def write_score(score: int):
  with open("data.json", "r") as file:
    data = json.load(file)
  data["high_score"] = int(score)
  with open("data.json", "w") as file:
    json.dump(data, file)

def get_high_score():
  with open("data.json", "r") as file:
    data = json.load(file)
  score = data["high_score"]
  return score

def write_previous_matrix(matrix: np.typing.NDArray[np.int32]):
  with open("data.json", "r") as file:
    data = json.load(file)
  data["previous_matrix"] = (matrix.tolist())
  with open("data.json", "w") as file:
    json.dump(data, file)

def get_previous_matrix():
  with open("data.json", "r") as file:
    data = json.load(file)
  previous_matrix = data["previous_matrix"]
  return previous_matrix

high_score = get_high_score()

while True:
  clock.tick(60)
  pg.display.update()
  mouse = pg.mouse.get_pos()
  
  for event in pg.event.get():
    
    if event.type == pg.QUIT:
      write_previous_matrix(np.array(matrix))
      pg.quit() 
      sys.exit() #close without error
    
    if game_loop:
      back_button = board(matrix)
      if event.type == pg.KEYDOWN :
        if event.key in (pg.K_s, pg.K_DOWN):
          matrix, score = move_down(matrix, score)
        elif event.key in (pg.K_z, pg.K_UP):
          matrix, score = move_up(matrix, score)
        elif event.key in (pg.K_q, pg.K_LEFT):
          matrix, score = move_left(matrix, score)
        elif event.key in (pg.K_d, pg.K_RIGHT):
          matrix, score = move_right(matrix, score)
        
        dood = game_over_check(matrix)
        if event.key == pg.K_y:
          dood = True
          
        if score > high_score:
          high_score = score
          write_score(score)
        
      elif event.type == pg.MOUSEBUTTONDOWN and back_button != None and back_button.collidepoint(mouse): 
        score = 0
        game_loop = False
        matrix = matrix = np.zeros((4,4), int)
        dood = False
    else:
      play_button, continue_button = main_menu()
      if event.type == pg.MOUSEBUTTONDOWN:
        if play_button.collidepoint(mouse):
          game_loop = True
        elif continue_button.collidepoint(mouse):
          matrix = get_previous_matrix()
          game_loop = True