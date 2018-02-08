# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015-2016 by EcpyHqcLegacy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Drivers for the Tektronik AWG5014 using VISA library.

"""
from __future__ import (division, unicode_literals, print_function,
                        absolute_import)

import re
import time
import logging
from textwrap import fill
from inspect import cleandoc
from threading import Lock
from contextlib import contextmanager

from visa import VisaTypeError, VisaIOError

from ..driver_tools import (BaseInstrument, InstrIOError, secure_communication,
                            instrument_property)
from ..visa_tools import VisaInstrument


class AWGChannel(BaseInstrument):

    def __init__(self, AWG, channel_num, caching_allowed=True,
                 caching_permissions={}):
        super(AWGChannel, self).__init__(None, caching_allowed,
                                         caching_permissions)
        self._AWG = AWG
        self._channel = channel_num

    def reopen_connection(self):
        """Reopens connection to insrtument

        """
        self._AWG.reopen_connection()

    @secure_communication()
    def select_sequence(self, name):
        """Select a sequence to run for the channel.

        """
        with self.secure():
            self._AWG.write('SOURCE{}:WAVEFORM "{}"'.format(self._channel,
                                                            name)
                            )

    @secure_communication()
    def clear_sequence(self):
        """Clear the sequence played by this channel.

        """
        with self.secure():
            self._AWG.write('SOURCE{}:WAVEFORM ""'.format(self._channel))

    @secure_communication()
    def set_sequence_pos(self, name, position):
        """Sets the sequence index position to waveform name.

        """
        self._AWG.clear_output_buffer()
        try:
            current_length = int(self._AWG.ask("SEQuence:LENGth?"))
        except Exception:
            log = logging.getLogger(__name__)
            msg = 'Could not read current_length, assuming 0'
            log.exception(msg)
            current_length = 0
        if position > current_length:
            self._AWG.write("SEQuence:LENGth {}".format(position))
        self._AWG.ask('*ESR?')
        msg = 'SEQuence:ELEMent{}:WAVeform{} "{}"'
        self._AWG.write(msg.format(position, self._channel, name))
        # ESR bit 5 signal a command error
        assert int(self._AWG.ask('*ESR?')) & 2**5 == 0, 'Command failed'

    @contextmanager
    def secure(self):
        """Lock acquire and release method

        """
        i = 0
        while not self._AWG.lock.acquire():
            time.sleep(0.1)
            i += 1
            if i > 50:
                raise InstrIOError
        try:
            yield
        finally:
            self._AWG.lock.release()

    @instrument_property
    @secure_communication()
    def output_state(self):
        """Output getter method

        """
        with self.secure():
            output = self._AWG.ask_for_values('OUTP{}:STAT?'
                                              .format(self._channel))[0]
            if output == 1:
                return 'ON'
            elif output == 0:
                return 'OFF'
            else:
                mes = cleandoc('AWG channel {} did not return its output'
                               .format(self._channel))
                raise InstrIOError(mes)

    @output_state.setter
    @secure_communication()
    def output_state(self, value):
        """Output setter method. 'ON', 'OFF'

        """
        with self.secure():
            on = re.compile('on', re.IGNORECASE)
            off = re.compile('off', re.IGNORECASE)
            if on.match(value) or value == 1:

                self._AWG.write('OUTP{}:STAT ON'.format(self._channel))
                if self._AWG.ask_for_values('OUTP{}:STAT?'
                                            .format(self._channel))[0] != 1:
                    raise InstrIOError(cleandoc('''Instrument did not set
                                                correctly the output'''))
            elif off.match(value) or value == 0:
                self._AWG.write('OUTP{}:STAT OFF'.format(self._channel))
                if self._AWG.ask_for_values('OUTP{}:STAT?'
                                            .format(self._channel))[0] != 0:
                    raise InstrIOError(cleandoc('''Instrument did not set
                                                correctly the output'''))
            else:
                mess = fill(cleandoc('''The invalid value {} was sent to
                            switch_on_off method''').format(value), 80)
                raise VisaTypeError(mess)

    @instrument_property
    @secure_communication()
    def marker1_high_voltage(self):
        """Marker1 high voltage getter method

        """
        with self.secure():
            m1_HV = self._AWG.ask_for_values("SOURce{}:MARK1:VOLTage:HIGH?"
                                             .format(self._channel))[0]
            if m1_HV is not None:
                return m1_HV
            else:
                raise InstrIOError

    @marker1_high_voltage.setter
    @secure_communication()
    def marker1_high_voltage(self, value):
        """Marker1 high voltage setter method

        """
        with self.secure():
            self._AWG.write("SOURce{}:MARK1:VOLTage:HIGH {}"
                            .format(self._channel, value))
            result = self._AWG.ask_for_values("SOURce{}:MARK1:VOLTage:HIGH?"
                                              .format(self._channel))[0]
            if abs(result - value) > 10**-12:
                raise InstrIOError(cleandoc('''Instrument did not set
                                            correctly the marker1 high
                                            voltage'''))

    @instrument_property
    @secure_communication()
    def marker2_high_voltage(self):
        """Marker2 high voltage getter method

        """
        with self.secure():
            m2_HV = self._AWG.ask_for_values("SOURce{}:MARK2:VOLTage:HIGH?"
                                             .format(self._channel))[0]
            if m2_HV is not None:
                return m2_HV
            else:
                raise InstrIOError

    @marker2_high_voltage.setter
    @secure_communication()
    def marker2_high_voltage(self, value):
        """Marker2 high voltage setter method

        """
        with self.secure():
            self._AWG.write("SOURce{}:MARK2:VOLTage:HIGH {}"
                            .format(self._channel, value))
            result = self._AWG.ask_for_values("SOURce{}:MARK2:VOLTage:HIGH?"
                                              .format(self._channel))[0]
            if abs(result - value) > 10**-12:
                raise InstrIOError(cleandoc('''Instrument did not set
                                            correctly the marker2 high
                                            voltage'''))

    @instrument_property
    @secure_communication()
    def marker1_low_voltage(self):
        """Marker1 low voltage getter method

        """
        with self.secure():
            m1_LV = self._AWG.ask_for_values("SOURce{}:MARK1:VOLTage:LOW?"
                                             .format(self._channel))[0]
            if m1_LV is not None:
                return m1_LV
            else:
                raise InstrIOError

    @marker1_low_voltage.setter
    @secure_communication()
    def marker1_low_voltage(self, value):
        """Marker1 low voltage setter method

        """
        with self.secure():
            self._AWG.write("SOURce{}:MARK1:VOLTage:LOW {}"
                            .format(self._channel, value))
            result = self._AWG.ask_for_values("SOURce{}:MARK1:VOLTage:LOW?"
                                              .format(self._channel))[0]
            if abs(result - value) > 10**-12:
                raise InstrIOError(cleandoc('''AWG channel {} did not set
                                            correctly the marker1 low
                                            voltage'''.format(self._channel)))

    @instrument_property
    @secure_communication()
    def marker2_low_voltage(self):
        """Marker2 low voltage getter method

        """
        with self.secure():
            m2_LV = self._AWG.ask_for_values("SOURce{}:MARK2:VOLTage:LOW?"
                                             .format(self._channel))[0]
            if m2_LV is not None:
                return m2_LV
            else:
                raise InstrIOError

    @marker2_low_voltage.setter
    @secure_communication()
    def marker2_low_voltage(self, value):
        """Marker2 low voltage setter method

        """
        with self.secure():
            self._AWG.write("SOURce{}:MARK2:VOLTage:LOW {}"
                            .format(self._channel, value))
            result = self._AWG.ask_for_values("SOURce{}:MARK2:VOLTage:LOW?"
                                              .format(self._channel))[0]
            if abs(result - value) > 10**-12:
                raise InstrIOError(cleandoc('''AWG channel {} did not set
                                            correctly the marker2 low
                                            voltage'''.format(self._channel)))

    @instrument_property
    @secure_communication()
    def marker1_delay(self):
        """Marker1 delay getter method. Unit = seconds

        """
        with self.secure():
            m1_delay = self._AWG.ask_for_values("SOURce{}:MARK1:DEL?"
                                                .format(self._channel))[0]
            if m1_delay is not None:
                return m1_delay
            else:
                raise InstrIOError

    @marker1_delay.setter
    @secure_communication()
    def marker1_delay(self, value):
        """Marker1 delay setter method. Unit = seconds

        """
        with self.secure():
            self._AWG.write("SOURce{}:MARK1:DEL {}"
                            .format(self._channel, value))
            result = self._AWG.ask_for_values("SOURce{}:MARK1:DEL?"
                                              .format(self._channel))[0]
            if abs(result - value) > 10**-12:
                raise InstrIOError(cleandoc('''AWG channel {} did not set
                                            correctly the marker1 delay
                                            '''.format(self._channel)))

    @instrument_property
    @secure_communication()
    def marker2_delay(self):
        """Marker2 delay getter method. Unit = seconds

        """
        with self.secure():
            m2_delay = self._AWG.ask_for_values("SOURce{}:MARK2:DEL?"
                                                .format(self._channel))[0]
            if m2_delay is not None:
                return m2_delay
            else:
                raise InstrIOError

    @marker2_delay.setter
    @secure_communication()
    def marker2_delay(self, value):
        """Marker2 delay setter method. Unit = seconds

        """
        with self.secure():
            self._AWG.write("SOURce{}:MARK2:DEL {}"
                            .format(self._channel, value))
            result = self._AWG.ask_for_values("SOURce{}:MARK2:DEL?"
                                              .format(self._channel))[0]
            if abs(result - value) > 10**-12:
                raise InstrIOError(cleandoc('''AWG channel {} did not set
                                            correctly the marker2 delay
                                            '''.format(self._channel)))

    @instrument_property
    @secure_communication()
    def delay(self):
        """Delay getter method. Unit = seconds

        """
        with self.secure():
            dela = self._AWG.ask_for_values("SOURce{}:DEL:ADJ?"
                                            .format(self._channel))[0]
            if dela is not None:
                return dela
            else:
                raise InstrIOError

    @delay.setter
    @secure_communication()
    def delay(self, value):
        """Delay setter method. Unity = seconds

        """
        with self.secure():
            self._AWG.write("SOURce{}:DEL:ADJ {}"
                            .format(self._channel, value))
            result = self._AWG.ask_for_values("SOURce{}:DEL:ADJ?"
                                              .format(self._channel))[0]
            if abs(result - value) > 10**-12:
                raise InstrIOError(cleandoc('''AWG channel {} did not set
                                            correctly the delay'''
                                            .format(self._channel)))

    @instrument_property
    @secure_communication()
    def offset(self):
        """Offset getter method

        """
        with self.secure():
            msg = "SOURce{}:VOLTage:LEVel:IMMediate:OFFSet?"
            offs = self._AWG.ask_for_values((msg.format(self._channel)))[0]
            if offs is not None:
                return offs
            else:
                raise InstrIOError

    @offset.setter
    @secure_communication()
    def offset(self, value):
        """Offset setter method

        """
        with self.secure():
            self._AWG.write("SOURce{}:VOLTage:LEVel:IMMediate:OFFSet {}"
                            .format(self._channel, value))
            msg = "SOURce{}:VOLTage:LEVel:IMMediate:OFFSet?"
            result = self._AWG.ask_for_values(msg.format(self._channel))[0]
            if abs(result - value) > 10**-12:
                raise InstrIOError(cleandoc('''AWG channel {} did not set
                                            correctly the offset'''
                                            .format(self._channel)))

    @instrument_property
    @secure_communication()
    def vpp(self):
        """Vpp getter method

        """
        with self.secure():
            vp = self._AWG.ask_for_values("SOURce{}:VOLTage?"
                                          .format(self._channel))[0]
            if vp is not None:
                return vp
            else:
                raise InstrIOError

    @vpp.setter
    @secure_communication()
    def vpp(self, value):
        """Vpp setter method

        """
        with self.secure():
            self._AWG.write("SOURce{}:VOLTage {}"
                            .format(self._channel, value))
            result = self._AWG.ask_for_values("SOURce{}:VOLTage?"
                                              .format(self._channel))[0]
            if abs(result - value) > 10**-12:
                raise InstrIOError(cleandoc('''AWG channel {} did not set
                                            correctly the vpp'''
                                            .format(self._channel)))

    @instrument_property
    @secure_communication()
    def phase(self):
        """Phase getter method. Unity = degrees

        """
        with self.secure():
            phi = self._AWG.ask_for_values("SOURce{}:PHAS:ADJ?"
                                           .format(self._channel))[0]
            if phi is not None:
                return phi
            else:
                raise InstrIOError

    @phase.setter
    @secure_communication()
    def phase(self, value):
        """Phase setter method. Unity = degrees

        """
        with self.secure():
            self._AWG.write("SOURce{}:PHAS:ADJ {}"
                            .format(self._channel, value))
            result = self._AWG.ask_for_values("SOURce{}:PHAS:ADJ?"
                                              .format(self._channel))[0]
            if abs(result - value) > 10**-12:
                raise InstrIOError(cleandoc('''AWG channel {} did not set
                                            correctly the phase'''
                                            .format(self._channel)))


class AWG(VisaInstrument):
    """
    """
    caching_permissions = {'defined_channels': True}

    def __init__(self, connection_info, caching_allowed=True,
                 caching_permissions={}, auto_open=True):
        super(AWG, self).__init__(connection_info, caching_allowed,
                                  caching_permissions, auto_open)
        self.channels = {}
        self.lock = Lock()

    def reopen_connection(self):
        """Clear buffer on connection reseting.

        """
        super(AWG, self).reopen_connection()
        self.write('*CLS')  # As this does not seem to work poll the output
        while True:
            try:
                self.read()
            except VisaIOError:
                break

    def clear_output_buffer(self):
        """Cleans output buffer. This replaces '*CLS' which does not work
        properly

        """
        _timeout = self.timeout
        self.timeout = 100
        while True:
            try:
                self.read()
            except VisaIOError:
                self.timeout = _timeout
                break

    def get_channel(self, num):
        """
        """
        if num not in self.defined_channels:
            return None

        if num in self.channels:
            return self.channels[num]
        else:
            channel = AWGChannel(self, num)
            self.channels[num] = channel
            return channel

    @secure_communication()
    def to_send(self, name, waveform):
        """Command to send to the instrument. waveform = string of a bytearray

        """
        numbyte = len(waveform)
        looplength = numbyte//2
        self.write("WLIST:WAVEFORM:DELETE '{}'".format(name))
        self.write("WLIST:WAVEFORM:NEW '{}' , {}, INTeger" .format(name,
                                                                   looplength))

        header = "WLIS:WAV:DATA '{}',0,{},".format(name, looplength)
        self._driver.write_binary_values(header, waveform, datatype='B')
        self.write('*WAI')

    @secure_communication()
    def clear_sequence(self):
        """Command to delete the sequence

        """
        self.write("SEQuence:LENGth 0")

    @secure_communication()
    def set_goto_pos(self, position, goto):
        """Sets the goto value at position to goto

        """
        self.write('SEQuence:ELEMent' + str(position) + ':GOTO:STATe 1')
        self.write('SEQuence:ELEMent' + str(position) + ':GOTO:INDex ' +
                   str(goto))

    @secure_communication()
    def set_jump_pos(self, position, jump):
        """Sets the jump value at position to jump

        """
        self.write('SEQuence:ELEMent' + str(position) + ':JTARget:TYPE INDex')
        self.write('SEQuence:ELEMent' + str(position) + ':JTARget:INDex ' +
                   str(jump))

    @secure_communication()
    def send_event(self):
        """Send an event

        """
        self.write('EVENt:IMM')

    @secure_communication()
    def ask_sequencer_pos(self):
        """Ask the current position index of the sequencer

        """
        pos = self.ask('AWGC:SEQ:POS?')
        return(pos)

    @secure_communication()
    def set_repeat(self, position, repeat):
        """Sets the loop count for the specified subsequence element.
        The loop count is an integer.

        """
        self.write('SEQUENCE:ELEMENT' + str(position) + ':LOOP:COUNT ' +
                   str(repeat))

    @secure_communication()
    def set_trigger_pos(self, position):
        """Sets the waveform at position to wait for trigger

        """
        self.write('SEQuence:ELEMent' + str(position) + ':TWAIT 1')

    @instrument_property
    @secure_communication()
    def internal_trigger_period(self):
        """Getter for internal trigger period

        """
        return self.ask("TRIGGER:SEQUENCE:TIMER?")

    @internal_trigger_period.setter
    @secure_communication()
    def internal_trigger_period(self, value):
        """Setter for internal trigger period in nanoseconds

        """
        self.write("TRIGGER:SEQUENCE:TIMER " + str(value) + "NS")

    @instrument_property
    @secure_communication()
    def internal_trigger(self):
        """Getter for trigger internal or external

        """
        ore = self.ask("TRIGGER:SEQUENCE:SOURCE?")
        if ore == 'INT':
            return 'True'
        elif ore == 'EXT':
            return 'False'
        else:
            raise InstrIOError

    @internal_trigger.setter
    @secure_communication()
    def internal_trigger(self, value):
        """Setter for internal trigger enable

        """
        if value in ('INT', 1, 'True'):
            self.write('TRIGGER:SEQUENCE:SOURCE INT')
        elif value in ('EXT', 0, 'False'):
            self.write('TRIGGER:SEQUENCE:SOURCE EXT')
        else:
            mess = fill(cleandoc('''The invalid value {} was sent to
                                 internal_trigger method''').format(value), 80)
            raise VisaTypeError(mess)

    @instrument_property
    @secure_communication()
    def defined_channels(self):
        """
        """
        defined_channels = [1, 2, 3, 4]
        return defined_channels

    @instrument_property
    @secure_communication()
    def oscillator_reference_external(self):
        """Oscillator reference external getter method

        """
        ore = self.ask("SOUR:ROSC:SOUR?")
        if ore == 'EXT':
            return 'True'
        elif ore == 'INT':
            return 'False'
        else:
            raise InstrIOError

    @oscillator_reference_external.setter
    @secure_communication()
    def oscillator_reference_external(self, value):
        """Oscillator reference external setter method

        """
        if value in ('EXT', 1, 'True'):
            self.write('SOUR:ROSC:SOUR EXT')
            if self.ask('SOUR:ROSC:SOUR?') != 'EXT':
                raise InstrIOError(cleandoc('''Instrument did not set
                                            correctly the oscillator
                                            reference'''))
        elif value in ('INT', 0, 'False'):
            self.write('SOUR:ROSC:SOUR INT')
            if self.ask('SOUR:ROSC:SOUR?') != 'INT':
                raise InstrIOError(cleandoc('''Instrument did not set
                                            correctly the oscillator
                                            reference'''))
        else:
            mess = fill(cleandoc('''The invalid value {} was sent to
                                 oscillator_reference_external
                                 method''').format(value), 80)
            raise VisaTypeError(mess)

    @instrument_property
    @secure_communication()
    def clock_source(self):
        """Clock source getter method

        """
        cle = self.ask("AWGControl:CLOCk:SOURce?")
        if cle is not None:
            return cle
        else:
            raise InstrIOError

    @clock_source.setter
    @secure_communication()
    def clock_source(self, value):
        """Clock source setter method

        """
        if value in ('EXT', 1, 'True'):
            self.write('AWGControl:CLOCk:SOURce EXT')
            if self.ask('AWGControl:CLOCk:SOURce?') != 'EXT':
                raise InstrIOError(cleandoc('''Instrument did not set
                                            correctly the clock source'''))
        elif value in ('INT', 0, 'False'):
            self.write('AWGControl:CLOCk:SOURce INT')
            if self.ask('AWGControl:CLOCk:SOURce?') != 'INT':
                raise InstrIOError(cleandoc('''Instrument did not set
                                            correctly the clock source'''))
        else:
            mess = fill(cleandoc('''The invalid value {} was sent to
                                 clock_source_external
                                 method''').format(value), 80)
            raise VisaTypeError(mess)

    @instrument_property
    @secure_communication()
    def sampling_frequency(self):
        """Sampling frequency getter method

        """
        sampl_freq = self.ask_for_values("SOUR:FREQ:CW?")[0]
        if sampl_freq is not None:
            return sampl_freq
        else:
            raise InstrIOError

    @sampling_frequency.setter
    @secure_communication()
    def sampling_frequency(self, value):
        """Sampling frequency setter method

        """
        self.write("SOUR:FREQ:CW {}".format(value))
        result = self.ask_for_values("SOUR:FREQ:CW?")[0]
        if abs(result - value) > 10**-12:
            raise InstrIOError(cleandoc('''Instrument did not set correctly
                                        the sampling frequency'''))

#    @instrument_property
#    @secure_communication()
#    def running(self):
#        """Run state getter method
#
#        """
#        self.clear_output_buffer()
#
#        run = self.ask_for_values("AWGC:RST?")[0]
#        if run == 0:
#            return '0 : Instrument has stopped'
#        elif run == 1:
#            return '1 : Instrument is waiting for trigger'
#        elif run == 2:
#            return '2 : Intrument is running'
#        else:
#            raise InstrIOError
#
#    @running.setter
#    @secure_communication()
    def run_awg(self, value, delay=0.0):
        """Run state setter method

        """
        self.clear_output_buffer()
        if value in ('RUN', 1, 'True'):
            self.write('AWGC:RUN:IMM')
            self.write('AWGC:RST?')
            time.sleep(delay)
            values = self.read_values(format=2)
            if values[0] not in (1, 2):
                raise InstrIOError(cleandoc('''Instrument did not set
                                            correctly the run state'''))
        elif value in ('STOP', 0, 'False'):
            self.write('AWGC:STOP:IMM')
            if self.ask_for_values('AWGC:RST?')[0] != 0:
                raise InstrIOError(cleandoc('''Instrument did not set
                                            correctly the run state'''))
        else:
            mess = fill(cleandoc('''The invalid value {} was sent to
                                 running method''').format(value), 80)
            raise VisaTypeError(mess)

    @instrument_property
    @secure_communication()
    def run_mode(self):
        """Run mode getter method

        """
        self.clear_output_buffer()
        run_mode = self.ask("AWGControl:RMODe?")
        if run_mode is not None:
            return run_mode
        else:
            raise InstrIOError

    @run_mode.setter
    @secure_communication()
    def run_mode(self, value):
        """Run mode setter method

        """
        if value in ('CONT', 'CONTINUOUS', 'continuous'):
            self.write('AWGControl:RMODe CONT')
            if self.run_mode[:-1] != 'CONT':
                raise InstrIOError(cleandoc('''Instrument did not set
                                            correctly the run mode'''))
        elif value in ('TRIG', 'TRIGGERED', 'triggered'):
            self.write('AWGControl:RMODe TRIG')
            if self.run_mode[:-1] != 'TRIG':
                raise InstrIOError(cleandoc('''Instrument did not set
                                            correctly the run mode'''))
        elif value in ('GAT', 'GATED', 'gated'):
            self.write('AWGControl:RMODe GAT')
            if self.run_mode[:-1] != 'GAT':
                raise InstrIOError(cleandoc('''Instrument did not set
                                            correctly the run mode'''))
        elif value in ('SEQ', 'SEQUENCE', 'sequence'):
            self.write('AWGControl:RMODe SEQ')
            if self.run_mode[:-1] != 'SEQ':
                raise InstrIOError(cleandoc('''Instrument did not set
                                            correctly the run mode.'''))
        else:
            mess = fill(cleandoc('''The invalid value {} was sent to
                                 run mode method''').format(value), 80)
            raise VisaTypeError(mess)

    def delete_all_waveforms(self):
        """Deletes all user-defined waveforms from the currently loaded setup

        """
        nb_waveforms = int(self.ask("WLIST:SIZE?")) - 25 #nb of user defined wf
        wait_time = 1+int(nb_waveforms/120)
        self.write('WLIST:WAVEFORM:DELETE ALL')

        print('Waiting {}s for {} waveforms to be deleted'.format(wait_time,
                                                                 nb_waveforms))
        time.sleep(wait_time)


    def clear_all_sequences(self):
        """Clear the all sequences played by the AWG.

        """
        self.write('SEQuence:LENGth 0')
