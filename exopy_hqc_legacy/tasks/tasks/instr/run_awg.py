# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015-2020 by ExopyHqcLegacy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Tasks to set the parameters of arbitrary waveform generators.

"""
import logging
import time

from atom.api import (Float, Unicode, set_default)

from exopy.tasks.api import InstrumentTask


class RunAWGTask(InstrumentTask):
    """ Task to set AWG run mode

    """
    #: Switch to choose the AWG run mode
    switch = Unicode('Off').tag(pref=True)

    #: Delay required to load the sequence
    delay = Float(0).tag(pref=True)

    database_entries = set_default({'output': 0})

    def perform(self):
        """Default interface behavior.

        """
        if self.switch.lower() == 'on' or self.switch == '1':
            self.driver.send_event()
            # The delay is required when loading large sequences
            self.driver.set_running(True, delay=self.delay)
            self.write_in_database('output', 1)
        elif self.switch.lower() == 'event':
            time.sleep(self.delay)
            self.driver.send_event()
        elif self.switch.lower() == 'rearm':
            time.sleep(self.delay)
            success = False
            while not success:
                self.driver.send_event()
                pos = int(self.driver.ask_sequencer_pos())
                if pos == 1:
                    success = True
            time.sleep(self.delay)
        elif self.switch.lower() == 'off' or self.switch == '0':
            time.sleep(self.delay)
            self.driver.set_running(False)
            self.write_in_database('output', 0)
        else:
            logger = logging.getLogger(__name__)
            msg = "Unable to recognize {} running mode"
            logger.warning(msg.format(self.switch))
