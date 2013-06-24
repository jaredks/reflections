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
    def __init__(self, *args, **kwargs):
        self._dictrepr = False
        super(TwoWayDict, self).__init__(*args, **kwargs)

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

    def __repr__(self):
        if self._dictrepr:
            return super(TwoWayDict, self).__repr__()
        seen = set()
        kvs = [seen.add(k) or (k,v) for k,v in self.iteritems() if v not in seen]  # hacky but fastest way I found
        return '{{{}}}'.format(', '.join([repr(k)+'<->'+repr(v) for k,v in kvs]))

    @property
    def dictrepr(self):
        return self._dictrepr

    @dictrepr.setter
    def dictrepr(self, choice):
        self._dictrepr = bool(choice)

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
