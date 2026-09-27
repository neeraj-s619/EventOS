"""
Virtual Counting Line (ROI) Counter for CCTV Line Crossing.
Tracks IN and OUT flow transitions when centroid points cross a virtual horizontal or vertical line.
"""

from typing import Dict, Tuple, Set


class VirtualLineCounter:
    """
    Evaluates centroid trajectories against a virtual counting threshold line.
    Calculates IN, OUT, and NET FLOW = IN - OUT.
    """

    def __init__(self, line_y: int = 180, initial_in: int = 24, initial_out: int = 14):
        self.line_y = line_y
        self.in_count = initial_in
        self.out_count = initial_out
        self.counted_ids: Dict[int, str] = {}  # id -> "in" or "out"

    @property
    def net_flow(self) -> int:
        return self.in_count - self.out_count

    def process_tracks(
        self,
        current_objects: Dict[int, Tuple[int, int]],
        previous_objects: Dict[int, Tuple[int, int]]
    ) -> Dict[str, int]:
        """
        Detects crossing events between previous and current object positions.
        """
        for oid, (cx, cy) in current_objects.items():
            if oid in self.counted_ids:
                continue

            prev_pt = previous_objects.get(oid)
            if prev_pt is None:
                continue

            prev_cx, prev_cy = prev_pt

            # Downward crossing (IN)
            if prev_cy < self.line_y <= cy:
                self.in_count += 1
                self.counted_ids[oid] = "in"
            # Upward crossing (OUT)
            elif prev_cy > self.line_y >= cy:
                self.out_count += 1
                self.counted_ids[oid] = "out"

        return {
            "entered": self.in_count,
            "exited": self.out_count,
            "net": self.net_flow
        }
