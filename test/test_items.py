"""Test of the h5features.items module.

@author: Mathieu Bernard <mmathieubernardd@gmail.com>
"""

import h5py
import pytest

import generate
from utils import assert_raise, remove
from h5features.dataset.items import Items


class TestItemsInit:
    """Test of Items.__init__ and Items.check."""
    def test_good(self):
        args = [['a'], ['a', 'b'], [1], [1, 2]]
        for arg in args:
            assert arg == Items(arg).data

    def test_bad(self):
        args = [[1, 1], [1, 2, 2], ['a', 'b', 'c', 'a']]
        msg = 'all items must have different names.'
        for arg in args:
            assert_raise(Items, arg, msg)

class TestCreate:
    """Test of Items.create."""
    def setup(self):
        self.filename = 'test.h5'
        self.group = h5py.File(self.filename, 'w').create_group('group')
        self.items = Items(generate.items(10))

    def teardown(self):
        remove(self.filename)

    def test_create_good(self):
        self.items.create_dataset(self.group, 0.1)
        assert list(self.group.keys()) == ['items']

        group = self.group['items']
        assert group.name.split('/')[2] == 'items'
        assert group.shape == (0,)
        #assert group.chunks == (10,) TODO why this have changed ?
        assert group.chunks == (5000,)
        assert group.maxshape == (None,)
        assert group.dtype == type(str)

    def test_create_on_existing_group(self):
        self.group.create_dataset(self.items.name, (0,))
        with pytest.raises(RuntimeError) as err:
            self.items.create_dataset(self.group, 10)


def wrapper_is_compat(l1, l2):
    # Make l1 and l2 Items
    i1 = Items(l1)
    i2 = Items(l2)
    remove('test.h5.tmp')
    with h5py.File('test.h5.tmp') as h5file:
        g = h5file.create_group('deleteme')
        i2.create_dataset(g, 10)
        i2.write(g)
        res = i1.is_appendable_to(g)
    remove('test.h5.tmp')
    return res

class TestIsAppendableTo:
    def setup(self):
        self.filename = 'test.h5'
        self.items = Items(generate.items(10))
        self.h5file = h5py.File(self.filename)

    def teardown(self):
        remove(self.filename)
        remove('test.h5.tmp')

    def test_on_empty_group(self):
        group = self.h5file.create_group('group')
        assert_raise(self.items.is_appendable_to, group,
                     "unable to open object", KeyError)

        # Create an empty items group
        self.items.create_dataset(group, 10)
        assert self.items.is_appendable_to(group)

    def test_same_items_twice(self):
        group = self.h5file.create_group('group')
        self.items.create_dataset(group, 10)
        self.items.write(group)
        assert_raise(self.items.is_appendable_to, group,
                     'more than one shared items')

    def test_simple(self):
        l1 = ['c', 'd', 'e']
        l2 = ['a', 'b', 'c']
        l3 = [c for c in 'def']
        assert wrapper_is_compat(l1, l2)
        with pytest.raises(IOError):
            wrapper_is_compat(l2, l1)

        assert wrapper_is_compat(l2, l3)
        assert wrapper_is_compat(l3, l2)

        with pytest.raises(IOError):
            wrapper_is_compat(l1, l3)
        with pytest.raises(IOError):
            wrapper_is_compat(l3, l1)
        with pytest.raises(IOError):
            wrapper_is_compat(l1, l1)


class TestWrite:
    def setup(self):
        self.filename = 'test.h5'
        self.group = h5py.File(self.filename, 'w').create_group('group')
        self.items = Items(generate.items(10))

    def teardown(self):
        remove(self.filename)

    def test_write(self):
        self.items.create_dataset(self.group, 10)
        self.items.write(self.group)
        writed = self.group[self.items.name][...]

        assert len(writed) == 10
        assert self.items.data == list(writed)
        assert self.items == Items(list(writed))

    def test_init_by_copy(self):
        """creating items copy data"""
        items2 = Items(self.items.data)
        items2.data = [items2.data[1]]
        assert not items2 == self.items

    def test_side_effect(self):
        items2 = Items(self.items.data)
        self.items.create_dataset(self.group, 10)
        self.items.write(self.group)
        assert self.items == items2

    def test_append(self):
        self.items.create_dataset(self.group, 10)
        writed = self.group[self.items.name]
        assert len(writed[...]) == 0

        self.items.write(self.group)
        assert len(writed[...]) == 10

        self.items.write(self.group)
        assert len(writed[...]) == 20

        items2 = Items(generate.items(5))
        items2.write(self.group)
        assert len(writed[...]) == 25

        del self.group[self.items.name]
        self.items.create_dataset(self.group, 10)
        assert len(self.group[self.items.name][...]) == 0
