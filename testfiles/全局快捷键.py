import ctypes, win32con, ctypes.wintypes, win32gui
import sys
import threading

from PyQt5.QtWidgets import QApplication

from jamscreenshot import Slabel


class JHotkey(threading.Thread):
    def run(self):
        user32 = ctypes.windll.user32
        if not user32.RegisterHotKey(None, 100, win32con.MOD_ALT, 0x5A):
            print('RuntimeError')
        if not user32.RegisterHotKey(None, 101, win32con.MOD_ALT, 0x58):
            print('RuntimeError')
        if not user32.RegisterHotKey(None, 102, win32con.MOD_ALT, 0x43):
            print('RuntimeError')

        try:
            msg = ctypes.wintypes.MSG()
            while user32.GetMessageA(ctypes.byref(msg), None, 0, 0) != 0:  # GetMessageA 会堵塞线程直到收到事件
                print(msg.message, msg.wParam)
                if msg.message == win32con.WM_HOTKEY:
                    id = msg.wParam
                    if id == 100:
                        print('alt+z')
                        ss.screen_shot()
                    elif id == 101:
                        print('alt+x')
                    elif id == 102:
                        print('alt+c')
                user32.TranslateMessage(ctypes.byref(msg))
                user32.DispatchMessageA(ctypes.byref(msg))
        finally:
            user32.UnregisterHotKey(None, 1)


app = QApplication(sys.argv)
h = JHotkey()
h.start()
ss = Slabel()
# ss.screen_shot()

sys.exit(app.exec_())
