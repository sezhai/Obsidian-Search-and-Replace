#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path
import threading

class ObsidianReplacerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Obsidian 笔记批量替换工具")
        self.root.geometry("600x480")
        self.root.minsize(550, 450)
        
        # 变量绑定
        self.dir_path = tk.StringVar()
        self.old_val_var = tk.StringVar()
        self.new_val_var = tk.StringVar()
        self.scope_var = tk.StringVar(value='1') # 默认仅属性区
        
        self.create_widgets()

    def create_widgets(self):
        # ================= 1. 目录选择区 =================
        frame_dir = tk.LabelFrame(self.root, text=" 1. 目标文件夹 (包含所有子文件夹) ", padx=10, pady=10)
        frame_dir.pack(fill="x", padx=15, pady=5)
        
        tk.Entry(frame_dir, textvariable=self.dir_path, state="readonly").pack(side="left", fill="x", expand=True, padx=(0, 10))
        tk.Button(frame_dir, text="浏览...", command=self.browse_folder, bg="#f0f0f0").pack(side="right")

        # ================= 2. 作用范围选择 =================
        frame_scope = tk.LabelFrame(self.root, text=" 2. 生效范围 ", padx=10, pady=5)
        frame_scope.pack(fill="x", padx=15, pady=5)
        
        ttk.Radiobutton(frame_scope, text="仅限笔记属性区", variable=self.scope_var, value='1').pack(side="left", padx=10)
        ttk.Radiobutton(frame_scope, text="仅限笔记正文区", variable=self.scope_var, value='2').pack(side="left", padx=10)
        ttk.Radiobutton(frame_scope, text="全局无差别替换", variable=self.scope_var, value='3').pack(side="left", padx=10)

        # ================= 3. 参数输入区 =================
        frame_inputs = tk.LabelFrame(self.root, text=" 3. 替换内容 ", padx=10, pady=10)
        frame_inputs.pack(fill="x", padx=15, pady=5)
        
        tk.Label(frame_inputs, text="查找:", width=12, anchor="e").grid(row=0, column=0, pady=5, padx=5)
        tk.Entry(frame_inputs, textvariable=self.old_val_var, width=45).grid(row=0, column=1, pady=5, sticky="w")
        
        tk.Label(frame_inputs, text="替换:", width=12, anchor="e").grid(row=1, column=0, pady=5, padx=5)
        tk.Entry(frame_inputs, textvariable=self.new_val_var, width=45).grid(row=1, column=1, pady=5, sticky="w")

        # ================= 4. 执行与日志区 =================
        self.btn_execute = tk.Button(self.root, text="▶ 开始批量替换", command=self.start_execution, bg="#4CAF50", fg="white", font=("Microsoft YaHei", 10, "bold"), pady=5)
        self.btn_execute.pack(fill="x", padx=15, pady=10)
        
        frame_log = tk.LabelFrame(self.root, text=" 执行日志 ", padx=5, pady=5)
        frame_log.pack(fill="both", expand=True, padx=15, pady=(0, 15))
        
        self.txt_log = tk.Text(frame_log, state="disabled", bg="#1e1e1e", fg="#d4d4d4", font=("Consolas", 9))
        self.txt_log.pack(side="left", fill="both", expand=True)
        
        scrollbar = tk.Scrollbar(frame_log, command=self.txt_log.yview)
        scrollbar.pack(side="right", fill="y")
        self.txt_log.config(yscrollcommand=scrollbar.set)

    def browse_folder(self):
        folder = filedialog.askdirectory(title="选择 Obsidian 笔记位置")
        if folder:
            self.dir_path.set(folder)

    def log(self, message):
        """线程安全的日志输出"""
        self.txt_log.config(state="normal")
        self.txt_log.insert(tk.END, message + "\n")
        self.txt_log.see(tk.END)
        self.txt_log.config(state="disabled")

    def process_file(self, filepath: Path, old_val: str, new_val: str, scope: str) -> bool:
        """底层替换逻辑：利用状态机区分属性区与正文区"""
        try:
            content = filepath.read_text(encoding='utf-8')
            original_content = content
        except Exception:
            return False

        lines = content.split('\n')
        escaped_old = re.escape(old_val)
        
        in_frontmatter = False
        frontmatter_ended = False

        # 检测文件首行是否存在 YAML 区块边界
        if lines and lines[0].strip() == '---':
            in_frontmatter = True
        else:
            frontmatter_ended = True # 无属性区，全部视为正文

        for i in range(len(lines)):
            # 处理 YAML 边界逻辑
            if i == 0 and in_frontmatter:
                continue # 跳过首行的 '---'
                
            if in_frontmatter and lines[i].strip() == '---':
                in_frontmatter = False
                frontmatter_ended = True
                continue # 跳过闭合行的 '---'
                
            is_current_line_frontmatter = in_frontmatter
            is_current_line_body = frontmatter_ended

            # 根据用户选择的范围，判断当前行是否应该被处理
            should_process = False
            if scope == '1':   # 仅属性区
                should_process = is_current_line_frontmatter
            elif scope == '2': # 仅正文区
                should_process = is_current_line_body
            elif scope == '3': # 全局无差别
                should_process = True

            if should_process and (old_val in lines[i]):
                # 纯单词边界保护 (例如查找 "tag"，避免把 "staged" 改掉)
                if re.match(r'^\w+$', old_val):
                    lines[i] = re.sub(rf'\b{escaped_old}\b', new_val, lines[i])
                else:
                    # 包含特殊符号(如 #tag, 链接等)则直接替换
                    lines[i] = lines[i].replace(old_val, new_val)

        content = '\n'.join(lines)

        if content != original_content:
            try:
                filepath.write_text(content, encoding='utf-8')
                return True
            except Exception:
                return False
        return False

    def start_execution(self):
        target_dir = self.dir_path.get()
        if not target_dir or not Path(target_dir).is_dir():
            messagebox.showerror("错误", "请先选择有效的目标目录！")
            return
            
        old_val = self.old_val_var.get().strip()
        new_val = self.new_val_var.get().strip()
        scope = self.scope_var.get()
        
        if not old_val:
            messagebox.showerror("错误", "【查找内容】不能为空！")
            return
            
        self.btn_execute.config(state="disabled", text="正在处理中...")
        self.txt_log.config(state="normal")
        self.txt_log.delete(1.0, tk.END)
        self.txt_log.config(state="disabled")
        
        threading.Thread(target=self.run_replace_task, args=(target_dir, old_val, new_val, scope), daemon=True).start()

    def run_replace_task(self, target_dir, old_val, new_val, scope):
        target_path = Path(target_dir)
        self.log(f"[*] 扫描根目录: {target_path.resolve()}\n")
        
        modified_count = 0
        total_count = 0

        for md_file in target_path.rglob("*.md"):
            total_count += 1
            if self.process_file(md_file, old_val, new_val, scope):
                modified_count += 1
                # 输出带层级的相对路径，而不是单纯的文件名
                relative_path = md_file.relative_to(target_path)
                self.log(f"[✓ 更新] {relative_path}")
        
        self.log("\n" + "-" * 40)
        self.log(f"执行完毕！共扫描 {total_count} 个文件，实际修改 {modified_count} 个文件。")
        
        self.root.after(0, lambda: self.btn_execute.config(state="normal", text="▶ 开始批量替换"))
        self.root.after(0, lambda: messagebox.showinfo("完成", f"处理完毕！\n共深度扫描了 {total_count} 个文件，\n实际修改了 {modified_count} 个文件。"))

if __name__ == "__main__":
    import ctypes
    try: ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception: pass

    root = tk.Tk()
    app = ObsidianReplacerApp(root)
    root.mainloop()
