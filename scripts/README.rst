Scripts directory
-----------------

Store here the scripts that your plugin will provide. Consider to use the ``chimera-(nameofscript)`` standard.

Don't forget to put your script on ``setup.py`` by adding it on the ``scripts`` context. E. g.:

::

    setup(
        ...
        scripts = ['scripts/chimera-template']
        ...
        )


