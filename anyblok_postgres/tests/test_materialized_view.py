# This file is a part of the AnyBlok / postgres api project
#
#    Copyright (C) 2018 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#    Copyright (C) 2019 Jean-Sebastien SUZANNE <js.suzanne@gmail.com>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
import pytest
from anyblok_postgres.materialized_view import MaterializedViewFactory
from anyblok.model.exceptions import ViewException
from anyblok import Declarations
from sqlalchemy.sql import select, expression, union
from sqlalchemy.exc import OperationalError
from anyblok.column import Integer, String
from anyblok.relationship import Many2One
from anyblok.config import get_url
from sqlalchemy import create_engine
from anyblok.tests.conftest import init_registry_with_bloks
from contextlib import contextmanager

register = Declarations.register
Model = Declarations.Model


def simple_view():

    @register(Model)
    class T1:
        id = Integer(primary_key=True)
        code = String()
        val = Integer()

    @register(Model)
    class T2:
        id = Integer(primary_key=True)
        code = String()
        val = Integer()

    @register(Model, factory=MaterializedViewFactory)
    class TestView:
        code = String(primary_key=True)
        val1 = Integer()
        val2 = Integer()

        @classmethod
        def sqlalchemy_view_declaration(cls):
            T1 = cls.anyblok.T1
            T2 = cls.anyblok.T2
            query = select([T1.code.label('code'),
                            T1.val.label('val1'),
                            T2.val.label('val2')])
            return query.where(T1.code == T2.code)


@pytest.fixture(scope="class")
def registry_simple_view(request, bloks_loaded):
    registry = init_registry_with_bloks(
        [], simple_view)
    request.addfinalizer(registry.close)
    registry.T1.insert(code='test1', val=1)
    registry.T2.insert(code='test1', val=2)
    registry.T1.insert(code='test2', val=3)
    registry.T2.insert(code='test2', val=4)
    return registry


class TestSimpleView:

    @pytest.fixture(autouse=True)
    def transact(self, request, registry_simple_view):
        transaction = registry_simple_view.begin_nested()
        request.addfinalizer(transaction.rollback)

    def test_has_a_mapper(self, registry_simple_view):
        registry = registry_simple_view
        assert registry.TestView.__mapper__ is not None

    def test_ok(self, registry_simple_view):
        registry = registry_simple_view
        TestView = registry.TestView
        TestView.refresh_materialized_view()
        v1 = TestView.query().filter(TestView.code == 'test1').first()
        v2 = TestView.query().filter(TestView.code == 'test2').first()
        assert v1.val1 == 1
        assert v1.val2 == 2
        assert v2.val1 == 3
        assert v2.val2 == 4
        registry.T1.insert(code='test3', val=5)
        registry.T2.insert(code='test3', val=6)
        v3 = TestView.query().filter(TestView.code == 'test3').one_or_none()
        assert v3 is None
        TestView.refresh_materialized_view()
        v3 = TestView.query().filter(TestView.code == 'test3').one_or_none()
        assert v3
        assert v3.val1 == 5
        assert v3.val2 == 6

    def test_view_update_method(self, registry_simple_view):
        registry = registry_simple_view
        registry.TestView.refresh_materialized_view()
        with pytest.raises(AttributeError):
            registry.TestView.execute_sql_statement(
                registry.TestView.update_sql_statement())

    def test_view_delete_method(self, registry_simple_view):
        registry = registry_simple_view
        registry.TestView.refresh_materialized_view()
        with pytest.raises(AttributeError):
            registry.TestView.execute_sql_statement(
                registry.TestView.delete_sql_statement())


def view_with_relationship():

    @register(Model)
    class Rs:
        id = Integer(primary_key=True)

    @register(Model)
    class T1:
        id = Integer(primary_key=True)
        code = String()
        val = Integer()
        rs_id = Integer(foreign_key=Model.Rs.use('id'))
        rs = Many2One(model=Model.Rs, column_names='rs_id')

    @register(Model)
    class T2:
        id = Integer(primary_key=True)
        code = String()
        val = Integer()

    @register(Model, factory=MaterializedViewFactory)
    class TestView:
        code = String(primary_key=True)
        val1 = Integer()
        val2 = Integer()
        rs = Many2One(model=Model.Rs)

        @classmethod
        def sqlalchemy_view_declaration(cls):
            T1 = cls.anyblok.T1
            T2 = cls.anyblok.T2
            query = select([T1.code.label('code'),
                            T1.val.label('val1'),
                            T1.rs_id.label('rs_id'),
                            T2.val.label('val2')])
            return query.where(T1.code == T2.code)


@pytest.fixture(scope="class")
def registry_view_with_relationship(request, bloks_loaded):
    registry = init_registry_with_bloks(
        [], view_with_relationship)
    rs1 = registry.Rs.insert(id=1)
    rs2 = registry.Rs.insert(id=2)
    registry.T1.insert(code='test1', val=1, rs=rs1)
    registry.T2.insert(code='test1', val=2)
    registry.T1.insert(code='test2', val=3, rs=rs2)
    registry.T2.insert(code='test2', val=4)
    yield registry
    registry.close()


class TestViewWithRelationShip:

    @pytest.fixture(autouse=True)
    def transact(self, request, registry_view_with_relationship):
        transaction = registry_view_with_relationship.begin_nested()
        request.addfinalizer(transaction.rollback)
        return

    def test_ok(self, registry_view_with_relationship):
        registry = registry_view_with_relationship
        TestView = registry.TestView
        TestView.refresh_materialized_view()
        v1 = TestView.query().filter(TestView.code == 'test1').first()
        v2 = TestView.query().filter(TestView.code == 'test2').first()
        assert v1.val1 == 1
        assert v1.val2 == 2
        assert v1.rs.id == 1
        assert v2.val1 == 3
        assert v2.val2 == 4
        assert v2.rs.id == 2


def view_with_relationship_on_self():

    @register(Model)
    class T1:
        id = Integer(primary_key=True)
        code = String()
        val = Integer()
        parent = Many2One(model='Model.T1')

    @register(Model)
    class T2:
        id = Integer(primary_key=True)
        code = String()
        val = Integer()

    @register(Model, factory=MaterializedViewFactory)
    class TestView:
        code = String(primary_key=True)
        val1 = Integer()
        val2 = Integer()
        parent = Many2One(model='Model.TestView')

        @classmethod
        def sqlalchemy_view_declaration(cls):
            T1 = cls.anyblok.T1
            TP = cls.anyblok.T1.aliased()
            T2 = cls.anyblok.T2
            subquery = union(
                select([
                    T1.code.label('code'),
                    TP.code.label('parent_code')]
                ).where(T1.parent_id == TP.id),
                select([
                    T1.code.label('code'),
                    expression.literal_column("null as parent_code")
                ]).where(T1.parent_id.is_(None))
            ).alias()
            query = select([T1.code.label('code'),
                            T1.val.label('val1'),
                            T2.val.label('val2'),
                            subquery.c.parent_code.label('parent_code')])
            query = query.where(subquery.c.code == T1.code)
            query = query.where(subquery.c.code == T2.code)
            return query


def view_with_relationship_on_self_2():

    @register(Model)
    class T1:
        id = Integer(primary_key=True)
        code = String()
        val = Integer()
        parent = Many2One(model='Model.T1')

    @register(Model)
    class T2:
        id = Integer(primary_key=True)
        code = String()
        val = Integer()

    @register(Model, factory=MaterializedViewFactory)
    class TestView:
        code = String(primary_key=True)
        val1 = Integer(primary_key=True)
        val2 = Integer()
        parent = Many2One(model='Model.TestView')

        @classmethod
        def sqlalchemy_view_declaration(cls):
            T1 = cls.anyblok.T1
            TP = cls.anyblok.T1.aliased()
            T2 = cls.anyblok.T2
            subquery = union(
                select([
                    T1.code.label('code'),
                    TP.id.label('parent_val1'),
                    TP.code.label('parent_code')
                ]).where(T1.parent_id == TP.id),
                select([
                    T1.code.label('code'),
                    expression.literal_column("null as parent_val1"),
                    expression.literal_column("null as parent_code")
                ]).where(T1.parent_id.is_(None))
            ).alias()
            query = select([T1.code.label('code'),
                            T1.val.label('val1'),
                            T2.val.label('val2'),
                            subquery.c.parent_val1.label('parent_val1'),
                            subquery.c.parent_code.label('parent_code')])
            query = query.where(subquery.c.code == T1.code)
            query = query.where(subquery.c.code == T2.code)
            return query


@pytest.fixture(
    scope="class",
    params=[
        view_with_relationship_on_self,
        view_with_relationship_on_self_2,
    ]
)
def registry_view_with_relationship_on_self(request, bloks_loaded):
    registry = init_registry_with_bloks(
        [], request.param)
    request.addfinalizer(registry.close)
    parent = registry.T1.insert(code='test1', val=1)
    registry.T2.insert(code='test1', val=2)
    registry.T1.insert(code='test2', val=3, parent=parent)
    registry.T2.insert(code='test2', val=4)
    return registry


class TestViewWithRelationShipOnSelf:

    @pytest.fixture(autouse=True)
    def transact(self, request, registry_view_with_relationship_on_self):
        transaction = registry_view_with_relationship_on_self.begin_nested()
        request.addfinalizer(transaction.rollback)
        return

    def test_ok(self, registry_view_with_relationship_on_self):
        registry = registry_view_with_relationship_on_self
        TestView = registry.TestView
        TestView.refresh_materialized_view()
        v1 = TestView.query().filter(TestView.code == 'test1').first()
        v2 = TestView.query().filter(TestView.code == 'test2').first()
        assert v1.val1 == 1
        assert v1.val2 == 2
        assert v1.parent is None
        assert v2.val1 == 3
        assert v2.val2 == 4
        assert v2.parent.code == v1.code


def simple_view_with_same_table_by_declaration_model():

    @register(Model)
    class T1:
        id = Integer(primary_key=True)
        code = String()
        val = Integer()

    @register(Model)
    class T2:
        id = Integer(primary_key=True)
        code = String()
        val = Integer()

    @register(Model, factory=MaterializedViewFactory)
    class TestView:
        code = String(primary_key=True)
        val1 = Integer()
        val2 = Integer()

        @classmethod
        def sqlalchemy_view_declaration(cls):
            T1 = cls.anyblok.T1
            T2 = cls.anyblok.T2
            query = select([T1.code.label('code'),
                            T1.val.label('val1'),
                            T2.val.label('val2')])
            return query.where(T1.code == T2.code)

    @register(Model, factory=MaterializedViewFactory, tablename=Model.TestView)
    class TestView2:
        code = String(primary_key=True)
        val1 = Integer()
        val2 = Integer()


def simple_view_with_same_table_by_name():

    @register(Model)
    class T1:
        id = Integer(primary_key=True)
        code = String()
        val = Integer()

    @register(Model)
    class T2:
        id = Integer(primary_key=True)
        code = String()
        val = Integer()

    @register(Model, factory=MaterializedViewFactory)
    class TestView:
        code = String(primary_key=True)
        val1 = Integer()
        val2 = Integer()

        @classmethod
        def sqlalchemy_view_declaration(cls):
            T1 = cls.anyblok.T1
            T2 = cls.anyblok.T2
            query = select([T1.code.label('code'),
                            T1.val.label('val1'),
                            T2.val.label('val2')])
            return query.where(T1.code == T2.code)

    @register(Model, factory=MaterializedViewFactory, tablename='testview')
    class TestView2:
        code = String(primary_key=True)
        val1 = Integer()
        val2 = Integer()


def simple_view_with_same_table_by_inherit():

    @register(Model)
    class T1:
        id = Integer(primary_key=True)
        code = String()
        val = Integer()

    @register(Model)
    class T2:
        id = Integer(primary_key=True)
        code = String()
        val = Integer()

    @register(Model, factory=MaterializedViewFactory)
    class TestView:
        code = String(primary_key=True)
        val1 = Integer()
        val2 = Integer()

        @classmethod
        def sqlalchemy_view_declaration(cls):
            T1 = cls.anyblok.T1
            T2 = cls.anyblok.T2
            query = select([T1.code.label('code'),
                            T1.val.label('val1'),
                            T2.val.label('val2')])
            return query.where(T1.code == T2.code)

    @register(Model, factory=MaterializedViewFactory)
    class TestView2(Model.TestView):
        code = String(primary_key=True)
        val1 = Integer()
        val2 = Integer()


@pytest.fixture(
    scope="class",
    params=[
        simple_view_with_same_table_by_declaration_model,
        simple_view_with_same_table_by_name,
        simple_view_with_same_table_by_inherit,
    ]
)
def registry_view_with_inheritance(request, bloks_loaded):
    registry = init_registry_with_bloks(
        [], request.param)
    request.addfinalizer(registry.close)
    registry.T1.insert(code='test1', val=1)
    registry.T2.insert(code='test1', val=2)
    registry.T1.insert(code='test2', val=3)
    registry.T2.insert(code='test2', val=4)
    return registry


class TestViewWithInheritance:

    @pytest.fixture(autouse=True)
    def transact(self, request, registry_view_with_inheritance):
        transaction = registry_view_with_inheritance.begin_nested()
        request.addfinalizer(transaction.rollback)
        return

    def test_ok(self, registry_view_with_inheritance):
        registry = registry_view_with_inheritance
        TestView = registry.TestView
        TestView2 = registry.TestView2
        registry.TestView.refresh_materialized_view()
        assert registry.TestView.__view__ == registry.TestView2.__view__
        v1 = TestView.query().filter(TestView.code == 'test1').first()
        v2 = TestView.query().filter(TestView2.code == 'test1').first()
        assert v1.val1 == v2.val1
        assert v1.val2 == v2.val2


def simple_view_without_primary_key():

    @register(Model)
    class T1:
        id = Integer(primary_key=True)
        code = String()
        val = Integer()

    @register(Model)
    class T2:
        id = Integer(primary_key=True)
        code = String()
        val = Integer()

    @register(Model, factory=MaterializedViewFactory)
    class TestView:
        code = String()
        val1 = Integer()
        val2 = Integer()

        @classmethod
        def sqlalchemy_view_declaration(cls):
            T1 = cls.anyblok.T1
            T2 = cls.anyblok.T2
            query = select([T1.code.label('code'),
                            T1.val.label('val1'),
                            T1.val.label('val2')])
            return query.where(T1.code == T2.code)


def simple_view_without_view_declaration():

    @register(Model)
    class T1:
        id = Integer(primary_key=True)
        code = String()
        val = Integer()

    @register(Model)
    class T2:
        id = Integer(primary_key=True)
        code = String()
        val = Integer()

    @register(Model, factory=MaterializedViewFactory)
    class TestView:
        code = String(primary_key=True)
        val1 = Integer()
        val2 = Integer()


@pytest.fixture(
    scope="class",
    params=[
        simple_view_without_primary_key,
        simple_view_without_view_declaration,
    ]
)
def registry_view_with_exception(request, bloks_loaded):
    registry = init_registry_with_bloks([], request.param)
    request.addfinalizer(registry.close)
    return registry


class TestViewWithException:

    @pytest.fixture(autouse=True)
    def transact(self, request, registry_view_with_exception):
        transaction = registry_view_with_exception.begin_nested()
        request.addfinalizer(transaction.rollback)
        return

    @pytest.mark.xfail(raises=ViewException)
    def test_ok(self, registry_view_with_exception):
        # view is not create, this state must fail
        pass


def simple_view_with_no_data():

    @register(Model)
    class T1:
        id = Integer(primary_key=True)
        code = String()
        val = Integer()

    @register(Model)
    class T2:
        id = Integer(primary_key=True)
        code = String()
        val = Integer()

    @register(Model, factory=MaterializedViewFactory)
    class TestView:
        with_data = False
        code = String(primary_key=True)
        val1 = Integer()
        val2 = Integer()

        @classmethod
        def sqlalchemy_view_declaration(cls):
            T1 = cls.anyblok.T1
            T2 = cls.anyblok.T2
            query = select([T1.code.label('code'),
                            T1.val.label('val1'),
                            T2.val.label('val2')])
            return query.where(T1.code == T2.code)


def simple_view_with_data():

    @register(Model)
    class T1:
        id = Integer(primary_key=True)
        code = String()
        val = Integer()

    @register(Model)
    class T2:
        id = Integer(primary_key=True)
        code = String()
        val = Integer()

    @register(Model, factory=MaterializedViewFactory)
    class TestView:
        with_data = True
        code = String(primary_key=True)
        val1 = Integer()
        val2 = Integer()

        @classmethod
        def sqlalchemy_view_declaration(cls):
            T1 = cls.anyblok.T1
            T2 = cls.anyblok.T2
            query = select([T1.code.label('code'),
                            T1.val.label('val1'),
                            T2.val.label('val2')])
            return query.where(T1.code == T2.code)


class TestView:

    @contextmanager
    def get_registry(self, function):
        conn = create_engine(get_url()).connect()
        conn.execute(
            '''create table t1 (
                id integer CONSTRAINT pk_t1 PRIMARY KEY,
                code varchar(64),
                val integer
            )''')
        conn.execute(
            '''create table t2 (
                id integer CONSTRAINT pk_t2 PRIMARY KEY,
                code varchar(64),
                val integer
            )''')
        conn.execute(
            "insert into t1 (id, code, val) values (1, 'test1', 1)")
        conn.execute(
            "insert into t2 (id, code, val) values (2, 'test1', 2)")
        conn.execute(
            "insert into t1 (id, code, val) values (3, 'test2', 3)")
        conn.execute(
            "insert into t2 (id, code, val) values (4, 'test2', 4)")
        registry = None
        try:
            registry = init_registry_with_bloks([], function)
            yield registry
        finally:
            if registry:
                registry.rollback()
                registry.close()

            conn.execute('drop table if exists t1')
            conn.execute('drop table if exists t2')
            conn.close()

    def test_simple_view_with_no_data(self, bloks_loaded):
        with self.get_registry(simple_view_with_no_data) as registry:
            TestView = registry.TestView
            with pytest.raises(OperationalError):
                TestView.query().filter(TestView.code == 'test1').first()

    def test_simple_view_with_data(self, bloks_loaded):
        with self.get_registry(simple_view_with_data) as registry:
            TestView = registry.TestView
            v1 = TestView.query().filter(TestView.code == 'test1').first()
            v2 = TestView.query().filter(TestView.code == 'test2').first()
            assert v1.val1 == 1
            assert v1.val2 == 2
            assert v2.val1 == 3
            assert v2.val2 == 4
