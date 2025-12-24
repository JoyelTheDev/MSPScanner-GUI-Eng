from ttkbootstrap.tooltip import ToolTip
from Gui.Widgets import *


class PortsHotView(Frame):
    def __init__(self, master: Misc):
        super(PortsHotView, self).__init__(master, width=700, height=375)

        self.main_canvas = Canvas(self, width=700, height=375)
        self.ports_tip = ToolTip(self.main_canvas, delay=0)
        self.last_lines = []
        self.now_lines = []

        self.record_process_lock = Lock()
        self.draw_lock = Lock()
        self.draw_timer = time()
        self.ports_record: Dict[int, bool] = {i: False for i in range(1, 65536)}
        self.resized = [0 for _ in range(700)]

        self.main_canvas.pack(fill=BOTH, expand=YES)

        self.main_canvas.bind("<Configure>", self.draw)
        self.main_canvas.bind("<Motion>", self.mouse_move, add="+")

        self.draw()

    def reset_view(self) -> None:
        with self.record_process_lock:
            self.ports_record: Dict[int, bool] = {i: False for i in range(1, 65536)}
        self.draw()

    def callback(self, port: int) -> None:
        """
        Record this port's server existence on the heatmap
        :return: None
        """
        with self.record_process_lock:
            self.ports_record[port] = True
        self.draw()

    def draw(self, event=None) -> None:
        """
        Draw the heatmap
        :return: None
        """
        if not event:
            if not (time() - self.draw_timer) > 0.8:
                return
        with self.draw_lock:
            width = self.main_canvas.winfo_width()
            if width == 1:
                width = self.master.winfo_width()
            with self.record_process_lock:
                self.resized = self.resize_data(list(self.ports_record.values()), width // 2)
            for i in range(len(self.resized)):
                length = self.resized[i]
                self.now_lines.append(
                    self.main_canvas.create_rectangle(i * 2, 0,
                                                      i * 2 + 2, length * 5,
                                                      fill="#FFFF00",
                                                      width=0))
            self.main_canvas.delete(*self.last_lines)
            self.last_lines = self.now_lines.copy()
            self.now_lines.clear()
            self.draw_timer = time()

    def mouse_move(self, event: Event) -> None:
        if not self.ports_tip.toplevel:
            return
        index = int(event.x / self.main_canvas.winfo_width() * len(self.resized))
        group_counts = self.main_canvas.winfo_width() // 2
        group_size = 65535 // group_counts

        with self.record_process_lock:
            message = \
                f"Port range: {index * group_size}-{(index + 1) * group_size}\n" \
                f"Server count: {self.resized[index]}\n"
        tip_label_widget: Label = self.ports_tip.toplevel.winfo_children()[0]
        tip_label_widget.configure(text=message)

    @staticmethod
    def resize_data(data: List[int], counts: int) -> List[int]:
        data_2d: List[List[int]] = []
        group_size = len(data) // counts
        for i in range(counts - 1):
            data_2d.append(data[i * group_size:(i + 1) * group_size])
        data_2d.append(data[(counts - 1) * group_size:])
        data_resized: List[int] = [sum(i) for i in data_2d]
        return data_resized
