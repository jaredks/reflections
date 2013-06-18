reflections
===========

MirroredDict
------------

Works just like a normal Python `dict` on the surface

```python
>>> d = MirroredDict({2:22, 3:33, 4:22})
>>> d
{2: 22, 3: 33, 4: 22}
>>> d[6] = 33
>>> d
{2: 22, 3: 33, 4: 22, 6: 33}
```

Also maintains an inverse lookup (here with set-like objects)

```python
>>> ~d
{33: |3, 6|, 22: |2, 4|}
>>> (~d)[22]
|2, 4|
```

Can manipulate set objects directly and it will effect dictionary

```python
>>> (~d)[22] += 8
>>> ~d
{33: |3, 6|, 22: |8, 2, 4|}
>>> d
{8: 22, 2: 22, 3: 33, 4: 22, 6: 33}
```

Can use mutable objects as keys (values accessed by object identity)

```python
>>> d[5] = range(5)
>>> d
{2: 22, 3: 33, 4: 22, 5: [0, 1, 2, 3, 4], 6: 33, 8: 22}
>>> ~d
{[0, 1, 2, 3, 4]@1004a7488: 5, 33: |3, 6|, 22: |8, 2, 4|}
>>> z = d[5]
>>> (~d)[z]
5
```

Deleting a key, value pair which includes a set will delete each corresponding key, value pair in the inverse

```python
>>> del (~d)[33]
>>> ~d
{[0, 1, 2, 3, 4]@1004a7488: 5, 22: |8, 2, 4|}
>>> d
{2: 22, 4: 22, 5: [0, 1, 2, 3, 4], 8: 22}
```

BidirectionalDict / BiDict
--------------------------

Adds the value to the inverse `dict`. All keys must be unique and all values must be unique otherwise entries will be overwritten.

    A B D ...
    | | |
    B C A

```python
>>> d = BiDict(hi=2, hello=4, hola=2)
>>> d
{'hi': 2, 'hello': 4}
>>> ~d
{2: 'hi', 4: 'hello'}
>>> d['bonjour'] = 3
>>> d
{'bonjour': 3, 'hi': 2, 'hello': 4}
>>> ~d
{2: 'hi', 3: 'bonjour', 4: 'hello'}
>>> (~d)[5] = 'hi'
>>> d
{'bonjour': 3, 'hi': 5, 'hello': 4}
>>> ~d
{3: 'bonjour', 4: 'hello', 5: 'hi'}
```

TwoWayDict
----------

Simply adds the value as a key to the same `dict`. Best for when all elements are unique and each is part of a pair.

    A-B B-A C-D D-C ...

```python
>>> d = TwoWayDict()
>>> d[2] = 4
>>> d
{2: 4, 4: 2}
>>> d[3] = 6
>>> d
{2: 4, 3: 6, 4: 2, 6: 3}
>>> d[5] = 6
>>> d
{2: 4, 4: 2, 5: 6, 6: 5}
>>> del d[2]
>>> d
{5: 6, 6: 5}
```

Using
-----

    python setup.py install

Or just copy the script to your project.

License
-------

"Modified BSD License". See LICENSE for details. Copyright Jared Suttles, 2013.
