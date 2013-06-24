reflections
===========

MirroredDict
------------

Works just like a normal Python `dict` on the surface

```python
>>> euler_phi = MirroredDict({7:6, 8:4, 9:6, 10:4, 11:10})
>>> euler_phi
{8: 4, 9: 6, 10: 4, 11: 10, 7: 6}
>>> euler_phi[12] = 4
>>> euler_phi
{7: 6, 8: 4, 9: 6, 10: 4, 11: 10, 12: 4}
```

Also maintains an inverse lookup which uses unordered, constant-time reflection objects when there are equal values across multiple keys

```python
>>> ~euler_phi
{10: 11, 4: |8, 10, 12|, 6: |9, 7|}
>>> (~euler_phi)[4]
|8, 10, 12|
```

Normal and inverse lookup work using slice notation as well (inspired by [bidict](https://pypi.python.org/pypi/bidict))

```python
>>> euler_phi[12:]
4
>>> euler_phi[12:] == euler_phi[12]
True
>>> euler_phi[:6]
|9, 7|
```

Can manipulate reflection objects directly and it will effect dictionaries

```python
>>> euler_phi[:6] += 14
>>> ~euler_phi
{10: 11, 4: |8, 10, 12|, 6: |9, 14, 7|}
>>> euler_phi
{7: 6, 8: 4, 9: 6, 10: 4, 11: 10, 12: 4, 14: 6}
```

Deleting a key, value pair which includes a set will delete each corresponding key, value pair in the inverse

```python
>>> ~euler_phi
{10: 11, 4: |8, 10, 12|, 6: |9, 14, 7|}
>>> del euler_phi[:4]
>>> ~euler_phi
{10: 11, 6: |9, 14, 7|}
>>> euler_phi
{7: 6, 9: 6, 11: 10, 14: 6}
```

Can also use mutable objects as keys (values accessed by object identity)

```python
>>> series = MirroredDict({'first_primes': [2,3,5,7,9,11]})
>>> series
{'first_primes': [2, 3, 5, 7, 9, 11]}
>>> ~series
{[2, 3, 5, 7, 9, 11]@1004a7e60: 'first_primes'}
>>> series[:series['first_primes']]
'first_primes'
```

RelatonalDict
-------------

A subclass of MirroredDict, RelationalDict is useful for mapping relationships between elements. While MirroredDict has reflection objects for the inverse dictionary when multiple keys have the same value in the normal dictionary, RelationalDict autovivifies keys with values of those reflection objects in both directions.

An example use case would be a mapping of which people fancy which people.

```python
>>> likes = RelationalDict({'Thad':'Rhona', 'Marcos':'Kandi', 'Coleen':'Trevor'})
>>> likes['Thad'] += 'Kandi'
>>> likes['Rhona'].update(['Thad', 'Marcos'])
>>> likes['Trevor'] = 'Coleen'
>>> likes
{'Coleen': |'Trevor'|, 'Thad': |'Kandi', 'Rhona'|, 'Rhona': |'Marcos', 'Thad'|, 'Trevor': |'Coleen'|, 'Marcos': |'Kandi'|}
```

But we also want to know who is *liked by* who. Well that's easy enough.

```python
>>> liked_by = ~likes
>>> liked_by
{'Coleen': |'Trevor'|, 'Kandi': |'Thad', 'Marcos'|, 'Marcos': |'Rhona'|, 'Rhona': |'Thad'|, 'Trevor': |'Coleen'|, 'Thad': |'Rhona'|}
>>> len(liked_by['Kandi'])
2
>>> 'Coleen' in likes['Marcos']
False
>>> 'Coleen' in likes['Trevor']
True
```

BidirectionalDict / BiDict
--------------------------

Adds the value to the inverse `dict`. All keys must be unique and all values must be unique otherwise entries will be overwritten. Use over TwoWayDict if there is a need to distinguish between normal and inverse mappings.

    A B D ...
    | | |
    B C A

```python
>>> language_codes = BiDict(english='en', french='fr', spanish='es')
>>> language_codes
{'english': 'en', 'french': 'fr', 'spanish': 'es'}
>>> ~language_codes
{'fr': 'french', 'en': 'english', 'es': 'spanish'}
>>> language_codes[:'es']
'spanish'
>>> language_codes[:'de'] = 'german'
>>> language_codes
{'german': 'de', 'english': 'en', 'french': 'fr', 'spanish': 'es'}
>>> language_codes['american!'] = 'en'
>>> language_codes
{'german': 'de', 'american!': 'en', 'french': 'fr', 'spanish': 'es'}
```

TwoWayDict
----------

Simply adds the value as a key to the same `dict`. Best for when all elements are unique and each is part of a pair. Use over BidirectionalDict if there is no logical distinction between normal and inverse mappings.

    A-B B-A C-D D-C ...

```python
>>> pairs = TwoWayDict({'Mario':'Luigi', 'Peach':'Mario'})
>>> pairs
{'Mario'<->'Peach'}
>>> pairs['Peach']
'Mario'
>>> pairs['Mario']
'Peach'
>>> pairs['Link'] = 'Zelda'
>>> pairs
{'Mario'<->'Peach', 'Link'<->'Zelda'}
>>> pairs['Bowser'] = 'Mario'
>>> pairs
{'Zelda'<->'Link', 'Mario'<->'Bowser'}
```

Using
-----

    python setup.py install

License
-------

"Modified BSD License". See LICENSE for details. Copyright Jared Suttles, 2013.
