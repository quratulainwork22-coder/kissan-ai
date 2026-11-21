import os
import numpy as np
from PIL import Image

MODEL_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "models")
MODEL_PATH = os.path.join(MODEL_DIR, "cotton_model.keras")
LABELS_PATH = os.path.join(MODEL_DIR, "labels.txt")
CONFIDENCE_THRESHOLD = 0.70  # below this, result is "uncertain"

_model = None
_labels = None


def _load():
    global _model, _labels
    if _model is not None:
        return True
    if not (os.path.exists(MODEL_PATH) and os.path.exists(LABELS_PATH)):
        return False
    try:
        import tensorflow as tf
    except ImportError:
        return False
    _model = tf.keras.models.load_model(MODEL_PATH)
    with open(LABELS_PATH, encoding="utf-8") as f:
        _labels = [line.strip() for line in f if line.strip()]
    return True


def predict(image_path):
    """Returns (label_code, confidence)."""
    if not _load():
        return "model_not_ready", 0.0
    img = Image.open(image_path).convert("RGB").resize((224, 224))
    x = np.expand_dims(np.asarray(img, dtype="float32"), axis=0)  # 0-255, model rescales
    probs = _model.predict(x, verbose=0)[0]
    idx = int(np.argmax(probs))
    confidence = float(probs[idx])
    if confidence < CONFIDENCE_THRESHOLD:
        return "uncertain", confidence
    return _labels[idx], confidence
