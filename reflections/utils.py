#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# reflections: dict subclasses for bidirectional key, value access
# Copyright: (c) 2013, Jared Suttles. All rights reserved.
# License: See LICENSE for details.
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -


class DictSubclassMixin(object):
    """
    Mix-in for generic methods that replicate functionality of dict but instead call methods of the subclass. __init__ 
    is defined in terms of update and both update and setdefault are abstractions of __setitem__. In other words, all 
    methods in this mix-in rely on the specific implementation of __setitem__ for the class inheriting from 
    DictSubclassMixin.
    """
    def __init__(self, *args, **kwargs):
        super(DictSubclassMixin, self).__init__()
        self.update(*args, **kwargs)

    def setdefault(self, key, default=None):
        if key in self:
            return self[key]
        self[key] = default
        return default

    def update(self, iterable=None, **kwargs):
        if iterable is not None:
            for n, it in enumerate(iterable.iteritems() if isinstance(iterable, dict) else iterable):
                it = tuple(it)
                if len(it) != 2:
                    raise ValueError('{} update sequence element #{} has length {}; 2 is required'.format(
                        self.__class__.__name__, n, len(it)))
                key, value = it
                self[key] = value
        for key, value in kwargs.iteritems():
            self[key] = value


class InverseEnabledMixin(object):
    """
    Mix-in for methods shared between dict subclasses supporting an explicit inverted dictionary.
    """
    def __init__(self, *args, **kwargs):
        inverse = super(InverseEnabledMixin, self).__new__(self.__class__)
        self._inverse, inverse._inverse = inverse, self
        super(InverseEnabledMixin, self._inverse).__init__()
        super(InverseEnabledMixin, self).__init__(*args, **kwargs)

    def __invert__(self):
        return self._inverse
    inverse = property(__invert__)

    def clear(self):
        super(InverseEnabledMixin, self).clear()
        super(InverseEnabledMixin, self._inverse).clear()


def slice_notation(adjusting_function):
    """
    Decorator that returns replacement function using a slice object to determine correct dict (normal or inverse) and
    key or raises an exception.
    """
    def directed_adjustment(self, key, value=None):
        if isinstance(key, slice):  # problem: can't use slice notation to access elements that eval to False
            if (key.start is None) is (key.stop is None) or key.step is not None:
                raise TypeError('item access must be either normal [key:] or inverted [:key]')
            args = [self, key.start] if key.stop is None else [self._inverse, key.stop]
        else:
            args = [self, key]
        if value is not None:
            args.append(value)
        return adjusting_function(*args)
    return directed_adjustment


class Container(object):
    """
    Wraps mutable, unhashable data structures for use as keys. When hashed, can only access value using object identity.
    Don't actually use this outside of the contrived case of a key in an inverse dictionary.
    """
    __slots__ = 'contents'

    def __init__(self, contents):
        self.contents = contents

    def __eq__(self, other):
        return id(self.contents) == id(other.contents)

    def __hash__(self):
        return id(self.contents)

    def __repr__(self):
        return '{}@{}'.format(repr(self.contents), hex(id(self.contents))[2:])

    @classmethod
    def make_hashable(cls, item):
        try:
            hash(item)
            return item
        except TypeError:  # unhashable
            return cls(item)

    @classmethod
    def make_key_hashable(cls, key_function):
        return lambda self, *args: key_function(self, cls.make_hashable(args[0]), *args[1:])
