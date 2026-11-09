"""Эксперименттерді салыстыру, үздік модельді таңдау және қорытынды бағалау.

Іске қосу:  python -m src.evaluate --select-best

1) outputs/experiments.csv ішінен validation дәлдігі ең жоғары терең модель таңдалады
   (test жиыны таңдауға қатыспайды);
2) оның салмақтары models/digit_cnn.pt ретінде көшіріледі;
3) тест жиынында толық метрикалар есептеліп, outputs/metrics.json сақталады;
4) outputs/figures/ бумасына барлық графиктер салынады.
"""
import argparse
import csv
import json
import shutil

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import torch
from sklearn.metrics import classification_report, confusion_matrix, roc_auc_score
from torchvision import datasets

from . import DATA_DIR, EXPERIMENTS, FIGURES, MODELS, OUTPUTS, ROOT
from .data import dataset_report, get_loaders
from .model import build_model, count_params

plt.rcParams.update({"font.size": 10, "axes.titlesize": 11})


def load_rows():
    with open(OUTPUTS / "experiments.csv", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def select_best(rows):
    deep = [r for r in rows if (EXPERIMENTS / r["id"] / "history.json").exists()]
    return max(deep, key=lambda r: (float(r["val_acc"]), -int(r["id"][1:])))


@torch.no_grad()
def predict_all(model, loader):
    model.eval()
    probs, labels = [], []
    for x, y in loader:
        probs.append(torch.softmax(model(x), dim=1))
        labels.append(y)
    probs = torch.cat(probs).numpy()
    return probs.argmax(1), torch.cat(labels).numpy(), probs


# ---------------- Графиктер ----------------
def plot_class_distribution(rep):
    x = np.arange(10)
    fig, ax = plt.subplots(figsize=(9, 3.6))
    w = 0.27
    ax.bar(x - w, rep["train_counts"], w, label=f"Train ({rep['n_train']})")
    ax.bar(x, rep["val_counts"], w, label=f"Validation ({rep['n_val']})")
    ax.bar(x + w, rep["test_counts"], w, label=f"Test ({rep['n_test']})")
    ax.set_xticks(x)
    ax.set_xlabel("Цифр (класс)")
    ax.set_ylabel("Суреттер саны, дана")
    ax.set_title("Сыныптардың train/validation/test бойынша таралуы")
    ax.set_ylim(0, max(rep["train_counts"]) * 1.25)
    ax.legend(ncol=3, loc="upper center")
    ax.grid(axis="y", alpha=.3)
    fig.tight_layout()
    fig.savefig(FIGURES / "class_distribution.png", dpi=160)
    plt.close(fig)


def plot_samples():
    ds = datasets.MNIST(DATA_DIR, train=False, download=True)
    fig, axes = plt.subplots(2, 10, figsize=(12, 3))
    for i, ax in enumerate(axes.flat):
        ax.imshow(ds.data[i].numpy(), cmap="gray")
        ax.set_title(str(int(ds.targets[i])))
        ax.axis("off")
    fig.suptitle("MNIST тест жиынынан мысалдар (үстінде – нақты класс)")
    fig.tight_layout()
    fig.savefig(FIGURES / "dataset_samples.png", dpi=150)
    plt.close(fig)


def plot_history(h, exp_id):
    ep = np.arange(1, len(h["train_loss"]) + 1)
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(11, 4))
    a1.plot(ep, h["train_loss"], "o-", label="Оқыту (train)")
    a1.plot(ep, h["val_loss"], "s-", label="Валидация (validation)")
    a1.set_title(f"Шығын функциясы ({exp_id})")
    a1.set_xlabel("Дәуір (epoch)")
    a1.set_ylabel("Кросс-энтропия, өлшемсіз")
    a1.legend(); a1.grid(alpha=0.3)
    a2.plot(ep, np.array(h["train_acc"]) * 100, "o-", label="Оқыту (train)")
    a2.plot(ep, np.array(h["val_acc"]) * 100, "s-", label="Валидация (validation)")
    a2.set_title(f"Дәлдік ({exp_id})")
    a2.set_xlabel("Дәуір (epoch)")
    a2.set_ylabel("Accuracy, %")
    a2.legend(); a2.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(FIGURES / "training_curves.png", dpi=150)
    plt.close(fig)


def plot_val_curves(rows):
    fig, ax = plt.subplots(figsize=(8, 4))
    for r in rows:
        hp = EXPERIMENTS / r["id"] / "history.json"
        if hp.exists():
            h = json.loads(hp.read_text(encoding="utf-8"))
            ax.plot(np.arange(1, len(h["val_acc"]) + 1), np.array(h["val_acc"]) * 100, "o-",
                    label=f"{r['id']}: {r['model']} ({r['note']})", ms=4)
    base = [r for r in rows if r["id"] == "E01"]
    if base:
        ax.axhline(float(base[0]["val_acc"]) * 100, ls="--", c="gray", label="E01: логистикалық регрессия")
    ax.set_xlabel("Дәуір (epoch)")
    ax.set_ylabel("Validation accuracy, %")
    ax.set_title("Эксперименттердің validation дәлдігі")
    ax.set_ylim(90, 100)
    ax.legend(fontsize=8, loc="lower right")
    ax.grid(alpha=.3)
    fig.tight_layout()
    fig.savefig(FIGURES / "experiments_val_curves.png", dpi=150)
    plt.close(fig)


def plot_experiments_bar(rows):
    ids = [r["id"] for r in rows]
    val = [float(r["val_acc"]) * 100 for r in rows]
    test = [float(r["test_acc"]) * 100 for r in rows]
    x = np.arange(len(ids))
    fig, ax = plt.subplots(figsize=(8, 3.8))
    b1 = ax.bar(x - 0.2, val, 0.4, label="Validation")
    b2 = ax.bar(x + 0.2, test, 0.4, label="Test")
    for bars in (b1, b2):
        for b in bars:
            ax.text(b.get_x() + b.get_width() / 2, b.get_height() + 0.08, f"{b.get_height():.2f}",
                    ha="center", fontsize=7.5)
    ax.set_xticks(x, ids)
    ax.set_ylim(90, 101.2)
    ax.set_xlabel("Эксперимент")
    ax.set_ylabel("Accuracy, %")
    ax.set_title("Эксперименттер нәтижелерін салыстыру")
    ax.legend(loc="upper left", ncol=2)
    ax.grid(axis="y", alpha=.3)
    fig.tight_layout()
    fig.savefig(FIGURES / "experiments_bar.png", dpi=150)
    plt.close(fig)


def plot_confusion(cm):
    fig, ax = plt.subplots(figsize=(7, 6))
    im = ax.imshow(cm, cmap="Blues")
    ax.set_xticks(range(10)); ax.set_yticks(range(10))
    ax.set_xlabel("Болжанған цифр"); ax.set_ylabel("Нақты цифр")
    ax.set_title("Қателер матрицасы (тест жиыны, 10 000 сурет)")
    thr = cm.max() / 2
    for i in range(10):
        for j in range(10):
            ax.text(j, i, cm[i, j], ha="center", va="center", fontsize=8,
                    color="white" if cm[i, j] > thr else "black")
    fig.colorbar(im, ax=ax, fraction=0.046, label="Суреттер саны")
    fig.tight_layout()
    fig.savefig(FIGURES / "confusion_matrix.png", dpi=150)
    plt.close(fig)


def plot_errors(preds, labels, probs):
    ds = datasets.MNIST(DATA_DIR, train=False, download=True)
    idx = np.where(preds != labels)[0][:12]
    fig, axes = plt.subplots(2, 6, figsize=(11, 5.4))
    for ax, i in zip(axes.flat, idx):
        ax.imshow(ds.data[i].numpy(), cmap="gray")
        ax.set_title(f"Нақты: {labels[i]}\nБолжам: {preds[i]} ({probs[i].max()*100:.0f}%)", fontsize=9)
        ax.axis("off")
    for ax in list(axes.flat)[len(idx):]:
        ax.axis("off")
    fig.suptitle("Модель қателескен тест суреттері")
    fig.tight_layout()
    fig.savefig(FIGURES / "misclassified.png", dpi=150)
    plt.close(fig)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--select-best", action="store_true")
    ap.parse_args()

    rows = load_rows()
    best = select_best(rows)
    res = json.loads((EXPERIMENTS / best["id"] / "result.json").read_text(encoding="utf-8"))
    cfg = res["config"]
    shutil.copy(ROOT / res["weights"], MODELS / "digit_cnn.pt")

    model = build_model(cfg["model"])
    model.load_state_dict(torch.load(MODELS / "digit_cnn.pt", map_location="cpu"))
    _, _, test_loader = get_loaders(seed=cfg["seed"], num_workers=0)
    preds, labels, probs = predict_all(model, test_loader)
    rep = classification_report(labels, preds, digits=4, output_dict=True)
    cm = confusion_matrix(labels, preds)
    hist = json.loads((EXPERIMENTS / best["id"] / "history.json").read_text(encoding="utf-8"))

    ds_rep = dataset_report(cfg["seed"])
    (OUTPUTS / "dataset_report.json").write_text(json.dumps(ds_rep, indent=2), encoding="utf-8")

    metrics = {
        "best_experiment": best["id"],
        "config": cfg,
        "device": res["environment"]["device"],
        "environment": res["environment"],
        "params": count_params(model),
        "epochs": cfg["epochs"],
        "best_epoch": res["best_epoch"],
        "train_time_sec": res["train_time_sec"],
        "best_val_acc": res["best_val_acc"],
        "test_acc": float((preds == labels).mean()),
        "test_errors": int((preds != labels).sum()),
        "roc_auc_macro": float(roc_auc_score(labels, probs, multi_class="ovr", average="macro")),
        "history": hist,
        "per_class": {str(d): {k: rep[str(d)][k] for k in ("precision", "recall", "f1-score", "support")}
                      for d in range(10)},
        "macro_avg": rep["macro avg"],
        "confusion_matrix": cm.tolist(),
        "experiments": rows,
    }
    (OUTPUTS / "metrics.json").write_text(json.dumps(metrics, indent=2, ensure_ascii=False), encoding="utf-8")

    plot_samples()
    plot_class_distribution(ds_rep)
    plot_history(hist, best["id"])
    plot_val_curves(rows)
    plot_experiments_bar(rows)
    plot_confusion(cm)
    plot_errors(preds, labels, probs)
    print(f"Үздік эксперимент (validation бойынша): {best['id']}  "
          f"test_acc={metrics['test_acc']*100:.2f}%  ROC-AUC={metrics['roc_auc_macro']:.5f}")


if __name__ == "__main__":
    main()
