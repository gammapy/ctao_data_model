import collections
from astropy.time import Time
import astropy.units as u
from gammapy.irf import IRF, load_irf_dict_from_file

class IRFGroup:
    """Group different IRF components that represent the response in a given time range."""
    def __init__(self, aeff=None, psf=None, edisp=None, bkg=None, rad_max=None, time_range=None):
        """
        Parameters
        ----------
        aeff : `~gammapy.irf.EffectiveAreaTable2D`, optional
            Effective area. Default is None.
        edisp : `~gammapy.irf.EnergyDispersion2D`, optional
            Energy dispersion. Default is None.
        psf : `~gammapy.irf.PSF3D`, optional
            Point spread function. Default is None.
        bkg : `~gammapy.irf.Background3D`, optional
            Background rate model. Default is None.
        rad_max : `~gammapy.irf.RadMax2D`, optional
            Only for point-like IRFs: RAD_MAX table (energy dependent RAD_MAX)
            For a fixed RAD_MAX, create a RadMax2D with a single bin. Default is None.
        """
        self.aeff = aeff
        self.psf = psf
        self.bkg = bkg
        self.edisp = edisp
        self.rad_max = rad_max
        self.time_range = time_range

class IRFGroups(collections.abc.MutableSequence):
    """Sequence of IRF groups."""
    def __init__(self, irf_groups=None):
        self._irf_groups = []

        if irf_groups is None:
            irf_groups = []
        if isinstance(irf_groups, IRFGroup):
            irf_groups = [irf_groups]

        for grp in irf_groups:
            self.append(grp)

    def __getitem__(self, key):
        if isinstance(key, slice):
            return self.__class__(self._irf_groups[key])
        else:
            return self._irf_groups[key]

    def __delitem__(self, key):
        del self._irf_groups[self.index(key)]

    def __setitem__(self, key, irf_group):
        self._irf_groups[self.index(key)] = irf_group

    def insert(self, idx, irf_group):
        self._irf_groups.insert(idx, irf_group)

    def __len__(self):
        return len(self._irf_groups)

    @property
    def time_ranges(self):
        """List all IRFGroup time intervals."""
        return [irf_grp.time_range for irf_grp in self._irf_groups]

    def get_irf_group(self, time):
        """Retrieve IRFGroup valid at `~astropy.time.Time` time."""
        # TODO: Better use GTIs instead of list of times
        for grp in self._irf_groups:
            range = time - grp.time_range
            if range[0].to('d')>0 and range[1].to('d')<0:
                return grp
        return None