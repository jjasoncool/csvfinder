import os
import tkinter as tk
from tkinter import filedialog, ttk
import pandas as pd
import csv
import threading

# 自訂分析模組
import analysis


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
        self.folder_path = ""
        self.selected_option = tk.StringVar(value="SwathAngle")
        # 添加錯誤窗口狀態標誌
        self.error_window_open = False
        self.df = None
        # treeview columns
        self.columns = None
        self.create_widgets()

    # 主要設計UI的位置
    def create_widgets(self):
        # 匯入檔案的按鈕和路徑顯示在同一列上
        top_frame = tk.Frame(self.root)
        top_frame.pack(pady=10, padx=10, fill="x")

        self.label = tk.Label(top_frame, text="No folder selected", anchor="w")
        self.label.pack(side="left", padx=10, fill="x", expand=True)

        self.browse_button = tk.Button(
            top_frame, text="Browse Folder", command=self.browse_folder
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

        # 深度異常值複選框
        self.extra_options_frame = tk.Frame(self.root)

        self.depth_anomaly_var = tk.BooleanVar()
        self.depth_anomaly_check = tk.Checkbutton(
            self.extra_options_frame,
            text="列出 Depth 異常值",
            variable=self.depth_anomaly_var,
        )
        self.depth_anomaly_check.pack(pady=5)

        # THU 範圍
        self.thu_range_frame = RangeFrame(
            self.extra_options_frame, text="THU range", error_callback=self.show_error
        )
        self.thu_range_frame.pack(pady=5)

        # TVU 範圍
        self.tvu_range_frame = RangeFrame(
            self.extra_options_frame, text="TVU range", error_callback=self.show_error
        )
        self.tvu_range_frame.pack(pady=5)

        self.analyze_button = tk.Button(self.root, text="Analyze", command=lambda: threading.Thread(target=self.analyze_and_show_data).start())
        self.analyze_button.pack(pady=10)

        self.progress = ttk.Progressbar(self.root, orient=tk.HORIZONTAL, length=300, mode='determinate')
        self.progress.pack(pady=10, fill='x', expand=True)

        self.result_tree = None

    def update_ui(self, value):
        if value == "TPU":
            self.extra_options_frame.pack(pady=5, before=self.analyze_button)
        else:
            self.extra_options_frame.pack_forget()

    def browse_folder(self):
        self.folder_path = filedialog.askdirectory()
        self.label.config(text=f"Selected folder: {self.folder_path}")

    def analyze_and_show_data(self):
        self.root.after(0, self.destroy_result_tree)
        try:
            files = [os.path.join(self.folder_path, f) for f in os.listdir(self.folder_path) if f.endswith(('.csv', '.txt')) and not f.startswith('error_')]

            all_results = []
            threads = []

            for file_path in files:
                thread = threading.Thread(target=self.process_file, args=(file_path, all_results))
                thread.start()
                threads.append(thread)

            for thread in threads:
                thread.join()

            if all_results:
                final_results = pd.concat(all_results).drop_duplicates().reset_index(drop=True)
                print("final results:", final_results)
                self.update_progress(100, complete=True)
                if self.columns is not None:
                    columns = self.columns
                else:
                    columns = ['Filename'] + final_results.columns.tolist()
                self.show_treeview(final_results, columns)
            else:
                self.update_progress(100, complete=True)
                self.show_error("No valid files processed", None)
        except Exception as e:
            self.root.after(0, self.show_error, str(e), None)


    def process_file(self, file_path, all_results):
        try:
        # 存儲加載的資料框
            df = self.load_data(file_path)
            params = self.collect_params()
            results, columns = analysis.analyze_data(df, params)
            print("result:", results)
            # 新增檔案名稱到每一行的第一列
            results.insert(0, 'Filename', os.path.basename(file_path))

            # 檢查結果是否為空或包含特定消息
            if not results.empty and not (results.shape[1] == 2 and 'Message' in results.columns and results.at[0, 'Message'] == '查無異常資料'):
                # 保存新的文件
                new_file_path = os.path.join(os.path.dirname(file_path), 'error_' + os.path.basename(file_path))
                results.to_csv(new_file_path, index=False)

            all_results.append(results)
            if self.columns is None:
                self.columns = ['Filename'] + columns

        except Exception as e:
            self.root.after(0, self.show_error, f"Error processing file {file_path}:\n {str(e)}", None)

    def destroy_result_tree(self):
        if self.result_tree:
            self.result_tree.destroy()
            self.result_tree = None

    def load_data(self, file_path):
        try:
            chunks = []
            chunk_size = 10000
            total_rows = 0
            if file_path.endswith(".csv"):
                total_size = sum(1 for _ in open(file_path))
                for chunk in pd.read_csv(file_path, header=None, chunksize=chunk_size, low_memory=False):
                    chunks.append(chunk)
                    total_rows += len(chunk)
                    self.update_progress(total_rows, total_size)
            elif file_path.endswith(".txt"):
                with open(file_path, "r") as file:
                    sample = file.read(1024)
                    sniffer = csv.Sniffer()
                    delimiter = sniffer.sniff(sample).delimiter
                total_size = sum(1 for _ in open(file_path))
                for chunk in pd.read_csv(file_path, delimiter=delimiter, header=None, chunksize=chunk_size, low_memory=False):
                    chunks.append(chunk)
                    total_rows += len(chunk)
                    self.update_progress(total_rows, total_size)
            df = pd.concat(chunks, ignore_index=True)
            return df

        except Exception as e:
            self.show_error(e, None)

    def update_progress(self, value, total_size=None, complete=False):
        if complete:
            self.root.after(0, self.progress.configure, {'value': 100, 'maximum': 100})
        else:
            percent = (value / total_size) * 100 if total_size else value
            self.root.after(0, self.progress.configure, {'value': percent, 'maximum': 100})

    # 把UI上面的選擇項目轉成字典
    def collect_params(self):
        params = {
            "selected_option": self.selected_option.get(),
            "depth_anomaly": self.depth_anomaly_var.get(),
            "thu_range": (
                self.thu_range_frame.start_entry.var.get(),
                self.thu_range_frame.end_entry.var.get()
            ) if self.thu_range_frame.var.get() else (None, None),
            "tvu_range": (
                self.tvu_range_frame.start_entry.var.get(),
                self.tvu_range_frame.end_entry.var.get()
            ) if self.tvu_range_frame.var.get() else (None, None)
        }
        return params

    def show_treeview(self, results, columns):
        if self.result_tree:
            self.result_tree.destroy()

        self.result_tree = ttk.Treeview(self.root)
        self.result_tree["columns"] = columns
        self.result_tree["show"] = "headings"

        for col in self.result_tree["columns"]:
            self.result_tree.heading(col, text=col)
            self.result_tree.column(col, width=100)

        for index, row in results.iterrows():
            self.result_tree.insert("", "end", values=tuple(row))

        for col in self.result_tree["columns"]:
            # 忽略 NaN 值
            valid_lengths = results[col].dropna().astype(str).map(len)
            if not valid_lengths.empty:
                max_len = max(valid_lengths.max(), len(col)) + 2
            else:
                max_len = len(col) + 2
            self.result_tree.column(col, width=max_len * 10, anchor=tk.CENTER)

        self.result_tree.pack(pady=10)

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
            widget.focus_set()  # 重新設置焦點到觸發事件的控件上
        self.reset_all_ranges()

    def reset_all_ranges(self):
        if hasattr(self, 'thu_range_frame'):
            self.thu_range_frame.reset_validation()
        if hasattr(self, 'tvu_range_frame'):
            self.tvu_range_frame.reset_validation()


if __name__ == "__main__":
    root = tk.Tk()
    app = CSVAnalyzer(root)
    root.mainloop()
