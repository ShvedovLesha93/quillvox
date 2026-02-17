"""
Console window hider for Windows.

This allows to use console=True in the .spec file_level
(which makes multiprocessing work)
while hiding the console from the user.
"""

import sys
import platform


def hide_console():
    """
    Hide the console window on Windows.

    This function must be called at the very start of the application,
    before creating QApplication.
    """
    if platform.system() == "Windows":
        try:
            import ctypes

            # Get the console window handle
            hwnd = ctypes.windll.kernel32.GetConsoleWindow()

            if hwnd != 0:
                # Hide the console window
                # SW_HIDE = 0
                ctypes.windll.user32.ShowWindow(hwnd, 0)

                # Optional: Also remove from taskbar
                # GWL_EXSTYLE = -20
                # WS_EX_TOOLWINDOW = 0x00000080
                # ctypes.windll.user32.SetWindowLongW(
                #     hwnd,
                #     -20,
                #     ctypes.windll.user32.GetWindowLongW(hwnd, -20) | 0x00000080
                # )

        except Exception as e:
            # If hiding fails, just continue
            # The console will be visible but app will work
            print(f"Warning: Could not hide console: {e}")


def show_console():
    """
    Show the console window on Windows (for debugging).
    """
    if platform.system() == "Windows":
        try:
            import ctypes

            hwnd = ctypes.windll.kernel32.GetConsoleWindow()
            if hwnd != 0:
                # SW_SHOW = 5
                ctypes.windll.user32.ShowWindow(hwnd, 5)
        except:
            pass
