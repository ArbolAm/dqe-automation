from typing import List, Optional

import pandas as pd


class DataQualityLibrary:
    @staticmethod
    def check_dataset_is_not_empty(df: pd.DataFrame) -> None:
        assert df is not None, "Dataset is None."
        assert not df.empty, "Dataset is empty."

    @staticmethod
    def check_data_completeness(
        df_expected: pd.DataFrame,
        df_actual: pd.DataFrame,
    ) -> None:
        expected_columns = list(df_expected.columns)
        actual_columns = list(df_actual.columns)
        assert set(expected_columns) == set(actual_columns), (
            "Data completeness failed: column mismatch. "
            f"Expected columns: {expected_columns}; actual columns: {actual_columns}."
        )
        assert len(df_expected) == len(df_actual), (
            "Data completeness failed: row-count mismatch. "
            f"Expected {len(df_expected)} rows; actual {len(df_actual)} rows."
        )

        expected_sorted = (
            df_expected.sort_values(by=expected_columns, kind="mergesort")
            .reset_index(drop=True)
        )
        actual_sorted = (
            df_actual.reindex(columns=expected_columns)
            .sort_values(by=expected_columns, kind="mergesort")
            .reset_index(drop=True)
        )
        try:
            pd.testing.assert_frame_equal(
                expected_sorted,
                actual_sorted,
                check_dtype=False,
                check_exact=True,
            )
        except AssertionError as error:
            raise AssertionError(
                "Data completeness failed: source and Parquet values differ.\n"
                f"{error}"
            ) from error

    @staticmethod
    def check_count(
        df_expected: pd.DataFrame,
        df_actual: pd.DataFrame,
    ) -> None:
        assert len(df_expected) == len(df_actual), (
            "Row-count mismatch: "
            f"expected {len(df_expected)} rows, got {len(df_actual)} rows."
        )

    @staticmethod
    def check_duplicates(
        df: pd.DataFrame,
        column_names: Optional[List[str]] = None,
    ) -> None:
        columns = column_names or list(df.columns)
        missing_columns = [column for column in columns if column not in df.columns]
        assert not missing_columns, (
            f"Duplicate check references missing columns: {missing_columns}."
        )

        duplicate_rows = df[df.duplicated(subset=columns, keep=False)]
        assert duplicate_rows.empty, (
            f"Found {len(duplicate_rows)} duplicate rows using columns {columns}. "
            f"Sample:\n{duplicate_rows.head(10).to_string(index=False)}"
        )

    @staticmethod
    def check_not_null_values(
        df: pd.DataFrame,
        column_names: Optional[List[str]] = None,
    ) -> None:
        columns = column_names or list(df.columns)
        missing_columns = [column for column in columns if column not in df.columns]
        assert not missing_columns, (
            f"Not-null check references missing columns: {missing_columns}."
        )

        null_counts = df[columns].isna().sum()
        null_counts = null_counts[null_counts > 0]
        assert null_counts.empty, (
            "Null values found in mapped columns: "
            f"{null_counts.to_dict()}."
        )

    @staticmethod
    def check_data_full_data_set(
        df_expected: pd.DataFrame,
        df_actual: pd.DataFrame,
    ) -> None:
        DataQualityLibrary.check_data_completeness(df_expected, df_actual)
