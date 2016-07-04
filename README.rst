chimera-aagcloudwatcher plugin
==============================

.. image:: https://github.com/astroufsc/chimera-stellarium/raw/master/docs/images/img1.png

Chimera plugin for `AAG cloud watcher`_ safety cloud detector. This plugin uses the COM+ methods available by the AAG Cloud watcher software on Windows to comunicate with the device. A future implementation can be done to connect to the device over serial. Nevertheless, the usage of Windows software haves the advantage of the easy calibration access.

A dump of all COM+ methods accessible for developers can be found on docs directory and a brief explanation can be found on Cloud Watcher documentation: http://lunatico.es/aagcw/enhelp/scr/Inter-program%20Communications/41-InterprogramCommunicationProtocol.htm

Usage
-----

In the same computer were the AAG software is running, install this plugin and configure it accordingly to the example below.

* Download link for the AAG software: http://www.lunatico.es/ourproducts/aag-cloud-watcher/moreinfo/software-downloads.html

* Help for the AAG software: http://lunatico.es/aagcw/enhelp/

Installation
------------

::

    pip install -U git+https://github.com/astroufsc/chimera-aagcloudwatcher.git


Configuration Example
---------------------

To configure this plugin, simply add this configuration to the ``chimera.config`` file:

::

    weatherstations:
      - name: aag
        type: AAGCloudWatcherCOM


Tested versions
---------------

This plugin was tested on AAG cloud watcher software version 7.20.100


Contact
-------

For more information, contact us on chimera's discussion list:
https://groups.google.com/forum/#!forum/chimera-discuss

Bug reports and patches are welcome and can be sent over our GitHub page:
https://github.com/astroufsc/chimera-aagcloudwatcher/

.. _AAG cloud watcher: http://www.lunatico.es/ourproducts/aag-cloud-watcher.html