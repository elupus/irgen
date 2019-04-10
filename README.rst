************************************
Generation/Conversion of IR commands
************************************
This module support conversion and generation of IR formats

Status
======

.. image:: https://travis-ci.org/elupus/irgen.svg?branch=master
    :target: https://travis-ci.org/elupus/irgen

.. image:: https://coveralls.io/repos/github/elupus/irgen/badge.svg?branch=master
    :target: https://coveralls.io/github/elupus/irgen?branch=master


Input Formats
=============

Nec
---
Several NEC variants are supported:
nec1,nec1-y1,nec1-y2,nec1-y3,nec1-f16,nec2,nec2-y1,
nec2-y2,nec2-y3,nec2-f16,necx1,necx1-y1,necx1-y2,
necx1-y3,necx1-f16,necx2,necx2-y1,necx2-y2,necx2-y3,necx2-f16

.. code-block:: bash

    irgen -i nec1 -d 16 0 0 -o raw


Philips RC-5 Protocol
---------------------

.. code-block:: bash

    irgen -i rc5 -d 16 -1 0 -o raw


Philips RC-6 Protocol
---------------------

.. code-block:: bash

    irgen -i rc6 -d 16 -1 0 -o raw


Raw
---
Raw times, positive meaning on negative meaning off.

.. code-block:: bash

    irgen -i raw -d +889.0 -889.0 +1778.0 -1778.0 +1778.0 -889.0 +889.0 -889.0 +889.0 -889.0 +889.0 -889.0 +889.0 -889.0 +889.0 -889.0 +889.0 -889.0 +889.0 -889.0 +889.0 -1778.0 +889.0 -88900.0 -o pronto

Broadlink
---------

.. code-block:: bash

    irgen -i broadlink_base64 -d JgAaAB0dOjo6HR0dHR0dHR0dHR0dHR0dHTodAAtnDQUAAAAAAAAAAAAAAAA= -o pronto


Output Formats
==============

Raw
---
Raw times, positive meaning on negative meaning off.

Pronto
------
Pronto IR format

Broadlink
---------
Broadlink binary format for their IR transmitters.
Two variants ``broadlink`` and ``broadlink_base64`` with
the latter being base64 encoded.

.. code-block:: bash

    irgen -i rc5 -d 16 -1 0 -o broadlink
    irgen -i rc5 -d 16 -1 0 -o broadlink_base64


Console
=======

The module contains a commandline utility to test and request data from
called ``irgen``.

Library
=======

The module contains a library with functions for generation of ir codes
