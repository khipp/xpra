#!/usr/bin/env python3

import sys

nid = 1


def notify(*_args) -> bool:
    global nid
    from xpra.notification.dbus_backend import DBUSNotifier, log
    log.enable_debug()
    notifier = DBUSNotifier()
    notifier.app_name_format = "%s"
    # ensure we can send the image-path hint:
    notifier.parse_hints = notifier.noparse_hints
    actions = ("0", "Hello", "1", "Goodbye")
    hints = {
        "image-path": "/usr/share/xpra/icons/encoding.png",
    }
    notifier.show_notify("dbus-id", None, nid, "xpra test app", 0, "",
                         "Notification %i Summary" % nid, "Notification %i Body" % nid,
                         actions, hints, 60*1000, "")
    nid += 1
    return True


def main():
    name = "test"
    if len(sys.argv) >= 2:
        name = sys.argv[1]
    from xpra.platform import program_context
    with program_context(name, name):
        notify()
        from gi.repository import GLib  # @UnresolvedImport
        GLib.timeout_add(60*1000, notify)
        loop = GLib.MainLoop()
        loop.run()


if __name__ == "__main__":
    main()
