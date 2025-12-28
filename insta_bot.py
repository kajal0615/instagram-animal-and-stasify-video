import os
import random
import json
import time
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from instagrapi import Client

# --- 1. CONFIGURATION ---
CLIENT_ID = os.environ["CLIENT_ID"]
CLIENT_SECRET = os.environ["CLIENT_SECRET"]
REFRESH_TOKEN = os.environ["REFRESH_TOKEN"]

# Folders
SATISFY_FOLDER_ID = os.environ["DRIVE_SATISFY_ID"]
FUNNY_FOLDER_ID = os.environ["DRIVE_FUNNY_ID"]

# Instagram
INSTA_USER = os.environ["INSTA_USERNAME"]
INSTA_PASS = os.environ["INSTA_PASSWORD"]
INSTA_SESSION = os.environ.get("INSTA_SESSION") # Session Secret

HISTORY_FILE = "history.txt"

def get_drive_service():
    creds = Credentials(None, refresh_token=REFRESH_TOKEN, token_uri="https://oauth2.googleapis.com/token", client_id=CLIENT_ID, client_secret=CLIENT_SECRET)
    if not creds.valid: creds.refresh(Request())
    return build('drive', 'v3', credentials=creds)

def get_videos(service, folder_id, tag):
    try:
        # Shared folder support ke liye ye parameters zaroori hain
        results = service.files().list(
            q=f"'{folder_id}' in parents and mimeType contains 'video/' and trashed=false",
            fields="files(id, name)", 
            supportsAllDrives=True, 
            includeItemsFromAllDrives=True
        ).execute()
        files = results.get('files', [])
        for f in files: f['category'] = tag
        return files
    except Exception as e:
        print(f"Error accessing folder {tag}: {e}")
        return []

def load_history():
    if not os.path.exists(HISTORY_FILE): return []
    with open(HISTORY_FILE, "r") as f: return f.read().splitlines()

def save_history(vid_id):
    with open(HISTORY_FILE, "a") as f: f.write(f"{vid_id}\n")

def get_caption(category):
    if category == "SATISFY":
        titles = ["Oddly Satisfying 🤤", "Deeply Relaxing ✨", "ASMR Visuals 🎧", "So Smooth 🧊", "Brain Massage 🧠"]
        tags = "#satisfying #oddlysatisfying #asmr #relaxing #stressrelief #calming #visualasmr #slime #soapcutting #viralreels"
    else: # FUNNY
        titles = ["Wait for it... 😂", "Too Cute! 🐶", "Funny Animal Fail 🤣", "Instant Mood Boost 💖", "LOL Moment 😆"]
        tags = "#funnyanimals #dogreels #catreels #petfails #funnyvideos #cute #viral #trending #shorts"
    
    return f"{random.choice(titles)}\n.\n.\nFollow @{INSTA_USER} for more!\n{tags}"

def main():
    print("--- Instagram Bot Started ---")
    drive = get_drive_service()
    
    # 1. Fetch Videos
    print("Scanning Drive Folders...")
    all_videos = get_videos(drive, SATISFY_FOLDER_ID, "SATISFY") + get_videos(drive, FUNNY_FOLDER_ID, "FUNNY")
    print(f"Total Videos Found: {len(all_videos)}")
    
    if not all_videos:
        print("No videos found! Check Folder Sharing & IDs.")
        return

    # 2. Check History (Avoid Duplicates)
    history = load_history()
    new_videos = [v for v in all_videos if v['id'] not in history]
    
    if not new_videos:
        print("All videos have been uploaded! Please add new content.")
        return

    # 3. Random Selection
    video = random.choice(new_videos)
    print(f"Selected: {video['name']} (Category: {video['category']})")

    # 4. Download
    print("Downloading...")
    with open("insta_post.mp4", "wb") as f:
        f.write(drive.files().get_media(fileId=video['id']).execute())

    # 5. Instagram Login (SESSION METHOD)
    print("Logging into Instagram...")
    cl = Client()
    try:
        # Session Load karo
        if INSTA_SESSION:
            print("Using Saved Session...")
            cl.set_settings(json.loads(INSTA_SESSION))
        
        # Login (Session hone par ye safe hai)
        cl.login(INSTA_USER, INSTA_PASS)
        
        # Upload
        print("Uploading Reel...")
        cl.clip_upload(path="insta_post.mp4", caption=get_caption(video['category']))
        print("Upload Successful!")
        
        # Save to History
        save_history(video['id'])
        print("History Updated.")

    except Exception as e:
        print(f"Instagram Upload Failed: {e}")
        exit(1)

if __name__ == "__main__":
    main()
