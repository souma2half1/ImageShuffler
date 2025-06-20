"""ImageShuffler GUI application.

This tool allows users to select multiple source folders and a single
 destination folder, choose how many images to move from each source
 folder, and move them either in file name order or randomly.

Supported image extensions: .jpg, .jpeg, .png, .webp
"""

import os
import random
import shutil
from glob import glob
from tkinter import (
    Tk, Frame, Label, Button, Entry, filedialog, StringVar,
    IntVar, Radiobutton, Scrollbar, Text, ttk, END, DISABLED, NORMAL
)

IMAGE_EXTS = {'.jpg', '.jpeg', '.png', '.webp'}


def is_image_file(path: str) -> bool:
    return os.path.splitext(path)[1].lower() in IMAGE_EXTS


def list_images(directory: str) -> list[str]:
    files = [f for f in glob(os.path.join(directory, '*')) if is_image_file(f)]
    files.sort()
    return files


class SourceRow:
    def __init__(self, master: Frame, path: str, remove_callback):
        self.master = master
        self.path = path
        self.remove_callback = remove_callback
        images = list_images(path)
        self.available = len(images)

        self.path_label = Label(master, text=path)
        self.count_label = Label(master, text=str(self.available))
        self.amount_var = IntVar(value=self.available)
        self.amount_entry = Entry(master, width=5, textvariable=self.amount_var)
        self.remove_btn = Button(
            master, text="取り消し", command=self.remove
        )

    def grid(self, row: int):
        self.path_label.grid(row=row, column=0, sticky='w')
        self.count_label.grid(row=row, column=1)
        self.amount_entry.grid(row=row, column=2)
        self.remove_btn.grid(row=row, column=3)

    def remove(self):
        self.path_label.destroy()
        self.count_label.destroy()
        self.amount_entry.destroy()
        self.remove_btn.destroy()
        self.remove_callback(self)

    def get_amount(self) -> int:
        try:
            value = int(self.amount_var.get())
        except ValueError:
            value = 0
        return max(0, min(value, self.available))


class ImageShufflerGUI:
    def __init__(self, root: Tk):
        self.root = root
        self.root.title("ImageShuffler")

        self.sources_frame = Frame(root)
        self.sources_frame.pack(fill='x', padx=5, pady=5)

        headers = ['フォルダパス', '移動可能枚数', '移動枚数', '取り消し']
        for i, h in enumerate(headers):
            Label(self.sources_frame, text=h, font=('Arial', 10, 'bold')).grid(row=0, column=i)

        self.rows: list[SourceRow] = []

        ops = Frame(root)
        ops.pack(fill='x', padx=5, pady=5)

        Button(ops, text="対象フォルダを追加", command=self.add_folder).grid(row=0, column=0, padx=5)
        Button(ops, text="移動先フォルダを選択", command=self.select_dest).grid(row=0, column=1, padx=5)

        self.order_var = StringVar(value='name')
        Radiobutton(ops, text="ファイル名順", variable=self.order_var, value='name').grid(row=1, column=0)
        Radiobutton(ops, text="ランダム", variable=self.order_var, value='random').grid(row=1, column=1)

        Button(ops, text="実行", command=self.execute).grid(row=2, column=0, pady=5)

        self.total_label = Label(root, text="合計移動枚数: 0")
        self.total_label.pack(anchor='w', padx=5)

        log_frame = Frame(root)
        log_frame.pack(fill='both', expand=True, padx=5, pady=5)
        self.log_text = Text(log_frame, height=10)
        self.log_text.pack(side='left', fill='both', expand=True)
        scrollbar = Scrollbar(log_frame, command=self.log_text.yview)
        scrollbar.pack(side='right', fill='y')
        self.log_text.config(yscrollcommand=scrollbar.set)

        self.dest_dir: str | None = None

    def add_folder(self):
        path = filedialog.askdirectory()
        if not path:
            return
        if any(r.path == path for r in self.rows):
            return
        if self.dest_dir and os.path.abspath(path) == os.path.abspath(self.dest_dir):
            return
        row = SourceRow(self.sources_frame, path, self.remove_row)
        self.rows.append(row)
        row.grid(len(self.rows))
        self.update_total()

    def remove_row(self, row: SourceRow):
        if row in self.rows:
            self.rows.remove(row)
            self.regrid_rows()
            self.update_total()

    def regrid_rows(self):
        for idx, row in enumerate(self.rows, start=1):
            row.grid(idx)

    def select_dest(self):
        path = filedialog.askdirectory()
        if path:
            self.dest_dir = path

    def execute(self):
        if not self.dest_dir:
            self.log("移動先フォルダを選択してください")
            return
        for row in self.rows:
            self.move_from_row(row)
        self.update_total()
        self.log("--- 完了 ---")

    def move_from_row(self, row: SourceRow):
        images = list_images(row.path)
        amount = row.get_amount()
        if amount == 0:
            self.log(f"{row.path}: 移動枚数が0のためスキップ")
            return
        if self.order_var.get() == 'random':
            random.shuffle(images)
        selected = images[:amount]
        moved = 0
        for img in selected:
            dest_name = os.path.basename(img)
            dest_path = os.path.join(self.dest_dir, dest_name)
            base, ext = os.path.splitext(dest_name)
            i = 1
            while os.path.exists(dest_path):
                dest_name = f"{base}_{i}{ext}"
                dest_path = os.path.join(self.dest_dir, dest_name)
                i += 1
            try:
                shutil.move(img, dest_path)
                moved += 1
            except Exception as e:
                self.log(f"{img} の移動に失敗: {e}")
        self.log(f"{row.path}: {moved}/{amount} 枚を移動")

    def update_total(self):
        total = sum(r.get_amount() for r in self.rows)
        self.total_label.config(text=f"合計移動枚数: {total}")

    def log(self, message: str):
        self.log_text.configure(state=NORMAL)
        self.log_text.insert(END, message + "\n")
        self.log_text.configure(state=DISABLED)
        self.log_text.see(END)


def main():
    root = Tk()
    gui = ImageShufflerGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
