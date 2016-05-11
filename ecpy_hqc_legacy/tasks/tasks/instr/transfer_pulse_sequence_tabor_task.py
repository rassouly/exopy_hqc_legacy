# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015-2016 by EcpyHqcLegacy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Interface to transfer a sequence on the Tabor AWG.

"""
from __future__ import (division, unicode_literals, print_function,
                        absolute_import)

from ecpy.tasks.api import InstrTaskInterface

# XXX unfinished

class TaborTransferInterface(InstrTaskInterface):
    """Interface for the Tabor, handling naming the transfered sequences and
    selecting it.

    """

    def perform(self):
        """Compile and transfer the sequence into the AWG.

        """
        task = self.task

        res, seqs = task.compile_sequence()
        if not res:
            mess = 'Failed to compile the pulse sequence: missing {}, errs {}'
            raise RuntimeError(mess.format(*seqs))

        for ch_id in task.driver.defined_channels:
            ch = task.driver.get_channel(ch_id)
            ch.output_state = 'OFF'
            if ch_id in seqs:
                task.driver.to_send(seqs[ch_id], ch_id)
                ch.output_state = 'ON'

    def validate_context(self, context):
        """Validate the context is appropriate for the driver.

        """
        return context.__class__.__name__ == 'TABORContext'
