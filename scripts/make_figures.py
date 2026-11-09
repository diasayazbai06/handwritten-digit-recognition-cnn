"""Есепке арналған сызбалар: жүйенің жалпы құрылымы және CNN архитектурасы."""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

RES = Path(__file__).resolve().parent.parent / "outputs" / "figures"
RES.mkdir(exist_ok=True)


def boxes_row(items, path, title, colors, figsize=(13, 3.0), fontsize=10.5):
    fig, ax = plt.subplots(figsize=figsize)
    n = len(items)
    w, gap = 1.0, 0.3
    total = n * w + (n - 1) * gap
    ax.set_xlim(-0.2, total + 0.2)
    ax.set_ylim(-0.1, 1.25)
    ax.axis("off")
    for i, (txt, col) in enumerate(zip(items, colors)):
        x = i * (w + gap)
        ax.add_patch(FancyBboxPatch((x, 0.15), w, 0.8, boxstyle="round,pad=0.03",
                                    fc=col, ec="#333333", lw=1.2))
        ax.text(x + w / 2, 0.55, txt, ha="center", va="center", fontsize=fontsize, wrap=True)
        if i < n - 1:
            ax.add_patch(FancyArrowPatch((x + w + 0.03, 0.55), (x + w + gap - 0.03, 0.55),
                                         arrowstyle="-|>", mutation_scale=16, lw=1.4,
                                         color="#333333"))
    fig.tight_layout()
    fig.savefig(path, dpi=170)
    plt.close(fig)


boxes_row(
    ["Кіріс сурет\n(PNG / JPG)", "Сұр түске\nтүрлендіру,\nинверсия", "Қию,\n20×20 масштаб,\nортаға қою",
     "Нормализация\n28×28", "CNN моделі\n(DigitCNN)", "Softmax:\n10 ықтималдық", "Нәтиже:\nцифр + %"],
    RES / "pipeline.png", "Тану жүйесінің жалпы құрылымы",
    ["#e8f0fe", "#fff4e5", "#fff4e5", "#fff4e5", "#e6f4ea", "#e6f4ea", "#fce8e6"],
    figsize=(11, 2.4), fontsize=9)

boxes_row(
    ["Кіріс\n1×28×28", "Conv 3×3 ×32\nBN + ReLU\nConv 3×3 ×32", "MaxPool 2×2\nDropout 0,25\n32×14×14",
     "Conv 3×3 ×64\nBN + ReLU\nConv 3×3 ×64", "MaxPool 2×2\nDropout 0,25\n64×7×7",
     "Flatten 3136\nLinear 128\nDropout 0,5", "Linear 10\nSoftmax"],
    RES / "architecture.png", "DigitCNN моделінің архитектурасы",
    ["#e8f0fe", "#d2e3fc", "#fef7e0", "#d2e3fc", "#fef7e0", "#e6f4ea", "#fce8e6"],
    figsize=(11, 2.4), fontsize=8.8)
print("ok")
