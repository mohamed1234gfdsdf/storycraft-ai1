import React, { useState, useEffect } from 'react';
import { Loader2, Book, Lightbulb, Download, Eye, Pencil } from 'lucide-react';

function App() {
  const [storyIdea, setStoryIdea] = useState('');
  const [numScenes, setNumScenes] = useState(6);
  const [storyType, setStoryType] = useState(''); // Default to empty, forcing selection
  const [currentStory, setCurrentStory] = useState(null); // Stores the generated story object
  const [isLoadingStory, setIsLoadingStory] = useState(false);
  const [generatingImages, setGeneratingImages] = useState({}); // { scene_index: boolean }
  const [imageGenerationErrors, setImageGenerationErrors] = useState({}); // { scene_index: string }
  const [showPromptModal, setShowPromptModal] = useState(null); // null or { index, prompt }
  const [showMotionPromptModal, setShowMotionPromptModal] = useState(null); // null or { index, prompt }
  const [editPromptMode, setEditPromptMode] = useState(null); // null or scene_index
  const [imageAspectRatio, setImageAspectRatio] = useState('16:9'); // Default to 16:9

  // New state for selecting Image Generation Model
  const [imageGenerator, setImageGenerator] = useState('google-imagen'); // 'google-imagen' or 'openai-dall-e'
  // New state for OpenAI API Key (if DALL-E is selected)
  const [openAIApiKey, setOpenAIApiKey] = useState('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');

  const [isDownloadReady, setIsDownloadReady] = useState(false); // New state to check if JSZip/FileSaver are loaded
  const [isDownloading, setIsDownloading] = useState(false); // New state for download button loading

  // States for cat character customization
  const [catCharacters, setCatCharacters] = useState([
    { name: 'Mama Cat', color: 'برتقالي', size: 'متوسط', type: 'تابي', customDescription: '' },
    { name: 'Little Kitten', color: 'رمادي', size: 'صغير', type: 'تابي', customDescription: '' },
  ]);

  // API Key for Google AI models. Canvas will provide this in runtime if running in Canvas.
  // IMPORTANT: If running locally (outside Canvas), you MUST replace this empty string
  // with your actual Google AI Studio / Google Cloud API Key for Gemini/Imagen.
  const googleApiKey = ""; 

  // Effect to load JSZip and FileSaver from CDN and set isDownloadReady
  useEffect(() => {
    const loadScript = (src, onLoadCallback) => {
      const script = document.createElement('script');
      script.src = src;
      script.onload = onLoadCallback;
      script.onerror = () => console.error(`Failed to load script: ${src}`);
      document.body.appendChild(script);
    };

    let jszipLoaded = false;
    let fileSaverLoaded = false;

    const checkReady = () => {
      if (jszipLoaded && fileSaverLoaded) {
        setIsDownloadReady(true);
      }
    };

    if (typeof window.JSZip === 'undefined') {
      loadScript('https://cdnjs.cloudflare.com/ajax/libs/jszip/3.10.1/jszip.min.js', () => {
        jszipLoaded = true;
        checkReady();
      });
    } else {
      jszipLoaded = true;
    }

    if (typeof window.saveAs === 'undefined') {
      loadScript('https://cdnjs.cloudflare.com/ajax/libs/FileSaver.js/2.0.5/FileSaver.min.js', () => {
        fileSaverLoaded = true;
        checkReady();
      });
    } else {
      fileSaverLoaded = true;
    }

    checkReady();
  }, []);

  // Handler for changing individual cat character properties
  const handleCatCharacterChange = (index, field, value) => {
    setCatCharacters(prevChars =>
      prevChars.map((char, i) =>
        i === index ? { ...char, [field]: value } : char
      )
    );
  };

  // Function to dynamically generate character descriptions based on user choices or default
  const generateDynamicCharacterDescription = () => {
    if (storyType !== 'قصص قطط') {
      return `Mama Cat: a plump adult orange tabby cat with soft realistic fur and light cream stripes, wide amber eyes, a small pink nose, clean whiskers. She wears a beige kitchen apron tied at the back. Always standing upright on her hind legs with a confident posture. Little Kitten: a small light gray tabby kitten with soft fur, big green eyes, a round face, and a blue-and-white pacifier in his mouth. Often sitting or standing near Mama.`;
    }

    return catCharacters.map(char => {
      let description = `${char.name}: A `;
      if (char.size === 'كبير') {
        description += `very large, plump `;
      } else if (char.size === 'صغير') {
        description += `tiny, delicate `;
      } else {
        description += `medium-sized `;
      }
      description += `${char.color} ${char.type} cat with soft realistic fur, `;
# Explicitly state "cat" nature for Mama Cat's posture to avoid human-like appearance
      if (char.name === 'Mama Cat') {
        description += `wide amber eyes, a small pink nose, clean whiskers. She wears a beige kitchen apron tied at the back. Always standing upright on her hind legs with a confident, CAT-LIKE posture, not human-like.`;
      } else if (char.name === 'Little Kitten') {
        description += `big green eyes, a round face, and a blue-and-white pacifier in his mouth. Often sitting or standing near Mama.`;
      }
      if (char.customDescription.trim()) {
        description += ` Additional details: ${char.customDescription.trim()}.`;
      }
      return description;
    }).join(' ');
  };

  // Function to call the Gemini API for text generation (gemini-2.0-flash)
  const generateTextWithGemini = async (prompt, schema = null) => {
    if (imageGenerator === 'google-imagen' && !googleApiKey) {
      alert("خطأ: الرجاء إدخال مفتاح API الخاص بـ Google لتوليد النص والصور باستخدام Google Imagen.");
      throw new Error("Google API Key is missing for Imagen/Gemini.");
    }
    try {
      let chatHistory = [{ role: "user", parts: [{ text: prompt }] }];
      const payload = { contents: chatHistory };

      if (schema) {
        payload.generationConfig = {
          responseMimeType: "application/json",
          responseSchema: schema
        };
      }

      const apiUrl = `https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key=${googleApiKey}`;

      const response = await fetch(apiUrl, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      if (!response.ok) {
        const errorData = await response.json();
        console.error('Gemini Text API Error:', errorData);
        throw new Error(`Failed to generate text: ${response.statusText} - ${errorData.error?.message || ''}. الرجاء التحقق من مفتاح الـ API الخاص بـ Google والمحاولة مرة أخرى. (خطأ رقم ${response.status})`);
      }

      const result = await response.json();
      if (result.candidates && result.candidates.length > 0 &&
        result.candidates[0].content && result.candidates[0].content.parts &&
        result.candidates[0].content.parts.length > 0) {
        const text = result.candidates[0].content.parts[0].text;
        return schema ? JSON.parse(text) : text;
      } else {
        console.warn('Gemini Text API: Unexpected response structure or no content.');
        return null;
      }
    } catch (error) {
      console.error('Error generating text with Gemini:', error);
      alert(`حدث خطأ أثناء توليد القصة: ${error.message}. الرجاء التحقق من مفتاح الـ API الخاص بـ Google والمحاولة مرة أخرى.`);
      throw error;
    }
  };

  // Function to call the Imagen API for image generation (imagen-3.0-generate-002)
  const callGoogleImagenAPI = async (prompt) => {
    if (!googleApiKey) {
      alert("خطأ: الرجاء إدخال مفتاح API الخاص بـ Google لتوليد الصور باستخدام Google Imagen.");
      throw new Error("Google API Key is missing for Imagen.");
    }
    try {
      const payload = { instances: { prompt: prompt }, parameters: { "sampleCount": 1 } };
      const apiUrl = `https://generativelanguage.googleapis.com/v1beta/models/imagen-3.0-generate-002:predict?key=${googleApiKey}`;

      const response = await fetch(apiUrl, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      const responseText = await response.text();

      if (!response.ok) {
        const errorData = await response.json();
        console.error('Imagen API Error:', errorData);
        throw new Error(`Failed to generate image with Imagen: ${response.statusText} - ${errorData.error?.message || ''}. الرجاء التحقق من مفتاح الـ API الخاص بـ Google والمحاولة مرة أخرى. (خطأ رقم ${response.status})`);
      }

      if (!responseText) {
        console.warn('Imagen API: Empty response body received.');
        return null;
      }

      const result = JSON.parse(responseText);
      if (result.predictions && result.predictions.length > 0 && result.predictions[0].bytesBase64Encoded) {
        return `data:image/png;base64,${result.predictions[0].bytesBase64Encoded}`; // Return Base64 URL
      } else {
        console.warn('Imagen API: Unexpected response structure or no image data in parsed JSON.');
        return null;
      }
    } catch (error) {
      console.error('Error generating image with Imagen:', error);
      alert(`حدث خطأ أثناء توليد الصورة باستخدام Imagen: ${error.message}. الرجاء التحقق من مفتاح الـ API الخاص بـ Google والمحاولة مرة أخرى.`);
      return null;
    }
  };

  // Function to call the OpenAI DALL-E API for image generation
  const callOpenAIDallEAPI = async (prompt) => {
    if (!openAIApiKey) {
      alert("خطأ: الرجاء إدخال مفتاح API الخاص بـ OpenAI لاستخدام DALL-E.");
      throw new Error("OpenAI API Key is missing for DALL-E.");
    }

    let size = "1024x1024"; // Default DALL-E 3 size
    let model = "dall-e-3";

    if (imageAspectRatio === '16:9') {
      size = "1792x1024"; // DALL-E 3 landscape
    } else if (imageAspectRatio === '9:16') {
      size = "1024x1792"; // DALL-E 3 portrait
    }

    try {
      const response = await fetch('https://api.openai.com/v1/images/generations', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${openAIApiKey}`
        },
        body: JSON.stringify({
          prompt: prompt,
          n: 1, // Number of images to generate
          size: size,
          model: model,
          quality: "standard" // or "hd"
        })
      });

      if (!response.ok) {
        const errorData = await response.json();
        console.error('DALL-E API Error:', errorData);
        throw new Error(`Failed to generate image with DALL-E: ${response.statusText} - ${errorData.error?.message || ''}. الرجاء التحقق من مفتاح الـ API الخاص بـ OpenAI وصلاحيته. (خطأ رقم ${response.status})`);
      }

      const data = await response.json();
      if (data.data && data.data.length > 0 && data.data[0].url) {
        return data.data[0].url; // DALL-E returns a direct URL
      } else {
        console.warn('DALL-E API: Unexpected response structure or no image URL.');
        return null;
      }
    } catch (error) {
      console.error('Error generating image with DALL-E:', error);
      alert(`حدث خطأ أثناء توليد الصورة باستخدام DALL-E: ${error.message}. الرجاء التحقق من مفتاح الـ API الخاص بـ OpenAI وصلاحيته.`);
      return null;
    }
  };


  const generateStoryOutline = async (type) => {
    setIsLoadingStory(true);
    setCurrentStory(null);
    setGeneratingImages({});
    setImageGenerationErrors({}); // Clear previous errors

    // Get dynamic character descriptions based on user choices or default
    const charactersDynamicDescription = generateDynamicCharacterDescription(); // Base description

    // Determine aspect ratio prompt part based on user selection
    let aspectRatioText = '';
    if (imageAspectRatio === '9:16') {
      // VERY STRONG EMPHASIS FOR 9:16 VERTICAL OUTPUT, combining user suggestions
      aspectRatioText = 'Output image MUST be 9:16 aspect ratio. Generate a tall, vertical, portrait-oriented image with exact dimensions of 1080 pixels width by 1920 pixels height. Strictly avoid square images, horizontal images, skewed images, or any other aspect ratio. The orientation must be strictly portrait, no rotation. This specific vertical resolution is CRITICAL for YouTube Shorts, so ensure the image is tall and narrow, not square or wide.';
      if (imageGenerator === 'openai-dall-e') {
        imageGeneratorSpecificPrompt = ' Ensure the image output size is 1024x1792 pixels. ';
      }
    } else { // 16:9
      aspectRatioText = 'Aspect ratio 16:9, horizontal, landscape (1920x1080 pixels). Strictly avoid square images, vertical images, skewed images, or any other aspect ratio. The orientation must be strictly landscape, no rotation.';
      if (imageGenerator === 'openai-dall-e') {
        imageGeneratorSpecificPrompt = ' Ensure the image output size is 1792x1024 pixels. ';
      }
    }
    
    // Strengthened prompt for composition - **CRITICAL FOR IMAGE QUALITY**
    const compositionPrompt = `
      **Composition Rules (CRITICAL):** Ensure all characters are **fully visible within the frame**, **well-composed**, **centrally placed**, and **uncropped** (no cut-off bodies or heads). The scene should be a **full-body shot** of all characters, providing a wide view of their surroundings. Avoid any form of cropping. Maintain the exact requested aspect ratio.
    `;

    // Prompt rule for facial expressions
    const facialExpressionBasePrompt = `Character faces should vividly express emotions and reactions appropriate to the scene's mood and narrative (e.g., happy, sad, surprised, curious, playful, worried, angry, confused). Ensure diverse and dynamic facial expressions for each character based on the scene context.`;

    // ENHANCED: Character Consistency with more strong negative phrasing against human-like traits.
    const characterConsistencyBasePrompt = `
      **Character Consistency (CRITICAL & ABSOLUTE):** The characters (Mama Cat, Little Kitten) MUST maintain their EXACT SAME FELINE appearance, species (they are PURE CATS, NOT HUMANS or any other animal species), colors, patterns, and proportions across ALL scenes in the story. Their size relative to each other (e.g., Little Kitten is always much smaller compared to Mama Cat) must be strictly consistent. They are always real cats, NEVER HUMANS, NEVER HUMAN-LIKE, NEVER BIPEDAL (unless explicitly standing on hind legs, but retaining full cat physiology), and NEVER ANTHROPOMORPHIC. Avoid any variations in their design, details, or species from one scene to another.
    `;

    try {
      let prompt = '';
      // The prompt sent to Gemini to generate scene outlines, including detailed image_prompt instructions
      // It must contain all rules so Gemini incorporates them into its generated image_prompt strings.
      const imagePromptGenerationInstruction = `
        A detailed image generation prompt for ${imageGenerator === 'openai-dall-e' ? 'DALL-E 3' : 'Imagen 3.0'} based on the scene summary.
        This prompt MUST include:
        1. All character details: "${charactersDynamicDescription.trim()}"
        2. Strict visual rules: "${imageGeneratorSpecificPrompt} ${characterConsistencyBasePrompt} ${aspectRatioText} ${compositionPrompt} ${facialExpressionBasePrompt} EXTREMELY WIDE SHOT, Full-body characters visible, No cropping, Clear background, Realistic lighting, No cartoon exaggeration."
        3. A specific description of the environment and action from the scene summary.
        Example: "Mama Cat: ...; Little Kitten: ...; Composition Rules: ...; Aspect Ratio: ...; Character Consistency: ...; Facial Expression: ...; In a cozy kitchen, Mama Cat is happily baking cookies while Little Kitten curiously watches her, eyes sparkling with excitement."
      `;

      if (type === 'idea') {
        prompt = `
          Generate a story outline with exactly ${numScenes} scenes based on the idea: '${storyIdea}'.
          Each scene must have:
          1. "title": A concise scene title in Arabic.
          2. "summary_ar": A summary in Egyptian Arabic dialect, suitable for children.
          3. "image_prompt": ${imagePromptGenerationInstruction}
          4. "motion_prompt": A detailed prompt describing potential motion/animation for the scene in Arabic, based on its summary.

          Provide the output as a JSON object with a 'story' key, which is an array of scene objects.
        `;
      } else if (type === 'suggest') {
        prompt = `
          Generate a "${storyType}" story outline with exactly ${numScenes} scenes.
          Each scene must have:
          1. "title": A concise scene title in Arabic.
          2. "summary_ar": A summary in Egyptian Arabic dialect, suitable for children.
          3. "image_prompt": ${imagePromptGenerationInstruction}
          4. "motion_prompt": A detailed prompt describing potential motion/animation for the scene in Arabic, based on its summary.

          Provide the output as a JSON object with a 'story' key, which is an array of scene objects.
        `;
      }

      const schema = {
        type: "OBJECT",
        properties: {
          story: {
            type: "ARRAY",
            items: {
              type: "OBJECT",
              properties: {
                title: { type: "STRING" },
                summary_ar: { type: "STRING" },
                image_prompt: { type: "STRING" },
                motion_prompt: { type: "STRING" }
              },
              required: ["title", "summary_ar", "image_prompt", "motion_prompt"]
            }
          }
        },
        required: ["story"]
      };

      const generatedStoryData = await generateTextWithGemini(prompt, schema);
      if (generatedStoryData && generatedStoryData.story && generatedStoryData.story.length > 0) {
        const initialScenes = generatedStoryData.story.map((scene) => ({
          ...scene,
          image_url: null, // Initialize image_url as null
        }));
        setCurrentStory({
          id: `story-${Date.now()}`,
          title: storyIdea || `${storyType} Story`,
          type: type,
          story: initialScenes, // Use 'story' key consistently
        });
      } else {
        console.error("No scenes generated by the LLM.");
        alert("لم يتم توليد أي مشاهد. الرجاء المحاولة مرة أخرى بفكرة مختلفة أو ضبط المعلمات.");
      }
    } catch (error) {
      console.error("Error generating story outline:", error);
      // Error message already shown by generateTextWithGemini
    } finally {
      setIsLoadingStory(false);
    }
  };

  // Centralized function to generate image based on selected generator
  const generateImageForScene = async (sceneIndex, prompt, retryCount = 0) => {
    const MAX_RETRIES = 2; // Number of times to retry failed image generation

    setGeneratingImages(prev => ({ ...prev, [sceneIndex]: true }));
    setImageGenerationErrors(prev => ({ ...prev, [sceneIndex]: '' })); // Clear previous error for this scene

    let imageUrl = null;
    try {
      await new Promise(resolve => setTimeout(resolve, 1000)); // Small delay before each attempt
      
      if (imageGenerator === 'google-imagen') {
        if (!googleApiKey) {
          throw new Error("Google API Key is missing for Imagen.");
        }
        imageUrl = await callGoogleImagenAPI(prompt);
      } else if (imageGenerator === 'openai-dall-e') {
        if (!openAIApiKey) {
          throw new Error("OpenAI API Key is missing for DALL-E.");
        }
        imageUrl = await callOpenAIDallEAPI(prompt);
      }

      if (imageUrl) {
        setCurrentStory(prevStory => {
          if (!prevStory) return prevStory;
          const updatedScenes = [...prevStory.story];
          updatedScenes[sceneIndex] = {
            ...updatedScenes[sceneIndex],
            image_url: imageUrl,
          };
          return { ...prevStory, story: updatedScenes };
        });
      } else {
        // If image generation failed, log and possibly retry
        console.warn(`Failed to generate image for scene ${sceneIndex + 1} with ${imageGenerator} (Attempt ${retryCount + 1}).`);
        if (retryCount < MAX_RETRIES) {
          setImageGenerationErrors(prev => ({ ...prev, [sceneIndex]: `جاري إعادة المحاولة... (${retryCount + 1}/${MAX_RETRIES})` }));
          await new Promise(resolve => setTimeout(resolve, 3000)); // Longer delay before retry
          await generateImageForScene(sceneIndex, prompt, retryCount + 1); // Recursive retry
        } else {
          setImageGenerationErrors(prev => ({ ...prev, [sceneIndex]: 'فشل توليد الصورة بعد عدة محاولات. حاول "إعادة توليد الصورة" يدوياً.' }));
        }
      }
    } catch (error) {
      console.error(`Error generating image for scene ${sceneIndex + 1} with ${imageGenerator}:`, error);
      // If error occurs, set error state and possibly retry
      if (retryCount < MAX_RETRIES) {
        setImageGenerationErrors(prev => ({ ...prev, [sceneIndex]: `فشل (جاري إعادة المحاولة ${retryCount + 1}/${MAX_RETRIES})...` }));
        await new Promise(resolve => setTimeout(resolve, 3000));
        await generateImageForScene(sceneIndex, prompt, retryCount + 1);
      } else {
        setImageGenerationErrors(prev => ({ ...prev, [sceneIndex]: `فشل توليد الصورة: ${error.message}.` }));
      }
    } finally {
      setGeneratingImages(prev => ({ ...prev, [sceneIndex]: false }));
    }
  };

  const handleSceneTextChange = (index, field, value) => {
    setCurrentStory(prevStory => {
      if (!prevStory) return prevStory;
      const updatedScenes = [...prevStory.story];
      updatedScenes[index] = { ...updatedScenes[index], [field]: value };
      return { ...prevStory, story: updatedScenes };
    });
  };

  const handlePromptChange = (index, field, value) => {
    setCurrentStory(prevStory => {
      if (!prevStory) return prevStory;
      const updatedScenes = [...prevStory.story];
      updatedScenes[index] = { ...updatedScenes[index], [field]: value };
      return { ...prevStory, story: updatedScenes };
    });
  };

  // Function to convert Base64 to Blob (still needed for Imagen downloads if it returns Base64)
  const base64ToBlob = (base64, mimeType) => {
    const byteCharacters = atob(base64);
    const byteNumbers = new Array(byteCharacters.length);
    for (let i = 0; i < byteCharacters.length; i++) {
      byteNumbers[i] = byteCharacters.charCodeAt(i);
    }
    const byteArray = new Uint8Array(byteNumbers);
    return new Blob([byteArray], { type: mimeType });
  };

  const handleDownloadAllImages = async () => {
    if (!isDownloadReady) {
      alert("مكتبات التنزيل غير جاهزة بعد. يرجى الانتظار قليلاً والمحاولة مرة أخرى.");
      return;
    }
    if (!currentStory || !currentStory.story || currentStory.story.length === 0) {
      alert("لا توجد صور لتنزيلها.");
      return;
    }
    if (isDownloading) return;

    setIsDownloading(true);
    const zip = new window.JSZip();
    let imagesAdded = 0;

    for (const scene of currentStory.story) {
      if (scene.image_url) {
        try {
          let imageBlob = null;
          if (scene.image_url.startsWith('data:image/')) {
            // For Base64 images (e.g., from Imagen if not changed to direct URL)
            const base64Data = scene.image_url.split(',')[1];
            imageBlob = base64ToBlob(base64Data, 'image/png');
          } else {
            // For direct image URLs (e.g., from DALL-E)
            const response = await fetch(scene.image_url);
            if (!response.ok) throw new Error(`Failed to fetch image from URL: ${scene.image_url}`);
            imageBlob = await response.blob();
          }

          const fileName = `scene_${scene.title.replace(/[^a-zA-Z0-9\u0600-\u06FF\s]/g, '_').substring(0, 50)}.png`;
          zip.file(fileName, imageBlob);
          imagesAdded++;
        } catch (error) {
          console.error(`Failed to process or add image for scene "${scene.title}":`, error);
        }
      } else {
        console.warn(`Scene "${scene.title}" has no valid image URL for download.`);
      }
    }

    if (imagesAdded > 0) {
      try {
        const content = await zip.generateAsync({ type: "blob" });
        window.saveAs(content, "Smart_Story_Builder_Images.zip");
        alert("تم تنزيل الصور بنجاح!");
      } catch (error) {
        console.error("Error zipping or saving images:", error);
        alert("حدث خطأ أثناء ضغط أو حفظ الصور. الرجاء المحاولة مرة أخرى.");
      }
    } else {
      alert("لم يتم العثور على أي صور صالحة للتنزيل.");
    }
    setIsDownloading(false);
  };

  const downloadMotionPrompt = (sceneIndex, motionPrompt) => {
    const fileName = `motion_prompt_scene_${sceneIndex + 1}.txt`;
    const blob = new Blob([motionPrompt], { type: "text/plain;charset=utf-8" });
    window.saveAs(blob, fileName);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-100 to-blue-200 text-gray-800 p-4 sm:p-8 font-inter">
      {/* CDN links for Tailwind CSS, JSZip, and FileSaver */}
      <script src="https://cdn.tailwindcss.com"></script>
      <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap" rel="stylesheet" />

      {/* Custom Styles */}
      <style>
        {`
        .font-inter { font-family: 'Inter', sans-serif; }
        /* Modal Overlay */
        .modal-overlay {
          position: fixed;
          top: 0;
          left: 0;
          right: 0;
          bottom: 0;
          background-color: rgba(0, 0, 0, 0.6);
          display: flex;
          justify-content: center;
          align-items: center;
          z-index: 1000;
        }
        /* Modal Content */
        .modal-content {
          background-color: #ffffff;
          padding: 1.5rem;
          border-radius: 1rem;
          max-width: 90%;
          max-height: 80%;
          overflow-y: auto;
          box-shadow: 0 10px 25px rgba(0, 0, 0, 0.2);
          position: relative;
        }
        /* Modal Close Button */
        .modal-close-button {
          position: absolute;
          top: 1rem;
          right: 1rem;
          background: none;
          border: none;
          font-size: 1.5rem;
          cursor: pointer;
          color: #6b7280;
        }
        /* Editable Text Styling */
        [contentEditable="true"]:focus {
          outline: 2px solid #a78bfa; /* purple-400 */
          outline-offset: 2px;
          border-radius: 0.25rem;
        }
        `}
      </style>

      <header className="text-center mb-8">
        <h1 className="text-4xl sm:text-5xl font-extrabold text-purple-700 drop-shadow-lg flex items-center justify-center">
          <Book className="w-10 h-10 sm:w-12 sm:h-12 mr-3 text-blue-600" />
          صانع القصص الذكي
        </h1>
        <p className="text-lg sm:text-xl text-gray-600 mt-2">
          أنشئ قصصك المصورة بالذكاء الاصطناعي في دقائق!
        </p>
      </header>

      <main className="max-w-4xl mx-auto bg-white rounded-xl shadow-2xl p-6 sm:p-10">
        <div className="grid md:grid-cols-2 gap-8">
          {/* Section: Start with an Idea */}
          <div className="bg-blue-50 p-6 rounded-lg border-2 border-blue-200 shadow-inner">
            <h2 className="text-2xl font-bold text-blue-700 mb-4 flex items-center">
              <Pencil className="w-6 h-6 mr-2" /> عندي فكرة وعاوز أبدأ بيها
            </h2>
            <div className="mb-4">
              <label htmlFor="storyIdea" className="block text-gray-700 text-sm font-bold mb-2">
                فكرة القصة:
              </label>
              <textarea
                id="storyIdea"
                className="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:ring-2 focus:ring-blue-500 h-24"
                placeholder="اكتب فكرتك هنا (مثلاً: قطة صغيرة تائهة تبحث عن منزل في مدينة كبيرة)..."
                value={storyIdea}
                onChange={(e) => setStoryIdea(e.target.value)}
              ></textarea>
            </div>
            <div className="mb-4">
              <label htmlFor="numScenesIdea" className="block text-gray-700 text-sm font-bold mb-2">
                عدد المشاهد:
              </label>
              <input
                type="number"
                id="numScenesIdea"
                className="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:ring-2 focus:ring-blue-500"
                min="1"
                value={numScenes}
                onChange={(e) => setNumScenes(Math.max(1, parseInt(e.target.value)))}
              />
            </div>
            <div className="mb-6">
              <label htmlFor="imageAspectRatioIdea" className="block text-gray-700 text-sm font-bold mb-2">
                حجم الصور:
              </label>
              <select
                id="imageAspectRatioIdea"
                className="shadow border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:ring-2 focus:ring-blue-500"
                value={imageAspectRatio}
                onChange={(e) => setImageAspectRatio(e.target.value)}
              >
                <option value="16:9">16:9 أفقي (YouTube Video)</option>
                <option value="9:16">9:16 عمودي (YouTube Shorts)</option>
              </select>
            </div>
            {/* Image Generator Selection - duplicated for both sections for clarity */}
            <div className="mb-6">
              <label htmlFor="imageGeneratorIdea" className="block text-gray-700 text-sm font-bold mb-2">
                مولد الصور:
              </label>
              <select
                id="imageGeneratorIdea"
                className="shadow border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:ring-2 focus:ring-blue-500"
                value={imageGenerator}
                onChange={(e) => setImageGenerator(e.target.value)}
              >
                <option value="google-imagen">Google Imagen</option>
                <option value="openai-dall-e">OpenAI DALL-E 3</option>
              </select>
            </div>
            {imageGenerator === 'openai-dall-e' && (
              <div className="mb-6">
                <label htmlFor="openAIApiKeyIdea" className="block text-gray-700 text-sm font-bold mb-2">
                  مفتاح API الخاص بـ OpenAI:
                </label>
                <input
                  type="password"
                  id="openAIApiKeyIdea"
                  className="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="أدخل مفتاح OpenAI API الخاص بك هنا"
                  value={openAIApiKey}
                  onChange={(e) => setOpenAIApiKey(e.target.value)}
                />
              </div>
            )}
            <button
              onClick={() => generateStoryOutline('idea')}
              className="w-full bg-blue-600 hover:bg-blue-700 text-white font-bold py-3 px-4 rounded-lg focus:outline-none focus:shadow-outline transition duration-300 ease-in-out transform hover:scale-105 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center"
              // Disable if no idea, or if DALL-E selected and no key provided, or if Google Imagen selected and no Google API key provided
              disabled={isLoadingStory || !storyIdea.trim() || (imageGenerator === 'openai-dall-e' && !openAIApiKey) || (imageGenerator === 'google-imagen' && !googleApiKey)}
            >
              {isLoadingStory ? <Loader2 className="animate-spin inline-block mr-2" /> : <Book className="inline-block mr-2" />}
              توليد القصة
            </button>
          </div>

          {/* Section: Suggest for me */}
          <div className="bg-purple-50 p-6 rounded-lg border-2 border-purple-200 shadow-inner">
            <h2 className="text-2xl font-bold text-purple-700 mb-4 flex items-center">
              <Lightbulb className="w-6 h-6 mr-2" /> مش عندي فكرة، اقترحلي
            </h2>
            <div className="mb-4">
              <label htmlFor="storyType" className="block text-gray-700 text-sm font-bold mb-2">
                نوع القصة:
              </label>
              <select
                id="storyType"
                className="shadow border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:ring-2 focus:ring-purple-500"
                value={storyType}
                onChange={(e) => setStoryType(e.target.value)}
              >
                <option value="">اختر نوع القصة</option>
                <option value="قصص قطط">قصص قطط</option>
                <option value="قصص مغامرات">قصص مغامرات</option>
                <option value="قصص خيالية">قصص خيالية</option>
                <option value="قصص أطفال">قصص أطفال</option>
                <option value="قصص تعليمية">قصص تعليمية</option>
              </select>
            </div>

            {storyType === 'قصص قطط' && (
              <div className="mb-4 p-4 bg-yellow-50 rounded-lg border border-yellow-200">
                <h3 className="text-lg font-semibold text-yellow-800 mb-3">تخصيص شخصيات القطط:</h3>
                {catCharacters.map((char, index) => (
                  <div key={index} className="mb-3 p-3 border border-yellow-300 rounded-md bg-yellow-100">
                    <h4 className="font-medium text-yellow-900 mb-2">{char.name}</h4>
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                      <div>
                        <label className="block text-gray-700 text-sm mb-1">اللون:</label>
                        <select
                          className="shadow border rounded w-full py-1 px-2 text-gray-700 focus:outline-none focus:ring-2 focus:ring-yellow-500"
                          value={char.color}
                          onChange={(e) => handleCatCharacterChange(index, 'color', e.target.value)}
                        >
                          <option value="برتقالي">برتقالي</option>
                          <option value="رمادي">رمادي</option>
                          <option value="أسود">أسود</option>
                          <option value="أبيض">أبيض</option>
                          <option value="بني">بني</option>
                          <option value="ذهبي">ذهبي</option>
                          <option value="متعدد الألوان">متعدد الألوان</option>
                        </select>
                      </div>
                      <div>
                        <label className="block text-gray-700 text-sm mb-1">الحجم:</label>
                        <select
                          className="shadow border rounded w-full py-1 px-2 text-gray-700 focus:outline-none focus:ring-2 focus:ring-yellow-500"
                          value={char.size}
                          onChange={(e) => handleCatCharacterChange(index, 'size', e.target.value)}
                        >
                          <option value="صغير">صغير</option>
                          <option value="متوسط">متوسط</option>
                          <option value="كبير">كبير</option>
                        </select>
                      </div>
                      <div className="col-span-1 sm:col-span-2">
                        <label className="block text-gray-700 text-sm mb-1">النوع/السلالة:</label>
                        <select
                          className="shadow border rounded w-full py-1 px-2 text-gray-700 focus:outline-none focus:ring-2 focus:ring-yellow-500"
                          value={char.type}
                          onChange={(e) => handleCatCharacterChange(index, 'type', e.target.value)}
                        >
                          <option value="تابي">تابي</option>
                          <option value="سيامي">سيامي</option>
                          <option value="فارسي">فارسي</option>
                          <option value="مين كون">مين كون</option>
                          <option value="بنجال">بنجال</option>
                          <option value="بلدي">بلدي</option>
                          <option value="أبو الهول">أبو الهول</option>
                        </select>
                      </div>
                      <div className="col-span-1 sm:col-span-2">
                        <label className="block text-gray-700 text-sm mb-1">وصف مخصص إضافي (اختياري):</label>
                        <textarea
                          className="shadow appearance-none border rounded w-full py-1 px-2 text-gray-700 h-16 focus:outline-none focus:ring-2 focus:ring-yellow-500"
                          placeholder="مثلاً: بعيون خضراء لامعة، أو يرتدي وشاحًا أحمر صغيرًا."
                          value={char.customDescription}
                          onChange={(e) => handleCatCharacterChange(index, 'customDescription', e.target.value)}
                        ></textarea>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}

            <div className="mb-4">
              <label htmlFor="numScenesSuggest" className="block text-gray-700 text-sm font-bold mb-2">
                عدد المشاهد:
              </label>
              <input
                type="number"
                id="numScenesSuggest"
                className="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:ring-2 focus:ring-purple-500"
                min="1"
                value={numScenes}
                onChange={(e) => setNumScenes(Math.max(1, parseInt(e.target.value)))}
              />
            </div>
            <div className="mb-6">
              <label htmlFor="imageAspectRatioSuggest" className="block text-gray-700 text-sm font-bold mb-2">
                حجم الصور:
              </label>
              <select
                id="imageAspectRatioSuggest"
                className="shadow border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:ring-2 focus:ring-purple-500"
                value={imageAspectRatio}
                onChange={(e) => setImageAspectRatio(e.target.value)}
              >
                <option value="16:9">16:9 أفقي (YouTube Video)</option>
                <option value="9:16">9:16 عمودي (YouTube Shorts)</option>
              </select>
            </div>
            {/* Image Generator Selection - duplicated for both sections for clarity */}
            <div className="mb-6">
              <label htmlFor="imageGeneratorSuggest" className="block text-gray-700 text-sm font-bold mb-2">
                مولد الصور:
              </label>
              <select
                id="imageGeneratorSuggest"
                className="shadow border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:ring-2 focus:ring-purple-500"
                value={imageGenerator}
                onChange={(e) => setImageGenerator(e.target.value)}
              >
                <option value="google-imagen">Google Imagen</option>
                <option value="openai-dall-e">OpenAI DALL-E 3</option>
              </select>
            </div>
            {imageGenerator === 'openai-dall-e' && (
              <div className="mb-6">
                <label htmlFor="openAIApiKeySuggest" className="block text-gray-700 text-sm font-bold mb-2">
                  مفتاح API الخاص بـ OpenAI:
                </label>
                <input
                  type="password"
                  id="openAIApiKeySuggest"
                  className="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:ring-2 focus:ring-purple-500"
                  placeholder="أدخل مفتاح OpenAI API الخاص بك هنا"
                  value={openAIApiKey}
                  onChange={(e) => setOpenAIApiKey(e.target.value)}
                />
              </div>
            )}
            <button
              onClick={() => generateStoryOutline('suggest')}
              className="w-full bg-purple-600 hover:bg-purple-700 text-white font-bold py-3 px-4 rounded-lg focus:outline-none focus:shadow-outline transition duration-300 ease-in-out transform hover:scale-105 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center"
              // Disable if no story type selected, or if DALL-E selected and no key provided, or if Google Imagen selected and no Google API key provided
              disabled={isLoadingStory || !storyType || (imageGenerator === 'openai-dall-e' && !openAIApiKey) || (imageGenerator === 'google-imagen' && !googleApiKey)}
            >
              {isLoadingStory ? <Loader2 className="animate-spin inline-block mr-2" /> : <Lightbulb className="inline-block mr-2" />}
              اقترح قصة
            </button>
          </div>
        </div>

        {/* Loading Indicator for Story Generation */}
        {isLoadingStory && (
          <div className="text-center mt-8 text-xl text-gray-600 p-4 bg-gray-100 rounded-lg shadow-md">
            <Loader2 className="animate-spin inline-block w-8 h-8 mr-3 text-blue-500" />
            جاري توليد القصة والمشاهد... قد يستغرق الأمر بضع لحظات.
          </div>
        )}

        {/* Generated Story Scenes */}
        {currentStory && (
          <div className="mt-10 border-t-2 border-gray-200 pt-8">
            <h2 className="text-3xl font-bold text-gray-800 mb-6 text-center">القصة المولدة</h2>

            {/* Global Download Button */}
            <button
              onClick={handleDownloadAllImages}
              className="mb-6 w-full bg-green-600 hover:bg-green-700 text-white font-bold py-3 px-4 rounded-lg focus:outline-none focus:shadow-outline transition duration-300 ease-in-out transform hover:scale-105 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center"
              disabled={!isDownloadReady || isDownloading || Object.values(generatingImages).some(val => val)}
            >
              {isDownloading ? <Loader2 className="animate-spin inline-block mr-2" /> : <Download className="inline-block mr-2" />}
              {isDownloading ? 'جاري التنزيل...' : 'تنزيل جميع الصور (ZIP)'}
            </button>

            <div className="space-y-8">
              {currentStory.story.map((scene, index) => (
                <div key={index} className="bg-white rounded-lg shadow-lg p-6 border border-gray-200">
                  <h3
                    className="text-2xl font-semibold text-blue-700 mb-3 cursor-pointer hover:text-blue-800"
                    contentEditable
                    onBlur={(e) => handleSceneTextChange(index, 'title', e.target.textContent)}
                    suppressContentEditableWarning={true}
                  >
                    المشهد {index + 1}: {scene.title}
                  </h3>
                  <p
                    className="text-gray-700 mb-4 text-lg leading-relaxed cursor-pointer hover:bg-gray-50 p-1 rounded"
                    contentEditable
                    onBlur={(e) => handleSceneTextChange(index, 'summary_ar', e.target.textContent)}
                    suppressContentEditableWarning={true}
                  >
                    {scene.summary_ar}
                  </p>

                  {/* Image display. Use object-contain for Imagen, or object-cover if DALL-E produces native size perfectly */}
                  <div className={`relative bg-gray-100 rounded-lg overflow-hidden mb-4
                    ${imageAspectRatio === '16:9' ? 'aspect-video w-full' : 'aspect-[9/16] w-full max-w-sm mx-auto'}`}>
                    {scene.image_url ? (
                      // Use object-contain for Imagen output (which might be square and padded)
                      // Use object-cover for DALL-E output (which should match aspect ratio natively)
                      <img
                        src={scene.image_url}
                        alt={`Scene ${index + 1}`}
                        className={`w-full h-full ${imageGenerator === 'openai-dall-e' ? 'object-cover' : 'object-contain'}`}
                      />
                    ) : (
                      <div className="absolute inset-0 flex flex-col items-center justify-center text-center text-gray-500 p-4">
                        {generatingImages[index] ? (
                          <>
                            <Loader2 className="animate-spin inline-block w-8 h-8 text-blue-500" />
                            <p className="mt-2">جاري توليد الصورة...</p>
                          </>
                        ) : imageGenerationErrors[index] ? (
                          <>
                            <p className="text-red-500 mb-2">فشل توليد الصورة:</p>
                            <p className="text-sm text-red-700">{imageGenerationErrors[index]}</p>
                            <button
                               onClick={() => generateImageForScene(index, scene.image_prompt, 0)} // Manual retry
                               className="mt-2 px-3 py-1 bg-red-100 text-red-800 rounded-md hover:bg-red-200 text-sm"
                             >
                               إعادة محاولة
                             </button>
                          </>
                        ) : (
                          <p>جاري انتظار الصورة...</p>
                        )}
                      </div>
                    )}
                  </div>

                  <div className="flex flex-wrap gap-3 justify-center mt-4">
                    <button
                      onClick={() => setShowPromptModal({ index, prompt: scene.image_prompt })}
                      className="bg-gray-200 hover:bg-gray-300 text-gray-800 font-bold py-2 px-4 rounded-lg text-sm flex items-center transition duration-300"
                    >
                      <Eye className="w-4 h-4 mr-2" />
                      عرض/تعديل برومبت الصورة
                    </button>
                    <button
                      onClick={() => generateImageForScene(index, scene.image_prompt, 0)} // Reset retry count for manual click
                      className="bg-blue-500 hover:bg-blue-600 text-white font-bold py-2 px-4 rounded-lg text-sm flex items-center transition duration-300 disabled:opacity-50 disabled:cursor-not-allowed"
                      // Disable if generating, or if DALL-E selected and no key provided, or if Google Imagen selected and no Google API key provided
                      disabled={generatingImages[index] || (imageGenerator === 'openai-dall-e' && !openAIApiKey) || (imageGenerator === 'google-imagen' && !googleApiKey)}
                    >
                      {generatingImages[index] ? <Loader2 className="animate-spin inline-block mr-2" /> : <Pencil className="w-4 h-4 mr-2" />}
                      إعادة توليد الصورة
                    </button>
                    <button
                      onClick={() => setShowMotionPromptModal({ index, prompt: scene.motion_prompt })}
                      className="bg-gray-200 hover:bg-gray-300 text-gray-800 font-bold py-2 px-4 rounded-lg text-sm flex items-center transition duration-300"
                    >
                      <Eye className="w-4 h-4 mr-2" />
                      عرض برومبت الحركة
                    </button>
                    <button
                      onClick={() => downloadMotionPrompt(index, scene.motion_prompt)}
                      className="bg-green-500 hover:bg-green-600 text-white font-bold py-2 px-4 rounded-lg text-sm flex items-center transition duration-300"
                    >
                      <Download className="w-4 h-4 mr-2" />
                      تحميل برومبت الحركة (txt)
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </main>

      {/* Prompt Modal */}
      {showPromptModal && (
        <div className="modal-overlay">
          <div className="modal-content w-full max-w-2xl">
            <button
              onClick={() => { setShowPromptModal(null); setEditPromptMode(null); }}
              className="modal-close-button"
            >
              ×
            </button>
            <h3 className="text-xl font-bold mb-4 text-gray-800">برومبت الصورة للمشهد {showPromptModal.index + 1}</h3>
            {editPromptMode === showPromptModal.index ? (
              <textarea
                className="w-full p-3 border border-gray-300 rounded-lg focus:ring-purple-500 focus:border-purple-500 transition-all duration-200 h-40 resize-y text-gray-800"
                value={currentStory.story[showPromptModal.index].image_prompt}
                onChange={(e) => handlePromptChange(showPromptModal.index, 'image_prompt', e.target.value)}
              ></textarea>
            ) : (
              <p className="bg-gray-100 p-3 rounded-lg text-gray-700 whitespace-pre-wrap">
                {showPromptModal.prompt}
              </p>
            )}
            <div className="flex justify-end gap-3 mt-4">
              {editPromptMode === showPromptModal.index ? (
                <>
                  <button
                    onClick={() => {
                      const updatedPrompt = currentStory.story[showPromptModal.index].image_prompt;
                      setEditPromptMode(null);
                      generateImageForScene(showPromptModal.index, updatedPrompt, 0); // Reset retry count for manual click
                      setShowPromptModal(null);
                    }}
                    className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center"
                    disabled={generatingImages[showPromptModal.index] || (imageGenerator === 'openai-dall-e' && !openAIApiKey) || (imageGenerator === 'google-imagen' && !googleApiKey)}
                  >
                    {generatingImages[showPromptModal.index] ? <Loader2 className="animate-spin inline-block mr-2" /> : null}
                    حفظ وتحديث الصورة
                  </button>
                  <button
                    onClick={() => {
                      setShowPromptModal(null);
                      setEditPromptMode(null);
                    }}
                    className="px-4 py-2 bg-gray-300 text-gray-800 rounded-lg hover:bg-gray-400 transition-colors"
                  >
                    إلغاء
                  </button>
                </>
              ) : (
                <>
                  <button
                    onClick={() => setEditPromptMode(showPromptModal.index)}
                    className="px-4 py-2 bg-yellow-500 text-white rounded-lg hover:bg-yellow-600 transition-colors flex items-center"
                  >
                    <Pencil className="w-4 h-4 mr-2" />
                    تعديل
                  </button>
                  <button
                    onClick={() => setShowPromptModal(null)}
                    className="px-4 py-2 bg-gray-300 text-gray-800 rounded-lg hover:bg-gray-400 transition-colors"
                  >
                    إغلاق
                  </button>
                </>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Motion Prompt Modal */}
      {showMotionPromptModal && (
        <div className="modal-overlay">
          <div className="modal-content w-full max-w-2xl">
            <button
              onClick={() => setShowMotionPromptModal(null)}
              className="modal-close-button"
            >
              ×
            </button>
            <h3 className="text-xl font-bold mb-4 text-gray-800">برومبت الحركة للمشهد {showMotionPromptModal.index + 1}</h3>
            <p className="bg-gray-100 p-3 rounded-lg text-gray-700 whitespace-pre-wrap">
              {showMotionPromptModal.prompt}
            </p>
            <div className="flex justify-end gap-3 mt-4">
              <button
                onClick={() => downloadMotionPrompt(showMotionPromptModal.index, showMotionPromptModal.prompt)}
                className="bg-green-500 hover:bg-green-600 text-white font-bold py-2 px-4 rounded-lg text-sm flex items-center transition duration-300"
              >
                <Download className="w-4 h-4 mr-2" />
                تحميل (txt)
              </button>
              <button
                onClick={() => setShowMotionPromptModal(null)}
                className="bg-gray-300 hover:bg-gray-400 text-gray-800 rounded-lg font-bold py-2 px-4 transition duration-300"
              >
                إغلاق
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default App;
