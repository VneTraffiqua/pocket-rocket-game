import random
import time
import curses
import asyncio
from itertools import cycle
from fire_animation import fire
from curses_tools import draw_frame, read_controls, get_frame_size

TIC_TIMEOUT = 0.1


async def blink(canvas, row, column, symbol, offset_tics):
    while True:
        canvas.addstr(row, column, symbol, curses.A_DIM)
        [await asyncio.sleep(0) for _ in range(offset_tics)]
        canvas.addstr(row, column, symbol)
        [await asyncio.sleep(0) for _ in range(7)]
        canvas.addstr(row, column, symbol, curses.A_BOLD)
        [await asyncio.sleep(0) for _ in range(2)]
        canvas.addstr(row, column, symbol)
        [await asyncio.sleep(0) for _ in range(4)]


async def animate_spaceship(canvas, row, column):
    with open('./files/rocket_frame_1.txt', 'r') as rocket:
        rocket1 = rocket.read()
    with open('./files/rocket_frame_2.txt', 'r') as rocket:
        rocket2 = rocket.read()
    rocket_height, rocket_length = get_frame_size(rocket1)
    window_height, window_length = canvas.getmaxyx()

    iter_list = [rocket1, rocket1, rocket2, rocket2]

    row = window_height // 2 - rocket_height // 2
    column = window_length // 2 - rocket_length // 2
    border_size = 1

    for item in cycle(iter_list):
        rows_direction, columns_direction, space_pressed = read_controls(
            canvas)
        row = row + rows_direction
        column = column + columns_direction
        row_position = min(
            window_height - rocket_height - border_size,
            row
        )
        column_position = min(
            window_length - rocket_length - border_size,
            column
        )
        row_position = max(1, row_position)
        column_position = max(1, column_position)
        draw_frame(canvas, row_position, column_position, item)
        await asyncio.sleep(0)
        draw_frame(canvas, row_position, column_position, item, negative=True)


def draw(canvas):
    curses.curs_set(False)
    height, length = curses.window.getmaxyx(canvas)
    row, column = height, length
    canvas.border()
    coroutines = []
    coroutines.append(animate_spaceship(canvas, row, column))
    symbol_of_stars = '+*.:'
    border_width = 2
    for _ in range(150):
        coroutines.append(blink(
            canvas,
            random.randint(1, height - border_width),
            random.randint(1, length - border_width),
            symbol=random.choice(symbol_of_stars),
            offset_tics=random.randint(0, 8)
        ))
    while True:
        try:
            for coroutine in coroutines:
                coroutine.send(None)
            canvas.refresh()
            time.sleep(0.1)
        except StopIteration:
            coroutines.pop()
            continue


if __name__ == '__main__':
    curses.update_lines_cols()
    curses.wrapper(draw)


