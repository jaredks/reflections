#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# reflections: dict subclasses for bidirectional key, value access
# Copyright: (c) 2013, Jared Suttles. All rights reserved.
# License: See LICENSE for details.
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
from .utils import DictSubclassMixin, InverseEnabledMixin, slice_notation


class BidirectionalDict(InverseEnabledMixin, DictSubclassMixin, dict):
    """
    Implements a two-way mapping of key->value and value->key in two dicts, each of which being the inverse of the
    other. Use over TwoWayDict if there is a need to distinguish between normal and inverse mappings. In other words,
    when there is a directional relationship from key to value and knowing the inverse is sometimes helpful.
    """
    @slice_notation
    def __getitem__(self, key):
        return super(BidirectionalDict, self).__getitem__(key)

    @slice_notation
    def __setitem__(self, key, value):
        if key in self:
            super(BidirectionalDict, self._inverse).__delitem__(self[key])
        if value in self._inverse:
            super(BidirectionalDict, self).__delitem__(self._inverse[value])
        super(BidirectionalDict, self).__setitem__(key, value)
        super(BidirectionalDict, self._inverse).__setitem__(value, key)

    @slice_notation
    def __delitem__(self, key):
        super(BidirectionalDict, self._inverse).__delitem__(self[key])
        super(BidirectionalDict, self).__delitem__(key)

    def pop(self, *args, **kwargs):
        before = len(self)
        value = super(BidirectionalDict, self).pop(*args, **kwargs)
        if len(self) != before:
            super(BidirectionalDict, self._inverse).__delitem__(value)
        return value

    def popitem(self):
        key, value = super(BidirectionalDict, self).popitem()
        super(BidirectionalDict, self._inverse).__delitem__(value)
        return key, value
BiDict = BidirectionalDict
