# StoryCraft AI – Simple Draft to Scenes Generator 🐾

import streamlit as st
import google.generativeai as genai
from PIL import Image
from io import BytesIO
import tempfile
import os
import zipfile

# ====== إعداد مفتاح API ======
GOOGLE_API_KEY = "AIzaSyD__P7mHG3kYbVWfF3XRHZB--8FUSDOFUw"
genai.configure(api_key=GOOGLE_API_KEY)
text_model = genai.GenerativeModel("gemini-1.5-pro")
image_model = genai.GenerativeModel("models/image")

# ====== واجهة المستخدم ======
st.set_page_config(page_title="StoryCraft AI", layout="wide")
st.title("📖 StoryCraft AI – قصص القطط التريندي")

# ====== مدخلات المستخدم ======
draft = st.text_input("📝 اكتب ملخص القصة (مثال: قطة وأبنها اصطادوا سمكة قرش)", "")
num_scenes = st.number_input("🎬 عدد المشاهد المطلوبة", min_value=1, max_value=20, value=5)

# ====== تحليل المشاهد من الدرافت ======
def break_to_scenes(draft, num_scenes):
    prompt = f"""قسم القصة التالية إلى {num_scenes} مشاهد تصويرية مناسبة لكتاب أطفال. 
لكل مشهد اكتب:
1. عنوان قصير للمشهد
2. وصف تفصيلي للمشهد (المكان، القطة، الطفل، وضعيتهم، الحدث)
3. صيغة الوصف تكون مناسبة لتوليد صورة.

القصة: {draft}
"""
    response = text_model.generate_content(prompt)
    return response.text.strip().split("\n\n")

# ====== توليد صورة من الوصف ======
def generate_image(prompt):
    try:
        res = image_model.generate_content([prompt])
        image_data = res.candidates[0].content.parts[0].data
        return Image.open(BytesIO(image_data))
    except Exception as e:
        st.error(f"خطأ في توليد الصورة: {e}")
        return None

# ====== زر البدء ======
if st.button("🚀 تحليل القصة وتوليد المشاهد"):
    if draft.strip() == "":
        st.warning("من فضلك اكتب ملخص القصة أولاً.")
    else:
        scenes = break_to_scenes(draft, num_scenes)
        images = []

        for i, scene in enumerate(scenes):
            st.markdown(f"### 🎬 مشهد {i+1}")
            st.text(scene)
            with st.spinner("⏳ جاري توليد الصورة..."):
                img = generate_image(scene)
                if img:
                    st.image(img, caption=f"مشهد {i+1}", use_column_width=True)
                    images.append((scene, img))

        # تحميل ZIP
        with tempfile.TemporaryDirectory() as tmpdir:
            zip_path = os.path.join(tmpdir, "story_export.zip")
            with zipfile.ZipFile(zip_path, "w") as zipf:
                for idx, (desc, img) in enumerate(images):
                    desc_file = os.path.join(tmpdir, f"scene_{idx+1}.txt")
                    img_file = os.path.join(tmpdir, f"scene_{idx+1}.jpg")
                    with open(desc_file, "w", encoding="utf-8") as f:
                        f.write(desc)
                    img.save(img_file)
                    zipf.write(desc_file, f"scene_{idx+1}.txt")
                    zipf.write(img_file, f"scene_{idx+1}.jpg")

            with open(zip_path, "rb") as f:
                st.download_button("⬇️ تحميل كل المشاهد", f, file_name="story.zip")

