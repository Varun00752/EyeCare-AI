import os
import uuid
import numpy as np
import cv2

LABELS = ["No DR", "Mild", "Moderate", "Severe", "Proliferative DR"]

GRADE_ADVICE = {
    0: "No signs detected. Repeat screening every 12 months.",
    1: "Mild changes. Control blood sugar, re-screen in 6-12 months.",
    2: "Moderate. Consult an ophthalmologist within 1-3 months.",
    3: "Severe. Consult an ophthalmologist urgently.",
    4: "Proliferative. Seek immediate specialist care."
}

_MODEL = None
_MODEL_LOADED = False

def load_model_once():
    """
    Lazy-load the EfficientNet-B0 model (ml/dr_model.keras).
    If missing or load fails, gracefully fall back to demo mode.
    """
    global _MODEL, _MODEL_LOADED
    if _MODEL_LOADED:
        return _MODEL

    model_path = os.path.join(os.path.dirname(__file__), "dr_model.keras")
    if os.path.exists(model_path):
        try:
            import tensorflow as tf
            # Suppress oneDNN / verbose info
            os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"
            _MODEL = tf.keras.models.load_model(model_path)
            print(f"[ML Module] Successfully loaded real model from {model_path}")
        except Exception as e:
            print(f"[ML Module] Warning: Failed to load model file ({e}). Falling back to DEMO MODE.")
            _MODEL = None
    else:
        print("[ML Module] dr_model.keras not found. Running in DEMO MODE.")
        _MODEL = None

    _MODEL_LOADED = True
    return _MODEL


def is_demo_mode():
    """Returns True if running in fallback demo mode (i.e. model not loaded)."""
    return load_model_once() is None


def validate_image(path):
    """
    Validate input image format, readable status, and dimensions.
    Returns (cv2_image, warning_message).
    """
    if not os.path.exists(path):
        raise ValueError("Image file not found.")

    img = cv2.imread(path)
    if img is None:
        raise ValueError("File is not a valid or readable image.")

    h, w = img.shape[:2]
    if h < 100 or w < 100:
        raise ValueError(f"Image too small ({w}x{h}). Minimum size required is 100x100 pixels.")

    # Warn if image doesn't appear to be a fundus photo (fundus typically has strong red/orange dominance)
    warning = None
    r_mean = np.mean(img[:, :, 2])
    g_mean = np.mean(img[:, :, 1])
    b_mean = np.mean(img[:, :, 0])
    if r_mean < 35 or (r_mean < g_mean and r_mean < b_mean):
        warning = "The uploaded image has low retinal illumination or does not look like a typical fundus photograph. Results may be inaccurate."

    return img, warning


def crop_black_borders(img, tol=10):
    """Crop surrounding black borders common in fundus photography."""
    if len(img.shape) == 2:
        mask = img > tol
        return img[np.ix_(mask.any(1), mask.any(0))]
    
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    mask = gray > tol
    
    if not mask.any():
        return img

    check_shape = img[np.ix_(mask.any(1), mask.any(0))]
    if check_shape.shape[0] == 0 or check_shape.shape[1] == 0:
        return img
    return check_shape


def preprocess(path):
    """
    Preprocess fundus image:
    1. Read and crop black borders
    2. Resize to 256x256
    3. Apply CLAHE on L channel in LAB color space
    4. Return float32 array with pixel values in 0-255 (no extra normalization)
    """
    img, warning = validate_image(path)
    cropped = crop_black_borders(img)
    resized = cv2.resize(cropped, (256, 256), interpolation=cv2.INTER_AREA)

    # CLAHE on L channel of LAB
    lab = cv2.cvtColor(resized, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    l_enhanced = clahe.apply(l)
    lab_enhanced = cv2.merge((l_enhanced, a, b))
    enhanced_bgr = cv2.cvtColor(lab_enhanced, cv2.COLOR_LAB2BGR)

    # Pixel values in 0-255 with no extra normalization as required
    return enhanced_bgr.astype(np.float32), warning


def overlay_heatmap(img_bgr, cam):
    """Overlay CAM heatmap over preprocessed fundus image."""
    cam_resized = cv2.resize(cam, (img_bgr.shape[1], img_bgr.shape[0]))
    cam_normalized = np.uint8(255 * np.clip(cam_resized, 0, 1))
    heatmap_colored = cv2.applyColorMap(cam_normalized, cv2.COLORMAP_JET)

    # 60% original image + 40% heatmap overlay
    base = np.uint8(np.clip(img_bgr, 0, 255))
    overlay = cv2.addWeighted(base, 0.6, heatmap_colored, 0.4, 0)
    return overlay


def generate_demo_gradcam(img_shape, seed_val=42):
    """Generate a simulated Grad-CAM attention heatmap for demo fallback mode."""
    h, w = img_shape[:2]
    np.random.seed(seed_val % 1000)
    
    y, x = np.ogrid[:h, :w]
    center_y, center_x = h // 2 + np.random.randint(-25, 25), w // 2 + np.random.randint(-35, 35)
    dist_from_center = np.sqrt((x - center_x)**2 + (y - center_y)**2)
    
    cam = np.exp(-dist_from_center**2 / (2 * (40 + np.random.randint(10, 30))**2))
    
    for _ in range(3):
        sx = np.random.randint(40, w - 40)
        sy = np.random.randint(40, h - 40)
        d = np.sqrt((x - sx)**2 + (y - sy)**2)
        cam += 0.45 * np.exp(-d**2 / (2 * (18 + np.random.randint(5, 15))**2))
    
    cam = (cam - cam.min()) / (cam.max() - cam.min() + 1e-8)
    return cam.astype(np.float32)


def grad_cam(model, preprocessed_img, last_conv="top_conv"):
    """
    Compute Grad-CAM heatmap on layer 'top_conv' using TensorFlow GradientTape.
    Falls back to simulated heatmap if model is None or on computation error.
    """
    if model is None:
        return generate_demo_gradcam(preprocessed_img.shape), 0

    try:
        import tensorflow as tf
        grad_model = tf.keras.models.Model(
            inputs=model.input,
            outputs=[model.get_layer(last_conv).output, model.output]
        )
        # Input with pixel values 0-255 (no extra normalization)
        img_input = np.expand_dims(preprocessed_img, axis=0)

        with tf.GradientTape() as tape:
            conv_outputs, predictions = grad_model(img_input)
            pred_class = tf.argmax(predictions[0])
            loss = predictions[:, pred_class]

        grads = tape.gradient(loss, conv_outputs)
        pooled_grads = tf.reduce_mean(grads, axis=(0, 1, 2))
        conv_outputs = conv_outputs[0]
        heatmap = conv_outputs @ pooled_grads[..., tf.newaxis]
        heatmap = tf.squeeze(heatmap)
        heatmap = tf.maximum(heatmap, 0) / (tf.math.reduce_max(heatmap) + 1e-8)
        return heatmap.numpy(), int(pred_class)
    except Exception as e:
        print(f"[ML Grad-CAM] Real Grad-CAM failed ({e}), generating demo heatmap.")
        return generate_demo_gradcam(preprocessed_img.shape), 0


def predict_dr(image_path, output_dir=None):
    """
    Run Diabetic Retinopathy prediction on the image at `image_path`.
    Uses real EfficientNet-B0 model with top_conv Grad-CAM when dr_model.keras is present,
    or falls back to demo mode if absent.
    
    Returns dict:
      {
        "grade": int (0-4),
        "label": str,
        "confidence": float (0-1),
        "probs": list[float] (sum=1.0),
        "heatmap_path": str (relative filename),
        "demo": bool,
        "warning": str or None,
        "advice": str
      }
    """
    # 1. Preprocess: crop black borders, resize 256, CLAHE on L channel of LAB, pixel values 0-255
    preprocessed_img, warning = preprocess(image_path)
    model = load_model_once()

    is_demo = False
    grade = 0
    confidence = 0.0
    probs = [0.0] * 5
    cam = None

    if model is not None:
        try:
            # Inference with 0-255 float32 input (no extra normalization)
            img_input = np.expand_dims(preprocessed_img, axis=0)
            preds = model.predict(img_input, verbose=0)[0]
            grade = int(np.argmax(preds))
            confidence = float(preds[grade])
            probs = [float(p) for p in preds]
            cam, _ = grad_cam(model, preprocessed_img, last_conv="top_conv")
            is_demo = False
        except Exception as e:
            print(f"[ML Predict] Real inference error ({e}), falling back to demo mode.")
            model = None

    if model is None:
        # Fallback DEMO MODE when model file is missing or fails
        is_demo = True
        img_raw = cv2.imread(image_path)
        stat_hash = int(np.mean(img_raw) * 100 + img_raw.shape[0] * 3)
        np.random.seed(stat_hash % 9999)

        grade_pool = [0, 1, 2, 2, 3, 4]
        grade = int(np.random.choice(grade_pool))

        logits = np.random.uniform(0.1, 0.4, size=5)
        logits[grade] = np.random.uniform(1.2, 2.5)
        exp_l = np.exp(logits)
        probs = (exp_l / np.sum(exp_l)).tolist()
        confidence = float(probs[grade])

        cam = generate_demo_gradcam(preprocessed_img.shape, seed_val=stat_hash)

    # Generate and save overlay heatmap
    overlay = overlay_heatmap(preprocessed_img, cam)
    
    heatmap_filename = f"heatmap_{uuid.uuid4().hex[:12]}.png"
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
        heatmap_save_path = os.path.join(output_dir, heatmap_filename)
    else:
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        heatmap_save_path = os.path.join(base_dir, "static", "heatmaps", heatmap_filename)
        os.makedirs(os.path.dirname(heatmap_save_path), exist_ok=True)

    cv2.imwrite(heatmap_save_path, overlay)

    return {
        "grade": grade,
        "label": LABELS[grade],
        "confidence": round(confidence, 4),
        "probs": [round(p, 4) for p in probs],
        "heatmap_path": heatmap_filename,
        "demo": is_demo,
        "warning": warning,
        "advice": GRADE_ADVICE[grade]
    }


def predict_infection(path):
    """Optional bonus: eye infection screening. Returns None if model does not exist."""
    return None
