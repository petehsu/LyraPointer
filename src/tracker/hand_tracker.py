"""
手部追踪器 - 封装 MediaPipe Hands

使用 MediaPipe 进行实时手部追踪，返回 21 个手部关键点。
"""

from dataclasses import dataclass
from typing import Optional
import cv2
import mediapipe as mp
import numpy as np


@dataclass
class Point3D:
    """3D 坐标点"""
    x: float
    y: float
    z: float
    
    def to_tuple(self) -> tuple[float, float]:
        """转换为 2D 元组 (x, y)"""
        return (self.x, self.y)
    
    def to_pixel(self, width: int, height: int) -> tuple[int, int]:
        """转换为像素坐标"""
        return (int(self.x * width), int(self.y * height))


@dataclass
class HandLandmarks:
    """手部关键点数据"""
    # 21 个关键点
    landmarks: list[Point3D]
    # 手的类型 (Left/Right)
    handedness: str
    # 置信度
    score: float
    
    # 手指关键点索引
    WRIST = 0
    THUMB_CMC = 1
    THUMB_MCP = 2
    THUMB_IP = 3
    THUMB_TIP = 4
    INDEX_MCP = 5
    INDEX_PIP = 6
    INDEX_DIP = 7
    INDEX_TIP = 8
    MIDDLE_MCP = 9
    MIDDLE_PIP = 10
    MIDDLE_DIP = 11
    MIDDLE_TIP = 12
    RING_MCP = 13
    RING_PIP = 14
    RING_DIP = 15
    RING_TIP = 16
    PINKY_MCP = 17
    PINKY_PIP = 18
    PINKY_DIP = 19
    PINKY_TIP = 20
    
    # 手指名称到关键点的映射
    FINGER_TIPS = {
        "thumb": THUMB_TIP,
        "index": INDEX_TIP,
        "middle": MIDDLE_TIP,
        "ring": RING_TIP,
        "pinky": PINKY_TIP,
    }
    
    FINGER_PIPS = {
        "thumb": THUMB_IP,
        "index": INDEX_PIP,
        "middle": MIDDLE_PIP,
        "ring": RING_PIP,
        "pinky": PINKY_PIP,
    }
    
    FINGER_MCPS = {
        "thumb": THUMB_MCP,
        "index": INDEX_MCP,
        "middle": MIDDLE_MCP,
        "ring": RING_MCP,
        "pinky": PINKY_MCP,
    }
    
    def get_landmark(self, index: int) -> Point3D:
        """获取指定索引的关键点"""
        return self.landmarks[index]
    
    def get_finger_tip(self, finger: str) -> Point3D:
        """获取手指尖端坐标"""
        return self.landmarks[self.FINGER_TIPS[finger]]
    
    def get_finger_pip(self, finger: str) -> Point3D:
        """获取手指中间关节坐标"""
        return self.landmarks[self.FINGER_PIPS[finger]]
    
    def get_finger_mcp(self, finger: str) -> Point3D:
        """获取手指根部关节坐标"""
        return self.landmarks[self.FINGER_MCPS[finger]]
    
    def get_wrist(self) -> Point3D:
        """获取手腕坐标"""
        return self.landmarks[self.WRIST]


class HandTracker:
    """手部追踪器"""
    
    def __init__(
        self,
        max_hands: int = 1,
        model_complexity: int = 0,
        detection_confidence: float = 0.7,
        tracking_confidence: float = 0.5,
    ):
        """
        初始化手部追踪器
        
        Args:
            max_hands: 最大追踪手数
            model_complexity: 模型复杂度 (0=轻量, 1=完整)
            detection_confidence: 检测置信度阈值
            tracking_confidence: 追踪置信度阈值
        """
        self.mp_hands = mp.solutions.hands
        self.mp_drawing = mp.solutions.drawing_utils
        self.mp_drawing_styles = mp.solutions.drawing_styles
        
        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=max_hands,
            model_complexity=model_complexity,
            min_detection_confidence=detection_confidence,
            min_tracking_confidence=tracking_confidence,
        )
        
        self._last_landmarks: Optional[list[HandLandmarks]] = None
    
    def process(self, frame: np.ndarray) -> list[HandLandmarks]:
        """
        处理一帧图像，返回手部关键点列表
        
        Args:
            frame: BGR 格式的图像帧
            
        Returns:
            手部关键点列表
        """
        # 转换为 RGB (MediaPipe 需要)
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # 处理图像
        results = self.hands.process(rgb_frame)
        
        hands_data: list[HandLandmarks] = []
        
        if results.multi_hand_landmarks:
            for hand_landmarks, handedness in zip(
                results.multi_hand_landmarks,
                results.multi_handedness
            ):
                # 提取关键点
                landmarks = [
                    Point3D(lm.x, lm.y, lm.z)
                    for lm in hand_landmarks.landmark
                ]
                
                # 获取手的类型和置信度
                hand_type = handedness.classification[0].label
                score = handedness.classification[0].score
                
                hands_data.append(HandLandmarks(
                    landmarks=landmarks,
                    handedness=hand_type,
                    score=score,
                ))
        
        self._last_landmarks = hands_data
        return hands_data
    
    def draw_landmarks(
        self,
        frame: np.ndarray,
        hands_data: list[HandLandmarks],
        draw_connections: bool = True,
    ) -> np.ndarray:
        """
        在图像上绘制手部骨架
        
        Args:
            frame: 图像帧
            hands_data: 手部关键点数据
            draw_connections: 是否绘制连接线
            
        Returns:
            绘制后的图像
        """
        annotated_frame = frame.copy()
        h, w = frame.shape[:2]
        
        for hand in hands_data:
            # 绘制关键点
            for i, point in enumerate(hand.landmarks):
                cx, cy = point.to_pixel(w, h)
                
                # 手指尖端用较大的圆
                if i in [4, 8, 12, 16, 20]:
                    cv2.circle(annotated_frame, (cx, cy), 8, (0, 255, 0), -1)
                    cv2.circle(annotated_frame, (cx, cy), 10, (255, 255, 255), 2)
                else:
                    cv2.circle(annotated_frame, (cx, cy), 5, (0, 200, 0), -1)
            
            if draw_connections:
                # 绘制骨架连接
                connections = [
                    # 拇指
                    (0, 1), (1, 2), (2, 3), (3, 4),
                    # 食指
                    (0, 5), (5, 6), (6, 7), (7, 8),
                    # 中指
                    (0, 9), (9, 10), (10, 11), (11, 12),
                    # 无名指
                    (0, 13), (13, 14), (14, 15), (15, 16),
                    # 小指
                    (0, 17), (17, 18), (18, 19), (19, 20),
                    # 手掌
                    (5, 9), (9, 13), (13, 17),
                ]
                
                for start, end in connections:
                    p1 = hand.landmarks[start].to_pixel(w, h)
                    p2 = hand.landmarks[end].to_pixel(w, h)
                    cv2.line(annotated_frame, p1, p2, (0, 255, 0), 2)
        
        return annotated_frame
    
    def release(self):
        """释放资源"""
        self.hands.close()
