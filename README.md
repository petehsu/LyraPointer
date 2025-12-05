# LyraPointer - Gesture Control System

[中文文档](README_zh-CN.md)

🖐️ Control your computer completely with hand gestures using a webcam. No mouse or touchpad required.

LyraPointer is a Python-based application that uses computer vision to track hand movements and map them to system mouse and keyboard actions. It is designed to be a complete mouse replacement.

## ✨ Features

- ✅ **Complete Mouse Replacement**: Move, click, double-click, right-click, drag, and scroll.
- ✅ **Customizable Gestures**: Configure gesture-to-action mappings via YAML.
- ✅ **Visual Feedback**: Real-time visualization of hand skeleton and gesture status.
- ✅ **Background Operation**: Minimizes to system tray.
- ✅ **Optimized Performance**: Smooth tracking with One Euro Filter, optimized for entry-level GPUs (e.g., MX350).

## 🛠️ Tech Stack & Open Source Projects

LyraPointer is built on the shoulders of giants. We gratefully acknowledge the following open-source projects:

- **[MediaPipe](https://github.com/google/mediapipe)** (Apache-2.0): For robust and real-time hand tracking.
- **[OpenCV](https://github.com/opencv/opencv)** (Apache-2.0): For image processing and camera input.
- **[PyAutoGUI](https://github.com/asweigart/pyautogui)** (BSD): For cross-platform mouse and keyboard control.
- **[pystray](https://github.com/moses-palmer/pystray)** (LGPL/MIT): For system tray integration.
- **[One Euro Filter](https://gery.casiez.net/1euro/)**: For adaptive jitter reduction and smoothing.

## 📋 Requirements

- **Python 3.11 or 3.12** (MediaPipe does not support Python 3.13 yet)
- Webcam
- Linux / Windows / macOS

## 🚀 Installation

### Arch Linux

```bash
# Install Python 3.12
sudo pacman -S python312

# Create virtual environment
python3.12 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Ubuntu/Debian

```bash
# Install dependencies
sudo apt install python3-pip python3-venv

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Windows

```powershell
# Create virtual environment
python -m venv .venv
.venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## 🎮 Usage

```bash
# Activate virtual environment
source .venv/bin/activate

# Run LyraPointer
python run.py
```

### Default Gestures

| Gesture | Action |
|---------|--------|
| 👆 Index Finger Pointing | Move Cursor |
| 👌 Thumb + Index Pinch | Left Click |
| 🤏 Thumb + Middle Pinch | Right Click |
| ✌️ Index + Middle Extended | Scroll Mode (Move hand up/down) |
| ✋ Open Palm | Pause/Resume Control |
| ✊ Fist | Rest (No action) |

### Shortcuts

- `Q` - Quit application
- `P` - Pause/Resume control
- `V` - Show/Hide visualizer window

## ⚙️ Configuration

You can customize gestures, sensitivity, and other settings in `config/gestures.yaml`.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
