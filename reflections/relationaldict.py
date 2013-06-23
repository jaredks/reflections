#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# reflections: dict subclasses for bidirectional key, value access
# Copyright: (c) 2013, Jared Suttles. All rights reserved.
# License: See LICENSE for details.
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
from .mirroreddict import MirroredDict, Reflection
from .utils import Container, slice_notation


class RelationalDict(MirroredDict):
    """
    A subclass of MirroredDict, implementing a bidirectional mapping where values are part of a Reflection object, in
    both directions. Such a data structure can be used to model many-to-many relationships. Has autovivification of
    Reflection objects enabled as it serves as the only value for a RelationalDict (objects are created whenever new
    keys are referenced).
    """
    @slice_notation
    def __setitem__(self, key, value):
        if key in self:  # overwriting an existing key
            if value is self[key]:  # ignore if same object (this is for += and -= of Reflection)
                return
            self._inverse._contract(self[key], key)
        if not isinstance(value, Reflection):
            self._inverse._expand(value, key)
            value = Reflection(self._inverse, key, value)
        super(MirroredDict, self).__setitem__(key, value)

    def __missing__(self, key):
        return Reflection(self._inverse, key)

    @Container.make_key_hashable
    def _expand(self, key, value):
        if key in self:
            self[key]._set.add(value)
        else:
            super(MirroredDict, self).__setitem__(key, Reflection(self.inverse, key, value))

    def _contract(self, key, value):
        if isinstance(key, Reflection):
            for k in key:
                self._contract(k, value)
        else:
            key = Container._make_hashable(key)
            self[key]._set.remove(value)
            if len(self[key]) == 0:  # delete set when nothing in it
                super(MirroredDict, self).__delitem__(key)
ManyToManyDict = RelationalDict
