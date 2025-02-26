"""Test to check the per functional transformers."""

import unittest

import numpy as np

import skfda.representation.basis as basis
from skfda.datasets import fetch_growth
from skfda.exploratory.stats import unconditional_expected_value


class TestUncondExpectedVals(unittest.TestCase):
    """Tests for unconditional expected values method."""

    def test_transform(self) -> None:
        """Check the data transformation is done correctly."""
        X = fetch_growth(return_X_y=True)[0]

        def f(x: np.ndarray) -> np.ndarray:  # noqa: WPS430
            return np.log(x)

        data_grid = unconditional_expected_value(X[:5], f)
        data_basis = unconditional_expected_value(
            X[:5].to_basis(basis.BSpline(n_basis=7)),
            f,
        )
        np.testing.assert_allclose(data_basis, data_grid, rtol=1e-3)


if __name__ == '__main__':
    unittest.main()
