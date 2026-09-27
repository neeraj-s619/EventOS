"""
Multi-Object Centroid Tracker with Persistent IDs and Motion Vector Tracking.
Maintains persistent track IDs and movement histories across CCTV video frames.
"""

from typing import Dict, List, Tuple, Optional
import math


class CentroidTracker:
    """
    Euclidean distance object tracker with history trajectories and disappearance timeout.
    """

    def __init__(self, max_disappeared: int = 15, max_distance: int = 70):
        self.next_id = 101
        self.objects: Dict[int, Tuple[int, int]] = {}         # id -> (cx, cy)
        self.boxes: Dict[int, Tuple[int, int, int, int]] = {}   # id -> (x, y, w, h)
        self.disappeared: Dict[int, int] = {}
        self.history: Dict[int, List[Tuple[int, int]]] = {}   # id -> recent points
        self.max_disappeared = max_disappeared
        self.max_distance = max_distance

    def update(self, rects: List[Tuple[int, int, int, int]]) -> Dict[int, Tuple[int, int, int, int]]:
        """
        Updates tracked objects with new frame detections.
        rects: list of (x, y, w, h)
        Returns: dict of object_id -> (x, y, w, h)
        """
        if len(rects) == 0:
            for oid in list(self.disappeared.keys()):
                self.disappeared[oid] += 1
                if self.disappeared[oid] > self.max_disappeared:
                    self._deregister(oid)
            return self.boxes

        input_centroids = [
            (int(x + w / 2), int(y + h / 2), (x, y, w, h))
            for (x, y, w, h) in rects
        ]

        if len(self.objects) == 0:
            for cx, cy, box in input_centroids:
                self._register(cx, cy, box)
            return self.boxes

        object_ids = list(self.objects.keys())
        object_centroids = [self.objects[oid] for oid in object_ids]

        assigned_objects = set()
        assigned_inputs = set()

        for i, (cx, cy, box) in enumerate(input_centroids):
            best_dist = float("inf")
            best_oid = None
            for j, oid in enumerate(object_ids):
                if oid in assigned_objects:
                    continue
                ox, oy = object_centroids[j]
                dist = (cx - ox) ** 2 + (cy - oy) ** 2
                if dist < (self.max_distance ** 2) and dist < best_dist:
                    best_dist = dist
                    best_oid = oid

            if best_oid is not None:
                self.objects[best_oid] = (cx, cy)
                self.boxes[best_oid] = box
                self.disappeared[best_oid] = 0
                assigned_objects.add(best_oid)
                assigned_inputs.add(i)

                if best_oid not in self.history:
                    self.history[best_oid] = []
                self.history[best_oid].append((cx, cy))
                if len(self.history[best_oid]) > 10:
                    self.history[best_oid].pop(0)

        # Handle unassigned existing objects
        for oid in object_ids:
            if oid not in assigned_objects:
                self.disappeared[oid] = self.disappeared.get(oid, 0) + 1
                if self.disappeared[oid] > self.max_disappeared:
                    self._deregister(oid)

        # Handle new detections
        for i, (cx, cy, box) in enumerate(input_centroids):
            if i not in assigned_inputs:
                self._register(cx, cy, box)

        return self.boxes

    def _register(self, cx: int, cy: int, box: Tuple[int, int, int, int]):
        self.objects[self.next_id] = (cx, cy)
        self.boxes[self.next_id] = box
        self.disappeared[self.next_id] = 0
        self.history[self.next_id] = [(cx, cy)]
        self.next_id += 1

    def _deregister(self, oid: int):
        self.objects.pop(oid, None)
        self.boxes.pop(oid, None)
        self.disappeared.pop(oid, None)
        self.history.pop(oid, None)
