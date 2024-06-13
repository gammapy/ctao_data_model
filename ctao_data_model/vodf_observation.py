# Licensed under a 3-clause BSD style license - see LICENSE.rst
from gammapy.data import EventList, GTI, Observation, ObservationMetaData, ObservationFilter, Observations

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
    def aeff(self):
        if self.n_groups == 1:
            return self._irf_groups[0].aeff
        else:
            raise ValueError(f"Observation contains more than one IRF group.")

    @property
    def edisp(self):
        if self.n_groups == 1:
            return self._irf_groups[0].edisp
        else:
            raise ValueError(f"Observation contains more than one IRF group.")

    @property
    def psf(self):
        if self.n_groups==1:
            return self._irf_groups[0].psf
        else:
            raise ValueError(f"Observation contains more than one IRF group.")

    @property
    def events(self):
        """Event list of the observation as an `~gammapy.data.EventList`."""
        events = self._events  # Removed events filtering for now
        return events

    @property
    def n_groups(self):
        return len(self._irf_groups)

    @property
    def event_types(self):
        return self._irf_groups.event_types

    @property
    def pointing(self):
        return self._pointing

    def _irf_group_filter(self, idx):
        # TODO: for now assume only one interval.
        gti = self._irf_groups[idx].gti
        time_filter = [gti.time_start[0], gti.time_stop[0]]
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


    def split(self, event_types=None):
        """Split VODFObservation into a list of simple Observation elements."""
        observations = Observations()
        event_types = self.event_types if event_types is None else event_types
        event_types = [event_types] if not isinstance(event_types, list) else event_types

        for irf_group in self._irf_groups:
            if irf_group.event_type in event_types:
                # What to do with obsid. Now this is an int

                # Note there might be several GTIs
                time_filter = [irf_group.gti.time_start[0], irf_group.gti.time_stop[0]]

                # Need a filter based on specific value
                event_type_band = (irf_group.event_type-0.5, irf_group.event_type+0.5)
                event_filter = {'type': 'custom', 'opts': dict(parameter='event_type', band=event_type_band)}

                filter = ObservationFilter(time_filter=time_filter, event_filters=[event_filter])

                obs = Observation(self.obs_id,
                        aeff=irf_group.aeff,
                        edisp=irf_group.edisp,
                        psf=irf_group.psf,
                        bkg=irf_group.bkg,
                        gti=irf_group.gti,
                        rad_max=irf_group.rad_max,
                        pointing=self._pointing,
                        events=self.events,
                        obs_filter=filter,
                        )
                observations.append(obs)

        return observations


