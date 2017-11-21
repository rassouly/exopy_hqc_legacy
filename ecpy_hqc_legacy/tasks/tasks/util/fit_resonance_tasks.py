# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015-2017 by EcpyHqcLegacy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Tasks to operate on numpy.arrays.

"""
from __future__ import (division, unicode_literals, print_function,
                        absolute_import)

import numpy as np
from future.utils import raise_from
from atom.api import (Enum, Unicode, set_default)
from scipy.interpolate import splrep, sproot, splev
from scipy.optimize import curve_fit, leastsq

from ecpy.tasks.api import SimpleTask, validators

ARR_VAL = validators.Feval(types=np.ndarray)


class FitResonanceTask(SimpleTask):
    """ Store the pair(s) of index/value for the resonance frequency.

    Wait for any parallel operation before execution.

    """
    #: Name of the target in the database.
    target_array = Unicode().tag(pref=True, feval=ARR_VAL)

    #: Name of the column into which the extrema should be looked for.
    column_name_data_maglin = Unicode().tag(pref=True)
    column_name_data_phase = Unicode().tag(pref=True)
    column_name_freq = Unicode().tag(pref=True)

    #: Flag indicating the measurement setup. This changes the fit function
    mode = Enum('Reflection', 'Transmission').tag(pref=True)

    database_entries = set_default({'res_value': 1.0})

    wait = set_default({'activated': True})  # Wait on all pools by default.

    def perform(self):
        """ Find resonance frequency of database array and store index/value
            pairs.

        """
        array = self.format_and_eval_string(self.target_array)
        freq = array[self.column_name_freq]
        data_maglin = array[self.column_name_data_maglin]
        data_phase = array[self.column_name_data_phase]
        data_c = data_maglin*np.exp(1j*np.pi/180*data_phase)
        if self.mode == 'Reflection':
            val = fit_complex_a_out(freq, data_c)
            self.write_in_database('res_value', val)
        if self.mode == 'Transmission':
            val = fit_lorentzian(freq, data_maglin)
            self.write_in_database('res_value', val)

    def check(self, *args, **kwargs):
        """ Check the target array can be found and has the right column.

        """
        test, traceback = super(FitResonanceTask, self).check(*args, **kwargs)

#        if not test:
#            return test, traceback
#
#        array = self.format_and_eval_string(self.target_array)
#        err_path = self.get_error_path()
#
#        if self.column_name:
#            if array.dtype.names:
#                names = array.dtype.names
#                if self.column_name not in names:
#                    msg = 'No column named {} in array. (column are : {})'
#                    traceback[err_path] = msg.format(self.column_name, names)
#                    return False, traceback
#            else:
#                traceback[err_path] = 'Array has no named columns'
#                return False, traceback
#
#        else:
#            if array.dtype.names:
#                msg = 'The target array has names columns : {}. Choose one'
#                traceback[err_path] = msg.format(array.dtype.names)
#                return False, traceback
#            elif len(array.shape) > 1:
#                msg = 'Must use 1d array when using non record arrays.'
#                traceback[err_path] = msg
#                return False, traceback

        return test, traceback

    def _post_setattr_mode(self, old, new):
        """ Update the database entries according to the mode.

        """


def complex_fit(f, xData, yData, p0, weights=None, bounds=()):
    if np.isscalar(p0):
        p0 = np.array([p0])

    def residuals(params, x, y):
        if weights is not None:
            diff = weights * f(x, *params) - y
        else:
            diff = f(x, *params) - y
        flatDiff = np.zeros(diff.size * 2, dtype=np.float64)
        flatDiff[0:flatDiff.size:2] = diff.real
        flatDiff[1:flatDiff.size:2] = diff.imag
        return flatDiff

    res = leastsq(residuals, p0, args=(xData, yData), maxfev=1000,
                  ftol=1e-2, full_output=1)
    return res[0], res[1]


def complex_a_out(f, f_0, kc, ki, a_in, T):  # kc and ki are kappas/2pi
    D = f - f_0
    num = - 1j*D + (kc - ki)/2
    den = 1j*D + (kc+ki)/2
    if kc > 0 and ki > 0 and f_0 > 0:
        return num/den*a_in*np.exp(1j*D*T)
    else:
        return np.Inf


def fit_complex_a_out(f, a_out):
    f_0 = get_f0_reflection(f, a_out)
    kc = (np.max(f) - np.min(f))/10.
    ki = kc
    T = 0

    def aux(f, f_0, kc, ki, re_a_in, im_a_in, T):
        return complex_a_out(f, f_0, kc, ki, re_a_in + 1j*im_a_in, T)
    a_in = -a_out[0]
    popt, pcov = complex_fit(aux, f, a_out, (f_0, kc, ki, np.real(a_in),
                                             np.imag(a_in), T))
    return popt[0]


def get_f0_reflection(f, a_out):
    phase = np.unwrap(np.angle(a_out))
    phase_avg = (np.min(phase)+np.max(phase))/2
    spline = splrep(f, phase-phase_avg)
    roots = sproot(spline)
    if len(roots) != 1:
        maglin = np.abs(a_out)
        f0 = f[np.argmin(maglin)]
    else:
        f0 = roots[0]
    return f0


def lorentzian(x, x0, y0, A, B):
    numerator = A
    denominator = (x - x0)**2 + B
    y = y0 + (numerator/denominator)
    return y


def fit_lorentzian(x, y):
    ymax = np.max(y)
    index = np.argmax(y)
    x0 = x[index]
    y0 = min(y)

    spline = splrep(x, y-(y0+ymax)/2)
    roots = sproot(spline)
    whm = roots[-1]-roots[0]

    B = whm*whm/4.0
    A = B*(ymax-y0)
    popt, pcov = curve_fit(lorentzian, x, y, (x0, y0, A, B))

    return popt[0]
