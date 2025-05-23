# This file is part of Xpra.
# This file is based on websockify/websocket.py from the websockify project
# Copyright (C) 2019 Antoine Martin <antoine@xpra.org>
# Copyright (C) 2011 Joel Martin
# Copyright (C) 2016 Pierre Ossman
# Licensed under LGPL version 3 (see docs/LICENSE.LGPL-3)

import struct

from xpra.common import SizedBuffer
from xpra.net.websockets.common import OPCODE
from xpra.net.websockets.mask import hybi_unmask


def close_packet(code: int = 1000, reason: str = "") -> bytes:
    data = struct.pack("!H", code)
    if reason:
        # should validate that encoded data length is less than 125, meh
        data += reason.encode("utf-8")
    header = encode_hybi_header(OPCODE.CLOSE, len(data), has_mask=False, fin=True)
    return header + data


def encode_hybi_header(opcode, payload_len, has_mask=False, fin=True) -> bytes:
    """ Encode a HyBi style WebSocket frame """
    if (opcode & 0x0f) != opcode:
        raise ValueError(f"invalid opcode {opcode:x}")
    mask_bit = 0x80 * has_mask
    b1 = opcode | (0x80 * fin)
    if payload_len <= 125:
        return struct.pack('>BB', b1, payload_len | mask_bit)
    if payload_len < 65536:
        return struct.pack('>BBH', b1, 126 | mask_bit, payload_len)
    return struct.pack('>BBQ', b1, 127 | mask_bit, payload_len)


def decode_hybi(buf: SizedBuffer) -> tuple[int, SizedBuffer, int, int] | None:
    """ Decode HyBi style WebSocket packets """
    blen = len(buf)
    hlen = 2
    if blen < hlen:
        # log("decode_hybi_header() buffer too small: %i", blen)
        return None

    b1, b2 = struct.unpack(">BB", buf[:2])
    opcode = b1 & 0x0f
    fin = bool(b1 & 0x80)
    masked = bool(b2 & 0x80)
    if masked:
        hlen += 4
        if blen < hlen:
            # log("decode_hybi_header() buffer too small for mask: %i", blen)
            return None

    payload_len = b2 & 0x7f
    if payload_len == 126:
        hlen += 2
        if blen < hlen:
            # log("decode_hybi_header() buffer too small for 126 payload: %i", blen)
            return None
        payload_len = struct.unpack('>H', buf[2:4])[0]
    elif payload_len == 127:
        hlen += 8
        if blen < hlen:
            # log("decode_hybi_header() buffer too small for 127 payload: %i", blen)
            return None
        payload_len = struct.unpack('>Q', buf[2:10])[0]

    # log("decode_hybi_header() decoded header '%s': hlen=%i,
    #    payload_len=%i, buffer len=%i", binascii.hexlify(buf[:hlen]), hlen, payload_len, blen)
    length = hlen + payload_len
    if blen < length:
        # log("decode_hybi_header() buffer too small for payload: %i (needed %i)", blen, length)
        return None

    if masked:
        payload = hybi_unmask(buf, hlen - 4, payload_len)
    else:
        payload = buf[hlen:length]
    # log("decode_hybi_header() payload_len=%i, hlen=%i,
    #    length=%i, fin=%s", payload_len, hlen, length, fin)
    return opcode, payload, length, fin
