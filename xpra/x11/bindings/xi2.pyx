# This file is part of Xpra.
# Copyright (C) 2017 Antoine Martin <antoine@xpra.org>
# Xpra is released under the terms of the GNU GPL v2, or, at your option, any
# later version. See the file COPYING for details.

import struct
from typing import Dict
from collections import deque

from xpra.log import Logger
log = Logger("x11", "bindings", "xinput")

from xpra.gtk.error import xlog
from xpra.x11.common import X11Event
from xpra.util.str_fn import hexstr

from libc.string cimport memset  # pylint: disable=syntax-error
from xpra.x11.bindings.xlib cimport (
    Display, Bool, Time, Window, Atom, Status,
    XGenericEventCookie,
    XQueryExtension,
    XGetEventData, XFreeEventData, XDefaultRootWindow, XQueryPointer,
    XFlush,
    XInternAtom, XFree,
    BadRequest, Success, XIAnyPropertyType,
)
from libc.stdint cimport uintptr_t   # pylint: disable=syntax-error


######
# Xlib primitives and constants
######

ctypedef unsigned long CARD32
DEF XNone = 0

cdef extern from "X11/extensions/XInput2.h":
    int XI_LASTEVENT
    int XI_DeviceChanged
    int XI_KeyPress
    int XI_KeyRelease
    int XI_ButtonPress
    int XI_ButtonRelease
    int XI_Motion
    int XI_Enter
    int XI_Leave
    int XI_FocusIn
    int XI_FocusOut
    int XI_HierarchyChanged
    int XI_PropertyEvent
    int XI_RawKeyPress
    int XI_RawKeyRelease
    int XI_RawButtonPress
    int XI_RawButtonRelease
    int XI_RawMotion
    int XI_TouchBegin
    int XI_TouchUpdate
    int XI_TouchEnd
    int XI_TouchOwnership
    int XI_RawTouchBegin
    int XI_RawTouchUpdate
    int XI_RawTouchEnd

    int XIMasterPointer
    int XIMasterKeyboard
    int XISlavePointer
    int XISlaveKeyboard
    int XIFloatingSlave

    int XIButtonClass
    int XIKeyClass
    int XIValuatorClass
    int XIScrollClass
    int XITouchClass

    int XIAllDevices
    int XIAllMasterDevices

    ctypedef struct XIValuatorState:
        int           mask_len
        unsigned char *mask
        double        *values

    ctypedef struct XIEvent:
        int           type
        unsigned long serial
        Bool          send_event
        Display       *display
        int           extension
        int           evtype
        Time          time

    ctypedef struct XIRawEvent:
        int           type      #GenericEvent
        unsigned long serial
        Bool          send_event
        Display       *display
        int           extension #XI extension offset
        int           evtype    #XI_RawKeyPress, XI_RawKeyRelease, etc
        Time          time
        int           deviceid
        int           sourceid
        int           detail
        int           flags
        XIValuatorState valuators
        double        *raw_values

    ctypedef struct XIButtonState:
        int           mask_len
        unsigned char *mask

    ctypedef struct XIModifierState:
        int    base
        int    latched
        int    locked
        int    effective

    ctypedef XIModifierState XIGroupState

    ctypedef struct XIDeviceEvent:
        int           type
        unsigned long serial
        Bool          send_event
        Display       *display
        int           extension
        int           evtype
        Time          time
        int           deviceid
        int           sourceid
        int           detail
        Window        root
        Window        event
        Window        child
        double        root_x
        double        root_y
        double        event_x
        double        event_y
        int           flags
        XIButtonState       buttons
        XIValuatorState     valuators
        XIModifierState     mods
        XIGroupState        group

    ctypedef struct XIHierarchyInfo:
        int           deviceid
        int           attachment
        int           use
        Bool          enabled
        int           flags

    ctypedef struct XIHierarchyEvent:
        int           type
        unsigned long serial
        Bool          send_event
        Display       *display
        int           extension
        int           evtype            #XI_HierarchyChanged
        Time          time
        int           flags
        int           num_info
        XIHierarchyInfo *info

    ctypedef struct XIEventMask:
        int                 deviceid
        int                 mask_len
        unsigned char*      mask

    ctypedef struct XIAnyClassInfo:
        int         type
        int         sourceid

    ctypedef struct XIDeviceInfo:
        int                 deviceid
        char                *name
        int                 use
        int                 attachment
        Bool                enabled
        int                 num_classes
        XIAnyClassInfo      **classes

    ctypedef struct XIButtonClassInfo:
        int         type
        int         sourceid
        int         num_buttons
        Atom        *labels
        XIButtonState state

    ctypedef struct XIKeyClassInfo:
        int         type
        int         sourceid
        int         num_keycodes
        int         *keycodes

    ctypedef struct XIValuatorClassInfo:
        int         type
        int         sourceid
        int         number
        Atom        label
        double      min
        double      max
        double      value
        int         resolution
        int         mode

    ctypedef struct XIScrollClassInfo:
        int         type
        int         sourceid
        int         number
        int         scroll_type
        double      increment
        int         flags

    ctypedef struct XITouchClassInfo:
        int         type
        int         sourceid
        int         mode
        int         num_touches

    Status XIQueryVersion(Display *display, int *major_version_inout, int *minor_version_inout)
    Status XISelectEvents(Display *display, Window win, XIEventMask *masks, int num_masks)
    XIDeviceInfo* XIQueryDevice(Display *display, int deviceid, int *ndevices_return)
    void XIFreeDeviceInfo(XIDeviceInfo *info)
    Atom *XIListProperties(Display *display, int deviceid, int *num_props_return)
    Status XIGetProperty(Display *display, int deviceid, Atom property, long offset, long length,
                         Bool delete_property, Atom type, Atom *type_return,
                         int *format_return, unsigned long *num_items_return,
                         unsigned long *bytes_after_return, unsigned char **data)


DEF MAX_XI_EVENTS = 64
DEF XI_EVENT_MASK_SIZE = (MAX_XI_EVENTS+7)//8

XI_EVENT_NAMES = {
    XI_DeviceChanged    : "XI_DeviceChanged",
    XI_KeyPress         : "XI_KeyPress",
    XI_KeyRelease       : "XI_KeyRelease",
    XI_ButtonPress      : "XI_ButtonPress",
    XI_ButtonRelease    : "XI_ButtonRelease",
    XI_Motion           : "XI_Motion",
    XI_Enter            : "XI_Enter",
    XI_Leave            : "XI_Leave",
    XI_FocusIn          : "XI_FocusIn",
    XI_FocusOut         : "XI_FocusOut",
    XI_HierarchyChanged : "XI_HierarchyChanged",
    XI_PropertyEvent    : "XI_PropertyEvent",
    XI_RawKeyPress      : "XI_RawKeyPress",
    XI_RawKeyRelease    : "XI_RawKeyRelease",
    XI_RawButtonPress   : "XI_RawButtonPress",
    XI_RawButtonRelease : "XI_RawButtonRelease",
    XI_RawMotion        : "XI_RawMotion",
    XI_TouchBegin       : "XI_TouchBegin",
    XI_TouchUpdate      : "XI_TouchUpdate",
    XI_TouchEnd         : "XI_TouchEnd",
    XI_TouchOwnership   : "XI_TouchOwnership",
    XI_RawTouchBegin    : "XI_RawTouchBegin",
    XI_RawTouchUpdate   : "XI_RawTouchUpdate",
    XI_RawTouchEnd      : "XI_RawTouchEnd",
}

XI_USE = {
    XIMasterPointer     : "master pointer",
    XIMasterKeyboard    : "master keyboard",
    XISlavePointer      : "slave pointer",
    XISlaveKeyboard     : "slave keyboard",
    XIFloatingSlave     : "floating slave",
}

CLASS_INFO = {
    XIButtonClass       : "button",
    XIKeyClass          : "key",
    XIValuatorClass     : "valuator",
    XIScrollClass       : "scroll",
    XITouchClass        : "touch",
}


from xpra.x11.bindings.core cimport X11CoreBindingsInstance


cdef class X11XI2BindingsInstance(X11CoreBindingsInstance):

    cdef int opcode
    cdef object events
    cdef object event_handlers
    cdef object device_cache

    def __init__(self):
        self.opcode = -1
        self.event_handlers = {}
        self.device_cache = {}
        self.reset_events()

    def __repr__(self):
        return "X11XI2Bindings(%s)" % self.display_name

    def connect(self, window, event, handler) -> None:
        self.event_handlers.setdefault(window, {})[event] = handler

    def disconnect(self, window) -> None:
        self.event_handlers.pop(window, None)

    def reset_events(self) -> None:
        self.events = deque(maxlen=100)

    def find_event(self, event_name: str, serial: int) -> int:
        for x in reversed(self.events):
            #log.info("find_event(%s, %#x) checking %s", event_name, serial, x)
            if x.name==event_name and x.serial==serial:
                #log.info("matched")
                return x
            if x.serial<serial:
                #log.info("serial too old")
                return 0
        return 0

    def find_events(self, event_name: str, windows) -> List[int]:
        cdef Window found = 0
        cdef Window window
        matches = []
        for x in reversed(self.events):
            window = x.xid
            if x.name==event_name and ((found>0 and found==window) or (found==0 and window in windows)):
                matches.append(x)
                found = window
            elif found:
                break
        return matches

    def get_xi_version(self, int major=2, int minor=2) -> Tuple[int, int]:
        self.context_check("get_xi_version")
        cdef int rmajor = major, rminor = minor
        cdef int rc = XIQueryVersion(self.display, &rmajor, &rminor)
        if rc == BadRequest:
            log.warn("Warning: no XI2 %i.%i support,", major, minor)
            log.warn(" server supports version %i.%i only", rmajor, rminor)
            return 0, 0
        log("get_xi_version%s=%s", (major, minor), (rmajor, rminor))
        return rmajor, rminor

    cdef int get_xi_opcode(self, int major=2, int minor=2):
        if self.opcode!=-1:
            return self.opcode
        cdef int opcode, event, error
        if not XQueryExtension(self.display, "XInputExtension", &opcode, &event, &error):
            log.warn("Warning: XI2 events are not supported")
            self.opcode = 0
            return 0
        cdef int rmajor = major, rminor = minor
        cdef int rc = XIQueryVersion(self.display, &rmajor, &rminor)
        if rc == BadRequest:
            log.warn("Warning: no XI2 %i.%i support,", major, minor)
            log.warn(" server supports version %i.%i only", rmajor, rminor)
            self.opcode = 0
            return 0
        elif rc:
            log.warn("Warning: Xlib bug querying XI2, code %i", rc)
            self.opcode = 0
            return 0
        self.opcode = opcode
        log("get_xi_opcode%s=%i", (major, minor), opcode)
        return opcode

    cdef void register_parser(self):
        log("register_parser()")
        if self.opcode>0:
            from xpra.x11.bindings.events import add_x_event_parser
            add_x_event_parser(self.opcode, self.parse_xi_event)

    cdef void register_gdk_events(self):
        log("register_gdk_events()")
        if self.opcode<=0:
            return
        global XI_EVENT_NAMES
        from xpra.x11.bindings.events import add_x_event_signal, add_x_event_type_name
        for e, xi_event_name in {
            XI_DeviceChanged    : "device-changed",
            XI_KeyPress         : "key-press",
            XI_KeyRelease       : "key-release",
            XI_ButtonPress      : "button-press",
            XI_ButtonRelease    : "button-release",
            XI_Motion           : "motion",
            XI_Enter            : "enter",
            XI_Leave            : "leave",
            XI_FocusIn          : "focus-in",
            XI_FocusOut         : "focus-out",
            XI_HierarchyChanged : "focus-changed",
            XI_PropertyEvent    : "property-event",
            XI_RawKeyPress      : "raw-key-press",
            XI_RawKeyRelease    : "raw-key-release",
            XI_RawButtonPress   : "raw-button-press",
            XI_RawButtonRelease : "raw-button-release",
            XI_RawMotion        : "raw-motion",
            XI_TouchBegin       : "touch-begin",
            XI_TouchUpdate      : "touch-update",
            XI_TouchEnd         : "touch-end",
            XI_TouchOwnership   : "touch-ownership",
            XI_RawTouchBegin    : "raw-touch-begin",
            XI_RawTouchUpdate   : "raw-touch-update",
            XI_RawTouchEnd      : "raw-touch-end",
        }.items():
            event = self.opcode+e
            add_x_event_signal(event, ("xi-%s" % xi_event_name, None))
            name = XI_EVENT_NAMES[e]
            add_x_event_type_name(event, name)

    def select_xi2_events(self) -> None:
        self.context_check("select_xi2_events")
        cdef Window win = XDefaultRootWindow(self.display)
        log("select_xi2_events() root window=%#x", win)
        assert XI_LASTEVENT<MAX_XI_EVENTS, "bug: source needs to be updated, XI_LASTEVENT=%i" % XI_LASTEVENT
        cdef XIEventMask evmasks[1]
        cdef unsigned char mask1[XI_EVENT_MASK_SIZE]
        memset(mask1, 0, XI_EVENT_MASK_SIZE)
        #define XISetMask(ptr, event)   (((unsigned char*)(ptr))[(event)>>3] |=  (1 << ((event) & 7)))
        #XISetMask(mask1, XI_RawMotion)
        for e in (
            XI_KeyPress, XI_KeyRelease,
            XI_Motion,
            XI_HierarchyChanged,
            XI_ButtonPress, XI_ButtonRelease,
            XI_RawButtonPress, XI_RawButtonRelease,
            XI_TouchBegin, XI_TouchUpdate, XI_TouchEnd,
            XI_RawTouchBegin, XI_RawTouchUpdate, XI_RawTouchEnd,
            XI_RawMotion,
            ):
            mask1[e>>3] |= (1<< (e & 0x7))
        evmasks[0].deviceid = XIAllDevices  #XIAllMasterDevices    #XIAllDevices
        evmasks[0].mask_len = XI_EVENT_MASK_SIZE
        evmasks[0].mask = mask1
        XISelectEvents(self.display, win, evmasks, 1)
        XFlush(self.display)

    def parse_xi_event(self, cookie):
        with xlog:
            return self.do_parse_xi_event(cookie)

    cdef object do_parse_xi_event(self, uintptr_t _cookie):
        self.context_check("parse_xi_event")
        cdef XGenericEventCookie *cookie = <XGenericEventCookie*> _cookie
        cdef XIHierarchyEvent *hierarchy_e
        cdef XIRawEvent *raw
        cdef int i = 0
        if not XGetEventData(self.display, cookie):
            log("parse_xi_event(%#x) no event data", _cookie)
            return None
        cdef XIEvent *xie = <XIEvent*> cookie.data
        #cdef XIDeviceEvent *device_e = <XIDeviceEvent*> cookie.data
        cdef int xi_type = cookie.evtype
        etype = self.opcode+xi_type
        global XI_EVENT_NAMES
        event_name = XI_EVENT_NAMES.get(xi_type)
        if not event_name:
            log("parse_xi_event(%#x) unknown XI2 event code: %i", _cookie, xi_type)
            return None

        #don't parse the same thing again:
        if len(self.events)>0:
            last_event = self.events[-1]
            if last_event.serial==xie.serial and last_event.type==etype:
                log("parse_xi_event(%#x) repeated %s event skipped (%s)",
                    _cookie, last_event.name, event_name)
                return None

        pyev = X11Event(event_name)
        pyev.type = etype
        pyev.send_event = bool(xie.send_event)
        pyev.serial = xie.serial
        pyev.time = int(xie.time)
        pyev.window = int(XDefaultRootWindow(self.display))

        device_info = None
        if xi_type in (XI_KeyPress, XI_KeyRelease,
                       XI_ButtonPress, XI_ButtonRelease,
                       XI_Motion,
                       XI_TouchBegin, XI_TouchUpdate, XI_TouchEnd):
            device = <XIDeviceEvent*> cookie.data
            #pyev.source = device.sourceid    #always 0
            device_info = self.device_cache.get(device.deviceid)
            pyev.device = device.deviceid
            pyev.detail = device.detail
            pyev.flags = device.flags
            pyev.window = int(device.child or device.event or device.root)
            pyev.x_root = device.root_x
            pyev.y_root = device.root_y
            pyev.x = device.event_x
            pyev.y = device.event_y
            #mask = []
            valuators = {}
            valuator = 0
            for i in range(device.valuators.mask_len*8):
                if device.valuators.mask[i>>3] & (1 << (i & 0x7)):
                    valuators[i] = device.valuators.values[valuator]
                    valuator += 1
            pyev.valuators = valuators
            buttons = []
            for i in range(device.buttons.mask_len):
                if device.buttons.mask[i>>3] & (1<< (i & 0x7)):
                    buttons.append(i)
            pyev.buttons = buttons
            state = []
            pyev.state = state
            pyev.modifiers = {
                "base"      : device.mods.base,
                "latched"   : device.mods.latched,
                "locked"    : device.mods.locked,
                "effective" : device.mods.effective,
            }
            #make it compatible with gdk events:
            pyev.state = device.mods.effective
        elif xi_type in (XI_RawKeyPress, XI_RawKeyRelease,
                         XI_RawButtonPress, XI_RawButtonRelease,
                         XI_RawMotion,
                         XI_RawTouchBegin, XI_RawTouchUpdate, XI_RawTouchEnd):
            raw = <XIRawEvent*> cookie.data
            valuators = {}
            raw_valuators = {}
            valuator = 0
            for i in range(raw.valuators.mask_len*8):
                if raw.valuators.mask[i>>3] & (1 << (i & 0x7)):
                    valuators[i] = raw.valuators.values[valuator]
                    raw_valuators[i] = raw.raw_values[valuator]
                    valuator += 1
            pyev.valuators = valuators
            pyev.raw_valuators = raw_valuators
        elif xi_type == XI_HierarchyChanged:
            hierarchy_e = <XIHierarchyEvent*> cookie.data
            pyev.window = 0
            pyev.flags = hierarchy_e.flags
            #for i in range(hierarchy_e.num_info):
            #XIHierarchyInfo *info
        XFreeEventData(self.display, cookie)
        pyev.xid = pyev.window
        self.events.append(pyev)

        handler = self.event_handlers.get(pyev.window, {}).get(event_name)
        if handler:
            log("parse_xi_event: %s, device_info=%s, handler=%s", pyev, device_info, handler)
            handler(pyev, device_info)
        log("parse_xi_event: no handler for %s", event_name)
        return None

    def get_devices(self, show_all=True, show_disabled=False) -> Dict[int, Dict[str, Any]]:
        log("get_devices(%s, %s)", show_all, show_disabled)
        self.context_check("get_devices")
        global XI_USE
        cdef int ndevices, i, j

        cdef XIDeviceInfo *device
        cdef XIAnyClassInfo *clazz
        if show_all:
            device_types = XIAllDevices
        else:
            device_types = XIAllMasterDevices
        cdef XIDeviceInfo *devices = XIQueryDevice(self.display, device_types, &ndevices)
        dinfo = {}
        for i in range(ndevices):
            device = &devices[i]
            if not device.enabled and not show_disabled:
                continue
            info = {
                "name"          : device.name,
                "use"           : XI_USE.get(device.use, "unknown use: %i" % device.use),
                "attachment"    : device.attachment,
                "enabled"       : device.enabled,
                }
            classes = {}
            for j in range(device.num_classes):
                clazz = device.classes[j]
                classes[j] = self.get_class_info(clazz)
            info["classes"] = classes
            properties = self.get_device_properties(device.deviceid)
            if properties:
                info["properties"] = properties
            log("[%i] %s: %s", device.deviceid, device.name, info)
            dinfo[device.deviceid] = info
        XIFreeDeviceInfo(devices)
        self.device_cache = dinfo
        return dinfo

    def get_device_properties(self, deviceid) -> Dict[str, Any]:
        self.context_check("get_device_properties")
        cdef int nprops, i
        cdef Atom *atoms = XIListProperties(self.display, deviceid, &nprops)
        if atoms==NULL or nprops==0:
            return None
        props = {}
        for i in range(nprops):
            value = self.get_device_property(deviceid, atoms[i])
            if value is not None:
                prop_name = self.get_atom_name(atoms[i])
                props[prop_name] = value
        return props

    cdef object get_device_property(self, int deviceid, Atom property, req_type=0):
        #code mostly duplicated from window bindings XGetWindowProperty:
        cdef int buffer_size = 64 * 1024
        cdef Atom xactual_type = <Atom> 0
        cdef int actual_format = 0
        cdef unsigned long nitems = 0, bytes_after = 0
        cdef unsigned char *prop = NULL
        cdef Atom xreq_type = XIAnyPropertyType
        if req_type:
            xreq_type = self.get_xatom(req_type)

        cdef Status status = XIGetProperty(self.display,
                               deviceid, property,
                               0,
                               buffer_size//4,
                               False,
                               xreq_type, &xactual_type,
                               &actual_format, &nitems, &bytes_after, &prop)
        if status != Success:
            raise RuntimeError("failed to retrieve XI property")
        if xactual_type == XNone:
            return None
        if xreq_type and xreq_type != xactual_type:
            raise RuntimeError("expected %s but got %s" % (req_type, self.get_atom_name(xactual_type)))
        # This should only occur for bad property types:
        assert not (bytes_after and not nitems)
        if bytes_after:
            raise RuntimeError("reserved %i bytes for buffer, but data is bigger by %i bytes!" % (buffer_size, bytes_after))
        assert actual_format > 0
        #unlike XGetProperty, we don't need to special case 64-bit:
        cdef int bytes_per_item = actual_format // 8
        cdef int nbytes = bytes_per_item * nitems
        data = (<char *> prop)[:nbytes]
        XFree(prop)
        prop_type = self.get_atom_name(xactual_type)
        log("hex=%s (type=%s, nitems=%i, bytes per item=%i, actual format=%i)",
            hexstr(data), prop_type, nitems, bytes_per_item, actual_format)
        fmt = None
        if prop_type=="INTEGER":
            fmt = {
                8   : b"b",
                16  : b"h",
                32  : b"i",
            }.get(actual_format)
        elif prop_type=="CARDINAL":
            fmt = {
                8   : b"B",
                16  : b"H",
                32  : b"I",
            }.get(actual_format)
        elif prop_type=="FLOAT":
            fmt = b"f"
        if fmt:
            value = struct.unpack(fmt*nitems, data)
            if nitems==1:
                return value[0]
            return value
        return data

    cdef dict get_class_info(self, XIAnyClassInfo *class_info):
        cdef int i
        cdef XIButtonClassInfo *button
        cdef XIKeyClassInfo *key
        cdef XIValuatorClassInfo *valuator
        cdef XIScrollClassInfo *scroll
        cdef XITouchClassInfo *touch
        info = {
            "type"      : CLASS_INFO.get(class_info.type, "unknown type: %i" % class_info.type),
            "sourceid"  : class_info.sourceid,
        }
        if class_info.type==XIButtonClass:
            button = <XIButtonClassInfo*> class_info
            buttons = []
            for i in range(button.num_buttons):
                if button.labels[i]>0:
                    buttons.append(self.get_atom_name(button.labels[i]))
            info["buttons"] = buttons
            #XIButtonState state
        elif class_info.type==XIKeyClass:
            key = <XIKeyClassInfo*> class_info
            keys = []
            for i in range(key.num_keycodes):
                keys.append(key.keycodes[i])
        elif class_info.type==XIValuatorClass:
            valuator = <XIValuatorClassInfo*> class_info
            info |= {
                "number"    : valuator.number,
                "min"       : valuator.min,
                "max"       : valuator.max,
                "value"     : valuator.value,
                "resolution": valuator.resolution,
                "mode"      : valuator.mode,
            }
            if valuator.label:
                info["label"] = self.get_atom_name(valuator.label)
        elif class_info.type==XIScrollClass:
            scroll = <XIScrollClassInfo*> class_info
            info |= {
                "number"        : scroll.number,
                "scroll-type"   : scroll.scroll_type,
                "increment"     : scroll.increment,
                "flags"         : scroll.flags,
            }
        elif class_info.type==XITouchClass:
            touch = <XITouchClassInfo*> class_info
            info |= {
                "mode"          : touch.mode,
                "num-touches"   : touch.num_touches,
            }
        return info

    def gdk_inject(self) -> None:
        self.get_xi_opcode()
        #log.info("XInput Devices:")
        #from xpra.util.str_fn import print_nested_dict
        #print_nested_dict(self.get_devices(), print_fn=log.info)
        self.register_parser()
        self.register_gdk_events()
        #self.select_xi2_events()


cdef X11CoreBindingsInstance singleton = None


def X11XI2Bindings() -> X11CoreBindingsInstance:
    global singleton
    if singleton is None:
        singleton = X11XI2BindingsInstance()
    return singleton
