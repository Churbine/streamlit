import streamlit as st
import yt_dlp
from PIL import Image
from io import BytesIO
import os
import requests

def download_file_from_google_drive(file_id, destination):
    URL = f"https://drive.google.com/uc?export=download&id={file_id}"
    session = requests.Session()

    response = session.get(URL, stream=True)
    token = None

    # Check for the download warning and handle the download accordingly
    for key, value in response.cookies.items():
        if key.startswith("download_warning"):
            token = value

    if token:
        params = { "confirm": token }
        response = session.get(URL, params=params, stream=True)

    with open(destination, "wb") as f:
        for chunk in response.iter_content(1024):
            if chunk:
                f.write(chunk)
    
    print(f"Downloaded ffmpeg.exe to {destination}")

# Your Google Drive file ID
file_id = "1wWOigaf0oyDGEaAI0KbgMX4GI2uwZpFv"  # Your provided file ID
destination = "ffmpeg.exe"
download_file_from_google_drive(file_id, destination)

# Now you can use 'ffmpeg.exe' in your project
ffmpeg_path = os.path.abspath("ffmpeg.exe")


# --- Utils ---
class MyLogger:
    def debug(self, msg): pass
    def warning(self, msg): st.warning(msg)
    def error(self, msg): st.error(msg)

def get_video_info(url):
    ydl_opts = {'quiet': True, 'logger': MyLogger()}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        return ydl.extract_info(url, download=False)

def download_video(url, file_type, resolution, output_path):
    ydl_opts = {
        'outtmpl': os.path.join(output_path, '%(title)s.%(ext)s'),
        'logger': MyLogger(),
        'quiet': True,
        'ffmpeg_location': 'ffmpeg.exe',  # optional
    }

    if file_type == 'mp4':
        ydl_opts['format'] = f'bestvideo[height<={resolution[:-1]}]+bestaudio/best'
        ydl_opts['postprocessors'] = [{'key': 'FFmpegVideoConvertor', 'preferedformat': 'mp4'}]
    else:
        ydl_opts['format'] = 'bestaudio/best'
        ydl_opts['postprocessors'] = [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }]

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

# --- UI ---
st.set_page_config(page_title="Churbine's YT Downloader", layout="centered")
st.title("🎵 Churbine's YouTube Playlist Downloader")

url = st.text_input("Paste YouTube video or playlist URL")

file_type = st.radio("Download as:", ["mp4", "mp3"])
if file_type == 'mp4':
    resolution = st.selectbox("Select resolution:", ["1080p", "720p", "480p", "360p", "240p", "144p"])
else:
    resolution = None

output_dir = st.text_input("Output folder (relative or absolute)", value="downloads")
os.makedirs(output_dir, exist_ok=True)

if st.button("Fetch and Download"):
    if not url:
        st.error("Please enter a URL.")
    else:
        try:
            info = get_video_info(url)
            entries = info['entries'] if 'entries' in info else [info]
            for entry in entries:
                st.markdown(f"**🎬 {entry['title']}**")

                # Thumbnail
                if thumb := entry.get('thumbnail'):
                    response = requests.get(thumb)
                    img = Image.open(BytesIO(response.content))
                    st.image(img, width=240)

                # Download
                with st.spinner(f"Downloading {entry['title']}..."):
                    download_video(entry['webpage_url'], file_type, resolution, output_dir)
                    st.success(f"✅ Downloaded: {entry['title']}")
        except Exception as e:
            st.error(f"Error: {e}")
