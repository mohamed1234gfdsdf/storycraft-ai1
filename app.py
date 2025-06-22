# StoryCraft AI - Full Smart Generator with Trendy Cats 🐾

import streamlit as st
import os
import tempfile
import zipfile
from PIL import Image
from io import BytesIO
from moviepy.editor import ImageSequenceClip
import google.generativeai as genai

# ========== Google Gemini Setup ==========
genai.configure(api_key="AIzaSyBYkcyBEkx4xLwJtGalzPAUxl68kesRz9U")
text_model = genai.GenerativeModel(model_name="gemini-1.5-pro")
image_model = genai.GenerativeModel(model_name="models/image")

# ========== UI Setup ==========
st.set_page_config(layout="wide")
st.title("📖 StoryCraft AI - Full Auto Story to Images/Video")

# ========== Inputs ==========
st.markdown("### ✍️ Write your short story draft")
draft = st.text_area("Write a simple story draft (summary or idea):", height=300)
num_scenes = st.slider("How many scenes to generate?", min_value=1, max_value=20, value=5)

# ========== Scene Breakdown ==========
def break_to_scenes(text, count):
    prompt = f"""
    Break this story into {count} short illustrated scenes.
    For each scene, return only the visual description in one paragraph.
    Focus on cinematic cat scenes, with emotional or funny detail.
    Text:
    {text}
    """
    response = text_model.generate_content(prompt)
    return response.text.strip().split("\n")

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

# ========== Generate Story ==========
if st.button("🚀 Generate Story Scenes"):
    if not draft:
        st.warning("Please enter a story draft first.")
    else:
        with st.spinner("Analyzing and generating scenes..."):
            scenes = break_to_scenes(draft, num_scenes)
            st.session_state["scenes"] = scenes
            st.session_state["images"] = []

            for idx, scene in enumerate(scenes):
                st.markdown(f"#### 🎬 Scene {idx+1}")
                st.text_area(f"📅 Description {idx+1}", value=scene, key=f"scene_{idx}")
                img = generate_image(scene)
                if img:
                    st.image(img, use_column_width=True)
                    st.session_state["images"].append(img)
                else:
                    st.warning(f"No image generated for scene {idx+1}.")

# ========== Download ZIP ==========
if st.button("⬇️ Download All Prompts + Images"):
    with tempfile.TemporaryDirectory() as tmpdir:
        prompt_path = os.path.join(tmpdir, "prompts.txt")
        with open(prompt_path, "w", encoding="utf-8") as f:
            for idx, scene in enumerate(st.session_state.get("scenes", [])):
                f.write(f"Scene {idx+1}:
{scene}\n\n")

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
if st.button("🎮 Compile as Video"):
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
