# SOCAR HSE AI

Computer vision prototype for workplace safety (HSE) monitoring, built during a hackathon.

## Demo





https://github.com/user-attachments/assets/a87fa794-8f91-4ab7-ad23-6b695dc22dad





## Overview

The model detects safety violations on video/images, such as a worker without a helmet or gloves. Detected violations are highlighted in **red**, so unsafe situations are easy to spot at a glance.

## Model

- Object detection with YOLO (`yolov26s.pt`)
- Violation classes: missing helmet, missing gloves
- Red bounding box = violation

## Usage

\`\`\`
pip install ultralytics
python [detection.py]
\`\`\`

## Status

Hackathon prototype. The project was not fully completed, but the core detection works as shown in the demo video.

## Author

Azer — [GitHub](https://github.com/azerrr18)
