#!/usr/bin/env python3
# Copyright 2016 Iain Peet
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

import os.path
from typing import Any

class Path(object):
    '''
    Represents a particular location in the filesystem.  Also knows where the
    workspace root is, enabling useful abs-relative transformations, etc.
    '''

    def __init__(self, path:str, ws_root:str) -> None:
        super(Path, self).__init__()
        if os.path.isabs(path):
            self.abs = os.path.realpath(path)
        else:
            self.abs = os.path.realpath(os.path.join(ws_root, path))
        self.ws_root = ws_root

    def __repr__(self) -> str:
        return 'Path({!r}, {!r})'.format(self.rel, self.ws_root)

    def __eq__(self, other: Any) -> bool:
        return isinstance(other, Path) and \
            (self.abs, self.ws_root) == (other.abs, other.ws_root)

    def __ge__(self, other: Any) -> bool:
        return self.abs >= other.abs

    def __gt__(self, other: Any) -> bool:
        return self.abs > other.abs

    def __ne__(self, other: Any) -> bool:
        return not self.__eq__(other)

    def __le__(self, other: Any) -> bool:
        return not self.__gt__(other)

    def __lt__(self, other: Any) -> bool:
        return not self.__ge__(other)

    def __hash__(self) -> int:
        return hash((self.abs, self.ws_root))

    @property
    def rel(self) -> str:
        return os.path.relpath(self.abs, self.ws_root)

    @property
    def shortest(self) -> str:
        return self.rel if len(self.rel) < len(self.abs) else self.abs

    @property
    def in_workspace(self) -> bool:
        return self.abs.startswith(self.ws_root)

    @property
    def basename(self) -> str:
        return os.path.basename(self.abs)

    @property
    def isdir(self) -> bool:
        return os.path.isdir(self.abs)

    def abbreviate(self, max_len:int=32, require_basename:bool=True) -> str:
        '''
        Returns the shortest possible path (whether abs or relative), removing
        characters from the middle if required to meet the given maximum.
        If require_basename is True, the abbreviation will always include the
        full basename.  If the basename is longer than max_len, max_len is not
        respected.
        '''
        assert max_len >= 16
        res = self.shortest
        if len(res) <= max_len:
            return res
        else:
            # Trim some out of the middle.  On the basis that the suffix is
            # probably most  important, and then the prefix, allocate 2/3
            # of our chars to the suffix, with remaining third less the '..'
            # going to the prefix.
            suffix_count = int(max_len * 2 / 3)
            if require_basename:
                if suffix_count < len(os.path.basename(res)):
                    suffix_count = len(os.path.basename(res))
            prefix_count = max_len - suffix_count - 2
            if prefix_count < 0:
                # Can occur with a long basename and require_basename
                prefix_count = 0
            return res[:prefix_count] + '..' + res[-suffix_count:]

import unittest

class PathTest(unittest.TestCase):
    def test_abbrev_rel_shorter(self) -> None:
        p = Path('/foo/bar', '/foo')
        self.assertEqual(p.abbreviate(), 'bar')

    def test_abbrev_abs_shorter(self) -> None:
        p = Path('/foo/bar', '/baz')
        self.assertEqual(p.abbreviate(), '/foo/bar')

    def test_abbrev_shortest(self) -> None:
        p = Path('/this/isareally/very/annoyingly/perversely/even/path', 'foo')
        self.assertEqual(p.abbreviate(max_len=16), '/thi../even/path')

    def test_abbrev_require_long_basename(self) -> None:
        p = Path('/foo/this_is_a_very_long_basename', '/bar')
        self.assertEqual(p.abbreviate(max_len=16),
            '..this_is_a_very_long_basename')

if __name__ == '__main__':
    unittest.main()
