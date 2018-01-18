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
from atom.api import (Enum, Bool, Unicode, set_default, Float, Int)
from scipy.interpolate import splrep, sproot, splev
from scipy.optimize import curve_fit, leastsq
import scipy.ndimage.filters as flt
import matplotlib.pyplot as plt

import logging
from ecpy.tasks.api import SimpleTask, InterfaceableTaskMixin, TaskInterface
from ecpy.tasks.api import validators

ARR_VAL = validators.Feval(types=np.ndarray)


class FitResonanceTask(InterfaceableTaskMixin, SimpleTask):
    """ Load an array from the disc into the database.

    """
    #: Name of the target in the database.
    target_array = Unicode().tag(pref=True, feval=ARR_VAL)
    ref_array = Unicode().tag(pref=True, feval=ARR_VAL)
    use_ref = Bool(False).tag(pref=True)
    if use_ref:
        print('bah')
    #: Kind of data to fit.
    selected_format = Unicode().tag(pref=True)

    wait = set_default({'activated': True})  # Wait on all pools by default.

    database_entries = set_default({'res_value': 1.0, 'fit_err': 0.0})

    def check(self, *args, **kwargs):
        """Check that the provided path and filename make sense.

        """
        test, traceback = super(FitResonanceTask, self).check(*args, **kwargs)
        err_path = self.get_error_path()

        if not test:
            return test, traceback

#        full_folder_path = self.format_string(self.folder)
#        filename = self.format_string(self.filename)
#        full_path = os.path.join(full_folder_path, filename)
#
#        if not os.path.isfile(full_path):
#            msg = ('File does not exist, be sure that your measure  will '
#                   'create it before this task is executed.')
#            traceback[err_path + '-file'] = msg

        return test, traceback


class FitVNAInterface(TaskInterface):
    """ Store the pair(s) of index/value for the resonance frequency.

    Wait for any parallel operation before execution.

    """
    #: Name of the column into which the extrema should be looked for.
    column_name_maglin = Unicode().tag(pref=True)
    column_name_phase = Unicode().tag(pref=True)
    column_name_freq = Unicode().tag(pref=True)

    #: Flag indicating the measurement setup. This changes the fit function
    mode = Enum('Reflection', 'Transmission', 'Lorentzian').tag(pref=True)

    array_format = ['VNA']

    def perform(self):
        """ Find resonance frequency of database array and store index/value
            pairs.

        """
        task = self.task
        array = task.format_and_eval_string(task.target_array)
        if 1 == 1:
            array_ref = task.format_and_eval_string(task.ref_array)

        freq = array[self.column_name_freq]
        data_maglin = array[self.column_name_maglin]

        if self.mode == 'Reflection':
            if 1 == 1:
                freq_ref = array_ref[self.column_name_freq]
                data_maglin_ref = array_ref[self.column_name_maglin]
                data_phase_ref = array_ref[self.column_name_phase]
            data_phase = array[self.column_name_phase]
            data_c = data_maglin*np.exp(1j*np.pi/180*data_phase)
            if 1 == 1:
                data_c_ref = data_maglin_ref*np.exp(1j*np.pi/180*data_phase_ref)
                data_c = data_c/data_c_ref

        if self.mode == 'Lorentzian':
            data_error = array[self.column_name_phase]
        if self.mode == 'Reflection':
            try:
                val, fit_err = fit_complex_a_out(freq, data_c)
            except:
                val = 1e9
                fit_err = 100
        if self.mode == 'Transmission':
            try:
                print(np.shape(freq), np.shape(data_maglin))
                val, fit_err = fit_lorentzian(freq, data_maglin)
            except:
                val = 1e9
                fit_err = 100
        if self.mode == 'Lorentzian':
            try:
                val, fit_err = fit_lorentzian(freq, data_maglin, error=data_error)
            except:
                val = 1e9
                fit_err = 100

        task.write_in_database('res_value', val)
        print('freq = '+str(np.round(val*1e-9, 5)*1e9) + ', error = '+str(np.round(fit_err, 2)))
        task.write_in_database('fit_err', fit_err)
        if fit_err > 1:
            log = logging.getLogger(__name__)
            msg = ('Fit resonance has abnormally high fit error,'
                   'freq fit = {} GHz, relative error = {}')
            log.warning(msg.format(round(val*1e-9, 3), round(fit_err, 2)))

    def check(self, *args, **kwargs):
        """ Check the target array can be found and has the right column.

        """
#        test, traceback = super(FitResonanceTask, self).check(*args, **kwargs)
#
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

        return True, {}

    def _post_setattr_mode(self, old, new):
        """ Update the database entries according to the mode.

        """

class FitAlazarInterface(TaskInterface):
    """ Store the pair(s) of index/value for the resonance frequency.

    Wait for any parallel operation before execution.

    """
    #: Name of the column into which the extrema should be looked for.
    column_name_Icor = Unicode().tag(pref=True)
    column_name_Qcor = Unicode().tag(pref=True)
    column_name_freq = Unicode().tag(pref=True)
    Tdelay = Unicode().tag(pref=True)

    #: Flag indicating the measurement setup. This changes the fit function
    mode = Enum('Reflection', 'Transmission', 'Lorentzian').tag(pref=True)

    array_format = ['Alazar']

    def perform(self):
        """ Find resonance frequency of database array and store index/value
            pairs.

        """
        task = self.task
        array = task.format_and_eval_string(task.target_array)
        if 1 == 0:
            array_ref = task.format_and_eval_string(task.ref_array)

        freq = 1e9*array[self.column_name_freq]
        Icor = array[self.column_name_Icor]
        Qcor = array[self.column_name_Qcor]
        Tdelay = float(task.format_and_eval_string(self.Tdelay))*1e-9
        data_c = (Icor + 1j*Qcor)*np.exp(1j*2*np.pi*freq*Tdelay)
        data_maglin = np.abs(data_c)

        if self.mode == 'Reflection':
            try:
                val, fit_err = fit_complex_a_out(freq, data_c)
            except:
                val = 1e9
                fit_err = 100
        if self.mode == 'Transmission':
            try:
                print(np.shape(freq), np.shape(data_maglin))
                val, fit_err = fit_lorentzian(freq, data_maglin)
            except:
                val = 1e9
                fit_err = 100
        if self.mode == 'Lorentzian':
            try:
                val, fit_err = fit_lorentzian(freq, data_maglin)
            except:
                val = 1e9
                fit_err = 100

        task.write_in_database('res_value', val)
        print('freq = '+str(np.round(val*1e-9, 5)*1e9) + ', error = '+str(np.round(fit_err, 2)))
        task.write_in_database('fit_err', fit_err)
        if fit_err > 1:
            log = logging.getLogger(__name__)
            msg = ('Fit resonance has abnormally high fit error,'
                   'freq fit = {} GHz, relative error = {}')
            log.warning(msg.format(round(val*1e-9, 3), round(fit_err, 2)))

    def check(self, *args, **kwargs):
        """ Check the target array can be found and has the right column.

        """
#        test, traceback = super(FitResonanceTask, self).check(*args, **kwargs)
#
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

        return True, {}

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
    f_0, kc = get_f0_reflection(f, a_out)
    kc = 10e6
    ki = kc
    T = 0
#
#    plt.close('all')
#    fig, ax = plt.subplots(3)
#    ax[0].scatter(f, np.abs(a_out))
#    ax[1].scatter(f, np.angle(a_out))
#    ax[0].plot([f_0, f_0], [min(np.abs(a_out)), max(np.abs(a_out))])
#    ax[0].plot([f_0-kc, f_0+kc], [max(np.abs(a_out)), max(np.abs(a_out))])
#    ax[2].scatter(np.real(a_out), np.imag(a_out))
#    ax[2].axis('equal')
#    plt.show()

    def aux(f, f_0, kc, ki, re_a_in, im_a_in, T):
        return complex_a_out(f, f_0, kc, ki, re_a_in + 1j*im_a_in, T)
    a_in = -a_out[0]
    popt, pcov = complex_fit(aux, f, a_out, (f_0, kc, ki, np.real(a_in),
                                             np.imag(a_in), T))
    fit_error = 100*np.sqrt(pcov[0, 0])/popt[0]

#    print(popt)

#    a_out_fit = complex_a_out(f, *popt)
#    ax[0].plot(f, np.abs(a_out_fit))
#    ax[1].plot(f, np.angle(a_out_fit))
#
    return popt[0], fit_error


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

    phase_flt = flt.gaussian_filter(phase, 1)
    dphase_flt = np.diff(phase_flt)
    df = f[:-1]
    spline = splrep(df, dphase_flt-(max(dphase_flt)+min(dphase_flt))/2)
    roots = sproot(spline)
    kc = roots[-1]-roots[0]
    return f0, kc


def lorentzian(x, x0, y0, A, B):
    numerator = A
    denominator = (x - x0)**2 + B
    y = y0 + (numerator/denominator)
    return y


def fit_lorentzian(x, y, error=None):
    if error is not None:
        for ii in range(len(y)):
            if error[ii] > 1:
                y[ii] = y[ii-1]

    ymean = np.mean(y)
    ymax = np.amax(y)
    ymin = np.amin(y)
    if ymean < (ymax+ymin)/2:
        index = np.argmax(y)
#        print(index)
        y0 = ymin
    else:
        ymax = ymin
        index = np.argmin(y)
        y0 = ymax
    x0 = x[index]
    spline = splrep(x, y-(y0+ymax)/2)
    roots = sproot(spline)
    whm = roots[-1]-roots[0]

    B = whm*whm/4.0
    A = B*(ymax-y0)
    popt, pcov = curve_fit(lorentzian, x, y, (x0, y0, A, B))
    fit_error = 100*np.sqrt(pcov[0, 0])/popt[0]

#    plt.close('all')
#    fig, ax = plt.subplots()
#    ax.scatter(x, y)
#    ax.plot(x, lorentzian(x, *popt))
#    ax.plot([min(x), max(x)], [y0, y0])
#    ax.plot([min(x), max(x)], [ymax, ymax])
#    ax.plot([x0, x0], [y0, ymax])
#    plt.show()
#    print(popt)
    return popt[0], fit_error
