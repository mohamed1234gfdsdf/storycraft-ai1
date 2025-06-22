import { useState, useEffect, useRef } from 'react';
import { initializeApp } from 'firebase/app';
import { getAuth, signInAnonymously, signInWithCustomToken, onAuthStateChanged } from 'firebase/auth';
import { getFirestore, doc, setDoc, getDoc, collection, onSnapshot } from 'firebase/firestore';

// Helper function to decode HTML entities (often returned by LLMs)
function decodeHtmlEntities(text) {
    const textarea = document.createElement('textarea');
    textarea.innerHTML = text;
    return textarea.value;
}

function App() {
    const [storyInput, setStoryInput] = useState('');
    const [numScenes, setNumScenes] = useState(6);
    const [scenes, setScenes] = useState([]);
    const [loadingLLM, setLoadingLLM] = useState(false);
    const [loadingImages, setLoadingImages] = useState({});
    const [imageAspectRatio, setImageAspectRatio] = useState('9:16'); // Default to vertical
    const [error, setError] = useState('');
    const [db, setDb] = useState(null);
    const [auth, setAuth] = useState(null);
    const [userId, setUserId] = useState(null);
    const downloadLinkRef = useRef(null); // Ref for triggering download
    const isScriptLoaded = useRef({ jszip: false, filesaver: false });

    // Load JSZip and FileSaver from CDN
    useEffect(() => {
        const loadScript = (src, id, onComplete) => {
            if (document.getElementById(id)) {
                onComplete();
                return;
            }
            const script = document.createElement('script');
            script.src = src;
            script.id = id;
            script.onload = () => {
                onComplete();
                console.log(`${id} script loaded`);
            };
            script.onerror = () => {
                console.error(`Failed to load script: ${src}`);
                setError(`Failed to load external library: ${id}`);
            };
            document.head.appendChild(script);
        };

        let jszipLoaded = false;
        let filesaverLoaded = false;

        const checkBothLoaded = () => {
            if (jszipLoaded && filesaverLoaded) {
                isScriptLoaded.current.jszip = true;
                isScriptLoaded.current.filesaver = true;
                console.log("All external scripts loaded.");
            }
        };

        loadScript('https://cdnjs.cloudflare.com/ajax/libs/jszip/3.10.1/jszip.min.js', 'jszip-script', () => {
            jszipLoaded = true;
            checkBothLoaded();
        });
        loadScript('https://cdnjs.cloudflare.com/ajax/libs/FileSaver.js/2.0.5/FileSaver.min.js', 'filesaver-script', () => {
            filesaverLoaded = true;
            checkBothLoaded();
        });

    }, []);


    // Firebase Initialization and Auth
    useEffect(() => {
        try {
            const firebaseConfig = typeof __firebase_config !== 'undefined' ? JSON.parse(__firebase_config) : null;
            if (firebaseConfig) {
                const app = initializeApp(firebaseConfig);
                const firestoreDb = getFirestore(app);
                const firebaseAuth = getAuth(app);
                setDb(firestoreDb);
                setAuth(firebaseAuth);

                const unsub = onAuthStateChanged(firebaseAuth, async (user) => {
                    if (user) {
                        setUserId(user.uid);
                        console.log("Firebase Auth Ready. User ID:", user.uid);
                    } else {
                        // Sign in anonymously if no user is present
                        const initialAuthToken = typeof __initial_auth_token !== 'undefined' ? __initial_auth_token : null;
                        if (initialAuthToken) {
                            await signInWithCustomToken(firebaseAuth, initialAuthToken);
                        } else {
                            await signInAnonymously(firebaseAuth);
                        }
                    }
                });
                return () => unsub(); // Cleanup on unmount
            } else {
                console.warn("Firebase config not found. Running without Firebase.");
                setUserId(crypto.randomUUID()); // Generate a random ID for unauthenticated use
            }
        } catch (e) {
            console.error("Firebase initialization failed:", e);
            setError("فشل تهيئة Firebase. قد لا تعمل بعض الميزات.");
            setUserId(crypto.randomUUID()); // Fallback to random ID
        }
    }, []);

    // Function to generate text (scene prompts) using Gemini API
    const generateTextPrompts = async () => {
        if (!storyInput.trim()) {
            setError('الرجاء إدخال وصف للقصة.');
            return;
        }
        setError('');
        setLoadingLLM(true);
        setScenes([]); // Clear previous scenes

        const chatHistory = [];
        const prompt = `
            أنا أرغب في إنشاء قصة قصيرة تتكون من ${numScenes} مشاهد. القصة كالتالي:
            "${storyInput}"

            الرجاء توليد ${numScenes} مشاهد تفصيلية لهذه القصة. لكل مشهد، قدم:
            1.  **عنوان المشهد (Scene Title):** عنوان قصير ومختصر.
            2.  **مطالبة الصورة (Image Prompt):** وصف تفصيلي للغاية للصورة المطلوبة، مصمم لتوليد صورة واقعية مفرطة بجودة بيكسار، مع زوايا تصوير احترافية. ركز على التفاصيل الدقيقة لوجوه القطط (عيون العنبر الواسعة للقطة الأم، عيون خضراء واقعية للقطة الصغيرة، فراء طبيعي، شوارب، أنوف وردية صغيرة، حواجب محددة جيدًا).
                **مهم للغاية للصور:**
                * **لقطة واسعة للغاية (EXTREMELY WIDE SHOT):** تأكد أن جميع العناصر مرئية بوضوح مع مساحة واسعة حولها للرسوم المتحركة. تجنب اللقطات المقربة (close-ups) ما لم يُطلب ذلك صراحة. يجب أن يكون سياق المشهد الكامل مرئيًا.
                * **الوضوح والتفاصيل:** يجب أن تكون جميع العناصر المذكورة واضحة وتفصيلية.
                * **الأسلوب:** واقعي مفرط، بجودة بيكسار سينمائية، ألوان ضوء النهار نظيفة (إلا إذا كان المشهد ليلي)، بدون مبالغة كرتونية.
                * **أبعاد الصورة:** سيتم ضبطها لاحقًا بناءً على اختيار المستخدم (9:16 أو 16:9 أو 1:1)، لذا ركز على المحتوى البصري.
                * **تفاصيل القطط:** القطة الأم: قطة برتقالية سمينة عصرية بالغة ذات وجه واقعي للغاية، عيون عنبر واسعة، نسيج فراء طبيعي بخطوط برتقالية وكريمية ناعمة، أنف وردي صغير، شوارب بيضاء نظيفة، وحواجب محددة جيدًا. ترتدي مئزرًا أنيقًا بيج فاتح. القطة الصغيرة: قطة صغيرة لطيفة للغاية ذات فراء رمادي فاتح، عيون خضراء واقعية، فراء قصير ناعم، أنف وردي صغير، ووجه دائري.
            3.  **مطالبة الحركة (Motion Prompt):** وصف موجز للحركة المقترحة في هذا المشهد، مناسب للرسوم المتحركة.

            الرجاء إخراج الإجابة بصيغة JSON فقط، كصفيف من الكائنات، حيث يحتوي كل كائن على المفاتيح التالية: sceneTitle, imagePrompt, motionPrompt.
        `;

        chatHistory.push({ role: "user", parts: [{ text: prompt }] });
        const payload = {
            contents: chatHistory,
            generationConfig: {
                responseMimeType: "application/json",
                responseSchema: {
                    type: "ARRAY",
                    items: {
                        type: "OBJECT",
                        properties: {
                            "sceneTitle": { "type": "STRING" },
                            "imagePrompt": { "type": "STRING" },
                            "motionPrompt": { "type": "STRING" }
                        },
                        "propertyOrdering": ["sceneTitle", "imagePrompt", "motionPrompt"]
                    }
                }
            }
        };

        const apiKey = "";
        const apiUrl = `https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key=${apiKey}`;

        try {
            const response = await fetch(apiUrl, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            const result = await response.json();

            if (result.candidates && result.candidates.length > 0 &&
                result.candidates[0].content && result.candidates[0].content.parts &&
                result.candidates[0].content.parts.length > 0) {
                const jsonText = result.candidates[0].content.parts[0].text;
                const parsedScenes = JSON.parse(jsonText);

                // Add default image URL and loading state for each scene
                const initialScenes = parsedScenes.map((scene, index) => ({
                    ...scene,
                    id: `scene-${index}-${Date.now()}`, // Unique ID for each scene
                    imageUrl: null,
                    loading: false
                }));
                setScenes(initialScenes);
                // Automatically generate images after text prompts are ready
                initialScenes.forEach(scene => generateImageForScene(scene.id, scene.imagePrompt));

            } else {
                setError('فشل في توليد المشاهد. لا توجد نتائج صالحة من النموذج.');
                console.error('LLM response structure unexpected:', result);
            }
        } catch (e) {
            setError(`حدث خطأ أثناء توليد المشاهد: ${e.message}`);
            console.error('Error generating text prompts:', e);
        } finally {
            setLoadingLLM(false);
        }
    };

    // Function to generate image using Imagen API
    const generateImageForScene = async (sceneId, imagePrompt) => {
        setLoadingImages(prev => ({ ...prev, [sceneId]: true }));
        setError('');

        let finalPrompt = imagePrompt;
        if (imageAspectRatio === '9:16') {
            finalPrompt += " (أبعاد عمودية 9:16)";
        } else if (imageAspectRatio === '16:9') {
            finalPrompt += " (أبعاد أفقية 16:9)";
        } else if (imageAspectRatio === '1:1') {
            finalPrompt += " (أبعاد مربعة 1:1)";
        }

        // Add more explicit instructions to avoid zooming
        finalPrompt += " EXTREMELY WIDE SHOT. AVOID CLOSE-UPS. Ensure full scene context is visible with generous space around elements.";


        const payload = { instances: { prompt: finalPrompt }, parameters: { "sampleCount": 1 } };
        const apiKey = "";
        const apiUrl = `https://generativelanguage.googleapis.com/v1beta/models/imagen-3.0-generate-002:predict?key=${apiKey}`;

        try {
            const response = await fetch(apiUrl, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            const result = await response.json();

            if (result.predictions && result.predictions.length > 0 && result.predictions[0].bytesBase64Encoded) {
                const imageUrl = `data:image/png;base64,${result.predictions[0].bytesBase64Encoded}`;
                setScenes(prevScenes =>
                    prevScenes.map(s => (s.id === sceneId ? { ...s, imageUrl: imageUrl } : s))
                );
            } else {
                console.error(`فشل في توليد الصورة للمشهد ${sceneId}: لا توجد نتائج صالحة.`, result);
                setError(`فشل في توليد الصورة للمشهد ${sceneId}.`);
                setScenes(prevScenes =>
                    prevScenes.map(s => (s.id === sceneId ? { ...s, imageUrl: 'https://placehold.co/200x200/FF0000/FFFFFF?text=Error' } : s))
                );
            }
        } catch (e) {
            console.error(`خطأ في توليد الصورة للمشهد ${sceneId}:`, e);
            setError(`حدث خطأ أثناء توليد الصورة للمشهد ${sceneId}: ${e.message}`);
            setScenes(prevScenes =>
                prevScenes.map(s => (s.id === sceneId ? { ...s, imageUrl: 'https://placehold.co/200x200/FF0000/FFFFFF?text=Error' } : s))
            );
        } finally {
            setLoadingImages(prev => ({ ...prev, [sceneId]: false }));
        }
    };

    // Update scene properties
    const handleSceneChange = (id, field, value) => {
        setScenes(prevScenes =>
            prevScenes.map(scene =>
                scene.id === id ? { ...scene, [field]: value } : scene
            )
        );
    };

    // Add a new scene
    const addScene = () => {
        const newSceneId = `scene-${scenes.length}-${Date.now()}`;
        setScenes(prevScenes => [
            ...prevScenes,
            {
                id: newSceneId,
                sceneTitle: 'مشهد جديد',
                imagePrompt: 'وصف لمشهد جديد (الرجاء التعديل لتوليد صورة).',
                motionPrompt: 'حركة المشهد الجديد.',
                imageUrl: null,
                loading: false
            }
        ]);
    };

    // Delete a scene
    const deleteScene = (id) => {
        setScenes(prevScenes => prevScenes.filter(scene => scene.id !== id));
    };

    // Re-generate image for an edited prompt
    const regenerateImage = (sceneId) => {
        const sceneToRegenerate = scenes.find(s => s.id === sceneId);
        if (sceneToRegenerate) {
            generateImageForScene(sceneId, sceneToRegenerate.imagePrompt);
        }
    };

    // Download all images as a zip file
    const downloadAllImages = async () => {
        if (!isScriptLoaded.current.jszip || !isScriptLoaded.current.filesaver) {
            setError('جاري تحميل مكتبات التنزيل. الرجاء المحاولة مرة أخرى بعد قليل.');
            return;
        }
        if (scenes.length === 0 || scenes.every(s => !s.imageUrl)) {
            setError('لا توجد صور لتنزيلها.');
            return;
        }

        const zip = new window.JSZip(); // Use window.JSZip
        let loadedImagesCount = 0;
        const totalImages = scenes.filter(s => s.imageUrl).length;

        if (totalImages === 0) {
            setError('لا توجد صور متاحة للتنزيل.');
            return;
        }

        setError('جارٍ إعداد الصور للتنزيل...');

        for (const scene of scenes) {
            if (scene.imageUrl) {
                try {
                    const response = await fetch(scene.imageUrl);
                    const blob = await response.blob();
                    zip.file(`${decodeHtmlEntities(scene.sceneTitle)}.png`, blob);
                    loadedImagesCount++;
                } catch (e) {
                    console.error(`فشل تحميل الصورة للمشهد ${scene.sceneTitle}:`, e);
                }
            }
        }

        if (loadedImagesCount > 0) {
            zip.generateAsync({ type: 'blob' })
                .then(function (content) {
                    window.saveAs(content, 'story_images.zip'); // Use window.saveAs
                    setError('');
                })
                .catch(e => {
                    setError(`فشل في إنشاء ملف ZIP: ${e.message}`);
                    console.error('Error zipping files:', e);
                });
        } else {
            setError('فشل في تحميل أي صور لتضمينها في ملف ZIP.');
        }
    };

    return (
        <div className="min-h-screen bg-gradient-to-br from-indigo-50 to-purple-100 p-6 font-inter text-gray-800">
            <div className="max-w-6xl mx-auto bg-white p-8 rounded-3xl shadow-xl border border-gray-200">
                <h1 className="text-4xl font-extrabold text-center text-purple-700 mb-8">
                    صانع القصص المرئية
                </h1>

                {/* Story Input Form */}
                <div className="mb-8 p-6 bg-purple-50 rounded-2xl border border-purple-200 shadow-inner">
                    <h2 className="text-2xl font-bold text-purple-600 mb-4">أخبرني قصتك!</h2>
                    <div className="mb-4">
                        <label htmlFor="storyInput" className="block text-lg font-medium text-gray-700 mb-2">
                            وصف القصة (مثال: قطة أم وبنتها اصطادتا سمكة وطلعت قرش):
                        </label>
                        <textarea
                            id="storyInput"
                            className="w-full p-3 border border-purple-300 rounded-lg shadow-sm focus:ring-purple-500 focus:border-purple-500 transition duration-200"
                            rows="4"
                            value={storyInput}
                            onChange={(e) => setStoryInput(e.target.value)}
                            placeholder="أدخل فكرة قصتك هنا..."
                        ></textarea>
                    </div>
                    <div className="mb-6 flex flex-col sm:flex-row items-center gap-4">
                        <div className="w-full sm:w-1/2">
                            <label htmlFor="numScenes" className="block text-lg font-medium text-gray-700 mb-2">
                                عدد المشاهد:
                            </label>
                            <input
                                id="numScenes"
                                type="number"
                                className="w-full p-3 border border-purple-300 rounded-lg shadow-sm focus:ring-purple-500 focus:border-purple-500 transition duration-200"
                                value={numScenes}
                                onChange={(e) => setNumScenes(Math.max(1, parseInt(e.target.value)))}
                                min="1"
                            />
                        </div>
                        <div className="w-full sm:w-1/2">
                            <label className="block text-lg font-medium text-gray-700 mb-2">
                                حجم الصورة:
                            </label>
                            <div className="flex space-x-4">
                                <label className="inline-flex items-center">
                                    <input
                                        type="radio"
                                        className="form-radio text-purple-600"
                                        name="imageRatio"
                                        value="9:16"
                                        checked={imageAspectRatio === '9:16'}
                                        onChange={(e) => setImageAspectRatio(e.target.value)}
                                    />
                                    <span className="ml-2 text-gray-700">عمودي (9:16)</span>
                                </label>
                                <label className="inline-flex items-center">
                                    <input
                                        type="radio"
                                        className="form-radio text-purple-600"
                                        name="imageRatio"
                                        value="16:9"
                                        checked={imageAspectRatio === '16:9'}
                                        onChange={(e) => setImageAspectRatio(e.target.value)}
                                    />
                                    <span className="ml-2 text-gray-700">أفقي (16:9)</span>
                                </label>
                                <label className="inline-flex items-center">
                                    <input
                                        type="radio"
                                        className="form-radio text-purple-600"
                                        name="imageRatio"
                                        value="1:1"
                                        checked={imageAspectRatio === '1:1'}
                                        onChange={(e) => setImageAspectRatio(e.target.value)}
                                    />
                                    <span className="ml-2 text-gray-700">مربع (1:1)</span>
                                </label>
                            </div>
                        </div>
                    </div>
                    <button
                        onClick={generateTextPrompts}
                        className="w-full bg-purple-600 text-white py-3 px-6 rounded-full font-semibold text-lg hover:bg-purple-700 transition duration-300 transform hover:scale-105 shadow-lg"
                        disabled={loadingLLM}
                    >
                        {loadingLLM ? (
                            <div className="flex items-center justify-center">
                                <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                                </svg>
                                جاري توليد المشاهد...
                            </div>
                        ) : (
                            'توليد المشاهد والتحقق'
                        )}
                    </button>
                    {error && <p className="text-red-600 mt-4 text-center">{error}</p>}
                </div>

                {/* Scenes Display */}
                {scenes.length > 0 && (
                    <div className="mt-10">
                        <div className="flex justify-between items-center mb-6">
                            <h2 className="text-3xl font-bold text-purple-700">مشاهد القصة</h2>
                            <button
                                onClick={downloadAllImages}
                                className="bg-green-500 text-white py-2 px-4 rounded-full font-semibold hover:bg-green-600 transition duration-300 transform hover:scale-105 shadow-md"
                            >
                                تحميل كل الصور
                            </button>
                        </div>
                        <div className="space-y-10">
                            {scenes.map((scene, index) => (
                                <div key={scene.id} className="p-6 bg-white rounded-2xl shadow-xl border border-blue-200 transition-all duration-300 hover:shadow-2xl">
                                    <div className="flex justify-between items-center mb-4">
                                        <h3 className="text-2xl font-bold text-blue-700">
                                            🎬 المشهد {index + 1}:
                                            <input
                                                type="text"
                                                className="ml-2 p-1 border border-blue-300 rounded-md w-auto focus:ring-blue-500 focus:border-blue-500"
                                                value={decodeHtmlEntities(scene.sceneTitle)}
                                                onChange={(e) => handleSceneChange(scene.id, 'sceneTitle', e.target.value)}
                                            />
                                        </h3>
                                        <button
                                            onClick={() => deleteScene(scene.id)}
                                            className="bg-red-500 text-white p-2 rounded-full hover:bg-red-600 transition duration-300 transform hover:scale-105 shadow-md"
                                            title="حذف المشهد"
                                        >
                                            <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                                                <path fillRule="evenodd" d="M9 2a1 1 0 00-.894.553L7.382 4H4a1 1 0 000 2v10a2 2 0 002 2h8a2 2 0 002-2V6a1 1 0 100-2h-3.382l-.724-1.447A1 1 0 0011 2H9zM7 8a1 1 0 011-1h4a1 1 0 110 2H8a1 1 0 01-1-1zm2 3a1 1 0 00-1 1v4a1 1 0 002 0v-4a1 1 0 00-1-1z" clipRule="evenodd" />
                                            </svg>
                                        </button>
                                    </div>

                                    <div className="mb-4">
                                        <label htmlFor={`image-prompt-${scene.id}`} className="block text-lg font-medium text-gray-700 mb-2">
                                            📸 Prompt:
                                        </label>
                                        <textarea
                                            id={`image-prompt-${scene.id}`}
                                            className="w-full p-3 border border-gray-300 rounded-lg shadow-sm focus:ring-blue-500 focus:border-blue-500 transition duration-200"
                                            rows="8"
                                            value={decodeHtmlEntities(scene.imagePrompt)}
                                            onChange={(e) => handleSceneChange(scene.id, 'imagePrompt', e.target.value)}
                                        ></textarea>
                                        <button
                                            onClick={() => regenerateImage(scene.id)}
                                            className="mt-3 bg-blue-500 text-white py-2 px-4 rounded-full font-semibold hover:bg-blue-600 transition duration-300 transform hover:scale-105 shadow-md"
                                            disabled={loadingImages[scene.id]}
                                        >
                                            {loadingImages[scene.id] ? (
                                                <div className="flex items-center justify-center">
                                                    <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                                                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                                                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                                                    </svg>
                                                    جاري إعادة توليد الصورة...
                                                </div>
                                            ) : (
                                                'إعادة توليد الصورة'
                                            )}
                                        </button>
                                    </div>

                                    <div className="mb-4">
                                        <label htmlFor={`motion-prompt-${scene.id}`} className="block text-lg font-medium text-gray-700 mb-2">
                                            ✨ Motion Prompt:
                                        </label>
                                        <textarea
                                            id={`motion-prompt-${scene.id}`}
                                            className="w-full p-3 border border-gray-300 rounded-lg bg-gray-50 shadow-sm"
                                            rows="3"
                                            value={decodeHtmlEntities(scene.motionPrompt)}
                                            readOnly // Motion prompt is not directly editable by user, generated by LLM
                                        ></textarea>
                                    </div>

                                    {scene.imageUrl ? (
                                        <div className="mt-4 flex justify-center">
                                            <img
                                                src={scene.imageUrl}
                                                alt={`Scene ${index + 1}`}
                                                className="rounded-xl shadow-lg border border-gray-200 max-w-full h-auto"
                                                style={{
                                                    maxWidth: imageAspectRatio === '9:16' ? '300px' : '600px', // Adjust max width for display
                                                    maxHeight: imageAspectRatio === '9:16' ? '600px' : '300px',
                                                    width: 'auto',
                                                    height: 'auto'
                                                }}
                                                onError={(e) => { e.target.onerror = null; e.target.src = 'https://placehold.co/200x200/FF0000/FFFFFF?text=Image+Load+Error'; }}
                                            />
                                        </div>
                                    ) : (
                                        <div className="mt-4 flex justify-center items-center h-48 bg-gray-100 rounded-xl border border-dashed border-gray-300 text-gray-500">
                                            {loadingImages[scene.id] ? (
                                                <div className="flex items-center">
                                                    <svg className="animate-spin -ml-1 mr-3 h-8 w-8 text-purple-500" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                                                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                                                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                                                    </svg>
                                                    جاري توليد الصورة...
                                                </div>
                                            ) : (
                                                'لا توجد صورة لهذا المشهد بعد.'
                                            )}
                                        </div>
                                    )}
                                </div>
                            ))}
                            <button
                                onClick={addScene}
                                className="w-full bg-indigo-500 text-white py-3 px-6 rounded-full font-semibold text-lg hover:bg-indigo-600 transition duration-300 transform hover:scale-105 shadow-lg flex items-center justify-center mt-8"
                            >
                                <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
                                    <path strokeLinecap="round" strokeLinejoin="round" d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
                                </svg>
                                إضافة مشهد جديد
                            </button>
                        </div>
                    </div>
                )}
            </div>
            {/* Hidden download link */}
            <a ref={downloadLinkRef} style={{ display: 'none' }} />
        </div>
    );
}

export default App;
