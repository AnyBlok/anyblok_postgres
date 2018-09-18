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
# from sqlalchemy import Table, MetaData
from sqlalchemy.sql import table
from sqlalchemy.orm import Query, mapper
from anyblok.common import anyblok_column_prefix


class CreateMaterializedView(DDLElement):
    def __init__(self, name, selectable):
        self.name = name
        self.selectable = selectable


class DropMaterializedView(DDLElement):
    def __init__(self, name):
        self.name = name


@compiles(CreateMaterializedView)
def compile(element, compiler, **kw):
    return 'CREATE MATERIALIZED VIEW %s AS %s' % (
        element.name,
        compiler.sql_compiler.process(element.selectable, literal_binds=True))


@compiles(DropMaterializedView)
def compile_drop_materialized_view(element, compiler, **kw):
    return "DROP MATERIALIZED VIEW IF EXISTS %s" % element.name


class Refresh:

    @classmethod
    def refresh_materialized_view(cls, concurrently=False):
        lnft = cls.registry.loaded_namespaces_first_step
        tablename = lnft[cls.__registry_name__]['__tablename__']
        cls.registry.flush()
        _con = 'CONCURRENTLY ' if concurrently else ''
        cls.registry.execute('REFRESH MATERIALIZED VIEW ' + _con + tablename)


class MaterializedViewFactory(ViewFactory):

    def insert_core_bases(self, bases, properties):
        bases.append(Refresh)
        super(MaterializedViewFactory, self).insert_core_bases(
            bases, properties)

    # def build_model(self, modelname, bases, properties):
    #     base = type(modelname, tuple(bases), {})
    #     self.apply_view(base, properties)
    #     return type(modelname, (base, self.registry.declarativebase),
    #                 properties)

    # def apply_view(self, base, properties):
    #     """ Transform the sqlmodel to view model

    #     :param base: Model cls
    #     :param properties: properties of the model
    #     :exception: MigrationException
    #     :exception: ViewException
    #     """
    #     tablename = properties.pop('__tablename__')
    #     if hasattr(base, '__materialized_view__'):
    #         view = base.__materialized_view__
    #     elif tablename in self.registry.loaded_views:
    #         view = self.registry.loaded_views[tablename]
    #     else:
    #         if not hasattr(base, 'sqlalchemy_view_declaration'):
    #             raise ViewException(
    #                 "%r.'sqlalchemy_view_declaration' is required to "
    #                 "define the query to apply of the view" % base)

    #         columns = []
    #         for c in properties['loaded_columns']:
    #             if c in properties['hybrid_property_columns']:
    #                 properties[c] = properties.pop(anyblok_column_prefix + c)
    #                 properties['hybrid_property_columns'].remove(c)

    #             columns.append(properties[c])

    #         selectable = getattr(base, 'sqlalchemy_view_declaration')()

    #         if isinstance(selectable, Query):
    #             selectable = selectable.subquery()

    #         view = Table(tablename, MetaData(),
    #                      *columns, *base.define_table_args())

    #         self.registry.loaded_views[tablename] = view
    #         DropMaterializedView(tablename).execute_at(
    #             'before-create', self.registry.declarativebase.metadata)
    #         CreateMaterializedView(tablename, selectable).execute_at(
    #             'after-create', self.registry.declarativebase.metadata)
    #         DropMaterializedView(tablename).execute_at(
    #             'before-drop', self.registry.declarativebase.metadata)

    #     properties['__materialized_view__'] = view
    #     properties['__table__'] = view

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

            for c in selectable.c:
                c._make_proxy(view)

            DropMaterializedView(tablename).execute_at(
                'before-create', self.registry.declarativebase.metadata)
            CreateMaterializedView(tablename, selectable).execute_at(
                'after-create', self.registry.declarativebase.metadata)
            DropMaterializedView(tablename).execute_at(
                'before-drop', self.registry.declarativebase.metadata)

        pks = [col for col in properties['loaded_columns']
               if getattr(getattr(base, anyblok_column_prefix + col),
                          'primary_key', False)]

        if not pks:
            raise ViewException(
                "%r have any primary key defined" % base)

        pks = [getattr(view.c, x) for x in pks]

        mapper_properties = self.get_mapper_properties(base, view, properties)
        setattr(base, '__view__', view)
        __mapper__ = mapper(
            base, view, primary_key=pks, properties=mapper_properties)
        setattr(base, '__mapper__', __mapper__)
