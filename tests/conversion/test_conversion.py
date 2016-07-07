# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015-2016 by EcpyHqcLegacy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Test the routines to update a HQCMeas .ini file to the formats used by ecpy.

"""
from __future__ import (division, unicode_literals, print_function,
                        absolute_import)

import os

import pytest
import enaml
from configobj import ConfigObj

from ecpy.measure.measure import Measure
from ecpy_hqc_legacy.conversion.convert import (update_task,
                                                update_task_interface,
                                                update_monitor,
                                                iterate_on_sections,
                                                convert_measure)

with enaml.imports():
    from ecpy.tasks.manifest import TaskManagerManifest


pytest_plugins = str('ecpy.testing.measure.fixtures'),


def test_update_task():
    """Test updating the informations about a task.

    """
    config = {'task_class': 'SetDCVoltageTask',
              'selected_driver': None,
              'selected_profile': None,
              'voltage': '1.0'}
    update_task(config)
    assert 'task_class' not in config
    assert config['task_id'] == 'ecpy_hqc_legacy.SetDCVoltageTask'
    assert 'dep_type' in config
    assert 'selected_driver' not in config
    assert 'selected_profile' not in config
    assert 'voltage' in config

    with pytest.raises(ValueError):
        config = {'task_class': '__dummy__'}
        update_task(config)


def test_update_task_interface():
    """Test updating the informations about a task interface.

    """
    config = {'interface_class': 'IterableLoopInterface',
              'iterable': '[]'}
    update_task_interface(config)
    assert 'interface_class' not in config
    assert config['interface_id'] == 'ecpy.IterableLoopInterface'
    assert 'dep_type' in config
    assert 'iterable' in config

    with pytest.raises(ValueError):
        config = {'interface_class': '__dummy__'}
        update_task_interface(config)


def test_update_monitor():
    """Test updating the informations related to a monitor.

    """
    config = {'id': None, 'undisplayed_entries': '[]', 'rule_0': {},
              'custom_0': {}}
    update_monitor(config)

    assert 'id' not in config
    assert config['undisplayed_entries'] == repr(['meas_name', 'meas_id',
                                                  'meas_date'])
    assert 'rule_0' not in config
    assert 'custom_0' not in config


def test_iterate_on_sections():
    """Test iterating on section sections

    """
    section = ConfigObj()
    section['a'] = {'val1': None}
    section['b'] = {'val2': None}
    section['b']['c'] = {'val3': None}

    class Checker(object):

        __slots__ = ('called')

        def __call__(self, section):
            self.called = True

    check1, check2 = Checker(), Checker()
    actions = {lambda x: 'val1' in x: check1, lambda x: 'val2' in x: check2}

    with pytest.raises(ValueError):
        iterate_on_sections(section, actions)

    assert check1.called
    assert check2.called


MEASURE_DIRECTORY = os.path.join(os.path.dirname(__file__), 'test_measures')


@pytest.mark.parametrize('meas_file', [])
def test_converting_a_measure(meas_workbench, meas_file, tmpdir):
    """Test converting a measure created using HQCMeas to make it run on Ecpy.

    """
    meas_workbench.register(TaskManagerManifest())
    plugin = meas_workbench.get_plugin('ecpy.measure')

    path = convert_measure(os.path.join(MEASURE_DIRECTORY, meas_file),
                           dest_folder=str(tmpdir))

    Measure.load(plugin, path)
