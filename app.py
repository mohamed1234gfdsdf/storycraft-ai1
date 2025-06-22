# StoryCraft AI - Build Full Story Scenes with Gemini
import streamlit as st
import os
import tempfile
import zipfile
from PIL import Image
from io import BytesIO
from moviepy.editor import ImageSequenceClip
import google.generativeai as genai

# ========== Google Gemini API Setup ==========
genai.configure(api_key="AIzaSyD__P7mHG3kYbVWfF3XRHZB--8FUSDOFUw")
text_model = genai.GenerativeModel(model_name="gemini-1.5-pro")
image_model = genai.GenerativeModel(model_name="models/image")

# ========== Streamlit UI Setup ==========
st.set_page_config(layout="wide")
st.title("📖 StoryCraft AI - Full Auto Story to Images/Video")

st.markdown("### ✍️ Write your story draft")
story_draft = st.text_area("Just describe your story in a few lines (example: a cat and her kitten fishing and they catch a shark)", height=300)

image_ratio = st.selectbox("Choose image ratio:", ["9:16", "16:9", "1:1"])

# ========== Auto Scene Breakdown ==========
def get_scenes_from_draft(text):
    prompt = f"""You're helping create visual scenes for a children's animated video.
Break down this draft story into a list of scenes (no more than 10). For each scene, return:
1. 🎬 Scene Title
2. 📸 Visual Description (what should appear in the image - include cat characters and key objects/actions)

Story draft:
{text}
"""
    response = text_model.generate_content(prompt)
    scenes = response.text.strip().split("\n\n")
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

# ========== Main Scene Generation ==========
if st.button("🚀 Generate All Scenes"):
    if not story_draft:
        st.warning("Please enter a story draft first.")
    else:
        scenes = get_scenes_from_draft(story_draft)
        st.session_state["scenes"] = scenes
        st.session_state["images"] = []

        for idx, scene in enumerate(scenes):
            st.markdown(f"#### 🎬 Scene {idx+1}")
            st.text_area(f"Scene Description {idx+1}", value=scene, key=f"scene_{idx}")
            with st.spinner("Generating image..."):
                img = generate_image(scene)
                if img:
                    st.image(img, use_column_width=True)
                    st.session_state["images"].append(img)
                else:
                    st.warning(f"No image generated for scene {idx+1}.")

# ========== Download Prompts + Images ==========
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
if st.button("🎞️ Compile Story into Video"):
    if "images" in st.session_state and st.session_state["images"]:
        with tempfile
