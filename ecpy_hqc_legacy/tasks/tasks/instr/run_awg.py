# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015-2016 by EcpyHqcLegacy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Tasks to set the parameters of arbitrary waveform generators.

"""
from __future__ import (division, unicode_literals, print_function,
                        absolute_import)

from atom.api import (Unicode, Bool, set_default, Enum)

from ecpy.tasks.api import (InstrumentTask, InterfaceableTaskMixin,
                            validators)
import logging


class RunAWGTask(InstrumentTask):
    """ Task to set AWG run mode

    """
    # switch to choose the AWG run mode: on or off
    switch = Unicode('Off').tag(pref=True, feval=validators.SkipLoop())
    database_entries = set_default({'output': 0})

    def perform(self, switch=None):
        """Default interface behavior.

        """
        if switch is None:
            switch = self.format_and_eval_string(self.switch)

        if switch == 'On' or switch == 1:
            self.driver.running = 1
            self.write_in_database('output', 1)
        else:
            self.driver.running = 0
            self.write_in_database('output', 0)
        log = logging.getLogger(__name__)
        msg = 'AWG running state OK'
        log.info(msg)
