import streamlit as st
import google.generativeai as genai

# إعداد Google Gemini
genai.configure(api_key="AIzaSyDiDuO9UDhPsA3UDQ7ZXoDfcovKE_Nmyog")
text_model = genai.GenerativeModel("gemini-pro")

# واجهة التطبيق
st.set_page_config(page_title="📖 StoryCraft - Simple Scene Builder", layout="centered")
st.title("📖 StoryCraft - Simple Scene Builder")

# إدخال القصة وعدد المشاهد
st.markdown("### ✍️ اكتب ملخص القصة هنا (درافت بسيط):")
story_draft = st.text_area("مثال: قطة وولدها اصطادوا قرش", height=200)

num_scenes = st.number_input("📸 عدد المشاهد المطلوبة:", min_value=1, max_value=20, value=7)

if st.button("💡 حلل القصة واطلع المشاهد"):
    if not story_draft.strip():
        st.warning("رجاءً اكتب ملخص القصة.")
    else:
        with st.spinner("⏳ بيحلل القصة..."):
            prompt = f"""
قسم القصة التالية إلى {num_scenes} مشهد تصويري مميز. 
كل مشهد يجب أن يحتوي على:
1. عنوان بسيط للمشهد
2. وصف بصري دقيق جدًا كأنك بتحضّر لصورة
3. اذكر إذا كانت القطة أو ابنها ظاهرين، وماذا يفعلون

القصة:
{story_draft}
"""
            try:
                response = text_model.generate_content(prompt)
                scenes = response.text.strip().split("\n\n")

                st.success("✅ تم استخراج المشاهد:")
                for idx, scene in enumerate(scenes):
                    st.markdown(f"#### 🎬 مشهد {idx+1}")
                    st.markdown(scene)

            except Exception as e:
                st.error(f"❌ حصل خطأ أثناء التحليل: {e}")
