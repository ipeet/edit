#!/usr/bin/env python3
# Copyright 2015 Iain Peet
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

import json
import logging
import os.path
from typing import Callable, Dict, List, Optional, Set

from workspace.path import Path

log = logging.getLogger(__name__)

def initialize_workspace(path:str) -> None:
    '''
    Set up a new worspace directory at the given path.
    '''
    if os.path.exists(path):
        raise Exception('Workspace already exists: {}'.format(path))
    os.makedirs(path)

class Workspace(object):
    def __init__(self, workspace_dir:str, must_exist:bool=False) -> None:
        self.workspace_dir = os.path.abspath(workspace_dir)
        self.files: Set[Path] = set()
        self.file_listeners: List[Callable[[Set[Path], Set[Path]], None]] = []
        self.config: Dict = {}

        if must_exist and not os.path.isdir(self.workspace_dir):
            raise Exception('No workspace dir: {}'.format(self.workspace_dir))

        self._load_config()
        self.reload_file_list()

    def reload_file_list(self) -> None:
        log.info("Loading workspace file list")
        root = self.root_dir
        new_files = set()

        for dirpath, dirnames, filenames in os.walk(root, topdown=True):
            # don't recurse into hidden dirs
            for name in list(dirnames):
                if name.startswith(".") or (name in self.exclude_files):
                    dirnames.remove(name)

            for name in dirnames + filenames:
                if name.startswith(".") or (name in self.exclude_files):
                    continue
                path = os.path.realpath(os.path.join(dirpath, name))
                new_files.add(Path(path, root))

        removed = self.files.difference(new_files)
        added = new_files.difference(self.files)
        self.files = new_files
        for listener in self.file_listeners:
            listener(removed, added)

    def _load_config(self) -> None:
        config_path = os.path.join(self.workspace_dir, 'config')
        try:
            with open(config_path) as f:
                self.config = json.loads(f.read())
        except IOError as e:
            if os.path.exists(config_path):
                log.error('Failed to write {}: {}'.format(config_path, e))
            else:
                # it's valid for no config to exist
                pass

    def _write_config(self) -> None:
        # XXX: shouldn't write (and possibly clobber) if read failed.
        if not os.path.isdir(self.workspace_dir):
            # no workspace dir -> no saving
            return
        config_path = os.path.join(self.workspace_dir, 'config')
        try:
            with open(os.path.join(self.workspace_dir, 'config'), 'w') as f:
                f.write(json.dumps(self.config, indent=4))
        except IOError as e:
            log.error('Failed to write {}: {}'.format(config_path, e))

    @property
    def open_files(self) -> List[Path]:
        return [Path(p, self.root_dir) for p in
            self.config.get('open_files', [])]

    @open_files.setter
    def open_files(self, files:List[Path]) -> None:
        self.config['open_files'] = [p.rel for p in files]
        self._write_config()

    @property
    def root_dir(self) -> str:
        return self.config.get(
            'root_dir', os.path.dirname(self.workspace_dir))

    @root_dir.setter
    def root_dir(self, root:str) -> None:
        self.config['root_dir'] = root
        self._write_config()

    @property
    def python_path(self) -> List[str]:
        return self.config.get('python_path', [])

    @property
    def exclude_files(self) -> List[str]:
        return self.config.get('exclude_files', [])

    @property
    def editor_options(self) -> Dict:
        # populate some defaults:
        res = {
            'style': 'solarized-light',
            'auto-indent': True,
            'indent-width': 4,
            'tab-width': 4,
            'insert-spaces-instead-of-tabs': True,
            'highlight-current-line': True,
            'show-right-margin': True,
            'right-margin-position': 80,
            'show-line-numbers': True,
            'smart-backspace': True,
        }
        res.update(self.config.get('editor_options', {}))
        return res

    @property
    def symbol_index(self) -> Path:
        return Path(os.path.join(self.workspace_dir, 'index.db'), self.root_dir)
        
    def get_stylesheet(self) -> bytes:
        '''
        If custom CSS has been provided, return it.  May return None.
        '''
        css_path = os.path.join(self.workspace_dir, 'override.css')
        if not os.path.exists(css_path):
            return None
        # NB: 'b' is important to the Gtk style loader
        with open(css_path, 'rb') as f:
            return f.read()

import tempfile
import unittest
import unittest.mock as mock
import shutil

class WorkspaceTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.mkdtemp()
        self.ws = os.path.join(self.temp_dir, '.workspace')
        self.alt_ws:Optional[str] = None
        open(os.path.join(self.temp_dir, 'foo'), 'w').close()
        os.mkdir(os.path.join(self.temp_dir, 'dir1'))
        open(os.path.join(self.temp_dir, 'dir1', 'file1'), 'w').close()
        os.mkdir(os.path.join(self.temp_dir, 'dir2'))
        open(os.path.join(self.temp_dir, 'dir2', 'file1'), 'w').close()

    def tearDown(self) -> None:
        shutil.rmtree(self.temp_dir)
        if self.alt_ws:
            shutil.rmtree(self.alt_ws)

    def assert_default_files(self, workspace:Workspace) -> None:
        self.assertEqual(
            set([p.rel for p in workspace.files]),
            set([ 'foo', 'dir1', 'dir1/file1', 'dir2', 'dir2/file1']))

    def test_init(self) -> None:
        w = Workspace(self.ws)
        self.assert_default_files(w)

    def test_init_remote_workspace(self) -> None:
        self.alt_ws = tempfile.mkdtemp()
        with open(os.path.join(self.alt_ws, 'config'), 'w') as f:
            f.write('{"root_dir": "'+self.temp_dir+'"}')
        w = Workspace(self.alt_ws)
        self.assert_default_files(w)

    def test_exclude_files(self) -> None:
        os.mkdir(self.ws)
        with open(os.path.join(self.ws, 'config'), 'w') as f:
            f.write('{"exclude_files": ["dir2"]}')
        w = Workspace(self.ws)
        self.assertEqual(
            set([p.rel for p in w.files]),
            set([  'foo', 'dir1', 'dir1/file1']))

    def test_update(self) -> None:
        w = Workspace(self.ws)
        open(os.path.join(self.temp_dir, 'dir1', 'file2'), 'w').close()
        os.unlink(os.path.join(self.temp_dir, 'dir2', 'file1'))
        cb = mock.MagicMock()
        w.file_listeners.append(cb)
        w.reload_file_list()
        cb.assert_called_once_with(
            set([Path('dir2/file1', self.temp_dir)]),
            set([Path('dir1/file2', self.temp_dir)]))

    def test_hidden_file(self) -> None:
        open(os.path.join(self.temp_dir, '.hidden'), 'w').close()
        w = Workspace(self.ws)
        self.assert_default_files(w)

    def test_hidden_dirs(self) -> None:
        os.mkdir(os.path.join(self.temp_dir, '.hidden'))
        open(os.path.join(self.temp_dir, '.hidden', 'not_hidden'), 'w').close()
        w = Workspace(self.ws)
        self.assert_default_files(w)

    def test_update_doesnt_create_workspace(self) -> None:
        w = Workspace(self.ws)
        w.open_files = [Path('foo', self.temp_dir), Path('bar', self.temp_dir)]
        self.assertFalse(os.path.exists(self.ws))

    def test_update_open_files_written(self) -> None:
        os.mkdir(self.ws)
        w = Workspace(self.ws)
        w.open_files = [Path('foo', self.temp_dir), Path('bar', self.temp_dir)]
        with open(os.path.join(self.ws, 'config')) as f:
            self.assertEqual(f.read(),
               '{\n    "open_files": [\n        "foo",\n        "bar"\n    ]\n}')

    def test_open_files_read(self) -> None:
        os.mkdir(os.path.join(self.ws))
        with open(os.path.join(self.ws, 'config'), 'w') as f:
            f.write('{"open_files": ["foo", "bar"]}')
        w = Workspace(self.ws)
        self.assertEqual([p.rel for p in w.open_files], ["foo", "bar"])

    def test_editor_options_have_defaults(self) -> None:
        os.mkdir(self.ws)
        w = Workspace(self.ws)
        opts = w.editor_options
        self.assertEqual(len(opts), 10)
        self.assertTrue(opts['auto-indent'])

    def test_editor_option_override_defaults(self) -> None:
        os.mkdir(self.ws)
        with open(os.path.join(self.ws, 'config'), 'w') as f:
            json.dump({'editor_options': {'indent-width': 42}}, f)
        w = Workspace(self.ws)
        opts = w.editor_options
        self.assertEqual(len(opts), 10)
        self.assertEqual(opts['indent-width'], 42)

if __name__ == '__main__':
    unittest.main()
