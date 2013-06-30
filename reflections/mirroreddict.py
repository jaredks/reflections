#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# reflections: dict subclasses for bidirectional key, value access
# Copyright: (c) 2013, Jared Suttles. All rights reserved.
# License: See LICENSE for details.
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
from .utils import DictSubclassMixin, InverseEnabledMixin, Container, slice_notation


class Reflection(object):
    """
    Constant time data structure used to hold objects in a mapping when there are duplicate values in the inverse.
    """
    __slots__ = ['_set', '_key', '_inverse_dict']

    def __init__(self, inverse_dict, key, element=None):
        self._set = set()
        if element is not None:
            self._set.add(Container.make_hashable(element))
        self._key = key
        self._inverse_dict = inverse_dict

    def __len__(self):
        return len(self._set)

    def __iter__(self):
        return (ele.contents if isinstance(ele, Container) else ele for ele in self._set)

    def __contains__(self, item):
        return item in self._set

    def __repr__(self):
        return '|{}|'.format(', '.join(map(repr, self._set)))

    @Container.make_key_hashable
    def add(self, element):
        self._set.add(element)
        self._inverse_dict._expand(element, self._key)
        return self
    __iadd__ = add

    @Container.make_key_hashable
    def remove(self, element):
        self._set.remove(element)
        self._inverse_dict._contract(element, self._key)
        return self
    __isub__ = remove

    def discard(self, element):
        try:
            self.remove(element)
        except KeyError:
            return

    def update(self, iterable):
        for ele in iterable:
            if ele not in self._set:
                self.add(ele)

    def _remove_last(self):
        if len(self) == 1:
            return self._set.pop()


class MirroredDict(InverseEnabledMixin, DictSubclassMixin, dict):
    """
    Implements a bidirectional mapping which allows for duplicate values by holding each key of a duplicated value in a
    set structure for the inverse dict. Can be used exactly as a normal dict but with access to an inverse mapping of
    values to keys, which would contain Reflection objects if not all values are unique. Although, mutable objects
    are used as keys to allow for mutable values (just like a normal dict), they are of limited usefulness as their
    values are accessed by object identity.
    """
    def __init__(self, *args, **kwargs):
        self._reflectvalues = False
        super(MirroredDict, self).__init__(*args, **kwargs)

    @property
    def reflectvalues(self):
        return self._reflectvalues

    @reflectvalues.setter
    def reflectvalues(self, choice):
        self._reflectvalues = choice

    @slice_notation
    @Container.make_key_hashable
    def __getitem__(self, key):
        return super(MirroredDict, self).__getitem__(key)

    @slice_notation
    def __setitem__(self, key, value):
        if key in self:  # overwriting an existing key
            if value is self[key]:  # ignore if same object (this is for += and -= of Reflection)
                return
            self._inverse._contract(self[key], key)
        if self._reflectvalues:
            reflect = Reflection(self.inverse, key)
            reflect.update(value)
            value = reflect
        else:
            self._inverse._expand(value, key)
        super(MirroredDict, self).__setitem__(key, value)

    @slice_notation
    def __delitem__(self, key):
        self._inverse._contract(self[key], key)
        super(MirroredDict, self).__delitem__(key)

    def keys(self):
        return list(self.iterkeys())

    def iterkeys(self):
        return (key.contents if isinstance(key, Container) else key for key in super(MirroredDict, self).iterkeys())
    __iter__ = iterkeys

    def pop(self, *args, **kwargs):
        before = len(self)
        value = super(MirroredDict, self).pop(*args, **kwargs)
        if len(self) != before:
            self._inverse._contract(value, args[0])
        return value

    def popitem(self):
        key, value = super(MirroredDict, self).popitem()
        self._inverse._contract(value, key)
        return key, value

    @Container.make_key_hashable
    def _expand(self, key, value):
        if key in self:
            if not isinstance(self[key], Reflection):
                super(MirroredDict, self).__setitem__(key, Reflection(self.inverse, key, self[key]))
            self[key]._set.add(value)
        else:
            super(MirroredDict, self).__setitem__(key, value)

    @Container.make_key_hashable
    def _contract(self, key, value):  # if >1 value for key, delete value; otherwise delete key, value pair
        if isinstance(key, Reflection):  # key actually set of keys; NOTE: value cannot ever be a set
            for k in key:
                self._contract(k, value)  # recursively call on each key in set
        else:
            if isinstance(self[key], Reflection):
                self[key]._set.remove(value)
                if len(self[key]) == 1:  # don't want to keep a singleton set
                    super(MirroredDict, self).__setitem__(key, self[key]._remove_last())
            else:
                super(MirroredDict, self).__delitem__(key)
