from dataclasses import dataclass,field

from typing import List, Optional,Dict
import time

ppe_classes = {"helmet","gloves","vest","boots","googles"}
person_classes = {"person"}

@dataclass
class RiskEvent:
    frame_id :int
    person_bbox : tuple
    missing_ppe : List[str]
    person_conf : float
    timestamp = field(default_factory=time.time)

    def to_dict(self):
        return {"fram_id":self.frame_id,
                "person_bbox":self.person_bbox,
                "missing_ppe":self.missing_ppe,
                "person_conf":round(self.person_conf,3),
                "timestamp":self.timestamp}

    def _iou_or_overlap(box_a,box_b):
        ax1,ay1,ax2,ay2 = box_a
        bx1,by1,bx2,by2 = box_b

        inter_x1 = max(ax1,bx1)
        inter_y1 = max(ay1,by1)
        inter_x2 = min(ax2,bx2)
        inter_y2 = min(ay2,by2)

        inter_w = max(0)

