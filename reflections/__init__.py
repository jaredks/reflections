#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# reflections: dict subclasses for bidirectional key, value access
# Copyright: (c) 2013, Jared Suttles. All rights reserved.
# License: See LICENSE for details.
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
__all__ = ['MirroredDict', 'RelationalDict', 'ManyToManyDict', 'BidirectionalDict', 'BiDict', 'TwoWayDict']

__title__ = 'reflections'
__version__ = '1.0.1'
__author__ = 'Jared Suttles'
__license__ = 'Modified BSD'
__copyright__ = 'Copyright 2013 Jared Suttles'

from .mirroreddict import MirroredDict
from .relationaldict import RelationalDict, ManyToManyDict
from .bidict import BidirectionalDict, BiDict
from .twowaydict import TwoWayDict
