""""Analytics about violations
Special dashboards
------------------------------ """


import streamlit as st
import os
import sys
from collections import Counter
import plotly.express as px
from datetime import datetime,timedelta,time
import pandas as pd

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from integration import list_videos,init_db,get_all_events


st.set_page_config(page_title="ppe violation Analytics",layout="wide",page_icon="📊")

st.title("ppe violation Analytics 📊")

conn = init_db()

col_f1, col_f2 = st.columns(2)
start_date = col_f1.date_input("From date", value=date.today() - timedelta(days=30))
end_date = col_f2.date_input("To date", value=date.today())

events = get_all_events(conn, start_date=start_date, end_date=end_date)
videos = list_videos(conn)

if not events:
    st.info("No violation data for the selected period.")
    st.stop()

df = pd.DataFrame(events)
df["created_dt"] = pd.to_datetime(df["created_at"], unit="s")
df["date"] = df["created_dt"].dt.date

# --- Верхние метрики ---
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Violations", len(df))
col2.metric("Processed Videos", df["video_id"].nunique())
col3.metric("Unique People", df["track_id"].nunique() if "track_id" in df else "—")
avg_conf = df["person_conf"].mean()
col4.metric("Average Confidence", f"{avg_conf:.2f}")

st.divider()

col_a, col_b = st.columns(2)

# --- Нарушения по типу СИЗ ---
with col_a:
    st.subheader("PPE Violation Types")
    ppe_counter = Counter()
    for missing_list in df["missing_ppe"]:
        for ppe in missing_list:
            ppe_counter[ppe] += 1

    ppe_df = pd.DataFrame(ppe_counter.items(), columns=["PPE Type", "Count"]).sort_values(
        "Count", ascending=False
    )
    fig_ppe = px.bar(ppe_df, x="PPE Type", y="Count", color="PPE Type")
    fig_ppe.update_layout(showlegend=False)
    st.plotly_chart(fig_ppe, use_container_width=True)

# --- Топ видео по числу нарушений ---
with col_b:
    st.subheader("Top Videos by Number of Violations")
    video_counts = df["video_filename"].value_counts().reset_index()
    video_counts.columns = ["Video", "Violations"]
    fig_video = px.bar(video_counts, x="Video", y="Violations", color="Video")
    fig_video.update_layout(showlegend=False)
    st.plotly_chart(fig_video, use_container_width=True)

st.divider()

# --- Тренд по времени ---
st.subheader("Trend of Violations Over Time")
daily_counts = df.groupby("date").size().reset_index(name="Violations")
fig_trend = px.line(daily_counts, x="date", y="Violations", markers=True)
fig_trend.update_layout(xaxis_title="Date", yaxis_title="Number of Violations")
st.plotly_chart(fig_trend, use_container_width=True)

st.divider()

# --- Таблица всех событий ---
st.subheader("All Events")
df_display = df.copy()
df_display["missing_ppe"] = df_display["missing_ppe"].apply(lambda x: ", ".join(x))
df_display = df_display[[
    "created_dt", "video_filename", "timestamp_sec", "missing_ppe", "person_conf", "track_id", "acknowledged"
]].rename(columns={
    "created_dt": "Date/Time",
    "video_filename": "Video",
    "timestamp_sec": "Time in Video (sec)",
    "missing_ppe": "Missing PPE",
    "person_conf": "Confidence",
    "track_id": "Person ID",
    "acknowledged": "Acknowledged",
})
st.dataframe(df_display, use_container_width=True, hide_index=True)
 