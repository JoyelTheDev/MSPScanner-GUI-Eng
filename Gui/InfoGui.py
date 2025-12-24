# -*- coding: UTF-8 -*-
from tkinter import Listbox
from tkinter.messagebox import showinfo

from ttkbootstrap.tooltip import ToolTip
from Gui.Widgets import *


class InfoWindow(Toplevel, Infer):
    """Main information window"""

    def __init__(self, master: Misc, data: ServerInfo):
        from Gui.Widgets import MOTD, Tabs

        super(InfoWindow, self).__init__(master=master)
        self.data = data
        self.load_window_title()
        self.wm_resizable(True, True)

        self.favicon = Label(self)
        self.MOTD = MOTD(self)
        self.tab = Tabs(self)
        self.base_info = BaseInfo(self)
        self.reload_button = Button(self.base_info, text="Refresh Info", command=self.reget_info, style="success")
        self.version_info = VersionInfo(self)

        if self.data.mod_server:
            self.mod_info = ModInfo(self)
            self.mod_info.load_data(self.data)

        self.load_data(data)
        self.pack_widgets()

    def load_data(self, data: ServerInfo):
        if data.has_favicon:
            self.favicon.image_io = BytesIO(data.favicon_data)
        else:
            with open(r"assets\server_icon.png", "rb") as f:
                self.favicon.image_io = BytesIO(f.read())
        self.favicon.image = Image.open(self.favicon.image_io, formats=["PNG"])
        self.favicon.image = self.favicon.image.resize((128, 128))
        self.favicon.favicon = ImageTk.PhotoImage(self.favicon.image)
        self.favicon.configure(image=self.favicon.favicon)
        # Keep favicon reference as self.favicon.image to prevent garbage collection
        self.load_icon(self.favicon.favicon)

        self.data = data
        self.MOTD.load_data(self.data)
        self.base_info.load_data(self.data)
        self.version_info.load_data(self.data)

    def reget_info(self):
        Thread(target=self._reget_info, daemon=True).start()

    def _reget_info(self):
        server_status = Port(self.data.host, self.data.port).get_server_info()
        if server_status["status"] == "offline":
            showinfo("Server is dead, it's all your fault (doge", "Server is offline", parent=self)
        elif server_status["status"] == "error":
            showinfo("Server has some issues: " + server_status["msg"], "Server: ?", parent=self)
        elif server_status["status"] == "online":
            self.load_data(ServerInfo(server_status["info"]))

    def load_icon(self, favicon: PhotoImage):
        """
        Load a PIL.ImageTK.PhotoImage as GUI icon

        Args:
            favicon: A PIL.ImageTK.PhotoImage instance
        """
        self.iconphoto(False, favicon)

    def pack_widgets(self):
        self.favicon.pack_configure()
        self.MOTD.configure(height=2)
        self.MOTD.pack_configure(fill=X)

        self.tab.pack(fill=BOTH, expand=True)
        self.tab.add(self.base_info, text="Basic Info")
        self.reload_button.pack_configure(pady=5)
        self.tab.add(self.version_info, text="Version Info")
        if self.data.mod_server:
            self.tab.add(self.mod_info, text="Mod Info")

    def load_window_title(self):
        text = ""
        for extra in self.data.description_json:
            text += extra["text"]
        self.title(text)


# noinspection PyTypeChecker
class PlayersInfo(Frame, Infer):
    """Player information component"""

    def __init__(self, master: Misc):
        super(PlayersInfo, self).__init__(master)

        self.leave_id = None
        self.motion_id = None
        self.text = Label(self, anchor=CENTER)
        self.player_list = Listbox(self, width=15)
        self.tip = ToolTip(self.player_list, "We can't find anyone on this server :-(", delay=0, alpha=0.8)
        self.text.pack(side=TOP, fill=X)
        self.player_list.pack(side=LEFT, fill=BOTH, expand=True)
        self.data = None
        self.now_item = None
        self.players = {}

    def load_data(self, data: ServerInfo):
        self.data = data

        self.text.configure(text=f"Players: {data.player_online}/{data.player_max}")
        if not config.accumulation_player:
            self.players.clear()
        for player in data.players:
            if player["name"] not in self.players:
                self.players[player["name"]] = player
        self.player_list.delete(0, END)
        for player in self.players.values():
            self.player_list.insert(END, player["name"])
        if len(data.players) > 0:
            self.player_list.unbind_all("<Enter>")
            self.player_list.bind("<Enter>", self.enter)
            self.player_list.bind("<Enter>", self.tip.enter, "+")
            self.player_list.bind("<Button-3>", self.pop_menu)
        else:
            self.tip.hide_tip()

        self.now_item = None

    def enter(self, event: Event):
        item = self.player_list.nearest(event.y)
        if item == -1:
            return
        self.tip.show_tip()
        uuid = self.data.players[item]['id']
        self.tip.toplevel.winfo_children()[0].configure(text="UUID: " + uuid)
        self.now_item = item
        self.leave_id = self.player_list.bind("<Leave>", self.leave, "+")
        self.motion_id = self.player_list.bind("<Motion>", self.update_tip, "+")

    def leave(self, _):
        self.player_list.unbind("<Motion>", self.motion_id)
        self.player_list.bind("<Motion>", self.tip.move_tip)
        self.player_list.unbind("<Leave>", self.leave_id)
        self.player_list.bind("<Leave>", self.tip.leave)

    def update_tip(self, event: Event):
        if self.tip.toplevel is not None:
            item = self.player_list.nearest(event.y)
            if item == -1 or item == self.now_item:
                return
            self.tip.toplevel.winfo_children()[0].configure(text="UUID: " + list(self.players.values())[item]['id'])
            self.now_item = item

    def pop_menu(self, event: Event):
        item = self.player_list.nearest(event.y)
        if item == -1:
            return
        player = list(self.players.values())[item]

        menu = Menu(self.player_list, tearoff=0)
        menu.add_command(label="Copy Name", command=lambda: copy_clipboard(player["name"]))
        menu.add_command(label="Copy UUID", command=lambda: copy_clipboard(player["id"]))
        menu.post(event.x_root, event.y_root)


class BaseInfo(Frame, Infer):
    """Server basic information component"""

    def __init__(self, master: Misc):
        super(BaseInfo, self).__init__(master)
        self.data = None

        self.player_list = PlayersInfo(self)
        self.host = Label(self, anchor=CENTER)
        self.ping = Label(self, anchor=CENTER)
        self.version = Label(self, anchor=CENTER)
        self.host_copy_b = Button(self, text="Copy Address")

        self.pack_widgets()
        if debug:
            self.print_data = Button(self, text="Print Data", command=lambda: print(self.data.parsed_data))
            self.print_data.pack(pady=5)

    def load_data(self, data: ServerInfo):
        self.data = data

        self.player_list.load_data(data)
        self.host.configure(text=f"Address: {data.host}:{data.port}")
        self.ping.configure(text=f"Ping: {data.ping}ms")
        self.version.configure(text=f"Version: {data.version_name}")
        self.host_copy_b.configure(command=lambda: copy_clipboard(f"{data.host}:{data.port}"))

    def pack_widgets(self):
        self.player_list.pack(side=LEFT, fill=BOTH, expand=True)
        self.host.pack()
        self.ping.pack()
        self.version.pack()
        self.host_copy_b.pack()


class VersionInfo(Frame, Infer):
    """Version information component"""

    def __init__(self, master: Misc):
        from Gui.Widgets import MOTD

        super(VersionInfo, self).__init__(master)
        self.data = None
        self.version_name_label_show: bool = config.version_name_label_show

        self.version_name_frame = Frame(self)
        self.version_name_label = Label(self.version_name_frame, anchor=CENTER)
        self.version_name_text = MOTD(self.version_name_frame)
        self.minecraft_version = Label(self, anchor=CENTER)
        self.protocol_version = Label(self, anchor=CENTER)
        self.major_name = Label(self, anchor=CENTER)
        self.version_type = Label(self, anchor=CENTER)

        self.bind_tip()
        self.pack_widgets()

    def bind_tip(self):
        tips = [(self.version_name_label, "Server version name (server response)\nSome servers modify this part"),
                (self.version_name_text, "Server version name (server response)\nSome servers modify this part"),
                (self.minecraft_version, "Server version name (common naming convention)"),
                (self.protocol_version, "Server protocol version (almost every MC version has different protocol version)"),
                (self.major_name, "Major version (which major version this server belongs to)"),
                (self.version_type, "Server version type")]
        for tip in tips:
            ToolTip(tip[0], tip[1], delay=0, alpha=0.8)

    def pack_widgets(self):
        self.version_name_frame.pack()
        self.version_name_label.pack(side=LEFT)
        if not self.version_name_label_show:
            self.version_name_text.configure(height=1, width=20)
            self.version_name_text.pack(side=LEFT)
        self.minecraft_version.pack()
        self.protocol_version.pack()
        self.major_name.pack()
        self.version_type.pack()

    def load_data(self, data: ServerInfo):
        self.data = data

        if "§" in data.version_name:
            description_json = DescriptionParser.format_chars_to_extras(data.version_name)
        else:
            description_json = [{"text": data.version_name}]
        self.version_name_label.configure(text="Version Name: ")
        if self.version_name_label_show:
            self.version_name_label.configure(text=f"Version Name: {data.version_name}")
        self.version_name_text.load_motd(description_json)
        self.minecraft_version.configure(text=f"Official Version: {data.protocol_name}")
        self.protocol_version.configure(text=f"Protocol Version: {data.protocol_version}")
        self.major_name.configure(text=f"Major Version: {data.protocol_major_name}")

        if data.version_type == "release":
            self.version_type.configure(text="Version Type: Release")
        elif data.version_type == "snapshot":
            self.version_type.configure(text=f"Version Type: Snapshot")
        else:
            self.version_type.configure(text=f"Version Type (undetected): {data.version_type}")


class ModInfo(Frame, Infer):
    """Mod information component"""

    def __init__(self, master: Misc):
        super(ModInfo, self).__init__(master)

        self.data = None
        self.mod_pack_info = Label(self)
        self.mod_list = Treeview(self, show=HEADINGS, columns=["mod", "version"])
        self.mod_info = Frame(self)

        self.pack_widgets()

    def pack_widgets(self):
        self.mod_list.heading("mod", text="Mod Name")
        self.mod_list.heading("version", text="Version")
        self.mod_list.bind("<Button-1>", self.select_mod)

        self.mod_pack_info.pack_configure(fill=X)
        self.mod_list.pack_configure(fill=BOTH, expand=True, side=LEFT)
        self.mod_info.pack_configure(fill=BOTH, expand=True, side=LEFT)

    def load_data(self, data: ServerInfo):
        print("Mod Pack Server Info:", data.mod_pack_info)
        self.data = data
        self.mod_list.delete(*self.mod_list.get_children())
        for mod in data.mod_list.items():
            if "OHNOES" in mod[1]:
                mod = (mod[0], "Unknown")  # Fixed the "OHNOES" face issue when loading old scan records
            self.mod_list.insert("", END, values=mod)

    def select_mod(self, event: Event):
        item_id = self.identify(event.x, event.y)
        if item_id == "border":
            return
        print("PASS ITEM:", item_id)
        name, version = self.mod_list.get_children(item_id)
        print("Mod Name:", name, "  ", "Version:", version)
