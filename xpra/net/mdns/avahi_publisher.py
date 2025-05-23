#!/usr/bin/env python3
# This file is part of Xpra.
# Copyright (C) 2013 Antoine Martin <antoine@xpra.org>
# Xpra is released under the terms of the GNU GPL v2, or, at your option, any
# later version. See the file COPYING for details.

# taken from the code I wrote for winswitch

import avahi  # @UnresolvedImport
import dbus
from socket import if_nametoindex, if_indextoname

try:
    from dbus.exceptions import DBusException
except ImportError:
    # not available in all versions of the bindings?
    DBusException = Exception

from xpra.net.mdns import XPRA_TCP_MDNS_TYPE, XPRA_UDP_MDNS_TYPE, SHOW_INTERFACE
from xpra.dbus.common import init_system_bus
from xpra.net.net_util import get_iface
from xpra.log import Logger

log = Logger("network", "mdns")


def get_interface_index(host) -> int:
    log("get_interface_index(%s)", host)
    if host in ("0.0.0.0", "", "*", "::"):
        return avahi.IF_UNSPEC

    if not if_nametoindex:
        log.warn("Warning: cannot convert interface to index (if_nametoindex is missing)")
        log.warn(" so returning 'IF_UNSPEC', avahi will publish on ALL interfaces")
        return avahi.IF_UNSPEC

    iface = get_iface(host)
    log("get_iface(%s)=%s", host, iface)
    if not iface:
        return avahi.IF_UNSPEC

    index = if_nametoindex(iface)
    log("if_nametoindex(%s)=%s", iface, index)
    if iface is None:
        return avahi.IF_UNSPEC
    return index


class AvahiPublishers:
    """
    Aggregates a number of AvahiPublisher(s).
    This takes care of constructing the appropriate AvahiPublisher
    with the interface index and port for the given list of (host,port)s to broadcast on,
    and to convert the text dict into a TXT string.
    """

    def __init__(self, listen_on, service_name: str, service_type: str = XPRA_TCP_MDNS_TYPE, text_dict=None):
        log("AvahiPublishers%s", (listen_on, service_name, service_type, text_dict))
        self.publishers = []
        try:
            bus = init_system_bus()
        except Exception as e:
            log.warn("failed to connect to the system dbus: %s", e)
            log.warn(" either start a dbus session or disable mdns support")
            return
        for host, port in listen_on:
            iface_index = get_interface_index(host)
            log("iface_index(%s)=%s", host, iface_index)
            td = text_dict or {}
            if SHOW_INTERFACE and iface_index is not None:
                td = text_dict.copy()
                try:
                    td["iface"] = if_indextoname(iface_index)
                except OSError:
                    pass
            txt = []
            if text_dict:
                for k, v in td.items():
                    txt.append(f"{k}={v}")
            fqdn = host
            if host in ("0.0.0.0", "::"):
                fqdn = ""
            elif host:
                try:
                    import socket
                    fqdn = socket.gethostbyaddr(host)[0]
                    log("gethostbyaddr(%s)=%s", host, fqdn)
                    if fqdn.find(".") < 0:
                        fqdn = socket.getfqdn(host)
                        log("getfqdn(%s)=%s", host, fqdn)
                    if fqdn.find(".") < 0:
                        if fqdn:
                            fqdn += ".local"
                        log("cannot find a fully qualified domain name for '%s', using: %s", host, fqdn)
                except (OSError, IndexError):
                    log("failed to get hostbyaddr for '%s'", host, exc_info=True)
            self.publishers.append(AvahiPublisher(bus, service_name, port,
                                                  service_type, domain="", host=fqdn,
                                                  text=txt, interface=iface_index))

    def start(self) -> None:
        log("avahi:starting: %s", self.publishers)
        if not self.publishers:
            return
        all_err = True
        for publisher in self.publishers:
            if publisher.start():
                all_err = False
        if all_err:
            log.warn(" to avoid this warning, disable mdns support ")
            log.warn(" using the 'mdns=no' option")

    def stop(self) -> None:
        log("stopping: %s", self.publishers)
        for publisher in self.publishers:
            publisher.stop()

    def update_txt(self, txt) -> None:
        for publisher in self.publishers:
            publisher.update_txt(txt)


class AvahiPublisher:

    def __init__(self, bus, name, port, stype=XPRA_TCP_MDNS_TYPE,
                 domain="", host="", text=(), interface=avahi.IF_UNSPEC):
        log("AvahiPublisher%s", (bus, name, port, stype, domain, host, text, interface))
        self.bus = bus
        self.name = name
        self.stype = stype
        self.domain = domain
        if host == "::":
            host = ""
        self.host = host
        self.port = port
        self.text = avahi.string_array_to_txt_array(text)
        self.interface = interface
        self.server = None
        self.group = None

    def iface(self) -> str:
        if self.interface > 0:
            return "interface %i" % self.interface
        return "all interfaces"

    def host_str(self) -> str:
        return "%s %s:%s on %s" % (self.name, self.host, self.port, self.iface())

    def __repr__(self):
        return "AvahiPublisher(%s)" % self.host_str()

    def start(self) -> bool:
        try:
            self.server = dbus.Interface(self.bus.get_object(avahi.DBUS_NAME, avahi.DBUS_PATH_SERVER),
                                         avahi.DBUS_INTERFACE_SERVER)
            self.group = dbus.Interface(self.bus.get_object(avahi.DBUS_NAME, self.server.EntryGroupNew()),
                                        avahi.DBUS_INTERFACE_ENTRY_GROUP)
        except Exception as e:
            log.warn("failed to connect to avahi's dbus interface: %s", e)
            return False
        log("avahi dbus server=%s", self.server)
        log("avahi dbus group=%s", self.group)
        self.server.connect_to_signal("StateChanged", self.server_state_changed)
        return self.server_state_changed(self.server.GetState())

    def server_state_changed(self, state, error=None) -> bool:
        log("server_state_changed(%s, %s) on %s", state, error, self.server)
        if state == avahi.SERVER_COLLISION:
            log.error("Error: mdns server name collision")
            if error:
                log.error(" %s", error)
            log.error(" for name '%s' and port %i on %s", self.name, self.port, self.iface())
            self.stop()
            return False
        if state == avahi.SERVER_RUNNING:
            self.add_service()
            return True
        state_str = "unknown"
        for const in ("INVALID", "REGISTERING", "COLLISION", "FAILURE"):
            val = getattr(avahi, "SERVER_%s" % const, None)
            if val is not None and val == state:
                state_str = const
                break
        log.warn("Warning: mdns server state changed to '%s'", state_str)
        log.warn(" for name '%s' and port %i on %s", self.name, self.port, self.iface())
        return False

    def add_service(self) -> None:
        if not self.group:
            return
        try:
            args = (
                self.interface, avahi.PROTO_UNSPEC, dbus.UInt32(0),
                self.name, self.stype, self.domain, self.host,
                dbus.UInt16(self.port), self.text,
            )
            log("calling %s%s", self.group, args)
            self.group.AddService(*args)
            self.group.Commit()
            log("dbus service added")
        except DBusException as e:
            log("cannot add service", exc_info=True)
            # use try+except as older versions may not have those modules?
            message = e.get_dbus_message()
            dbus_error_name = e.get_dbus_name()
            log.error("Error starting publisher %s", self.host_str())
            if dbus_error_name == "org.freedesktop.Avahi.CollisionError":
                log.error(" another instance already claims this dbus name")
                log.estr(e)
                log.error(" %s", message)
            else:
                for line in str(e).splitlines():
                    for part in line.split(":", 1):
                        if part:
                            log.error(f" {part}")
            self.stop()

    def stop(self) -> None:
        group = self.group
        log("%s.stop() group=%s", self, group)
        if group:
            self.group = None
            try:
                group.Reset()
            except Exception as e:
                log.error("Error stopping avahi publisher %s:", self)
                log.estr(e)
        self.server = None

    def update_txt(self, txt) -> None:
        if not self.server:
            log("update_txt(%s) ignored, already stopped", txt)
            return
        if not self.group:
            log.warn("Warning: cannot update mdns record")
            log.warn(" publisher has already been stopped")
            return
        # prevent avahi from choking on ints:
        txt_strs = {k: str(v) for k, v in txt.items()}

        def reply_handler(*args):
            log("reply_handler%s", args)
            log("update_txt(%s) done", txt)

        def error_handler(*args):
            log("error_handler%s", args)
            log.warn("Warning: failed to update mDNS TXT record")
            log.warn(" for name '%s'", self.name)
            log.warn(" host=%s, port=%s", self.host, self.port)
            log.warn(" with new data:")
            for k, v in txt_strs.items():
                log.warn(" * %s=%s", k, v)

        txt_array = avahi.dict_to_txt_array(txt_strs)
        self.group.UpdateServiceTxt(self.interface,
                                    avahi.PROTO_UNSPEC, dbus.UInt32(0), self.name, self.stype, self.domain,
                                    txt_array, reply_handler=reply_handler,
                                    error_handler=error_handler)


def main() -> None:
    from xpra.os_util import gi_import
    GLib = gi_import("GLib")
    import random
    import signal
    port = int(20000 * random.random()) + 10000
    host = ""
    name = "test service"
    bus = init_system_bus()
    publishers = []

    def add(service_type: str = XPRA_TCP_MDNS_TYPE):
        publisher = AvahiPublisher(bus, name, port, stype=service_type, host=host, text=("somename=somevalue",))
        publishers.append(publisher)

        def start() -> None:
            publisher.start()

        def update_rec() -> None:
            publisher.update_txt({b"hello": b"world"})

        GLib.idle_add(start)
        GLib.timeout_add(5 * 1000, update_rec)

    add(XPRA_TCP_MDNS_TYPE)
    add(XPRA_UDP_MDNS_TYPE)
    loop = GLib.MainLoop()

    def exit_loop(*_args):
        loop.quit()
    signal.signal(signal.SIGTERM, exit_loop)
    loop.run()


if __name__ == "__main__":
    main()
