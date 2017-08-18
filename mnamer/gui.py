#!/usr/bin/env python3

"""gui.py - processes user interaction via GUI interface
"""
import tkinter as tk
import webbrowser
from tkinter import ttk
from tkinter.filedialog import askdirectory, askopenfilenames
from tkinter.font import Font
from typing import List, Optional

from mnamer import utils
from mnamer.config import Config
from mnamer.icons import Icons
from mnamer.metadata import MediaType, Metadata


def launch(conf: Config,
           files: List[str],
           o_dest: Optional[str] = None,
           o_temp: Optional[str] = None,
           o_mtype: Optional[MediaType] = None,
           prev: bool = False
           ):
    model = Model(conf)
    view = View()
    controller = Controller(model, view)
    controller.add_media(files)
    view.update_ctrl()
    view.mainloop()


class Model:
    def __init__(self, config: Config):
        self.meta: List[Metadata] = list()
        self.config: Config = config

    def match(self, entries: List[int] = None):
        pass

    def rename(self, entries: List[int] = None):
        pass


class View(tk.Tk):
    def __init__(self):
        tk.Tk.__init__(self)

        # Setup window
        self.icon_store = Icons().__store
        self.minsize(1000, 650)
        self.iconphoto(True, self.icon_store['favicon'])
        self.wm_title("mnamer")
        self.grid_columnconfigure(index=0, weight=4)
        self.grid_columnconfigure(index=2, weight=3)
        self.grid_rowconfigure(index=0, weight=1)
        bold_label_font = Font(family="Helvetica", size=10, weight='bold')

        # Setup menu
        menu = tk.Menu(self, tearoff=0)
        self.config(menu=menu)
        self.file_menu = tk.Menu(menu, tearoff=0)
        menu.add_cascade(label="File", menu=self.file_menu)
        self.file_menu.add_command(label="Add File")
        self.file_menu.add_command(label="Add Folder")
        self.file_menu.add_separator()
        self.file_menu.add_command(label="Settings")
        self.file_menu.add_command(label="Import Settings")
        self.file_menu.add_command(label="Export Settings")
        self.file_menu.add_separator()
        self.file_menu.add_command(label="Exit")
        self.help_menu = tk.Menu(menu, tearoff=0)
        menu.add_cascade(label="Help", menu=self.help_menu)
        self.help_menu.add_command(label="Online Docs")
        self.help_menu.add_command(label="About")

        # Setup file panel
        files_panel = tk.Frame(self, relief=tk.GROOVE, borderwidth=2)
        files_panel.grid(
            row=0, column=0, padx=5, pady=5, sticky=tk.N + tk.E + tk.S + tk.W
        )
        files_label_h1 = tk.Label(
            files_panel, text="Media files", font=bold_label_font
        )
        files_label_h1.pack(side=tk.TOP, anchor=tk.W, padx=2, pady=(5, 0))
        self.files_label_h2 = tk.Label(
            files_panel, text="0 files added",
            font=Font(family='Helvetica', size=8)
        )
        self.files_label_h2.pack(side=tk.TOP, anchor=tk.W, padx=2)
        self.file_list = self._ListBox(
            files_panel,
            borderwidth=1,
            highlightcolor='lightgrey',
            selectmode=tk.BROWSE,
            activestyle=tk.NONE
        )
        self.file_list.pack(
            side=tk.TOP, expand=tk.YES, fill=tk.BOTH, padx=5, pady=5
        )
        vsb = ttk.Scrollbar(
            self.file_list,
            orient=tk.VERTICAL,
            command=self.file_list.yview
        )
        self.file_list.config(yscrollcommand=vsb.set)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)

        # Setup control panel
        ctrl_panel = tk.Frame(self)
        ctrl_panel.grid(
            row=0, column=1, padx=5, pady=(5, 0), sticky=tk.N + tk.S
        )
        self.ctrl_listbox = self._IconPanel(ctrl_panel, self.icon_store)
        self.ctrl_listbox.insert('previous')
        self.ctrl_listbox.insert('next', top=False)
        self.ctrl_listbox.insert('add_folder')
        self.ctrl_listbox.insert('add_file')
        self.ctrl_listbox.insert('remove')
        self.ctrl_listbox.insert('match')
        self.ctrl_listbox.insert('rename')

        # Setup query panel
        query_panel = tk.Frame(self, relief=tk.GROOVE, borderwidth=2)
        query_panel.grid(
            row=0, column=2, padx=5, pady=5, sticky=tk.N + tk.E + tk.S + tk.W
        )

        # Setup database selection frame
        db_label_h1 = tk.Label(
            query_panel, text="Database Selection", font=bold_label_font
        )
        db_label_h1.pack(side=tk.TOP, anchor=tk.W, padx=2, pady=(5, 0))
        db_comps = self._FieldBuilder(query_panel)
        db_comps.insert('media_type', combo=True)
        db_comps.insert('database', combo=True)

        # Setup match frame
        match_label_h1 = tk.Label(
            query_panel, text='Match results', font=bold_label_font
        )
        match_label_h1.pack(side=tk.TOP, anchor=tk.W, pady=(10, 2))
        self.match_listbox = tk.Listbox(
            query_panel,
            borderwidth=1,
            highlightcolor='lightgrey',
            selectmode=tk.BROWSE,
            activestyle=tk.NONE
        )
        self.match_listbox.pack(
            expand=tk.YES, fill=tk.BOTH, padx=5, pady=5)
        vsb = ttk.Scrollbar(
            self.match_listbox,
            orient=tk.VERTICAL,
            command=self.match_listbox.yview
        )
        self.match_listbox.config(yscrollcommand=vsb.set)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)

        # Setup metadata frame
        meta_label_h1 = tk.Label(
            query_panel, text="Metadata Entry", font=bold_label_font
        )
        meta_label_h1.pack(side=tk.TOP, anchor=tk.W, padx=2, pady=(10, 2))
        self.meta_fields = self._FieldBuilder(query_panel)
        self.meta_fields.insert('title')
        self.meta_fields.insert('year')
        self.meta_fields.insert('season')
        self.meta_fields.insert('episode')
        self.meta_fields.insert('quality')
        self.meta_fields.insert('template')
        self.meta_fields.insert('original_filename')
        self.meta_fields.insert('new_filename')

    def update_ctrl(self, e=None):

        # Set previous button
        self.ctrl_listbox['previous'].config(
            state=tk.ACTIVE if self.file_list.has_previous else tk.DISABLED
        )

        # Set remove button
        self.ctrl_listbox['remove'].config(
            state=tk.ACTIVE if self.file_list.cur_name else tk.DISABLED
        )

        # Set match button
        self.ctrl_listbox['match'].config(
            state=tk.ACTIVE if self.file_list.cur_name else tk.DISABLED
        )

        # Set rename button
        self.ctrl_listbox['rename'].config(
            state=tk.ACTIVE if self.file_list.cur_name else tk.DISABLED
        )

        # Set next button
        self.ctrl_listbox['next'].config(
            state=tk.ACTIVE if self.file_list.has_next else tk.DISABLED
        )

    class _ListBox(tk.Listbox):

        @property
        def cur_name(self):
            return self.get(tk.ANCHOR) \
                if self.get(tk.ANCHOR) \
                else self.get(tk.ACTIVE)

        @property
        def cur_index(self):
            return self.curselection()[0] if self.curselection() else -1

        @cur_index.setter
        def cur_index(self, value):
            self.select_clear(self.cur_index)
            self.select_set(value)

        @property
        def has_files(self):
            return self.size() > 0

        @property
        def has_next(self):
            return 0 < self.cur_index + 1 < self.size()

        @property
        def has_previous(self):
            return self.cur_index > 0

    class _IconPanel(dict):
        def __init__(self, master, icon_store, **kwargs):
            super().__init__(**kwargs)
            self.master = master
            self.icon_store = icon_store
            self.font = Font(family='Helvetica', size=10)
            self.font = Font(family='Helvetica', size=10)

        def insert(self, name, width=75, top=True):
            btn = tk.Button(
                master=self.master,
                width=width,
                text=name.replace('_', ' ').capitalize(),
                image=self.icon_store[name],
                compound=tk.TOP,
                relief=tk.GROOVE,
                font=self.font
            )
            self[name] = btn
            self[name].pack(side=tk.TOP if top else tk.BOTTOM, pady=(0, 5))

    class _FieldBuilder(dict):
        def __init__(self, master, **kwargs):
            super().__init__(**kwargs)
            self.master = master
            self.font = Font(family='Helvetica', size=8)

        def insert(self, name, combo=False, enabled=False):
            label = tk.Label(
                master=self.master,
                text=name.replace('_', ' ').capitalize(),
                font=self.font,
            )
            label.pack(side=tk.TOP, padx=2, anchor=tk.W)

            if combo:
                entry = ttk.Combobox(
                    master=self.master,
                    font=self.font,
                    state=tk.NORMAL if enabled else tk.DISABLED
                )
            else:
                entry = tk.Entry(
                    master=self.master,
                    font=self.font,
                    state=tk.NORMAL if enabled else tk.DISABLED
                )
            entry.pack(side=tk.TOP, padx=5, pady=5, anchor=tk.W, fill=tk.X)
            self[name] = entry

    class AboutDialog(tk.Toplevel):
        def __init__(self, master):
            tk.Toplevel.__init__(self, master=master)
            self._img_label = tk.Label(self, image=master.images['logo'])
            self._img_label.pack(padx=10, pady=10)
            font = Font(family='Helvetica', size=12)
            tk.Label(self, font=font, text='Jessy Williams (jkwill87)').pack()
            tk.Label(self, font=font, text='jessy@jessywilliams.com').pack()
            tk.Label(self, font=font, text='github.com/jkwill87/mnamer').pack()
            tk.Label(self, font=font, text='License: MIT').pack()

            # Make modal and non-resizeable
            self.resizable(width=False, height=False)
            self.transient(master)
            self.grab_set()
            master.wait_window(self)


class Controller:
    def __init__(self, model: Model, view: View, movie_mode: bool = True):
        self.model = model
        self.view = view
        self.movie_mode = movie_mode

        # Register menu commands
        self.view.file_menu.entryconfig('Add File', command=self.add_file)
        self.view.file_menu.entryconfig('Add Folder', command=self.add_folder)
        self.view.help_menu.entryconfig('About', command=self.show_about)
        self.view.help_menu.entryconfig(
            'Online Docs', command=lambda:
            webbrowser.open_new('https://github.com/jkwill87/mnamer/wiki')
        )

        # Register control panel commands
        self.view.ctrl_listbox['add_folder'].config(command=self.add_folder)
        self.view.ctrl_listbox['add_file'].config(command=self.add_file)
        self.view.ctrl_listbox['remove'].config(command=self.remove)
        self.view.ctrl_listbox['previous'].config(command=self.move_previous)
        self.view.ctrl_listbox['next'].config(command=self.move_next)

        # Register bindings
        self.view.file_list.bind('<<ListboxSelect>>', self.view.update_ctrl)

    def add_media(self, targets, mtype=MediaType.UNKNOWN) -> bool:
        selected = utils.crawl(
            targets=targets,
            recurse=self.model.config.recurse,
            extmask=self.model.config.extmask,
        )

        # Add files to list, skipping those which have been already included
        if selected:
            self.model.meta += [
                Metadata(file, mtype) for file in selected
                if file not in self.model.meta
                ]
            self.set_listbox()
            self.view.files_label_h2.config(
                text='%d files added' % len(self.model.meta))
            if self.view.file_list.cur_index < 0:
                self.view.file_list.cur_index = 0
            return True

        else:
            return False

    def add_file(self):
        return self.add_media(targets=askopenfilenames())

    def add_folder(self):
        return self.add_media(targets=askdirectory())

    def set_listbox(self):
        self.view.file_list.delete(0, tk.END)
        oddrow = True
        for meta in self.model.meta:
            self.view.file_list.insert(tk.END, meta.filename)
            oddrow = False if oddrow else True  # toggle

    def remove(self):
        index = self.view.file_list.cur_index
        del (self.model.meta[index])
        self.view.file_list.delete(index)
        self.view.update_ctrl()

        if index == 1:
            self.view.file_list.select_set(0)
        elif index == self.view.file_list.size():
            self.view.file_list.select_set(index - 1)
        else:
            self.view.file_list.select_set(index)

        self.view.files_label_h2.config(
            text='%d files added' % len(self.model.meta))

    def show_about(self):
        about_window = self.view.AboutDialog(self.view)
        about_window.mainloop()

    def move_previous(self):
        self.view.file_list.cur_index -= 1
        self.view.update_ctrl()

    def move_next(self):
        self.view.file_list.cur_index += 1
        self.view.update_ctrl()


class SettingsWindow(tk.Toplevel):
    def __init__(self, master):
        tk.Toplevel.__init__(self, master)
