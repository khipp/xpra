#!/usr/bin/env python3
# This file is part of Xpra.
# Copyright (C) 2018 Antoine Martin <antoine@xpra.org>
# Xpra is released under the terms of the GNU GPL v2, or, at your option, any
# later version. See the file COPYING for details.

import unittest

from xpra.util.objects import AdHocStruct
from unit.server.mixins.servermixintest_util import ServerMixinTest
from unit.process_test_util import DisplayContext


class InputMixinTest(ServerMixinTest):

    def test_input(self):
        with DisplayContext():
            from xpra.server.mixins.keyboard import KeyboardServer
            from xpra.server.source.keyboard import KeyboardMixin
            opts = AdHocStruct()
            self._test_mixin_class(KeyboardServer, opts, {}, KeyboardMixin)


def main():
    unittest.main()


if __name__ == '__main__':
    main()
