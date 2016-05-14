import logging
import sys

import time
from chimera.core.exceptions import ChimeraException
from chimera.interfaces.filterwheel import InvalidFilterPositionException
from chimera.instruments.filterwheel import FilterWheelBase
from chimera.core.lock import lock

log = logging.getLogger(__name__)

if sys.platform == "win32":
    sys.coinit_flags = 0
    from win32com.client import Dispatch
    from pywintypes import com_error
else:
    log.warning("Not on Windows. ASCOM Filter Wheel will not work.")


class ASCOMFilterWheel(FilterWheelBase):
    __config__ = {"ascom_id": "ASCOM.Simulator.FilterWheel",
                  "ascom_setup": False,
                  "max_connection_attempts": 3,
                  "change_timeout": 60}     # seconds

    def __init__(self):
        FilterWheelBase.__init__(self)

        self._n_attempts = 0

    def __start__(self):

        self.open()

    def open(self):
        '''
        Connects to ASCOM server
        :return:
        '''
        self.log.debug('Starting ASCOM filter wheel at %s' % self["ascom_id"])
        self._ascom = Dispatch(self["ascom_id"])
        if self["ascom_setup"]:
            self._ascom.SetupDialog()
        try:
            self._ascom.Connected = True
        except com_error:
            if self._n_attempts > self["max_connection_attempts"]:
                raise ChimeraException("Could not configure filterwheel after %d tries" % self._n_attempts)
            self._n_attempts += 1
            self._ascom.SetupDialog()
            self.open()
        try:
            self["filter_wheel_model"] = "ASCOM: %s" % self._ascom.Description
        except AttributeError:
            self["filter_wheel_model"] = "ASCOM filter wheel %s" % self["ascom_id"]

    def getFilter(self):
        return self._getFilterName(self._ascom.Position)

    @lock
    def setFilter(self, filter):
        filterName = str(filter).upper()

        if filterName not in self.getFilters():
            raise InvalidFilterPositionException("Invalid filter %s." % filter)

        self.filterChange(filter, self.getFilter())

        self._ascom.Position = self._getFilterPosition(filter)

        t0 = time.time()
        while time.time() - t0 < self["change_timeout"]:
            if self.getFilter() == filterName:
                return True
        return False
