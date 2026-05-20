
# Multi-Game-Pygame

This is a python game that uses pygame to show images. It has the folowing games:

- 2048
- Chess (missing "en passent")
- Minesweeper
- Tetris
- Tic-Tac-Toe




## Authors

- [Brend Vanhooren](https://www.github.com/Brend-Vanhooren)


## Deployment

Install all files (README not required) and keep them in the same structure as this repo. This is needed because otherwise the script will not find the games.

This program requires pygame and numpy to be installed. At the time of writing, the newest python version that support this is 3.13

To install the libraries, run the following commands:

```bash
py -3.13 -m pip install --upgrade pip
pip install numpy pygame

#If you have multiple versions of python and are on windows:
py -3.13 -m pip install numpy pygame
```

To run the games, simply start the "start_menu.py" file:

```bash
py -3.13 "C:\path\to\script\start_menu.py"
```
