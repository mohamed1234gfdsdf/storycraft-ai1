import streamlit as st
import openai
import json
import requests
import zipfile
import io
import base64

# Set page configuration
st.set_page_config(
    page_title="AI Story Generator",
    layout="wide"
)

# Title
st.title("📚 AI Story + Image Generator")

# Sidebar settings
st.sidebar.title("Settings")

# API Keys
openai_api_key = st.sidebar.text_input("Enter your OpenAI API key", type="password")

# Prompt input
prompt_input = st.text_area("✏️ Write your story prompt:", height=150)

# Number of scenes
num_scenes = st.slider("Number of Scenes", min_value=1, max_value=10, value=5)

# Story language
language = st.selectbox("Select story language", ["English", "Arabic"])

# Output style
output_type = st.selectbox("Output Type", ["Narrative", "Dialogues"])

# Image style prompt (added for better visuals)
image_style = st.text_input("Image Style (e.g., Pixar style, realistic, watercolor)", value="Pixar style")

# Generate button
generate_button = st.button("🚀 Generate Story + Images")

# Display JSON
debug_mode = st.checkbox("Show Raw JSON Output")
# Function to break the story into scenes (via Gemini API)
def break_to_scenes(draft, num_scenes):
    try:
        prompt = f"""
        Break this story into {num_scenes} clear visual scenes, and return them in JSON format with keys:
        - scene_number
        - scene_text (short visual description)
        - image_prompt (English only, 9:16 format, with visual keywords for image generation, no text on image)
        
        Story:
        {draft}
        """
        response = requests.post(
            "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent",
            params={"key": google_api_key},
            headers={"Content-Type": "application/json"},
            json={"contents": [{"parts": [{"text": prompt}]}]}
        )
        return response.json()
    except Exception as e:
        st.error(f"Error breaking story into scenes: {e}")
        return None
# Function to call DALL·E 3 API to generate image
def generate_image(prompt):
    try:
        response = openai.Image.create(
            model="dall-e-3",
            prompt=prompt,
            n=1,
            size="1024x1792"  # 9:16 vertical format
        )
        return response["data"][0]["url"]
    except Exception as e:
        st.error(f"Image generation failed: {e}")
        return None
# عندما يضغط المستخدم على زر Generate
if generate_button and openai_api_key and prompt_input:
    st.info("Generating story and images... Please wait ⏳")

    openai.api_key = openai_api_key

    # Step 1: Generate full story draft (using OpenAI GPT-4 or similar)
    try:
        story_prompt = f"Write a short children's story in {language} with {num_scenes} scenes, in {output_type} format. Prompt: {prompt_input}"
        story_response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a creative children's story writer."},
                {"role": "user", "content": story_prompt}
            ]
        )
        story_text = story_response.choices[0].message.content
        st.success("✅ Story generated successfully!")
        st.markdown("### 📖 Story")
        st.markdown(story_text)
    except Exception as e:
        st.error(f"Failed to generate story: {e}")
        story_text = ""

    # Step 2: Break story into scenes (via Gemini API)
    google_api_key = st.sidebar.text_input("Google API Key (for Gemini)", type="password")
    scenes_data = break_to_scenes(story_text, num_scenes)

    if scenes_data:
        scenes = []
        try:
            # Try extracting JSON directly
            scenes_json = json.loads(scenes_data["candidates"][0]["content"]["parts"][0]["text"])
            scenes = scenes_json
        except Exception as e:
            st.warning("⚠ Could not parse scenes as JSON, showing raw:")
            st.text(scenes_data)

        image_urls = []
        zip_buffer = io.BytesIO()
        zip_file = zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED)

        for scene in scenes:
            st.markdown(f"### 🎬 Scene {scene['scene_number']}")
            st.markdown(f"📝 {scene['scene_text']}")

            image_prompt = scene["image_prompt"] + ", " + image_style
            image_url = generate_image(image_prompt)

            if image_url:
                st.image(image_url, caption=f"Scene {scene['scene_number']}", use_column_width=True)
                image_data = requests.get(image_url).content
                zip_file.writestr(f"scene_{scene['scene_number']}.png", image_data)
                image_urls.append(image_url)

        zip_file.close()

        # Provide download link
        b64 = base64.b64encode(zip_buffer.getvalue()).decode()
        href = f'<a href="data:application/zip;base64,{b64}" download="story_images.zip">📥 Download All Images as ZIP</a>'
        st.markdown(href, unsafe_allow_html=True)
# عرض الـ JSON الخام لو المستخدم فعل debug mode
if debug_mode and scenes_data:
    st.markdown("### 🐞 Raw JSON Output")
    st.json(scenes_data)
