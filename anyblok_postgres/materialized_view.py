# This file is a part of the AnyBlok / postgres api project
#
#    Copyright (C) 2018 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
from anyblok.model.factory import ViewFactory
from anyblok.model.exceptions import ViewException
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.schema import DDLElement
from sqlalchemy.sql import table
from sqlalchemy import event
from sqlalchemy.orm import Query
from anyblok.common import anyblok_column_prefix


class CreateMaterializedView(DDLElement):
    def __init__(self, name, selectable, with_data=None):
        self.name = name
        self.selectable = selectable
        self.with_data = with_data


@compiles(CreateMaterializedView)
def compile(element, compiler, **kw):
    with_data = ''
    if element.with_data is True:
        with_data = ' WITH DATA'
    elif element.with_data is False:
        with_data = ' WITH NO DATA'

    return 'CREATE MATERIALIZED VIEW IF NOT EXISTS %s AS %s%s' % (
        element.name,
        compiler.sql_compiler.process(element.selectable, literal_binds=True),
        with_data
    )


class Refresh:

    @classmethod
    def refresh_materialized_view(cls, concurrently=False):
        lnft = cls.anyblok.loaded_namespaces_first_step
        tablename = lnft[cls.__registry_name__]['__tablename__']
        cls.anyblok.flush()
        _con = 'CONCURRENTLY ' if concurrently else ''
        cls.anyblok.execute('REFRESH MATERIALIZED VIEW ' + _con + tablename)


class MaterializedViewFactory(ViewFactory):

    def insert_core_bases(self, bases, properties):
        bases.append(Refresh)
        super(MaterializedViewFactory, self).insert_core_bases(
            bases, properties)

    def apply_view(self, base, properties):
        """ Transform the sqlmodel to view model

        :param base: Model cls
        :param properties: properties of the model
        :exception: MigrationException
        :exception: ViewException
        """
        tablename = base.__tablename__
        if hasattr(base, '__view__'):
            view = base.__view__
        elif tablename in self.registry.loaded_views:
            view = self.registry.loaded_views[tablename]
        else:
            if not hasattr(base, 'sqlalchemy_view_declaration'):
                raise ViewException(
                    "%r.'sqlalchemy_view_declaration' is required to "
                    "define the query to apply of the view" % base)

            view = table(tablename)

            self.registry.loaded_views[tablename] = view
            selectable = getattr(base, 'sqlalchemy_view_declaration')()

            if isinstance(selectable, Query):
                selectable = selectable.subquery()

            for c in selectable.subquery().columns:
                col = c._make_proxy(view)[1]
                view._columns.replace(col)

            metadata = self.registry.declarativebase.metadata
            event.listen(metadata, 'after_create', CreateMaterializedView(
                view, selectable, getattr(base, 'with_data', None)))

        pks = [col for col in properties['loaded_columns']
               if getattr(getattr(base, anyblok_column_prefix + col),
                          'primary_key', False)]

        if not pks:
            raise ViewException(
                "%r have any primary key defined" % base)

        pks = [getattr(view.c, x) for x in pks]
        mapper_properties = self.get_mapper_properties(base, view, properties)
        base.anyblok.declarativebase.registry.map_imperatively(
            base, view, primary_key=pks, properties=mapper_properties)
        setattr(base, '__view__', view)
