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


from configobj import ConfigObj


#:
TASK_DEP_TYPE = 'ecpy.task'

#:
INTERFACE_DEP_TYPE = 'ecpy.tasks.interface'

#:
TASKS = {}

#:
INTERFACES = {}

#:
MONITORS = {}

#:
TEXT_MONITOR_RULES = {}


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
        raise ValueError('Unknown or unsupported task found %s' % old_id)
    interface_config['interface_id'] = INTERFACES[old_id]
    del interface_config['interface_class']
    interface_config['dep_type'] = TASK_DEP_TYPE


def rename_monitor_sections(config):
    """In HQCMeas monitors are indexed
    """


def update_monitor(config):
    """Update the informations related to a monitor.

    """
    del config['id']


def update_text_monitor_rule(config):
    """Update a text monitor rule.

    """
    r_class = config['class_name']
    if r_class not in TEXT_MONITOR_RULES:
        raise ValueError('Unknown text monitor rule: %s' % r_class)
    config['class_id'] = TEXT_MONITOR_RULES[r_class]
    del config['class_name']


def update_text_monitor_entry(config):
    """Update a custom text monitor entry.

    """
    pass


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
        iterate_on_sections(section, action_mapping)


def convert_measure(meas_path, archive_folder=None):
    """Convert a measure created using HQCMeas to make it run on Ecpy.

    Parameters
    ----------
    meas_path : unicode
        Path to the file containing the measure to update.

    archive_folder : unicode or None
        Path to the folder in which to store the old file after conversion.

    """
    config = ConfigObj(meas_path)

    # Update the main task hierarchy.
    update_task['root_task']
    iterate_on_sections(config['root_task'],
                        {lambda x: 'task_class' in x: update_task,
                         lambda x: 'interface_class' in x:
                             update_task_interface})

    #: Update the monitors and delete the other non-existing tools
    monitor_actions = {lambda x: 'displayed_entries' in x: update_monitor,
                       lambda x: 'class_name' in x: update_text_monitor_rule,
                       lambda x: 'depend_on' in x: update_text_monitor_entry}
    for i in int(config['monitors']):
        m_config = config['monitor_%s' % i]
        if m_config['id'] not in MONITORS:
            raise ValueError('Unknown monitor: %s' % m_config['id'])
        config.rename('monitor_%s', MONITORS[m_config['id']])
        iterate_on_sections(m_config, monitor_actions)

    del config['monitors']
    del config['checks']
    del config['headers']
    new_path = meas_path.rstrip('.ini') + '.meas.ini'
    with open(new_path, 'wb') as f:
        config.write(f)
