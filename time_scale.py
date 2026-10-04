"""  Page for time scaling
Shows the clickable time scale
"""

import streamlit as st
import os
import sys
import plotly.graph_objects as go
import pandas as pd

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from integration import init_db,list_videos,get_events_for_video

st.set_page_config(page_title="PPE violation timeline",layout="wide",page_icon="⏱️")

st.title("⏱️ PPE violation timeline")

conn = init_db()

videos = list_videos(conn) 

if not videos:
    st.info("No videos in the database. Import videos in the 'Upload' tab first.")
else:
    # Video selector
    video_options = {v["id"]: f"{v['filename']} [{v['status']}]" for v in videos}
    selected_id = st.selectbox("Select video", list(video_options.keys()), 
                              format_func=lambda x: video_options[x])
    selected_video = next(v for v in videos if v['id'] == selected_id)
    video_filename = selected_video['filename']
    video_duration = selected_video['duration_sec'] or 20.0

    # Get events for selected video
    # pyrefly: ignore [name-defined]
    events = get_events_for_video(conn, selected_id)
    
    if not events:
        st.success(f"'{video_filename}' has no violation events.")
    else:
        # Create DataFrame for timeline
        df = pd.DataFrame(events)
        df["missing_ppe"] = df["missing_ppe"].apply(lambda x: ", ".join(x) if isinstance(x, list) else str(x))

        # Format timestamp
        df['time_str'] = pd.to_datetime(df['timestamp'], unit='s').dt.strftime('%H:%M:%S')

        # Plotly timeline chart
        fig = go.Figure()

        # Add traces for each PPE violation type
        ppe_types = df['missing_ppe'].unique()
        
        # pyrefly: ignore [name-defined]
        colors = {"helmet": "#ff6347", "vest": "#ffa500", "gloves": "#87ceeb"}
        
        for ppe_type in ppe_types:
            ppe_df = df[df['missing_ppe'] == ppe_type]
            fig.add_trace(go.Scatter(
                x=ppe_df['timestamp'],
                y=[ppe_type]*len(ppe_df),
                mode='markers',
                name=ppe_type.capitalize(),
                marker=dict(
                    size=12,
                    color=colors.get(ppe_type, '#00008b'),
                    line=dict(width=2, color='DarkSlateGrey')
                ),
                hovertemplate="<b>Violation:</b> PPE欠缺<br>" +
                             "<b>PPE Type:</b> " + ppe_type + "<br>" +
                             "<b>Time:</b> %{x:.1f}s<br>" +
                             "<b>Frame:</b> %{text}<extra></extra>",
                text=ppe_df['frame_id']
            ))

        # Layout
        fig.update_layout(
            xaxis_title="Time (seconds)",
            yaxis_title="PPE Violation Type",
            yaxis=dict(autorange="reversed"),
            hovermode='closest',
            template='plotly_white',
            height=400,
            margin=dict(l=20, r=20, t=40, b=20),
            legend=dict(orientation="h", y=1.02, x=1)
        )

        st.subheader(f"Timeline for: {video_filename}")
        st.plotly_chart(fig, use_container_width=True)

        # Data table
        st.markdown("#### Violation Details")
        
        # Select columns to display
        columns_to_show = ['time_str', 'missing_ppe', 'person_conf', 'frame_id', 'track_id']
        display_df = df[columns_to_show].rename(columns={
            'time_str': 'Time',
            'missing_ppe': 'Missing PPE',
            'person_conf': 'Person Conf.',
            'frame_id': 'Frame',
            'track_id': 'Track ID',
        })
        
        st.dataframe(display_df, use_container_width=True, hide_index=True)

        st.caption(f"Total violations: {len(df)} | Video duration: {video_duration:.1f}s")