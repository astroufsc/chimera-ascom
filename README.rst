chimera_ascom plugin
====================

This is a `chimera`_ plugin for ASCOM_ telescope control standard.

.. _chimera: https://github.com/astroufsc/chimera

.. _ASCOM: http://www.ascom-standards.org/

Usage
-----

Install chimera_ on your computer, and then, this package. Edit the configuration like the example below matching the
`ascom_id` of your device to the id on the ASCOM manager. It current implements only telescope (`type: ASCOMTelescope`)
and focuser (`type: ASCOMFocuser`).

.. _chimera: https://www.github.com/astroufsc/chimera/

Installation
------------

Besides `chimera`, `chimera_ascom` depends of `win32com` and `pywintypes` Python modules. It runs only on *Windows*
operating systems.

::

    pip install -U git+https://github.com/astroufsc/chimera_ascom.git


Configuration Example
---------------------

* ASCOM Simulator

::

    telescope:
        name: tel_sim
        type: ASCOMTelescope
        ascom_id: ScopeSim.Telescope

    focuser:
        name: foc_sim
        type: ASCOMFocuser
        ascom_id: FocusSim.Focuser


* ASA DDM160 with M2 focuser

::

    telescope:
        name: ASA_DDM160
        type: ASCOMTelescope
        ascom_id: AstrooptikServer.Telescope

    focuser:
        name: ASA_focuser
        type: ASCOMFocuser
        ascom_id: ACCServer.Focuser


Tested Hardware
---------------

This plugin was tested on these hardware:

* `Astrosysteme Austria`_ Telescope model `ASA DDM160`_ with M2 focuser.

.. _Astrosysteme Austria: http://www.astrosysteme.at
.. _ASA DDM160: http://www.astrosysteme.at/eng/mount_ddm160.html


Contact
-------

For more information, contact us on chimera's discussion list:
https://groups.google.com/forum/#!forum/chimera-discuss

Bug reports and patches are welcome and can be sent over our GitHub page:
https://github.com/astroufsc/chimera_ascom/