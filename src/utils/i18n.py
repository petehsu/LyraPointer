"""
LyraPointer 国际化 (i18n) 模块

提供多语言支持，包括语言切换和翻译功能。
"""

import json
import os
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional


class Language(Enum):
    """支持的语言"""

    EN = "en"  # English
    ZH_CN = "zh_CN"  # 简体中文
    ZH_TW = "zh_TW"  # 繁體中文
    JA = "ja"  # 日本語
    KO = "ko"  # 한국어


@dataclass
class LanguageInfo:
    """语言信息"""

    code: str
    name: str  # 语言的本地名称
    english_name: str  # 英文名称
    flag: str = ""  # 国旗 emoji（可选）


# 语言信息定义
LANGUAGE_INFO: Dict[Language, LanguageInfo] = {
    Language.EN: LanguageInfo("en", "English", "English", "🇺🇸"),
    Language.ZH_CN: LanguageInfo("zh_CN", "简体中文", "Simplified Chinese", "🇨🇳"),
    Language.ZH_TW: LanguageInfo("zh_TW", "繁體中文", "Traditional Chinese", "🇹🇼"),
    Language.JA: LanguageInfo("ja", "日本語", "Japanese", "🇯🇵"),
    Language.KO: LanguageInfo("ko", "한국어", "Korean", "🇰🇷"),
}


# ============================================================================
# 翻译文本定义
# ============================================================================

TRANSLATIONS: Dict[str, Dict[str, str]] = {
    # ========== 应用信息 ==========
    "app.name": {
        "en": "LyraPointer",
        "zh_CN": "LyraPointer",
        "zh_TW": "LyraPointer",
        "ja": "LyraPointer",
        "ko": "LyraPointer",
    },
    "app.title": {
        "en": "LyraPointer - Gesture Control System",
        "zh_CN": "LyraPointer - 手势控制系统",
        "zh_TW": "LyraPointer - 手勢控制系統",
        "ja": "LyraPointer - ジェスチャーコントロールシステム",
        "ko": "LyraPointer - 제스처 제어 시스템",
    },
    "app.description": {
        "en": "Control your computer with hand gestures",
        "zh_CN": "用手势控制电脑",
        "zh_TW": "用手勢控制電腦",
        "ja": "手のジェスチャーでコンピュータを操作",
        "ko": "손동작으로 컴퓨터를 제어하세요",
    },
    # ========== 手势名称 ==========
    "gesture.none": {
        "en": "No Gesture",
        "zh_CN": "无手势",
        "zh_TW": "無手勢",
        "ja": "ジェスチャーなし",
        "ko": "제스처 없음",
    },
    "gesture.no_hand": {
        "en": "No Hand Detected",
        "zh_CN": "未检测到手",
        "zh_TW": "未偵測到手",
        "ja": "手が検出されません",
        "ko": "손이 감지되지 않음",
    },
    "gesture.pointer": {
        "en": "Pointer Mode",
        "zh_CN": "指针模式",
        "zh_TW": "指標模式",
        "ja": "ポインターモード",
        "ko": "포인터 모드",
    },
    "gesture.click": {
        "en": "Click",
        "zh_CN": "点击",
        "zh_TW": "點擊",
        "ja": "クリック",
        "ko": "클릭",
    },
    "gesture.double_click": {
        "en": "Double Click",
        "zh_CN": "双击",
        "zh_TW": "雙擊",
        "ja": "ダブルクリック",
        "ko": "더블클릭",
    },
    "gesture.right_click": {
        "en": "Right Click",
        "zh_CN": "右键",
        "zh_TW": "右鍵",
        "ja": "右クリック",
        "ko": "우클릭",
    },
    "gesture.dragging": {
        "en": "Dragging",
        "zh_CN": "拖拽中",
        "zh_TW": "拖曳中",
        "ja": "ドラッグ中",
        "ko": "드래그 중",
    },
    "gesture.scroll": {
        "en": "Scroll Mode",
        "zh_CN": "滚动模式",
        "zh_TW": "滾動模式",
        "ja": "スクロールモード",
        "ko": "스크롤 모드",
    },
    "gesture.scroll_up": {
        "en": "Scrolling Up",
        "zh_CN": "向上滚动",
        "zh_TW": "向上滾動",
        "ja": "上にスクロール",
        "ko": "위로 스크롤",
    },
    "gesture.scroll_down": {
        "en": "Scrolling Down",
        "zh_CN": "向下滚动",
        "zh_TW": "向下滾動",
        "ja": "下にスクロール",
        "ko": "아래로 스크롤",
    },
    "gesture.palm": {
        "en": "Pause Control",
        "zh_CN": "暂停控制",
        "zh_TW": "暫停控制",
        "ja": "制御一時停止",
        "ko": "제어 일시정지",
    },
    "gesture.fist": {
        "en": "Rest",
        "zh_CN": "休息",
        "zh_TW": "休息",
        "ja": "休止",
        "ko": "휴식",
    },
    # ========== 状态信息 ==========
    "status.paused": {
        "en": "PAUSED",
        "zh_CN": "已暂停",
        "zh_TW": "已暫停",
        "ja": "一時停止",
        "ko": "일시정지",
    },
    "status.running": {
        "en": "Running",
        "zh_CN": "运行中",
        "zh_TW": "運行中",
        "ja": "実行中",
        "ko": "실행 중",
    },
    "status.connecting": {
        "en": "Connecting...",
        "zh_CN": "连接中...",
        "zh_TW": "連接中...",
        "ja": "接続中...",
        "ko": "연결 중...",
    },
    "status.camera_error": {
        "en": "Camera Error",
        "zh_CN": "摄像头错误",
        "zh_TW": "攝像頭錯誤",
        "ja": "カメラエラー",
        "ko": "카메라 오류",
    },
    # ========== 设置界面 ==========
    "settings.title": {
        "en": "Settings",
        "zh_CN": "设置",
        "zh_TW": "設定",
        "ja": "設定",
        "ko": "설정",
    },
    "settings.general": {
        "en": "General",
        "zh_CN": "通用",
        "zh_TW": "一般",
        "ja": "一般",
        "ko": "일반",
    },
    "settings.gestures": {
        "en": "Gestures",
        "zh_CN": "手势",
        "zh_TW": "手勢",
        "ja": "ジェスチャー",
        "ko": "제스처",
    },
    "settings.language": {
        "en": "Language",
        "zh_CN": "语言",
        "zh_TW": "語言",
        "ja": "言語",
        "ko": "언어",
    },
    "settings.sensitivity": {
        "en": "Sensitivity",
        "zh_CN": "灵敏度",
        "zh_TW": "靈敏度",
        "ja": "感度",
        "ko": "민감도",
    },
    "settings.smoothing": {
        "en": "Smoothing",
        "zh_CN": "平滑度",
        "zh_TW": "平滑度",
        "ja": "スムージング",
        "ko": "부드러움",
    },
    "settings.scroll_speed": {
        "en": "Scroll Speed",
        "zh_CN": "滚动速度",
        "zh_TW": "滾動速度",
        "ja": "スクロール速度",
        "ko": "스크롤 속도",
    },
    "settings.flip_x": {
        "en": "Horizontal Mirror",
        "zh_CN": "水平镜像",
        "zh_TW": "水平鏡像",
        "ja": "左右反転",
        "ko": "좌우 반전",
    },
    "settings.flip_y": {
        "en": "Vertical Mirror",
        "zh_CN": "垂直镜像",
        "zh_TW": "垂直鏡像",
        "ja": "上下反転",
        "ko": "상하 반전",
    },
    "settings.show_skeleton": {
        "en": "Show Hand Skeleton",
        "zh_CN": "显示手部骨架",
        "zh_TW": "顯示手部骨架",
        "ja": "手の骨格を表示",
        "ko": "손 골격 표시",
    },
    "settings.show_fps": {
        "en": "Show FPS",
        "zh_CN": "显示帧率",
        "zh_TW": "顯示幀率",
        "ja": "FPSを表示",
        "ko": "FPS 표시",
    },
    "settings.save": {
        "en": "Save",
        "zh_CN": "保存",
        "zh_TW": "儲存",
        "ja": "保存",
        "ko": "저장",
    },
    "settings.cancel": {
        "en": "Cancel",
        "zh_CN": "取消",
        "zh_TW": "取消",
        "ja": "キャンセル",
        "ko": "취소",
    },
    "settings.apply": {
        "en": "Apply",
        "zh_CN": "应用",
        "zh_TW": "套用",
        "ja": "適用",
        "ko": "적용",
    },
    "settings.reset": {
        "en": "Reset to Default",
        "zh_CN": "恢复默认",
        "zh_TW": "恢復預設",
        "ja": "デフォルトに戻す",
        "ko": "기본값으로 복원",
    },
    "settings.mirroring": {
        "en": "Mirroring",
        "zh_CN": "镜像设置",
        "zh_TW": "鏡像設定",
        "ja": "ミラーリング",
        "ko": "미러링",
    },
    "settings.control": {
        "en": "Control",
        "zh_CN": "控制",
        "zh_TW": "控制",
        "ja": "コントロール",
        "ko": "컨트롤",
    },
    "settings.interface": {
        "en": "Interface",
        "zh_CN": "界面",
        "zh_TW": "介面",
        "ja": "インターフェース",
        "ko": "인터페이스",
    },
    "settings.about": {
        "en": "About",
        "zh_CN": "关于",
        "zh_TW": "關於",
        "ja": "について",
        "ko": "정보",
    },
    "settings.language_change_title": {
        "en": "Language Changed",
        "zh_CN": "语言已更改",
        "zh_TW": "語言已更改",
        "ja": "言語が変更されました",
        "ko": "언어가 변경되었습니다",
    },
    "settings.language_change_message": {
        "en": "Language changed. Restart now to apply?",
        "zh_CN": "语言已更改，是否立即重启应用？",
        "zh_TW": "語言已更改，是否立即重新啟動應用程式？",
        "ja": "言語が変更されました。今すぐ再起動して適用しますか？",
        "ko": "언어가 변경되었습니다. 지금 다시 시작하여 적용하시겠습니까?",
    },
    "settings.restart_failed": {
        "en": "Failed to restart application",
        "zh_CN": "重启应用失败",
        "zh_TW": "重新啟動應用程式失敗",
        "ja": "アプリケーションの再起動に失敗しました",
        "ko": "애플리케이션을 다시 시작하지 못했습니다",
    },
    # ========== 托盘菜单 ==========
    "tray.show_hide": {
        "en": "Show/Hide Window",
        "zh_CN": "显示/隐藏窗口",
        "zh_TW": "顯示/隱藏視窗",
        "ja": "ウィンドウを表示/非表示",
        "ko": "창 표시/숨기기",
    },
    "tray.pause": {
        "en": "Pause",
        "zh_CN": "暂停",
        "zh_TW": "暫停",
        "ja": "一時停止",
        "ko": "일시정지",
    },
    "tray.resume": {
        "en": "Resume",
        "zh_CN": "恢复",
        "zh_TW": "恢復",
        "ja": "再開",
        "ko": "재개",
    },
    "tray.settings": {
        "en": "Settings",
        "zh_CN": "设置",
        "zh_TW": "設定",
        "ja": "設定",
        "ko": "설정",
    },
    "tray.quit": {
        "en": "Quit",
        "zh_CN": "退出",
        "zh_TW": "退出",
        "ja": "終了",
        "ko": "종료",
    },
    # ========== 快捷键提示 ==========
    "hotkey.quit": {
        "en": "Q - Quit",
        "zh_CN": "Q - 退出",
        "zh_TW": "Q - 退出",
        "ja": "Q - 終了",
        "ko": "Q - 종료",
    },
    "hotkey.pause": {
        "en": "P - Pause/Resume",
        "zh_CN": "P - 暂停/恢复",
        "zh_TW": "P - 暫停/恢復",
        "ja": "P - 一時停止/再開",
        "ko": "P - 일시정지/재개",
    },
    "hotkey.toggle_window": {
        "en": "V - Show/Hide Window",
        "zh_CN": "V - 显示/隐藏窗口",
        "zh_TW": "V - 顯示/隱藏視窗",
        "ja": "V - ウィンドウ表示/非表示",
        "ko": "V - 창 표시/숨기기",
    },
    # ========== 提示和警告 ==========
    "warning.wayland": {
        "en": "Wayland session detected. Some features may not work.",
        "zh_CN": "检测到 Wayland 会话，部分功能可能无法使用。",
        "zh_TW": "偵測到 Wayland 會話，部分功能可能無法使用。",
        "ja": "Waylandセッションが検出されました。一部の機能が動作しない場合があります。",
        "ko": "Wayland 세션이 감지되었습니다. 일부 기능이 작동하지 않을 수 있습니다.",
    },
    "warning.camera_not_found": {
        "en": "Camera not found",
        "zh_CN": "未找到摄像头",
        "zh_TW": "未找到攝像頭",
        "ja": "カメラが見つかりません",
        "ko": "카메라를 찾을 수 없음",
    },
    "info.started": {
        "en": "LyraPointer started",
        "zh_CN": "LyraPointer 已启动",
        "zh_TW": "LyraPointer 已啟動",
        "ja": "LyraPointerが起動しました",
        "ko": "LyraPointer 시작됨",
    },
    "info.stopped": {
        "en": "LyraPointer stopped",
        "zh_CN": "LyraPointer 已停止",
        "zh_TW": "LyraPointer 已停止",
        "ja": "LyraPointerが停止しました",
        "ko": "LyraPointer 중지됨",
    },
    # ========== 手势说明 ==========
    "help.pointer": {
        "en": "Index finger pointing → Move cursor",
        "zh_CN": "食指指向 → 移动鼠标",
        "zh_TW": "食指指向 → 移動滑鼠",
        "ja": "人差し指で指す → カーソル移動",
        "ko": "검지 손가락 → 커서 이동",
    },
    "help.click": {
        "en": "Thumb + Index pinch → Left click",
        "zh_CN": "拇指+食指捏合 → 左键点击",
        "zh_TW": "拇指+食指捏合 → 左鍵點擊",
        "ja": "親指+人差し指でつまむ → 左クリック",
        "ko": "엄지 + 검지 집기 → 좌클릭",
    },
    "help.right_click": {
        "en": "Thumb + Middle pinch → Right click",
        "zh_CN": "拇指+中指捏合 → 右键点击",
        "zh_TW": "拇指+中指捏合 → 右鍵點擊",
        "ja": "親指+中指でつまむ → 右クリック",
        "ko": "엄지 + 중지 집기 → 우클릭",
    },
    "help.scroll": {
        "en": "Index + Middle extended → Scroll mode",
        "zh_CN": "食指+中指伸出 → 滚动模式",
        "zh_TW": "食指+中指伸出 → 滾動模式",
        "ja": "人差し指+中指を伸ばす → スクロールモード",
        "ko": "검지 + 중지 펴기 → 스크롤 모드",
    },
    "help.palm": {
        "en": "Open palm → Pause/Resume",
        "zh_CN": "五指张开 → 暂停/恢复",
        "zh_TW": "五指張開 → 暫停/恢復",
        "ja": "手のひらを開く → 一時停止/再開",
        "ko": "손바닥 펴기 → 일시정지/재개",
    },
    "help.fist": {
        "en": "Fist → Rest (no action)",
        "zh_CN": "握拳 → 休息（无操作）",
        "zh_TW": "握拳 → 休息（無操作）",
        "ja": "グー → 休止（操作なし）",
        "ko": "주먹 → 휴식 (동작 없음)",
    },
}


class I18n:
    """
    国际化管理器

    提供翻译和语言切换功能。

    Example:
        >>> i18n = I18n()
        >>> i18n.set_language(Language.ZH_CN)
        >>> print(i18n.t("gesture.click"))  # 输出: 点击
    """

    def __init__(self, default_language: Language = Language.EN):
        """
        初始化国际化管理器

        Args:
            default_language: 默认语言
        """
        self._language = default_language
        self._translations = TRANSLATIONS.copy()
        self._fallback_language = Language.EN
        self._change_callbacks: List[Callable[[Language], None]] = []

    @property
    def language(self) -> Language:
        """获取当前语言"""
        return self._language

    @property
    def language_code(self) -> str:
        """获取当前语言代码"""
        return self._language.value

    def set_language(self, language: Language):
        """
        设置语言

        Args:
            language: 目标语言
        """
        if language != self._language:
            self._language = language
            # 触发语言变化回调
            for callback in self._change_callbacks:
                try:
                    callback(language)
                except Exception:
                    pass

    def set_language_by_code(self, code: str) -> bool:
        """
        通过语言代码设置语言

        Args:
            code: 语言代码 (如 "en", "zh_CN")

        Returns:
            是否设置成功
        """
        for lang in Language:
            if lang.value == code:
                self.set_language(lang)
                return True
        return False

    def t(self, key: str, **kwargs) -> str:
        """
        翻译文本

        Args:
            key: 翻译键
            **kwargs: 格式化参数

        Returns:
            翻译后的文本
        """
        return self.translate(key, **kwargs)

    def translate(self, key: str, **kwargs) -> str:
        """
        翻译文本

        Args:
            key: 翻译键
            **kwargs: 格式化参数

        Returns:
            翻译后的文本
        """
        if key not in self._translations:
            return key

        translations = self._translations[key]
        lang_code = self._language.value

        # 尝试获取当前语言的翻译
        if lang_code in translations:
            text = translations[lang_code]
        # 回退到默认语言
        elif self._fallback_language.value in translations:
            text = translations[self._fallback_language.value]
        else:
            return key

        # 格式化
        if kwargs:
            try:
                text = text.format(**kwargs)
            except (KeyError, ValueError):
                pass

        return text

    def add_translation(self, key: str, translations: Dict[str, str]):
        """
        添加翻译

        Args:
            key: 翻译键
            translations: 语言代码到翻译文本的映射
        """
        self._translations[key] = translations

    def add_translations(self, translations: Dict[str, Dict[str, str]]):
        """
        批量添加翻译

        Args:
            translations: 翻译字典
        """
        self._translations.update(translations)

    def on_language_change(self, callback: Callable[[Language], None]):
        """
        注册语言变化回调

        Args:
            callback: 回调函数
        """
        self._change_callbacks.append(callback)

    def get_available_languages(self) -> List[LanguageInfo]:
        """
        获取可用语言列表

        Returns:
            语言信息列表
        """
        return [LANGUAGE_INFO[lang] for lang in Language]

    def get_language_info(self, language: Optional[Language] = None) -> LanguageInfo:
        """
        获取语言信息

        Args:
            language: 语言，如果为 None 则返回当前语言信息

        Returns:
            语言信息
        """
        if language is None:
            language = self._language
        return LANGUAGE_INFO[language]

    def detect_system_language(self) -> Language:
        """
        检测系统语言

        Returns:
            检测到的语言
        """
        import locale

        try:
            # 获取系统语言设置
            lang_code = locale.getdefaultlocale()[0]

            if lang_code:
                lang_code = lang_code.lower()

                # 匹配语言
                if lang_code.startswith("zh_cn") or lang_code == "zh":
                    return Language.ZH_CN
                elif lang_code.startswith("zh_tw") or lang_code.startswith("zh_hk"):
                    return Language.ZH_TW
                elif lang_code.startswith("ja"):
                    return Language.JA
                elif lang_code.startswith("ko"):
                    return Language.KO
        except Exception:
            pass

        return Language.EN

    def auto_detect_and_set(self):
        """自动检测并设置系统语言"""
        detected = self.detect_system_language()
        self.set_language(detected)


# 全局 i18n 实例
_global_i18n: Optional[I18n] = None


def get_i18n() -> I18n:
    """获取全局 i18n 实例"""
    global _global_i18n
    if _global_i18n is None:
        _global_i18n = I18n()
    return _global_i18n


def t(key: str, **kwargs) -> str:
    """
    便捷翻译函数

    Args:
        key: 翻译键
        **kwargs: 格式化参数

    Returns:
        翻译后的文本

    Example:
        >>> print(t("gesture.click"))
    """
    return get_i18n().t(key, **kwargs)


def set_language(language: Language):
    """便捷函数：设置语言"""
    get_i18n().set_language(language)


def get_language() -> Language:
    """便捷函数：获取当前语言"""
    return get_i18n().language


def get_available_languages() -> List[LanguageInfo]:
    """便捷函数：获取可用语言列表"""
    return get_i18n().get_available_languages()
