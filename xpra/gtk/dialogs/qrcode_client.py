# This file is part of Xpra.
# Copyright (C) 2020 Antoine Martin <antoine@xpra.org>
# Xpra is released under the terms of the GNU GPL v2, or, at your option, any
# later version. See the file COPYING for details.

import sys
from typing import Any

from xpra.common import noerr
from xpra.util.objects import typedict
from xpra.util.env import envbool
from xpra.os_util import gi_import
from xpra.util.system import SIGNAMES
from xpra.util.str_fn import bytestostr
from xpra.exit_codes import ExitCode, ExitValue
from xpra.gtk.window import add_close_accel
from xpra.gtk.widget import label
from xpra.gtk.pixbuf import get_icon_pixbuf
from xpra.gtk.signals import install_signal_handlers
from xpra.gtk.css_overrides import inject_css_overrides
from xpra.client.base.client import XpraClientBase
from xpra.client.base.command import InfoXpraClient
from xpra.platform.gui import force_focus
from xpra.gtk.dialogs.qrcode import qr_pixbuf
from xpra.log import Logger

Gtk = gi_import("Gtk")
GLib = gi_import("GLib")

log = Logger("client", "util")

IPV6 = envbool("XPRA_IPV6", False)

inject_css_overrides()


def dpath(caps: typedict, *path) -> Any:
    d: typedict = caps
    for x in path:
        val = d.dictget(x)
        if not val:
            return None
        d = typedict(val)
    return d


class QRCodeClient(InfoXpraClient):

    def do_command(self, caps: typedict) -> None:
        sockets = dpath(caps, "network", "sockets")
        if not sockets:
            log.error("Error: network.sockets path not found in server info response")
            super().quit(ExitCode.PACKET_FAILURE)
            return
        # this will also prevent timeouts:
        self._protocol.close()
        self.exit_code = 0
        addr_types: dict[tuple[str, int], list[str]] = {}
        for socktype in ("ws", "wss"):
            sockdefs = typedict(sockets.dictget(socktype, {}))
            addresses = sockdefs.tupleget("addresses", ())
            for address in addresses:
                try:
                    host, port = address
                except (ValueError, IndexError):
                    continue
                host = bytestostr(host)
                if host.startswith("127.0.0.") or host.startswith("::1"):
                    continue
                if host.find(":") >= 0:
                    if IPV6:
                        host = "[%s]" % host
                    else:
                        continue
                addr_types.setdefault((host, port), []).append(socktype)
        log("addr_types=%s", addr_types)
        if addr_types:
            uris = []
            for addr, socktypes in addr_types.items():
                host, port = addr
                proto = "http" if "ws" in socktypes else "https"
                if (proto == "http" and port == 80) or (proto == "https" and port == 443):
                    uri = "%s://%s/" % (proto, host)
                else:
                    uri = "%s://%s:%i/" % (proto, host, port)
                uris.append(uri)

            def show_addresses() -> None:
                w = QRCodeWindow(uris)
                w.show_all()

            GLib.idle_add(show_addresses)
        else:
            noerr(sys.stdout.write, "no addresses found")
            noerr(sys.stdout.flush)
            super().quit(ExitCode.OK)

    def exit_loop(self) -> None:
        Gtk.main_quit()

    def quit(self, exit_code: ExitValue = 0) -> None:
        # only exit if we encountered an error
        # InfoXpraClient calls quit(ExitCode.OK) on `connection-lost`,
        # but we don't want to exit then
        if exit_code != 0:
            super().quit(exit_code)

    def run(self) -> ExitValue:
        # override so we can use a GTK main loop instead
        XpraClientBase.run(self)
        Gtk.main()
        return self.exit_code


class QRCodeWindow(Gtk.Window):

    def __init__(self, uris):
        self.exit_code = None
        super().__init__(type=Gtk.WindowType.TOPLEVEL)
        self.connect("delete_event", self.exit)
        title = "Xpra Server QR Codes"
        n = len(uris)
        self.set_title(title)
        self.set_size_request(512 * n, 580)
        self.set_position(Gtk.WindowPosition.CENTER)
        icon = get_icon_pixbuf("xpra.png")
        if icon:
            self.set_icon(icon)
        hbox = Gtk.HBox(homogeneous=True, spacing=20)
        for uri in uris:
            vbox = Gtk.VBox(homogeneous=False, spacing=10)
            vbox.add(label(uri))
            pixbuf = qr_pixbuf(uri, width=360, height=360)
            image = Gtk.Image().new_from_pixbuf(pixbuf)
            vbox.add(image)
            hbox.add(vbox)
        self.add(hbox)
        add_close_accel(self, self.exit)
        install_signal_handlers("", self.handle_signal)

    def handle_signal(self, signum, frame=None):
        log("handle_signal(%s, %s)", SIGNAMES.get(signum, signum), frame)
        self.exit_code = 128 - (signum or 0)
        GLib.idle_add(self.exit)

    def run(self) -> ExitValue:
        self.show_all()
        force_focus()
        self.present()
        if Gtk.main_level() == 0:
            Gtk.main()
        return self.exit_code or 0

    def exit(self, *args):
        log("exit%s calling %s", args, Gtk.main_quit)
        if self.exit_code is None:
            self.exit_code = 0
        Gtk.main_quit()


def do_main(opts):
    import os
    if os.environ.get("XPRA_HIDE_DOCK") is None:
        os.environ["XPRA_HIDE_DOCK"] = "1"
    from xpra.platform import program_context
    with program_context("qrcode", "QRCode"):
        Gtk.Window.set_auto_startup_notification(setting=False)
        c = QRCodeClient(opts)
        # add_close_accel(w, Gtk.main_quit)
        return c.run()


def main(_args):
    from xpra.scripts.config import make_defaults_struct
    defaults = make_defaults_struct()
    return do_main(defaults)


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main(sys.argv))
