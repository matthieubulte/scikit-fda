"""Functional Transformers Module."""

from __future__ import annotations

from typing import Tuple, Union

import numpy as np

from ...representation import FDataBasis, FDataGrid


def local_averages(
    data: Union[FDataGrid, FDataBasis],
    n_intervals: int,
) -> np.ndarray:
    r"""
    Calculate the local averages of a given data.

    Take functional data as a grid or a basis and performs
    the following map:

    .. math::
        f_1(X) = \frac{1}{|T_1|} \int_{T_1} X(t) dt,\dots, \\
        f_p(X) = \frac{1}{|T_p|} \int_{T_p} X(t) dt

    where {T_1,\dots,T_p} are disjoint intervals of the interval [a,b]

    It is calculated for a given number of intervals,
    which are of equal sizes.
    Args:
        data: FDataGrid or FDataBasis where we want to
        calculate the local averages.
        n_intervals: number of intervals we want to consider.
    Returns:
        ndarray of shape (n_intervals, n_samples, n_dimensions)
        with the transformed data for FDataBasis and (n_intervals, n_samples)
        for FDataGrid.

    Example:

        We import the Berkeley Growth Study dataset.
        We will use only the first 30 samples to make the
        example easy.
        >>> from skfda.datasets import fetch_growth
        >>> dataset = fetch_growth(return_X_y=True)[0]
        >>> X = dataset[:30]

        Then we decide how many intervals we want to consider (in our case 2)
        and call the function with the dataset.
        >>> import numpy as np
        >>> from skfda.exploratory.stats import local_averages
        >>> np.around(local_averages(X, 2), decimals=2)
        array([[  993.98,   950.82,   911.93,   946.44,   887.3 ,   930.18,
                  927.89,   959.72,   928.14,  1002.57,   953.22,   971.53,
                  947.54,   976.26,   988.16,   974.07,   943.67,   965.36,
                  925.48,   931.64,   932.47,   922.56,   927.99,   908.83,
                  930.23,   933.65,   980.25,   919.39,  1013.98,   940.23],
               [ 1506.69,  1339.79,  1317.25,  1392.53,  1331.65,  1340.17,
                 1320.15,  1436.71,  1310.51,  1482.64,  1371.34,  1446.15,
                 1394.84,  1445.87,  1416.5 ,  1434.16,  1418.19,  1421.35,
                 1354.89,  1383.46,  1323.45,  1343.07,  1360.87,  1325.57,
                 1342.55,  1389.99,  1379.43,  1301.34,  1517.04,  1374.91]])
    """
    domain_range = data.domain_range

    left, right = domain_range[0]
    interval_size = (right - left) / n_intervals
    integrated_data = []
    for i in np.arange(left, right, interval_size):
        interval = (i, i + interval_size)
        integrated_data = integrated_data + [
            data.integrate(interval=(interval,)),
        ]
    return np.asarray(integrated_data)


def _calculate_curves_occupation_(
    curve_y_coordinates: np.ndarray,
    curve_x_coordinates: np.ndarray,
    interval: Tuple,
) -> np.ndarray:
    y1, y2 = interval

    # Reshape original curves so they have one dimension less
    new_shape = curve_y_coordinates.shape[1::-1]
    curve_y_coordinates = curve_y_coordinates.reshape(
        new_shape[::-1],
    )

    # Calculate interval sizes on the X axis
    x_rotated = np.roll(curve_x_coordinates, 1)
    intervals_x_axis = curve_x_coordinates - x_rotated

    # Calculate which points are inside the interval given (y1,y2) on Y axis
    greater_than_y1 = curve_y_coordinates >= y1
    less_than_y2 = curve_y_coordinates <= y2
    inside_interval_bools = greater_than_y1 & less_than_y2

    # Correct booleans so they are not repeated
    bools_interval = np.roll(
        inside_interval_bools, 1, axis=1,
    ) & inside_interval_bools

    # Calculate intervals on X axis where the points are inside Y axis interval
    intervals_x_inside = np.multiply(bools_interval, intervals_x_axis)

    # Delete first element of each interval as it will be a negative number
    intervals_x_inside = np.delete(intervals_x_inside, 0, axis=1)

    return np.sum(intervals_x_inside, axis=1)


def occupation_measure(
    data: Union[FDataGrid, FDataBasis],
    intervals: np.ndarray,
    *,
    n_points: Union[int, None] = None,
) -> np.ndarray:
    r"""
    Calculate the occupation measure of a grid.

    It performs the following map.
        ..math:
            :math:`f_1(X) = |t: X(t)\in T_p|,\dots,|t: X(t)\in T_p|`

        where :math:`{T_1,\dots,T_p}` are disjoint intervals in
        :math:`\mathbb{R}` and | | stands for the Lebesgue measure.

        Args:
            data: FDataGrid or FDataBasis where we want to calculate
            the occupation measure.
            intervals: ndarray of tuples containing the
            intervals we want to consider. The shape should be
            (n_sequences,2)
            n_points: Number of points to evaluate in the domain.
            By default will be used the points defined on the FDataGrid.
            On a FDataBasis this value should be specified.
        Returns:
            ndarray of shape (n_intervals, n_samples)
            with the transformed data.

    Example:
        We will create the FDataGrid that we will use to extract
        the occupation measure
        >>> from skfda.representation import FDataGrid
        >>> import numpy as np
        >>> t = np.linspace(0, 10, 100)
        >>> fd_grid = FDataGrid(
        ...     data_matrix=[
        ...         t,
        ...         2 * t,
        ...         np.sin(t),
        ...     ],
        ...     grid_points=t,
        ... )

        Finally we call to the occupation measure function with the
        intervals that we want to consider. In our case (0.0, 1.0)
        and (2.0, 3.0). We need also to specify the number of points
        we want that the function takes into account to interpolate.
        We are going to use 501 points.
        >>> from skfda.exploratory.stats import occupation_measure
        >>> np.around(
        ...     occupation_measure(
        ...         fd_grid,
        ...         [(0.0, 1.0), (2.0, 3.0)],
        ...         n_points=501,
        ...     ),
        ...     decimals=2,
        ... )
        array([[ 1.  ,  0.5 ,  6.27],
               [ 0.98,  0.48,  0.  ]])

    """
    if isinstance(data, FDataBasis) and n_points is None:
        raise ValueError(
            "Number of points to consider, should be given "
            + " as an argument for a FDataBasis. Instead None was passed.",
        )

    for interval_check in intervals:
        y1, y2 = interval_check
        if y2 < y1:
            raise ValueError(
                "Interval limits (a,b) should satisfy a <= b. "
                + str(interval_check) + " doesn't",
            )

    if n_points is None:
        function_x_coordinates = data.grid_points[0]
        function_y_coordinates = data.data_matrix
    else:
        function_x_coordinates = np.arange(
            data.domain_range[0][0],
            data.domain_range[0][1],
            (data.domain_range[0][1] - data.domain_range[0][0]) / n_points,
        )
        function_y_coordinates = data(function_x_coordinates)

    return np.asarray([
        _calculate_curves_occupation_(  # noqa: WPS317
            function_y_coordinates,
            function_x_coordinates,
            interval,
        )
        for interval in intervals
    ])


def number_up_crossings(
    data: FDataGrid,
    levels: np.ndarray,
) -> np.ndarray:
    r"""
    Calculate the number of up crossings to a level of a FDataGrid.

    Let f_1(X) = N_i, where N_i is the number of up crossings of X
    to a level c_i \in \mathbb{R}, i = 1,\dots,p.

    Recall that the process X(t) is said to have an up crossing of c
    at :math:`t_0 > 0` if for some :math:`\epsilon >0`, X(t) $\leq$
    c if t :math:'\in (t_0 - \epsilon, t_0) and X(t) $\geq$ c if
    :math:`t\in (t_0, t_0+\epsilon)`.

    If the trajectories are differentiable, then
    :math:`N_i = card\{t \in[a,b]: X(t) = c_i, X' (t) > 0\}.`

        Args:
            data: FDataGrid where we want to calculate
            the number of up crossings.
            levels: sequence of numbers including the levels
            we want to consider for the crossings.
        Returns:
            ndarray of shape (n_levels, n_samples)\
            with the values of the counters.

    Example:

    We import the Medflies dataset and for simplicity we use
    the first 50 samples.
    >>> from skfda.datasets import fetch_medflies
    >>> dataset = fetch_medflies()
    >>> X = dataset['data'][:50]

    Then we decide the level we want to consider (in our case 40)
    and call the function with the dataset. The output will be the number of
    times each curve cross the level 40 growing.
    >>> from skfda.exploratory.stats import number_up_crossings
    >>> import numpy as np
    >>> number_up_crossings(X, np.asarray([40]))
    array([[[6],
            [3],
            [7],
            [7],
            [3],
            [4],
            [5],
            [7],
            [4],
            [6],
            [4],
            [4],
            [5],
            [6],
            [0],
            [5],
            [1],
            [6],
            [0],
            [7],
            [0],
            [6],
            [2],
            [5],
            [6],
            [5],
            [8],
            [4],
            [3],
            [7],
            [1],
            [3],
            [0],
            [5],
            [2],
            [7],
            [2],
            [5],
            [5],
            [5],
            [4],
            [4],
            [1],
            [2],
            [3],
            [5],
            [3],
            [3],
            [5],
            [2]]])
    """
    curves = data.data_matrix

    distances = np.asarray([
        level - curves
        for level in levels
    ])

    points_greater = distances >= 0
    points_smaller = distances <= 0
    points_smaller_rotated = np.roll(points_smaller, -1, axis=2)

    return np.sum(
        points_greater & points_smaller_rotated,
        axis=2,
    )
