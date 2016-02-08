# ! /usr/bin/env python
# -*- coding: iso-8859-1 -*-

# chimera - observatory automation system
# Copyright (C) 2007  P. Henrique Silva <henrique@astro.ufsc.br>

# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA
# 02110-1301, USA.

import sys
import threading
import logging
import time

from chimera.core.exceptions import ChimeraException
from chimera.util.coord import Coord
from chimera.util.position import Position, Epoch
from chimera.instruments.telescope import TelescopeBase
from chimera.interfaces.telescope import TelescopeStatus, TelescopePier, TelescopePierSide

log = logging.getLogger(__name__)

if sys.platform == "win32":
    sys.coinit_flags = 0  # TODO: check why this?

    from win32com.client import Dispatch
    from pywintypes import com_error

else:
    log.warning("Not on Windows. ASCOM Telescope will not work.")


def com(func):
    """
    Wrapper decorator used to handle COM objects errors.
    Every method that use COM method should be decorated.
    """

    def com_wrapper(*args, **kwargs):

        try:
            return func(*args, **kwargs)
        except com_error, e:
            raise ChimeraException(str(e))

    return com_wrapper


class ASCOMTelescope(TelescopeBase, TelescopePier):
    __config__ = {"ascom_id": "ASCOM.Simulator.Telescope"}

    def __init__(self):
        TelescopeBase.__init__(self)

        self._abort = threading.Event()

        self._ascom = None
        self._ascom = None
        self._idle_time = 0.2
        self._target = None
        self._isFanning = None
        self._isOpen = None

    @com
    def __start__(self):
        self.open()
        super(ASCOMTelescope, self).__start__()
        return True

    @com
    def __stop__(self):
        self.close()
        super(ASCOMTelescope, self).__stop__()
        return True

    @com
    def open(self):
        try:
            self._ascom = Dispatch(self['ascom_id'])
            self._ascom.Connected = True
        except com_error:
            self.log.error(
                "Couldn't instantiate ASCOM %d COM objects." % self["ascom_id"])
            return False

        return self.unpark()

    @com
    def close(self):
        return True
        # try:
        #     # self._ascom.Disconnect()
        #     # self._ascom.DisconnectTelescope()
        #     # self._ascom.Disconnect()
        #     self._ascom.Quit()
        # except com_error:
        #     self.log.error("Couldn't disconnect to ASCOM.")
        #     return False

    @com
    def getRa(self):
        return Coord.fromH(self._ascom.RightAscension)

    @com
    def getDec(self):
        return Coord.fromD(self._ascom.Declination)

    @com
    def getAz(self):
        return Coord.fromD(self._ascom.Azimuth)

    @com
    def getAlt(self):
        return Coord.fromD(self._ascom.Altitude)

    @com
    def getPositionRaDec(self):
        return Position.fromRaDec(self._ascom.RightAscension, self._ascom.Declination, epoch=Epoch.NOW)

    @com
    def getPositionAltAz(self):
        return Position.fromAltAz(self._ascom.Altitude, self._ascom.Azimuth)

    @com
    def getTargetRaDec(self):
        if not self._target:
            return self.getPositionRaDec()
        return self._target

    @com
    def slewToRaDec(self, position):

        if self.isSlewing():
            self.log.error('Telescope is Slewing. Slew aborted.')
            return False

        self._target = position
        self._abort.clear()

        if not self._ascom.CanSlew:
            raise ChimeraException('Cannot Slew: Telescope does not slew.')
        elif self._ascom.AtPark:
            raise ChimeraException('Cannot Slew: Telescope is Parked')
        elif not self._ascom.Tracking:
            raise ChimeraException('Cannot Slew: Telescope is Not Tracking')

        if self._ascom.CanSlew and not self._ascom.AtPark and self._ascom.Tracking:

            self.slewBegin(position)

            # At least for ASA telescopes, (ra, dec) should be in NOW epoch, not J2000.
            position = position.toEpoch(Epoch.NOW)
            self.log.info("Telescope %s slewing to ra %3.2f and dec %3.2f" % (self['ascom_id'],
                                                                              position.ra.H, position.dec.D))
            self._ascom.SlewToCoordinates(position.ra.H, position.dec.D)

            status = TelescopeStatus.OK

            while self._ascom.Slewing:

                # [ABORT POINT]
                if self._abort.isSet():
                    status = TelescopeStatus.ABORTED
                    break

                time.sleep(self._idle_time)

            self.slewComplete(self.getPositionRaDec(), status)
            print 'Slew Complete'
            self.log.info("Slew Complete.")

        else:
            self.log.info("Can't slew.")
            return False

        #
        #     # except com_error:
        #     #     raise PositionOutsideLimitsException("Position outside limits.")
        # except:
        #     print 'FIXME:'
        #     NotImplementedError()

        return True

    @com
    def slewToAltAz(self, position):

        if self.isSlewing():
            self.log.error('Telescope is Slewing. Slew aborted.')
            return False

        self._target = position
        self._abort.clear()

        if not self._ascom.CanSlew:
            raise ChimeraException('Cannot Slew: Telescope does not slew.')
        elif self._ascom.AtPark:
            raise ChimeraException('Cannot Slew: Telescope is Parked')
        # elif not self._ascom.Tracking:  FIXME: Telescope should or should not be tracking to move?
        #     raise ChimeraException('Cannot Slew: Telescope is Not Tracking')

        self.slewBegin(position)
        self.log.info("Telescope %s slewing to alt %3.2f and az %3.2f" % (self['ascom_id'], position.alt.D, position.az.D))
        self._ascom.SlewToAltAz(position.az.D, position.alt.D)

        status = TelescopeStatus.OK

        while self._ascom.Slewing:

            # [ABORT POINT]
            if self._abort.isSet():
                status = TelescopeStatus.ABORTED
                break

            time.sleep(self._idle_time)

        self.slewComplete(self.getPositionRaDec(), status)
        print 'Slew Complete'
        self.log.info("Slew Complete.")

        #
        #     # except com_error:
        #     #     raise PositionOutsideLimitsException("Position outside limits.")
        # except:
        #     print 'FIXME:'
        #     NotImplementedError()

        return True

        # if self.isSlewing():
        #     return False
        #
        # self._target = position
        #
        # # try:
        # self._ascom.Asynchronous = 1
        # self.slewBegin((position.ra, position.dec))
        # self._ascom.SlewToAltAz(position.alt.D, position.az.D)
        #
        # while not self._ascom.IsSlewComplete:
        #     time.sleep(self._idle_time)
        #
        # self.slewComplete(self.getPositionRaDec())
        #
        # # except com_error:
        # #     raise PositionOutsideLimitsException("Position outside limits.")
        #
        # return True

    @com
    def abortSlew(self):
        if self.isSlewing():
            self._abort.set()
            time.sleep(self._idle_time)
            self._ascom.AbortSlew()
            return True

        return False

    @com
    def isSlewing(self):
        return self._ascom.Slewing

    @com
    def isTracking(self):
        return self._ascom.Tracking == 1

    @com
    def park(self):
        self.stopTracking()
        self._ascom.Park()

    @com
    def unpark(self):
        if self._ascom.AtPark:  # Is parked?
            self._ascom.Unpark()
            try:
                self._ascom.FindHome()
            except:
                log.info('Telescope %s does not have FindHome implemented. Skipping...' % self['ascom_id'])
        self.startTracking()

    @com
    def isParked(self):
        return self._ascom.AtPark

    @com
    def startTracking(self):
        if self._ascom.CanSetTracking:
            self._ascom.Tracking = True
        else:
            return False

    @com
    def stopTracking(self):
        if self._ascom.CanSetTracking:
            self._ascom.Tracking = False
        else:
            return False

    def isFanning(self):
        return self._isFanning

    @com
    def startFan(self):
        # FIXME: Can be checked by SupportedActions method on ASCOM
        if self['ascom_id'] in ['AstrooptikServer.Telescope']:
            if self.isFanning():
                return True
            self._ascom.Action('Telescope:StartFans')
            self.log.debug('Starting telescope fans...')
            return True
        else:
            raise NotImplementedError()

    @com
    def stopFan(self):
        # FIXME: Can be checked by SupportedActions method on ASCOM
        if self['ascom_id'] in ['AstrooptikServer.Telescope']:
            if not self.isFanning():
                return True
            self.log.debug('Stopping telescope fans...')
            self._ascom.Action('Telescope:StopFans')
            return True
        else:
            raise NotImplementedError()

    def isOpen(self):
        return self._isOpen

    def getPierSide(self):
        if self._ascom.SideOfPier == -1:
            return TelescopePierSide.UNKNOWN
        elif self._ascom.SideOfPier == 0:
            return TelescopePierSide.EAST
        elif self._ascom.SideOfPier == 1:
            return TelescopePierSide.WEST

    @com
    def openCover(self):
        # FIXME: Can be checked by SupportedActions method on ASCOM
        if self['ascom_id'] in ['AstrooptikServer.Telescope']:
            if self.isOpen():
                return True
            self.log.debug('Opening telescope cover...')
            self._ascom.Action('Telescope:OpenCover')
            return True
        else:
            raise NotImplementedError()

    @com
    def closeCover(self):
        # FIXME: Can be checked by SupportedActions method on ASCOM
        if self['ascom_id'] in ['AstrooptikServer.Telescope']:
            if not self.isOpen():
                return True
            self.log.debug('Closing telescope cover...')
            self._ascom.Action('Telescope:CloseCover')
            return True
        else:
            raise NotImplementedError()

            # @com
            # def moveEast(self, offset, slewRate=None):
            #     self._ascom.Asynchronous = 0
            #     self._ascom.Jog(offset.AS / 60.0, 'East')
            #     self._ascom.Asynchronous = 1
            #
            # @com
            # def moveWest(self, offset, slewRate=None):
            #     self._ascom.Asynchronous = 0
            #     self._ascom.Jog(offset.AS / 60.0, 'West')
            #     self._ascom.Asynchronous = 1
            #
            # @com
            # def moveNorth(self, offset, slewRate=None):
            #     self._ascom.Asynchronous = 0
            #     self._ascom.Jog(offset.AS / 60.0, 'North')
            #     self._ascom.Asynchronous = 1
            #
            # @com
            # def moveSouth(self, offset, slewRate=None):
            #     self._ascom.Asynchronous = 0
            #     self._ascom.Jog(offset.AS / 60.0, 'South')
            #     self._ascom.Asynchronous = 1
            #

    def getMetadata(self, request):
        md = super(ASCOMTelescope, self).getMetadata(request)
        md.append(('PIERSIDE', self.getPierSide().__str__(), 'Side-of-pier'))
        return md
