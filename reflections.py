#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# reflections: dict subclasses for bidirectional key, value access
# Copyright: (c) 2013, Jared Suttles. All rights reserved.
# License: See LICENSE for details.
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
__all__ = ['MirroredDict', 'BidirectionalDict', 'BiDict', 'TwoWayDict']


class ReflectiveDict(object):
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
                    raise ValueError(
                        'MirroredDict update sequence element #{} has length {}; 2 is required'.format(n, len(it)))
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

    def _determine_key_direction(self, key):
        if isinstance(key, slice):  # problem: can't use slice notation to access elements that eval to False
            if (key.start is None) is (key.stop is None) or key.step is not None:
                raise TypeError('item access must be either normal [key:] or inverted [:key]')
            if key.stop is None:
                return key.start, self
            return key.stop, self._inverse
        return key, self

    def clear(self):
        #super(self.__class__, self).clear()
        #super(self.__class__, self._inverse).clear()
        dict.clear(self)
        dict.clear(self._inverse)


class MirroredDict(ReflectiveDict, InverseEnabled, dict):
    """
    Implements a bidirectional mapping which allows for duplicate values by holding each key of a duplicated value in a
    set structure for the inverse dict. Can be used exactly as a normal dict but with access to an inverse mapping of
    values to keys, which would contain MirroredDictSet objects if not all values are unique. Although, mutable objects
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

    def __getitem__(self, key):
        key, whichdict = self._determine_key_direction(key)
        if key.__hash__ is None:  # if unhashable type
            key = Container(key)  # use object identity
        return super(MirroredDict, whichdict).__getitem__(key)

    def __setitem__(self, key, value):
        key, whichdict = self._determine_key_direction(key)
        if key in whichdict:  # overwriting an existing key
            if value is whichdict[key]:  # ignore if same object (this is for += and -= of MirroredDictSet)
                return
            whichdict._inverse._contract(whichdict[key], key)
        whichdict._inverse._expand(value, key)
        super(MirroredDict, whichdict).__setitem__(key, value)

    def __delitem__(self, key):
        key, whichdict = self._determine_key_direction(key)
        whichdict._inverse._contract(whichdict[key], key)
        super(MirroredDict, whichdict).__delitem__(key)

    def keys(self):
        return list(self.iterkeys())

    def iterkeys(self):
        return (key.contents if isinstance(key, Container) else key for key in super(MirroredDict, self).iterkeys())
    __iter__ = iterkeys

    #def clear(self):
    #    super(MirroredDict, self).clear()
    #    super(MirroredDict, self._inverse).clear()

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

    def _expand(self, key, value):
        if key.__hash__ is None:
            key = Container(key)
        if key in self:
            if not isinstance(self[key], MirroredDictSet):
                super(MirroredDict, self).__setitem__(key, MirroredDictSet(self[key], key, self.inverse))
            self[key]._set.add(value)
        else:
            super(MirroredDict, self).__setitem__(key, value)

    def _contract(self, key, value):  # if >1 value for key, delete value; otherwise delete key, value pair
        if key.__hash__ is None:
            key = Container(key)
        if isinstance(key, MirroredDictSet):  # key actually set of keys; NOTE: value cannot ever be a set
            for k in key:
                self._contract(k, value)  # recursively call on each key in set
        else:
            if isinstance(self[key], MirroredDictSet):
                self[key]._set.remove(value)
                if len(self[key]) == 1:  # don't want to keep a singleton set
                    super(MirroredDict, self).__setitem__(key, self[key]._remove_last())
            else:
                super(MirroredDict, self).__delitem__(key)


class MirroredDictSet(object):
    """
    Constant time data structure used to hold objects in a mapping when there are duplicate values in the inverse.
    """
    __slots__ = ['_set', '_key', '_inverse_dict']

    def __init__(self, element, key, inverse_dict):
        try:
            self._set = {element}
        except TypeError:  # unhashable
            self._set = {Container(element)}
        self._key = key
        self._inverse_dict = inverse_dict

    def __len__(self):
        return len(self._set)

    def __iter__(self):
        return (ele.contents if isinstance(ele, Container) else ele for ele in self._set)

    def __repr__(self):
        return '|{}|'.format(', '.join([repr(ele) for ele in self._set]))

    def add(self, element):
        self._set.add(element)
        self._inverse_dict._expand(element, self._key)
        return self
    __iadd__ = add

    def remove(self, element):
        if element.__hash__ is None:
            element = Container(element)
        self._set.remove(element)
        self._inverse_dict._contract(element, self._key)
        return self
    __isub__ = remove

    def _remove_last(self):
        if len(self) == 1:
            return self._set.pop()


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


class BidirectionalDict(ReflectiveDict, InverseEnabled, dict):
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

    def __getitem__(self, key):
        key, whichdict = self._determine_key_direction(key)
        return super(BidirectionalDict, whichdict).__getitem__(key)

    def __setitem__(self, key, value):
        key, whichdict = self._determine_key_direction(key)
        if key in whichdict:
            super(BidirectionalDict, whichdict._inverse).__delitem__(whichdict[key])
        if value in whichdict._inverse:
            super(BidirectionalDict, whichdict).__delitem__(whichdict._inverse[value])
        super(BidirectionalDict, whichdict).__setitem__(key, value)
        super(BidirectionalDict, whichdict._inverse).__setitem__(value, key)

    def __delitem__(self, key):
        key, whichdict = self._determine_key_direction(key)
        super(BidirectionalDict, whichdict._inverse).__delitem__(whichdict[key])
        super(BidirectionalDict, whichdict).__delitem__(key)

    #def clear(self):
    #    super(BidirectionalDict, self).clear()
    #    super(BidirectionalDict, self._inverse).clear()

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


class TwoWayDict(ReflectiveDict, dict):
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
