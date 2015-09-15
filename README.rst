chimera-ascom plugin
====================

A chimera_ plugin for ASCOM_ telescope control standard.

Usage
-----

Install chimera_ on your computer, and then, this package. Edit the configuration like the example below matching the
``ascom_id`` of your device to the id on the ASCOM manager. It current implements telescope (``type: ASCOMTelescope``),
focuser (``type: ASCOMFocuser``), camera (``type: ASCOMCamera``) and filter wheel camera (``type: ASCOMFilterWheel``).

Installation
------------

Besides chimera, ``chimera-ascom`` depends of ``win32com`` and ``pywintypes`` Python modules. It runs only on *Windows*
operating systems.

::

    pip install -U git+https://github.com/astroufsc/chimera-ascom.git


Configuration Example
---------------------

* ASCOM Simulator

::

    telescope:
        name: tel_sim
        type: ASCOMTelescope
        ascom_id: ASCOM.Simulator.Telescope

    focuser:
        name: foc_sim
        type: ASCOMFocuser
        ascom_id: FocusSim.Focuser

    camera:
        name: cam_sim
        type: ASCOMCamera
        ascom_id: ASCOM.Simulator.Camera

    filterwheel:
        name: fwheel_sim
        type: ASCOMFilterWheel
        ascom_id: ASCOM.Simulator.FilterWheel


* `ASA DDM160`_ with M2 focuser

::

    telescope:
        name: ASA_DDM160
        type: ASCOMTelescope
        ascom_id: AstrooptikServer.Telescope

    focuser:
        name: ASA_focuser
        type: ASCOMFocuser
        ascom_id: ACCServer.Focuser

* `Apogee Alta U-16M`_ camera with `FW50-9R`_ filter wheel

::

    camera:
        name: apogee
        type: ASCOMCamera
        ascom_id: ASCOM.Apogee.Camera

    filterwheel:
        name: apogee
        type: ASCOMFilterWheel
        ascom_id: ASCOM.Apogee.FilterWheel
        filters: F1 F2 F3 F4 F5 F6 F7 F8 F9

Tested Hardware
---------------

This plugin was tested on:

* `Astrosysteme Austria`_ Telescope model `ASA DDM160`_ with M2 focuser.

* `Apogee Alta U-16M`_ camera with `FW50-9R`_ filter wheel

Contact
-------

For more information, contact us on chimera's discussion list:
https://groups.google.com/forum/#!forum/chimera-discuss

Bug reports and patches are welcome and can be sent over our GitHub page:
https://github.com/astroufsc/chimera-ascom/


.. _chimera: https://www.github.com/astroufsc/chimera/
.. _Astrosysteme Austria: http://www.astrosysteme.at
.. _ASA DDM160: http://www.astrosysteme.at/eng/mount_ddm160.html
.. _ASCOM: http://www.ascom-standards.org/
.. _Apogee Alta U-16M: http://www.andor.com/scientific-cameras/apogee-camera-range/alta-ccd-series
.. _FW50-9R: http://www.ccd.com/pdf/FW50.pdf
