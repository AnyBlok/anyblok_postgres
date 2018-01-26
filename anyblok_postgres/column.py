# This file is a part of the AnyBlok / Postgres api project
#
#    Copyright (C) 2018 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
from sqlalchemy.dialects.postgresql import JSONB, OID
from sqlalchemy import select
from anyblok.column import Column
from anyblok.common import anyblok_column_prefix

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


class LargeObject(Column):
    """Postgres JSONB column

    ::

        from anyblok.declarations import Declarations
        from anyblok_postgres.column import LargeObject


        @Declarations.register(Declarations.Model)
        class Test:

            x = LargeObject()

        -----------------------------

        test = Test.insert()
        test.x = hugefile
        test.x  # get the huge file

    """
    sqlalchemy_type = OID

    def wrap_setter_column(self, fieldname):
        attr_name = anyblok_column_prefix + fieldname

        def setter_column(model_self, value):
            action_todos = set()
            if fieldname in model_self.loaded_columns:
                action_todos = model_self.registry.expire_attributes.get(
                    model_self.__registry_name__, {}).get(fieldname, set())

            self.expire_related_attribute(model_self, action_todos)
            pks = model_self.to_primary_keys()
            table = model_self.__table__.c
            dbfname = self.db_column_name or fieldname
            query = select([getattr(table, dbfname)])
            query = query.where(
                *[getattr(table, x) == y for x, y in pks.items()])
            oldvalue = model_self.registry.execute(query).fetchone()
            if oldvalue:
                oldvalue = oldvalue[0]

            value = self.setter_format_value(
                value, oldvalue, model_self.registry)
            res = setattr(model_self, attr_name, value)
            self.expire_related_attribute(model_self, action_todos)
            return res

        return setter_column

    def setter_format_value(self, value, oldvalue, registry):
        if value is not None:
            cursor = registry.session.connection().connection.cursor()
            lobj = cursor.connection.lobject(oldvalue or 0, 'wb')
            lobj.write(value)
            value = lobj.oid

        return value

    def wrap_getter_column(self, fieldname):
        """Return a default getter for the field

        :param fieldname: name of the field
        """
        attr_name = anyblok_column_prefix + fieldname

        def getter_column(model_self):
            return self.getter_format_value(
                getattr(model_self, attr_name),
                model_self.registry
            )

        return getter_column

    def getter_format_value(self, value, registry):
        if value is not None:
            cursor = registry.session.connection().connection.cursor()
            lobj = cursor.connection.lobject(value, 'rb')
            return lobj.read()
