# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015-2016 by EcpyHqcLegacy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Routines to update a HQCMeas .ini file to the formats used by ecpy.

"""
from __future__ import (division, unicode_literals, print_function,
                        absolute_import)

import os
import shutil
from ast import literal_eval

from configobj import ConfigObj


#: Dependency id for tasks.
TASK_DEP_TYPE = 'ecpy.task'

#: Dependency id for task interfaces.
INTERFACE_DEP_TYPE = 'ecpy.tasks.interface'

#: Mapping between task_class (in HQCMeas) and task_id (in ecpy)
TASKS = {'ComplexTask': 'ecpy.ComplexTask',
         'WhileTask': 'ecpy.WhileTask',
         'ConditionalTask': 'ecpy.ConditionalTask',
         'BreakTask': 'ecpy.BreakTask',
         'ContinueTask': 'ecpy.ContinueTask',
         'LoopTask':  'ecpy.LoopTask',
         'LogTask': 'ecpy.LogTask',
         'DefinitionTask': 'ecpy.DefinitionTask',
         'FormulaTask': 'ecpy.FormulaTask',
         'SleepTask': 'ecpy.SleepTask',
         'ArrayExtremaTask': 'ecpy_hqc_legacy.ArrayExtremaTask',
         'ArrayFindValueTask': 'ecpy_hqc_legacy.ArrayFindValueTask',
         'SaveTask': 'ecpy_hqc_legacy.SaveTask',
         'SaveFileTask': 'ecpy_hqc_legacy.SaveFileTask',
         'SaveFileHDF5Task': 'ecpy_hqc_legacy.SaveFileHDF5Task',
         'SaveArrayTask': 'ecpy_hqc_legacy.SaveArrayTask',
         'LoadArrayTask': 'ecpy_hqc_legacy.LoadArrayTask',
         'ApplyMagFieldTask': 'ecpy_hqc_legacy.ApplyMagFieldTask',
         'LockInMeasureTask': 'ecpy_hqc_legacy.LockInMeasureTask',
         'MeasDCVoltageTask': 'ecpy_hqc_legacy.MeasDCVoltageTask',
         'SetRFFrequencyTask': 'ecpy_hqc_legacy.SetRFFrequencyTask',
         'SetRFPowerTask': 'ecpy_hqc_legacy.SetRFPowerTask',
         'SetRFOnOffTask': 'ecpy_hqc_legacy.SetRFOnOffTask',
         'PNASinglePointMeasureTask':
             'ecpy_hqc_legacy.PNASinglePointMeasureTask',
         'PNASweepTask': 'ecpy_hqc_legacy.PNASweepTask',
         'PNAGetTraces': 'ecpy_hqc_legacy.PNAGetTraces',
         'SetDCVoltageTask': 'ecpy_hqc_legacy.SetDCVoltageTask',
         'DemodSPTask': 'ecpy_hqc_legacy.DemodSPTask'}

#: Mapping between interface_class (in HQCMeas) and interface_id (in ecpy)
INTERFACES = {'IterableLoopInterface':
              'ecpy.LoopTask:ecpy.IterableLoopInterface',
              'LinspaceLoopInterface':
              'ecpy.LoopTask:ecpy.LinspaceLoopInterface',
              'MultiChannelVoltageSourceInterface':
              ('ecpy_hqc_legacy.SetDCVoltageTask:'
               'ecpy_hqc_legcy.MultiChannelVoltageSourceInterface'),
              'PNASetRFFrequencyInterface':
              ('ecpy_hqc_legacy.SetRFFrequencyTask:'
               'ecpy_hqc_legacy.PNASetRFFrequencyInterface'),
              'PNASetRFPowerInterface':
              ('ecpy_hqc_legacy.SetRFPowerTask:'
               'ecpy_hqc_legacy.PNASetRFPowerInterface'),
              'CSVLoadInterface':
              ('ecpy_hqc_legacy.LoadArrayTask:'
               'ecpy_hqc_legacy.CSVLoadInterface')}

#: Mapping between monitor_class and monitor_id
MONITORS = {'hqc_meas.measure.monitors.text_monitor':
            'ecpy.text_monitor'}


def update_task(task_config):
    """Update the informations about a task.

    Only the task itself is updated not its children or subparts.

    Parameters
    ----------
    task_config : configobj.Section
        Section holding the task infos that should be updated.

    """
    old_id = task_config['task_class']
    if old_id not in TASKS:
        raise ValueError('Unknown or unsupported task found %s' % old_id)
    task_config['task_id'] = TASKS[old_id]
    del task_config['task_class']
    task_config['dep_type'] = TASK_DEP_TYPE

    for key in ['selected_driver', 'selected_profile']:
        if key in task_config:
            del task_config[key]

    # XXX update access_exs
    if 'access_exs' in task_config:
        if task_config['access_exs'] == '[]':
            del task_config['access_exs']
        else:
            raise RuntimeError('Cannot handle access_exs')


def update_task_interface(interface_config):
    """Update the informations about a task interface.

    Only the task interface itself is updated not its children or subparts.

    Parameters
    ----------
    interface_config : configobj.Section
        Section holding the task interface infos that should be updated.

    """
    old_id = interface_config['interface_class']
    if old_id not in INTERFACES:
        raise ValueError('Unknown or unsupported interface found %s' % old_id)
    interface_config['interface_id'] = INTERFACES[old_id]
    del interface_config['interface_class']
    interface_config['dep_type'] = INTERFACE_DEP_TYPE


def update_monitor(config):
    """Update the informations related to a monitor.

    """
    del config['id']
    undisp = literal_eval(config['undisplayed'])
    config['undisplayed'] = repr(undisp + ['meas_name', 'meas_id',
                                           'meas_date'])
    for k in list(config):
        if k.startswith('rule_'):
            del config[k]
        elif k.startswith('custom_'):
            del config[k]

    config['rule_0'] = 'Loop progress'
    config['rule_1'] = 'Measure entries'


def iterate_on_sections(section, action_mapping):
    """Iterate on section sections and call the appropriate action on each.

    Parameters
    ----------
    section : Section
        Section whose subsections should be walked.

    action_mapping : dict
        Dictionary mapping test functions to callable that should be called if
        the test return True. Both callbale should take as single argument the
        section under inspection.

    """
    for s in section.sections:
        s = section[s]
        action = None
        for t in action_mapping:
            if t(s):
                action = action_mapping[t]
                break
        if action is None:
            raise ValueError('No matching action could be found for %s' % s)
        action(s)
        iterate_on_sections(s, action_mapping)


def convert_measure(meas_path, archive_folder=None, dest_folder=None):
    """Convert a measure created using HQCMeas to make it run on Ecpy.

    Parameters
    ----------
    meas_path : unicode
        Path to the file containing the measure to update.

    archive_folder : unicode or None, optional
        Path to the folder in which to store the old file after conversion.

    dest_folder : unicode or None, optional
        Save the new measure into the specified folder

    Returns
    -------
    new_path : unicode
        Location of the new file

    """
    config = ConfigObj(meas_path)

    # Update the main task hierarchy.
    update_task(config['root_task'])
    iterate_on_sections(config['root_task'],
                        {lambda x: 'task_class' in x: update_task,
                         lambda x: 'interface_class' in x:
                             update_task_interface})

    #: Update the monitors and delete the other non-existing tools
    for i in range(int(config['monitors'])):
        m_config = config['monitor_%s' % i]
        if m_config['id'] not in MONITORS:
            raise ValueError('Unknown monitor: %s' % m_config['id'])
        config.rename('monitor_%s' % i, MONITORS[m_config['id']])
        update_monitor(m_config)

    del config['monitors']
    del config['checks']
    del config['headers']

    if dest_folder:
        new_path = os.path.join(dest_folder,
                                os.path.basename(meas_path)[:-4] + '.meas.ini')
    else:
        new_path = meas_path[:-4] + '.meas.ini'

    print(config)
    with open(new_path, 'wb') as f:
        config.write(f)

    if archive_folder:
        shutil.move(meas_path, archive_folder)

    return new_path
