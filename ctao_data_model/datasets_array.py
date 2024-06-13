# Licensed under a 3-clause BSD style license - see LICENSE.rst
import numpy as np
from gammapy.maps import MapAxes, MapAxis
from gammapy.datasets import Datasets

class DatasetsArray:
    """A dataset container with a MapAxes.

       All datasets should have the same geometry.
    """
    def __init__(self, datasets, axis):
        # here we should test that all datasets have the same geometry for all data members.

        # ideally this should be immutable too
        self._datasets = Datasets(datasets)
        self._axes = MapAxes([axis])

    @property
    def axis(self):
        return self._axes[0]

    @property
    def datasets(self):
        return self._datasets

    @classmethod
    def create(cls, reference_dataset, axis):
        """Create array of datasets copying the reference dataset along the provided MapAxes."""
        datasets = []
        for center in axis.center:
            name = f"{reference_dataset.name}_{axis.name}_{center:g}"
            datasets.append(reference_dataset.copy(name=name))
        return cls(datasets, axis)

    def get_by_coord(self, coord):
        """Get datasets by their coord in the array."""
        # we assume only one entry
        idx = int(self._axes.coord_to_idx(coord)[0][0])
        return self.datasets[idx]



