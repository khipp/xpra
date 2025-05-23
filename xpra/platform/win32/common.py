#!/usr/bin/env python3
# This file is part of Xpra.
# Copyright (C) 2017 Antoine Martin <antoine@xpra.org>
# Xpra is released under the terms of the GNU GPL v2, or, at your option, any
# later version. See the file COPYING for details.

from typing import Any

from ctypes import (
    WinDLL, WINFUNCTYPE, GetLastError,  # @UnresolvedImport
    POINTER, Structure,
    c_ulong, c_ushort, c_ubyte, c_int, c_long, c_void_p, c_size_t, c_char,
    byref, sizeof,
)
from ctypes.wintypes import (
    HWND, DWORD, WPARAM, LPARAM, HDC, HMONITOR, HMODULE,
    SHORT, ATOM, RECT, POINT, MAX_PATH, WCHAR, BYTE,
    HANDLE, LPSTR, LPCWSTR, UINT, INT, BOOL, WORD, HGDIOBJ,
    LONG, LPVOID, HBITMAP, LPCSTR, LPWSTR, HWINSTA,
    HINSTANCE, HMENU, ULONG, HHOOK, LPMSG,
    LCID, HKL,
)

# imported from this module but not used here:
assert GetLastError

LPCTSTR = LPCSTR
LRESULT = c_long
DEVMODE = c_void_p
PDWORD = POINTER(DWORD)
LPDWORD = POINTER(DWORD)
PBYTE = POINTER(BYTE)
HCURSOR = HANDLE
HICON = HANDLE
HBRUSH = HANDLE


class CURSORINFO(Structure):
    _fields_ = [
        ("cbSize", DWORD),
        ("flags", DWORD),
        ("hCursor", HCURSOR),
        ("ptScreenPos", POINT),
    ]


class ICONINFO(Structure):
    _fields_ = [
        ("fIcon", BOOL),
        ("xHotspot", DWORD),
        ("yHotspot", DWORD),
        ("hbmMask", HBITMAP),
        ("hbmColor", HBITMAP),
    ]


PICONINFO = POINTER(ICONINFO)


# noinspection PyTypeChecker
class ICONINFOEXA(Structure):
    _fields_ = [
        ("cbSize", DWORD),
        ("fIcon", BOOL),
        ("xHotspot", DWORD),
        ("yHotspot", DWORD),
        ("hbmMask", HBITMAP),
        ("hbmColor", HBITMAP),
        ("wResID", WORD),
        ("sxModName", c_char * MAX_PATH),
        ("szResName", c_char * MAX_PATH),
    ]


PICONINFOEXA = POINTER(ICONINFOEXA)


# noinspection PyTypeChecker
class ICONINFOEXW(Structure):
    _fields_ = [
        ("cbSize", DWORD),
        ("fIcon", BOOL),
        ("xHotspot", DWORD),
        ("yHotspot", DWORD),
        ("hbmMask", HBITMAP),
        ("hbmColor", HBITMAP),
        ("wResID", WORD),
        ("sxModName", WCHAR * MAX_PATH),
        ("szResName", WCHAR * MAX_PATH),
    ]


PICONINFOEXW = POINTER(ICONINFOEXW)


class Bitmap(Structure):
    _fields_ = [
        ("bmType", LONG),
        ("bmWidth", LONG),
        ("bmHeight", LONG),
        ("bmWidthBytes", LONG),
        ("bmPlanes", WORD),
        ("bmBitsPixel", WORD),
        ("bmBits", LPVOID)
    ]


class CIEXYZ(Structure):
    _fields_ = [
        ('ciexyzX', DWORD),
        ('ciexyzY', DWORD),
        ('ciexyzZ', DWORD),
    ]


class CIEXYZTRIPLE(Structure):
    _fields_ = [
        ('ciexyzRed', CIEXYZ),
        ('ciexyzBlue', CIEXYZ),
        ('ciexyzGreen', CIEXYZ),
    ]


class BITMAPINFOHEADER(Structure):
    _fields_ = [
        ("biSize", DWORD),
        ("biWidth", LONG),
        ("biHeight", LONG),
        ("biPlanes", WORD),
        ("biBitCount", WORD),
        ("biCompression", DWORD),
        ("biSizeImage", DWORD),
        ("biXPelsPerMeter", LONG),
        ("biYPelsPerMeter", LONG),
        ("biClrUsed", DWORD),
        ("biClrImportant", DWORD),
    ]


PBITMAPINFOHEADER = POINTER(BITMAPINFOHEADER)


class BITMAPINFO(Structure):
    _fields_ = [
        ("bmiHeader", BITMAPINFOHEADER),
        ("bmiColors", DWORD),
    ]


PBITMAPINFO = POINTER(BITMAPINFO)


class BITMAPV5HEADER(Structure):
    _fields_ = [
        ('bV5Size', DWORD),
        ('bV5Width', LONG),
        ('bV5Height', LONG),
        ('bV5Planes', WORD),
        ('bV5BitCount', WORD),
        ('bV5Compression', DWORD),
        ('bV5SizeImage', DWORD),
        ('bV5XPelsPerMeter', LONG),
        ('bV5YPelsPerMeter', LONG),
        ('bV5ClrUsed', DWORD),
        ('bV5ClrImportant', DWORD),
        ('bV5RedMask', DWORD),
        ('bV5GreenMask', DWORD),
        ('bV5BlueMask', DWORD),
        ('bV5AlphaMask', DWORD),
        ('bV5CSType', DWORD),
        ('bV5Endpoints', CIEXYZTRIPLE),
        ('bV5GammaRed', DWORD),
        ('bV5GammaGreen', DWORD),
        ('bV5GammaBlue', DWORD),
        ('bV5Intent', DWORD),
        ('bV5ProfileData', DWORD),
        ('bV5ProfileSize', DWORD),
        ('bV5Reserved', DWORD),
    ]


PBITMAPV5HEADER = POINTER(BITMAPV5HEADER)

CCHDEVICENAME = 32


class MONITORINFOEX(Structure):
    # noinspection PyTypeChecker
    _fields_ = [
        ('cbSize', DWORD),
        ('rcMonitor', RECT),
        ('rcWork', RECT),
        ('dwFlags', DWORD),
        ('szDevice', WCHAR * CCHDEVICENAME),
    ]


class SECURITY_ATTRIBUTES(Structure):
    _fields_ = [
        ("nLength", c_int),
        ("lpSecurityDescriptor", c_void_p),
        ("bInheritHandle", c_int),
    ]


LPSECURITY_ATTRIBUTES = POINTER(SECURITY_ATTRIBUTES)


def GetMonitorInfo(hmonitor) -> dict[str, Any]:
    info = MONITORINFOEX()
    info.szDevice = ""
    info.cbSize = sizeof(MONITORINFOEX)
    if not GetMonitorInfoW(hmonitor, byref(info)):
        raise OSError()  # @UndefinedVariable
    monitor = info.rcMonitor.left, info.rcMonitor.top, info.rcMonitor.right, info.rcMonitor.bottom
    work = info.rcWork.left, info.rcWork.top, info.rcWork.right, info.rcWork.bottom
    return {
        "Work": work,
        "Monitor": monitor,
        "Flags": info.dwFlags,
        "Device": info.szDevice or "",
    }


kernel32 = WinDLL("kernel32", use_last_error=True)
LocalFree = kernel32.LocalFree
FormatMessageW = kernel32.FormatMessageW
GetCurrentThreadId = kernel32.GetCurrentThreadId
GetCurrentThreadId.restype = DWORD
GetCurrentThreadId.argtypes = []
SetConsoleTitleA = kernel32.SetConsoleTitleA
SetConsoleTitleA.restype = INT
SetConsoleTitleA.argtypes = [LPCTSTR]
GetConsoleScreenBufferInfo = kernel32.GetConsoleScreenBufferInfo
GetModuleHandleA = kernel32.GetModuleHandleA
GetModuleHandleA.restype = HMODULE
GetModuleHandleW = kernel32.GetModuleHandleW
GetModuleHandleW.restype = HMODULE
GetModuleHandleExA = kernel32.GetModuleHandleExA
GetModuleHandleExA.argtypes = [DWORD, LPCSTR, POINTER(HMODULE)]
GetModuleHandleExA.restype = BOOL
ConsoleCtrlHandler = WINFUNCTYPE(BOOL, DWORD)
SetConsoleCtrlHandler = kernel32.SetConsoleCtrlHandler
SetConsoleCtrlHandler.argtypes = (ConsoleCtrlHandler, BOOL)
SetConsoleCtrlHandler.restype = BOOL
GetComputerNameW = kernel32.GetComputerNameW
GetComputerNameW.restype = BOOL
GetComputerNameW.argtypes = [LPWSTR, LPDWORD]
GetCurrentProcess = kernel32.GetCurrentProcess
GetCurrentProcess.argtypes = []
GetCurrentProcess.restype = HANDLE
HeapAlloc = kernel32.HeapAlloc
HeapAlloc.restype = LPVOID
HeapAlloc.argtypes = [HANDLE, DWORD, c_size_t]
GetProcessHeap = kernel32.GetProcessHeap
GetProcessHeap.restype = HANDLE
GetProcessHeap.argtypes = []
CloseHandle = kernel32.CloseHandle
CloseHandle.argtypes = [HANDLE]
CloseHandle.restype = BOOL
GetProductInfo = kernel32.GetProductInfo
GetProductInfo.argtypes = [DWORD, DWORD, DWORD, DWORD, PDWORD]
GetProductInfo.restype = BOOL
GetStdHandle = WINFUNCTYPE(HANDLE, DWORD)(("GetStdHandle", kernel32))
HGLOBAL = HANDLE
GlobalAlloc = kernel32.GlobalAlloc
GlobalAlloc.restype = HGLOBAL
GlobalAlloc.argtypes = [UINT, c_size_t]
GlobalFree = kernel32.GlobalFree
GlobalFree.restype = HGLOBAL
GlobalFree.argtypes = [HGLOBAL]
GlobalLock = kernel32.GlobalLock
GlobalLock.restype = LPVOID
GlobalLock.argtypes = [HGLOBAL]
GlobalSize = kernel32.GlobalSize
GlobalSize.argtypes = [HGLOBAL]
GlobalSize.restype = c_size_t
GlobalUnlock = kernel32.GlobalUnlock
GlobalUnlock.restype = BOOL
GlobalUnlock.argtypes = [HGLOBAL]
WideCharToMultiByte = kernel32.WideCharToMultiByte
WideCharToMultiByte.restype = c_int
WideCharToMultiByte.argtypes = [UINT, DWORD, LPCWSTR, c_int, c_void_p, c_int, LPCSTR, POINTER(BOOL)]
MultiByteToWideChar = kernel32.MultiByteToWideChar
MultiByteToWideChar.restype = c_int
MultiByteToWideChar.argtypes = [UINT, DWORD, LPCSTR, c_int, LPWSTR, c_int]
WTSGetActiveConsoleSessionId = kernel32.WTSGetActiveConsoleSessionId
WTSGetActiveConsoleSessionId.restype = DWORD
WTSGetActiveConsoleSessionId.argtypes = []
QueryFullProcessImageNameA = kernel32.QueryFullProcessImageNameA
QueryFullProcessImageNameA.restype = BOOL
QueryFullProcessImageNameA.argtypes = [HANDLE, DWORD, LPSTR, PDWORD]
OpenProcess = kernel32.OpenProcess
OpenProcess.restype = HANDLE
OpenProcess.argtypes = [DWORD, BOOL, DWORD]
GetThreadLocale = kernel32.GetThreadLocale
GetThreadLocale.argtypes = []
GetThreadLocale.restype = LCID

user32 = WinDLL("user32", use_last_error=True)
RegisterClassExA = user32.RegisterClassExA
RegisterClassExA.restype = ATOM
RegisterClassExW = user32.RegisterClassExW
RegisterClassExW.restype = ATOM
UnregisterClassA = user32.UnregisterClassA
UnregisterClassA.restype = BOOL
UnregisterClassA.argtypes = [LPCSTR, HINSTANCE]
UnregisterClassW = user32.UnregisterClassW
UnregisterClassW.restype = BOOL
UnregisterClassW.argtypes = [LPCWSTR, HINSTANCE]
CreateWindowExA = user32.CreateWindowExA
CreateWindowExA.restype = HWND
CreateWindowExA.argtypes = [DWORD, ATOM, LPCWSTR, DWORD, c_int, c_int, c_int, c_int, HWND, HMENU, HINSTANCE, LPVOID]
CreateWindowExW = user32.CreateWindowExW
CreateWindowExW.restype = HWND
CreateWindowExW.argtypes = [DWORD, ATOM, LPCWSTR, DWORD, c_int, c_int, c_int, c_int, HWND, HMENU, HINSTANCE, LPVOID]
DestroyWindow = user32.DestroyWindow
DestroyWindow.restype = BOOL
DestroyWindow.argtypes = [HWND]
DefWindowProcA = user32.DefWindowProcA
DefWindowProcA.argtypes = [HWND, UINT, WPARAM, LPARAM]
DefWindowProcA.restype = INT
DefWindowProcW = user32.DefWindowProcW
DefWindowProcW.argtypes = [HWND, UINT, WPARAM, LPARAM]
DefWindowProcW.restype = INT
WNDPROC = WINFUNCTYPE(LRESULT, HWND, UINT, WPARAM, LPARAM)
CallWindowProcW = user32.CallWindowProcW
CallWindowProcW.argtypes = [WNDPROC, HWND, UINT, WPARAM, LPARAM]
CallWindowProcW.restype = LRESULT
MessageBoxA = user32.MessageBoxA
MessageBoxA.restype = INT
MessageBoxA.argtypes = [HWND, LPCTSTR, LPCTSTR, UINT]
GetSystemMetrics = user32.GetSystemMetrics
GetSystemMetrics.restype = INT
GetSystemMetrics.argtypes = [INT]
SetWindowLongA = user32.SetWindowLongA
SetWindowLongA.restype = LONG
SetWindowLongA.argtypes = [HWND, INT, LONG]
SetWindowLongW = user32.SetWindowLongW
SetWindowLongW.restype = LONG
SetWindowLongW.argtypes = [HWND, INT, WNDPROC]
GetWindowLongW = user32.GetWindowLongW
GetWindowLongW.restype = LONG
GetWindowLongW.argtypes = [HWND, INT]
ClipCursor = user32.ClipCursor
ClipCursor.restype = BOOL
GetCursorPos = user32.GetCursorPos
GetCursorPos.argtypes = [POINTER(POINT)]
GetCursorPos.restype = BOOL
SetCursorPos = user32.SetCursorPos
SetCursorPos.argtypes = [INT, INT]
SetCursorPos.restype = BOOL
GetPhysicalCursorPos = user32.GetPhysicalCursorPos
GetPhysicalCursorPos.argtypes = [POINTER(POINT)]
GetPhysicalCursorPos.restype = BOOL
SetPhysicalCursorPos = user32.SetPhysicalCursorPos
SetPhysicalCursorPos.argtypes = [INT, INT]
SetPhysicalCursorPos.restype = BOOL
GetCursorInfo = user32.GetCursorInfo
GetCursorInfo.argtypes = [POINTER(CURSORINFO)]
GetCursorInfo.restype = BOOL
LogicalToPhysicalPoint = user32.LogicalToPhysicalPoint
LogicalToPhysicalPoint.argtypes = [HWND, POINTER(POINT)]
LogicalToPhysicalPoint.restype = BOOL
SendMessageA = user32.SendMessageA
PostMessageA = user32.PostMessageA
FindWindowA = user32.FindWindowA
GetWindowRect = user32.GetWindowRect
GetDoubleClickTime = user32.GetDoubleClickTime
_EnumDisplayMonitors = user32.EnumDisplayMonitors
MonitorFromWindow = user32.MonitorFromWindow
MonitorFromWindow.restype = HMONITOR
GetMonitorInfoW = user32.GetMonitorInfoW
GetMonitorInfoW.argtypes = [HMONITOR, POINTER(MONITORINFOEX)]
GetMonitorInfoW.restype = BOOL
UnhookWindowsHookEx = user32.UnhookWindowsHookEx
CallNextHookEx = user32.CallNextHookEx
CallNextHookEx.restype = LRESULT
CallNextHookEx.argtyps = [HHOOK, INT, WPARAM, LPARAM]
SetWindowsHookExA = user32.SetWindowsHookExA
SetWindowsHookExA.restype = HHOOK
SetWindowsHookExA.argtypes = [INT, HANDLE, HINSTANCE, DWORD]
GetMessageA = user32.GetMessageA
GetMessageA.restype = BOOL
GetMessageA.argtypes = [LPMSG, HWND, UINT, UINT]
TranslateMessage = user32.TranslateMessage
TranslateMessage.restype = BOOL
TranslateMessage.argtypes = [LPMSG]
DispatchMessageA = user32.DispatchMessageA
DispatchMessageA.restype = LRESULT
DispatchMessageA.argtypes = [LPMSG]
MapVirtualKeyW = user32.MapVirtualKeyW
GetKeyboardState = user32.GetKeyboardState
GetKeyboardState.argtypes = [PBYTE]
GetKeyboardState.restype = BOOL
SetKeyboardState = user32.SetKeyboardState
SetKeyboardState.argtypes = [PBYTE]
SetKeyboardState.restype = BOOL
GetAsyncKeyState = user32.GetAsyncKeyState
GetAsyncKeyState.argtypes = [INT]
GetAsyncKeyState.restype = SHORT
VkKeyScanW = user32.VkKeyScanW
VkKeyScanW.argtypes = [WCHAR]
keybd_event = user32.keybd_event
GetKeyState = user32.GetKeyState
GetKeyState.restype = SHORT
GetKeyboardLayout = user32.GetKeyboardLayout
GetKeyboardLayout.argtypes = [DWORD]
GetKeyboardLayout.restype = HKL
GetKeyboardLayoutList = user32.GetKeyboardLayoutList
GetKeyboardLayoutList.restype = int
# noinspection PyTypeChecker
GetKeyboardLayoutList.argtypes = [c_int, POINTER(HANDLE * 32)]
GetKeyboardLayoutName = user32.GetKeyboardLayoutNameA
GetKeyboardLayoutName.restype = BOOL
GetKeyboardLayoutName.argtypes = [LPSTR]
ActivateKeyboardLayout = user32.ActivateKeyboardLayout
ActivateKeyboardLayout.argtypes = [HKL, UINT]
ActivateKeyboardLayout.restype = HKL
SystemParametersInfoA = user32.SystemParametersInfoA
EnumWindowsProc = WINFUNCTYPE(BOOL, HWND, LPARAM)
EnumWindows = user32.EnumWindows
EnumWindows.argtypes = [EnumWindowsProc, LPARAM]
IsWindowVisible = user32.IsWindowVisible
GetWindowThreadProcessId = user32.GetWindowThreadProcessId
GetWindowThreadProcessId.argtypes = [HWND, LPDWORD]
GetWindowThreadProcessId.restype = DWORD
GetDesktopWindow = user32.GetDesktopWindow
GetDesktopWindow.restype = HWND
GetWindowDC = user32.GetWindowDC
GetWindowDC.argtypes = [HWND]
GetWindowDC.restype = HDC
ReleaseDC = user32.ReleaseDC
ReleaseDC.restype = c_int
ReleaseDC.argtypes = [HWND, HDC]
mouse_event = user32.mouse_event
LoadIconA = user32.LoadIconA
LoadIconA.restype = HICON
# can also pass int as second arg, so don't declare argtypes:
# LoadIconA.argtypes = [HINSTANCE, LPCSTR]
RegisterWindowMessageA = user32.RegisterWindowMessageA
RegisterWindowMessageA.restype = UINT
RegisterWindowMessageA.argtypes = [LPCSTR]
UpdateWindow = user32.UpdateWindow
UpdateWindow.restype = BOOL
UpdateWindow.argtypes = [HWND]
DestroyIcon = user32.DestroyIcon
DestroyIcon.restype = BOOL
DestroyIcon.argtypes = [HICON]
LoadImageW = user32.LoadImageW
LoadImageW.argtypes = [HINSTANCE, LPCWSTR, UINT, INT, INT, UINT]
LoadImageW.restype = HANDLE
CreateIconIndirect = user32.CreateIconIndirect
CreateIconIndirect.restype = HICON
CreateIconIndirect.argtypes = [POINTER(ICONINFO)]
GetDC = user32.GetDC
GetDC.argtypes = [HWND]
GetDC.restype = HDC
ReleaseDC = user32.ReleaseDC
ReleaseDC.argtypes = [HWND, HDC]
ReleaseDC.restype = c_int
DrawIcon = user32.DrawIcon
DrawIcon.argtypes = [HDC, INT, INT, HICON]
DrawIcon.restype = BOOL
DrawIconEx = user32.DrawIconEx
DrawIconEx.argtypes = [HDC, INT, INT, HICON, INT, INT, UINT, HBRUSH, UINT]
DrawIconEx.restype = BOOL
GetIconInfo = user32.GetIconInfo
GetIconInfo.argtypes = [HICON, PICONINFO]
GetIconInfo.restype = BOOL
GetIconInfoExA = user32.GetIconInfoExA
GetIconInfoExA.argtypes = [HICON, PICONINFOEXA]
GetIconInfoExA.restype = BOOL
GetIconInfoExW = user32.GetIconInfoExW
GetIconInfoExW.argtypes = [HICON, PICONINFOEXW]
GetIconInfoExW.restype = BOOL
CopyIcon = user32.CopyIcon
CopyIcon.argtypes = [HICON]
CopyIcon.restype = HICON
PostQuitMessage = user32.PostQuitMessage
PostQuitMessage.argtypes = [INT]
OpenWindowStationW = user32.OpenWindowStationW
OpenWindowStationW.restype = HWINSTA
ACCESS_MASK = DWORD
OpenWindowStationW.argtypes = [LPWSTR, BOOL, ACCESS_MASK]
OpenWindowStationA = user32.OpenWindowStationA
OpenWindowStationA.restype = HWINSTA
OpenWindowStationA.argtypes = [LPCSTR, BOOL, ACCESS_MASK]
GetProcessWindowStation = user32.GetProcessWindowStation
GetProcessWindowStation.restype = HWINSTA
GetProcessWindowStation.argtypes = []
SetProcessWindowStation = user32.SetProcessWindowStation
SetProcessWindowStation.restype = BOOL
SetProcessWindowStation.argtypes = [HWINSTA]
CreateWindowStationA = user32.CreateWindowStationA
CreateWindowStationA.restype = HWINSTA
CreateWindowStationA.argtypes = [LPCSTR, DWORD, ACCESS_MASK, LPSECURITY_ATTRIBUTES]
CloseWindowStation = user32.CloseWindowStation
CloseWindowStation.restype = BOOL
CloseWindowStation.argtypes = [HWINSTA]
WINSTAENUMPROCA = WINFUNCTYPE(BOOL, LPSTR, LPARAM)
EnumWindowStationsA = user32.EnumWindowStationsA
EnumWindowStationsA.restype = BOOL
EnumWindowStationsA.argtypes = [WINSTAENUMPROCA, LPARAM]
HDESK = HANDLE
CreateDesktopA = user32.CreateDesktopA
CreateDesktopA.restype = HDESK
DEVMODEA = c_void_p
CreateDesktopA.argtypes = [LPCSTR, LPCSTR, DEVMODEA, DWORD, ACCESS_MASK, LPSECURITY_ATTRIBUTES]
CreateDesktopExA = user32.CreateDesktopExA
CreateDesktopExA.argtypes = [LPCSTR, LPCSTR, DEVMODEA, DWORD, ACCESS_MASK, LPSECURITY_ATTRIBUTES, ULONG, LPVOID]
CreateDesktopExA = user32.CreateDesktopExA
CreateDesktopExA.restype = HDESK
OpenDesktopW = user32.OpenDesktopW
OpenDesktopW.restype = HDESK
OpenDesktopW.argtypes = [LPWSTR, DWORD, BOOL, ACCESS_MASK]
CloseDesktop = user32.CloseDesktop
CloseDesktop.restype = BOOL
CloseDesktop.argtypes = [HDESK]
OpenInputDesktop = user32.OpenInputDesktop
OpenInputDesktop.restype = HDESK
OpenInputDesktop.argtypes = [DWORD, BOOL, ACCESS_MASK]
DESKTOPENUMPROCA = WINFUNCTYPE(BOOL, LPCSTR, LPARAM)
EnumDesktopsA = user32.EnumDesktopsA
EnumDesktopsA.restype = BOOL
EnumDesktopsA.argtypes = [HWINSTA, DESKTOPENUMPROCA, LPARAM]
GetThreadDesktop = user32.GetThreadDesktop
GetThreadDesktop.restype = HDESK
GetThreadDesktop.argtypes = [DWORD]
GetUserObjectInformationA = user32.GetUserObjectInformationA
GetUserObjectInformationA.restype = BOOL
GetUserObjectInformationA.argtypes = [HANDLE, INT, LPVOID, DWORD, LPDWORD]
CreatePopupMenu = user32.CreatePopupMenu
CreatePopupMenu.restype = HMENU
CreatePopupMenu.argtypes = []
AppendMenu = user32.AppendMenuW
AppendMenu.restype = BOOL
AppendMenu.argtypes = [HMENU, UINT, UINT, LPCWSTR]


# clipboard functions:


class COPYDATASTRUCT(Structure):
    _fields_ = [
        ("dwData", POINTER(ULONG)),
        ("cbData", DWORD),
        ("lpData", LPVOID),
    ]


OpenClipboard = user32.OpenClipboard
OpenClipboard.restype = BOOL
OpenClipboard.argtypes = [HWND]
CloseClipboard = user32.CloseClipboard
CloseClipboard.restype = BOOL
CloseClipboard.argtypes = []
EmptyClipboard = user32.EmptyClipboard
EmptyClipboard.restype = BOOL
EmptyClipboard.argtypes = []
SetClipboardData = user32.SetClipboardData
SetClipboardData.restype = HANDLE
SetClipboardData.argtypes = [UINT, HANDLE]
RegisterClipboardFormatA = user32.RegisterClipboardFormatA
RegisterClipboardFormatA.restype = UINT
RegisterClipboardFormatA.argtypes = [LPCSTR]
GetClipboardData = user32.GetClipboardData
GetClipboardData.restype = HANDLE
GetClipboardData.argtypes = [UINT]
GetClipboardSequenceNumber = user32.GetClipboardSequenceNumber
GetClipboardSequenceNumber.restype = DWORD
GetClipboardSequenceNumber.argtypes = []
GetClipboardOwner = user32.GetClipboardOwner
GetClipboardOwner.restype = HWND
GetClipboardOwner.argtypes = []
GetOpenClipboardWindow = user32.GetOpenClipboardWindow
GetOpenClipboardWindow.restype = HWND
GetOpenClipboardWindow.argtypes = []
AddClipboardFormatListener = user32.AddClipboardFormatListener
AddClipboardFormatListener.restype = BOOL
AddClipboardFormatListener.argtypes = [HWND]
RemoveClipboardFormatListener = user32.RemoveClipboardFormatListener
RemoveClipboardFormatListener.restype = BOOL
RemoveClipboardFormatListener.argtypes = [HWND]
GetUpdatedClipboardFormats = user32.GetUpdatedClipboardFormats
GetUpdatedClipboardFormats.restype = BOOL
GetUpdatedClipboardFormats.argtypes = [POINTER(UINT), UINT, POINTER(UINT)]
IsClipboardFormatAvailable = user32.IsClipboardFormatAvailable
IsClipboardFormatAvailable.restype = BOOL
IsClipboardFormatAvailable.argtypes = [UINT]
SetClipboardViewer = user32.SetClipboardViewer
SetClipboardViewer.restype = HWND
SetClipboardViewer.argtypes = [HWND]
GetClipboardFormatNameA = user32.GetClipboardFormatNameA
GetClipboardFormatNameA.restype = c_int
GetClipboardFormatNameA.argtypes = [UINT, LPCSTR, c_int]
GetClipboardFormatNameW = user32.GetClipboardFormatNameW
GetClipboardFormatNameW.restype = c_int
GetClipboardFormatNameW.argtypes = [UINT, LPWSTR, c_int]
EnumClipboardFormats = user32.EnumClipboardFormats
EnumClipboardFormats.restype = UINT
EnumClipboardFormats.argtypes = [UINT]
CountClipboardFormats = user32.CountClipboardFormats
CountClipboardFormats.restype = c_int
CountClipboardFormats.argtypes = []
GetWindowTextA = user32.GetWindowTextA
GetWindowTextA.restype = c_int
GetWindowTextA.argtypes = [HWND, LPSTR, c_int]
GetWindowTextW = user32.GetWindowTextW
GetWindowTextW.restype = c_int
GetWindowTextW.argtypes = [HWND, LPWSTR, c_int]
GetWindowTextLengthA = user32.GetWindowTextLengthA
GetWindowTextLengthA.restype = c_int
GetWindowTextLengthA.argtypes = [HWND]
GetWindowTextLengthW = user32.GetWindowTextLengthW
GetWindowTextLengthW.restype = c_int
GetWindowTextLengthW.argtypes = [HWND]


class PROCESS_INFORMATION(Structure):
    _fields_ = (
        ('_hProcess', HANDLE),
        ('_hThread', HANDLE),
        ('dwProcessId', DWORD),
        ('dwThreadId', DWORD),
    )


PPROCESS_INFORMATION = POINTER(PROCESS_INFORMATION)


class STARTUPINFOA(Structure):
    _fields_ = (
        ('cb', DWORD),
        ('lpReserved', LPWSTR),
        ('lpDesktop', LPWSTR),
        ('lpTitle', LPWSTR),
        ('dwX', DWORD),
        ('dwY', DWORD),
        ('dwXSize', DWORD),
        ('dwYSize', DWORD),
        ('dwXCountChars', DWORD),
        ('dwYCountChars', DWORD),
        ('dwFillAttribute', DWORD),
        ('dwFlags', DWORD),
        ('wShowWindow', WORD),
        ('cbReserved2', WORD),
        ('lpReserved2', c_void_p),
        ('hStdInput', HANDLE),
        ('hStdOutput', HANDLE),
        ('hStdError', HANDLE),
    )


PSTARTUPINFOA = POINTER(STARTUPINFOA)
advapi32 = WinDLL("advapi32")
CreateProcessAsUserA = advapi32.CreateProcessAsUserA
CreateProcessAsUserA.restype = BOOL
CreateProcessAsUserA.argtypes = [HANDLE, LPCSTR, LPSTR, LPSECURITY_ATTRIBUTES, LPSECURITY_ATTRIBUTES, BOOL, DWORD,
                                 LPVOID, LPCSTR, LPCSTR, PSTARTUPINFOA, PPROCESS_INFORMATION]
LogonUser = advapi32.LogonUserW
LogonUser.argtypes = [LPCWSTR, LPCWSTR, LPCWSTR, DWORD, DWORD, POINTER(HANDLE)]
LogonUser.restype = BOOL
GetUserNameA = advapi32.GetUserNameA
GetUserNameA.restype = BOOL

gdi32 = WinDLL("gdi32", use_last_error=True)
CreateCompatibleDC = gdi32.CreateCompatibleDC
CreateCompatibleDC.argtypes = [HDC]
CreateCompatibleDC.restype = HDC
CreateCompatibleBitmap = gdi32.CreateCompatibleBitmap
CreateCompatibleBitmap.argtypes = [HDC, c_int, c_int]
CreateCompatibleBitmap.restype = HBITMAP
CreateBitmap = gdi32.CreateBitmap
CreateBitmap.argtypes = [INT, INT, UINT, UINT, POINTER(c_void_p)]
CreateBitmap.restype = HBITMAP
GetBitmapBits = gdi32.GetBitmapBits
GetBitmapBits.argtypes = [HGDIOBJ, LONG, LPVOID]
GetBitmapBits.restype = LONG
SelectObject = gdi32.SelectObject
SelectObject.argtypes = [HDC, HGDIOBJ]
SelectObject.restype = HGDIOBJ
BitBlt = gdi32.BitBlt
BitBlt.argtypes = [HDC, c_int, c_int, c_int, c_int, HDC, c_int, c_int, DWORD]
BitBlt.restype = BOOL
GetDeviceCaps = gdi32.GetDeviceCaps
GetDeviceCaps.argtypes = [HDC, c_int]
GetDeviceCaps.restype = c_int
GetSystemPaletteEntries = gdi32.GetSystemPaletteEntries
GetSystemPaletteEntries.restype = UINT
GetStockObject = gdi32.GetStockObject
GetStockObject.restype = HGDIOBJ
SetPixelV = gdi32.SetPixelV
CreateDIBSection = gdi32.CreateDIBSection
CreateDIBSection.restype = HBITMAP
CreateDIBSection.argtypes = [HANDLE, POINTER(BITMAPV5HEADER), UINT, POINTER(c_void_p), HANDLE, DWORD]
CreateDIBitmap = gdi32.CreateDIBitmap
CreateDIBitmap.restype = HBITMAP
CreateDIBitmap.argtypes = [HDC, PBITMAPINFOHEADER, DWORD, c_void_p, PBITMAPINFO, UINT]
DeleteObject = gdi32.DeleteObject
DeleteObject.argtypes = [HGDIOBJ]
DeleteObject.restype = BOOL
DeleteDC = gdi32.DeleteDC
DeleteDC.restype = BOOL
DeleteDC.argtypes = [HDC]
CreateDCA = gdi32.CreateDCA
CreateDCA.restype = HDC
CreateDCA.argtypes = [LPCSTR, LPCSTR, LPCSTR, DEVMODE]
ChoosePixelFormat = gdi32.ChoosePixelFormat
ChoosePixelFormat.argtypes = [HDC, c_void_p]
ChoosePixelFormat.restype = c_int
GetPixelFormat = gdi32.GetPixelFormat
GetPixelFormat.argtypes = [HDC]
GetPixelFormat.restype = c_int
SetPixelFormat = gdi32.SetPixelFormat
SetPixelFormat.argtypes = [HDC, c_int, c_void_p]
SetPixelFormat.restype = BOOL
DescribePixelFormat = gdi32.DescribePixelFormat
DescribePixelFormat.argtypes = [HDC, c_int, UINT, c_void_p]
DescribePixelFormat.restype = c_int
SwapBuffers = gdi32.SwapBuffers
SwapBuffers.argtypes = [HDC]
SwapBuffers.restype = BOOL
BeginPaint = user32.BeginPaint
BeginPaint.argtypes = [HWND, c_void_p]
BeginPaint.restype = HDC
EndPaint = user32.EndPaint
EndPaint.argtypes = [HWND, c_void_p]
EndPaint.restype = HDC
GetObjectA = gdi32.GetObjectA
GetObjectA.argtypes = [HGDIOBJ, INT, LPVOID]
GetObjectA.restype = INT

# wrap EnumDisplayMonitors to hide the callback function:
MonitorEnumProc = WINFUNCTYPE(BOOL, HMONITOR, HDC, POINTER(RECT), LPARAM)
_EnumDisplayMonitors.argtypes = [HDC, POINTER(RECT), MonitorEnumProc, LPARAM]
_EnumDisplayMonitors.restype = BOOL


def EnumDisplayMonitors() -> list:
    results = []

    def _callback(monitor, _dc, _rect, _data):
        results.append(monitor)
        return 1

    callback = MonitorEnumProc(_callback)
    _EnumDisplayMonitors(0, None, callback, 0)
    return results


def GetIntSystemParametersInfo(key) -> int | None:
    rv = INT()
    r = SystemParametersInfoA(key, 0, byref(rv), 0)
    if r == 0:
        return None
    return rv.value


class WNDCLASSEX(Structure):
    _fields_ = [
        ("cbSize", UINT),
        ("style", UINT),
        ("lpfnWndProc", WNDPROC),
        ("cbClsExtra", INT),
        ("cbWndExtra", INT),
        ("hInstance", HANDLE),
        ("hIcon", HANDLE),
        ("hCursor", HANDLE),
        ("hbrBackground", HANDLE),
        ("lpszMenuName", LPCWSTR),
        ("lpszClassName", LPCWSTR),
        ("hIconSm", HANDLE),
    ]


# GUID = c_ubyte * 16


class GUID(Structure):
    # noinspection PyTypeChecker
    _fields_ = [
        ('Data1', c_ulong),
        ('Data2', c_ushort),
        ('Data3', c_ushort),
        ('Data4', c_ubyte * 8),
    ]

    def __str__(self):
        return "{%08x-%04x-%04x-%s-%s}" % (
            self.Data1,
            self.Data2,
            self.Data3,
            ''.join(["%02x" % d for d in self.Data4[:2]]),
            ''.join(["%02x" % d for d in self.Data4[2:]]),
        )


IID = GUID
REFIID = POINTER(IID)

ERROR_PIPE_NOT_CONNECTED = 233
ERROR_MORE_DATA = 234
ERROR_BROKEN_PIPE = 109
ERROR_NO_DATA = 232
ERROR_HANDLE_EOF = 38
ERROR_IO_INCOMPLETE = 996
ERROR_IO_PENDING = 997
ERROR_CANCELLED = 1223
ERROR_ACCESS_DENIED = 5
ERROR_INVALID_HANDLE = 6
ERROR_OPERATION_ABORTED = 995
ERROR_INVALID_PARAMETER = 87
ERROR_SUCCESS = 0
ERROR_COUNTER_TIMEOUT = 1121
ERROR_PIPE_BUSY = 231

IO_ERROR_STR = {
    ERROR_PIPE_NOT_CONNECTED: "PIPE_NOT_CONNECTED",
    ERROR_MORE_DATA: "MORE_DATA",
    ERROR_BROKEN_PIPE: "BROKEN_PIPE",
    ERROR_NO_DATA: "NO_DATA",
    ERROR_HANDLE_EOF: "HANDLE_EOF",
    ERROR_IO_INCOMPLETE: "IO_INCOMPLETE",
    ERROR_IO_PENDING: "IO_PENDING",
    ERROR_CANCELLED: "CANCELLED",
    ERROR_ACCESS_DENIED: "ACCESS_DENIED",
    ERROR_INVALID_HANDLE: "INVALID_HANDLE",
    ERROR_OPERATION_ABORTED: "OPERATION_ABORTED",
    ERROR_INVALID_PARAMETER: "INVALID_PARAMETER",
    ERROR_SUCCESS: "SUCCESS",
    ERROR_COUNTER_TIMEOUT: "COUNTER_TIMEOUT",
    ERROR_PIPE_BUSY: "PIPE_BUSY",
}

# https://gist.github.com/EBNull/6135237
LANG_NEUTRAL = 0x00
SUBLANG_NEUTRAL = 0x00
SUBLANG_DEFAULT = 0x01

LANG_ENGLISH = 0x09
SUBLANG_ENGLISH_US = 0x01


def MAKELANGID(primary, sublang) -> int:
    return (primary & 0xFF) | (sublang & 0xFF) << 16


LCID_ENGLISH = MAKELANGID(LANG_ENGLISH, SUBLANG_ENGLISH_US)
LCID_DEFAULT = MAKELANGID(LANG_NEUTRAL, SUBLANG_DEFAULT)
LCID_NEUTRAL = MAKELANGID(LANG_NEUTRAL, SUBLANG_NEUTRAL)


def FormatMessageSystem(message_id, langid: int = LCID_ENGLISH) -> str:
    from xpra.platform.win32.constants import (
        FORMAT_MESSAGE_ALLOCATE_BUFFER, FORMAT_MESSAGE_FROM_SYSTEM, FORMAT_MESSAGE_IGNORE_INSERTS,
    )
    sys_flag = FORMAT_MESSAGE_ALLOCATE_BUFFER | FORMAT_MESSAGE_FROM_SYSTEM | FORMAT_MESSAGE_IGNORE_INSERTS
    bufptr = LPWSTR()
    chars = kernel32.FormatMessageW(sys_flag, None, message_id, langid, byref(bufptr), 0, None)
    if not chars:
        chars = FormatMessageW(sys_flag, None, message_id, LCID_NEUTRAL, byref(bufptr), 0, None)
        if not chars:
            return str(message_id)
    if not bufptr.value:
        return str(message_id)
    val = bufptr.value[:chars]
    LocalFree(bufptr)
    return str(val)
