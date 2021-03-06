"""Test of read/write facilities of the h5features module.

@author: Mathieu Bernard
"""

import os
import numpy as np
import h5py
import pytest

import h5features.h5features as h5f
import generate
from utils import remove, assert_raise

def test_raise_on_write_sparse():
    a, b, c = generate.full(1)
    with pytest.raises(NotImplementedError) as ioerror:
        h5f.write('test.h5', 'group', a, b, c, dformat='sparse')
    assert 'sparse' in str(ioerror.value)

class TestH5FeaturesWrite:
    """Test write methods."""

    def setup(self):
        self.filename = 'test.h5'

    def teardown(self):
        remove(self.filename)

    def test_bad_data(self):
        with pytest.raises(IOError) as ioerror:
            h5f.write('/silly/path/to/no/where.h5', 'group', [], [], [])
        assert 'data is empty' == str(ioerror.value)

    def test_bad_file(self):
        a, b, c = generate.full(2)
        with pytest.raises(IOError) as ioerror:
            h5f.write('/silly/path/to/no/where.h5', 'group', a, b, c)
        assert all([s in str(ioerror.value)]
                   for s in ['/silly/path', 'No such file'])

    def test_bad_file2(self):
        with open(self.filename, 'w') as f:
            f.write('This is not a HDF5 file')

        with pytest.raises(IOError) as ioerror:
            h5f.write(self.filename, 'group', [], [], [])
        msg = str(ioerror.value)
        assert self.filename in msg
        assert 'not a HDF5 file' in msg

    def test_simple_write(self):
        self.features_0 = np.random.randn(300, 20)
        self.times_0 = np.linspace(0, 2, 300)

        h5f.simple_write(self.filename, 'f',
                         self.times_0, self.features_0)

        with h5py.File(self.filename, 'r') as f:
            assert ['f'] == list(f.keys ())

            g = f.get('f')
            assert list(g.keys()) == (
                ['features', 'index', 'items', 'times'])

            assert g['features'].shape == (300,20)
            assert g['index'].shape == (1,)
            assert g['items'].shape == (1,)
            assert g['times'].shape == (300,)

    def test_write(self):
        files, times, features = generate.full(30, 20, 10)
        h5f.write(self.filename, 'f', files, times, features)

        with h5py.File(self.filename, 'r') as f:
            assert ['f'] == list(f.keys ())
            g = f.get('f')
            assert list(g.keys()) == ['features', 'index', 'items', 'times']
            assert g.get('features').shape[1] == 20
            assert g.get('index').shape == (30,)
            assert g.get('items').shape == (30,)
            assert g.get('features').shape[0] == g.get('times').shape[0]


class TestH5FeaturesReadWrite:
    """Test more advanced read/write facilities.

    This is a legacy test from h5features-1.0. It ensures the
    top-down compatibility of the module from current version to 1.0.

    """

    def setup(self):
        self.filename = 'test.h5'
        self.dim = 20 # Dimensions of the features

    def teardown(self):
        remove(self.filename)

    def test_write_simple(self):
        # write/read a file with a single item
        features_0 = np.random.randn(300, self.dim)
        times_0 = np.linspace(0, 2, 300)
        h5f.simple_write(self.filename, 'group1', times_0, features_0, 'item')
        t0, f0 = h5f.read(self.filename, 'group1')

        times_0_r, features_0_r = h5f.read(self.filename, 'group1')
        assert list(times_0_r.keys()) == ['item']
        assert list(features_0_r.keys ()) == ['item']
        assert all(times_0_r['item'] == times_0)
        assert (features_0_r['item'] == features_0).all()


    def test_append(self):
        """Append a new item to an existing dataset."""
        i, t, f = generate.full(30, self.dim, 40, items_root='File')
        h5f.write(self.filename, 'group', i, t, f)

        # append new item to existing dataset
        features_added = np.zeros(shape=(1, self.dim))
        times_added = np.linspace(0, 2, 1)
        h5f.write(self.filename, 'group', ['File_31'],
                  [times_added], [features_added])

        with pytest.raises(IOError) as err:
            h5f.write(self.filename, 'group', ['File_3'],
                      [times_added], [features_added])
        assert 'data can be added only at the end' in str(err.value)


        # read it
        times_r, features_r = h5f.read(self.filename, 'group')
        assert set(times_r.keys()) == set(i+['File_31'])
        assert set(features_r.keys()) == set(i+['File_31'])
        assert all(times_r['File_31'] == times_added)
        assert (features_r['File_31'] == features_added).all()

    # def test_concat(self):
    #     """Concatenate new data to an existing item in an existing file."""
    #     i, t, f = generate.full(1, self.dim, 4, items_root='File')
    #     h5f.write(self.filename, 'group', i, t, f)
    #     assert ['File_0'] == i

    #     # concatenate new item to an existing one
    #     features_added = np.zeros(shape=(2, self.dim))
    #     times_added = np.linspace(0, 2, 2)
    #     h5f.write(self.filename, 'group', ['File_0'],
    #               [times_added], [features_added])

    #     # read it
    #     times_r, features_r = h5f.read(self.filename, 'group')
    #     assert list(times_r.keys()) == i == ['File_0']
    #     assert list(features_r.keys()) == i == ['File_0']

    #     for ii, ff in enumerate(i):
    #         assert all(times_r[ff] == t[ii])
    #         assert (features_r[ff] == f[ii]).all()

    #     print(times_r['File_0'], '\n'*2, t[-1], '\n'*2, times_added)
    #     assert times_r['File_0'] == np.concatenate([t[-1], times_added])
    #     assert (features_r['File_0'] == np.concatenate([f[-1],
    #                                                     features_added],
    #                                                    axis=0) ).all()
