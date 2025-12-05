# LyraPointer 安装指南

本文档详细介绍如何在不同操作系统上安装和配置 LyraPointer。

---

## 目录

1. [系统要求](#系统要求)
2. [Linux 安装](#linux-安装)
3. [Windows 安装](#windows-安装)
4. [macOS 安装](#macos-安装)
5. [验证安装](#验证安装)
6. [常见问题](#常见问题)

---

## 系统要求

### 硬件要求

| 组件 | 最低要求 | 推荐配置 |
|------|----------|----------|
| CPU | 双核 2.0 GHz | 四核 2.5 GHz+ |
| 内存 | 4 GB | 8 GB+ |
| 摄像头 | 480p USB/内置 | 720p+ |
| GPU | 集成显卡 | 独立显卡（可选） |

### 软件要求

| 软件 | 版本要求 | 说明 |
|------|----------|------|
| Python | 3.11 或 3.12 | MediaPipe 不支持 3.13 |
| pip | 20.0+ | Python 包管理器 |
| Git | 2.0+ | 用于克隆仓库（可选） |

### 支持的操作系统

- **Linux**: Ubuntu 20.04+, Debian 11+, Arch Linux, Fedora 35+
- **Windows**: Windows 10/11 (64-bit)
- **macOS**: macOS 11 Big Sur+

---

## Linux 安装

### Arch Linux

```bash
# 1. 安装 Python 3.12
sudo pacman -S python312

# 2. 安装系统依赖
sudo pacman -S git opencv

# 3. 克隆项目
git clone https://github.com/your-username/LyraPointer.git
cd LyraPointer

# 4. 创建虚拟环境
python3.12 -m venv .venv
source .venv/bin/activate

# 5. 安装 Python 依赖
pip install --upgrade pip
pip install -r requirements.txt

# 6. 运行
python run.py
```

### Ubuntu / Debian

```bash
# 1. 更新系统
sudo apt update && sudo apt upgrade -y

# 2. 安装依赖
sudo apt install -y \
    python3-pip \
    python3-venv \
    python3-dev \
    git \
    libgl1-mesa-glx \
    libglib2.0-0

# 3. 安装 Python 3.12（如果系统版本不是 3.11/3.12）
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt update
sudo apt install python3.12 python3.12-venv python3.12-dev

# 4. 克隆项目
git clone https://github.com/your-username/LyraPointer.git
cd LyraPointer

# 5. 创建虚拟环境
python3.12 -m venv .venv
source .venv/bin/activate

# 6. 安装 Python 依赖
pip install --upgrade pip
pip install -r requirements.txt

# 7. 运行
python run.py
```

### Fedora

```bash
# 1. 安装依赖
sudo dnf install -y \
    python3.12 \
    python3.12-devel \
    git \
    mesa-libGL

# 2. 克隆项目
git clone https://github.com/your-username/LyraPointer.git
cd LyraPointer

# 3. 创建虚拟环境
python3.12 -m venv .venv
source .venv/bin/activate

# 4. 安装 Python 依赖
pip install --upgrade pip
pip install -r requirements.txt

# 5. 运行
python run.py
```

### Wayland 环境额外配置

如果你使用 Wayland 桌面环境（如 GNOME 40+ 默认），需要额外配置：

```bash
# 方法 1：安装 ydotool（推荐）
# Arch Linux
sudo pacman -S ydotool

# Ubuntu/Debian
sudo apt install ydotool

# 启动 ydotool 守护进程
sudo systemctl enable --now ydotool

# 方法 2：使用 X11 会话运行
XDG_SESSION_TYPE=x11 python run.py
```

---

## Windows 安装

### 方法 1：使用 Python 官方安装包

1. **下载 Python 3.12**
   - 访问 https://www.python.org/downloads/
   - 下载 Python 3.12.x (64-bit)
   - 安装时勾选 "Add Python to PATH"

2. **打开 PowerShell 或命令提示符**

3. **克隆或下载项目**
   ```powershell
   git clone https://github.com/your-username/LyraPointer.git
   cd LyraPointer
   ```

4. **创建虚拟环境**
   ```powershell
   python -m venv .venv
   .venv\Scripts\activate
   ```

5. **安装依赖**
   ```powershell
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

6. **运行**
   ```powershell
   python run.py
   ```

### 方法 2：使用 Anaconda

1. **安装 Anaconda**
   - 下载: https://www.anaconda.com/download
   - 安装并打开 Anaconda Prompt

2. **创建环境**
   ```bash
   conda create -n lyrapointer python=3.12
   conda activate lyrapointer
   ```

3. **安装项目**
   ```bash
   cd path/to/LyraPointer
   pip install -r requirements.txt
   ```

4. **运行**
   ```bash
   python run.py
   ```

---

## macOS 安装

### 使用 Homebrew

```bash
# 1. 安装 Homebrew（如果没有）
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# 2. 安装 Python 3.12
brew install python@3.12

# 3. 克隆项目
git clone https://github.com/your-username/LyraPointer.git
cd LyraPointer

# 4. 创建虚拟环境
python3.12 -m venv .venv
source .venv/bin/activate

# 5. 安装依赖
pip install --upgrade pip
pip install -r requirements.txt

# 6. 运行
python run.py
```

### 权限设置

macOS 需要授予摄像头和辅助功能权限：

1. **摄像头权限**
   - 首次运行时会提示授权
   - 或在 系统偏好设置 → 安全性与隐私 → 隐私 → 摄像头 中添加

2. **辅助功能权限**（用于控制鼠标）
   - 系统偏好设置 → 安全性与隐私 → 隐私 → 辅助功能
   - 添加终端或 Python

---

## 验证安装

### 检查 Python 版本

```bash
python --version
# 应显示 Python 3.11.x 或 Python 3.12.x
```

### 检查依赖安装

```bash
# 激活虚拟环境
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate   # Windows

# 检查关键包
python -c "import cv2; print(f'OpenCV: {cv2.__version__}')"
python -c "import mediapipe; print(f'MediaPipe: {mediapipe.__version__}')"
python -c "import pyautogui; print('PyAutoGUI: OK')"
```

### 检查摄像头

```bash
# 列出可用摄像头（Linux）
ls -la /dev/video*

# 测试摄像头
python -c "
import cv2
cap = cv2.VideoCapture(0)
if cap.isOpened():
    print('Camera OK')
    cap.release()
else:
    print('Camera not found')
"
```

### 运行测试

```bash
# 运行单元测试
pip install pytest
python -m pytest tests/ -v
```

---

## 常见问题

### Q: ModuleNotFoundError: No module named 'cv2'

**原因**: OpenCV 未正确安装

**解决方案**:
```bash
pip uninstall opencv-python opencv-python-headless
pip install opencv-python
```

### Q: MediaPipe 安装失败

**原因**: Python 版本不兼容

**解决方案**:
- 确保使用 Python 3.11 或 3.12
- 不要使用 Python 3.13

```bash
# 检查 Python 版本
python --version

# 如果版本不对，重新创建虚拟环境
python3.12 -m venv .venv --clear
```

### Q: 摄像头无法打开

**Linux**:
```bash
# 检查摄像头设备
ls -la /dev/video*

# 添加用户到 video 组
sudo usermod -aG video $USER
# 然后重新登录
```

**Windows**:
- 检查设备管理器中摄像头是否正常
- 确保没有其他程序占用摄像头

**macOS**:
- 检查系统偏好设置中的摄像头权限

### Q: PyAutoGUI 在 Wayland 下不工作

**解决方案**:
1. 安装 ydotool（推荐）
2. 或切换到 X11 会话
3. 或设置环境变量 `XDG_SESSION_TYPE=x11`

### Q: 系统托盘图标不显示

**Linux (GNOME)**:
```bash
# 安装 AppIndicator 扩展
sudo apt install gnome-shell-extension-appindicator
# 然后在 GNOME Extensions 中启用
```

### Q: 运行时提示权限不足

**Linux**:
```bash
# 给脚本执行权限
chmod +x run.py
```

**Windows**:
- 以管理员身份运行命令提示符

**macOS**:
- 在系统偏好设置中授予辅助功能权限

---

## 可选依赖

### 音频反馈支持

```bash
# 安装音频库
pip install simpleaudio

# 或者
pip install playsound
```

### 开发依赖

```bash
# 测试
pip install pytest pytest-cov

# 代码格式化
pip install black isort

# 类型检查
pip install mypy
```

---

## 下一步

安装完成后，请参阅：

- [快速入门](quickstart.md) - 5 分钟上手教程
- [手势说明](gestures.md) - 了解所有支持的手势
- [配置详解](configuration.md) - 自定义设置

---

## 获取帮助

如果遇到问题：

1. 查看 [故障排除](troubleshooting.md)
2. 搜索 [GitHub Issues](https://github.com/your-username/LyraPointer/issues)
3. 创建新的 Issue 描述你的问题