# Based on http://www.ascom-standards.org/Help/Developer/html/AllMembers_T_ASCOM_DriverAccess_Focuser.htm
import logging
import sys

from chimera.core.lock import lock
from chimera.interfaces.focuser import FocuserFeature, InvalidFocusPositionException, FocuserAxis
from chimera.instruments.focuser import FocuserBase

log = logging.getLogger(__name__)

if sys.platform == "win32":
    sys.coinit_flags = 0
    from win32com.client import Dispatch
    from pywintypes import com_error
else:
    log.warning("Not on Windows. ASCOM FOCUSER will not work.")


class ASCOMFocuser(FocuserBase):
    __config__ = {"ascom_id": 'FocusSim.Focuser'}

    def __init__(self):
        FocuserBase.__init__(self)


    def __start__(self):
        self.open()

        self._supports = {FocuserFeature.TEMPERATURE_COMPENSATION: self._ascom.TempCompAvailable,
                          FocuserFeature.POSITION_FEEDBACK: True,  # TODO: Check FEEDBACK
                          FocuserFeature.ENCODER: self._ascom.Absolute,
                          FocuserFeature.CONTROLLABLE_X: False,
                          FocuserFeature.CONTROLLABLE_Y: False,
                          FocuserFeature.CONTROLLABLE_Z: True,
                          FocuserFeature.CONTROLLABLE_U: False,
                          FocuserFeature.CONTROLLABLE_V: False,
                          FocuserFeature.CONTROLLABLE_W: False}

        self._position = self.getPosition()
        self["focuser_model"] = 'ASCOM standard focuser id %s' % self['ascom_id']
        self["model"] = self["focuser_model"]

    @lock
    def moveIn(self, n, axis=FocuserAxis.Z):
        # Check if axis is on the permitted axis list
        self._checkAxis(axis)

        target = self.getPosition() - n

        if self._inRange(target):
            self._setPosition(target)
        else:
            raise InvalidFocusPositionException("%d is outside focuser boundaries." % target)

    @lock
    def moveOut(self, n, axis=FocuserAxis.Z):
        # Check if axis is on the permitted axis list
        self._checkAxis(axis)

        target = self.getPosition() + n

        if self._inRange(target):
            self._setPosition(target)
        else:
            raise InvalidFocusPositionException("%d is outside focuser boundaries." % target)

    @lock
    def moveTo(self, position, axis=FocuserAxis.Z):
        # Check if axis is on the permitted axis list
        self._checkAxis(axis)

        if self._inRange(position):
            self._setPosition(position)
        else:
            raise InvalidFocusPositionException("%d is outside focuser boundaries." % int(position))

    @lock
    def getPosition(self, axis=FocuserAxis.Z):
        # Check if axis is on the permitted axis list
        self._checkAxis(axis)

        return int(self._ascom.Position)

    def getRange(self, axis=FocuserAxis.Z):
        # Check if axis is on the permitted axis list
        self._checkAxis(axis)

        return 0, int(self._ascom.MaxStep)

    def _setPosition(self, n):
        self.log.info("Changing focuser to %s" % n)
        self._ascom.Move(n)
        while self._ascom.IsMoving:
            pass  # FIXME: Add a timeout? Add an ABORT?!
        self._position = self._ascom.Position

    def _inRange(self, n):
        min_pos, max_pos = self.getRange()
        return min_pos <= n <= max_pos

    def open(self):
        try:
            self._ascom = Dispatch(self['ascom_id'])
            self._ascom.Link = True
        except com_error:
            self.log.error(
                "Couldn't instantiate ASCOM %d COM objects." % self["telescope_id"])
            return False

    def getTemperature(self):
        # FIXME: Raises an exception if ambient temperature is not available
        return self._ascom.Temperature
