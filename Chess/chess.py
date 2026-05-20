import numpy as np
import numpy.typing as npt
import pygame as pg
import sys
import os

pg.init()
os.chdir(os.path.dirname(os.path.abspath(__file__))) #set working directory to location of this file
rng = np.random.default_rng()
clock = pg.time.Clock()

tile_size = 115
height = int(8.5*tile_size)
width = int(8*tile_size)

# Load pieces: first all white pieces, then black
pieces_img: list[pg.Surface] = []
for color in ['w', 'b']:
    for piece in ['k', 'q', 'r', 'b', 'n', 'p']:
        pieces_img.append(pg.transform.smoothscale(pg.image.load(f'Pieces/{color}{piece}.png'), (tile_size, tile_size)))

sounds: list[pg.mixer.Sound] = []
for sound in ['move', 'castle', 'capture', 'promote', 'check', 'checkmate']:
    sounds.append(pg.mixer.Sound(f'Sounds/{sound}.wav'))

board_matrix: npt.NDArray[np.str_] = np.array([
    ["br", "bn", "bb", "bq", "bk", "bb", "bn", "br"],
    ["bp", "bp", "bp", "bp", "bp", "bp", "bp", "bp"],
    ["0", "0", "0", "0", "0", "0", "0", "0"],
    ["0", "0", "0", "0", "0", "0", "0", "0"],
    ["0", "0", "0", "0", "0", "0", "0", "0"],
    ["0", "0", "0", "0", "0", "0", "0", "0"],
    ["wp", "wp", "wp", "wp", "wp", "wp", "wp", "wp"],
    ["wr", "wn", "wb", "wq", "wk", "wb", "wn", "wr"]
], dtype=np.str_)
possible_moves: list[tuple[int, int]] = []
pieces_rects: list[pg.Rect] = [] # rects for promotion
previous_tile: tuple[int, int] = ((-1, -1)) # invalid tile
turn = "w" #White starts
checked = False; checkmated = False
king_moves= [(1,1), (-1,-1), (1,-1), (-1,1), (1,0), (0,1), (-1,0), (0,-1)]
white_castle_possible = [True, True, True]; black_castle_possible = [True, True, True] # [king, left_rook, right_rook] True if piece hasn't moved
casling = False; promotion = False; promoted = False
en_passent_pawn: tuple[int, int] | None = None

display = pg.display.set_mode((width, height), pg.RESIZABLE | pg.SRCALPHA)
display.fill((53, 36, 22))
pg.display.set_caption("Chess")
pg.display.set_icon(pieces_img[0]) # White King
restart_button = None

draw_surf = pg.Surface.subsurface(display, (width//2-4*tile_size, 0, 8*tile_size, int(8*tile_size)))

def clicked_tile(pos: tuple[int, int]) -> tuple[int, int]:
    x, y = np.subtract(pos, draw_surf.get_abs_offset())
    return (y // tile_size, x // tile_size)

def board_background() -> None:
    for x in range(8):
        for y in range(8):
            if (x+y)%2 == 0: color = (202, 175, 127)
            else: color = (129, 86, 50)
            pg.draw.rect(draw_surf, color, (y*tile_size, x*tile_size, tile_size, tile_size))
            
def draw_board() -> None:
    for x in range(8):
        for y in range(8):
            piece = board_matrix[x, y]
            if piece != "0":
                piece_img = pieces_img[int(piece[0] == 'b') * 6 + 'kqrbnp'.index(piece[1])]
                draw_surf.blit(piece_img, (y*tile_size, x*tile_size))

def draw_possible_moves(mogelijke_moves: list[tuple[int, int]]) -> None:
    transparent_surface = pg.Surface((width, height), pg.SRCALPHA)
    transparent_surface.fill((0,0,0,0))
    for move in mogelijke_moves:
        x, y = move
        pg.draw.circle(transparent_surface, (200, 200, 200, 190), (y*tile_size + tile_size/2, x*tile_size + tile_size/2), tile_size//6.8)
    display.blit(transparent_surface, (width//2-4*tile_size, 0))

# Needs to be updated for en passant
def pawn(pos: tuple[int, int]) -> list[tuple[int, int]]:
    x, y = pos
    color = board_matrix[x, y][0]  # 'w' or 'b'
    possible_moves: list[tuple[int, int]] = []
    global en_passent_pawn
    # White Pawn
    if color == "w":
        if 0 <= x-1 <= 7 and board_matrix[(x-1,y)] =="0": 
            possible_moves.append((x-1,y))
            if x == 6 and 0 <= x-2 <= 7 and board_matrix[(x-2,y)] == "0": 
                possible_moves.append((x-2,y))
        if 0 <= x-1 <= 7 and 0 <= y-1 <= 7 and board_matrix[(x-1,y-1)][0] == "b":
            possible_moves.append((x-1,y-1))
        if 0 <= x-1 <= 7 and 0 <= y+1 <= 7 and board_matrix[(x-1,y+1)][0] == "b":
            possible_moves.append((x-1,y+1))


    # Black Pawn
    elif color == "b":
        if 0 <= x+1 <= 7 and board_matrix[(x+1, y)] == "0":
            possible_moves.append((x+1, y))
            if x == 1 and 0 <= x+2 <= 7 and board_matrix[(x+2, y)] == "0":
                possible_moves.append((x+2, y))
                en_passent_pawn = (x+2,y)
        if 0 <= x+1 <= 7 and 0 <= y-1 <= 7 and board_matrix[(x+1, y-1)][0] == "w":
            possible_moves.append((x+1, y-1))
        if 0 <= x+1 <= 7 and 0 <= y+1 <= 7 and board_matrix[(x+1, y+1)][0] == "w":
            possible_moves.append((x+1, y+1))
    return possible_moves

def rook(pos: tuple[int, int]) -> list[tuple[int, int]]:
    x, y = pos
    possible_moves: list[tuple[int, int]] = []
    color = board_matrix[x, y][0]

    # Up
    for i in range(1, 8):
        test_x = x - i
        if 0 <= test_x <= 7:
            piece = board_matrix[test_x, y]
            if piece == "0":
                possible_moves.append((test_x, y))
            elif piece[0] != color:
                possible_moves.append((test_x, y))
                break
            else: break
        else: break

    # Down
    for i in range(1, 8):
        test_x = x + i
        if 0 <= test_x <= 7:
            piece = board_matrix[test_x, y]
            if piece == "0":
                possible_moves.append((test_x, y))
            elif piece[0] != color:
                possible_moves.append((test_x, y))
                break
            else: break
        else: break

    # Right
    for i in range(1, 8):
        test_y = y + i
        if 0 <= test_y <= 7:
            piece = board_matrix[x, test_y]
            if piece == "0":
                possible_moves.append((x, test_y))
            elif piece[0] != color:
                possible_moves.append((x, test_y))
                break
            else: break
        else: break

    # Left
    for i in range(1, 8):
        test_y = y - i
        if 0 <= test_y <= 7:
            piece = board_matrix[x, test_y]
            if piece == "0":
                possible_moves.append((x, test_y))
            elif piece[0] != color:
                possible_moves.append((x, test_y))
                break
            else: break
        else: break

    return possible_moves

def bishop(pos: tuple[int, int]) -> list[tuple[int, int]]:
    x, y = pos
    possible_moves: list[tuple[int, int]] = []
    color = board_matrix[x, y][0]

    # Up-Right
    for i in range(1, 8):
        test_x = x - i
        test_y = y + i 
        if 0 <= test_y <= 7 and 0 <= test_x <= 7:
            piece = board_matrix[test_x, test_y]
            if piece == "0":
                possible_moves.append((test_x, test_y))
            elif piece[0] != color:
                possible_moves.append((test_x, test_y))
                break
            else: break
        else: break

    # Up-Left
    for i in range(1, 8):
        test_x = x - i
        test_y = y - i
        if 0 <= test_y <= 7 and 0 <= test_x <= 7:
            piece = board_matrix[test_x, test_y]
            if piece == "0":
                possible_moves.append((test_x, test_y))
            elif piece[0] != color:
                possible_moves.append((test_x, test_y))
                break
            else: break
        else: break

    # Down-Right
    for i in range(1, 8):
        test_y = y + i
        test_x = x + i
        if 0 <= test_y <= 7 and 0 <= test_x <= 7:
            piece = board_matrix[test_x, test_y]
            if piece == "0":
                possible_moves.append((test_x, test_y))
            elif piece[0] != color:
                possible_moves.append((test_x, test_y))
                break
            else: break
        else: break

    # Down-Left
    for i in range(1, 8):
        test_x = x + i
        test_y = y - i
        if 0 <= test_y <= 7 and 0 <= test_x <= 7:
            piece = board_matrix[test_x, test_y]
            if piece == "0":
                possible_moves.append((test_x, test_y))
            elif piece[0] != color:
                possible_moves.append((test_x, test_y))
                break
            else: break
        else: break
    
    return possible_moves

def knight(pos: tuple[int, int]) -> list[tuple[int, int]]:
    x, y = pos
    possible_moves: list[tuple[int, int]] = []
    color = board_matrix[x, y][0]

    knight_moves = [(2, 1), (2, -1), (-2, 1), (-2, -1), (1, 2), (1, -2), (-1, 2), (-1, -2)]

    # Check knight_moves relative to knight's position
    for a, b in knight_moves:
        new_x = x + a
        new_y = y + b
        if 0 <= new_y <= 7 and 0 <= new_x <= 7:
            piece = board_matrix[new_x, new_y]
            if piece == "0" or piece[0] != color:
                possible_moves.append((new_x, new_y))

    return possible_moves

def queen(pos: tuple[int, int]) -> list[tuple[int, int]]:
    # Combine moves of rook and bischop
    return (rook(pos) + bishop(pos))

def king(pos: tuple[int, int]) -> list[tuple[int, int]]:
    global board_matrix
    x, y = pos
    possible_moves: list[tuple[int, int]] = []
    color = board_matrix[x, y][0]
    # Check king_moves relative to king's position 
    for a, b in king_moves:
        new_x = x + a
        new_y = y + b
        if 0 <= new_y <= 7 and 0 <= new_x <= 7:
            piece = board_matrix[new_x, new_y]
            if piece == "0" or piece[0] != color:
                possible_moves.append((new_x, new_y))

    if {'w': white_castle_possible, 'b': black_castle_possible}[color][0] == True and not checked:
        if {'w': white_castle_possible, 'b': black_castle_possible}[color][1] == True:
            if (x, y-1) in possible_moves:
                if board_matrix[x, y-2] == "0" and board_matrix[x, y-3] == "0":
                    possible_moves.append((x, y-2)) # Left castle

        if {'w': white_castle_possible, 'b': black_castle_possible}[color][2] == True:
            if (x, y+1) in possible_moves:
                if board_matrix[x, y+2] == "0":
                    possible_moves.append((x, y+2)) # Right castle
        
    return possible_moves

def check(color:  str) -> bool:
    king_pos = np.argwhere(board_matrix == f"{color}k")  # Find the king's position
    if king_pos.size == 0: # King not found
        return True
    king_pos = (king_pos[0][0], king_pos[0][1])
    piece_moves: list[tuple[int, int]] = []
    for x in range(8):
        for y in range(8):
            if board_matrix[x, y] != "0" and board_matrix[x, y][0] != color:
                piece = board_matrix[x, y]
                if piece[1] in piece_functions:
                    piece_moves = piece_functions[piece[1]]((x, y)) + piece_moves

    if king_pos in piece_moves: return True
    return False

def checkmate(color: str) -> bool: 
    all_possible_moves: list[tuple[int, int]] = []

    for x in range(8):
        for y in range(8):
            if board_matrix[x, y] != "0" and board_matrix[x, y][0] == color:
                all_possible_moves = get_possible_moves((x, y)) + all_possible_moves

    if check(color) and len(all_possible_moves) == 0: return True
    return False

def turn_switch(current_turn: str) -> str:
    return "b" if current_turn == "w" else "w"

def draw_turn(turn: str) -> None:
    font = pg.font.SysFont("verdana", tile_size//4)
    text = font.render(f"Turn: {'White' if turn == 'w' else 'Black'}", True, (255, 255, 255))
    draw_surf.blit(text, (tile_size//10, tile_size*8.1))

def draw_check() -> None:
    font = pg.font.SysFont("verdana", tile_size//4)
    text = font.render("Check!", True, (255, 255, 255))
    draw_surf.blit(text, (tile_size*7, tile_size*8.1))

def draw_checkmate() -> pg.Rect:
    font = pg.font.SysFont("verdana", tile_size//2)
    text = font.render(f"Checkmate!, {'Black' if turn == 'w' else 'White'} wins!", True, (255, 255, 255))
    text_rect = text.get_rect(center = (width//2, height//2))
    rect = pg.Rect(text_rect.x - 10, text_rect.y - 10, text_rect.width + 20, text_rect.height + 20)
    pg.draw.rect(draw_surf, (53, 36, 22), rect, 0, 7)
    draw_surf.blit(text, text_rect)

    button_text = font.render("Restart", True, (255,255,255))
    button_text_rect = button_text.get_rect(center = (width // 2, height // 2 + tile_size))
    button_rect = pg.Rect(button_text_rect.x - 10, button_text_rect.y - 10, button_text_rect.width + 20, button_text_rect.height + 20)
    pg.draw.rect(draw_surf, (53, 36, 22), button_rect, 0, 7)
    draw_surf.blit(button_text, button_text_rect)

    return button_rect

def draw_promotion() -> list[pg.Rect]:
    pieces_rects: list[pg.Rect] = []
    
    font = pg.font.SysFont("verdana", tile_size//3)
    text = font.render("Promotion", True, (255, 255, 255))
    text_rect = text.get_rect(center = (width // 2, height // 4))
    rect = pg.Rect(text_rect.x - 10, text_rect.y - 10, text_rect.width + 20, text_rect.height + 20)
    pg.draw.rect(draw_surf, (53, 36, 22), rect, 0, 7)
    draw_surf.blit(text, text_rect)

    img_rect = pg.Rect(0, 0, 4.1*tile_size, 1.1*tile_size)
    img_rect.center = (width // 2, int(height // 2.6))
    pg.draw.rect(draw_surf, (53, 36, 22), img_rect, 0, 7)
    
    for i, piece in enumerate(['q', 'r', 'b', 'n']):
        piece_img = pieces_img[int(turn == 'b') * 6 + 'kqrbnp'.index(piece)]
        piece_rect = piece_img.get_rect(center = (img_rect.x + (i+.55) * tile_size, height // 2.6))
        draw_surf.blit(piece_img, piece_rect)
        pieces_rects.append(piece_rect)
    return pieces_rects

def get_possible_moves(pos: tuple[int, int]) -> list[tuple[int, int]]:
    color = board_matrix[pos][0]
    piece = board_matrix[pos][1]
    possible_moves = piece_functions[piece](pos)
    legal_moves: list[tuple[int, int]] = []

    for move in possible_moves:
        # Simulate move
        temp = board_matrix[move]
        board_matrix[move] = f'{color}{piece}'
        board_matrix[pos] = "0"
        if not check(color):
            legal_moves.append(move)
        # Restore board
        board_matrix[pos] = f'{color}{piece}'
        board_matrix[move] = temp

    return legal_moves

piece_functions = {'p': pawn, 'r': rook, 'n': knight, 'b': bishop, 'q': queen,'k': king}


fullscreen = False

while True:
    clock.tick(60) #set FPS
    mouse = pg.mouse.get_pos() #get mouse position

    #resize_images and screen
    width, height = pg.Surface.get_size(display)
    tile_size = int(width/8 if width <= height else height/8.5)
    for i in range(len(pieces_img)):
        pieces_img[i] = pg.transform.smoothscale(pieces_img[i], (tile_size, tile_size))
    
    draw_surf = pg.Surface.subsurface(display, (width//2-4*tile_size, 0, 8*tile_size, int(8.5*tile_size)))

    # Draw board and pieces
    display.fill((53, 36, 22))
    board_background()
    draw_board()
    draw_possible_moves(possible_moves)
    draw_turn(turn)
    if checkmated: restart_button = draw_checkmate()
    if checked: draw_check()
    
    pg.display.update()

    for event in pg.event.get():
        if event.type == pg.QUIT:
            pg.quit()
            sys.exit()
        if event.type == pg.KEYDOWN:
            if event.key == pg.K_t:
                turn = turn_switch(turn)
            elif event.key == pg.K_F11:
                pg.display.toggle_fullscreen()
                fullscreen = not fullscreen

        if event.type == pg.MOUSEBUTTONDOWN:
            if checkmated and restart_button != None and restart_button.collidepoint(mouse):
                # Reset game
                board_matrix = np.array([
                    ["br", "bn", "bb", "bq", "bk", "bb", "bn", "br"],
                    ["bp", "bp", "bp", "bp", "bp", "bp", "bp", "bp"],
                    ["0", "0", "0", "0", "0", "0", "0", "0"],
                    ["0", "0", "0", "0", "0", "0", "0", "0"],
                    ["0", "0", "0", "0", "0", "0", "0", "0"],
                    ["0", "0", "0", "0", "0", "0", "0", "0"],
                    ["wp", "wp", "wp", "wp", "wp", "wp", "wp", "wp"],
                    ["wr", "wn", "wb", "wq", "wk", "wb", "wn", "wr"]
                ], dtype=np.str_)
                possible_moves = []
                previous_tile = (-1, -1)
                turn = 'w'
                checked = False
                checkmated = False
                white_castle_possible = [True, True, True]
                black_castle_possible = [True, True, True]
                                            
            else: # If not checkmated
                tile = clicked_tile(mouse) #get clicked tile
                if not np.all((0 <= np.array(tile)) & (np.array(tile) <= 7)): continue #check if clicked on board

                if tile in possible_moves: #if clicked tile is a possible move, move piece to that tile
                    if board_matrix[tile] != "0": pg.mixer.Sound.play(sounds[2]) #if clicked tile is occupied, play capture.wav
                    color = board_matrix[previous_tile][0]

                    if board_matrix[previous_tile][1] == "k": {'w': white_castle_possible, 'b': black_castle_possible}[color][0] = False #king has moved
                        
                    elif board_matrix[previous_tile][1] == "r":
                        if previous_tile[1] == 0: {'w': white_castle_possible, 'b': black_castle_possible}[color][1] = False #left rook has moved
                        elif previous_tile[1] == 7: {'w': white_castle_possible, 'b': black_castle_possible}[color][2] = False #right rook has moved
                    
                    elif board_matrix[previous_tile][1] == "p" and (tile[0] == 0 or tile[0] == 7): #pawn promotion
                        promotion = True
                        while promotion:
                            pieces_rects = draw_promotion() #draw promotion rects
                            pg.display.update()
                            for event in pg.event.get():
                                if event.type == pg.QUIT:
                                    pg.quit()
                                    sys.exit()
                                elif event.type == pg.MOUSEBUTTONDOWN:
                                    mouse = pg.mouse.get_pos()
                                    for i, rect in enumerate(pieces_rects):
                                        if rect.collidepoint(mouse):
                                            color = board_matrix[previous_tile][0]
                                            board_matrix[tile] = f"{color}{'qrbn'[i]}"
                                            board_matrix[previous_tile] = "0"
                                            previous_tile = (-1, -1)
                                            turn = turn_switch(turn)
                                            possible_moves = []
                                            promotion = False
                                            promoted = True

                    if abs(tile[1] - previous_tile[1]) == 2 and tile[0] == previous_tile[0] and board_matrix[previous_tile][1] == "k" and not promoted: #castling
                        casling = True
                        pg.mixer.Sound.play(sounds[1]) #play castle.wav
                        if tile[1] == 2: #left castle 
                            board_matrix[tile[0], 3] = f"{color}r" #move left rook to castle position
                            board_matrix[tile[0], 0] = "0" #remove left rook from original position
                        elif tile[1] == 6: #right castle 
                            board_matrix[tile[0], 5] = f"{color}r" #move right rook to castle position
                            board_matrix[tile[0], 7] = "0" #remove right rook from original position

                    if not promoted: #if promotion didn't handle move
                        board_matrix[tile] = board_matrix[previous_tile]
                        board_matrix[previous_tile] = "0"
                        previous_tile = (-1, -1)
                        possible_moves = []
                        turn = turn_switch(turn) #switch turn after a valid move
                    
                    checked = check(turn)
                    if not checkmated: checkmated = checkmate(turn)
                    if checkmated:      pg.mixer.Sound.play(sounds[5]) #play checkmate.wav
                    elif checked:       pg.mixer.Sound.play(sounds[4]) #check if the move puts the king in check, play check.wav
                    elif promoted:      pg.mixer.Sound.play(sounds[3]) # play promote.wav
                    elif not casling:   pg.mixer.Sound.play(sounds[0]) # play move.wav
                    
                    casling = False; promoted = False #reset casling en promoted
                    
                elif board_matrix[tile] == "0": #if clicked tile is empty, reset possible moves and previous tile
                    possible_moves = []
                    previous_tile = (-1, -1)
                elif board_matrix[tile] != "0" and board_matrix[tile][0] == turn: #if clicked tile is occupied by turn's piece
                    if tile == previous_tile: #reset possible moves and previous tile when clicking the smame tile
                        possible_moves = []
                        previous_tile = (-1, -1)

                    else: # check clicked piece and get possible moves
                        possible_moves = get_possible_moves(tile)
                        previous_tile = tile