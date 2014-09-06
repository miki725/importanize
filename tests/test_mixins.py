# -*- coding: utf-8 -*-
from __future__ import print_function, unicode_literals
import unittest

import mock

from importanize.mixin import ComparatorMixin


class TestComparatorMixin(unittest.TestCase):
    @mock.patch.object(ComparatorMixin, '__eq__', create=True)
    def test_ne(self, mock_eq):
        mock_eq.return_value = True

        c1 = ComparatorMixin()
        c2 = ComparatorMixin()

        self.assertFalse(c1 != c2)
        mock_eq.assert_called_once_with(c2)

    @mock.patch.object(ComparatorMixin, '__eq__', create=True)
    @mock.patch.object(ComparatorMixin, '__gt__', create=True)
    def test_lt(self, mock_eq, mock_gt):
        mock_eq.return_value = False
        mock_gt.return_value = False

        c1 = ComparatorMixin()
        c2 = ComparatorMixin()

        self.assertTrue(c1 < c2)
        mock_eq.assert_called_once_with(c2)
        mock_gt.assert_called_once_with(c2)

    @mock.patch.object(ComparatorMixin, '__eq__', create=True)
    @mock.patch.object(ComparatorMixin, '__gt__', create=True)
    def test_ge(self, mock_eq, mock_gt):
        mock_eq.return_value = True
        mock_gt.return_value = True

        c1 = ComparatorMixin()
        c2 = ComparatorMixin()

        self.assertTrue(c1 >= c2)
        mock_eq.assert_called_once_with(c2)
        mock_gt.assert_called_once_with(c2)

    @mock.patch.object(ComparatorMixin, '__gt__', create=True)
    def test_le(self, mock_gt):
        mock_gt.return_value = False

        c1 = ComparatorMixin()
        c2 = ComparatorMixin()

        self.assertTrue(c1 <= c2)
        mock_gt.assert_called_once_with(c2)
