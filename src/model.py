"""Модельдер: базалық көп қабатты перцептрон (MLP) және негізгі конволюциялық желі (DigitCNN)."""
import torch
import torch.nn as nn

# MNIST оқыту жиынының орташа мәні мен стандартты ауытқуы (нормализация үшін)
MNIST_MEAN = 0.1307
MNIST_STD = 0.3081


class MLP(nn.Module):
    """Толық байланысқан желі: 784 -> 256 -> 128 -> 10 (салыстыру үшін)."""

    def __init__(self, num_classes: int = 10):
        super().__init__()
        self.net = nn.Sequential(
            nn.Flatten(),
            nn.Linear(28 * 28, 256), nn.ReLU(), nn.Dropout(0.2),
            nn.Linear(256, 128), nn.ReLU(), nn.Dropout(0.2),
            nn.Linear(128, num_classes),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.net(x)


class DigitCNN(nn.Module):
    """Екі конволюциялық блок + толық байланысқан классификатор.

    Кіріс: 1x28x28 сұр түсті сурет. Шығыс: 10 класс (0–9 цифрлары).
    """

    def __init__(self, num_classes: int = 10):
        super().__init__()
        self.features = nn.Sequential(
            # 1-блок: 1x28x28 -> 32x14x14
            nn.Conv2d(1, 32, kernel_size=3, padding=1),
            nn.BatchNorm2d(32),
            nn.ReLU(),
            nn.Conv2d(32, 32, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.MaxPool2d(2),
            nn.Dropout(0.25),
            # 2-блок: 32x14x14 -> 64x7x7
            nn.Conv2d(32, 64, kernel_size=3, padding=1),
            nn.BatchNorm2d(64),
            nn.ReLU(),
            nn.Conv2d(64, 64, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.MaxPool2d(2),
            nn.Dropout(0.25),
        )
        self.classifier = nn.Sequential(
            nn.Flatten(),
            nn.Linear(64 * 7 * 7, 128),
            nn.ReLU(),
            nn.Dropout(0.5),
            nn.Linear(128, num_classes),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.classifier(self.features(x))


def build_model(name: str) -> nn.Module:
    models = {"mlp": MLP, "cnn": DigitCNN}
    if name not in models:
        raise ValueError(f"Белгісіз модель: {name}")
    return models[name]()


def count_params(model: nn.Module) -> int:
    return sum(p.numel() for p in model.parameters() if p.requires_grad)
