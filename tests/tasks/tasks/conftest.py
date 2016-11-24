# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015-2016 by EcpyHqcLegacy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Views for the PNA tasks.

"""
from __future__ import (division, unicode_literals, print_function,
                        absolute_import)

import pytest
import enaml

with enaml.imports():
    from ecpy_hqc_legacy.manifest import HqcLegacyManifest

pytest_plugins = str('ecpy.testing.tasks.fixtures'),


@pytest.yield_fixture
def task_workbench(task_workbench):
    """Task workbench in which the HqcLegacyManifest has been registered.

    """
    task_workbench.register(HqcLegacyManifest())
    yield task_workbench
    task_workbench.unregister('ecpy_hqc_legacy')
