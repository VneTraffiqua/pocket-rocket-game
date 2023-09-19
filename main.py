import os
import random
import time
import curses
import asyncio
from itertools import cycle
from fire_animation import fire
from curses_tools import draw_frame, read_controls, get_frame_size
from space_garbage import fly_garbage
from physics import update_speed


TIC_TIMEOUT = 0.1
TRASH_DIR = 'files/trash'


async def sleep(tics=1):
    for _ in range(tics):
        await asyncio.sleep(0)


async def blink(canvas, row, column, symbol, offset_tics):
    while True:
        canvas.addstr(row, column, symbol, curses.A_DIM)
        await sleep(offset_tics)
        canvas.addstr(row, column, symbol)
        await sleep(offset_tics)
        canvas.addstr(row, column, symbol, curses.A_BOLD)
        await sleep(offset_tics)
        canvas.addstr(row, column, symbol)
        await sleep(tics=1)


async def fill_orbit_with_garbage(canvas, length, offset_tics):
    global coroutines
    while True:
        await sleep(offset_tics)
        with open(os.path.join(TRASH_DIR, random.choice(
                os.listdir(TRASH_DIR)))) as garbage_file:
            frame = garbage_file.read()
        coroutines.append(
                fly_garbage(canvas, random.randint(1, length), frame)
        )


async def animate_spaceship(canvas):
    global coroutines
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
    row_speed = column_speed = 0

    for item in cycle(iter_list):
        rows_direction, columns_direction, space_pressed = read_controls(
            canvas)
        if space_pressed:
            coroutines.append(fire(canvas, row, column + 2))
        row_speed, column_speed = update_speed(
            row_speed, column_speed, rows_direction, columns_direction
        )
        row = row + row_speed
        column = column + column_speed
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
        await sleep(tics=1)
        draw_frame(canvas, row_position, column_position, item, negative=True)


def draw(canvas):
    curses.curs_set(False)
    height, length = curses.window.getmaxyx(canvas)
    row, column = height, length

    global coroutines
    coroutines.append(animate_spaceship(canvas))
    coroutines.append(fill_orbit_with_garbage(canvas, length, 10))

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
        canvas.border()
        for coroutine in coroutines.copy():
            try:
                coroutine.send(None)
            except StopIteration:
                coroutines.remove(coroutine)
        canvas.refresh()
        time.sleep(0.1)


if __name__ == '__main__':
    coroutines = []
    curses.update_lines_cols()
    curses.wrapper(draw)


