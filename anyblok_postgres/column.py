# This file is a part of the AnyBlok / Postgres api project
#
#    Copyright (C) 2018 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
from sqlalchemy.dialects.postgresql import JSONB
from anyblok.column import Column

json_null = object()


class Jsonb(Column):
    """Postgres JSONB column

    ::

        from anyblok.declarations import Declarations
        from anyblok_postgres.column import Jsonb


        @Declarations.register(Declarations.Model)
        class Test:

            x = Jsonb()

    """
    sqlalchemy_type = JSONB(none_as_null=True)
