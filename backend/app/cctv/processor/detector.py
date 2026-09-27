"""
Pedestrian and Object Detector for EVENTOS CCTV Pipeline.
Uses OpenCV HOG + SVM with NMS and high-contrast silhouette segmentation fallback.
Designed to detect people in real CCTV replay footage reliably.
"""

import cv2
import numpy as np
from typing import List, Tuple, Dict, Any, Optional
import logging

logger = logging.getLogger("eventos.cctv.detector")


class PedestrianDetector:
    """
    Pedestrian detector supporting OpenCV HOG descriptor and silhouette fallback.
    Outputs standard bounding boxes (x, y, w, h) and confidence scores.
    """

    def __init__(self, confidence_threshold: float = 0.3, nms_threshold: float = 0.4):
        self.confidence_threshold = confidence_threshold
        self.nms_threshold = nms_threshold
        self.hog = None
        self._init_hog()

    def _init_hog(self):
        try:
            self.hog = cv2.HOGDescriptor()
            self.hog.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())
        except Exception as e:
            logger.warning(f"Could not initialize OpenCV HOG: {e}")
            self.hog = None

    def detect(self, frame: np.ndarray) -> List[Tuple[int, int, int, int]]:
        """
        Detects pedestrians in an OpenCV BGR frame.
        Returns list of (x, y, w, h) bounding boxes.
        """
        if frame is None or frame.size == 0:
            return []

        h, w = frame.shape[:2]
        boxes: List[Tuple[int, int, int, int]] = []

        if self.hog is not None:
            try:
                rects, weights = self.hog.detectMultiScale(
                    frame,
                    winStride=(8, 8),
                    padding=(4, 4),
                    scale=1.05
                )
                if len(rects) > 0:
                    rects_list = [[x, y, x + wb, y + hb] for (x, y, wb, hb) in rects]
                    indices = cv2.dnn.NMSBoxes(
                        bboxes=[[x, y, wb - x, hb - y] for x, y, wb, hb in rects_list],
                        scores=[float(w_score) if isinstance(w_score, (float, np.floating)) else 0.85 for w_score in weights],
                        score_threshold=self.confidence_threshold,
                        nms_threshold=self.nms_threshold
                    )
                    if len(indices) > 0:
                        for idx in indices.flatten():
                            x1, y1, x2, y2 = rects_list[idx]
                            boxes.append((int(x1), int(y1), int(x2 - x1), int(y2 - y1)))
                    else:
                        for (x, y, wb, hb) in rects:
                            boxes.append((int(x), int(y), int(wb), int(hb)))
            except Exception as e:
                logger.debug(f"HOG detect failed, using fallback: {e}")

        # If HOG yields low detections on noisy CCTV video, augment with silhouette segmentation
        if len(boxes) < 8:
            fallback_boxes = self._detect_silhouette(frame)
            if len(fallback_boxes) > len(boxes):
                boxes = fallback_boxes

        return boxes

    def _detect_silhouette(self, frame: np.ndarray) -> List[Tuple[int, int, int, int]]:
        """
        Contrast & silhouette based detection for low-light or overhead crowd CCTV feeds.
        """
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        mask = (gray < 195).astype(np.uint8) * 255
        # Exclude border edges
        mask[:, :50] = 0
        mask[:, -50:] = 0

        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 5))
        cleaned = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

        contours, _ = cv2.findContours(cleaned, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        boxes = []
        for c in contours:
            area = cv2.contourArea(c)
            if 140 < area < 4500:
                x, y, w, h = cv2.boundingRect(c)
                if h > 20 and (h / max(1, w)) > 1.05:
                    boxes.append((x, y, w, h))
        return boxes
