.. This file is a part of the AnyBlok / POstgres project
..
..    Copyright (C) 2018 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
..    Copyright (C) 2018 Georges Racinet <gracinet@anybox.fr>
..    Copyright (C) 2019 Jean-Sebastien SUZANNE <js.suzanne@gmail.fr>
..
.. This Source Code Form is subject to the terms of the Mozilla Public License,
.. v. 2.0. If a copy of the MPL was not distributed with this file,You can
.. obtain one at http://mozilla.org/MPL/2.0/.

.. contents::

CHANGELOG
=========

0.2.0 (2019-06-25)
------------------

* Added columns for built-in range types: PR #2 by @gracinet
* Added **Materialized view** factory: PR #1
* Fixed when the model have more than one primary key,
  the query to get the old value was wrong

0.1.0 (2018-01-26)
------------------

* Added **Jsonb** column
* Added **LargeObject** column
