#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# reflections: dict subclasses for bidirectional key, value access
# Copyright: (c) 2013, Jared Suttles. All rights reserved.
# License: See LICENSE for details.
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
from .utils import DictSubclassMixin


class TwoWayDict(DictSubclassMixin, dict):
    """
    Implements a two-way mapping of key->value and value->key within the same dictionary. Use over BidirectionalDict if
    there is no logical distinction between normal and inverse mappings. In other words, when there is a mutual
    association from key to value and from value to key.
    """
    def __setitem__(self, key, value):
        if key in self:
            super(TwoWayDict, self).__delitem__(self[key])
        if value in self:
            super(TwoWayDict, self).__delitem__(self[value])
        super(TwoWayDict, self).__setitem__(key, value)
        super(TwoWayDict, self).__setitem__(value, key)

    def __delitem__(self, key):
        super(TwoWayDict, self).__delitem__(self[key])
        super(TwoWayDict, self).__delitem__(key)

    def pop(self, *args, **kwargs):
        before = len(self)
        value = super(TwoWayDict, self).pop(*args, **kwargs)
        if len(self) != before:
            super(TwoWayDict, self).__delitem__(value)
        return value

    def popitem(self):
        key, value = super(TwoWayDict, self).popitem()
        super(TwoWayDict, self).__delitem__(value)
        return key, value
