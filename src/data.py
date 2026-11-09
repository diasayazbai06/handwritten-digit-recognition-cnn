"""MNIST деректерін жүктеу, train/validation/test бөлу және зерттеушілік талдау.

Бөлу қағидасы: ресми 60 000 оқыту жиынынан 54 000 – train, 6 000 – validation
(seed бойынша бекітілген кездейсоқ бөлу). Ресми 10 000 тест жиыны тек қорытынды
бағалауда қолданылады, сондықтан деректердің ағып кетуі болмайды.
"""
import hashlib

import numpy as np
import torch
from torch.utils.data import DataLoader, Subset
from torchvision import datasets, transforms

from . import DATA_DIR
from .model import MNIST_MEAN, MNIST_STD

N_TRAIN, N_VAL = 54_000, 6_000


def split_indices(seed: int):
    """Train/validation индекстері (seed бойынша қайталанатын)."""
    g = torch.Generator().manual_seed(seed)
    perm = torch.randperm(N_TRAIN + N_VAL, generator=g).tolist()
    return perm[:N_TRAIN], perm[N_TRAIN:]


def get_transforms(augment: bool):
    base = [transforms.ToTensor(), transforms.Normalize((MNIST_MEAN,), (MNIST_STD,))]
    if augment:
        aug = transforms.RandomAffine(degrees=10, translate=(0.1, 0.1), scale=(0.9, 1.1))
        return transforms.Compose([aug] + base)
    return transforms.Compose(base)


def get_loaders(seed: int = 42, batch_size: int = 128, augment: bool = False, num_workers: int = 4):
    """Үш DataLoader қайтарады: train (қажет болса аугментациямен), validation, test."""
    train_full_aug = datasets.MNIST(DATA_DIR, train=True, download=True, transform=get_transforms(augment))
    train_full_plain = datasets.MNIST(DATA_DIR, train=True, download=True, transform=get_transforms(False))
    test_set = datasets.MNIST(DATA_DIR, train=False, download=True, transform=get_transforms(False))

    tr_idx, va_idx = split_indices(seed)
    g = torch.Generator().manual_seed(seed)
    kw = dict(num_workers=num_workers, persistent_workers=num_workers > 0)
    train_loader = DataLoader(Subset(train_full_aug, tr_idx), batch_size=batch_size,
                              shuffle=True, generator=g, **kw)
    val_loader = DataLoader(Subset(train_full_plain, va_idx), batch_size=1000, **kw)
    test_loader = DataLoader(test_set, batch_size=1000, **kw)
    return train_loader, val_loader, test_loader


def get_numpy_splits(seed: int = 42):
    """Базалық (scikit-learn) модель үшін нормаланған жалпақ массивтер."""
    tr = datasets.MNIST(DATA_DIR, train=True, download=True)
    te = datasets.MNIST(DATA_DIR, train=False, download=True)
    X = (tr.data.numpy().reshape(-1, 784) / 255.0 - MNIST_MEAN) / MNIST_STD
    y = tr.targets.numpy()
    Xt = (te.data.numpy().reshape(-1, 784) / 255.0 - MNIST_MEAN) / MNIST_STD
    yt = te.targets.numpy()
    tr_idx, va_idx = split_indices(seed)
    return (X[tr_idx], y[tr_idx]), (X[va_idx], y[va_idx]), (Xt, yt)


def dataset_report(seed: int = 42) -> dict:
    """Зерттеушілік талдау: көлемі, сыныптар таралуы, қайталанатын суреттер, пиксель статистикасы."""
    tr = datasets.MNIST(DATA_DIR, train=True, download=True)
    te = datasets.MNIST(DATA_DIR, train=False, download=True)
    tr_idx, va_idx = split_indices(seed)
    ytr = tr.targets.numpy()

    def counts(y):
        return np.bincount(y, minlength=10).tolist()

    def hashes(arr):
        return [hashlib.md5(a.tobytes()).hexdigest() for a in arr]

    h_train = hashes(tr.data.numpy())
    h_test = hashes(te.data.numpy())
    train_px = tr.data.numpy()[tr_idx].astype(np.float32) / 255.0
    return {
        "n_train": len(tr_idx), "n_val": len(va_idx), "n_test": len(te),
        "image_shape": list(tr.data.shape[1:]),
        "train_counts": counts(ytr[tr_idx]),
        "val_counts": counts(ytr[va_idx]),
        "test_counts": counts(te.targets.numpy()),
        "duplicates_in_train": len(h_train) - len(set(h_train)),
        "train_test_overlap": len(set(h_train) & set(h_test)),
        "pixel_mean_train": float(train_px.mean()),
        "pixel_std_train": float(train_px.std()),
        "missing_values": 0,
    }
