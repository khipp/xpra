#!/usr/bin/env python3
# Copyright (C) 2020 Antoine Martin <antoine@xpra.org>
# Xpra is released under the terms of the GNU GPL v2, or, at your option, any
# later version. See the file COPYING for details.

from xpra.os_util import gi_import
from xpra.platform import program_context
from xpra.platform.gui import force_focus
from xpra.gtk.util import get_default_root_window
from xpra.gtk.window import add_close_accel
from xpra.gtk.widget import label
from xpra.gtk.pixbuf import get_icon_pixbuf

Gtk = gi_import("Gtk")
GLib = gi_import("GLib")


def make_window() -> Gtk.Window:
    window = Gtk.Window(type=Gtk.WindowType.TOPLEVEL)
    window.set_title("Window Transient Test")
    window.set_size_request(400, 300)
    window.set_position(Gtk.WindowPosition.CENTER)
    window.connect("delete_event", Gtk.main_quit)
    icon = get_icon_pixbuf("windows.png")
    if icon:
        window.set_icon(icon)
    vbox = Gtk.VBox(homogeneous=False, spacing=0)

    btn = Gtk.Button(label="Create Transient")

    def create_transient(*_args) -> Gtk.Window:
        tw = Gtk.Window(type=Gtk.WindowType.TOPLEVEL)
        tw.set_size_request(200, 100)
        if icon:
            tw.set_icon(icon)
        tw.connect("delete_event", lambda x, y: tw.destroy())
        tw.set_transient_for(window)
        tw.add(label("Transient Window"))
        tw.show_all()

    btn.connect('clicked', create_transient)
    vbox.pack_start(btn, expand=False, fill=False, padding=10)

    btn = Gtk.Button(label="Create Transient (with 5 second delay)")

    def delayed_transient(*_args) -> None:
        GLib.timeout_add(5000, create_transient)

    btn.connect('clicked', delayed_transient)
    vbox.pack_start(btn, expand=False, fill=False, padding=10)

    btn = Gtk.Button(label="Create Root Transient")

    def create_root_transient(*_args) -> None:
        tw = Gtk.Window(type=Gtk.WindowType.TOPLEVEL)
        tw.set_size_request(200, 100)
        if icon:
            tw.set_icon(icon)
        tw.connect("delete_event", lambda x, y: tw.destroy())
        tw.realize()
        tw.get_window().set_transient_for(get_default_root_window())
        tw.add(label("Transient Root Window"))
        tw.show_all()

    btn.connect('clicked', create_root_transient)
    vbox.pack_start(btn, expand=False, fill=False, padding=10)
    window.add(vbox)
    return window


def main() -> int:
    with program_context("window-transient", "Window Transient"):
        w = make_window()
        add_close_accel(w, Gtk.main_quit)
        from xpra.gtk.signals import quit_on_signals
        quit_on_signals("transient window test")

        def show_with_focus() -> None:
            force_focus()
            w.show_all()
            w.present()

        GLib.idle_add(show_with_focus)
        Gtk.main()
        return 0


if __name__ == "__main__":
    import sys
    r = main()
    sys.exit(r)
