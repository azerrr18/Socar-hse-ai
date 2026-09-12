from ultralytics import YOLO

def main():
    model = YOLO(r"C:\Users\Azer\Desktop\Security\yolov8n.pt")
    data_yaml = r"C:\Users\Azer\Desktop\Security\Security\data.yaml"

    print("===Execute Validation===")
    metrics = model.val(data=data_yaml,workers=0)

    print("mAp50:", metrics.box.map50)
    print("mAp50-95:", metrics.box.map)
    print("mAp50-95 (per class):", metrics.box.maps)
    print("Classes:", metrics.names)

    test_image = r"C:\Users\Azer\Desktop\Security\test_image.jpg"

    results = model.predict(source=test_image,
                            save=True,
                            conf=0.25,
                            name="predict_check")
    print("Model is ready")

    for r in results:
        for box in r.boxes:
            cls_id = int(box.cls)
            conf = float(box.conf[0])
            print(f"Class ID: {cls_id}, Confidence: {conf}")

if __name__ == "__main__":
    main()