import sqlite3
import json 
import os
import time
from datetime import datetime,time


#initialize the database for our project
DB_PATH = os.path.join(os.path.dirname(__file__),"events.db")


def init_db(db_path=DB_PATH):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    conn.execute("""CREATE TABLE IF NOT EXISTS events(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    video_id INTEGER NOT NULL,
    frame_id INTEGER,
    missing_ppe TEXT,
    person_conf REAL,
    timestamp REAL,
    track_id INTEGER,
    created_at REAL NOT NULL,
    acknowledged INTEGER DEFAULT 0,
    FOREIGN KEY(video_id) REFERENCES videos(id) ON DELETE CASCADE)""")

    #CREATING SECOND TABLE
    conn.execute("""CREATE TABLE IF NOT EXISTS videos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    video_id INTEGER NOT NULL,
    filename TEXT NOT NULL,
    filepath TEXT NOT NULL,
    uploaded_at REAL NOT NULL,
    duration_sec REAL NOT NULL,
    fps REAL,
    status TEXT DEFAULT 'pending' --pending|processing|done|error) """)
    
    conn.commit()
    return conn



def save_event(conn,event):
    #insert new event into database
    conn.execute("INSERT INTO events(frame_id,missing_ppe,person_conf,timestamp) "
    "VALUES (?,?,?,?)",(
        event.frame_id,
        json.dumps(event.missing_ppe),
        event.person_conf,
        event.timestamp
    ),
    )
    conn.commit()

def get_video_stats(conn):
    #summary statistics for dashboard
    total_videos = conn.execute("SELECT COUNT(DISTINCT video_id) FROM videos").fetchone()[0]
    total_events = conn.execute("SELECT COUNT(*) FROM events").fetchone()[0]
    active_today = conn.execute("SELECT COUNT(*) FROM events WHERE date(timestamp)=date('now')").fetchone()[0]
    unique_persons = conn.execute("SELECT COUNT(DISTINCT person_id) FROM events").fetchone()[0]

    return {"total_videos":total_videos,
            "total_events":total_events,
            "active_today":active_today,
            "unique_persons":unique_persons}

""" Adding and deleting the video: """  
def add_video(conn,filename:str,filepath:str,duration:float=None,fps:float=None) -> int:
    cur = conn.execute("INSERT INTO videos (filename,filepath,uploaded_at,duration,fps)  VALUES (?,?,?,?,?)",
    (filepath,filename,time.time(),duration,fps),)
    conn.commit()
    return cur.lastrowid

def delete_video(conn,video_id:int):
    #Deletes the video and all data about the video
    row = conn.execute("SELECT filepath FROM videos WHERE id=?",(video_id,)).fetchone()
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("DELETE FROM videos WHERE id=?",(video_id,))
    conn.execute("DELETE FROM events WHERE video_id=?",(video_id,))
    conn.commit()
    if row and row['filepath'] and os.path.exists(row['filepath']):
        try:
            os.remove(row['filepath'])
        except OSError:
            pass
            
    
    
def list_videos(conn):
    rows = conn.execute("SELECT * FROM videos ORDER BY uploaded_at DESC").fetchall()
    return [dict(row) for row in rows]

def update_video_status(conn,video_id : int, status:str):
    """
    Updates the status of a video
    """
    conn.execute("UPDATE videos SET status=? WHERE id=?",(status,video_id))
    conn.commit()
  
#-------------------------------------------
#Violations from events
#---------------------------------------

def save_event(conn,video_id:int,event,timestamp:float=None) :
    conn.execute("""
    INSERT INTO events(video_id,frame_id,missing_ppe,person_conf,timestamp,track_id,created_at)
    VALUES (?,?,?,?,?,?,?)
    """,(
        video_id,
        event.frame_id,
        json.dumps(event.missing_ppe),
        event.person_conf,
        event.timestamp,
        getattr(event,"track_id",None)
    ))
    conn.commit()

def get_events_for_video(conn,video_id:int):
    rows = conn.execute("SELECT * FROM events WHERE video_id=? ORDER BY timestamp ASC",(video_id,)).fetchall()
    events = []
    for r in rows:
        d = dict(r)
        d["missing_ppe"]= json.loads(d["missing_ppe"])
        events.append(d)
    return events
    

def get_all_events(conn,start_date=None,end_date=None):
    query = """SELECT events.*, videos.filename as video_filename
    FROM events 
    JOIN videos on events.video_id = videos.video_id"""


#now we define some test values to check it
if __name__ == "__main__":
    from ultralytics import YOLO
    from risk_engine import RiskEngine

    conn = init_db()
    model = YOLO(r"C:\Users\Azer\Desktop\Security\runs\detect\ppe-runs\train_v2\weights\best.pt")
    engine = RiskEngine(reqiured_ppe=["helmet","vest"],min_consecutive_frames=5)
    test_video_path = r"C:\Users\Azer\Desktop\Security\19832492-hd_1920_1080_25fps.mp4"
    frame_id = 0


    for result in model.predict(source=test_video_path,stream=True, verbose=False):
        events = engine.process_frame(result,frame_id=frame_id)

        for e in events:
            save_event(conn,e)
            print(f"[Frame {frame_id}] Saved violation: {e.missing_ppe}")
        frame_id +=1
        
    conn.close()
    print("Processing completed. Data saved to events.db")


