import tkinter as tk
from tkinter import filedialog
from tkinter import ttk
import pandas as pd


class NumericEntry(tk.Entry):
    def __init__(self, master=None, **kwargs):
        self.var = tk.StringVar()
        kwargs['textvariable'] = self.var
        super().__init__(master, **kwargs)
        validate_command = (self.register(self.validate_input), '%P')
        self.config(validate='key', validatecommand=validate_command)
        self.configure(width=4)

    def validate_input(self, proposed_value):
        if proposed_value == "" or self.is_valid_number(proposed_value):
            return True
        else:
            self.bell()  # 發出警報音
            return False

    @staticmethod
    def is_valid_number(value):
        try:
            float(value)  # 嘗試將值轉換為浮點數
            return True
        except ValueError:
            return False


class RangeFrame(tk.Frame):
    def __init__(self, master=None, text="", error_callback=None, **kwargs):
        super().__init__(master, **kwargs)
        self.error_callback = error_callback
        self.var = tk.BooleanVar()
        self.check = tk.Checkbutton(
            self, text=text, variable=self.var, command=self.toggle_state
        )
        self.start_entry = NumericEntry(self)
        self.end_entry = NumericEntry(self)
        self.label = tk.Label(self, text="~")

        self.check.pack(side="left")
        self.start_entry.pack(side="left", padx=5)
        self.label.pack(side="left")
        self.end_entry.pack(side="left", padx=5)

        self.start_entry.bind("<FocusOut>", self.validate_range)
        self.end_entry.bind("<FocusOut>", self.validate_range)

        self.toggle_state()

    def toggle_state(self):
        state = "normal" if self.var.get() else "disabled"
        self.start_entry.config(state=state)
        self.end_entry.config(state=state)
        if state == "disabled":
            self.start_entry.var.set("")
            self.end_entry.var.set("")

    def validate_range(self, event=None):
        start = self.start_entry.var.get()
        end = self.end_entry.var.get()
        if start and end:
            try:
                if float(start) > float(end):
                    self.show_error(
                        "Start value must be less than or equal to end value",
                        event.widget
                    )
            except ValueError:
                self.show_error("Invalid numeric value", event.widget)

    def show_error(self, message, widget):
        self.start_entry.config(validate="none")
        self.end_entry.config(validate="none")
        if self.error_callback:
            self.error_callback(message, widget)

    def reset_validation(self):
        self.start_entry.config(validate="key")
        self.end_entry.config(validate="key")


class CSVAnalyzer:
    def __init__(self, root):
        self.root = root
        self.root.title("CSV Analyzer")
        self.file_path = ""
        self.selected_option = tk.StringVar(value="SwathAngle")
        # 添加錯誤窗口狀態標誌
        self.error_window_open = False
        self.create_widgets()

    def create_widgets(self):
        # 匯入檔案的按鈕和路徑顯示在同一列上
        top_frame = tk.Frame(self.root)
        top_frame.pack(pady=10, padx=10, fill="x")

        self.label = tk.Label(top_frame, text="No file selected", anchor="w")
        self.label.pack(side="left", padx=10, fill="x", expand=True)

        self.browse_button = tk.Button(
            top_frame, text="Browse CSV/TXT", command=self.browse_csv
        )
        self.browse_button.pack(side="left")

        # 選擇框的標籤和選擇框在同一列上
        selector_frame = tk.Frame(self.root)
        selector_frame.pack(pady=5)

        self.selector_label = tk.Label(selector_frame, text="Function Selection:")
        self.selector_label.pack(side="left", padx=5)

        self.selector = tk.OptionMenu(
            selector_frame,
            self.selected_option,
            "SwathAngle",
            "TPU",
            command=self.update_ui,
        )
        self.selector.pack(side="left", padx=5)

        self.column_label = tk.Label(self.root, text="Enter Column Index:")
        self.column_label.pack(pady=5)

        self.column_entry = tk.Entry(self.root)
        self.column_entry.pack(pady=5)

        # 深度異常值複選框
        self.extra_options_frame = tk.Frame(self.root)

        self.depth_anomaly_var = tk.BooleanVar()
        self.depth_anomaly_check = tk.Checkbutton(
            self.extra_options_frame,
            text="列出 Depth 異常值",
            variable=self.depth_anomaly_var,
        )
        self.depth_anomaly_check.pack(pady=5)

        # TPU 範圍
        self.tpu_range_frame = RangeFrame(
            self.extra_options_frame, text="TPU range", error_callback=self.show_error
        )
        self.tpu_range_frame.pack(pady=5)

        # THU 範圍
        self.thu_range_frame = RangeFrame(
            self.extra_options_frame, text="THU range", error_callback=self.show_error
        )
        self.thu_range_frame.pack(pady=5)

        self.analyze_button = tk.Button(self.root, text="Analyze")
        self.analyze_button.pack(pady=10)

        self.preview_tree = None
        self.result_tree = None

    def update_ui(self, value):
        if value == "TPU":
            self.extra_options_frame.pack(pady=5, before=self.column_label)
        else:
            self.extra_options_frame.pack_forget()

    def browse_csv(self):
        self.file_path = filedialog.askopenfilename(
            filetypes=[("CSV and TXT files", "*.csv *.txt")]
        )
        self.label.config(text=f"Selected file: {self.file_path}")
        self.show_preview()

    def show_preview(self):
        if not self.file_path:
            return

        if self.preview_tree:
            self.preview_tree.destroy()

        try:
            df = self.load_data(self.file_path)
            preview = df.head()

            self.preview_tree = ttk.Treeview(self.root)
            self.preview_tree["columns"] = list(preview.columns)
            self.preview_tree["show"] = "headings"

            for col in self.preview_tree["columns"]:
                self.preview_tree.heading(col, text=col)
                self.preview_tree.column(col, width=100)

            for index, row in preview.iterrows():
                self.preview_tree.insert("", "end", values=list(row))

            self.preview_tree.pack(pady=10)
        except Exception as e:
            self.show_error(e, None)

    def load_data(self, file_path):
        try:
            if file_path.endswith(".csv"):
                df = pd.read_csv(file_path)
            elif file_path.endswith(".txt"):
                with open(file_path, "r") as file:
                    first_line = file.readline()
                    delimiter = (
                        "," if first_line.count(",") > first_line.count("\t") else "\t"
                    )
                df = pd.read_csv(file_path, delimiter=delimiter)
            return df
        except Exception as e:
            self.show_error(e, None)

    def show_error(self, error_message, widget):
        if not self.error_window_open:  # 檢查是否已有錯誤窗口打開
            self.error_window_open = True  # 標記錯誤窗口已打開
            error_window = tk.Toplevel(self.root)
            error_window.title("Error")
            tk.Label(error_window, text=error_message).pack(pady=10, padx=10)
            tk.Button(
                error_window, text="Close", command=lambda: self.close_error_window(error_window, widget)
            ).pack(pady=5)
            error_window.focus_force()  # 強制獲取焦點
            error_window.grab_set()    # 讓窗口模態化(點不到主視窗)

    def close_error_window(self, window, widget):
        window.destroy()
        self.error_window_open = False  # 重置錯誤窗口標誌
        if widget:
            widget.focus_set()  # 重新设置焦点到触发事件的控件上
        self.reset_all_ranges()

    def reset_all_ranges(self):
        if hasattr(self, 'tpu_range_frame'):
            self.tpu_range_frame.reset_validation()
        if hasattr(self, 'thu_range_frame'):
            self.thu_range_frame.reset_validation()


if __name__ == "__main__":
    root = tk.Tk()
    app = CSVAnalyzer(root)
    root.mainloop()
