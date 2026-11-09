"""Модельдер мен алдын ала өңдеуге арналған қарапайым тесттер.

Іске қосу:  python -m unittest discover tests
"""
import unittest

import numpy as np
import torch
from PIL import Image, ImageDraw

from src.data import split_indices
from src.model import DigitCNN, MLP, count_params
from src.predict import preprocess


class TestModels(unittest.TestCase):
    def test_cnn_output_shape(self):
        out = DigitCNN()(torch.zeros(4, 1, 28, 28))
        self.assertEqual(tuple(out.shape), (4, 10))

    def test_mlp_output_shape(self):
        out = MLP()(torch.zeros(2, 1, 28, 28))
        self.assertEqual(tuple(out.shape), (2, 10))

    def test_cnn_param_count(self):
        self.assertEqual(count_params(DigitCNN()), 468_010)


class TestData(unittest.TestCase):
    def test_split_is_reproducible_and_disjoint(self):
        tr1, va1 = split_indices(42)
        tr2, va2 = split_indices(42)
        self.assertEqual(tr1, tr2)
        self.assertEqual(len(tr1), 54_000)
        self.assertEqual(len(va1), 6_000)
        self.assertFalse(set(tr1) & set(va1))


class TestPreprocess(unittest.TestCase):
    def _digit_on_white(self):
        img = Image.new("RGB", (200, 200), "white")
        ImageDraw.Draw(img).line([(60, 40), (140, 40), (90, 170)], fill="black", width=14)
        return img

    def test_output_shape_and_range(self):
        arr = preprocess(self._digit_on_white())
        self.assertEqual(arr.shape, (28, 28))
        self.assertGreaterEqual(arr.min(), 0.0)
        self.assertLessEqual(arr.max(), 1.0)

    def test_white_background_is_inverted(self):
        arr = preprocess(self._digit_on_white())
        # MNIST форматы: фон қара (0), цифр ақ – шеттері нөлге жақын болуы керек
        self.assertLess(arr[0].mean(), 0.05)
        self.assertGreater(arr.max(), 0.5)

    def test_digit_is_centered(self):
        arr = preprocess(self._digit_on_white())
        yy, xx = np.indices(arr.shape)
        cy, cx = (yy * arr).sum() / arr.sum(), (xx * arr).sum() / arr.sum()
        self.assertAlmostEqual(cy, 14, delta=1.5)
        self.assertAlmostEqual(cx, 14, delta=1.5)

    def test_empty_image(self):
        arr = preprocess(Image.new("L", (50, 50), 255))
        self.assertEqual(arr.sum(), 0)


if __name__ == "__main__":
    unittest.main()
