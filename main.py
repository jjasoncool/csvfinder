import tkinter as tk
from tkinter import filedialog
from tkinter import ttk
import pandas as pd

class CSVAnalyzer:
    def __init__(self, root):
        self.root = root
        self.root.title("CSV Analyzer")
        self.file_path = ""
        self.selected_option = tk.StringVar(value="SwathAngle")
        self.create_widgets()

    def create_widgets(self):
        # 匯入檔案的按鈕和路徑顯示在同一列上
        top_frame = tk.Frame(self.root)
        top_frame.pack(pady=10, padx=10, fill='x')

        self.label = tk.Label(top_frame, text="No file selected", anchor='w')
        self.label.pack(side='left', padx=10, fill='x', expand=True)

        self.browse_button = tk.Button(top_frame, text="Browse CSV/TXT", command=self.browse_csv)
        self.browse_button.pack(side='left')

        # 選擇框的標籤和選擇框在同一列上
        selector_frame = tk.Frame(self.root)
        selector_frame.pack(pady=5)

        self.selector_label = tk.Label(selector_frame, text="Function Selection:")
        self.selector_label.pack(side='left', padx=5)

        self.selector = tk.OptionMenu(selector_frame, self.selected_option, "SwathAngle", "TPU", command=self.update_ui)
        self.selector.pack(side='left', padx=5)

        self.column_label = tk.Label(self.root, text="Enter Column Index:")
        self.column_label.pack(pady=5)

        self.column_entry = tk.Entry(self.root)
        self.column_entry.pack(pady=5)

        # 额外选项，仅在选择 "TPU" 时显示
        self.extra_options_frame1 = tk.Frame(self.root)
        self.extra_options_frame2 = tk.Frame(self.root)
        self.extra_options_frame3 = tk.Frame(self.root)

        self.depth_anomaly_var = tk.BooleanVar()
        self.depth_anomaly_check = tk.Checkbutton(self.extra_options_frame1, text="列出 Depth 異常值", variable=self.depth_anomaly_var)
        self.depth_anomaly_check.pack(anchor='w')

        self.tpu_range_var = tk.BooleanVar()
        self.tpu_range_check = tk.Checkbutton(self.extra_options_frame2, text="TPU range", variable=self.tpu_range_var)
        self.tpu_range_check.pack(anchor='w')
        self.tpu_range_start = tk.Entry(self.extra_options_frame2, width=10)
        self.tpu_range_start.pack(side='left')
        self.tpu_range_label = tk.Label(self.extra_options_frame2, text="~")
        self.tpu_range_label.pack(side='left')
        self.tpu_range_end = tk.Entry(self.extra_options_frame2, width=10)
        self.tpu_range_end.pack(side='left')

        self.thu_range_var = tk.BooleanVar()
        self.thu_range_check = tk.Checkbutton(self.extra_options_frame3, text="THU range", variable=self.thu_range_var)
        self.thu_range_check.pack(anchor='w')
        self.thu_range_start = tk.Entry(self.extra_options_frame3, width=10)
        self.thu_range_start.pack(side='left')
        self.thu_range_label = tk.Label(self.extra_options_frame3, text="~")
        self.thu_range_label.pack(side='left')
        self.thu_range_end = tk.Entry(self.extra_options_frame3, width=10)
        self.thu_range_end.pack(side='left')

        self.analyze_button = tk.Button(self.root, text="Analyze", command=self.analyze_csv)
        self.analyze_button.pack(pady=10)

        self.preview_tree = None
        self.result_tree = None

    def browse_csv(self):
        self.file_path = filedialog.askopenfilename(filetypes=[("CSV and TXT files", "*.csv *.txt")])
        self.label.config(text=f"Selected file: {self.file_path}")
        self.show_preview()

    def update_ui(self, value):
        if value == "TPU":
            self.extra_options_frame1.pack(pady=5, before=self.column_label)
            self.extra_options_frame2.pack(pady=5, before=self.column_label)
            self.extra_options_frame3.pack(pady=5, before=self.column_label)
        else:
            self.extra_options_frame1.pack_forget()
            self.extra_options_frame2.pack_forget()
            self.extra_options_frame3.pack_forget()

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
            self.show_error(e)

    def analyze_csv(self):
        if not self.file_path:
            self.show_error("No file selected. Please browse and select a CSV or TXT file.")
            return

        if self.result_tree:
            self.result_tree.destroy()

        try:
            col_index = int(self.column_entry.get())
            df = self.load_data(self.file_path)

            max_value = df.iloc[:, col_index].max()
            min_value = df.iloc[:, col_index].min()
            max_row = df.iloc[:, col_index].idxmax()
            min_row = df.iloc[:, col_index].idxmin()

            self.result_tree = ttk.Treeview(self.root)
            self.result_tree["columns"] = ["Description", "Value"]
            self.result_tree["show"] = "headings"

            for col in self.result_tree["columns"]:
                self.result_tree.heading(col, text=col)
                self.result_tree.column(col, width=200)

            self.result_tree.insert("", "end", values=("Column Index", col_index))
            self.result_tree.insert("", "end", values=("Max Value", max_value))
            self.result_tree.insert("", "end", values=("Max Value Row", max_row + 1))
            self.result_tree.insert("", "end", values=("Max Value Data", df.iloc[max_row].to_dict()))
            self.result_tree.insert("", "end", values=("Min Value", min_value))
            self.result_tree.insert("", "end", values=("Min Value Row", min_row + 1))
            self.result_tree.insert("", "end", values=("Min Value Data", df.iloc[min_row].to_dict()))

            self.result_tree.pack(pady=10)
        except Exception as e:
            self.show_error(e)

    def load_data(self, file_path):
        try:
            if file_path.endswith('.csv'):
                df = pd.read_csv(file_path)
            elif file_path.endswith('.txt'):
                with open(file_path, 'r') as file:
                    first_line = file.readline()
                    delimiter = ',' if first_line.count(',') > first_line.count('\t') else '\t'
                df = pd.read_csv(file_path, delimiter=delimiter)
            return df
        except Exception as e:
            self.show_error(e)

    def show_error(self, error_message):
        if self.result_tree:
            self.result_tree.destroy()
        self.result_tree = ttk.Treeview(self.root)
        self.result_tree.insert("", "end", text=f"Error: {error_message}")
        self.result_tree.pack(pady=10)

if __name__ == "__main__":
    root = tk.Tk()
    app = CSVAnalyzer(root)
    root.mainloop()
