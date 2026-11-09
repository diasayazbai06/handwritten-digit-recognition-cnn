"""Қолжазба цифрларды тану жүйесінің веб-қосымшасы (Flask сервері).

Іске қосу:  python app.py   ->   http://localhost:5000
"""
import base64
import io
import json
import random
from pathlib import Path

import numpy as np
from flask import Flask, jsonify, render_template, request, send_from_directory
from PIL import Image
from torchvision import datasets

from src import FIGURES, OUTPUTS, ROOT
from src.predict import load_model, predict, preprocess
app = Flask(__name__, template_folder="web/templates", static_folder="web/static")
app.config["MAX_CONTENT_LENGTH"] = 8 * 1024 * 1024  # 8 МБ шектеу

model = load_model()
test_set = datasets.MNIST(ROOT / "data", train=False, download=True)
metrics = json.loads((OUTPUTS / "metrics.json").read_text(encoding="utf-8"))


def to_data_url(arr01: np.ndarray, scale: int = 1) -> str:
    """[0..1] массивті PNG data-URL түріне айналдыру (браузерде көрсету үшін)."""
    img = Image.fromarray((arr01 * 255).clip(0, 255).astype(np.uint8))
    if scale > 1:
        img = img.resize((img.width * scale, img.height * scale), Image.NEAREST)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()


def result_json(digit28: np.ndarray, extra: dict | None = None):
    probs = predict(model, digit28)
    out = {
        "digit": int(probs.argmax()),
        "confidence": float(probs.max()),
        "probs": [round(float(p), 6) for p in probs],
        "preview": to_data_url(digit28, scale=4),
    }
    if extra:
        out.update(extra)
    return jsonify(out)


@app.get("/")
def index():
    return render_template("index.html", m=metrics)


@app.post("/api/predict")
def api_predict():
    """Кіріс: JSON {"image": "data:image/png;base64,..."} немесе multipart файл."""
    try:
        if "file" in request.files:
            img = Image.open(request.files["file"].stream)
        else:
            data = request.get_json(force=True)["image"]
            img = Image.open(io.BytesIO(base64.b64decode(data.split(",", 1)[-1])))
        if img.mode in ("RGBA", "LA"):
            # Мөлдір фонды ақ түске ауыстыру
            bg = Image.new("RGB", img.size, "white")
            bg.paste(img, mask=img.split()[-1])
            img = bg
        digit = preprocess(img)
    except Exception as exc:  # дұрыс емес файл
        return jsonify({"error": f"Суретті оқу мүмкін болмады: {exc}"}), 400
    if digit.max() == 0:
        return jsonify({"error": "Суретте цифр табылмады"}), 400
    return result_json(digit)


@app.get("/api/sample")
def api_sample():
    """MNIST тест жиынынан кездейсоқ сурет."""
    idx = random.randrange(len(test_set))
    img, label = test_set[idx]
    digit = np.asarray(img, dtype=np.float32) / 255.0
    return result_json(digit, {"index": idx, "label": int(label),
                               "original": to_data_url(digit, scale=8)})


@app.get("/api/metrics")
def api_metrics():
    return jsonify(metrics)


@app.get("/results/<path:name>")
def results_file(name):
    """Оқыту графиктерін (outputs/figures бумасы) сайтта көрсету."""
    return send_from_directory(FIGURES, name)


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)
