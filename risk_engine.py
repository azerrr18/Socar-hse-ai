# ---------------------------------------------------------------------------
#Capturing the video
# ---------------------------------------------------------------------------
from dataclasses import dataclass,field

from typing import List, Optional,Dict
import time,math

ppe_classes = {"helmet","gloves","vest","boots","goggles"}
person_classes =  "Person"

@dataclass
class RiskEvent:
    frame_id :int
    person_bbox : tuple
    missing_ppe : List[str]
    person_conf : float
    timestamp : float = field(default_factory=time.time)

    def to_dict(self):
        return {"frame_id":self.frame_id,
                "person_bbox":self.person_bbox,
                "missing_ppe":self.missing_ppe,
                "person_conf":round(self.person_conf,3),
                "timestamp":self.timestamp}


def _iou_or_overlap(box_a, box_b) -> float:
    ax1, ay1, ax2, ay2 = box_a
    bx1, by1, bx2, by2 = box_b

    inter_x1 = max(ax1, bx1)
    inter_y1 = max(ay1, by1)
    inter_x2 = min(ax2, bx2)
    inter_y2 = min(ay2, by2)

    inter_w = max(0.0, inter_x2 - inter_x1)
    inter_h = max(0.0, inter_y2 - inter_y1)
    inter_area = inter_w * inter_h
    b_area = max(1e-6, (bx2 - bx1) * (by2 - by1))
    overlap = inter_area / b_area
    return overlap

def expand_box(box,frame_h,frame_w,margin_ratio=0.15):
    x1,y1,x2,y2 = box
    w = x2-x1
    h = y2-y1
    mx = w*margin_ratio
    my = h*margin_ratio
    return (max(0,x1-mx),max(0,y1-my),min(frame_w,x2+mx),min(frame_h,y2+my))

def center_box(box):
    x1,y1,x2,y2 = box
    return (x1+x2)/2,(y1+y2)/2

def center_dist(box_a,box_b):
    ax,ay = center_box(box_a)
    bx,by = center_box(box_b)
    return math.sqrt((ax-bx)**2+(ay-by)**2)

class PersonTrecker:
    def __init__(self,max_distance: float = 80.0,max_frames_missing: int = 15):
        self.max_distance = max_distance
        self.max_frames_missing = max_frames_missing
        self.next_id = 0
        self.tracks = {}


    def update_self(self,person_boxes,frame_id):
        assigned = {}
        used_id_tracks = set()

        for box in person_boxes:
            best_id = None
            best_dist = self.max_distance
            for track_id,info in  self.tracks.items():
                if track_id in used_id_tracks:
                    continue
                dist = center_dist(box,info["box"])

                if dist<best_dist:
                    best_dist = dist
                    best_id = track_id

            if best_id is None:
                best_id = self.next_id
                self.next_id += 1

                used_id_tracks.add(best_id)
                self.tracks[best_id] = {"box":box,"last_seen":frame_id}
                assigned[best_id] = box

        stale = [tid for tid,info in self.tracks.items()
                 if frame_id - info["last_seen"]>self.max_frames_missing]
        for tid in stale:
            del self.tracks[tid]

        return assigned

class ViolationTrecker:
    def __init__(self,min_consecutive_frames : int=5):
        self.min_consecutive_frames = min_consecutive_frames
        self.streaks = {}
        self.already_confirmed = set()



    def update_violation(self,track_id,missing_ppe):
        if missing_ppe:
            self.streaks[track_id] = self.streaks.get(track_id,0) + 1
        else:
            self.streaks[track_id] = 0
            self.already_confirmed.discard(track_id)

        streak = self.streaks[track_id]
        if streak>self.min_consecutive_frames and track_id not in self.already_confirmed:
            self.already_confirmed.add(track_id)
            return True,streak
        return False,streak

class RiskEngine:
    def __init__(self,
                 reqiured_ppe:Optional[List[str]]=None,
                 overlap_treshold:float=0.3,
                 person_conf_treshold:float=0.5,
                 ppe_conf_treshold:float=0.4,
                 min_consecutive_frames:int=5,
                 max_track_distance:float=80.0):
        self.required_ppe = reqiured_ppe or ["helmet","vest"]
        self.overlap_treshold = overlap_treshold
        self.person_conf_treshold = person_conf_treshold
        self.ppe_conf_treshold = ppe_conf_treshold
        self.trackers = PersonTrecker(max_distance=max_track_distance)
        self.violations = ViolationTrecker(min_consecutive_frames=min_consecutive_frames)


    def process_frame(self, result, frame_id:int=0) -> List[RiskEvent]:
        events : List[RiskEvent] = []
        names = result.names
        frame_h,frame_w = result.orig_shape
        persons = []
        ppe_boxes: Dict[str, List[tuple]] = {cls: [] for cls in ppe_classes}

        for box in result.boxes:
            cls_id = int(box.cls[0])
            conf = float(box.conf[0])
            cls_name = names[cls_id]
            xyxy = tuple(box.xyxy[0].tolist())

            if cls_name == person_classes and conf >= self.person_conf_treshold:
                persons.append((xyxy,conf))
            elif cls_name in ppe_classes and conf >= self.ppe_conf_treshold:
                ppe_boxes[cls_name].append(xyxy)

            person_boxes_only = [p[0] for p in persons]
            assigned_tracks = self.trackers.update_self(person_boxes_only,frame_id)

            box_to_track_id = {box:tid for tid,box in assigned_tracks.items()}

        for person_box,person_conf in persons:
            search_area = expand_box(person_box,frame_h,frame_w)
            missing = []
            for ppe_class in self.required_ppe:
                found = False
                for candidate_box in ppe_boxes.get(ppe_class,[]):
                    if _iou_or_overlap(search_area,candidate_box) >= self.overlap_treshold:
                        found = True
                        break
                if not found:
                    missing.append(ppe_class)
            track_id = box_to_track_id.get(person_box)


            if missing:
                events.append(RiskEvent(
                    frame_id=frame_id,
                    person_bbox=person_box,
                    missing_ppe=missing,
                    person_conf=person_conf
                ))
        return events
# ---------------------------------------------------------------------------
#Loading the model
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    from ultralytics import YOLO
    model = YOLO(r"C:\Users\Azer\Desktop\Security\runs\detect\train\weights\best.pt")
    test_video = r"C:\Users\Azer\Desktop\Security\19832492-hd_1920_1080_25fps.mp4"
    engine = RiskEngine(reqiured_ppe=["helmet","vest"])
    frame_id = 0
    all_events = []

    for result in model.predict(source=test_video,stream=True,conf=0.25,verbose=False):
        events = engine.process_frame(result,frame_id=frame_id)
        for e in events:
            print(f"[Frame {frame_id}] violation: lack {e.missing_ppe}"
                  f"(person conf={e.person_conf})")
        all_events.extend(events)
        frame_id += 1

    print(f"\nTotal frames: {frame_id}")
    print(f"Total violations: {len(all_events)}")

