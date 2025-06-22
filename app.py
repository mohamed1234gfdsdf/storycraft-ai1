# StoryCraft AI Setup - Full Version

import streamlit as st
import os
import zipfile
import tempfile
from moviepy.editor import concatenate_videoclips, VideoFileClip, AudioFileClip, CompositeAudioClip
import google.generativeai as genai
from PIL import Image
import base64
from io import BytesIO

# Initialize Gemini API
GOOGLE_API_KEY = "AIzaSyA6_qwHcCEw9hPwuYubsaAZqH5XSo_5FL8"
genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel("models/image")

# Title
st.set_page_config(layout="wide")
st.title("🎬 StoryCraft AI - Generate & Animate Trendy Cat Stories")

# Session state
if "scenes" not in st.session_state:
    st.session_state["scenes"] = []
if "audio_map" not in st.session_state:
    st.session_state["audio_map"] = {}
if "generated_images" not in st.session_state:
    st.session_state["generated_images"] = {}

# Character bank
DEFAULT_CHARACTERS = [
    "Fluffy the Chef Cat",
    "Luna the Adventurer",
    "Zeko the Curious Kitten",
    "Milo the Trendy Explorer"
]

# Sound Effects Mapping
SOUND_LIBRARY = {
    "eating": "sounds/eating.mp3",
    "meow": "sounds/meow.mp3",
    "broom": "sounds/broom.mp3",
    "water": "sounds/water.mp3",
    "footsteps": "sounds/footsteps.mp3",
    "chirping": "sounds/birds.mp3"
}

def pick_sound(description):
    if any(word in description.lower() for word in ["eat", "food", "bite"]):
        return SOUND_LIBRARY["eating"]
    if "meow" in description.lower():
        return SOUND_LIBRARY["meow"]
    if any(word in description.lower() for word in ["broom", "clean"]):
        return SOUND_LIBRARY["broom"]
    if "water" in description.lower():
        return SOUND_LIBRARY["water"]
    if any(word in description.lower() for word in ["walk", "run", "step"]):
        return SOUND_LIBRARY["footsteps"]
    if "bird" in description.lower():
        return SOUND_LIBRARY["chirping"]
    return None

def generate_image_from_description(description):
    response = model.generate_content([description], stream=False)
    image_data = response.candidates[0].content.parts[0].data
    img = Image.open(BytesIO(image_data))
    return img

# Sidebar
with st.sidebar:
    st.header("📦 Manage Scenes")
    add_scene = st.button("➕ Add New Scene")
    if add_scene:
        st.session_state.scenes.append({"title": "Untitled Scene", "desc": "", "image_path": None, "video_path": None})

    clear = st.button("🗑️ Clear All")
    if clear:
        st.session_state.scenes = []
        st.session_state.audio_map = {}
        st.session_state.generated_images = {}

# Scene inputs
for idx, scene in enumerate(st.session_state.scenes):
    with st.expander(f"🎞️ Scene {idx + 1}: {scene['title']}", expanded=True):
        scene["title"] = st.text_input("Scene Title", value=scene["title"], key=f"title_{idx}")
        scene["desc"] = st.text_area("Scene Description", value=scene["desc"], key=f"desc_{idx}")
        scene["image_path"] = st.file_uploader("Upload Image (Optional)", type=["png", "jpg"], key=f"img_{idx}")
        scene["video_path"] = st.file_uploader("Upload Video (Optional)", type=["mp4"], key=f"vid_{idx}")

        selected_audio = pick_sound(scene["desc"])
        if selected_audio:
            st.session_state.audio_map[idx] = selected_audio
            st.audio(selected_audio)

        if st.button("🖼️ Generate Image with Gemini", key=f"gen_img_{idx}"):
            with st.spinner("Generating image from Gemini..."):
                img = generate_image_from_description(scene["desc"])
                st.session_state.generated_images[idx] = img

        if idx in st.session_state.generated_images:
            st.image(st.session_state.generated_images[idx], caption="Generated Image", use_column_width=True)

        if st.button("🗑️ Delete Scene", key=f"delete_{idx}"):
            st.session_state.scenes.pop(idx)
            break

# Downloads
st.markdown("---")
col1, col2 = st.columns(2)

with col1:
    if st.button("⬇️ Download All Prompts"):
        with tempfile.NamedTemporaryFile(delete=False, suffix="_prompts.txt") as tmp:
            for sc in st.session_state.scenes:
                tmp.write(f"{sc['title']}:\n{sc['desc']}\n\n".encode("utf-8"))
            st.download_button("Download Prompts", tmp.name, file_name="all_prompts.txt")

with col2:
    if st.button("⬇️ Download All Images"):
        with tempfile.NamedTemporaryFile(delete=False, suffix=".zip") as zf:
            with zipfile.ZipFile(zf.name, "w") as zipf:
                for i, sc in enumerate(st.session_state.scenes):
                    if sc["image_path"]:
                        zipf.write(sc["image_path"].name, f"scene_{i+1}.jpg")
                    elif i in st.session_state.generated_images:
                        img_path = os.path.join(tempfile.gettempdir(), f"scene_{i+1}_gen.jpg")
                        st.session_state.generated_images[i].save(img_path)
                        zipf.write(img_path, f"scene_{i+1}.jpg")
            st.download_button("Download Images ZIP", zf.name, file_name="images.zip")

# Final compilation
if st.button("🎞️ Compile Full Story Video"):
    temp_videos = []
    for idx, sc in enumerate(st.session_state.scenes):
        if sc["video_path"]:
            video = VideoFileClip(sc["video_path"].name).subclip(0, min(5, VideoFileClip(sc["video_path"].name).duration))
            audio_path = st.session_state.audio_map.get(idx)
            if audio_path:
                audio = AudioFileClip(audio_path).subclip(0, video.duration)
                video = video.set_audio(CompositeAudioClip([video.audio, audio]))
            temp_videos.append(video)

    if temp_videos:
        final = concatenate_videoclips(temp_videos, method="compose")
        final_path = os.path.join(tempfile.gettempdir(), "final_story_video.mp4")
        final.write_videofile(final_path, codec="libx264", audio_codec="aac")
        st.success("🎉 Final video compiled!")
        st.video(final_path)
        with open(final_path, "rb") as f:
            st.download_button("⬇️ Download Final Video", f, file_name="final_story.mp4")
    else:
        st.warning("🚫 No valid videos to compile!")
