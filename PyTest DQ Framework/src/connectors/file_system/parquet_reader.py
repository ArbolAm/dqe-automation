from pathlib import Path
from typing import List, Union

import pandas as pd


class ParquetReader:
	def process(
		self,
		target_path: Union[str, Path],
		include_subfolders: bool = False,
	) -> pd.DataFrame:
		path = Path(target_path)
		if not path.exists():
			raise FileNotFoundError(f"Parquet target path does not exist: {path}")

		if path.is_file():
			if path.suffix.lower() != ".parquet":
				raise ValueError(f"Expected a Parquet file, got: {path}")
			return pd.read_parquet(path, engine="pyarrow")

		parquet_files: List[Path]
		if include_subfolders:
			parquet_files = sorted(path.rglob("*.parquet"))
		else:
			parquet_files = sorted(path.glob("*.parquet"))

		if not parquet_files:
			raise FileNotFoundError(f"No Parquet files found under: {path}")

		dataframes = [
			pd.read_parquet(parquet_file, engine="pyarrow")
			for parquet_file in parquet_files
		]
		return pd.concat(dataframes, ignore_index=True, sort=False)
