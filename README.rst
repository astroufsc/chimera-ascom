chimera_template plugin
=======================

This is an template plugin for the chimera observatory control system
https://github.com/astroufsc/chimera .

Usage
-----

Rename chimera_template for your plugin name. It is important that the plugin
name must start with chimera\_ to be found by chimera. Instruments and
controllers must follow the
`standard chimera_(plugin_name)/(instruments|controllers)/(plugin).py`

The class inside `(plugin).py` should be named Plugin (with CamelCase letters).

For more info: https://github.com/astroufsc/chimera/blob/master/docs/site/chimerafordevs.rst#chimera-objects