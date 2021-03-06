#!/usr/bin/env python3
# Copyright 2015 Iain Peet
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

import ast
import logging
import graph.edge as edge
import graph.node as node
from graph.parsers.python3 import resolve_import, make_finder
import imp
import os.path
from workspace.path import Path

class PyFile(node.File):
    def __init__(self, path, workspace, finder=imp.find_module, no_load=False):
        super(PyFile, self).__init__(path)
        self.workspace = workspace
        self.finder = finder
        self.imports = set() # {'path'}
        self.functions = [] # [node.Function]
        self.classes = [] # [node.Class]
        self.calls = [] # [node.Call]

        if not no_load:
            self._load()

    def _load(self):
        with open(self.path.abs) as f:
            try:
                tree = ast.parse(f.read())
            except SyntaxError as e:
                logging.info("Couldn't parse {}: {}".format(self.path, e))
                return

        parsed_imports = [] #[(name, maybe_not_module), ...]
        self.functions = []
        for n in ast.walk(tree):
            if isinstance(n, ast.Import):
                for name in n.names:
                    parsed_imports.append((name.name, False))
            if isinstance(n, ast.ImportFrom):
                parsed_imports.append((n.module, False))
                for name in n.names:
                    parsed_imports.append(
                        ('{}.{}'.format(n.module, name.name), True))

        new_imports = set()
        for name, maybe_not_module in parsed_imports:
            try:
                parent, paths = resolve_import(
                    name, self.finder, self.workspace.python_path)
                new_imports.update(set(
                    Path(os.path.realpath(p), self.workspace.root_dir)
                    for p in paths))
            except ImportError as e:
                if not maybe_not_module:
                    # ImportError is not interesting if this is a name in
                    # "from mod import names", as it's probably a non-module
                    # name.
                    logging.info('Failed to resolve {}:{}: {}'.format(
                        self.path, name, e))

        self.imports = new_imports

    def visit(self, source_graph):
        for i in self.imports:
            d = source_graph.find_file(i)
            if not d:
                # This happens when python resolves a dependency on a file we
                # don't understand...
                continue
            e = edge.Edge(edge.EdgeType.IMPORT, self, d)
            self.outgoing.add(e)
            d.incoming.add(e)

def new_file(path, workspace, external=False):
    if not os.path.isfile(path.abs):
        return None
    if path.abs.endswith('.py'):
        return PyFile(path, workspace, no_load=external)
    elif path.abs.endswith('.pyc'):
        return None
    else:
        logging.debug('Unrecognized file type: {}'.format(path))
        return None

import tempfile
import unittest
import unittest.mock as mock
import shutil

class PyFileTest(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.src = Path('src.py', self.dir)
        self.modules = {
            ('mod', ('/root/pkg/',)): ('/root/pkg/mod.py', imp.PY_SOURCE),
            ('pkg', ('/root/',)): ('/root/pkg/', imp.PKG_DIRECTORY),
            ('root', None): ('/root/', imp.PKG_DIRECTORY)
        }
        self.ws = mock.MagicMock()

    def tearDown(self):
        shutil.rmtree(self.dir)

    def test_load_empty(self):
        open(self.src.abs, 'w').close()
        p = PyFile(self.src, self.ws)
        self.assertEqual(p.imports, set())

    def test_load_malformed(self):
        with open(self.src.abs, 'w') as f:
            f.write('invalid python')
        p = PyFile(self.src, self.ws, make_finder({}))
        self.assertEqual(p.imports, set())

    def test_load_import(self):
        with open(self.src.abs, 'w') as f:
            f.write('import root.pkg.mod')
        mock_finder = make_finder(self.modules)
        p = PyFile(self.src, self.ws, mock_finder)
        self.assertEqual(
            set(i.abs for i in p.imports),
            {'/root/__init__.py', '/root/pkg/__init__.py', '/root/pkg/mod.py'})

    def test_load_multi_import_as(self):
        with open(self.src.abs, 'w') as f:
            f.write('import root.foo as f, root.pkg.mod as m')
        self.modules.update({
            ('foo', ('/root/',)): ('/root/foo.py', imp.PY_SOURCE)
        })
        p = PyFile(self.src, self.ws, make_finder(self.modules))
        self.assertEqual(set(i.abs for i in p.imports),  {
            '/root/__init__.py',
            '/root/foo.py',
            '/root/pkg/__init__.py',
            '/root/pkg/mod.py'
        })

    def test_load_from_import_nonmod(self):
        with open(self.src.abs, 'w') as f:
            f.write('from root.pkg import Classy')
        p = PyFile(self.src, self.ws, make_finder(self.modules))
        self.assertEqual(set(i.abs for i in p.imports),
            {'/root/__init__.py', '/root/pkg/__init__.py'})

    def test_load_from_import_mod(self):
        with open(self.src.abs, 'w') as f:
            f.write('from root.pkg import mod')
        p = PyFile(self.src, self.ws, make_finder(self.modules))
        self.assertEqual(set(i.abs for i in p.imports),
            {'/root/__init__.py', '/root/pkg/__init__.py', '/root/pkg/mod.py'})

if __name__ == '__main__':
    logging.basicConfig(level=logging.ERROR)
    unittest.main()

