import cv2
from risk_engine import RiskEngine,ppe_classes,person_classes
from torch.ao.quantization import per_channel_dynamic_qconfig
from ultralytics import YOLO

model_path = r"C:\Users\Azer\Desktop\Security\runs\detect\train\weights\best.pt"
video_path = r"C:\Users\Azer\Desktop\Security\19832492-hd_1920_1080_25fps.mp4"

color_person_ok = (0,200,0)
color_ppe = (255,200,0)
color_violation = (0,0,255)

def draw_box(frame,xyxy,color,label,thickness=2):
    x1,y1,x2,y2 = [int(v) for v in xyxy]
    cv2.rectangle(frame,(x1,y1),(x2,y2),color,thickness)
    cv2.putText(frame,label,(x1,max(0,y1-8)),
                cv2.FONT_HERSHEY_SIMPLEX,0.5,color,2)

def main():
    model = YOLO(model_path)
    engine = RiskEngine(reqiured_ppe=["helmet","vest"])
    cap = cv2.VideoCapture(video_path)

    if not cap.isOpened():
        print("Error opening video file")
        return

    frame_id = 0
    paused = False

    while cap.isOpened():
        if not paused:
            ret,frame = cap.read()
            if not ret:
                break

            results = model.predict(source=frame,conf=0.25,verbose=False)
            result = results[0]
            events = engine.process_frame(result,frame_id=frame_id)
            violated_persons =  {tuple(e.person_bbox) for e in events}

            for box in result.boxes:
                cls_id = int(box.cls[0])
                conf = float(box.conf[0])
                cls_name = result.names[cls_id]
                xyxy = tuple(box.xyxy[0].tolist())

                if cls_name == person_classes:
                    is_violation = xyxy in violated_persons
                    color = color_violation if is_violation else color_person_ok
                    label = f"Person: {conf:.2f}" + (" - VIOLATION" if is_violation else " - OK")
                    draw_box(frame, xyxy, color, label)

                elif cls_name in ppe_classes:
                    draw_box(frame, xyxy, color_ppe, f"{cls_name} {conf:.2f}")

                # Счётчик наверху кадра
            cv2.putText(frame, f"Frame {frame_id} | Violations this frame: {len(events)}",
                        (10, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

            frame_id += 1

        cv2.imshow("HSE PPE Detection - press q to quit, space to pause", frame)

        key = cv2.waitKey(1) & 0xFF
        if key == ord("q"):
            break
        elif key == ord(" "):
            paused = not paused

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()

