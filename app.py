# StoryCraft AI - Full Smart Generator with Trendy Cats 🐾

import streamlit as st
import os
import tempfile
import zipfile
import base64
from PIL import Image
from io import BytesIO
from moviepy.editor import ImageSequenceClip
import google.generativeai as genai

# ========== Google Gemini Setup ==========
GOOGLE_API_KEY = "AIzaSyD__P7mHG3kYbVWfF3XRHZB--8FUSDOFUw"
genai.configure(api_key=GOOGLE_API_KEY)
image_model = genai.GenerativeModel("models/image")
text_model = genai.GenerativeModel("gemini-pro")

# ========== UI Setup ==========
st.set_page_config(layout="wide")
st.title("📖 StoryCraft AI - Full Auto Story to Images/Video")

# ========== Inputs ==========
st.markdown("### ✍️ Write your full story draft")
story_draft = st.text_area("Write your story draft (free text):", height=400)

image_ratio = st.selectbox("Choose image ratio:", ["9:16", "16:9", "1:1"])

use_gemini = st.checkbox("Use Gemini for generation", value=True)
use_huggingface = st.checkbox("Use HuggingFace for video generation", value=False)

# ========== Auto Scene Breakdown ==========
def get_scenes_from_draft(text):
    prompt = f"Break down the following children's story into distinct illustrated scenes. For each scene, provide:\n1. Title\n2. Visual description\n3. Mention if cats appear and their action.\nText:\n{text}"
    response = text_model.generate_content(prompt)
    scenes = response.text.strip().split("Scene")
    return [s.strip() for s in scenes if s.strip()]

# ========== Image Generation ==========
def generate_image(prompt):
    try:
        response = image_model.generate_content([prompt], stream=False)
        image_data = response.candidates[0].content.parts[0].data
        img = Image.open(BytesIO(image_data))
        return img
    except Exception as e:
        st.error(f"Image generation failed: {e}")
        return None

# ========== Generate Scenes ==========
if st.button("🚀 Analyze Story & Generate All Scenes"):
    if not story_draft:
        st.warning("Please enter a draft story first.")
    else:
        scenes = get_scenes_from_draft(story_draft)
        st.session_state["scenes"] = scenes
        st.session_state["images"] = []

        for idx, scene in enumerate(scenes):
            st.markdown(f"#### 🎨 Scene {idx+1}")
            st.text_area(f"📝 Scene Description {idx+1}", value=scene, key=f"scene_{idx}")
            with st.spinner("Generating image..."):
                img = generate_image(scene)
                if img:
                    st.image(img, use_column_width=True)
                    st.session_state["images"].append(img)
                else:
                    st.warning(f"No image generated for scene {idx+1}.")

# ========== Downloads ==========
if st.button("⬇️ Download Prompts + Images"):
    with tempfile.TemporaryDirectory() as tmpdir:
        prompt_path = os.path.join(tmpdir, "prompts.txt")
        with open(prompt_path, "w", encoding="utf-8") as f:
            for idx, scene in enumerate(st.session_state.get("scenes", [])):
                f.write(f"Scene {idx+1}:\n{scene}\n\n")

        for idx, img in enumerate(st.session_state.get("images", [])):
            img_path = os.path.join(tmpdir, f"scene_{idx+1}.jpg")
            img.save(img_path)

        zip_path = os.path.join(tmpdir, "story_bundle.zip")
        with zipfile.ZipFile(zip_path, "w") as zipf:
            zipf.write(prompt_path, arcname="prompts.txt")
            for idx in range(len(st.session_state.get("images", []))):
                zipf.write(os.path.join(tmpdir, f"scene_{idx+1}.jpg"), arcname=f"scene_{idx+1}.jpg")

        with open(zip_path, "rb") as f:
            st.download_button("📦 Download Story ZIP", f, file_name="story.zip")

# ========== Compile to Video ==========
if st.button("🎮 Compile Story into Video"):
    if "images" in st.session_state and st.session_state.images:
        with tempfile.TemporaryDirectory() as tmpdir:
            image_paths = []
            for idx, img in enumerate(st.session_state.images):
                path = os.path.join(tmpdir, f"scene_{idx+1}.jpg")
                img.save(path)
                image_paths.append(path)

            clip = ImageSequenceClip(image_paths, fps=1)
            video_path = os.path.join(tmpdir, "story_video.mp4")
            clip.write_videofile(video_path, codec="libx264", audio=False)

            st.success("✅ Video Compiled!")
            st.video(video_path)
            with open(video_path, "rb") as f:
                st.download_button("⬇️ Download Final Video", f, file_name="final_story.mp4")
    else:
        st.warning("No images found.")
