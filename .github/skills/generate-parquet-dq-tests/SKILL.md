---
name: generate-parquet-dq-tests
description: >-
  Generates one PyTest data-quality test module for a mapped Parquet dataset
  using the team's test automation strategy. Invoke it when the framework is
  ready and a dataset module is requested; it does not modify framework,
  configuration, or Jenkins files.
disable-model-invocation: true
---

# Generate Parquet DQ tests

Complete this skill as **Step 2** of the PyTest DQ assignment. Read first:

- `PyTest DQ Framework/docs/test-automation-strategy.md` — **§5 Skill contract**, **§6 Test design standard**
- `docs/parquet-aggregated-data-mapping.md` — dataset definitions (expected SQL comes from here)

**Do not** paste expected SQL for the three named datasets into this skill.  
**Do not** instruct the agent to copy SQL from `data_dev/`.

When finished, every `TODO` below must be replaced. Run the **Skill review** checklist before using the skill to generate tests.

## When this skill applies

Use this skill when asked to create or update a dataset-level Parquet DQ test
module in the existing PyTest DQ Framework. The framework connectors, fixtures,
DQ library, `pytest.ini`, dependencies, and Jenkins job are prerequisites and
are outside this skill's scope.

Write only the requested module at
`PyTest DQ Framework/tests/dq checks/parquet_files/test_<dataset_name>.py`.
Do not create framework code or change `conftest.py`, `pytest.ini`, requirements,
Jenkins files, pipeline code, or unrelated tests. If the framework prerequisites
are missing or the request requires changing them, stop and explain the blocker
instead of expanding scope.

## Inputs you must have

Obtain all of the following before generating the module:

- The dataset folder name under `/parquet_data/`.
- Its definition in `docs/parquet-aggregated-data-mapping.md`: output columns,
  grain, measures and expressions, source tables and join path, and any filters.
- The author name and requirement or ticket ID for the module header.

The mapping file is authoritative for dataset columns and transformation intent.
If the mapping conflicts with the summary in the strategy document, follow the
mapping. If the requested dataset is absent, its mapping is ambiguous, or the
author or requirement ID is unavailable, ask for the missing information rather
than guessing or inventing expected behavior.

Never use `data_dev/`, its `queries.py`, parquet-loader SQL, or the generated
Parquet contents to derive the expected query. Do not copy the ETL query or
reverse-engineer its implementation.

## Hard rules

1. Generate one module per dataset at
  `PyTest DQ Framework/tests/dq checks/parquet_files/test_<dataset_name>.py`;
  retain the dataset folder's snake_case name.
2. PostgreSQL is the expected source: `source_data` uses `db_connection` and
  `get_data_sql`. Parquet is the actual target: `target_data` uses
  `parquet_reader.process('/parquet_data/<dataset_name>',
  include_subfolders=True)`. Never swap these roles.
3. Derive expected SQL only from the mapping. Use only its source columns, join
  path, grain, measures, expressions, and explicitly stated filters. Do not add
  pipeline-only `WHERE`, `UNION`, `CASE`, sign changes, or other logic.
4. Alias every expected output to the mapped Parquet column name. Keep the
  expected query's grain and output columns aligned with the mapping.
5. Keep this skill dataset-agnostic: do not include concrete expected SQL or
  named-dataset-specific test logic here.
6. Use the framework's `data_quality_library` methods; do not reimplement
  comparisons or pandas checks in the test module. Include smoke, completeness,
  count, uniqueness, and not-null checks for every dataset.
7. Check uniqueness using the mapped grain columns, so duplicate keys are
  detected even if measure values differ. Check not-null for every mapped
  output column.
8. Mark every test with `pytest.mark.parquet_data` and the dataset-specific
  marker. Add `pytest.mark.smoke` only to
  `test_check_dataset_is_not_empty`.
9. Do not edit framework/library code or run the suite unless explicitly asked.
  Never alter expected SQL just to make a failing comparison pass.

## Workflow

1. Read the strategy's sections 5 and 6 and the requested dataset entry in the
  mapping. Confirm the dataset name, output columns, grain, measures, joins,
  filters, author, and requirement ID are known.
2. Draft the expected PostgreSQL query from the mapping: select the mapped
  dimensions and measures, use the mapped join path, group by the mapped grain,
  and alias each result to its target column name. Apply only mapping-specified
  expressions and filters.
3. Create one test module using the template below. Populate its header, query,
  target path, duplicate-check grain columns, and not-null column list from the
  supplied inputs and mapping. Keep the fixture and check names as shown.
4. Apply the required markers to each test. The smoke marker belongs only on
  the not-empty test. Do not change registration or other framework files if a
  marker is not registered; report that as a prerequisite issue.
5. Review the module against the mapping and the Skill review checklist. Verify
  that source and target are not reversed and that every required check is
  present. Do not add SQL for other datasets to the skill or module.
6. Run pytest only when requested. If asked, use the strategy's
  `pytest tests -m "parquet_data"` invocation with the configured database
  options and HTML report path. Report failures as observed; do not change the
  expected query to force a green result.

## Template

Replace every angle-bracket placeholder with the requested dataset's mapped
values. The query placeholder is intentionally generic; write the SQL from the
mapping, not from an ETL implementation or a dataset-specific example.

```python
"""
Description: Data Quality checks for <dataset_name> dataset.
Requirement(s): <requirement_id>
Author(s): <author_name>
"""

import pytest


@pytest.fixture(scope='module')
def source_data(db_connection):
   source_query = """
   -- Expected query derived from the mapping: grain, measures, and joins.
   """
   return db_connection.get_data_sql(source_query)


@pytest.fixture(scope='module')
def target_data(parquet_reader):
   target_path = '/parquet_data/<dataset_name>'
   return parquet_reader.process(target_path, include_subfolders=True)


@pytest.mark.parquet_data
@pytest.mark.smoke
@pytest.mark.<dataset_name>
def test_check_dataset_is_not_empty(target_data, data_quality_library):
   data_quality_library.check_dataset_is_not_empty(target_data)


@pytest.mark.parquet_data
@pytest.mark.<dataset_name>
def test_check_data_completeness(source_data, target_data, data_quality_library):
   data_quality_library.check_data_completeness(source_data, target_data)


@pytest.mark.parquet_data
@pytest.mark.<dataset_name>
def test_check_count(source_data, target_data, data_quality_library):
   data_quality_library.check_count(source_data, target_data)


@pytest.mark.parquet_data
@pytest.mark.<dataset_name>
def test_check_uniqueness(target_data, data_quality_library):
   data_quality_library.check_duplicates(
      target_data, ['<grain_column_1>', '<grain_column_2>']
   )


@pytest.mark.parquet_data
@pytest.mark.<dataset_name>
def test_check_not_null_values(target_data, data_quality_library):
   data_quality_library.check_not_null_values(
      target_data, ['<mapped_output_column_1>', '<mapped_output_column_2>']
   )
```

## SQL derivation (generic)

Build the query from the mapping, one output column at a time:

- Read source table and column names and the required join keys from the mapping.
  Join only the tables needed to produce the mapped outputs.
- Select each mapped dimension at the mapped grain and include each mapped
  measure with its stated aggregate or expression. Put the grain dimensions in
  `GROUP BY` as required by the query.
- Apply the mapping's date, name, or other expression as specified, and alias
  the result to the exact output column name. Do not infer a different date
  granularity, name format, rounding rule, or numeric treatment from sample
  values or pipeline output.
- Add a filter only when the mapping explicitly defines it. A blank or absent
  mapping filter means no added filter.
- Select only the columns needed for the mapped Parquet output. Do not add
  implementation details from the pipeline, and do not adjust the query after
  seeing target data to make the comparison pass.

## After generation

Review the generated module against the mapping and section 6 of
`PyTest DQ Framework/docs/test-automation-strategy.md`. Confirm the file name
matches the dataset, the SQL aliases and grain match the mapped output, all five
checks are present, the duplicate check uses the mapped grain, and not-null
covers every output column.

Do not run pytest unless the user asks. If asked to run it, use the strategy's
registered-marker filter and database options. Preserve the expected query when
tests fail; report the failing check and its useful assertion detail so the
transformation or mapping can be investigated.

---

## Skill review (self-check before Step 3)

Reject your own skill if any of these are true:

- [ ] Contains concrete expected SQL for `facility_name_min_time_spent_per_visit_date`, `facility_type_avg_time_spent_per_visit_date`, or `patient_sum_treatment_cost_per_facility_type`
- [ ] Tells the agent to use `data_dev/` or parquet loader SQL
- [ ] Omits completeness, count, uniqueness, or not-null
- [ ] Swaps Postgres vs Parquet fixtures or generates trivial always-pass checks
- [ ] Any section still says `TODO`
