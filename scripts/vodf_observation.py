from gammapy.data import EventList, GTI, Observation, ObservationMetaData, ObservationFilter

class VODFObservation:
    """In-memory observation.

    Parameters
    ----------
    obs_id : int, optional
        Observation id. Default is None
    obs_info : dict, optional
        Observation info dict. Default is None.
    irf_groups : `~gammapy.irf.IRFGroups`
        Groups of IRFs valid for this observation.
    gti : `~gammapy.data.GTI`, optional
        Table with GTI start and stop time. Default is None.
    events : `~gammapy.data.EventList`, optional
        Event list. Default is None.
    pointing : `~gammapy.data.FixedPointingInfo`, optional
        Pointing information. Default is None.
    location : `~astropy.coordinates.EarthLocation`, optional
        Earth location of the observatory. Default is None.
    """
    def __init__(
        self,
        obs_id=None,
        meta=None,
        gti=None,
        irf_groups=None,
        events=None,
        pointing=None,
        location=None,
    ):
        self.obs_id = obs_id
        self._irf_groups = irf_groups
        self._gti = gti   # technically this should be the union of SOIs
        self._events = events
        self._pointing = pointing
        self._location = location  # this is part of the meta or is it data?
        self._meta = meta

    @property
    def meta(self):
        """Return metadata container."""
        if self._meta is None and self.events:
            self._meta = ObservationMetaData.from_header(self.events.table.meta)
        return self._meta

    @property
    def events(self):
        """Event list of the observation as an `~gammapy.data.EventList`."""
        events = self._events  # Removed events filtering for now
        return events

    def _irf_group_filter(self, idx):
        time_filter = self._irf_groups[idx].time_range
        return ObservationFilter(time_filter=time_filter)

    def select_time(self, time_interval):
        """Select a time interval of the observation.

        Parameters
        ----------
        time_interval : `astropy.time.Time`
            Start and stop time of the selected time interval.
            For now, we only support a single time interval.

        Returns
        -------
        new_obs : `~gammapy.data.Observation`
            A new observation instance of the specified time interval.
        """
        new_obs_filter = self.obs_filter.copy()
        new_obs_filter.time_filter = time_interval
        obs = copy.deepcopy(self)
        obs.obs_filter = new_obs_filter
        return obs

    def events_in_irf_group(self, idx):
        filter = self._irf_group_filter(idx)
        return filter.filter_events(self.events)
