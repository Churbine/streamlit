import streamlit as st
import yt_dlp
from PIL import Image
from io import BytesIO
import os
import requests
import tarfile

def download_and_extract_ffmpeg():
    url = "https://drive.google.com/file/d/1WAGOmqa-6yABjuCJ9LjEQs-v3GKxWIWG/view?usp=sharing"
    filename = "ffmpeg.tar.xz"
    extract_dir = "ffmpeg"

    if not os.path.exists(extract_dir):
        response = requests.get(url)
        with open(filename, "wb") as f:
            f.write(response.content)

        with tarfile.open(filename, "r:xz") as tar:
            tar.extractall(extract_dir)

    # Find ffmpeg binary inside extracted folder
    for root, dirs, files in os.walk(extract_dir):
        for file in files:
            if file == "ffmpeg":
                return os.path.abspath(os.path.join(root, file))

    raise FileNotFoundError("FFmpeg binary not found after extraction.")





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
