"""Кез келген суретті MNIST форматына келтіру және цифрды болжау."""
from pathlib import Path

import numpy as np
import torch
from PIL import Image, ImageOps

from . import MODELS
from .model import MNIST_MEAN, MNIST_STD, DigitCNN


def load_model(path: Path = MODELS / "digit_cnn.pt") -> DigitCNN:
    model = DigitCNN()
    model.load_state_dict(torch.load(path, map_location="cpu"))
    model.eval()
    return model


def preprocess(img: Image.Image) -> np.ndarray:
    """Суретті 28x28 өлшемге келтіреді: қара фон, ақ цифр, ортаға орналастырылған."""
    g = ImageOps.grayscale(img)
    arr = np.asarray(g, dtype=np.float32)
    # Фон ашық болса (қағаздағы жазу), түстерді инверсиялау
    if arr.mean() > 127:
        arr = 255 - arr
    arr[arr < 40] = 0  # әлсіз шуды тазалау
    ys, xs = np.nonzero(arr)
    if len(xs) == 0:
        return np.zeros((28, 28), dtype=np.float32)
    arr = arr[ys.min():ys.max() + 1, xs.min():xs.max() + 1]

    # Ұзын жағын 20 пиксельге келтіру (MNIST стандарты сияқты)
    h, w = arr.shape
    scale = 20.0 / max(h, w)
    nh, nw = max(1, round(h * scale)), max(1, round(w * scale))
    small = np.asarray(Image.fromarray(arr.astype(np.uint8)).resize((nw, nh), Image.LANCZOS),
                       dtype=np.float32)

    canvas = np.zeros((28, 28), dtype=np.float32)
    top, left = (28 - nh) // 2, (28 - nw) // 2
    canvas[top:top + nh, left:left + nw] = small

    # Масса орталығы бойынша ортаға жылжыту
    total = canvas.sum()
    if total > 0:
        yy, xx = np.indices(canvas.shape)
        cy, cx = (yy * canvas).sum() / total, (xx * canvas).sum() / total
        canvas = np.roll(canvas, (round(14 - cy), round(14 - cx)), axis=(0, 1))
    return canvas / 255.0


@torch.no_grad()
def predict(model: DigitCNN, digit28: np.ndarray) -> np.ndarray:
    """28x28 [0..1] массивті қабылдап, 10 класс ықтималдығын қайтарады."""
    x = (torch.tensor(digit28, dtype=torch.float32) - MNIST_MEAN) / MNIST_STD
    out = model(x.view(1, 1, 28, 28))
    return torch.softmax(out, dim=1)[0].numpy()


if __name__ == "__main__":
    import sys
    m = load_model()
    for p in sys.argv[1:]:
        probs = predict(m, preprocess(Image.open(p)))
        print(f"{p}: цифр = {probs.argmax()} (сенімділік {probs.max()*100:.1f}%)")
