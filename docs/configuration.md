# LyraPointer 配置详解

本文档详细介绍 LyraPointer 的所有配置选项和自定义方法。

---

## 目录

1. [配置文件位置](#配置文件位置)
2. [配置结构概览](#配置结构概览)
3. [手势配置](#手势配置)
4. [控制设置](#控制设置)
5. [摄像头设置](#摄像头设置)
6. [性能设置](#性能设置)
7. [界面设置](#界面设置)
8. [配置示例](#配置示例)
9. [配置技巧](#配置技巧)

---

## 配置文件位置

LyraPointer 的主配置文件位于：

```
LyraPointer/
└── config/
    └── gestures.yaml    # 主配置文件
```

配置文件使用 YAML 格式，易于阅读和编辑。

---

## 配置结构概览

```yaml
# 版本号
version: "1.0"

# 手势定义
gestures:
  ...

# 控制设置
settings:
  ...

# 界面设置
ui:
  ...
```

---

## 手势配置

### 基本结构

```yaml
gestures:
  # 手势名称
  gesture_name:
    description: "手势描述"
    type: "pinch"          # 手势类型（可选）
    fingers: [...]         # 涉及的手指
    threshold: 0.05        # 阈值
    action: "action_name"  # 触发的动作
    hold_frames: 3         # 需要保持的帧数
```

### 手势类型

| 类型 | 说明 | 示例 |
|------|------|------|
| `pinch` | 两指捏合 | 点击、右键 |
| `extended` | 手指伸出 | 指针、滚动 |
| `all` | 所有手指 | 握拳、张开手掌 |

### 可用动作

| 动作 | 说明 |
|------|------|
| `move_cursor` | 移动鼠标光标 |
| `left_click` | 左键单击 |
| `right_click` | 右键单击 |
| `double_click` | 左键双击 |
| `scroll_mode` | 进入滚动模式 |
| `toggle_pause` | 切换暂停状态 |
| `none` | 无操作 |

### 手势配置示例

```yaml
gestures:
  # 指针模式 - 食指伸出控制鼠标
  pointer:
    description: "指针模式 - 控制鼠标移动"
    fingers:
      index: true
      middle: false
      ring: false
      pinky: false
    action: "move_cursor"
    
  # 左键点击 - 拇指食指捏合
  click:
    description: "点击 - 拇指食指捏合"
    type: "pinch"
    fingers: ["thumb", "index"]
    threshold: 0.05        # 捏合距离阈值
    action: "left_click"
    hold_frames: 3         # 防止误触
    
  # 右键点击 - 拇指中指捏合
  right_click:
    description: "右键 - 拇指中指捏合"
    type: "pinch"
    fingers: ["thumb", "middle"]
    threshold: 0.05
    action: "right_click"
    hold_frames: 3
    
  # 滚动模式 - 食指中指伸出
  scroll:
    description: "滚动模式 - 上下移动滚动"
    fingers:
      index: true
      middle: true
      ring: false
      pinky: false
    action: "scroll_mode"
    
  # 暂停控制 - 五指张开
  pause:
    description: "暂停/恢复控制"
    fingers:
      thumb: true
      index: true
      middle: true
      ring: true
      pinky: true
    action: "toggle_pause"
    hold_frames: 10        # 需要保持较长时间
    
  # 休息状态 - 握拳
  fist:
    description: "休息状态 - 无操作"
    fingers:
      thumb: false
      index: false
      middle: false
      ring: false
      pinky: false
    action: "none"
```

---

## 控制设置

### 灵敏度 (sensitivity)

控制鼠标移动的速度比例。

```yaml
settings:
  sensitivity: 1.5
```

| 值 | 效果 |
|---|------|
| 0.1 - 0.5 | 非常慢，适合精细操作 |
| 0.5 - 1.0 | 较慢，更精确 |
| 1.0 - 1.5 | 正常速度（推荐） |
| 1.5 - 3.0 | 较快，适合大屏幕 |
| 3.0 - 5.0 | 非常快，可能难以控制 |

**建议**: 从 1.5 开始，根据个人习惯调整。

### 平滑度 (smoothing)

控制鼠标移动的平滑程度，平衡抖动和延迟。

```yaml
settings:
  smoothing: 0.7
```

| 值 | 效果 |
|---|------|
| 0.0 - 0.3 | 低平滑，响应快但可能抖动 |
| 0.3 - 0.6 | 中等平滑（日常使用） |
| 0.6 - 0.8 | 高平滑，稳定但有延迟 |
| 0.8 - 0.99 | 非常平滑，明显延迟 |

**建议**: 0.6 - 0.8 适合大多数人。如果抖动严重，增加此值。

### 双击间隔 (double_click_interval)

两次点击被识别为双击的最大间隔时间（毫秒）。

```yaml
settings:
  double_click_interval: 300
```

**范围**: 100 - 500 ms  
**推荐**: 250 - 350 ms

### 滚动速度 (scroll_speed)

每次滚动的行数。

```yaml
settings:
  scroll_speed: 5
```

**范围**: 1 - 20  
**推荐**: 3 - 8

### 控制区域 (control_zone)

定义摄像头画面中可以触发控制的区域（归一化坐标 0-1）。

```yaml
settings:
  control_zone:
    x_min: 0.15    # 左边界
    x_max: 0.85    # 右边界
    y_min: 0.15    # 上边界
    y_max: 0.85    # 下边界
```

**说明**:
- 只有手在此区域内时才会控制鼠标
- 设置较小的区域可以避免边缘误触
- 区域越小，手的移动范围越集中

**常用配置**:

```yaml
# 大控制区域（适合经验用户）
control_zone:
  x_min: 0.1
  x_max: 0.9
  y_min: 0.1
  y_max: 0.9

# 小控制区域（适合新手，减少误触）
control_zone:
  x_min: 0.2
  x_max: 0.8
  y_min: 0.2
  y_max: 0.8

# 中心区域（舒适操作）
control_zone:
  x_min: 0.25
  x_max: 0.75
  y_min: 0.2
  y_max: 0.8
```

---

## 摄像头设置

```yaml
settings:
  camera:
    index: 0       # 摄像头索引
    width: 640     # 分辨率宽度
    height: 480    # 分辨率高度
    fps: 30        # 帧率
    flip_x: true   # 水平镜像
    flip_y: false  # 垂直镜像
```

### 摄像头索引 (index)

如果有多个摄像头，可以通过索引选择：

| 索引 | 说明 |
|------|------|
| 0 | 默认摄像头（通常是内置） |
| 1 | 第二个摄像头（通常是外接） |
| 2+ | 更多摄像头 |

### 分辨率

| 分辨率 | 性能 | 精度 | 推荐场景 |
|--------|------|------|----------|
| 320x240 | 最快 | 低 | 低性能设备 |
| 640x480 | 快 | 中 | **推荐大多数用户** |
| 1280x720 | 慢 | 高 | 高性能设备 |

### 镜像设置

```yaml
camera:
  flip_x: true   # 水平翻转（镜像效果）
  flip_y: false  # 垂直翻转
```

**建议**: 保持 `flip_x: true` 以获得自然的镜像效果。

---

## 性能设置

```yaml
settings:
  performance:
    process_interval: 1        # 处理间隔
    model_complexity: 0        # 模型复杂度
    detection_confidence: 0.7  # 检测置信度
    tracking_confidence: 0.5   # 追踪置信度
```

### 处理间隔 (process_interval)

每隔几帧处理一次（用于低性能设备）。

| 值 | 说明 |
|----|------|
| 1 | 每帧处理（默认） |
| 2 | 隔帧处理 |
| 3 | 每3帧处理一次 |

**建议**: 正常设备用 1，低性能设备可以尝试 2。

### 模型复杂度 (model_complexity)

MediaPipe 手部检测模型的复杂度。

| 值 | 说明 | 性能 | 精度 |
|----|------|------|------|
| 0 | Lite 模型 | 快 | 一般 |
| 1 | Full 模型 | 慢 | 较高 |

**建议**: 大多数情况下使用 0。

### 置信度设置

```yaml
detection_confidence: 0.7   # 新手检测的置信度阈值
tracking_confidence: 0.5    # 追踪时的置信度阈值
```

- **detection_confidence**: 越高越严格，可能漏检
- **tracking_confidence**: 越高越稳定，但可能丢失追踪

**推荐值**: 
- detection: 0.6 - 0.8
- tracking: 0.4 - 0.6

---

## 界面设置

```yaml
ui:
  language: "zh_CN"           # 界面语言
  show_visualizer: true       # 显示可视化窗口
  show_skeleton: true         # 显示手部骨架
  show_gesture_info: true     # 显示手势信息
  show_control_zone: true     # 显示控制区域
  show_fps: true              # 显示帧率
```

### 支持的语言

| 代码 | 语言 |
|------|------|
| `en` | English |
| `zh_CN` | 简体中文 |
| `zh_TW` | 繁體中文 |
| `ja` | 日本語 |
| `ko` | 한국어 |

### 显示选项

| 选项 | 说明 |
|------|------|
| show_visualizer | 是否显示摄像头预览窗口 |
| show_skeleton | 是否在预览中显示手部骨架 |
| show_gesture_info | 是否显示当前识别的手势 |
| show_control_zone | 是否显示控制区域边框 |
| show_fps | 是否显示帧率 |

---

## 配置示例

### 新手友好配置

```yaml
version: "1.0"

settings:
  sensitivity: 1.2
  smoothing: 0.8
  scroll_speed: 3
  control_zone:
    x_min: 0.2
    x_max: 0.8
    y_min: 0.2
    y_max: 0.8
  camera:
    width: 640
    height: 480
  performance:
    model_complexity: 0
    detection_confidence: 0.7

ui:
  show_skeleton: true
  show_fps: true
```

### 高性能配置

```yaml
version: "1.0"

settings:
  sensitivity: 1.8
  smoothing: 0.5
  scroll_speed: 6
  control_zone:
    x_min: 0.1
    x_max: 0.9
    y_min: 0.1
    y_max: 0.9
  camera:
    width: 1280
    height: 720
  performance:
    model_complexity: 1
    detection_confidence: 0.6
    tracking_confidence: 0.4

ui:
  show_skeleton: false
  show_fps: true
```

### 低性能设备配置

```yaml
version: "1.0"

settings:
  sensitivity: 1.5
  smoothing: 0.7
  scroll_speed: 5
  camera:
    width: 320
    height: 240
    fps: 20
  performance:
    process_interval: 2
    model_complexity: 0
    detection_confidence: 0.6

ui:
  show_skeleton: false
  show_control_zone: false
  show_fps: true
```

---

## 配置技巧

### 1. 减少抖动

如果鼠标抖动严重：

```yaml
settings:
  smoothing: 0.85        # 增加平滑度
  sensitivity: 1.2       # 降低灵敏度
```

### 2. 减少延迟

如果感觉延迟明显：

```yaml
settings:
  smoothing: 0.5         # 降低平滑度
  performance:
    process_interval: 1  # 每帧处理
```

### 3. 提高识别准确率

```yaml
settings:
  performance:
    model_complexity: 1         # 使用完整模型
    detection_confidence: 0.8   # 提高置信度
```

### 4. 在低光环境下使用

```yaml
settings:
  performance:
    detection_confidence: 0.5   # 降低检测阈值
    tracking_confidence: 0.3    # 降低追踪阈值
```

### 5. 使用大屏幕/多显示器

```yaml
settings:
  sensitivity: 2.5       # 增加灵敏度
  control_zone:
    x_min: 0.05
    x_max: 0.95          # 扩大控制区域
```

---

## 配置热重载

修改配置文件后，可以通过以下方式应用：

1. **通过设置界面保存** - 自动应用部分设置
2. **重启程序** - 应用所有设置

部分设置（如灵敏度、平滑度）可以即时生效，而摄像头设置需要重启。

---

## 下一步

- [手势说明](gestures.md) - 详细了解手势操作
- [故障排除](troubleshooting.md) - 解决常见问题
- [插件开发](plugins.md) - 创建自定义功能