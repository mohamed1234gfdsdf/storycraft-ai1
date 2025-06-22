# 📖 Step 1 - Simple Draft to Scenes
import streamlit as st
import google.generativeai as genai

# إعداد مفتاح Gemini
GOOGLE_API_KEY = "ضع هنا مفتاح Gemini بتاعك"
genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel("gemini-pro")

# واجهة المستخدم
st.title("📖 StoryCraft - Simple Scene Builder")
story_draft = st.text_area("✍️ أكتب ملخص القصة هنا (درافت بسيط):", height=200)
num_scenes = st.number_input("📸 عدد المشاهد المطلوبة:", min_value=1, max_value=20, value=5, step=1)

if st.button("✅ حلل القصة وطلّع المشاهد"):
    if not story_draft.strip():
        st.warning("⚠️ اكتب ملخص القصة الأول.")
    else:
        with st.spinner("🔍 بيحلل القصة..."):
            prompt = f"""
You are an expert children's story scene planner.

Based on the following draft:
"{story_draft}"

Please generate exactly {num_scenes} separate visual scenes. 
For each scene, return only:
1. Scene title
2. What we see visually
3. The action of the main characters (especially cats if any)

Output each scene clearly numbered. Write in English only.
"""
            try:
                response = model.generate_content(prompt)
                scenes = response.text.strip().split("\n\n")
                st.success("🎉 المشاهد اتحللت بنجاح!")

                for idx, scene in enumerate(scenes, start=1):
                    st.markdown(f"### 🎬 Scene {idx}")
                    st.markdown(scene)
            except Exception as e:
                st.error(f"❌ حصل خطأ أثناء التوليد: {e}")
