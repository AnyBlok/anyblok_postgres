.. This file is a part of the AnyBlok / POstgres project
..
..    Copyright (C) 2018 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
..
.. This Source Code Form is subject to the terms of the Mozilla Public License,
.. v. 2.0. If a copy of the MPL was not distributed with this file,You can
.. obtain one at http://mozilla.org/MPL/2.0/.

.. contents::

Fields
======

This package adds some fields that are specific to PostgreSQL.

Columns
-------

.. automodule:: anyblok_postgres.column

**Jsonb**
`````````

.. autoclass:: Jsonb
    :noindex:
    :members:
    :show-inheritance:

**LargeObject**
```````````````

.. autoclass:: LargeObject
    :noindex:
    :members:
    :show-inheritance:

**Ranges**
``````````

Since version 9.2, PostgreSQL supports a flexible range types system,
with a few predefined ones, that can be used within AnyBlok.

.. seealso:: Range Types in `PostgreSQL documentation
             <https://www.postgresql.org/docs/current/rangetypes.html>`_

.. autoclass:: Int4Range
    :noindex:
    :show-inheritance:

.. autoclass:: Int8Range
    :noindex:
    :show-inheritance:

.. autoclass:: NumRange
    :noindex:
    :show-inheritance:

.. autoclass:: DateRange
    :noindex:
    :show-inheritance:

.. autoclass:: TsRange
    :noindex:
    :show-inheritance:

.. autoclass:: TsTzRange
    :noindex:
    :show-inheritance:
