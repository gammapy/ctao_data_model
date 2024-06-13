# Licensed under a 3-clause BSD style license - see LICENSE.rst
import collections
from gammapy.utils.fits import LazyFitsData
from gammapy.data.data_store import REQUIRED_IRFS, ALL_HDUS, ALL_IRFS, MissingRequiredHDU

class IRFGroup:
    """Group different IRF components that represent the response in a given time range."""
    aeff = LazyFitsData(cache=False)
    edisp = LazyFitsData(cache=False)
    psf = LazyFitsData(cache=False)
    bkg = LazyFitsData(cache=False)
    gti = LazyFitsData(cache=False)

    def __init__(self, aeff=None, psf=None, edisp=None, bkg=None, rad_max=None, gti=None, event_type=None, is_pointlike=False):
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
        gti : `~gammapy.data.GTI`
            The validity time interval. Default is None.
        is_pointlike : bool
            Is the IRF group designed for pointlike analysis. Default is False
        """
        self.aeff = aeff
        self.psf = psf
        self.bkg = bkg
        self.edisp = edisp
        self.rad_max = rad_max
        self.gti = gti
        self.is_pointlike = is_pointlike
        self.event_type = event_type

    @classmethod
    def from_hdu_index_table(cls, hdu_table, obs_id, required_irf="full-enclosure"):
        """Access a given IRFGroup from a HDU index table.

        Parameters
        ----------
        hdu_table : `~gammapy.data.`
            Input index table
        obs_id : int
            Observation ID.
        required_irf : list of str or str, optional
            The list can include the following options:

            * `"gti"` :  Good time intervals
            * `"aeff"` : Effective area
            * `"bkg"` : Background
            * `"edisp"` : Energy dispersion
            * `"psf"` : Point Spread Function
            * `"rad_max"` : Maximal radius

            Alternatively single string can be used as shortcut:

            * `"full-enclosure"` : includes `["gti", "aeff", "edisp", "psf", "bkg"]`
            * `"point-like"` : includes `["gti", "aeff", "edisp"]`

            Default is `"full-enclosure"`.
        require_events : bool, optional
            Require events and gti table or not. Default is True.

        Returns
        -------
        irf_group : `~cato_data_model.IRFGroup`
            IRF container.
        """
        if obs_id not in hdu_table["OBS_ID"]:
            raise ValueError(f"OBS_ID = {obs_id} not in HDU index table.")

        kwargs = {"obs_id": int(obs_id)}

        # check for the "short forms"
        if isinstance(required_irf, str):
            required_irf = REQUIRED_IRFS[required_irf]

        if not set(required_irf).issubset(ALL_IRFS):
            difference = set(required_irf).difference(ALL_IRFS)
            raise ValueError(
                f"{difference} is not a valid hdu key. Choose from: {ALL_IRFS}"
            )

        required_hdus = {"gti"}.union(required_irf)

        missing_hdus = []
        kwargs_irf = {}
        for hdu in ALL_HDUS:
            hdu_location = hdu_table.hdu_location(
                obs_id=obs_id,
                hdu_type=hdu,
                warn_missing=False,
            )
            if hdu_location is not None:
                if hdu in ALL_IRFS or hdu == "gti":
                    kwargs_irf[hdu] = hdu_location
                else:
                    kwargs[hdu] = hdu_location
            elif hdu in required_hdus:
                missing_hdus.append(hdu)

        if len(missing_hdus) > 0:
            raise MissingRequiredHDU(
                f"Required HDUs {missing_hdus} not found in observation {obs_id}"
            )
        print(kwargs_irf)
        return IRFGroup(**kwargs_irf)


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
        return [irf_grp.gti for irf_grp in self._irf_groups]

    @property
    def event_types(self):
        """List all IRFGroup time intervals."""
        return list(set([irf_grp.event_type  for irf_grp in self._irf_groups]))


    def get_irf_group(self, time):
        """Retrieve IRFGroup valid at `~astropy.time.Time` time."""
        # TODO: Better use GTIs instead of list of times
        for grp in self._irf_groups:
            range = time - grp.time_range
            if range[0].to('d')>0 and range[1].to('d')<0:
                return grp
        return None