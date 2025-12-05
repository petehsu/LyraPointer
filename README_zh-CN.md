# LyraPointer - 手势控制系统

🖐️ 用摄像头识别手势，完全替代鼠标控制电脑。

## 功能特性

- ✅ **完全替代鼠标**：移动、点击、双击、右键、滚动、拖拽
- ✅ **自定义手势**：可配置手势-操作映射
- ✅ **可视化窗口**：实时显示手势识别状态
- ✅ **后台运行**：系统托盘模式

## 系统要求

- **Python 3.11 或 3.12**（MediaPipe 暂不支持 Python 3.13）
- 摄像头
- Linux / Windows / macOS

## 安装

### Arch Linux

```bash
# 安装 Python 3.12
sudo pacman -S python312

# 创建虚拟环境
python3.12 -m venv .venv
source .venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

### Ubuntu/Debian

```bash
# 安装依赖
sudo apt install python3-pip python3-venv

# 创建虚拟环境
python3 -m venv .venv
source .venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

### Windows

```powershell
# 创建虚拟环境
python -m venv .venv
.venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt
```

## 运行

```bash
# 启动 LyraPointer
python run.py

# 或者指定参数
python run.py --no-gui  # 无界面模式
python run.py --camera 1  # 指定摄像头
```

## 默认手势

| 手势 | 操作 |
|------|------|
| 食指指向 | 移动鼠标 |
| 拇指+食指捏合 | 左键点击 |
| 拇指+中指捏合 | 右键点击 |
| 快速捏合两次 | 双击 |
| 捏合保持 | 拖拽 |
| 食指+中指伸出 | 滚动模式 |
| 五指张开 | 暂停/恢复控制 |
| 握拳 | 休息状态 |

## 配置

编辑 `config/gestures.yaml` 自定义手势映射和控制参数。

## 快捷键

- `Q` - 退出程序
- `P` - 暂停/恢复控制
- `V` - 显示/隐藏可视化窗口

## 故障排除

### MediaPipe 安装失败

MediaPipe 目前仅支持 Python 3.8-3.12。如果你使用的是 Python 3.13，请安装 Python 3.12：

```bash
# Arch Linux
sudo pacman -S python312

# Ubuntu
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt install python3.12 python3.12-venv
```

### 摄像头权限问题

```bash
# 检查摄像头
ls -la /dev/video*

# 添加用户到 video 组
sudo usermod -aG video $USER
```

### X11 权限问题（PyAutoGUI）

如果使用 Wayland，可能需要切换到 X11 会话，或设置：

```bash
export XDG_SESSION_TYPE=x11
```
