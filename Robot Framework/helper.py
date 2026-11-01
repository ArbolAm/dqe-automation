from collections import Counter
from datetime import date
from pathlib import Path

import pandas as pd
from selenium.webdriver.common.by import By


_COLUMN_NAMES = {
	"facility type": "facility_type",
	"visit date": "visit_date",
	"average time spent": "avg_time_spent",
}


def get_local_file_url(file_path):
	"""Return a browser-safe file URL for a local path."""
	return Path(file_path).resolve().as_uri()


def read_html_table(table_element, filter_date=None):
	"""Read the displayed Plotly table from its Selenium-located SVG element."""
	column_elements = table_element.find_elements(By.CSS_SELECTOR, ".y-column")
	if not column_elements:
		raise ValueError("The located report element contains no table columns")

	data = {}
	for column_element in column_elements:
		cell_elements = column_element.find_elements(By.CSS_SELECTOR, ".column-cell")
		cell_values = [
			(cell.get_attribute("textContent") or "").strip()
			for cell in cell_elements
		]
		header_index = next(
			(
				index
				for index, value in enumerate(cell_values)
				if value.strip().lower() in _COLUMN_NAMES
			),
			None,
		)
		if header_index is None:
			raise ValueError("A table column is missing its header cell")

		header = _COLUMN_NAMES[cell_values[header_index].strip().lower()]
		if header in data:
			raise ValueError(f"Duplicate table column: {header}")
		data[header] = cell_values[:header_index] + cell_values[header_index + 1:]

	if len({len(values) for values in data.values()}) != 1:
		raise ValueError("The report table columns contain different row counts")
	frame = pd.DataFrame(data)
	return filter_dataframe_by_date(frame, filter_date)


def read_partitioned_parquet(parquet_folder, filter_date=None):
	"""Read partitioned Parquet data, optionally selecting one visit date."""
	base_path = Path(parquet_folder)
	parsed_date = _parse_filter_date(filter_date) if filter_date else None
	partition_path = (
		base_path / f"partition_date={parsed_date:%Y-%m}"
		if parsed_date
		else base_path
	)
	parquet_files = sorted(
		partition_path.glob("*.parquet")
		if parsed_date
		else partition_path.rglob("*.parquet")
	)
	if not parquet_files:
		raise FileNotFoundError(f"No Parquet files found in {partition_path}")

	frame = pd.concat((pd.read_parquet(path) for path in parquet_files), ignore_index=True)
	frame = _normalize_column_names(frame)
	if "visit_date" not in frame.columns:
		raise ValueError(f"No visit_date column found in {parquet_folder}")

	if not parsed_date:
		return frame.reset_index(drop=True)

	row_dates = pd.to_datetime(frame["visit_date"], errors="coerce").dt.strftime("%Y-%m-%d")
	return frame.loc[row_dates == parsed_date.isoformat()].reset_index(drop=True)


def filter_dataframe_by_date(frame, filter_date=None):
	"""Filter a DataFrame to the requested visit date when one is provided."""
	normalized_frame = _normalize_column_names(frame)
	if not filter_date:
		return normalized_frame.reset_index(drop=True)
	parsed_date = _parse_filter_date(filter_date)
	if "visit_date" not in normalized_frame.columns:
		raise ValueError("No visit_date column found in the report table")

	row_dates = pd.to_datetime(normalized_frame["visit_date"], errors="coerce").dt.strftime("%Y-%m-%d")
	return normalized_frame.loc[row_dates == parsed_date.isoformat()].reset_index(drop=True)


def compare_dataframes(expected, actual):
	"""Return missing, unexpected, or schema differences between two frames."""
	expected_frame = _normalize_values(_normalize_column_names(expected))
	actual_frame = _normalize_values(_normalize_column_names(actual))
	if list(expected_frame.columns) != list(actual_frame.columns):
		return [
			f"Column mismatch: expected {list(expected_frame.columns)!r}, "
			f"actual {list(actual_frame.columns)!r}"
		]

	expected_rows = Counter(expected_frame.itertuples(index=False, name=None))
	actual_rows = Counter(actual_frame.itertuples(index=False, name=None))
	differences = []
	for row, count in (expected_rows - actual_rows).items():
		differences.extend([f"Missing from Parquet: {row!r}"] * count)
	for row, count in (actual_rows - expected_rows).items():
		differences.extend([f"Unexpected in Parquet: {row!r}"] * count)
	return differences


def _normalize_column_names(frame):
	normalized = frame.copy()
	renamed_columns = {}
	for column in normalized.columns:
		normalized_name = str(column).strip().lower().replace("_", " ")
		renamed_columns[column] = _COLUMN_NAMES.get(
			normalized_name,
			normalized_name.replace(" ", "_"),
		)
	return normalized.rename(columns=renamed_columns)


def _normalize_values(frame):
	normalized = frame.copy()
	if "visit_date" in normalized.columns:
		normalized["visit_date"] = pd.to_datetime(
			normalized["visit_date"], errors="coerce"
		).dt.strftime("%Y-%m-%d")
	if "avg_time_spent" in normalized.columns:
		normalized["avg_time_spent"] = pd.to_numeric(
			normalized["avg_time_spent"], errors="coerce"
		)
	if "facility_type" in normalized.columns:
		normalized["facility_type"] = normalized["facility_type"].astype(str)
	return normalized


def _parse_filter_date(filter_date):
	parsed_date = date.fromisoformat(str(filter_date))
	if parsed_date.isoformat() != str(filter_date):
		raise ValueError("FILTER_DATE must use YYYY-MM-DD format")
	return parsed_date
