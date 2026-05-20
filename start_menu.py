import sys
import pygame as pg
import os
import subprocess

os.chdir(os.path.dirname(os.path.abspath(__file__))) #set working directory to location of this file
pg.init()
window = pg.display.set_mode((800,800), pg.RESIZABLE)

games: list[str] = ["2048", "Tic-Tac-Toe", "Chess", "Minesweeper", "Tetris"]

def draw_text(text: str, size: int, color: tuple[int, int, int], center_coordinates: tuple[float, float]) -> tuple[pg.Surface,pg.Rect]:
    font = pg.font.SysFont("verdana", size)
    text_surface = font.render(text, True, color)
    text_rect = text_surface.get_rect(center=center_coordinates)
    return text_surface, text_rect

def draw_buttons(games_list: list[str]) -> list[tuple[pg.Rect, str]]:
    rects: list[tuple[pg.Rect, str]] = []
    remaining_height = window.get_height()*.9
    spacing = remaining_height/(len(games_list) + 1)

    #Draw all game buttons
    for i, game in enumerate(games_list):
        text_surface, text_rect = draw_text(game, int(screen_size/15), (255,255,255), (window.get_width()/2, window.get_height()/10 + (i+1)*spacing))
        button_rect = text_rect.inflate(int(screen_size/50), int(screen_size/100))
        pg.draw.rect(window, (74, 8, 9), button_rect, 0, 10)
        window.blit(text_surface, text_rect)
        rects.append((button_rect, game))
    return rects

#Lauch a selected game
def run_game(selected_game: str) -> None:
    pg.quit()

    script_path = f"{selected_game}/{selected_game.lower()}.py"
    try: subprocess.run([sys.executable, script_path])
    except FileNotFoundError: print(f"File not found: {script_path}")

    sys.exit()

while True:
    pg.time.Clock().tick(60)
    pg.display.update()
    screen_size = min(window.get_size())

    window.fill((130, 6, 8))
    window.blit(*draw_text("Choose A Game", int(screen_size/10), (255,255,255), (window.get_width()/2, window.get_height()/10)))

    buttons: list[tuple[pg.Rect, str]] = draw_buttons(games)

    for event in pg.event.get():
        if event.type == pg.QUIT:
            pg.quit()
            sys.exit()
        elif event.type == pg.MOUSEBUTTONDOWN:
            for button, game_name in buttons:
                if button.collidepoint(event.pos):
                    run_game(game_name)
