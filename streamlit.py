"""First page:Welcome screen for app
Import the video 
This page allow import the video and start process """

import streamlit as st
import os
import sys
import time
import cv2
import subprocess
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from integration import init_db,add_video,list_videos,delete_video,update_video_status,save_event


st.set_page_config(page_title = "HSE Dashboard",layout = "wide",page_icon = "🦺")
st.title("🦺 HSE Dashboard")

conn = init_db()

videos_dir = os.path.join(os.path.dirname(__file__),"videos")

os.makedirs(videos_dir,exist_ok=True)
model_path = r"C:\Users\Azer\Desktop\Security\runs\detect\train\weights\best.pt"

#Adding new video------
st.subheader("1. Upload New Video")

uploaded_file = st.file_uploader("Choose a video file",type=["mp4","avi","mkv"])

if uploaded_file is not None:
    if st.button("➕ Add video to queue",type="primary"):
        save_path = os.path.join(videos_dir,uploaded_file.name)
        with open(save_path,"wb") as f:
            f.write(uploaded_file.getbuffer())

        cap = cv2.VideoCapture(save_path)
        fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
        frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT)
        duration_sec = frame_count / fps if fps else None
        cap.release()

        video_id = add_video(conn,uploaded_file.name,save_path,duration_sec,fps)
        st.success("Video added successfully!")

        update_video_status(conn,video_id,"processing")
        progress_bar = st.progress(0,text="Initializing YOLO model...")

        try:
            from ultralytics import YOLO
            from risk_engine import RiskEngine
            model = YOLO(model_path)
            engine = RiskEngine(reqiured_ppe=["helmet","vest"],min_consecutive_frames=5)

            total_frames = int(frame_count) if frame_count else 1
            frame_id = 0

            for result in model.predict(source=save_path, stream=True, conf=0.25, verbose=False):
                events = engine.process_frame(result, frame_id=frame_id)
                for e in events:
                    save_event(conn, video_id, e)

                frame_id += 1
                pct = min(frame_id / total_frames, 1.0)
                progress_bar.progress(pct, text=f"Processing frame {frame_id}/{total_frames}…")

            update_video_status(conn, video_id, "done")
            progress_bar.progress(1.0, text="Processing complete!")
            st.success(f"Finished! Detected violations saved to database.")


        
        except Exception as ex:
            st.error(f"Error during processing: {ex}")
            update_video_status(conn, video_id, "error")