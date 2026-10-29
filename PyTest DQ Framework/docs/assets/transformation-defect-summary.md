# Parquet Transformation Defect Summary

Run result: **8 failed, 7 passed, 2 deselected**. The report is `report.html` in this folder.

- `facility_name_min_time_spent_per_visit_date`: mapping expected 35,705 rows; Parquet returned 44,659. The mapped grain `(facility_name, visit_date)` has 17,908 rows involved in duplicates. Parquet contains extra rows and violates the expected grain.
- `facility_type_avg_time_spent_per_visit_date`: mapping expected 35,705 rows; Parquet returned 25,946, indicating 9,759 missing mapped groups.
- `patient_sum_treatment_cost_per_facility_type`: mapping expected 120 rows; Parquet returned 64, indicating 56 missing groups. Four `full_name` values are null. The report also shows a negative `sum_treatment_cost`, contrary to the mapping.

These are mapping-versus-Parquet discrepancies. Keep the mapping-derived expected queries unchanged while investigating the transformation. The build log identifies the failing checks but does not establish the exact pipeline operation responsible.
