#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Win32ネイティブスプラッシュスクリーン

PySide6のロード前に即座にスプラッシュを表示するため、
ctypes経由でWin32 APIを直接呼び出してウィンドウを作成する。
"""

import ctypes
import ctypes.wintypes

from version import VERSION, APP_NAME, DESCRIPTION

# --- Win32 定数 ---
WS_POPUP = 0x80000000
WS_VISIBLE = 0x10000000
WS_EX_TOOLWINDOW = 0x00000080
WS_EX_TOPMOST = 0x00000008
CS_HREDRAW = 0x0002
CS_VREDRAW = 0x0001
WM_PAINT = 0x000F
DT_CENTER = 0x01
DT_VCENTER = 0x04
DT_SINGLELINE = 0x20
DT_RIGHT = 0x02

# --- Win32 API型定義 ---
WNDPROC = ctypes.WINFUNCTYPE(
    ctypes.c_longlong,
    ctypes.wintypes.HWND,
    ctypes.c_uint,
    ctypes.wintypes.WPARAM,
    ctypes.wintypes.LPARAM,
)


class PAINTSTRUCT(ctypes.Structure):
    _fields_ = [
        ("hdc", ctypes.wintypes.HDC),
        ("fErase", ctypes.wintypes.BOOL),
        ("rcPaint", ctypes.wintypes.RECT),
        ("fRestore", ctypes.wintypes.BOOL),
        ("fIncUpdate", ctypes.wintypes.BOOL),
        ("rgbReserved", ctypes.c_byte * 32),
    ]


class WNDCLASSEXW(ctypes.Structure):
    _fields_ = [
        ("cbSize", ctypes.c_uint),
        ("style", ctypes.c_uint),
        ("lpfnWndProc", WNDPROC),
        ("cbClsExtra", ctypes.c_int),
        ("cbWndExtra", ctypes.c_int),
        ("hInstance", ctypes.wintypes.HINSTANCE),
        ("hIcon", ctypes.wintypes.HICON),
        ("hCursor", ctypes.wintypes.HICON),
        ("hbrBackground", ctypes.wintypes.HBRUSH),
        ("lpszMenuName", ctypes.c_wchar_p),
        ("lpszClassName", ctypes.c_wchar_p),
        ("hIconSm", ctypes.wintypes.HICON),
    ]


# --- Win32 API参照 ---
user32 = ctypes.windll.user32
gdi32 = ctypes.windll.gdi32
kernel32 = ctypes.windll.kernel32

# DefWindowProcWの型を正しく設定（64bit対応）
user32.DefWindowProcW.argtypes = [
    ctypes.wintypes.HWND, ctypes.c_uint,
    ctypes.wintypes.WPARAM, ctypes.wintypes.LPARAM,
]
user32.DefWindowProcW.restype = ctypes.c_longlong

# --- ウィンドウサイズ ---
_WIN_W = 360
_WIN_H = 180

# --- 色定数（BGR形式） ---
_CLR_BG = 0x00F8F4F0       # #f0f4f8
_CLR_ACCENT = 0x00D47800    # #0078d4
_CLR_TITLE = 0x001A1A1A     # #1a1a1a
_CLR_SUBTITLE = 0x00666666  # #666666
_CLR_LOADING = 0x00D47800   # #0078d4
_CLR_VERSION = 0x00999999   # #999999


def _create_font(height, weight=400):
    """GDIフォントを作成"""
    return gdi32.CreateFontW(
        height, 0, 0, 0, weight,
        0, 0, 0, 1, 0, 0, 4, 0,
        "Yu Gothic UI",
    )


def _draw_text(hdc, text, rect_tuple, color, font_height, font_weight=400, align=0):
    """テキストを描画してフォントを適切に解放"""
    font = _create_font(font_height, font_weight)
    old_font = gdi32.SelectObject(hdc, font)
    gdi32.SetTextColor(hdc, color)
    rect = ctypes.wintypes.RECT(*rect_tuple)
    user32.DrawTextW(hdc, text, -1, ctypes.byref(rect), align | DT_SINGLELINE | DT_VCENTER)
    gdi32.SelectObject(hdc, old_font)
    gdi32.DeleteObject(font)


def _fill_rect(hdc, rect_tuple, color):
    """矩形を塗りつぶし"""
    brush = gdi32.CreateSolidBrush(color)
    rect = ctypes.wintypes.RECT(*rect_tuple)
    user32.FillRect(hdc, ctypes.byref(rect), brush)
    gdi32.DeleteObject(brush)


def _wnd_proc(hwnd, msg, wparam, lparam):
    """ウィンドウプロシージャ"""
    if msg == WM_PAINT:
        ps = PAINTSTRUCT()
        hdc = user32.BeginPaint(hwnd, ctypes.byref(ps))

        # 背景
        _fill_rect(hdc, (0, 0, _WIN_W, _WIN_H), _CLR_BG)

        # アクセントライン（上部4px）
        _fill_rect(hdc, (0, 0, _WIN_W, 4), _CLR_ACCENT)

        gdi32.SetBkMode(hdc, 1)  # TRANSPARENT

        # アプリ名
        _draw_text(hdc, APP_NAME, (0, 35, _WIN_W, 80),
                   _CLR_TITLE, -30, 700, DT_CENTER)

        # サブタイトル
        _draw_text(hdc, DESCRIPTION, (0, 85, _WIN_W, 110),
                   _CLR_SUBTITLE, -14, 400, DT_CENTER)

        # 読み込み中
        _draw_text(hdc, "読み込み中...", (12, _WIN_H - 30, 200, _WIN_H - 10),
                   _CLR_LOADING, -13)

        # バージョン
        _draw_text(hdc, f"v{VERSION}", (_WIN_W - 110, _WIN_H - 30, _WIN_W - 10, _WIN_H - 10),
                   _CLR_VERSION, -12, 400, DT_RIGHT)

        user32.EndPaint(hwnd, ctypes.byref(ps))
        return 0

    return user32.DefWindowProcW(hwnd, msg, wparam, lparam)


# コールバック参照を保持（GC防止）
_wnd_proc_cb = WNDPROC(_wnd_proc)


class Win32Splash:
    """Win32ネイティブスプラッシュスクリーン

    PySide6のインポート前に呼び出すことで、
    ~50ms以内にスプラッシュを画面に表示できる。
    """

    _CLASS_NAME = "PDFmergeSplash"

    def __init__(self):
        self._hwnd = None
        self._h_instance = kernel32.GetModuleHandleW(None)
        self._registered = False

        self._register_class()
        self._create_window()

    def _register_class(self):
        """ウィンドウクラスを登録"""
        wc = WNDCLASSEXW()
        wc.cbSize = ctypes.sizeof(WNDCLASSEXW)
        wc.style = CS_HREDRAW | CS_VREDRAW
        wc.lpfnWndProc = _wnd_proc_cb
        wc.hInstance = self._h_instance
        wc.hbrBackground = gdi32.CreateSolidBrush(_CLR_BG)
        wc.lpszClassName = self._CLASS_NAME

        user32.RegisterClassExW(ctypes.byref(wc))
        self._registered = True

    def _create_window(self):
        """ウィンドウを作成して画面中央に表示"""
        screen_w = user32.GetSystemMetrics(0)
        screen_h = user32.GetSystemMetrics(1)
        x = (screen_w - _WIN_W) // 2
        y = (screen_h - _WIN_H) // 2

        self._hwnd = user32.CreateWindowExW(
            WS_EX_TOOLWINDOW | WS_EX_TOPMOST,
            self._CLASS_NAME, None,
            WS_POPUP | WS_VISIBLE,
            x, y, _WIN_W, _WIN_H,
            None, None, self._h_instance, None,
        )
        user32.UpdateWindow(self._hwnd)

    def close(self):
        """スプラッシュを閉じてリソースを解放"""
        if self._hwnd:
            user32.DestroyWindow(self._hwnd)
            self._hwnd = None
        if self._registered:
            user32.UnregisterClassW(self._CLASS_NAME, self._h_instance)
            self._registered = False
