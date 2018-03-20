# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015-2018 by ExopyHqcLegacy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Tasks to set the parameters of arbitrary waveform generators.

"""
import logging
import numbers
import numpy as np

from atom.api import (Enum, Unicode, Value)

from exopy.tasks.api import (InstrumentTask, validators)
import exopy_hqc_legacy.instruments.drivers.dll.SA124B as sa

SA_SWEEPING = 0x0
SA_REAL_TIME = 0x1


class TuneIQMixerTask(InstrumentTask):
    """ Task to tune an IQ mixer in SSB
        Implicit use of a SignalHound spectrum analyzer
        Tunes channels I and Q DC offset, relative delay and voltage
        to suppress LO leakage and unwanted sideband
        TODO: handle task with two instruments: AWG AND Spectrum analyzer
        TODO: implement realtime sweep for better SNR

    """

    # Get user inputs
    channelI = Enum('Ch1', 'Ch2', 'Ch3', 'Ch4').tag(pref=True)
    channelQ = Enum('Ch1', 'Ch2', 'Ch3', 'Ch4').tag(pref=True)

    # LO frequency
    freq = Unicode('0.0').tag(pref=True,
                              feval=validators.SkipLoop(types=numbers.Real))
    # IF frequency
    det = Unicode('0.0').tag(pref=True,
                             feval=validators.SkipLoop(types=numbers.Real))
    # Desired sideband, e.g. if Lower, suppress freq and freq+det
    SB = Enum('Lower', 'Upper').tag(pref=True)

    my_sa = Value()  # signal analyzer
    chI = Value()
    chQ = Value()
    freq_Hz = Value()
    det_Hz = Value()
    SB_sgn = Value()

    def check(self, *args, **kwargs):
        ''' Default checks and check different AWG channels
        '''
        test, traceback = super(TuneIQMixerTask, self).check(*args, **kwargs)
        if not test:
            return test, traceback

        if self.channelI == self.channelQ:
            test = False
            msg = 'I and Q channels need to be different !'
            traceback[self.get_error_path()] = msg
        return test, traceback

    def perform(self):
        """Default interface behavior.

        """
        # open signal analyzer
        serial = sa.saGetSerialNumberList()[0]
        assert serial != 0
        connection_infos = {u'serial': serial}
        self.my_sa = sa.SA124B(connection_infos, mode=SA_SWEEPING)

        # AWG channels
        awg = self.driver
        awg.run_mode = 'CONT'
        awg.run_awg(1, delay=0.5)
        self.chI = awg.get_channel(int(self.channelI[-1]))
        self.chQ = awg.get_channel(int(self.channelQ[-1]))

        # set sa sweep params
        self.my_sa.do_set_rbw_vbw(1e3, 1e3)
        self.my_sa.do_set_span(250e3)

        # convert user inputs into adequate units
        self.freq_Hz = self.format_and_eval_string(self.freq)*1e9
        self.det_Hz = self.format_and_eval_string(self.det)*1e9
        self.SB_sgn = 1 if self.SB == 'Lower' else -1

        # Initialize AWG params

        # we always operate the AWG at 4V, if not 4,
        # then assume the AWG has just been turned on
        if self.get_chI_vpp != 4:
            self.chI_vpp(4.0)
            self.chQ_vpp(4.0)

        # perform optimization twice
        self.tune_ssb('lo')
        self.tune_ssb('sb')
        pos_lo, cost = self.tune_ssb('lo')
        pos_sb, cost = self.tune_ssb('sb')

        # get power for optimal parameters at sig, leakage and sideband
        sig = self.my_sa.read_single_freq(self.freq_Hz-self.SB_sgn*self.det_Hz,
                                          n_av=10)
        lo = self.my_sa.read_single_freq(self.freq_Hz, n_av=10)
        sb = self.my_sa.read_single_freq(self.freq_Hz+self.SB_sgn*self.det_Hz,
                                         n_av=10)

        # close signal analyzer
        self.my_sa._close()

        # log values
        log = logging.getLogger(__name__)
        msg1 = 'Tuned IQ mixer at LO = %s GHz, IF = %s MHz, \
                Signal: %s dBm, LO: %s dBm, SB: %s dBm' % \
               (1e-9*self.freq_Hz, 1e-6*self.det_Hz, sig, lo, sb)
        log.info(msg1)
        msg2 = 'chI offset: %s V, chQ offset: %s V, chQvpp: %s V, \
                chQdelay: %s ns' % \
               (pos_lo[0], pos_lo[1], pos_sb[0], 1e9*pos_sb[1])
        log.info(msg2)

    # optimization procedure
    def tune_ssb(self, mode):
        # suppress lo leakage params
        if mode == 'lo':
            param1 = self.chI_offset
            param2 = self.chQ_offset
            f = self.freq_Hz
            pref = np.array([1, 1])
            pos0 = np.array([self.get_chI_offset(), self.get_chQ_offset()])

        # suppress other sideband params
        elif mode == 'sb':
            param1 = self.chQ_vpp
            param2 = self.chQ_delay
            f = self.freq_Hz + self.SB_sgn*self.det_Hz
            pref = np.array([1, 1e-9])
            pos0 = np.array([self.get_chQ_vpp(), self.get_chQ_delay()])
        else:
            msg = '''param has wrong value, should be lo or sb,
                     received %s''' % mode
            raise ValueError(msg)

        # 4 directions in parameter search space
        sens = [np.array([1, 0]), np.array([0, 1]),
                np.array([-1, 0]), np.array([0, -1])]

        # initial cost (cost = power of sa at f)
        cost0 = self.cost(param1, param2, pos0[0], pos0[1], f)

        # initialize coutners and step size
        dec = 0.1  # decimal: step size
        s = 0  # direction
        c = 0  # counter: number of explored directions at given point
        eval_count = 0  # counter: number of cost evaluations

        poslist = [pos0]
        # stop search when dec < AWG resolution
        while dec >= 0.001:
            # break when max eval count has reach or
            # all 4 directions have been explored
            while c < 4 and eval_count < 1000:
                # probe cost at new pos: pos1
                pos1 = pos0 + dec*sens[s]*pref
                cost1 = self.cost(param1, param2, pos1[0], pos1[1], f)
                eval_count += 1
                # if lower cost, update pos
                if cost1 < cost0:
                    cost0 = cost1
                    pos0 = pos1
                    c = 0
                    poslist.append(pos0)
                else:
                    c += 1
                    s = np.mod(s+1, 4)
            c = 0
            # decrease dec if all explored directions give higher cost
            dec /= 10
        return pos0, cost0

    # optimization cost function: get power in dBm at f from signal_analyzer
    def cost(self, param1, param2, val1, val2, f):
        param1(val1)
        param2(val2)
        return self.my_sa.read_single_freq(f, n_av=10)

    # define AWG getter and setter functions to pass into cost function
    def chI_offset(self, value):
        self.chI.offset = value

    def chQ_offset(self, value):
        self.chQ.offset = value

    def get_chI_offset(self):
        return self.chI.offset

    def get_chQ_offset(self):
        return self.chQ.offset

    def chI_vpp(self, value):
        self.chI.vpp = value

    def chQ_vpp(self, value):
        self.chQ.vpp = value

    def get_chI_vpp(self):
        return self.chI.vpp

    def get_chQ_vpp(self):
        return self.chQ.vpp

    def chQ_delay(self, value):
        self.chQ.delay = value

    def get_chQ_delay(self):
        return self.chQ.delay
