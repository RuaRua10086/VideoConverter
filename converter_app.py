import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import threading
import subprocess
import shutil
import sys

class VideoConverterApp:
    """
    一个使用 Tkinter 和 FFmpeg 构建的，支持多线程处理的视频格式转换器。
    """
    def __init__(self, root):
        self.root = root
        self.root.title("视频格式转换器 (v1.1)")
        self.root.geometry("800x600")
        self.root.minsize(700, 500)

        # --- 变量定义 ---
        self.source_path = tk.StringVar()
        self.dest_path = tk.StringVar()
        self.target_format = tk.StringVar()
        self.input_formats = {
            # --- 主流通用格式 ---
            '.mp4', '.mkv', '.avi', '.mov', '.wmv', '.flv', '.webm',
            
            # --- MPEG 家族 ---
            '.mpg', '.mpeg', '.m2v', 
            
            # --- 移动设备格式 ---
            '.3gp', '.3g2',
            
            # --- 广播和高清摄像机格式 ---
            '.ts', '.mts', '.m2ts', 
            
            # --- DVD/VCD 格式 ---
            '.vob',
            
            # --- 专业和开放格式 ---
            '.mxf', '.ogv', '.ogg',
            
            # --- 其他常见格式 ---
            '.rmvb', '.asf', '.divx', '.f4v'
        }
        self.output_formats = ["mp4", "mkv", "mov", "avi", "webm", "flv"]

        # <--- 2. 获取FFmpeg路径 ---
        self.ffmpeg_path = self.get_ffmpeg_path()
        
        
        # --- 样式配置 ---
        self.style = ttk.Style(self.root)
        self.style.theme_use('vista')

        # --- 创建主框架 ---
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # --- 创建并布局所有控件 ---
        self.controls = self.create_widgets(main_frame)

        #初始化检查
        self.check_ffmpeg()

    
    def get_ffmpeg_path(self):
        """获取FFmpeg可执行文件的路径"""
        if getattr(sys, 'frozen', False):
            base_path = sys._MEIPASS
        else:
            base_path = os.path.abspath(".")

        return os.path.join(base_path, "ffmpeg_bin", "ffmpeg.exe")

    def check_ffmpeg(self):
        """检查FFmpeg可执行文件是否存在"""
        if not os.path.exists(self.ffmpeg_path):
            self.log(f"错误: 在 {self.ffmpeg_path} 未找到 ffmpeg.exe。")
            self.log("程序功能将受限。")
            if hasattr(self, 'convert_button'):
                self.convert_button.config(state='disabled')
        else:
            self.log("FFmpeg核心已找到，程序准备就绪。")

    def create_widgets(self, container):
        """在主容器中创建并放置所有UI控件，并返回需要控制状态的控件列表"""
        
        # 说明按钮
        about_button = ttk.Button(container, text="说明", command=self.show_about)
        about_button.grid(row=2, column=1, padx=(10, 0), sticky=tk.E)
        
        # 路径选择
        ttk.Label(container, text="源文件夹路径:").grid(row=0, column=0, sticky=tk.W, pady=5)
        source_entry = ttk.Entry(container, textvariable=self.source_path, state='readonly', width=70)
        source_entry.grid(row=0, column=1, sticky=tk.EW, padx=(5, 10))
        source_button = ttk.Button(container, text="浏览...", command=self.select_source_path)
        source_button.grid(row=0, column=2)

        ttk.Label(container, text="目标文件夹路径:").grid(row=1, column=0, sticky=tk.W, pady=5)
        dest_entry = ttk.Entry(container, textvariable=self.dest_path, state='readonly', width=70)
        dest_entry.grid(row=1, column=1, sticky=tk.EW, padx=(5, 10))
        dest_button = ttk.Button(container, text="浏览...", command=self.select_dest_path)
        dest_button.grid(row=1, column=2)

        # 格式选择
        ttk.Label(container, text="选择目标格式:").grid(row=2, column=0, sticky=tk.W, pady=15)
        self.target_format.set(self.output_formats[0])
        format_menu = ttk.OptionMenu(container, self.target_format, self.output_formats[0], *self.output_formats)
        format_menu.grid(row=2, column=1, sticky=tk.W, padx=5)
        
        # 开始转换按钮
        button_frame = ttk.Frame(container)
        button_frame.grid(row=3, column=0, columnspan=3, pady=20)
        self.convert_button = ttk.Button(button_frame, text="开始转换", command=self.start_conversion, style="Accent.TButton")
        self.convert_button.pack()
        self.style.configure("Accent.TButton", font=("Microsoft YaHei UI", 12, "bold"), padding=10)

        # 进度条
        self.progress_bar = ttk.Progressbar(container, orient='horizontal', mode='determinate', length=100)
        self.progress_bar.grid(row=4, column=0, columnspan=3, sticky=tk.EW, pady=10)
        
        # 日志输出区域
        ttk.Label(container, text="转换日志:").grid(row=5, column=0, sticky=tk.W, pady=5)
        log_frame = ttk.Frame(container)
        log_frame.grid(row=6, column=0, columnspan=3, sticky="nsew")
        
        self.log_area = tk.Text(log_frame, height=15, state='disabled', wrap=tk.WORD, bg="#f0f0f0", font=("Microsoft YaHei UI", 9))
        self.log_area.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar = ttk.Scrollbar(log_frame, command=self.log_area.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_area.config(yscrollcommand=scrollbar.set)

        container.columnconfigure(1, weight=1)
        container.rowconfigure(6, weight=1)

        # 返回需要统一控制状态的控件
        return [source_button, dest_button, format_menu, self.convert_button, about_button]

    def toggle_controls(self, state):
        """启用或禁用所有输入控件"""
        for control in self.controls:
            control.config(state=state)

    def select_source_path(self):
        path = filedialog.askdirectory(title="请选择包含视频的源文件夹")
        if path:
            self.source_path.set(path)
            self.log(f"已选择源文件夹: {path}")

    def select_dest_path(self):
        path = filedialog.askdirectory(title="请选择保存转换后视频的目标文件夹")
        if path:
            self.dest_path.set(path)
            self.log(f"已选择目标文件夹: {path}")

    def log(self, message):
        self.log_area.config(state='normal')
        self.log_area.insert(tk.END, message + "\n")
        self.log_area.see(tk.END)
        self.log_area.config(state='disabled')

    def find_video_files(self, src_path):
        """递归查找源路径下的所有视频文件"""
        video_files = []
        for root, _, files in os.walk(src_path):
            for file in files:
                if os.path.splitext(file)[1].lower() in self.input_formats:
                    video_files.append(os.path.join(root, file))
        return video_files

    def start_conversion(self):
        """验证输入并启动后台转换线程"""
        source = self.source_path.get()
        dest = self.dest_path.get()
        
        if not source or not dest:
            messagebox.showwarning("输入错误", "请同时选择源文件夹和目标文件夹！")
            return
        if source == dest:
            if not messagebox.askyesno("确认", "源文件夹和目标文件夹相同，可能导致文件覆盖或混乱，确定要继续吗？"):
                return

        # 创建并启动后台线程
        conversion_thread = threading.Thread(target=self.run_conversion, daemon=True)
        conversion_thread.start()
        
    def run_conversion(self):
        """在后台线程中执行实际的转换任务"""
        # --- 准备阶段 ---
        self.root.after(0, self.toggle_controls, 'disabled')
        self.root.after(0, self.log, "="*60)
        self.root.after(0, self.log, "开始执行转换任务...")

        source_dir = self.source_path.get()
        dest_dir = self.dest_path.get()
        target_ext = "." + self.target_format.get()
        
        video_files = self.find_video_files(source_dir)

        if not video_files:
            self.root.after(0, self.log, "未在源文件夹中找到支持的视频文件。")
            self.root.after(0, self.toggle_controls, 'normal')
            return

        self.root.after(0, lambda: self.progress_bar.config(maximum=len(video_files), value=0))
        self.root.after(0, self.log, f"发现 {len(video_files)} 个视频文件待转换。")

        # --- 循环转换 ---
        success_count = 0
        fail_count = 0
        for i, input_path in enumerate(video_files):
            filename = os.path.basename(input_path)
            base_name = os.path.splitext(filename)[0]
            output_filename = base_name + target_ext

            # 创建与源目录结构相同的目标子目录
            relative_path = os.path.relpath(os.path.dirname(input_path), source_dir)
            output_subdir = os.path.join(dest_dir, relative_path)
            os.makedirs(output_subdir, exist_ok=True)
            output_path = os.path.join(output_subdir, output_filename)
            
            self.root.after(0, self.log, f"({i+1}/{len(video_files)}) 正在转换: {filename}")

            # 构建并执行 FFmpeg 命令
            command = [
                self.ffmpeg_path,
                "-i", input_path,
                "-y",  # 覆盖输出文件
                "-c:v", "copy", # 尝试直接复制视频流（速度快）
                "-c:a", "aac", # 重新编码音频为aac
                "-b:a", "192k", # 设置音频比特率
                output_path
            ]
            
            # 这是一个更通用的命令，会重新编码视频和音频，兼容性更好但速度慢
            # command = [
            #     "ffmpeg",
            #     "-i", input_path,
            #     "-y",
            #     output_path
            # ]
            
            try:
                # 使用 CREATE_NO_WINDOW 防止在 Windows 上弹出黑窗
                proc = subprocess.run(command, capture_output=True, text=True, check=True, creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
                self.root.after(0, self.log, f"  -> 成功保存至: {output_path}")
                success_count += 1
            except subprocess.CalledProcessError as e:
                # 如果快速复制视频流失败，尝试完全重新编码
                self.root.after(0, self.log, f"  -> 快速复制失败，尝试完全重新编码...")
                command = [self.ffmpeg_path, "-i", input_path, "-y", output_path]
                try:
                    proc = subprocess.run(command, capture_output=True, text=True, check=True, creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
                    self.root.after(0, self.log, f"  -> 成功保存至: {output_path}")
                    success_count += 1
                except subprocess.CalledProcessError as e2:
                    self.root.after(0, self.log, f"  -> 错误: 转换失败! FFmpeg 输出:\n{e2.stderr}")
                    fail_count += 1
            
            # 更新进度条
            self.root.after(0, self.progress_bar.step)

        # --- 清理阶段 ---
        final_message = f"任务完成！成功: {success_count}, 失败: {fail_count}."
        self.root.after(0, self.log, final_message)
        self.root.after(0, lambda: messagebox.showinfo("任务完成", final_message))
        self.root.after(0, self.toggle_controls, 'normal')
        self.root.after(0, lambda: self.progress_bar.config(value=0))

    def show_about(self):
        """弹出说明窗口，显示自定义说明内容"""
        about_text = (
            "视频格式转换器 说明\n"
            "-----------------------------\n"
            "直接选择文件夹，自动搜索所有子目录和视频！！！\n"
            "直接选择文件夹，自动搜索所有子目录和视频！！！\n"
            "直接选择文件夹，自动搜索所有子目录和视频！！！\n"
            "\n"

            "本工具支持多种主流视频格式：\n"
            "通用主流格式：'.mp4', '.mkv', '.avi', '.mov', '.wmv', '.flv', '.webm'\n"
            "MPEG 家族：'.mpg', '.mpeg', '.m2v'\n"
            "移动设备格式：'.3gp', '.3g2'\n"
            "广播和高清摄像机格式：'.ts', '.mts', '.m2ts'\n"
            "DVD/VCD 格式：'.vob'\n"
            "专业和开放格式：'.mxf', '.ogv', '.ogg'\n"
            "其他常见格式：'.rmvb', '.asf', '.divx', '.f4v'\n"
            "\n"
            
            "注意事项：\n"
            "- 请确保已安装 FFmpeg 并配置到系统环境变量。\n"
            "- 支持保留源目录结构。\n"
            "- 转换过程不会删除原文件。\n"
            "\n"
            "如有问题或建议，请联系开发者。"
        )
        win = tk.Toplevel(self.root)
        win.title("关于本程序")
        win.geometry("450x500")
        win.resizable(False, False)
        text = tk.Text(win, wrap=tk.WORD, height=18, width=50, state='normal', bg="#f8f8f8", font=("Microsoft YaHei UI", 10))
        text.insert(tk.END, about_text)
        text.config(state='disabled')
        text.pack(padx=15, pady=15, fill=tk.BOTH, expand=True)
        btn = ttk.Button(win, text="关闭", command=win.destroy)
        btn.pack(pady=(0, 15))

if __name__ == "__main__":
    root = tk.Tk()
    app = VideoConverterApp(root)
    root.mainloop()