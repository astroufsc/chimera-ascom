# Based on http://www.ascom-standards.org/Help/Developer/html/AllMembers_T_ASCOM_DriverAccess_Camera.htm

__author__ = 'william'

import sys
import logging
import datetime as dt

import numpy as np
from chimera.core.lock import lock
from chimera.instruments.camera import CameraBase
from chimera.core.exceptions import ChimeraException
from chimera.interfaces.camera import CameraFeature, CCD, ReadoutMode, CameraStatus, Shutter

log = logging.getLogger(__name__)

if sys.platform == "win32":
    sys.coinit_flags = 0
    from win32com.client import Dispatch
    from pywintypes import com_error
else:
    log.warning("Not on Windows. ASCOM CAMERA will not work.")


class ASCOMCamera(CameraBase):
    __config__ = {"ascom_id": 'ASCOM.Simulator.Camera',
                  "ascom_setup": False,
                  "max_connection_attempts": 3,
                  "ccd_width": None,
                  "ccd_height": None}

    def __init__(self):
        CameraBase.__init__(self)

        self._n_attempts = 0

    def __start__(self):

        self.open()

        # self._ascom_supported_actions = list(self._ascom.SupportedActions)
        try:
            self._ascom_min_exptime = self._ascom.ExposureMin
        except AttributeError:
            self._ascom_min_exptime = 0
        try:
            self._ascom_max_exptime = self._ascom.ExposureMax
        except AttributeError:
            self._ascom_max_exptime = None

        # self.__cooling = False
        #
        # self.__lastFilter = self._getFilterName(0)
        # self.__temperature = 20.0
        # self.__setpoint = 0
        # self.__lastFrameStart = 0
        # self.__isFanning = False

        # my internal CCD code
        self._MY_CCD = 1 << 1
        self._MY_ADC = 1 << 2
        self._MY_READOUT_MODE = 1 << 3

        self._ccds = {self._MY_CCD: CCD.IMAGING}

        self._adcs = {"12 bits": self._MY_ADC}

        self._binnings = {"1x1": 0,
                          "2x2": 1,
                          "3x3": 2,
                          "9x9": 3}

        self._binning_factors = {"1x1": 1,
                                 "2x2": 2,
                                 "3x3": 3,
                                 "9x9": 9}

        self._supports = {CameraFeature.TEMPERATURE_CONTROL: self._ascom.CanSetCCDTemperature,
                          CameraFeature.PROGRAMMABLE_GAIN: False,
                          CameraFeature.PROGRAMMABLE_OVERSCAN: False,
                          CameraFeature.PROGRAMMABLE_FAN: False,  # 'SetFanSpeed' in self._ascom_supported_actions,
                          CameraFeature.PROGRAMMABLE_LEDS: False,
                          CameraFeature.PROGRAMMABLE_BIAS_LEVEL: False}

        try:
            self._ascom_readout_modes = list(self._ascom.ReadoutModes)
        except AttributeError:
            self._ascom_readout_modes = [0]
        if len(self._ascom_readout_modes) != 1:  # if camera haves more than 1 readout mode, throw an exception
            self.close()
            raise NotImplementedError("Multiple ReadOut modes not implemented.")

        self._pixelWidth = self._ascom.PixelSizeX
        self._pixelHeight = self._ascom.PixelSizeY
        self["ccd_width"] = self._ascom.CameraXSize
        self["ccd_height"] = self._ascom.CameraYSize
        self._readoutModes = {self._MY_CCD: {}}
        i_mode_tot = 0
        for i_mode in range(len(self._ascom_readout_modes)):
            for binning, i_mode in self._binnings.iteritems():
                readoutMode = ReadoutMode()
                vbin, hbin = [int(v) for v in binning.split('x')]
                readoutMode.mode = i_mode
                readoutMode.gain = self._ascom.ElectronsPerADU
                readoutMode.width = self["ccd_width"] / hbin
                readoutMode.height = self["ccd_height"] / vbin
                readoutMode.pixelWidth = self._pixelWidth * hbin
                readoutMode.pixelHeight = self._pixelHeight * vbin
                self._readoutModes[self._MY_CCD].update({i_mode: readoutMode})
                i_mode_tot += 1

        try:
            self["camera_model"] = "ASCOM: %s" % self._ascom.Description
            self["ccd_model"] = "ASCOM: %s" % self._ascom.Description
        except AttributeError:
            self["camera_model"] = "ASCOM camera %s" % self["ascom_id"]

        self.setHz(2)

    def __stop__(self):
        self.close()

    def close(self):
        self._ascom.Connected = False

    def open(self):
        '''
        Connects to ASCOM server
        :return:
        '''
        self.log.debug('Starting ASCOM camera at %s' % self["ascom_id"])
        self._ascom = Dispatch(self["ascom_id"])
        if self["ascom_setup"]:
            self._ascom.SetupDialog()
        try:
            self._ascom.Connected = True
        except com_error:
            if self._n_attempts > self["max_connection_attempts"]:
                raise ChimeraException("Could not configure camera after %d tries" % self._n_attempts)
            self._n_attempts += 1
            self._ascom.SetupDialog()
            self.open()

    def _expose(self, request):
        """
        .. method:: expose(request=None, **kwargs)

            Start an exposure based upon the specified image request or
            create a new image request from kwargs

            :keyword request: ImageRequest object
            :type request: ImageRequest
        """
        self.exposeBegin(request)

        if self._ascom_max_exptime is not None:
            if request["exptime"] > self._ascom_max_exptime:
                # self.log.error("Exposure time greater than max: %3.2f" % self._ascom_max_exptime)
                raise InvalidExposureTime("Exposure time greater than max: %3.2f" % self._ascom_max_exptime)

        if request['shutter'] == Shutter.OPEN:
            light = True
        elif request['shutter'] == Shutter.CLOSE:
            light = False
        elif request['shutter'] == Shutter.LEAVE_AS_IS:
            raise ChimeraException('Not supported to leave as is shutter.')

        # Can only take images of exptime > minexptime.
        if request["exptime"] < self._ascom_min_exptime:
            request["exptime"] = self._ascom_min_exptime
            self.log.error("Exposure time less than the minimum %f, changing to the minimum." % request["exptime"])

        mode, binning, top, left, width, height = self._getReadoutModeInfo(request["binning"], request["window"])
        # Binning
        vbin, hbin = [int(v) for v in binning.split('x')]
        self._ascom.BinX = vbin
        self._ascom.BinY = hbin

        # Subframing
        self._ascom.StartX = left
        self._ascom.StartY = top

        self._ascom.NumX = width
        self._ascom.NumY = height

        # Start Exposure...
        self._ascom.StartExposure(request["exptime"], light)

        status = CameraStatus.OK

        while 5 > self._ascom.CameraState > 0:
            # [ABORT POINT]
            if self.abort.isSet():
                self._ascom.StopExposure()
                status = CameraStatus.ABORTED
                break

        self.exposeComplete(request, status)

    def _readout(self, request):
        self.readoutBegin(request)

        pix = np.array(self._ascom.ImageArray)

        (mode, binning, top, left, width, height) = self._getReadoutModeInfo(request["binning"], request["window"])

        proxy = self._saveImage(request, pix, {
            "frame_start_time": dt.datetime.strptime(self._ascom.LastExposureStartTime, "%Y-%m-%dT%H:%M:%S"),
            "frame_temperature": self.getTemperature(),
            "binning_factor": self._binning_factors[binning]})

        # [ABORT POINT]
        if self.abort.isSet():
            self.readoutComplete(None, CameraStatus.ABORTED)
            return None

        self.readoutComplete(proxy, CameraStatus.OK)
        return proxy

    @lock
    def startFan(self, rate=None):
        if not self.supports(CameraFeature.PROGRAMMABLE_FAN):
            return False
        self._ascom.Action('SetFanSpeed', 3)
        return True

    @lock
    def stopFan(self):
        if not self.supports(CameraFeature.PROGRAMMABLE_FAN):
            return False
        self._ascom.Action('SetFanSpeed', 0)
        return True

    def isFanning(self):
        if not self.supports(CameraFeature.PROGRAMMABLE_FAN):
            return False
        return bool(self._ascom.Action('GetFanSpeed', 1))

    def getCCDs(self):
        return self._ccds

    def getCurrentCCD(self):
        return self._MY_CCD

    def getBinnings(self):
        return self._binnings

    def getADCs(self):
        return self._adcs

    def getPhysicalSize(self):
        return self["ccd_width"], self["ccd_height"]

    def getPixelSize(self):
        return self._pixelWidth, self._pixelHeight

    def getOverscanSize(self, ccd=None):
        return 0, 0  # FIXME

    def getReadoutModes(self):
        return self._readoutModes

    def supports(self, feature=None):
        return self._supports[feature]

    @lock
    def startCooling(self, setpoint):
        if not self.supports(CameraFeature.TEMPERATURE_CONTROL):
            return False
        self._ascom.CoolerOn = True
        self._ascom.SetCCDTemperature = setpoint
        return True

    @lock
    def stopCooling(self):
        if not self.supports(CameraFeature.TEMPERATURE_CONTROL):
            return False
        self._ascom.CoolerOn = False

    def isCooling(self):
        if not self.supports(CameraFeature.TEMPERATURE_CONTROL):
            return False
        return self._ascom.CoolerOn

    @lock
    def getTemperature(self):
        if not self.supports(CameraFeature.TEMPERATURE_CONTROL):
            return False
        return self._ascom.CCDTemperature

    def getSetPoint(self):
        return self._ascom.SetCCDTemperature

        # TODO: Add getMetadata() method with gain in e-/ADU.


class InvalidExposureTime(ChimeraException):
    pass
