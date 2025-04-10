import os
import toolkit as tk
import terminal as tl
from pathlib import Path

TAG_BACK = 0
TAG_DIRY = 1
TAG_FILE = 2

PANEL_SEARCH = 0
PANEL_RECENTS = 1
PANEL_FAVORITES = 2
PANEL_COMPUTER = 3
PANEL_DIRECTORY = 4
panels: list[tl.Panel] = []
_w, _h = 0, 0
mx, my = 0, 0
mouse_on_items: bool = False

cwd:    list[str] = []
home:   list[str] = []
drives: list[str] = []

def win32_get_available_drives() -> list[str]:
    import string
    import ctypes
    out = []
    bitmask = ctypes.cdll.kernel32.GetLogicalDrives()
    for i, letter in enumerate(string.ascii_uppercase):
        if bitmask & (1 << i):
            out.append(f'{letter}:')
    return out

def get_dir_item_list(currentdir: list[str]):
    items = os.listdir("/".join(currentdir))
    directories = []
    files = []
    for item in items:
        path = "/".join(currentdir + [item])
        if os.path.isdir(path):
            directories.append(item)
        else:
            files.append(item)
    return directories, files


def create_panels(width: int, height: int):
    global panels
    # Calculate panel areas
    left_tab_width = min(24, int(width * 0.3333))
    left_tab_yptr = 1

    panels[PANEL_SEARCH] = tl.Panel( # Search
        x = 0,
        y = left_tab_yptr,
        width = left_tab_width,
        height = 3
    )
    left_tab_yptr += panels[0].height

    num_lines = (height -4) // 3
    panels[PANEL_RECENTS] = tl.Panel( # Recents
        x = 0,
        y = left_tab_yptr,
        width = left_tab_width,
        height = num_lines +2
    )
    left_tab_yptr += panels[1].height

    panels[PANEL_FAVORITES] = tl.Panel( # Favorites
        x = 0,
        y = left_tab_yptr,
        width = left_tab_width,
        height = num_lines +2
    )
    left_tab_yptr += panels[2].height

    panels[PANEL_COMPUTER] = tl.Panel( # Computer
        x = 0,
        y = left_tab_yptr,
        width = left_tab_width,
        height = num_lines +2
    )
    left_tab_yptr += panels[3].height

    panels[PANEL_DIRECTORY] = tl.Panel( # Current Directory
        x = left_tab_width +1,
        y = 1,
        width = width - (left_tab_width +1),
        height = height -4
    )

def total_redraw(width: int, height: int):
    global panels
    create_panels(width, height)
    panel_names = ["🔎 Search ", "🚀 Recents ", "⭐ Favorites ", "💽 Computer ", "🗃️ Current Directory "]

    print(tl.fgd(128, 128, 128), end='')
    for i, panel in enumerate(panels):
        tl.draw_panel(panel, name=panel_names[i])


def draw_item_list(dirs, files, item_list_hovered: int = -1):
    global panels
    # print(panels)
    items = panels[-1]
    item_list = [('..', TAG_BACK)] + [(d, TAG_DIRY) for d in dirs] + [(f, TAG_FILE) for f in files]

    # Draw loop
    item_list_str = ""
    for i, item in enumerate(item_list[items.scroll_y : items.scroll_y + items.height -1]):
        icon = "📄" if item[1] == TAG_FILE else "📂" if item[1] == TAG_DIRY else "🔙"
        bgd = tl.bgd(40, 40, 40) if i == item_list_hovered else tl.reset()
        fgd = tl.fgd(128, 128, 128) if item[0][0] in "._" else tl.fgd(255, 255, 255)

        item_list_str += (
            f"{tl.move(items.x +1, items.y +i +1)}{bgd}{icon} "
            f"{fgd}{item[0][items.scroll_x : items.scroll_x + items.width -1]}"
            + (" " * (items.width - len(item[0]) - 6))
        )
    print(item_list_str, end='')

def draw_computer():
    global drives
    panel = panels[PANEL_COMPUTER]
    out = ""

    items = ["Home"] + drives
    for i, item in enumerate(items):
        out += (
            f"{tl.move(panel.x +1, panel.y +i +1)}{tl.fgd(255, 255, 255)}"
            f"{item[:panel.width -1]}"
        )
    print(out, end='')



@tl.on_update(0.025)
def update():
    global _w, _h, currentdir
    global mx, my
    global mouse_on_items

    while ie := tl.read_input():
        if ie['type'] == tl.INPUT_KEYBOARD and ie['key'] == ord('q'):
            return True
        if ie['type'] == tl.INPUT_MOUSE:
            mx, my = ie['x'], ie['y']

            mouse_on_items = False
            if ie['x'] > panels[PANEL_DIRECTORY].x:
                mouse_on_items = True


    width, height = tl.size()
    if width != _w or height != _h:
        _w, _h = width, height
        print(tl.erase_screen(), end='')
        total_redraw(width, height)

    dirs, files = get_dir_item_list(currentdir)
    draw_item_list(dirs, files, item_list_hovered=(my-2) if mouse_on_items else -1)
    draw_computer()

    print(tl.move(0, 0))



# Main entrypoints
# ----------------------------------------------------------------------------------------------------------------------
def select(allow_multiple: bool = True) -> list[str]:
    global panels, _w, _h
    global currentdir
    global cwd, home, drives
    # Areas
    # - Recents
    # - Tagged/Marked
    # - Computer (drives)
    # - current directory files/dirs
    # - Search

    # Buttons
    # - New (folder, file)
    # - Select
    # - Cancel
    panels = [tl.Panel for _ in range(5)]
    cwd    = os.getcwd().split('\\')
    home   = str(Path.home()).split('\\')
    drives = win32_get_available_drives() if os.name == 'nt' else []
    currentdir = cwd


    tl.set_title("File Select")
    print(tl.erase_screen(), end='')
    while True:
        if update():
            break


# def select_directory
# def save



tl.hide_cursor()
select()
print(tl.reset())
tl.show_cursor()