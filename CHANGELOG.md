# Changelog

All notable changes to LyraPointer will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### Added
- Wayland environment detection and warning message at startup
- Comprehensive logging system with file rotation (`src/utils/logging.py`)
- Event system for decoupled architecture (`src/core/events.py`)
- State machine for gesture control flow (`src/core/state_machine.py`)
- Plugin system for custom gestures and actions (`src/plugins/`)
- Configuration validator with detailed error messages (`src/config/validator.py`)
- Audio feedback system (`src/feedback/audio.py`)
- Wayland mouse controller using ydotool (`src/control/wayland_mouse.py`)
- Gesture recorder for recording and playback (`src/gestures/recorder.py`)
- Custom exception classes (`src/exceptions.py`)
- Unit tests for gestures, smoother, and events
- Comprehensive documentation in `docs/` directory
- `IMPROVEMENTS.md` with detailed improvement suggestions

### Fixed
- Fixed missing `SettingsWindow` export in `src/ui/__init__.py`
- Fixed system tray error handling to prevent stack traces on Wayland
- Improved error handling throughout the codebase

### Changed
- Improved code formatting and style consistency
- Enhanced system tray to silently handle initialization failures
- Updated `src/config/__init__.py` to include validator exports

---

## [1.0.0] - 2025-01-01

### Added
- Initial release of LyraPointer
- Hand tracking using MediaPipe
- Gesture detection for pointer, click, double-click, right-click, drag, scroll
- One Euro Filter for smooth cursor movement
- System tray integration with pystray
- Settings window using Tkinter
- YAML configuration file support
- Real-time visualization with OpenCV
- Multi-monitor support via screeninfo
- Keyboard shortcuts (Q to quit, P to pause, V to toggle window)

### Supported Gestures
- 👆 Index finger pointing → Move cursor
- 👌 Thumb + index pinch → Left click
- 🤏 Thumb + middle pinch → Right click
- 👌👌 Quick double pinch → Double click
- 👌→ Pinch and hold → Drag
- ✌️ Index + middle extended → Scroll mode
- ✋ Open palm → Pause/Resume
- ✊ Fist → Rest (no action)

### Supported Platforms
- Linux (X11)
- Windows
- macOS

### Dependencies
- Python 3.11 or 3.12
- opencv-python >= 4.8.0
- mediapipe >= 0.10.0
- pyautogui >= 0.9.54
- pynput >= 1.7.6
- pystray >= 0.19.0
- Pillow >= 10.0.0
- PyYAML >= 6.0
- numpy >= 1.24.0
- screeninfo >= 0.8.1

---

## Version History Summary

| Version | Date | Description |
|---------|------|-------------|
| 1.0.0 | 2025-01-01 | Initial release with core functionality |
| 1.1.0 | Unreleased | Event system, plugins, improved stability |

---

## Upgrade Notes

### Upgrading from 1.0.0 to 1.1.0

1. **New Dependencies**: No new required dependencies, but optional features may require:
   - `simpleaudio` for audio feedback
   - `ydotool` for Wayland support

2. **Configuration**: Existing `config/gestures.yaml` files are fully compatible.

3. **Breaking Changes**: None. All existing functionality preserved.

---

## Future Plans

See [IMPROVEMENTS.md](IMPROVEMENTS.md) for planned features and improvements.

### High Priority
- Camera reconnection mechanism
- Enhanced Wayland support

### Medium Priority
- Multi-hand support
- Custom gesture recording

### Low Priority
- Air keyboard
- Application-specific profiles

---

## Contributing

When contributing, please update this changelog with your changes under the `[Unreleased]` section.

Categories:
- `Added` for new features
- `Changed` for changes in existing functionality
- `Deprecated` for soon-to-be removed features
- `Removed` for now removed features
- `Fixed` for any bug fixes
- `Security` for vulnerability fixes