import os
import random
import time
import curses
import asyncio
from obstacles import Obstacle, show_obstacles
from itertools import cycle
from curses_tools import draw_frame, read_controls, get_frame_size
from physics import update_speed
from explosion import explode
from game_scenario import get_garbage_delay_tics, PHRASES


TRASH_DIR = 'files/trash'
OBSTACLES_IN_LAST_COLLISION = []
OBSTACLES = []
COROUTINES = []
YEAR = 1957


async def fire(
        canvas, start_row, start_column, rows_speed=-0.3, columns_speed=0
):

    row, column = start_row, start_column

    canvas.addstr(round(row), round(column), '*')
    await asyncio.sleep(0)

    canvas.addstr(round(row), round(column), 'O')
    await asyncio.sleep(0)
    canvas.addstr(round(row), round(column), ' ')

    row += rows_speed
    column += columns_speed

    symbol = '-' if columns_speed else '|'

    rows, columns = canvas.getmaxyx()
    max_row, max_column = rows - 1, columns - 1

    curses.beep()
    while 0 < row < max_row and 0 < column < max_column:
        canvas.addstr(round(row), round(column), symbol)
        await asyncio.sleep(0)
        canvas.addstr(round(row), round(column), ' ')
        row += rows_speed
        column += columns_speed
        for obstacle in OBSTACLES:
            if obstacle.has_collision(row, column):
                OBSTACLES_IN_LAST_COLLISION.append(obstacle)
                OBSTACLES.remove(obstacle)
                return


async def sleep(tics=1):
    for _ in range(tics):
        await asyncio.sleep(0)


async def show_year(canvas, max_row):
    global YEAR
    information_line = ''
    while True:
        if YEAR in PHRASES:
            information_line = f' - {PHRASES[YEAR]}'
        text_line = canvas.derwin(max_row - 2, 2)
        text_line.addstr(f'Year: {YEAR}{information_line}')
        YEAR += 1
        await sleep(15)


async def fly_garbage(canvas, column, garbage_frame, speed=0.5):
    """Animate garbage, flying from top to bottom. Сolumn position will stay same, as specified on start."""
    rows_number, columns_number = canvas.getmaxyx()

    column = max(column, 0)
    column = min(column, columns_number - 1)

    row = 0

    garbage_height, garbage_width = get_frame_size(garbage_frame)
    obstacle = Obstacle(row, column, garbage_height, garbage_width)
    OBSTACLES.append(obstacle)

    while row < rows_number:
        if obstacle in OBSTACLES_IN_LAST_COLLISION:
            OBSTACLES_IN_LAST_COLLISION.remove(obstacle)
            await explode(canvas, row, column)
            return
        draw_frame(canvas, row, column, garbage_frame)
        obstacle.row = row
        obstacle.column = column
        await asyncio.sleep(0)
        draw_frame(canvas, row, column, garbage_frame, negative=True)
        row += speed
    OBSTACLES.remove(obstacle)


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
    while True:
        await sleep(offset_tics)
        if get_garbage_delay_tics(YEAR):
            await sleep(get_garbage_delay_tics(YEAR))
            with open(os.path.join(TRASH_DIR, random.choice(
                    os.listdir(TRASH_DIR)))) as garbage_file:
                frame = garbage_file.read()
            COROUTINES.append(
                    fly_garbage(canvas, random.randint(1, length), frame)
            )


async def animate_spaceship(canvas):
    with open('./files/rocket_frame_1.txt', 'r') as rocket:
        rocket1 = rocket.read()
    with open('./files/rocket_frame_2.txt', 'r') as rocket:
        rocket2 = rocket.read()
    rocket_height, rocket_length = get_frame_size(rocket1)
    window_height, window_length = canvas.getmaxyx()

    iter_list = [rocket1, rocket1, rocket2, rocket2]

    start_row = window_height // 2 - rocket_height // 2
    start_column = window_length // 2 - rocket_length // 2
    row = start_row
    column = start_column
    border_size = 1
    row_speed = column_speed = 0

    for item in cycle(iter_list):
        rows_direction, columns_direction, space_pressed = read_controls(
            canvas)

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
        if space_pressed and YEAR > 2019:
            COROUTINES.append(fire(canvas, row_position, column_position + 2))
        draw_frame(canvas, row_position, column_position, item)
        await sleep(tics=1)
        draw_frame(canvas, row_position, column_position, item, negative=True)
        for obstacle in OBSTACLES:
            if obstacle.has_collision(row_position, column_position):
                COROUTINES.append(show_game_over(canvas, start_row, start_column))
                return


async def show_game_over(canvas, center_row, center_column):
    with open('files/game_over.txt', 'r') as game_over:
        game_over_frame = game_over.read()
    frame_rows, frame_columns = get_frame_size(game_over_frame)
    while True:
        draw_frame(canvas, center_row - frame_rows / 2, center_column - frame_columns / 2, game_over_frame)
        await sleep()


def draw(canvas):
    global YEAR
    curses.curs_set(False)
    height, length = curses.window.getmaxyx(canvas)
    COROUTINES.append(show_year(canvas, height))
    COROUTINES.append(animate_spaceship(canvas))
    COROUTINES.append(fill_orbit_with_garbage(canvas, length, 1))
    symbol_of_stars = '+*.:'
    border_width = 2
    for _ in range(150):
        COROUTINES.append(blink(
            canvas,
            random.randint(1, height - border_width),
            random.randint(1, length - border_width),
            symbol=random.choice(symbol_of_stars),
            offset_tics=random.randint(0, 8)
        ))

    while True:
        canvas.border()
        for coroutine in COROUTINES.copy():
            try:
                coroutine.send(None)
            except StopIteration:
                COROUTINES.remove(coroutine)
        canvas.refresh()
        time.sleep(0.1)


if __name__ == '__main__':
    curses.update_lines_cols()
    curses.wrapper(draw)
