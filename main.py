import os
import random
import json
import time
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload
from instagrapi import Client

# --- VIDEO EDITING ---
from moviepy.editor import VideoFileClip, vfx

# --- 1. CONFIGURATION ---
CLIENT_ID = os.environ["CLIENT_ID"]
CLIENT_SECRET = os.environ["CLIENT_SECRET"]
REFRESH_TOKEN = os.environ["REFRESH_TOKEN"]

# Folders
SATISFY_FOLDER_ID = os.environ["DRIVE_SATISFY_ID"]
DONE_FOLDER_ID = os.environ["DRIVE_DONE_ID"]  # <-- Ye zaroori hai move karne ke liye

# Instagram
INSTA_USER = os.environ["INSTA_USERNAME"]
INSTA_PASS = os.environ["INSTA_PASSWORD"]
INSTA_SESSION = os.environ.get("INSTA_SETTINGS")

# --- 2. SETUP SERVICES ---
def get_google_services():
    creds = Credentials(
        None, 
        refresh_token=REFRESH_TOKEN, 
        token_uri="https://oauth2.googleapis.com/token", 
        client_id=CLIENT_ID, 
        client_secret=CLIENT_SECRET
    )
    if not creds.valid:
        creds.refresh(Request())
    
    return build('drive', 'v3', credentials=creds), build('youtube', 'v3', credentials=creds)

# --- 3. VIDEO EDITING (Pro Mode) ---
def edit_video(raw_path, final_path):
    print("🎬 Editing Video: Speed, Color & Border...")
    clip = VideoFileClip(raw_path)
    
    # 1. Speed 1.1x
    clip = clip.fx(vfx.speedx, 1.1)
    
    # 2. Color Vibrance 1.2x
    clip = clip.fx(vfx.colorx, 1.2)
    
    # 3. White Border
    clip = clip.margin(top=40, bottom=40, left=40, right=40, color=(255, 255, 255))
    
    # Save
    clip.write_videofile(
        final_path, 
        codec="libx264", 
        audio_codec="aac", 
        fps=24, 
        verbose=False, 
        logger=None
    )
    print("✅ Editing Complete!")

# --- 4. METADATA GENERATOR (Only Satisfying) ---
def get_metadata():
    titles = [
        "Oddly Satisfying Video 🤤 #Shorts", 
        "Deeply Relaxing Visuals ✨ #ASMR", 
        "The Most Satisfying Thing Ever 🧊", 
        "Brain Massage: Visual ASMR 🧠",
        "Can You Watch This Without Tingles? 😴",
        "Ultimate Stress Relief 💆‍♂️ #Satisfying"
    ]
    
    tags = ["satisfying", "oddlysatisfying", "asmr", "relaxing", "stress relief", "slime", "shorts", "visualasmr"]
    cat_id = '24' # Entertainment
    
    insta_tags = "#satisfying #oddlysatisfying #asmr #relaxing #stressrelief #calming #visualasmr #slime #viralreels"
    
    selected_title = random.choice(titles)
    
    # Description for YouTube
    desc = f"{selected_title}\n\nSubscribe for daily relaxation! 🚀\n\n#shorts #{tags[0]} #{tags[1]}"
    
    # Caption for Instagram
    insta_caption = f"{selected_title.split('#')[0].strip()}\n.\nFollow @{INSTA_USER} for more! ❤️\n.\n{insta_tags}"
    
    return selected_title, desc, tags, cat_id, insta_caption

# --- 5. MAIN BOT ---
def main():
    print("--- 🚀 Satisfying Bot Started ---")
    
    try:
        drive, youtube = get_google_services()
    except Exception as e:
        print(f"❌ Login Error: {e}")
        return

    # 1. Fetch Videos from Satisfy Folder Only
    print("Scanning Drive Folder...")
    all_videos = []

    try:
        res_sat = drive.files().list(
            q=f"'{SATISFY_FOLDER_ID}' in parents and mimeType contains 'video/' and trashed=false", 
            fields="files(id, name)"
        ).execute()
        
        all_videos = res_sat.get('files', [])
    except Exception as e:
        print(f"❌ Error Reading Folder: {e}")
        return
    
    if not all_videos:
        print("❌ No videos found in Satisfy Folder.")
        return

    # 2. Random Selection
    video = random.choice(all_videos)
    print(f"🎥 Selected: {video['name']}")

    # 3. Download
    raw_path = "raw_video.mp4"
    final_path = "final_video.mp4"
    
    print("📥 Downloading...")
    request = drive.files().get_media(fileId=video['id'])
    with open(raw_path, "wb") as f:
        downloader = MediaIoBaseDownload(f, request)
        done = False
        while done is False:
            status, done = downloader.next_chunk()

    # 4. Edit Video
    try:
        edit_video(raw_path, final_path)
        upload_file = final_path
    except Exception as e:
        print(f"⚠️ Editing Failed: {e}. Uploading Raw Video.")
        upload_file = raw_path

    # Get Metadata
    yt_title, yt_desc, yt_tags, yt_cat, insta_caption = get_metadata()

    # 5. YouTube Upload
    try:
        print(f"🎥 YouTube Uploading: {yt_title}")
        body = {
            'snippet': {
                'title': yt_title,
                'description': yt_desc,
                'tags': yt_tags,
                'categoryId': yt_cat
            },
            'status': {'privacyStatus': 'public', 'selfDeclaredMadeForKids': False}
        }
        media = MediaFileUpload(upload_file, chunksize=-1, resumable=True)
        youtube.videos().insert(part="snippet,status", body=body, media_body=media).execute()
        print("✅ YouTube Success!")
    except Exception as e:
        print(f"❌ YouTube Failed: {e}")

    # 6. Instagram Upload
    try:
        print("📸 Instagram Uploading...")
        cl = Client()
        
        # Try loading session
        try:
            if INSTA_SESSION:
                cl.set_settings(json.loads(INSTA_SESSION))
        except:
            pass
            
        cl.login(INSTA_USER, INSTA_PASS)
        cl.clip_upload(upload_file, insta_caption)
        print("✅ Instagram Success!")
    except Exception as e:
        print(f"❌ Instagram Failed: {e}")

    # 7. Cleanup (Move to DONE Folder)
    print("🧹 Cleaning up...")
    try:
        # Pata karo file ka parent kaun hai
        file_info = drive.files().get(fileId=video['id'], fields='parents').execute()
        prev_parents = ",".join(file_info.get('parents'))

        drive.files().update(
            fileId=video['id'],
            addParents=DONE_FOLDER_ID,
            removeParents=prev_parents
        ).execute()
        print("✅ Video Moved to Done Folder.")
    except Exception as e:
        print(f"⚠️ Drive Move Failed: {e}")

    # Delete local files
    if os.path.exists(raw_path): os.remove(raw_path)
    if os.path.exists(final_path): os.remove(final_path)
    
    print("🎉 Bot Run Complete!")

if __name__ == "__main__":
    main()
