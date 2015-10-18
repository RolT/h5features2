"""Provides the Items class to the h5features module.

@author Mathieu Bernard <mmathieubernardd@gmail.com>

"""

from h5py import special_dtype
from h5features2.dataset.dataset import Dataset

class Items(Dataset):
    """This class manages items in h5features files."""

    def __init__(self, data, name='items'):
        """Initializes an Items dataset from raw data.

        Parameters:

        data : list of str
            A list of item names (e.g. files from which the features
            where extracted). Each name of the list must be unique.

        name : str (default is 'items')
            The name of this items dataset.

        Raise:

        IOError if data is empty or if one or more names are not
        unique in the list.

        """
        if not data:
            raise IOError('data is empty')

        if not len(set(data)) == len(data):
            raise IOError('all items must have different names.')

        self.data = data
        self.name = name

    def create(self, group, items_by_chunk):
        """Creates an items subgroup in the given group.

        Parameters
        ----------

        group : HDF5 Group
            The group where to create the 'files' subgroup.

        items_by_chunk : int
            Number of items stored in a single data chunk.

        """
        str_dtype = special_dtype(vlen=str)
        group.create_dataset(self.name, (0,), dtype=str_dtype,
                             chunks=(items_by_chunk,), maxshape=(None,))


    def is_compatible(self, group):
        items_in_group = group[self.name][...]
        return (not set(items_in_group).intersection(self.data)
                or self.continue_last_item(group))

    def continue_last_item(self, group):
        """Return True if we can continue writing to the last item in the group.

        This method compares the shared items between the given group
        and self. Given these shared items, three cases can occur:

        - No shared items: return False

        - There is only one shared item. It is first in self and last
        in group : return True. In that case the first item in self is
        erased.

        - Otherwise raise IOError.

        """

        items_in_group = group[self.name][...]

        # Shared items between self and the group
        # TODO Really usefull to compute the whole intersection ?
        shared = set(items_in_group).intersection(self.data)
        nshared = len(shared)

        if nshared == 0:
            return False
        elif nshared == 1:
            # Assert the last item in group is the first item in self.
            if not self.data[0] == items_in_group[-1]:
                raise IOError('data can be added only at the end'
                              'of the last written file.')
            self.data = self.data[1:]
            return True
        else:
            # print(items_in_group, '\n'*3, self.data)
            raise IOError('groups cannot have more than one shared items.')

    def write(self, group):
        """Write stored items to the given HDF5 group.

        We assume that self.create() has been called.

        """
        # The HDF5 group where to write data
        items_group = group[self.name]

        nitems = items_group.shape[0]
        items_group.resize((nitems + len(self.data),))
        items_group[nitems:] = self.data