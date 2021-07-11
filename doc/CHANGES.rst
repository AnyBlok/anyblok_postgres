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

1.0.0 (UNRELEASED)
------------------

* Adapted to **AnyBlok >= 1.1**

0.2.2 (2021-07-11)
------------------

* Freezed version of **AnyBlok < 1.1.0**

0.2.2 (2019-10-31)
------------------

* Fixed, the dependencies of pyscopg is removed

0.2.1 (2019-09-16)
------------------

* Removed **python 3.4** capability
* Removed extra dependencies, let at the user, the choice of the driver to use

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
