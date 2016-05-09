# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015-2016 by EcpyHqcLegacy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Layout function used for instrument task views.

"""
from __future__ import (division, unicode_literals, print_function,
                        absolute_import)

from enaml.layout.api import grid, hbox


def auto_grid_layout(self):
    """
    """
    children = self.widgets()
    labels = [children[0]] + children[3::2]
    widgets = [hbox(children[1:2])] + children[4::2]
    n_labels = len(labels)
    n_widgets = len(widgets)
    if n_labels != n_widgets:
        if n_labels > n_widgets:
            labels.pop()
        else:
            widgets.pop()

    return [grid(labels, widgets)]
