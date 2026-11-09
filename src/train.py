"""Конфигурация бойынша бір экспериментті орындау.

Іске қосу:  python -m src.train --config configs/E04_cnn_aug.json

Нәтижелер:
  models/<ID>.pt                         – validation бойынша үздік салмақтар (терең модельдер)
  outputs/experiments/<ID>/history.json  – дәуірлер бойынша loss/accuracy
  outputs/experiments/<ID>/result.json   – конфигурация, метрикалар, уақыт, орта
  outputs/experiments.csv                – барлық эксперименттердің тіркеу кестесі
"""
import argparse
import csv
import json
import platform
import random
import subprocess
import time

import numpy as np
import torch
import torch.nn as nn

from . import EXPERIMENTS, MODELS, OUTPUTS, ROOT
from .data import get_loaders, get_numpy_splits
from .model import build_model, count_params


def set_seed(seed: int):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)


def environment() -> dict:
    """Бағдарламалық орта мен есептеу құрылғысы туралы мәлімет."""
    import sklearn
    import torchvision
    try:
        cpu = subprocess.run(["powershell", "-NoProfile", "-Command",
                              "(Get-CimInstance Win32_Processor).Name"],
                             capture_output=True, text=True, timeout=20).stdout.strip()
    except Exception:
        cpu = platform.processor()
    return {
        "os": f"{platform.system()} {platform.release()}",
        "python": platform.python_version(),
        "torch": torch.__version__,
        "torchvision": torchvision.__version__,
        "numpy": np.__version__,
        "scikit-learn": sklearn.__version__,
        "device": "cuda" if torch.cuda.is_available() else "cpu",
        "cpu": cpu,
        "threads": torch.get_num_threads(),
    }


def run_epoch(model, loader, criterion, device, optimizer=None):
    training = optimizer is not None
    model.train(training)
    total_loss, correct, n = 0.0, 0, 0
    with torch.set_grad_enabled(training):
        for x, y in loader:
            x, y = x.to(device), y.to(device)
            out = model(x)
            loss = criterion(out, y)
            if training:
                optimizer.zero_grad()
                loss.backward()
                optimizer.step()
            total_loss += loss.item() * x.size(0)
            correct += (out.argmax(1) == y).sum().item()
            n += x.size(0)
    return total_loss / n, correct / n


@torch.no_grad()
def accuracy(model, loader, device):
    model.eval()
    correct = n = 0
    for x, y in loader:
        correct += (model(x.to(device)).argmax(1).cpu() == y).sum().item()
        n += y.size(0)
    return correct / n


def train_baseline(cfg):
    """E01: логистикалық регрессия (scikit-learn) – базалық шешім."""
    from sklearn.linear_model import LogisticRegression
    (X, y), (Xv, yv), (Xt, yt) = get_numpy_splits(cfg["seed"])
    t0 = time.time()
    clf = LogisticRegression(C=cfg.get("C", 0.1), max_iter=cfg.get("max_iter", 200),
                             random_state=cfg["seed"])
    clf.fit(X, y)
    t = time.time() - t0
    return {
        "params": int(clf.coef_.size + clf.intercept_.size),
        "best_val_acc": float(clf.score(Xv, yv)),
        "test_acc": float(clf.score(Xt, yt)),
        "train_time_sec": round(t, 1),
        "history": None,
    }


def train_deep(cfg):
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    train_loader, val_loader, test_loader = get_loaders(
        seed=cfg["seed"], batch_size=cfg["batch_size"], augment=cfg["augment"],
        num_workers=cfg.get("num_workers", 4))
    model = build_model(cfg["model"]).to(device)
    criterion = nn.CrossEntropyLoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=cfg["lr"])
    scheduler = torch.optim.lr_scheduler.StepLR(optimizer, step_size=cfg["step_size"], gamma=cfg["gamma"])

    hist = {"train_loss": [], "train_acc": [], "val_loss": [], "val_acc": [], "epoch_time": []}
    best_val, best_epoch, t0 = 0.0, 0, time.time()
    weights = MODELS / f"{cfg['id']}.pt"
    for epoch in range(1, cfg["epochs"] + 1):
        te = time.time()
        tl, ta = run_epoch(model, train_loader, criterion, device, optimizer)
        vl, va = run_epoch(model, val_loader, criterion, device)
        scheduler.step()
        for k, v in zip(("train_loss", "train_acc", "val_loss", "val_acc", "epoch_time"),
                        (tl, ta, vl, va, time.time() - te)):
            hist[k].append(v)
        print(f"[{cfg['id']}] дәуір {epoch}/{cfg['epochs']}: train_loss={tl:.4f} "
              f"train_acc={ta:.4f} val_loss={vl:.4f} val_acc={va:.4f}", flush=True)
        if va > best_val:  # үздік модель тек validation бойынша таңдалады
            best_val, best_epoch = va, epoch
            torch.save(model.state_dict(), weights)
    train_time = time.time() - t0

    model.load_state_dict(torch.load(weights, map_location=device))
    return {
        "params": count_params(model),
        "best_val_acc": best_val,
        "best_epoch": best_epoch,
        "test_acc": accuracy(model, test_loader, device),
        "train_time_sec": round(train_time, 1),
        "history": hist,
        "weights": str(weights.relative_to(ROOT)).replace("\\", "/"),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True)
    args = ap.parse_args()
    from pathlib import Path
    cfg_path = Path(args.config)
    cfg_path = cfg_path if cfg_path.is_absolute() else ROOT / cfg_path
    cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
    set_seed(cfg["seed"])
    torch.set_num_threads(cfg.get("threads", torch.get_num_threads()))

    res = train_baseline(cfg) if cfg["model"] == "logreg" else train_deep(cfg)
    hist = res.pop("history")
    out_dir = EXPERIMENTS / cfg["id"]
    out_dir.mkdir(parents=True, exist_ok=True)
    if hist:
        (out_dir / "history.json").write_text(json.dumps(hist, indent=2), encoding="utf-8")
    result = {"config": cfg, **res, "environment": environment()}
    (out_dir / "result.json").write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")

    # Эксперименттерді тіркеу кестесі (әдістемелік нұсқаулықтың Г қосымшасы бойынша)
    csv_path = OUTPUTS / "experiments.csv"
    rows = []
    if csv_path.exists():
        with open(csv_path, encoding="utf-8") as f:
            rows = [r for r in csv.DictReader(f) if r["id"] != cfg["id"]]
    rows.append({
        "id": cfg["id"], "model": cfg["name"], "data": "MNIST v1 (54k/6k/10k)",
        "hyperparams": cfg.get("hp_text", ""), "seed": cfg["seed"],
        "val_acc": f"{res['best_val_acc']:.4f}", "test_acc": f"{res['test_acc']:.4f}",
        "time_sec": res["train_time_sec"], "params": res["params"], "note": cfg.get("note", ""),
    })
    rows.sort(key=lambda r: r["id"])
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print(f"[{cfg['id']}] val_acc={res['best_val_acc']:.4f} test_acc={res['test_acc']:.4f} "
          f"уақыт={res['train_time_sec']} с", flush=True)


if __name__ == "__main__":
    main()
