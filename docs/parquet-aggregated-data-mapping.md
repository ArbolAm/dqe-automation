# Parquet files with aggregated data — data mapping

Part of the [project environment](project-environment.md) (pipeline step 4).

Parquet files are created based on Postgres DB data.

## `facility_name_min_time_spent_per_visit_date`

| Target column | Transformation | Source | Source column | Sample | Comments |
| --- | --- | --- | --- | --- | --- |
| `facility_name` | — | `table.facilities` | `facility_name` | Maynard, Cole and Ortiz | grouping, not null |
| `visit_date` | — | `table.visits` | `visit_timestamp` | 2005-09-22 | grouping, not null |
| `min_time_spent` | `min(duration_minutes)` | `table.visits` | `duration_minutes` | 16 | not null |

- **Filters:** —
- **Partitioned:** by `visit_date` (year-month; day is excluded)

## `facility_type_avg_time_spent_per_visit_date`

| Target column | Transformation | Source | Source column | Sample | Comments |
| --- | --- | --- | --- | --- | --- |
| `facility_type` | — | `table.facilities` | `facility_type` | Hospital | grouping, not null |
| `visit_date` | — | `table.visits` | `visit_timestamp` | 2005-09-22 | grouping, not null |
| `avg_time_spent` | `avg(duration_minutes)` | `table.visits` | `duration_minutes` | 26.00 | rounding to two decimal places, not null |

- **Filters:** —
- **Partitioned:** by `visit_date` (year-month; day is excluded)

## `patient_sum_treatment_cost_per_facility_type`

| Target column | Transformation | Source | Source column | Sample | Comments |
| --- | --- | --- | --- | --- | --- |
| `facility_type` | — | `table.facilities` | `facility_type` | Clinic | grouping, not null |
| `full_name` | `first_name` + `last_name` | `table.patients` | `last_name`, `first_name` | Michael Cruz | format: `<first_name><sepparated_by_space><last_name>`, grouping, not null |
| `sum_treatment_cost` | `SUM(v.treatment_cost)` | `table.visits` | `treatment_cost` | 1632426.06 | Can't be negative, not null |

- **Filters:** —
- **Partitioned:** by `facility_type`
