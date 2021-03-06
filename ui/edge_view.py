#!/usr/bin/env python3
# Copyright 2016 Iain Peet
# 
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GObject

import graph.node as node
import os.path
from ui.wrappers import UILocation

class EdgeView(Gtk.VBox):        
    '''
    Displays a list of edges connecting to paricular vertex in the graph.
    '''
    
    OUTGOING = "outgoing"
    INCOMING = "incoming"
    
    __gsignals__ = {
        'location-selected': (GObject.SignalFlags.ACTION, None, (UILocation,))
    }
    
    def __init__(self, edge_type):
        super(EdgeView, self).__init__()
        self.edge_type = edge_type
        self.cur_node = None
        self.edges = []
        
        self.label = Gtk.Label(label='Edges: '+edge_type)
        self.pack_start(self.label, expand=False, fill=False, padding=0)
        
        self.tree_view = Gtk.TreeView(headers_visible=False)
        self.list_store = Gtk.ListStore(str)
        self.tree_view.set_model(self.list_store)
        self.tree_view.append_column(Gtk.TreeViewColumn(
            'Reference', Gtk.CellRendererText(), text=0))
        self.tree_view.connect('row-activated', self.on_activate_row)
        self.pack_start(self.tree_view, expand=True, fill=True, padding=0)
        
    def set_current_node(self, node):
        self.list_store.clear()
        self.cur_node = node
        self.edges = []
        if not node:
            # There may not be a node for the current loc
            return
            
        # Construct a list of (path, edge) tuples for sorting by path
        elements = []
        for e in getattr(self.cur_node, self.edge_type):
            # XXX cheesy assumption edge is an import:
            if self.edge_type is self.OUTGOING:
                elements.append((e.dest.path, e))
            elif self.edge_type is self.INCOMING:
                elements.append((e.source.path, e))
            else:
                raise NotImplementedError()
        
        for p, e in sorted(elements):
            self.list_store.append([p.abbreviate(48)])
            self.edges.append(e)
        
    def on_activate_row(self, widget, path, column):
        inx, = path.get_indices()
        # XXX cheesy assumption edge is an import
        if self.edge_type is self.OUTGOING:
            path = self.edges[inx].dest.path
        elif self.edge_type is self.INCOMING:
            path = self.edges[inx].source.path
        else:
            raise NotImplementedError()
            
        self.emit('location-selected', UILocation(node.Location(path, 0, 0)))

def sandbox():        
    import unittest.mock as mock
    from workspace.path import Path

    win = Gtk.Window()
    n = mock.MagicMock()
    n.outgoing = []
    for p in ['foo', 'bar', 'baz']:
        e = mock.MagicMock()
        e.dest.path = Path(p, '.')
        n.outgoing.append(e)
        
    edge_view = EdgeView(EdgeView.OUTGOING)
    edge_view.connect('location-selected', lambda w, f: print('select '+f))
    edge_view.set_current_node(n)
    win.add(edge_view)
    win.connect("delete-event", Gtk.main_quit)
    win.show_all()
    Gtk.main()
    
if __name__ == '__main__':
    sandbox()
    