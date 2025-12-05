"""
设置界面

使用 Tkinter 实现的配置界面，支持手势映射和参数调整。
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Callable, Optional

from ..config.settings import Settings
from ..gestures.gestures import GestureType, ActionType


class SettingsWindow:
    """设置窗口"""
    
    def __init__(
        self,
        settings: Settings,
        on_save: Optional[Callable] = None,
        on_close: Optional[Callable] = None,
    ):
        """
        初始化设置窗口
        
        Args:
            settings: 配置管理器
            on_save: 保存回调
            on_close: 关闭回调
        """
        self.settings = settings
        self.on_save = on_save
        self.on_close = on_close
        
        self.root: Optional[tk.Tk] = None
        self._is_open = False
        
        # 变量绑定
        self.vars = {}
    
    def show(self):
        """显示设置窗口"""
        if self._is_open:
            if self.root:
                self.root.lift()
            return
        
        self.root = tk.Tk()
        self.root.title("LyraPointer Settings")
        self.root.geometry("600x500")
        self.root.resizable(False, False)
        
        # 处理关闭事件
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        
        # 创建选项卡
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill="both", expand=True, padx=10, pady=10)
        
        # 通用设置
        general_frame = ttk.Frame(notebook)
        notebook.add(general_frame, text="General")
        self._create_general_tab(general_frame)
        
        # 手势设置
        gestures_frame = ttk.Frame(notebook)
        notebook.add(gestures_frame, text="Gestures")
        self._create_gestures_tab(gestures_frame)
        
        # 底部按钮
        btn_frame = ttk.Frame(self.root)
        btn_frame.pack(fill="x", padx=10, pady=10)
        
        ttk.Button(btn_frame, text="Save", command=self._save).pack(side="right", padx=5)
        ttk.Button(btn_frame, text="Cancel", command=self._on_close).pack(side="right", padx=5)
        
        self._is_open = True
        self.root.mainloop()
    
    def _create_general_tab(self, parent):
        """创建通用设置页"""
        # 1. 镜像设置
        mirror_group = ttk.LabelFrame(parent, text="Mirroring", padding=10)
        mirror_group.pack(fill="x", padx=10, pady=5)
        
        self.vars["flip_x"] = tk.BooleanVar(value=self.settings.flip_x)
        self.vars["flip_y"] = tk.BooleanVar(value=self.settings.flip_y)
        
        ttk.Checkbutton(
            mirror_group,
            text="Horizontal Mirror (Flip X)",
            variable=self.vars["flip_x"]
        ).pack(anchor="w")
        
        ttk.Checkbutton(
            mirror_group,
            text="Vertical Mirror (Flip Y)",
            variable=self.vars["flip_y"]
        ).pack(anchor="w")
        
        # 2. 控制参数
        control_group = ttk.LabelFrame(parent, text="Control", padding=10)
        control_group.pack(fill="x", padx=10, pady=5)
        
        # 灵敏度
        ttk.Label(control_group, text="Sensitivity:").pack(anchor="w")
        self.vars["sensitivity"] = tk.DoubleVar(value=self.settings.sensitivity)
        scale_sens = ttk.Scale(
            control_group,
            from_=0.1,
            to=5.0,
            variable=self.vars["sensitivity"],
            orient="horizontal",
        )
        scale_sens.pack(fill="x", pady=(0, 10))
        
        # 平滑度
        ttk.Label(control_group, text="Smoothing (Stability vs Latency):").pack(anchor="w")
        self.vars["smoothing"] = tk.DoubleVar(value=self.settings.smoothing)
        scale_smooth = ttk.Scale(
            control_group,
            from_=0.0,
            to=0.99,
            variable=self.vars["smoothing"],
            orient="horizontal",
        )
        scale_smooth.pack(fill="x", pady=(0, 10))
        
        # 滚动速度
        ttk.Label(control_group, text="Scroll Speed:").pack(anchor="w")
        self.vars["scroll_speed"] = tk.IntVar(value=self.settings.scroll_speed)
        scale_scroll = ttk.Scale(
            control_group,
            from_=1,
            to=20,
            variable=self.vars["scroll_speed"],
            orient="horizontal",
        )
        scale_scroll.pack(fill="x")
        
        # 3. UI 设置
        ui_group = ttk.LabelFrame(parent, text="Interface", padding=10)
        ui_group.pack(fill="x", padx=10, pady=5)
        
        self.vars["show_skeleton"] = tk.BooleanVar(value=self.settings.show_skeleton)
        self.vars["show_fps"] = tk.BooleanVar(value=self.settings.show_fps)
        
        ttk.Checkbutton(
            ui_group,
            text="Show Hand Skeleton",
            variable=self.vars["show_skeleton"]
        ).pack(anchor="w")
        
        ttk.Checkbutton(
            ui_group,
            text="Show FPS",
            variable=self.vars["show_fps"]
        ).pack(anchor="w")

    def _create_gestures_tab(self, parent):
        """创建手势设置页"""
        # 说明
        ttk.Label(
            parent,
            text="Customize gesture actions (Restart required for some changes)",
            font=("", 9, "italic")
        ).pack(pady=5)
        
        # 滚动区域
        canvas = tk.Canvas(parent)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # 手势列表
        gestures = self.settings.get("gestures", {})
        self.gesture_vars = {}
        
        action_options = [a.name.lower() for a in ActionType if a != ActionType.NONE]
        action_options.append("none")
        
        for name, config in gestures.items():
            frame = ttk.LabelFrame(scrollable_frame, text=name.title(), padding=5)
            frame.pack(fill="x", padx=5, pady=5)
            
            # 描述
            ttk.Label(frame, text=config.get("description", "")).pack(anchor="w")
            
            # 动作选择
            row = ttk.Frame(frame)
            row.pack(fill="x", pady=2)
            ttk.Label(row, text="Action:").pack(side="left")
            
            current_action = config.get("action", "none")
            var = tk.StringVar(value=current_action)
            self.gesture_vars[name] = var
            
            combo = ttk.Combobox(row, textvariable=var, values=action_options, state="readonly")
            combo.pack(side="right", expand=True, fill="x", padx=(10, 0))

    def _save(self):
        """保存设置"""
        # 保存通用设置
        self.settings.flip_x = self.vars["flip_x"].get()
        self.settings.flip_y = self.vars["flip_y"].get()
        self.settings.sensitivity = self.vars["sensitivity"].get()
        self.settings.smoothing = self.vars["smoothing"].get()
        self.settings.set("settings.scroll_speed", self.vars["scroll_speed"].get())
        self.settings.set("ui.show_skeleton", self.vars["show_skeleton"].get())
        self.settings.set("ui.show_fps", self.vars["show_fps"].get())
        
        # 保存手势设置
        for name, var in self.gesture_vars.items():
            self.settings.set(f"gestures.{name}.action", var.get())
        
        # 保存到文件
        self.settings.save()
        
        if self.on_save:
            self.on_save()
            
        self._on_close()
    
    def _on_close(self):
        """关闭窗口"""
        self._is_open = False
        if self.root:
            self.root.destroy()
            self.root = None
        
        if self.on_close:
            self.on_close()
