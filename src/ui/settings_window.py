"""
LyraPointer 设置窗口

使用 Tkinter 实现的配置界面，支持多语言和参数调整。
重写版本 - 改进UI设计和语言切换功能。
"""

import os
import sys
import tkinter as tk
from tkinter import messagebox, ttk
from typing import Callable, Dict, Optional

from ..config.settings import Settings
from ..utils.i18n import (
    Language,
    LanguageInfo,
    get_available_languages,
    get_i18n,
    t,
)


class ModernStyle:
    """现代化样式定义"""

    # 颜色
    BG_PRIMARY = "#1a1a2e"
    BG_SECONDARY = "#16213e"
    BG_TERTIARY = "#0f3460"
    ACCENT = "#e94560"
    ACCENT_HOVER = "#ff6b6b"
    TEXT_PRIMARY = "#ffffff"
    TEXT_SECONDARY = "#a0a0a0"
    TEXT_MUTED = "#606060"
    SUCCESS = "#4ecca3"
    WARNING = "#ffc107"
    BORDER = "#2a2a4a"

    # 字体
    FONT_FAMILY = "Segoe UI"
    FONT_SIZE_NORMAL = 10
    FONT_SIZE_LARGE = 12
    FONT_SIZE_TITLE = 14


class SettingsWindow:
    """设置窗口 - 改进版"""

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
        self._i18n = get_i18n()

        # 变量绑定
        self.vars: Dict[str, tk.Variable] = {}

    def show(self):
        """显示设置窗口"""
        if self._is_open:
            if self.root:
                self.root.lift()
                self.root.focus_force()
            return

        self._create_window()

    def _create_window(self):
        """创建窗口"""
        self.root = tk.Tk()
        self.root.title(t("settings.title") + " - LyraPointer")
        self.root.geometry("550x480")
        self.root.minsize(500, 450)
        self.root.resizable(True, True)

        # 设置窗口背景色
        self.root.configure(bg=ModernStyle.BG_PRIMARY)

        # 处理关闭事件
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

        # 配置样式
        self._configure_styles()

        # 创建主框架
        main_frame = ttk.Frame(self.root, style="Main.TFrame")
        main_frame.pack(fill="both", expand=True, padx=15, pady=15)

        # 标题
        title_label = ttk.Label(
            main_frame,
            text=t("settings.title"),
            style="Title.TLabel",
        )
        title_label.pack(anchor="w", pady=(0, 15))

        # 创建选项卡
        notebook = ttk.Notebook(main_frame, style="Custom.TNotebook")
        notebook.pack(fill="both", expand=True)

        # 通用设置页
        general_frame = ttk.Frame(notebook, style="Tab.TFrame")
        notebook.add(general_frame, text=f"  {t('settings.general')}  ")
        self._create_general_tab(general_frame)

        # 界面设置页
        interface_frame = ttk.Frame(notebook, style="Tab.TFrame")
        notebook.add(interface_frame, text=f"  {t('settings.interface')}  ")
        self._create_interface_tab(interface_frame)

        # 关于页
        about_frame = ttk.Frame(notebook, style="Tab.TFrame")
        notebook.add(about_frame, text=f"  {t('settings.about')}  ")
        self._create_about_tab(about_frame)

        # 底部按钮
        self._create_buttons(main_frame)

        self._is_open = True

        # 居中显示
        self._center_window()

        self.root.mainloop()

    def _configure_styles(self):
        """配置 ttk 样式"""
        style = ttk.Style()

        # 尝试使用更现代的主题
        available_themes = style.theme_names()
        if "clam" in available_themes:
            style.theme_use("clam")

        # 主框架
        style.configure(
            "Main.TFrame",
            background=ModernStyle.BG_PRIMARY,
        )

        # 选项卡框架
        style.configure(
            "Tab.TFrame",
            background=ModernStyle.BG_SECONDARY,
        )

        # 标题标签
        style.configure(
            "Title.TLabel",
            background=ModernStyle.BG_PRIMARY,
            foreground=ModernStyle.TEXT_PRIMARY,
            font=(ModernStyle.FONT_FAMILY, ModernStyle.FONT_SIZE_TITLE, "bold"),
        )

        # 普通标签
        style.configure(
            "TLabel",
            background=ModernStyle.BG_SECONDARY,
            foreground=ModernStyle.TEXT_PRIMARY,
            font=(ModernStyle.FONT_FAMILY, ModernStyle.FONT_SIZE_NORMAL),
        )

        # 分组标签
        style.configure(
            "Group.TLabel",
            background=ModernStyle.BG_SECONDARY,
            foreground=ModernStyle.ACCENT,
            font=(ModernStyle.FONT_FAMILY, ModernStyle.FONT_SIZE_LARGE, "bold"),
        )

        # 说明标签
        style.configure(
            "Hint.TLabel",
            background=ModernStyle.BG_SECONDARY,
            foreground=ModernStyle.TEXT_SECONDARY,
            font=(ModernStyle.FONT_FAMILY, 9),
        )

        # 分组框
        style.configure(
            "TLabelframe",
            background=ModernStyle.BG_SECONDARY,
            foreground=ModernStyle.TEXT_PRIMARY,
            bordercolor=ModernStyle.BORDER,
        )
        style.configure(
            "TLabelframe.Label",
            background=ModernStyle.BG_SECONDARY,
            foreground=ModernStyle.ACCENT,
            font=(ModernStyle.FONT_FAMILY, ModernStyle.FONT_SIZE_NORMAL, "bold"),
        )

        # 复选框
        style.configure(
            "TCheckbutton",
            background=ModernStyle.BG_SECONDARY,
            foreground=ModernStyle.TEXT_PRIMARY,
            font=(ModernStyle.FONT_FAMILY, ModernStyle.FONT_SIZE_NORMAL),
        )
        style.map(
            "TCheckbutton",
            background=[("active", ModernStyle.BG_SECONDARY)],
        )

        # 下拉框
        style.configure(
            "TCombobox",
            font=(ModernStyle.FONT_FAMILY, ModernStyle.FONT_SIZE_NORMAL),
        )

        # 滑块
        style.configure(
            "TScale",
            background=ModernStyle.BG_SECONDARY,
            troughcolor=ModernStyle.BG_TERTIARY,
        )

        # 笔记本（选项卡）
        style.configure(
            "Custom.TNotebook",
            background=ModernStyle.BG_PRIMARY,
            bordercolor=ModernStyle.BORDER,
        )
        style.configure(
            "Custom.TNotebook.Tab",
            background=ModernStyle.BG_TERTIARY,
            foreground=ModernStyle.TEXT_PRIMARY,
            padding=[15, 8],
            font=(ModernStyle.FONT_FAMILY, ModernStyle.FONT_SIZE_NORMAL),
        )
        style.map(
            "Custom.TNotebook.Tab",
            background=[("selected", ModernStyle.BG_SECONDARY)],
            foreground=[("selected", ModernStyle.ACCENT)],
        )

        # 按钮
        style.configure(
            "TButton",
            background=ModernStyle.BG_TERTIARY,
            foreground=ModernStyle.TEXT_PRIMARY,
            font=(ModernStyle.FONT_FAMILY, ModernStyle.FONT_SIZE_NORMAL),
            padding=[20, 8],
        )

        # 主按钮
        style.configure(
            "Accent.TButton",
            background=ModernStyle.ACCENT,
            foreground=ModernStyle.TEXT_PRIMARY,
            font=(ModernStyle.FONT_FAMILY, ModernStyle.FONT_SIZE_NORMAL, "bold"),
            padding=[25, 10],
        )

    def _create_general_tab(self, parent: ttk.Frame):
        """创建通用设置页"""
        # 滚动区域
        canvas = tk.Canvas(
            parent,
            bg=ModernStyle.BG_SECONDARY,
            highlightthickness=0,
        )
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas, style="Tab.TFrame")

        scrollable_frame.bind(
            "<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # 鼠标滚轮绑定
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        canvas.bind_all("<MouseWheel>", _on_mousewheel)

        # ===== 语言设置 =====
        lang_group = ttk.LabelFrame(
            scrollable_frame,
            text=f" {t('settings.language')} ",
            padding=15,
        )
        lang_group.pack(fill="x", padx=10, pady=8)

        lang_frame = ttk.Frame(lang_group, style="Tab.TFrame")
        lang_frame.pack(fill="x")

        ttk.Label(lang_frame, text=t("settings.language") + ":").pack(
            side="left", padx=(0, 10)
        )

        # 获取可用语言
        languages = get_available_languages()
        lang_options = [f"{lang.flag} {lang.name}" for lang in languages]
        lang_codes = [lang.code for lang in languages]

        # 当前语言
        current_lang = self._i18n.language_code
        current_idx = (
            lang_codes.index(current_lang) if current_lang in lang_codes else 0
        )

        self.vars["language"] = tk.StringVar(value=lang_options[current_idx])
        lang_combo = ttk.Combobox(
            lang_frame,
            textvariable=self.vars["language"],
            values=lang_options,
            state="readonly",
            width=25,
        )
        lang_combo.pack(side="left", fill="x", expand=True)
        lang_combo.bind("<<ComboboxSelected>>", self._on_language_change)

        # 语言提示
        ttk.Label(
            lang_group,
            text="Language change will take effect after restart",
            style="Hint.TLabel",
        ).pack(anchor="w", pady=(5, 0))

        # ===== 控制设置 =====
        control_group = ttk.LabelFrame(
            scrollable_frame,
            text=f" {t('settings.control')} ",
            padding=15,
        )
        control_group.pack(fill="x", padx=10, pady=8)

        # 平滑预设选择
        preset_frame = ttk.Frame(control_group, style="Tab.TFrame")
        preset_frame.pack(fill="x", pady=(0, 10))

        ttk.Label(preset_frame, text="Smoothing Preset:").pack(
            side="left", padx=(0, 10)
        )

        preset_options = [
            "🚀 Responsive (Most responsive)",
            "⚖️ Balanced (Recommended)",
            "🎯 Stable (Smoothest)",
            "⚙️ Custom",
        ]

        # 根据当前平滑值确定预设
        current_smoothing = self.settings.smoothing
        if current_smoothing < 0.25:
            current_preset_idx = 0
        elif current_smoothing < 0.6:
            current_preset_idx = 1
        elif current_smoothing < 0.85:
            current_preset_idx = 2
        else:
            current_preset_idx = 3

        self.vars["smoothing_preset"] = tk.StringVar(
            value=preset_options[current_preset_idx]
        )
        preset_combo = ttk.Combobox(
            preset_frame,
            textvariable=self.vars["smoothing_preset"],
            values=preset_options,
            state="readonly",
            width=30,
        )
        preset_combo.pack(side="left", fill="x", expand=True)
        preset_combo.bind("<<ComboboxSelected>>", self._on_preset_change)

        # 灵敏度
        self._create_slider(
            control_group,
            t("settings.sensitivity"),
            "sensitivity",
            0.5,
            3.0,
            self.settings.sensitivity,
            "Lower = slower cursor, Higher = faster cursor",
        )

        # 平滑度（自定义模式下可调）
        self._create_slider(
            control_group,
            t("settings.smoothing"),
            "smoothing",
            0.0,
            0.95,
            self.settings.smoothing,
            "0 = Most responsive, 1 = Smoothest (more delay)",
        )

        # 滚动速度
        self._create_slider(
            control_group,
            t("settings.scroll_speed"),
            "scroll_speed",
            1,
            20,
            self.settings.scroll_speed,
            "Scroll wheel speed",
        )

        # ===== 镜像设置 =====
        mirror_group = ttk.LabelFrame(
            scrollable_frame,
            text=f" {t('settings.mirroring')} ",
            padding=15,
        )
        mirror_group.pack(fill="x", padx=10, pady=8)

        self.vars["flip_x"] = tk.BooleanVar(value=self.settings.flip_x)
        ttk.Checkbutton(
            mirror_group,
            text=t("settings.flip_x"),
            variable=self.vars["flip_x"],
        ).pack(anchor="w", pady=3)

        self.vars["flip_y"] = tk.BooleanVar(value=self.settings.flip_y)
        ttk.Checkbutton(
            mirror_group,
            text=t("settings.flip_y"),
            variable=self.vars["flip_y"],
        ).pack(anchor="w", pady=3)

    def _create_interface_tab(self, parent: ttk.Frame):
        """创建界面设置页"""
        container = ttk.Frame(parent, style="Tab.TFrame")
        container.pack(fill="both", expand=True, padx=10, pady=10)

        # ===== 显示设置 =====
        display_group = ttk.LabelFrame(
            container,
            text=f" Display Options ",
            padding=15,
        )
        display_group.pack(fill="x", pady=8)

        self.vars["show_skeleton"] = tk.BooleanVar(value=self.settings.show_skeleton)
        ttk.Checkbutton(
            display_group,
            text=t("settings.show_skeleton"),
            variable=self.vars["show_skeleton"],
        ).pack(anchor="w", pady=5)

        self.vars["show_fps"] = tk.BooleanVar(value=self.settings.show_fps)
        ttk.Checkbutton(
            display_group,
            text=t("settings.show_fps"),
            variable=self.vars["show_fps"],
        ).pack(anchor="w", pady=5)

        # ===== 性能设置 =====
        perf_group = ttk.LabelFrame(
            container,
            text=" Performance ",
            padding=15,
        )
        perf_group.pack(fill="x", pady=8)

        ttk.Label(perf_group, text="Model Complexity:").pack(anchor="w")

        model_frame = ttk.Frame(perf_group, style="Tab.TFrame")
        model_frame.pack(fill="x", pady=5)

        self.vars["model_complexity"] = tk.IntVar(value=self.settings.model_complexity)

        ttk.Radiobutton(
            model_frame,
            text="Lite (Faster)",
            variable=self.vars["model_complexity"],
            value=0,
        ).pack(side="left", padx=(0, 20))

        ttk.Radiobutton(
            model_frame,
            text="Full (More Accurate)",
            variable=self.vars["model_complexity"],
            value=1,
        ).pack(side="left")

        ttk.Label(
            perf_group,
            text="Lite mode recommended for older hardware",
            style="Hint.TLabel",
        ).pack(anchor="w", pady=(5, 0))

    def _create_about_tab(self, parent: ttk.Frame):
        """创建关于页"""
        container = ttk.Frame(parent, style="Tab.TFrame")
        container.pack(fill="both", expand=True, padx=20, pady=20)

        # Logo/标题
        title_frame = ttk.Frame(container, style="Tab.TFrame")
        title_frame.pack(pady=20)

        ttk.Label(
            title_frame,
            text="🖐️ LyraPointer",
            font=(ModernStyle.FONT_FAMILY, 24, "bold"),
        ).pack()

        ttk.Label(
            title_frame,
            text="Gesture Control System",
            style="Hint.TLabel",
        ).pack(pady=5)

        # 版本信息
        info_frame = ttk.Frame(container, style="Tab.TFrame")
        info_frame.pack(pady=10)

        info_items = [
            ("Version", "1.1.0"),
            ("Author", "Pete Hsu"),
            ("License", "MIT"),
            ("Python", "3.11 / 3.12"),
        ]

        for label, value in info_items:
            row = ttk.Frame(info_frame, style="Tab.TFrame")
            row.pack(fill="x", pady=3)
            ttk.Label(row, text=f"{label}:", width=12, anchor="e").pack(side="left")
            ttk.Label(row, text=value, foreground=ModernStyle.TEXT_SECONDARY).pack(
                side="left", padx=10
            )

        # 链接
        link_frame = ttk.Frame(container, style="Tab.TFrame")
        link_frame.pack(pady=20)

        ttk.Label(
            link_frame,
            text="GitHub: github.com/your-username/LyraPointer",
            foreground=ModernStyle.ACCENT,
            cursor="hand2",
        ).pack()

        # 版权
        ttk.Label(
            container,
            text="© 2025 Pete Hsu. All rights reserved.",
            style="Hint.TLabel",
        ).pack(side="bottom", pady=10)

    def _create_slider(
        self,
        parent: ttk.Frame,
        label: str,
        var_name: str,
        min_val: float,
        max_val: float,
        current_val: float,
        hint: str = "",
    ):
        """创建滑块控件"""
        frame = ttk.Frame(parent, style="Tab.TFrame")
        frame.pack(fill="x", pady=8)

        # 标签和当前值
        header = ttk.Frame(frame, style="Tab.TFrame")
        header.pack(fill="x")

        ttk.Label(header, text=label).pack(side="left")

        value_var = tk.StringVar(value=f"{current_val:.2f}")
        value_label = ttk.Label(
            header, textvariable=value_var, foreground=ModernStyle.ACCENT
        )
        value_label.pack(side="right")

        # 滑块
        slider_var = tk.DoubleVar(value=current_val)
        self.vars[var_name] = slider_var

        def update_value_label(*args):
            val = slider_var.get()
            if isinstance(min_val, int) and isinstance(max_val, int):
                value_var.set(f"{int(val)}")
            else:
                value_var.set(f"{val:.2f}")

        slider_var.trace_add("write", update_value_label)

        slider = ttk.Scale(
            frame,
            from_=min_val,
            to=max_val,
            variable=slider_var,
            orient="horizontal",
        )
        slider.pack(fill="x", pady=5)

        # 提示文字
        if hint:
            ttk.Label(frame, text=hint, style="Hint.TLabel").pack(anchor="w")

    def _create_buttons(self, parent: ttk.Frame):
        """创建底部按钮"""
        btn_frame = ttk.Frame(parent, style="Main.TFrame")
        btn_frame.pack(fill="x", pady=(15, 0))

        # 重置按钮
        reset_btn = ttk.Button(
            btn_frame,
            text=t("settings.reset"),
            command=self._reset_defaults,
        )
        reset_btn.pack(side="left")

        # 保存和取消按钮
        save_btn = ttk.Button(
            btn_frame,
            text=t("settings.save"),
            style="Accent.TButton",
            command=self._save,
        )
        save_btn.pack(side="right", padx=(10, 0))

        cancel_btn = ttk.Button(
            btn_frame,
            text=t("settings.cancel"),
            command=self._on_close,
        )
        cancel_btn.pack(side="right")

    def _on_preset_change(self, event):
        """平滑预设变化"""
        selection = self.vars["smoothing_preset"].get()

        # 根据预设设置平滑值
        if "Responsive" in selection:
            smoothing_value = 0.15
        elif "Balanced" in selection:
            smoothing_value = 0.45
        elif "Stable" in selection:
            smoothing_value = 0.75
        else:
            # Custom - 不改变当前值
            return

        # 更新滑块值
        if "smoothing" in self.vars:
            self.vars["smoothing"].set(smoothing_value)

    def _on_language_change(self, event):
        """语言选择变化"""
        selection = self.vars["language"].get()
        languages = get_available_languages()

        for lang in languages:
            if lang.name in selection:
                current_lang = self.settings.get("ui.language", "en")
                if lang.code != current_lang:
                    # 保存语言设置到配置
                    self.settings.set("ui.language", lang.code)
                    self.settings.save()

                    # 询问是否重启
                    result = messagebox.askyesno(
                        t("settings.language_change_title")
                        if t("settings.language_change_title")
                        != "settings.language_change_title"
                        else "Language Changed",
                        t("settings.language_change_message")
                        if t("settings.language_change_message")
                        != "settings.language_change_message"
                        else "Language changed. Restart now to apply?",
                    )

                    if result:
                        self._restart_application()
                break

    def _restart_application(self):
        """重启应用程序"""
        try:
            # 关闭当前窗口
            if self.root:
                self.root.destroy()

            # 获取当前 Python 解释器和脚本路径
            python = sys.executable
            script = sys.argv[0]

            # 重启程序
            os.execl(python, python, script, *sys.argv[1:])
        except Exception as e:
            messagebox.showerror("Error", f"Failed to restart: {e}")

    def _reset_defaults(self):
        """重置为默认值"""
        result = messagebox.askyesno(
            "Reset Settings",
            "Are you sure you want to reset all settings to defaults?",
        )

        if result:
            self.settings.reset()
            self._on_close()
            messagebox.showinfo(
                "Settings Reset",
                "Settings have been reset. Please restart the application.",
            )

    def _save(self):
        """保存设置"""
        try:
            # 保存控制设置
            if "sensitivity" in self.vars:
                self.settings.sensitivity = self.vars["sensitivity"].get()
            if "smoothing" in self.vars:
                self.settings.smoothing = self.vars["smoothing"].get()
            if "scroll_speed" in self.vars:
                self.settings.set(
                    "settings.scroll_speed", int(self.vars["scroll_speed"].get())
                )

            # 保存镜像设置
            if "flip_x" in self.vars:
                self.settings.flip_x = self.vars["flip_x"].get()
            if "flip_y" in self.vars:
                self.settings.flip_y = self.vars["flip_y"].get()

            # 保存显示设置
            if "show_skeleton" in self.vars:
                self.settings.set("ui.show_skeleton", self.vars["show_skeleton"].get())
            if "show_fps" in self.vars:
                self.settings.set("ui.show_fps", self.vars["show_fps"].get())

            # 保存性能设置
            if "model_complexity" in self.vars:
                self.settings.set(
                    "settings.performance.model_complexity",
                    self.vars["model_complexity"].get(),
                )

            # 保存到文件
            self.settings.save()

            if self.on_save:
                self.on_save()

            self._on_close()

        except Exception as e:
            messagebox.showerror("Error", f"Failed to save settings: {e}")

    def _on_close(self):
        """关闭窗口"""
        self._is_open = False

        if self.root:
            # 解绑鼠标滚轮
            try:
                self.root.unbind_all("<MouseWheel>")
            except Exception:
                pass

            self.root.destroy()
            self.root = None

        if self.on_close:
            self.on_close()

    def _center_window(self):
        """窗口居中显示"""
        if self.root:
            self.root.update_idletasks()
            width = self.root.winfo_width()
            height = self.root.winfo_height()
            x = (self.root.winfo_screenwidth() // 2) - (width // 2)
            y = (self.root.winfo_screenheight() // 2) - (height // 2)
            self.root.geometry(f"{width}x{height}+{x}+{y}")
