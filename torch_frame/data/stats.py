from enum import Enum
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd

import torch_frame
from torch_frame.data.mapper import MultiCategoricalTensorMapper
from torch_frame.typing import Series


class StatType(Enum):
    r"""The different types for column statistics.

    Attributes:
        MEAN: The average value of a numerical column.
        STD: The standard deviation of a numerical column.
        QUANTILES: The minimum, first quartile, median, third quartile,
            and the maximum of a numerical column.
        COUNT: The count of each category in a categorical column.
        MULTI_COUNT: The count of each category in a multi-categorical
            column.
        YEAR_RANGE: The range of years in a timestamp column.
    """

    # Numerical:
    MEAN = "MEAN"
    STD = "STD"
    QUANTILES = "QUANTILES"

    # categorical:
    COUNT = "COUNT"

    # multicategorical:
    MULTI_COUNT = "MULTI_COUNT"

    # timestamp
    YEAR_RANGE = "YEAR_RANGE"

    # text_embedded (Also, embedding)
    # Note: For text_embedded, this stats is computed in
    # dataset._update_col_stats, not here.
    EMB_DIM = "EMB_DIM"

    @staticmethod
    def stats_for_stype(stype: torch_frame.stype) -> List["StatType"]:
        stats_type = {
            torch_frame.numerical: [
                StatType.MEAN,
                StatType.STD,
                StatType.QUANTILES,
            ],
            torch_frame.categorical: [StatType.COUNT],
            torch_frame.multicategorical: [StatType.MULTI_COUNT],
            torch_frame.sequence_numerical: [
                StatType.MEAN,
                StatType.STD,
                StatType.QUANTILES,
            ],
            torch_frame.timestamp: [
                StatType.YEAR_RANGE,
            ],
        }
        return stats_type.get(stype, [])

    def compute(
        self,
        ser: Series,
        sep: Optional[str] = None,
        time_format: Optional[str] = None,
    ) -> Any:
        if self == StatType.MEAN:
            flattened = np.hstack(np.hstack(ser.values))
            finite_mask = np.isfinite(flattened)
            if not finite_mask.any():
                # NOTE: We may just error out here if eveything is NaN
                return np.nan
            return np.mean(flattened[finite_mask]).item()

        elif self == StatType.STD:
            flattened = np.hstack(np.hstack(ser.values))
            finite_mask = np.isfinite(flattened)
            if not finite_mask.any():
                return np.nan
            return np.std(flattened[finite_mask]).item()

        elif self == StatType.QUANTILES:
            flattened = np.hstack(np.hstack(ser.values))
            finite_mask = np.isfinite(flattened)
            if not finite_mask.any():
                return [np.nan, np.nan, np.nan, np.nan, np.nan]
            return np.quantile(
                flattened[finite_mask],
                q=[0, 0.25, 0.5, 0.75, 1],
            ).tolist()

        elif self == StatType.COUNT:
            count = ser.value_counts(ascending=False)
            return count.index.tolist(), count.values.tolist()

        elif self == StatType.MULTI_COUNT:
            assert sep is not None
            ser = ser.apply(lambda row: MultiCategoricalTensorMapper.
                            split_by_sep(row, sep))
            ser = ser.explode().dropna()
            count = ser.value_counts(ascending=False)
            return count.index.tolist(), count.values.tolist()

        elif self == StatType.YEAR_RANGE:
            ser = pd.to_datetime(ser, format=time_format)
            year_range = ser.dt.year.values
            return [min(year_range), max(year_range)]


_default_values = {
    StatType.MEAN: np.nan,
    StatType.STD: np.nan,
    StatType.QUANTILES: [np.nan, np.nan, np.nan, np.nan, np.nan],
    StatType.COUNT: ([], []),
    StatType.MULTI_COUNT: ([], []),
    StatType.YEAR_RANGE: [np.nan, np.nan],
    StatType.EMB_DIM: -1,
}


def compute_col_stats(
    ser: Series,
    stype: torch_frame.stype,
    sep: Optional[str] = None,
    time_format: Optional[str] = None,
) -> Dict[StatType, Any]:
    if stype == torch_frame.numerical:
        ser = ser.mask(ser.isin([np.inf, -np.inf]), np.nan)

    if ser.isnull().all():
        # NOTE: We may just error out here if eveything is NaN
        stats = {
            stat_type: _default_values[stat_type]
            for stat_type in StatType.stats_for_stype(stype)
        }
    else:
        stats = {
            stat_type: stat_type.compute(ser.dropna(), sep, time_format)
            for stat_type in StatType.stats_for_stype(stype)
        }

    return stats
