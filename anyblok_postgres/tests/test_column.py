# This file is a part of the AnyBlok / Postgres project
#
#    Copyright (C) 2018 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
from anyblok.tests.testcase import DBTestCase
from anyblok.tests.test_column import simple_column
from anyblok_postgres.column import Jsonb, LargeObject
from os import urandom


class TestColumns(DBTestCase):

    def test_jsonb(self):
        registry = self.init_registry(simple_column, ColumnType=Jsonb)
        val = {'a': 'Test'}
        test = registry.Test.insert(col=val)
        self.assertEqual(test.col, val)

    def test_jsonb_update(self):
        registry = self.init_registry(simple_column, ColumnType=Jsonb)
        test = registry.Test.insert(col={'a': 'test'})
        test.col['b'] = 'test'
        self.assertEqual(test.col, {'a': 'test', 'b': 'test'})

    def test_jsonb_simple_filter(self):
        registry = self.init_registry(simple_column, ColumnType=Jsonb)
        Test = registry.Test
        Test.insert(col={'a': 'test'})
        Test.insert(col={'a': 'test'})
        Test.insert(col={'b': 'test'})
        self.assertEqual(
            Test.query().filter(Test.col['a'].astext == 'test').count(), 2)

    def test_jsonb_null(self):
        registry = self.init_registry(simple_column, ColumnType=Jsonb)
        Test = registry.Test
        Test.insert(col=None)
        Test.insert(col=None)
        Test.insert(col={'a': 'test'})
        self.assertEqual(Test.query().filter(Test.col.is_(None)).count(), 2)
        self.assertEqual(Test.query().filter(Test.col.isnot(None)).count(), 1)

    def test_large_object(self):
        registry = self.init_registry(simple_column, ColumnType=LargeObject)
        hugefile = urandom(1000)
        test = registry.Test.insert(col=hugefile)
        self.assertEqual(test.col, hugefile)
        oid1 = registry.execute('select col from test').fetchone()[0]
        self.assertNotEqual(oid1, hugefile)
        hugefile2 = urandom(1000)
        test.col = hugefile2
        registry.flush()
        self.assertNotEqual(test.col, hugefile)
        self.assertEqual(test.col, hugefile2)
        oid2 = registry.execute('select col from test').fetchone()[0]
        self.assertEqual(oid1, oid2)
