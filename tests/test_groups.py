# -*- coding: utf-8 -*-
from __future__ import print_function, unicode_literals
import unittest

import mock
import six

from importanize.groups import (
    BaseImportGroup,
    ImportGroups,
    LocalGroup,
    PackagesGroup,
    RemainderGroup,
    SitePackagesGroup,
    StdLibGroup,
)
from importanize.statements import ImportLeaf, ImportStatement


class TestBaseImportGroup(unittest.TestCase):
    def test_init(self):
        actual = BaseImportGroup(mock.sentinel.config)
        self.assertEqual(actual.config, mock.sentinel.config)
        self.assertListEqual(actual.statements, [])

    @mock.patch('importanize.groups.sorted', create=True)
    @mock.patch('importanize.groups.list', create=True)
    @mock.patch('importanize.groups.set', create=True)
    @mock.patch.object(BaseImportGroup, 'merged_statements')
    def test_unique_statements(self,
                               mock_merged_statements,
                               mock_set,
                               mock_list,
                               mock_sorted):
        group = BaseImportGroup()

        actual = group.unique_statements

        self.assertEqual(actual, mock_sorted.return_value)

        mock_set.assert_called_once_with(mock_merged_statements)
        mock_list.assert_called_once_with(mock_set.return_value)
        mock_sorted.assert_called_once_with(mock_list.return_value)

    def test_merged_statements(self):
        group = BaseImportGroup()
        group.statements = [ImportStatement([], 'a', [ImportLeaf('b')]),
                            ImportStatement([], 'a', [ImportLeaf('c')]),
                            ImportStatement([], 'b', [ImportLeaf('c')])]

        actual = group.merged_statements

        self.assertListEqual(sorted(actual), [
            ImportStatement([], 'a', [ImportLeaf('b'),
                                      ImportLeaf('c')]),
            ImportStatement([], 'b', [ImportLeaf('c')]),
        ])

    def test_merged_statements_leafless(self):
        group = BaseImportGroup()
        group.statements = [ImportStatement([], 'a', [ImportLeaf('b')]),
                            ImportStatement([], 'a', []),
                            ImportStatement([], 'b', [ImportLeaf('c')])]

        actual = group.merged_statements

        self.assertListEqual(sorted(actual), [
            ImportStatement([], 'a', []),
            ImportStatement([], 'a', [ImportLeaf('b')]),
            ImportStatement([], 'b', [ImportLeaf('c')]),
        ])

    def test_merged_statements_special(self):
        group = BaseImportGroup()
        group.statements = [ImportStatement([], 'a', [ImportLeaf('*')]),
                            ImportStatement([], 'b', [ImportLeaf('c')])]

        actual = group.merged_statements

        self.assertListEqual(sorted(actual), [
            ImportStatement([], 'a', [ImportLeaf('*')]),
            ImportStatement([], 'b', [ImportLeaf('c')]),
        ])

    def test_all_line_numbers(self):
        s2 = ImportStatement([2, 7], 'b')
        s1 = ImportStatement([1, 2], 'a')

        group = BaseImportGroup()
        group.statements = [s1, s2]

        self.assertListEqual(group.all_line_numbers(),
                             [1, 2, 7])

    def test_should_add_statement(self):
        with self.assertRaises(NotImplementedError):
            BaseImportGroup().should_add_statement(None)

    @mock.patch.object(BaseImportGroup, 'should_add_statement')
    def test_add_statement_true(self, mock_should):
        mock_should.return_value = True

        group = BaseImportGroup()
        group.add_statement(mock.sentinel.statement)

        self.assertListEqual(group.statements,
                             [mock.sentinel.statement])
        mock_should.assert_called_once_with(mock.sentinel.statement)

    @mock.patch.object(BaseImportGroup, 'should_add_statement')
    def test_add_statement_false(self, mock_should):
        mock_should.return_value = False

        group = BaseImportGroup()
        group.add_statement(mock.sentinel.statement)

        self.assertListEqual(group.statements, [])
        mock_should.assert_called_once_with(mock.sentinel.statement)

    def test_as_string(self):
        group = BaseImportGroup()
        group.statements = [ImportStatement([], 'b'),
                            ImportStatement([], 'a')]

        self.assertEqual(
            group.as_string(),
            'import a\n'
            'import b'
        )

    def test_as_string_with_artifacts(self):
        group = BaseImportGroup(file_artifacts={'sep': '\r\n'})
        group.statements = [ImportStatement([], 'b'),
                            ImportStatement([], 'a')]

        self.assertEqual(
            group.as_string(),
            'import a\r\n'
            'import b'
        )

    def test_formatted(self):
        group = BaseImportGroup()
        group.statements = [
            ImportStatement([], 'b' * 80, [ImportLeaf('c'),
                                           ImportLeaf('d')]),
            ImportStatement([], 'a')
        ]

        self.assertEqual(
            group.formatted(),
            'import a\n' +
            'from {} import (\n'.format('b' * 80) +
            '    c,\n' +
            '    d,\n' +
            ')'
        )

    def test_formatted_with_artifacts(self):
        artifacts = {'sep': '\r\n'}
        group = BaseImportGroup(file_artifacts=artifacts)
        group.statements = [
            ImportStatement(list(), 'b' * 80, [ImportLeaf('c'),
                                               ImportLeaf('d')],
                            file_artifacts=artifacts),
            ImportStatement([], 'a', file_artifacts=artifacts)
        ]

        self.assertEqual(
            group.formatted(),
            'import a\r\n' +
            'from {} import (\r\n'.format('b' * 80) +
            '    c,\r\n' +
            '    d,\r\n' +
            ')'
        )

    @mock.patch.object(BaseImportGroup, 'as_string')
    def test_str(self, mock_as_string):
        self.assertEqual(
            getattr(BaseImportGroup(),
                    '__{}__'.format(six.text_type.__name__))(),
            mock_as_string.return_value
        )
        mock_as_string.assert_called_once_with()


class TestSitePackagesGroup(unittest.TestCase):
    @mock.patch('importanize.groups.is_site_package')
    def test_should_add_statement(self, mock_is_std_lib):
        statement = mock.MagicMock()
        actual = SitePackagesGroup().should_add_statement(statement)
        self.assertEqual(actual, mock_is_std_lib.return_value)
        mock_is_std_lib.assert_called_once_with(statement.root_module)


class TestStdLibGroup(unittest.TestCase):
    @mock.patch('importanize.groups.is_std_lib')
    def test_should_add_statement(self, mock_is_std_lib):
        statement = mock.MagicMock()
        actual = StdLibGroup().should_add_statement(statement)
        self.assertEqual(actual, mock_is_std_lib.return_value)
        mock_is_std_lib.assert_called_once_with(statement.root_module)


class TestPackagesGroup(unittest.TestCase):
    def test_init(self):
        config = {'packages': []}
        group = PackagesGroup(config)
        self.assertDictEqual(group.config, config)

        with self.assertRaises(ValueError):
            PackagesGroup()

    def test_should_add_statement(self):
        config = {'packages': ['a']}
        group = PackagesGroup(config)

        self.assertTrue(group.should_add_statement(ImportStatement([], 'a')))
        self.assertFalse(group.should_add_statement(ImportStatement([], 'b')))


class TestLocalGroup(unittest.TestCase):
    def test_should_add_statement(self):
        group = LocalGroup()

        self.assertTrue(group.should_add_statement(ImportStatement([], '.a')))
        self.assertFalse(group.should_add_statement(ImportStatement([], 'b')))


class TestRemainderGroup(unittest.TestCase):
    def test_should_add_statement(self):
        group = RemainderGroup()

        self.assertTrue(group.should_add_statement(ImportStatement([], '.a')))


class TestImportGroups(unittest.TestCase):
    def test_init(self):
        groups = ImportGroups()
        self.assertListEqual(groups.groups, [])

    def test_all_line_numbers(self):
        groups = ImportGroups()

        self.assertListEqual(groups.all_line_numbers(), [])

        g = BaseImportGroup()
        g.statements = [mock.MagicMock(line_numbers=[2, 7],
                                       spec=ImportStatement)]
        groups.groups.append(g)

        g = BaseImportGroup()
        g.statements = [mock.MagicMock(line_numbers=[1, 2],
                                       spec=ImportStatement)]
        groups.groups.append(g)

        self.assertListEqual(groups.all_line_numbers(), [1, 2, 7])

    def test_add_group(self):
        groups = ImportGroups()

        with self.assertRaises(ValueError):
            groups.add_group({})

        with self.assertRaises(ValueError):
            groups.add_group({'type': 'foo'})

        groups.add_group({'type': 'stdlib'})

        self.assertEqual(len(groups.groups), 1)
        self.assertEqual(groups.groups[0].__class__, StdLibGroup)

    def test_add_statement_to_group_one(self):
        groups = ImportGroups()
        groups.groups = [
            LocalGroup()
        ]

        with self.assertRaises(ValueError):
            groups.add_statement_to_group(
                ImportStatement([], 'a')
            )

        groups.add_statement_to_group(
            ImportStatement([], '.a')
        )

        self.assertListEqual(
            groups.groups[0].statements,
            [ImportStatement([], '.a')]
        )

    def test_add_statement_to_group_priority(self):
        groups = ImportGroups()
        groups.groups = [
            RemainderGroup(),
            LocalGroup(),
        ]

        groups.add_statement_to_group(
            ImportStatement([], '.a')
        )

        self.assertListEqual(
            groups.groups[0].statements,
            []
        )
        self.assertListEqual(
            groups.groups[1].statements,
            [ImportStatement([], '.a')]
        )

    def test_as_string(self):
        self.assertEqual(ImportGroups().as_string(), '')

    def test_formatted_empty(self):
        self.assertEqual(ImportGroups().formatted(), '')

    def test_formatted_with_artifacts(self):
        artifacts = {'sep': '\r\n'}

        groups = ImportGroups(file_artifacts=artifacts)
        groups.groups = [
            RemainderGroup(file_artifacts=artifacts),
            LocalGroup(file_artifacts=artifacts),
        ]

        groups.add_statement_to_group(
            ImportStatement([], '.a', file_artifacts=artifacts)
        )
        groups.add_statement_to_group(
            ImportStatement([], 'foo', file_artifacts=artifacts)
        )

        self.assertEqual(
            groups.formatted(),
            'import foo\r\n'
            '\r\n'
            'import .a'
        )

    @mock.patch.object(ImportGroups, 'as_string')
    def test_str_mock(self, mock_as_string):
        self.assertEqual(
            getattr(ImportGroups(),
                    '__{}__'.format(six.text_type.__name__))(),
            mock_as_string.return_value
        )
