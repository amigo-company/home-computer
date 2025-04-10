# Terminal
# Author: Daniel Ervilha
# Type: lib

# References:
# - https://gist.github.com/fnky/458719343aabd01cfb17a3a4f7296797 (ANSI codes)
# - https://learn.microsoft.com/en-us/windows/console/input-record-str (Windows API INPUT_RECORD)
ABOUT = """
"""
import os
import time
from dataclasses import dataclass, field
from datetime import datetime

# Dataclasses
# ----------------------------------------------------------------------------------------------------------------------
@dataclass(slots=True)
class Panel:
    x: int = 0
    y: int = 0
    width: int = 0
    height: int = 0
    scroll_x: int = 0
    scroll_y: int = 0


# ANSI codes
# ----------------------------------------------------------------------------------------------------------------------
def reset():
    return "\033[0m"

def bold():
    return "\033[1m"
def underline():
    return "\033[4m"
def inverse():
    return "\033[7m"

def erase_line():
    return "\033[2K"
def erase_screen():
    return "\033[2J"
def erase_saved_lines():
    return "\033[2J"

def move(x: int, y: int):
    return f"\033[{y +1};{x +1}H"

def bgd(r: int, g: int, b: int):
    return f"\033[48;2;{r};{g};{b}m"
def fgd(r: int, g: int, b: int):
    return f"\033[38;2;{r};{g};{b}m"


# General
# ----------------------------------------------------------------------------------------------------------------------
def size() -> tuple[int, int]:
    ts = os.get_terminal_size()
    return ts.columns, ts.lines

# Terminal @on_update decorator
_TIME_ELAPSED_SAMPLE_COUNT: int = 8
_time_elapsed_ptr: int = 0
_time_elapsed_samples: list[float] = [0.05 for _ in range(_TIME_ELAPSED_SAMPLE_COUNT)]
def on_update(frametime: float): 
    def decorator(func):
        def wrapper(*args, **kwargs):
            global _time_elapsed_ptr, _time_elapsed_samples
            t0 = datetime.now()
            call_result = func(*args, **kwargs)
            _time_elapsed_samples[_time_elapsed_ptr] = float((datetime.now() - t0).microseconds) / 1_000_000
            time.sleep(max(0, frametime - (sum(_time_elapsed_samples) / _TIME_ELAPSED_SAMPLE_COUNT)))
            _time_elapsed_ptr = (_time_elapsed_ptr +1) &7
            return call_result
        return wrapper
    return decorator

'┌┐└┘'
def draw_panel(panel: Panel, name: str = None):
    out = ""

    out += f"{move(panel.x, panel.y)}" '╭' + ('─' * (panel.width -2)) + '╮'
    for i in range(1, panel.height -1):
        out += f"{move(panel.x, panel.y +i)}" '│' + (' ' * (panel.width -2)) + '│'
    out += f"{move(panel.x, panel.y + panel.height -1)}" '╰' + ('─' * (panel.width -2)) + '╯'

    if name:
        out += f"{move(panel.x +1, panel.y)}{name[:panel.width -1]}"

    print(out, end='')






# Signal handling
# ----------------------------------------------------------------------------------------------------------------------


# Input handling
# ----------------------------------------------------------------------------------------------------------------------
INPUT_KEYBOARD = 1
INPUT_MOUSE = 2

# Windows specific implementations
if os.name == 'nt':
    import ctypes
    import ctypes.wintypes as wintypes

    # Constants from Windows API
    _STD_INPUT_HANDLE = -10
    _STD_OUTPUT_HANDLE = -11
    _ENABLE_MOUSE_INPUT = 0x0010
    _ENABLE_EXTENDED_FLAGS = 0x0080
    _ENABLE_WINDOW_INPUT = 0x0008
    _FROM_LEFT_1ST_BUTTON_PRESSED = 0x0001
    _RIGHTMOST_BUTTON_PRESSED = 0x0002
    _MOUSE_MOVED = 0x0001
    _MOUSE_WHEELED = 0x0004

    # Structs from Windows API
    class COORD(ctypes.Structure):
        _fields_ = [("X", wintypes.SHORT), ("Y", wintypes.SHORT)]

    class KEY_EVENT_RECORD(ctypes.Structure):
        _fields_ = [
            ("bKeyDown", wintypes.BOOL),
            ("wRepeatCount", wintypes.WORD),
            ("wVirtualKeyCode", wintypes.WORD),
            ("wVirtualScanCode", wintypes.WORD),
            ("uChar", wintypes.WCHAR),
            ("dwControlKeyState", wintypes.DWORD),
        ]

    class MOUSE_EVENT_RECORD(ctypes.Structure):
        _fields_ = [
            ("dwMousePosition", COORD),
            ("dwButtonState", wintypes.DWORD),
            ("dwControlKeyState", wintypes.DWORD),
            ("dwEventFlags", wintypes.DWORD),
        ]

    class EVENT_UNION(ctypes.Union):
        _fields_ = [
            ("KeyEvent", KEY_EVENT_RECORD),
            ("MouseEvent", MOUSE_EVENT_RECORD),
        ]

    class INPUT_RECORD(ctypes.Structure):
        _fields_ = [
            ("EventType", wintypes.WORD),
            ("Event", EVENT_UNION),
        ]

    # kernel32 config
    kernel32 = ctypes.windll.kernel32
    handle = kernel32.GetStdHandle(_STD_INPUT_HANDLE)
    kernel32.SetConsoleMode(
        handle,
        _ENABLE_EXTENDED_FLAGS | _ENABLE_MOUSE_INPUT | _ENABLE_WINDOW_INPUT
    )

    # Input
    _forced_input_stack = []
    def force_input(event: dict[str, int]):
        _forced_input_stack.append(event)

    def read_input() -> dict[str, int]:
        if _forced_input_stack:
            return _forced_input_stack.pop()

        record = INPUT_RECORD()
        count = wintypes.DWORD()

        kernel32.PeekConsoleInputW(handle, ctypes.byref(record), 1, ctypes.byref(count))
        if not count.value:
            return None

        kernel32.ReadConsoleInputW(handle, ctypes.byref(record), 1, ctypes.byref(count))
        if record.EventType == INPUT_KEYBOARD:
            key = record.Event.KeyEvent
            return {
                'type': INPUT_KEYBOARD,
                'key': ord(key.uChar),
                'press': key.bKeyDown,
                'keycode': key.wVirtualKeyCode,
                'scancode': key.wVirtualScanCode
            }

        if record.EventType == INPUT_MOUSE:
            mouse = record.Event.MouseEvent
            return {
                'type': INPUT_MOUSE,
                'event': mouse.dwEventFlags,
                'button': mouse.dwButtonState,
                'x': mouse.dwMousePosition.X,
                'y': mouse.dwMousePosition.Y,
            }

    # Window title
    def set_title(title: str):
        kernel32.SetConsoleTitleW(title)
        # os.system(f"title {title}") # closed alternative

    # Cursor
    def hide_cursor():
        class CONSOLE_CURSOR_INFO(ctypes.Structure):
            _fields_ = [
                ("dwSize", ctypes.c_int),
                ("bVisible", ctypes.c_bool)
            ]
        cursor_info = CONSOLE_CURSOR_INFO()
            
        stdout_handle = ctypes.windll.kernel32.GetStdHandle(_STD_OUTPUT_HANDLE)
        ctypes.windll.kernel32.GetConsoleCursorInfo(stdout_handle, ctypes.byref(cursor_info))
        cursor_info.bVisible = False
        ctypes.windll.kernel32.SetConsoleCursorInfo(stdout_handle, ctypes.byref(cursor_info))

    def show_cursor():
        class CONSOLE_CURSOR_INFO(ctypes.Structure):
            _fields_ = [
                ("dwSize", ctypes.c_int),
                ("bVisible", ctypes.c_bool)
            ]
        cursor_info = CONSOLE_CURSOR_INFO()
            
        stdout_handle = ctypes.windll.kernel32.GetStdHandle(_STD_OUTPUT_HANDLE)
        ctypes.windll.kernel32.GetConsoleCursorInfo(stdout_handle, ctypes.byref(cursor_info))
        cursor_info.bVisible = True
        ctypes.windll.kernel32.SetConsoleCursorInfo(stdout_handle, ctypes.byref(cursor_info))

else:
    raise NotImplementedError("UNIX systems are not yet implemented. Please yell at me.")
