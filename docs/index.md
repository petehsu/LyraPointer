# LyraPointer 文档

欢迎使用 LyraPointer - 手势控制系统！

🖐️ 用摄像头识别手势，完全替代鼠标控制电脑。

---

## 目录

### 快速开始

- [安装指南](installation.md) - 如何安装和配置 LyraPointer
- [快速入门](quickstart.md) - 5 分钟上手教程
- [手势说明](gestures.md) - 所有支持的手势及用法

### 用户指南

- [配置详解](configuration.md) - 详细的配置选项说明
- [故障排除](troubleshooting.md) - 常见问题解决方案

### 开发者指南

- [开发指南](development.md) - 如何参与开发
- [架构概述](architecture.md) - 项目架构设计
- [API 参考](api/index.md) - 模块和类的 API 文档
- [插件开发](plugins.md) - 如何开发自定义插件

### 其他

- [更新日志](../CHANGELOG.md) - 版本更新记录
- [改进建议](../IMPROVEMENTS.md) - 项目改进计划

---

## 功能特性

- ✅ **完全替代鼠标**：移动、点击、双击、右键、滚动、拖拽
- ✅ **自定义手势**：可配置手势-操作映射
- ✅ **可视化窗口**：实时显示手势识别状态
- ✅ **后台运行**：系统托盘模式
- ✅ **插件系统**：支持自定义手势和动作
- ✅ **事件系统**：解耦的事件驱动架构

---

## 系统要求

| 要求 | 说明 |
|------|------|
| Python | 3.11 或 3.12（MediaPipe 暂不支持 3.13） |
| 摄像头 | 支持 USB 摄像头或内置摄像头 |
| 操作系统 | Linux / Windows / macOS |
| 显示服务器 | X11（推荐）或 Wayland（需要 ydotool） |

---

## 快速安装

```bash
# 克隆项目
git clone https://github.com/your-username/LyraPointer.git
cd LyraPointer

# 创建虚拟环境
python3.12 -m venv .venv
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate   # Windows

# 安装依赖
pip install -r requirements.txt

# 运行
python run.py
```

---

## 默认手势

| 手势 | 操作 | 说明 |
|------|------|------|
| 👆 食指指向 | 移动鼠标 | 只伸出食指 |
| 👌 拇指+食指捏合 | 左键点击 | 两指靠近 |
| 🤏 拇指+中指捏合 | 右键点击 | 两指靠近 |
| 快速捏合两次 | 双击 | 0.3秒内两次 |
| 捏合保持 | 拖拽 | 保持捏合并移动 |
| ✌️ 食指+中指伸出 | 滚动模式 | 上下移动滚动 |
| ✋ 五指张开 | 暂停/恢复 | 保持1秒触发 |
| ✊ 握拳 | 休息状态 | 无操作 |

---

## 快捷键

| 按键 | 功能 |
|------|------|
| `Q` | 退出程序 |
| `P` | 暂停/恢复控制 |
| `V` | 显示/隐藏可视化窗口 |

---

## 项目结构

```
LyraPointer/
├── config/              # 配置文件
│   └── gestures.yaml    # 手势配置
├── src/                 # 源代码
│   ├── config/          # 配置管理
│   ├── control/         # 系统控制（鼠标/键盘）
│   ├── core/            # 核心模块（事件/状态机）
│   ├── feedback/        # 反馈系统（音频）
│   ├── gestures/        # 手势识别
│   ├── plugins/         # 插件系统
│   ├── tracker/         # 手部追踪
│   ├── ui/              # 用户界面
│   └── utils/           # 工具模块
├── tests/               # 测试代码
├── docs/                # 文档
└── run.py               # 启动脚本
```

---

## 技术栈

- **[MediaPipe](https://github.com/google/mediapipe)** - 手部追踪
- **[OpenCV](https://github.com/opencv/opencv)** - 图像处理
- **[PyAutoGUI](https://github.com/asweigart/pyautogui)** - 鼠标/键盘控制
- **[One Euro Filter](https://gery.casiez.net/1euro/)** - 轨迹平滑

---

## 贡献

欢迎贡献代码、报告问题或提出建议！

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 创建 Pull Request

---

## 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](../LICENSE) 文件。

---

## 联系

- 作者：Pete Hsu
- 项目主页：[GitHub](https://github.com/your-username/LyraPointer)

如有问题或建议，请在 GitHub 上创建 Issue。