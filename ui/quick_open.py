#!/usr/bin/env python3
# Copyright 2015 Iain Peet
# 
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

from gi.repository import Gtk, GObject

import os.path
from ui.wrappers import UIPath
from workspace.path import Path

class QuickOpen(Gtk.VBox):
    __gsignals__ = {
        'path-selected': (GObject.SignalFlags.ACTION, None, (UIPath,))
    }
    
    def __init__(self, workspace):
        super(QuickOpen, self).__init__()
        self.workspace = workspace
        self.entry = Gtk.Entry(placeholder_text='Quick Open (Ctrl+P)')
        self.entry.connect('changed', self.on_entry_changed)
        self.entry.connect('activate', self.on_activate_entry)
        self.pack_start(self.entry, expand=False, fill=False, padding=0)
        
        self.tree_view = Gtk.TreeView(headers_visible=False)
        self.list_store = Gtk.ListStore(str)
        self._add_files_to_store()
        self.filter = self.list_store.filter_new()
        self.filter.set_visible_func(self.file_filter)
        self.tree_view.set_model(self.filter)
        self.tree_view.append_column(Gtk.TreeViewColumn(
            'Filename', Gtk.CellRendererText(), text=0))
        self.tree_view.connect('row-activated', self.on_activate_row)
        self.pack_start(self.tree_view, expand=True, fill=True, padding=0)
    
    def _add_files_to_store(self):
        self.paths = sorted([p for p in self.workspace.files if
            not os.path.isdir(p.abs)])
        for i, p in enumerate(self.paths):
            list_iter = self.list_store.append([p.abbreviate(48)])
        
    def file_filter(self, model, iterator, data):
        search = self.entry.get_text()
        if not search:
            return False
        if search == '*':
            return True
        inx, = model.get_path(iterator).get_indices()
        return search in self.paths[inx].shortest
        
    def register_accelerators(self, accel_group):
        key, mod = Gtk.accelerator_parse("<Control>p")
        self.entry.add_accelerator(
            "grab-focus", accel_group, key, mod, Gtk.AccelFlags.VISIBLE)
        
    def on_entry_changed(self, widget):
        self.filter.refilter()
        
    def on_activate_entry(self, widget):
        self.emit('path-selected', UIPath(Path(
            self.entry.get_text(), self.workspace.root_dir)))
        
    def on_activate_row(self, widget, path, column):
        inx, = self.filter.convert_path_to_child_path(path).get_indices()
        self.emit('path-selected', UIPath(self.paths[inx]))
        
def sandbox():
    import unittest.mock as mock
    from workspace.path import Path
    
    win = Gtk.Window()
    ws = mock.MagicMock()
    ws.root_dir = ''
    ws.files = [Path(p, '.') for p in [
        'foo.py', 
        'bar.py', 
        'baz.py', 
        'dir/foobar.py', 
        'dir/inner/coffee.py', 
        'other/bat.py'
    ]]
    quick_open = QuickOpen(ws)
    quick_open.connect('path-selected', 
        lambda w, f: print('select '+str(f)))
    win.add(quick_open)
    win.connect("delete-event", Gtk.main_quit)
    win.show_all()
    Gtk.main()

if __name__ == '__main__':
    sandbox()
    