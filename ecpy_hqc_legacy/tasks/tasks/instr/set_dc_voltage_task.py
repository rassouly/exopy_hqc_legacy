# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015-2016 by EcpyHqcLegacy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Task to set the parameters of microwave sources..

"""
from __future__ import (division, unicode_literals, print_function,
                        absolute_import)

import time

from atom.api import (Float, Value, Unicode, Int, set_default)

from ecpy.tasks.api import (InstrumentTask, InstrTaskInterface,
                            InterfaceableTaskMixin)


class SetDCVoltageTask(InterfaceableTaskMixin, InstrumentTask):
    """Set a DC voltage to the specified value.

    The user can choose to limit the rate by choosing an appropriate back step
    (larger step allowed), and a waiting time between each step.

    """
    #: Target value for the source (dynamically evaluated)
    target_value = Unicode().tag(pref=True, feval='Skip_empty')

    #: Largest allowed step when changing the output of the instr.
    back_step = Float().tag(pref=True)

    #: Largest allowed voltage
    safe_max = Float(0.0).tag(pref=True)

    #: Time to wait between changes of the output of the instr.
    delay = Float(0.01).tag(pref=True)

    parallel = set_default({'activated': True, 'pool': 'instr'})
    database_entries = set_default({'voltage': 0.01})

    def i_perform(self, value=None):
        """Default interface.

        """
        if self.driver.owner != self.task_name:
            self.driver.owner = self.task_name
            if hasattr(self.driver, 'function') and\
                    self.driver.function != 'VOLT':
                msg = ('Instrument assigned to task {} is not configured to '
                       'output a voltage')
                raise ValueError(msg.format(self.name))

        setter = lambda value: setattr(self.driver, 'voltage', value)
        current_value = getattr(self.driver, 'voltage')

        self.smooth_set(value, setter, current_value)

    def smooth_set(self, target_value, setter, current_value):
        """ Smoothly set the voltage.

        target_value : float
            Voltage to reach.

        setter : callable
            Function to set the voltage, should take as single argument the
            value.

        """
        if target_value is not None:
            value = target_value
        else:
            value = self.format_and_eval_string(self.target_value)

        if self.safe_max and self.safe_max < abs(value):
            msg = 'Requested voltage {} exceeds safe max : {}'
            raise ValueError(msg.format(value, self.safe_max))

        last_value = current_value

        if abs(last_value - value) < 1e-12:
            self.write_in_database('voltage', value)
            return

        elif self.back_step == 0:
            self.write_in_database('voltage', value)
            setter(value)
            return

        else:
            if (value - last_value)/self.back_step > 0:
                step = self.back_step
            else:
                step = -self.back_step

        if abs(value-last_value) > abs(step):
            while not self.root_task.should_stop.is_set():
                # Avoid the accumulation of rounding errors
                last_value = round(last_value + step, 9)
                setter(last_value)
                if abs(value-last_value) > abs(step):
                    time.sleep(self.delay)
                else:
                    break

        if not self.root_task.should_stop.is_set():
            setter(value)
            self.write_in_database('voltage', value)
            return

        self.write_in_database('voltage', last_value)


class MultiChannelVoltageSourceInterface(InstrTaskInterface):
    """Interface for multiple outputs sources.

    """
    #: Id of the channel to use.
    channel = Int(1).tag(pref=True)

    #: Reference to the driver for the channel.
    channel_driver = Value()

    def perform(self, value=None):
        """Set the specified voltage.

        """
        task = self.task
        if not self.channel_driver:
            self.channel_driver = task.driver.get_channel(self.channel)

        if self.channel_driver.owner != task.task_name:
            self.channel_driver.owner = task.task_name
            if hasattr(self.channel_driver, 'function') and\
                    self.channel_driver.function != 'VOLT':
                msg = ('Instrument output assigned to task {} is not '
                       'configured to output a voltage')
                raise ValueError(msg.format(self.name))

        setter = lambda value: setattr(self.channel_driver, 'voltage', value)
        current_value = getattr(self.channel_driver, 'voltage')

        task.smooth_set(value, setter, current_value)

    # XXX rework
    # could add a context manager to the instrument task to simplify that kind
    # of tests.
    def check(self, *args, **kwargs):
        if kwargs.get('test_instr'):
            task = self.task
            run_time = task.root_task.run_time
            traceback = {}
            config = None

            if task.selected_profile:
                if 'profiles' in run_time:
                    # Here use get to avoid errors if we were not granted the
                    # use of the profile. In that case config won't be used.
                    config = run_time['profiles'].get(task.selected_profile)
            else:
                return False, traceback

            if run_time and task.selected_driver in run_time['drivers']:
                driver_class = run_time['drivers'][task.selected_driver]
            else:
                return False, traceback

            if not config:
                return True, traceback

            try:
                instr = driver_class(config)
                if self.channel not in instr.defined_channels:
                    key = task.task_path + '/' + task.task_name + '_interface'
                    traceback[key] = 'Missing channel {}'.format(self.channel)
                instr.close_connection()
            except Exception:
                return False, traceback

            if traceback:
                return False, traceback
            else:
                return True, traceback

        else:
            return True, {}
