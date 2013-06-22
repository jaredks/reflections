#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# reflections: dict subclasses for bidirectional key, value access
# Copyright: (c) 2013, Jared Suttles. All rights reserved.
# License: See LICENSE for details.
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
__all__ = ['MirroredDict', 'RelationalDict', 'ManyToManyDict', 'BidirectionalDict', 'BiDict', 'TwoWayDict']


class DictSubclass(object):
    """
    Mix-in for generic methods that replicate functionality of dict but instead call methods of the subclass.
    """
    __slots__ = []

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


class InverseEnabled(object):
    """
    Mix-in for methods shared between dict subclasses supporting an explicit inverted dictionary.
    """
    __slots__ = []

    def __invert__(self):
        return self._inverse
    inverse = property(__invert__)

    def clear(self):
        dict.clear(self)
        dict.clear(self._inverse)

    @staticmethod
    def _slice_notation(adjusting_function):
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
    __slots__ = ['contents']

    def __init__(self, contents):
        self.contents = contents

    def __eq__(self, other):
        return id(self.contents) == id(other.contents)

    def __hash__(self):
        return id(self.contents)

    def __repr__(self):
        return '{}@{}'.format(repr(self.contents), hex(id(self.contents))[2:])

    @classmethod
    def _make_hashable(cls, item):
        try:
            hash(item)
            return item
        except TypeError:  # unhashable
            return cls(item)

    @classmethod
    def _make_key_hashable(cls, key_function):
        return lambda self, *args: key_function(self, cls._make_hashable(args[0]), *args[1:])


class MirroredDict(DictSubclass, InverseEnabled, dict):
    """
    Implements a bidirectional mapping which allows for duplicate values by holding each key of a duplicated value in a
    set structure for the inverse dict. Can be used exactly as a normal dict but with access to an inverse mapping of
    values to keys, which would contain Reflection objects if not all values are unique. Although, mutable objects
    are used as keys to allow for mutable values (just like a normal dict), they are of limited usefulness as their
    values are accessed by object identity.
    """
    __slots__ = ['_inverse']

    def __new__(cls, *args, **kwargs):
        instance = super(MirroredDict, cls).__new__(cls)
        inverse = super(MirroredDict, cls).__new__(cls)
        instance._inverse, inverse._inverse = inverse, instance
        return instance

    def __init__(self, *args, **kwargs):
        super(MirroredDict, self).__init__(*args, **kwargs)
        super(MirroredDict, self._inverse).__init__()
        for key, value in self.iteritems():
            self._inverse._expand(value, key)

    @InverseEnabled._slice_notation
    @Container._make_key_hashable
    def __getitem__(self, key):
        return super(MirroredDict, self).__getitem__(key)

    @InverseEnabled._slice_notation
    def __setitem__(self, key, value):
        if key in self:  # overwriting an existing key
            if value is self[key]:  # ignore if same object (this is for += and -= of Reflection)
                return
            self._inverse._contract(self[key], key)
        self._inverse._expand(value, key)
        super(MirroredDict, self).__setitem__(key, value)

    @InverseEnabled._slice_notation
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

    @Container._make_key_hashable
    def _expand(self, key, value):
        if key in self:
            if not isinstance(self[key], Reflection):
                super(MirroredDict, self).__setitem__(key, Reflection(self.inverse, key, self[key]))
            self[key]._set.add(value)
        else:
            super(MirroredDict, self).__setitem__(key, value)

    @Container._make_key_hashable
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


class Reflection(object):
    """
    Constant time data structure used to hold objects in a mapping when there are duplicate values in the inverse.
    """
    __slots__ = ['_set', '_key', '_inverse_dict']

    def __init__(self, inverse_dict, key, element=None):
        self._set = set()
        if element is not None:
            self._set.add(Container._make_hashable(element))
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

    @Container._make_key_hashable
    def add(self, element):
        self._set.add(element)
        self._inverse_dict._expand(element, self._key)
        return self
    __iadd__ = add

    @Container._make_key_hashable
    def remove(self, element):
        self._set.remove(element)
        self._inverse_dict._contract(element, self._key)
        return self
    __isub__ = remove

    @Container._make_key_hashable
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


class RelationalDict(MirroredDict):
    """
    A subclass of MirroredDict, implementing a bidirectional mapping where values are part of a Reflection object, in
    both directions. Such a data structure can be used to model many-to-many relationships. Autovivification of
    Reflection objects when new keys are referenced.
    """
    @InverseEnabled._slice_notation
    def __setitem__(self, key, value):
        if key in self:  # overwriting an existing key
            if value is self[key]:  # ignore if same object (this is for += and -= of Reflection)
                print 'same object!'
                return
            self._inverse._contract(self[key], key)
        if not isinstance(value, Reflection):
            self._inverse._expand(value, key)
            value = Reflection(self._inverse, key, value)
        super(MirroredDict, self).__setitem__(key, value)

    def __missing__(self, key):
        return Reflection(self._inverse, key)

    @Container._make_key_hashable
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


class BidirectionalDict(DictSubclass, InverseEnabled, dict):
    """
    Implements a two-way mapping of key->value and value->key in two dicts, each of which being the inverse of the
    other. Use over TwoWayDict if there is a need to distinguish between normal and inverse mappings. In other words,
    when there is a directional relationship from key to value and knowing the inverse is sometimes helpful.
    """
    __slots__ = ['_inverse']

    def __new__(cls, *args, **kwargs):
        instance = super(BidirectionalDict, cls).__new__(cls)
        inverse = super(BidirectionalDict, cls).__new__(cls)
        instance._inverse, inverse._inverse = inverse, instance
        return instance

    def __init__(self, *args, **kwargs):
        normal, inverse = {}, {}
        for k, v in dict(*args, **kwargs).iteritems():
            if k not in normal and v not in inverse:
                normal[k], inverse[v] = v, k
        super(BidirectionalDict, self).__init__(normal)
        super(BidirectionalDict, self._inverse).__init__(inverse)

    @InverseEnabled._slice_notation
    def __getitem__(self, key):
        return super(BidirectionalDict, self).__getitem__(key)

    @InverseEnabled._slice_notation
    def __setitem__(self, key, value):
        if key in self:
            super(BidirectionalDict, self._inverse).__delitem__(self[key])
        if value in self._inverse:
            super(BidirectionalDict, self).__delitem__(self._inverse[value])
        super(BidirectionalDict, self).__setitem__(key, value)
        super(BidirectionalDict, self._inverse).__setitem__(value, key)

    @InverseEnabled._slice_notation
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


class TwoWayDict(DictSubclass, dict):
    """
    Implements a two-way mapping of key->value and value->key within the same dictionary. Use over BidirectionalDict if
    there is no logical distinction between normal and inverse mappings. In other words, when there is a mutual
    association from key to value and from value to key.
    """
    __slots__ = []

    def __init__(self, *args, **kwargs):
        twoway = {}
        for k, v in dict(*args, **kwargs).iteritems():
            if k not in twoway and v not in twoway:
                twoway[k], twoway[v] = v, k
        super(TwoWayDict, self).__init__(twoway)

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
