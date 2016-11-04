#!/usr/bin/env python3
# Copyright 2015 Iain Peet
# 
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

from gi.repository import Gdk, GObject, Gtk
from ui.edit_pane import EditPane
from ui.quick_open import QuickOpen

class MainWindow(Gtk.Window):
    def __init__(self, workspace, src_graph):
        super(MainWindow, self).__init__(
            title="Edit", default_width=600, default_height=800)
        self.workspace = workspace
        self.src_graph = src_graph
        self.edit_pane = EditPane(self, self.workspace, self.src_graph)
        self.quick_open = QuickOpen(self.workspace)

        self.accelerators = Gtk.AccelGroup()
        self.add_accel_group(self.accelerators)
        self.menu_bar = Gtk.MenuBar()
        self._build_menus()

        self.hbox = Gtk.HBox()
        self.hbox.pack_start(self.edit_pane, True, True, 0)
        self.hbox.pack_start(self.quick_open, False, False, 0)
        
        self.vbox = Gtk.VBox()
        self.vbox.pack_start(self.menu_bar, False, False, 0)
        self.vbox.pack_start(self.hbox, True, True, 0)
        self.add(self.vbox)
        
    def _build_menus(self):
        file_menu_item = Gtk.MenuItem(label="File")
        file_menu = Gtk.Menu()
        file_menu_item.set_submenu(file_menu)
        
        save = Gtk.MenuItem(label="Save")
        key, mod = Gtk.accelerator_parse("<Control>s")        
        save.add_accelerator(
            "activate", self.accelerators, key, mod, Gtk.AccelFlags.VISIBLE)
        save.connect("activate", self.edit_pane.save_handler)
        file_menu.add(save)
        
        open_item = Gtk.MenuItem(label="Open")
        key, mod = Gtk.accelerator_parse("<Control>o")
        open_item.add_accelerator(
            "activate", self.accelerators, key, mod, Gtk.AccelFlags.VISIBLE)
        open_item.connect("activate", self.open_handler)
        file_menu.add(open_item)
        
        new = Gtk.MenuItem(label="New")
        key, mod = Gtk.accelerator_parse("<Control>n")
        new.add_accelerator(
            "activate", self.accelerators, key, mod, Gtk.AccelFlags.VISIBLE)
        new.connect("activate", self.edit_pane.new_file_handler)
        file_menu.add(new)
        
        close_tab = Gtk.MenuItem(label="Close Tab")
        key, mod = Gtk.accelerator_parse("<Control>w")
        close_tab.add_accelerator(
            "activate", self.accelerators, key, mod, Gtk.AccelFlags.VISIBLE)
        close_tab.connect("activate", self.edit_pane.close_tab_handler)
        file_menu.add(close_tab)
        
        quit = Gtk.MenuItem(label="Quit")
        key, mod = Gtk.accelerator_parse("<Control>q")
        quit.add_accelerator(
            "activate", self.accelerators, key, mod, Gtk.AccelFlags.VISIBLE)
        quit.connect("activate", Gtk.main_quit)
        file_menu.add(quit)
        
        self.menu_bar.add(file_menu_item)    
                
    def open_handler(self, widget):
        dialog = Gtk.FileChooserDialog(
            "Open File", 
            self,
            Gtk.FileChooserAction.OPEN,
            (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
            Gtk.STOCK_OPEN, Gtk.ResponseType.ACCEPT))
        dialog.set_current_folder(self.workspace.root_dir)
        res = dialog.run()
        if res == Gtk.ResponseType.ACCEPT:
            self.edit_pane.open_file(dialog.get_filename())
        dialog.destroy()
        