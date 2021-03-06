#!/usr/bin/env python3
# Copyright 2015 Iain Peet
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

from argparse import Namespace
import collections

class EdgeType:
    IMPORT='import'
    DECLARE='declare'
    REFER='refer'
    CALL = 'call'

Edge = collections.namedtuple('Edge', ['type', 'source', 'dest'])
