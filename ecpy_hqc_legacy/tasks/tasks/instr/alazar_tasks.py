# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015-2016 by EcpyHqcLegacy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Task to apply a magnetic field.

"""
from __future__ import (division, unicode_literals, print_function,
                        absolute_import)

from inspect import cleandoc

import numpy as np
from atom.api import (Unicode, Bool, set_default)

from ecpy.tasks.api import InstrumentTask

# XXX unfinished

class DemodAlazarTask(InstrumentTask):
    """ Get the raw or averaged quadratures of the signal.
        Can also get raw or averaged traces of the signal.
    """
    freq = Unicode('40').tag(pref=True)

    freqB = Unicode('40').tag(pref=True)

    timeaftertrig = Unicode('0').tag(pref=True)

    timeaftertrigB = Unicode('0').tag(pref=True)

    tracetimeaftertrig = Unicode('0').tag(pref=True)

    tracetimeaftertrigB = Unicode('0').tag(pref=True)

    duration = Unicode('1000').tag(pref=True)

    durationB = Unicode('0').tag(pref=True)

    traceduration = Unicode('0').tag(pref=True)

    tracedurationB = Unicode('0').tag(pref=True)

    tracesbuffer = Unicode('20').tag(pref=True)

    samplingtime = Unicode('1000').tag(pref=True)

    samplingtimeB = Unicode('0').tag(pref=True)

    tracesnumber = Unicode('1000').tag(pref=True)

    average = Bool(True).tag(pref=True)

    IQtracemode = Bool(False).tag(pref=True)
    driver_list = ['Alazar935x']

    task_database_entries = set_default({'Demod': {}, 'Trace': {}})

    def check(self, *args, **kwargs):
        """
        """
        test, traceback = super(DemodAlazarTask, self).check(*args,
                                                             **kwargs)

        err_path = self.get_error_path()
        if (self.format_and_eval_string(self.tracesnumber) %
                self.format_and_eval_string(self.tracesbuffer) != 0 ):
            test = False
            traceback[err_path + '-get_demod'] = \
                cleandoc('''The number of traces must be an integer multiple of the number of traces per buffer.''')

        if not (self.format_and_eval_string(self.tracesnumber) >= 1000):
            test = False
            traceback[err_path + '-get_demod'] = \
                cleandoc('''At least 1000 traces must be recorded. Please take real measurements and not noisy craps.''')

        time = [self.format_and_eval_string(elem) for elem in self.timeaftertrig.split(',')]
        duration = [self.format_and_eval_string(elem) for elem in self.duration.split(',')]
        timeB = [self.format_and_eval_string(elem) for elem in self.timeaftertrigB.split(',')]
        durationB = [self.format_and_eval_string(elem) for elem in self.durationB.split(',')]
        tracetime = [self.format_and_eval_string(elem) for elem in self.tracetimeaftertrig.split(',')]
        traceduration = [self.format_and_eval_string(elem) for elem in self.traceduration.split(',')]
        tracetimeB = [self.format_and_eval_string(elem) for elem in self.tracetimeaftertrigB.split(',')]
        tracedurationB = [self.format_and_eval_string(elem) for elem in self.tracedurationB.split(',')]
        tablesamplingtime = [self.format_and_eval_string(elem) for elem in self.samplingtime.split(',')]
        tablesamplingtimeB = [self.format_and_eval_string(elem) for elem in self.samplingtimeB.split(',')]

        if not (tablesamplingtime[0] >= 0 and tablesamplingtimeB[0] >= 0):
             test = False
             traceback[err_path + '-get_demod'] = \
                    cleandoc('''The sampling time should be positive.''')

        for t, d in ((time,duration), (timeB,durationB), (tracetime,traceduration), (tracetimeB,tracedurationB)):
            if len(t) != len(d):
                test = False
                traceback[err_path + '-get_demod'] = \
                    cleandoc('''An equal number of "Start time after trig" and "Duration" should be given.''')
            else :
                for tt, dd in zip(t, d):
                    if not (tt >= 0 and dd >= 0) :
                           test = False
                           traceback[err_path + '-get_demod'] = \
                               cleandoc('''Both "Start time after trig" and "Duration" must be >= 0.''')

        if ((0 in duration) and (0 in durationB) and (0 in traceduration) and (0 in tracedurationB)):
            test = False
            traceback[err_path + '-get_demod'] = \
                           cleandoc('''All measurements are disabled.''')

        if self.IQtracemode:
            if (len(time) != 1) or (len(timeB) != 1):
                test = False
                traceback[err_path + '-get_demod'] = \
                cleandoc('''In IQtrace mode, a single time step and initial time is required, not a list of them''')
            elif tablesamplingtime[0] / 1000.0 * float(self.format_and_eval_string(self.freq)) % 1.0 != 0.0:
                test = False
                traceback[err_path + '-get_demod'] = \
                cleandoc('''Please modify the IQtrace time step so that
                            it corresponds to an integer number of periods
                            in the demodulation.''')
            elif tablesamplingtimeB[0] / 1000.0 * float(self.format_and_eval_string(self.freqB)) % 1.0 != 0.0:
                test = False
                traceback[err_path + '-get_demod'] = \
                cleandoc('''Please modify the IQtrace time step so that
                            it corresponds to an integer number of periods
                            in the demodulation.''')
        return test, traceback

    def perform(self):
        """
        """
        if self.driver.owner != self.name:
            self.driver.owner = self.name

        self.driver.configure_board()

        recordsPerCapture = self.format_and_eval_string(self.tracesnumber)
        recordsPerBuffer = int(self.format_and_eval_string(self.tracesbuffer))

        if self.IQtracemode:
            if (self.format_and_eval_string(self.duration) == 0 or self.format_and_eval_string(self.samplingtime) == 0):
                timeA = []
            else:
                timeA = \
                    np.arange(self.format_and_eval_string(self.timeaftertrig)*10.0**-9,
                              self.format_and_eval_string(self.duration)*10.0**-9,
                              self.format_and_eval_string(self.samplingtime)*10.0**-9).tolist()
            if (self.format_and_eval_string(self.durationB) == 0 or self.format_and_eval_string(self.samplingtimeB) == 0):
                timeB = []
            else:
                timeB = \
                    np.arange(self.format_and_eval_string(self.timeaftertrigB)*10.0**-9,
                              self.format_and_eval_string(self.durationB)*10.0**-9,
                              self.format_and_eval_string(self.samplingtimeB)*10.0**-9).tolist()
            durationA = [self.format_and_eval_string(self.samplingtime)*10.0**-9] * len(timeA)
            durationB = [self.format_and_eval_string(self.samplingtimeB)*10.0**-9] * len(timeB)
        else:
            timeA = [self.format_and_eval_string(elem)*10.0**-9 for elem in self.timeaftertrig.split(',')]
            durationA = [self.format_and_eval_string(elem)*10.0**-9 for elem in self.duration.split(',')]
            timeB = [self.format_and_eval_string(elem)*10.0**-9 for elem in self.timeaftertrigB.split(',')]
            durationB = [self.format_and_eval_string(elem)*10.0**-9 for elem in self.durationB.split(',')]

        tracetimeA = [self.format_and_eval_string(elem)*10.0**-9 for elem in self.tracetimeaftertrig.split(',')]
        tracedurationA = [self.format_and_eval_string(elem)*10.0**-9 for elem in self.traceduration.split(',')]
        tracetimeB = [self.format_and_eval_string(elem)*10.0**-9 for elem in self.tracetimeaftertrigB.split(',')]
        tracedurationB = [self.format_and_eval_string(elem)*10.0**-9 for elem in self.tracedurationB.split(',')]

        NdemodA = len(durationA)
        if 0 in durationA:
            NdemodA = 0
            timeA = []
            durationA = []
        NdemodB = len(durationB)
        if 0 in durationB:
            NdemodB = 0
            timeB = []
            durationB = []
        NtraceA = len(tracedurationA)
        if 0 in tracedurationA:
            NtraceA = 0
            tracetimeA = []
            tracedurationA = []
        NtraceB = len(tracedurationB)
        if 0 in tracedurationB:
            NtraceB = 0
            tracetimeB = []
            tracedurationB = []

        startaftertrig = timeA + timeB + tracetimeA + tracetimeB
        duration = durationA + durationB + tracedurationA + tracedurationB

        freqA = self.format_and_eval_string(self.freq)*10.0**6
        freqB = self.format_and_eval_string(self.freqB)*10.0**6
        freq = [freqA] * NdemodA + [freqB] * NdemodB

        answerDemod, answerTrace = self.driver.get_demod(startaftertrig, duration,
                                       recordsPerCapture, recordsPerBuffer,
                                       freq, self.average,
                                       NdemodA, NdemodB, NtraceA, NtraceB)

        self.write_in_database('Demod', answerDemod)
        self.write_in_database('Trace', answerTrace)


class TracesAlazarTask(InstrumentTask):
    """ Get the raw or averaged traces of the signal.

    """

    timeaftertrig = Unicode().tag(pref=True)

    tracesnumber = Unicode().tag(pref=True)

    tracesbuffer = Unicode().tag(pref=True)

    average = Bool(True).tag(pref=True)

    task_database_entries = set_default({'traceA': np.zeros((1, 1)),
                                         'traceB': np.zeros((1, 1))})

    def check(self, *args, **kwargs):
        """
        """
        test, traceback = super(TracesAlazarTask, self).check(*args,
                                                              **kwargs)

        err_path = self.get_error_path()

        if (self.format_and_eval_string(self.tracesnumber) %
                self.format_and_eval_string(self.tracesbuffer)) != 0:
            test = False
            traceback[err_path + '-get_traces'] =\
                cleandoc('''The number of buffers used must be an integer.''')

        return test, traceback

    def perform(self):
        """
        """
        if self.driver.owner != self.name:
            self.driver.owner = self.name

        self.driver.configure_board()

        recordsPerCapture = int(max(1000,
                            self.format_and_eval_string(self.tracesnumber)))

        recordsPerBuffer = int(self.format_and_eval_string(self.tracesbuffer))

        answer = self.driver.get_traces(
            self.format_and_eval_string(self.timeaftertrig)*10**-6,
            recordsPerCapture, recordsPerBuffer, self.average
            )

        traceA, traceB = answer
        self.write_in_database('traceA', traceA)
        self.write_in_database('traceB', traceB)

KNOWN_PY_TASKS = [DemodAlazarTask, TracesAlazarTask]
