from ultralytics import YOLO
import torch

def main():
    print("Cuda available:", torch.cuda.is_available())
    if torch.cuda.is_available():
        print("GPU", torch.cuda.get_device_name(0))

    model = YOLO("yolov8n.pt")
    data_yaml = r"C:\Users\Azer\Desktop\Security\Security\data.yaml"

    results = model.train(data=data_yaml,
                          epochs=100,
                          imgsz=640,
                          batch=16,
                          device=0,
                          workers=0,
                          patience=30,
                          project="ppe-runs",
                          name="train_v2")

if __name__ == "__main__":
    main()