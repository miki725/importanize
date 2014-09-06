# -*- coding: utf-8 -*-
from __future__ import print_function, unicode_literals


class ComparatorMixin(object):
    def __ne__(self, other):
        return not (self == other)

    def __lt__(self, other):
        return not (self == other) and not (self > other)

    def __ge__(self, other):
        return (self == other) and (self > other)

    def __le__(self, other):
        return not (self > other)
