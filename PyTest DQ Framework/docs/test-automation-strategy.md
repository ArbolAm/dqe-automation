# Test Automation Strategy — PyTest DQ Framework

| Field | Value |
| --- | --- |
| System under test | `tafordqenetwork` pipeline: PostgreSQL 3NF tables → aggregated Parquet files |
| Framework | PyTest DQ Framework (`PyTest DQ Framework/`) |
| Related design | [dq-framework-design.md](dq-framework-design.md) |
| Audience | Data Quality Engineers implementing and extending the framework |

This document is the **strategy**. The design document is the **how the framework is built**. Dataset-level tests are generated from the **test design standard** in this TAS via a project skill — not from ad-hoc chat.

---

## 1. Purpose

Automate source-to-target validation of the Parquet transformation step:

- **Source / expected:** PostgreSQL 3NF tables (`facilities`, `visits`, `patients`), queried as the **intended** mapping.
- **Target / actual:** Parquet datasets written by the `data_dev` pipeline under `/parquet_data/<dataset_name>/`.

The goal is to detect transformation defects (wrong grain, extra/missing rows, duplicates, nulls, incorrect measures) — not to certify that the pipeline SQL and the tests are copies of each other.

---

## 2. Scope

### 2.1 In scope

- Completeness and count between expected SQL result and Parquet.
- Uniqueness (duplicates) and not-null on mapped columns.
- Smoke: target dataset is readable and not empty.
- PyTest framework: connectors, fixtures, reusable DQ library, HTML report, Jenkins job for the DQ tests.

### 2.2 Out of scope

- Validating `data_dev` data generation or 3NF load (covered by the pipeline itself).
- UI / API / Selenium / Robot checks.
- Performance, volume, or schema-evolution testing.
- Using transformation implementation (`data_dev/queries.py`, parquet loader SQL) as the expected result.

### 2.3 Datasets in the first increment

| Parquet dataset | Grain (expected) | Measures |
| --- | --- | --- |
| `facility_name_min_time_spent_per_visit_date` | `facility_name`, `visit_date` | `MIN(duration_minutes)` as `avg_time_spent` |
| `facility_type_avg_time_spent_per_visit_date` | `facility_type`, `visit_date` | `ROUND(AVG(duration_minutes), 2)` as `avg_time_spent` |
| `patient_sum_treatment_cost_per_facility_type` | `facility_type`, `full_name` | `SUM(treatment_cost)` as `sum_treatment_cost` |

Column names, joins, and grain come from [parquet-aggregated-data-mapping.md](../../docs/parquet-aggregated-data-mapping.md) (Project Environment). That file wins over this summary table if they differ. If mapping and pipeline SQL disagree, tests follow the **mapping**. Pipeline-only filters, `UNION`s, or `CASE` expressions that are not in the mapping must not appear in expected SQL.

---

## 3. Test approach

```text
mapping (business intent)
        │
        ▼
source_data  = Postgres query of the intended transformation
target_data  = ParquetReader.process('/parquet_data/<dataset>', include_subfolders=True)
        │
        ▼
smoke → completeness → count → uniqueness → not-null
```

- **Expected is independent of ETL code.** If the transformation is wrong, tests must fail.
- All-green against a known-buggy pipeline means expected SQL was copied from the pipeline, or checks are too weak. That is a failed strategy, not a passed run.
- Failures are **data defects** until proven otherwise. The report must explain root cause in the transformation, not “pytest assertion”.

### 3.1 Test types (mandatory per dataset)

| Type | Tests | Purpose |
| --- | --- | --- |
| Smoke | `test_check_dataset_is_not_empty` | File is present, readable, has rows |
| Completeness | `test_check_data_completeness`, `test_check_count` | Same rows/values and same row count as expected |
| Data quality | `test_check_uniqueness`, `test_check_not_null_values` | No duplicate grain; mapped columns are populated |

---

## 4. Implementation approach (AI-assisted)

Work is split so the framework, the team standard, and the checks stay reviewable.

| Step | Artifact | AI usage | Human owns |
| --- | --- | --- | --- |
| 1 | Framework (connectors, DQ library, `conftest`, `pytest.ini`, `requirements.txt`, `Jenkinsfile`) | Allowed (Chat / completions / Agent) against the **design** document | Structure matches design; no dataset test modules yet |
| 2 | Project skill `generate-parquet-dq-tests` | AI may help draft the skill text | Skill encodes **this TAS**, not dataset SQL |
| 3 | Three dataset test modules + run + defect report | Agent **must** use the skill | Mapping → SQL; interpretation of failures |

**Skill vs agent:** the skill is the reusable playbook (how this team writes a Parquet DQ module). Agent mode is the session that applies the skill. Do not replace the skill with a one-off chat prompt.

**Forbidden in step 1:** creating `tests/dq checks/parquet_files/test_<dataset>.py` for the three datasets. `tests/test_examples.py` is the only test-shape sample until the skill exists.

---

## 5. Skill contract

The project skill is a versioned artifact. Review it like code.

### 5.1 Location and identity

| Item | Value |
| --- | --- |
| Path | `.github/skills/generate-parquet-dq-tests/SKILL.md` |
| Name | `generate-parquet-dq-tests` |
| Invoke | Explicitly (name the skill in Agent / Copilot Chat) |

### 5.2 Input (provided by the user or read from mapping)

- Dataset name (folder under `/parquet_data/`).
- Mapping: output columns, grain, measures, join path, optional filters **from mapping only**.
- Author / requirement id for the file header.

### 5.3 Output

One PyTest module per dataset:

`PyTest DQ Framework/tests/dq checks/parquet_files/test_<dataset_name>.py`

The module must follow section 6. The skill must not edit framework library code unless the user explicitly asks.

### 5.4 Rules the skill must enforce

1. **Dataset-agnostic.** No hardcoded SQL for the three known datasets inside `SKILL.md`. The skill explains *how* to derive SQL from a mapping.
2. **Source = Postgres, target = Parquet.** Do not swap fixtures (the sample `test_examples.py` has placeholders and mixed direction — follow this TAS, not the placeholder names).
3. **Do not read `data_dev/`** (especially `queries.py` and parquet-loader SQL) to build expected queries.
4. **Do not add** `UNION` / extra `WHERE` / `CASE` / sign flips unless they are in the mapping.
5. Aliases and grain of `source_data` must match the Parquet schema / mapping names.
6. `target_path` is `/parquet_data/<dataset_name>` with `include_subfolders=True`.
7. Markers: `parquet_data`, dataset-specific mark, `smoke` only on the not-empty test.
8. Not-null column list = mapped output columns for that dataset.

### 5.5 Skill review (reject if)

- Contains concrete expected SQL for a named parquet dataset.
- Tells the agent to copy SQL from `data_dev`.
- Omits completeness, count, uniqueness, or not-null.
- Generates tests that always pass (empty asserts, comparing target to itself).

---

## 6. Test design standard

This section is the source of truth for the skill.

### 6.1 Naming and placement

- File: `test_<dataset_name>.py` (same snake_case as the parquet folder).
- Folder: `tests/dq checks/parquet_files/`.
- One dataset per file. Do not put three datasets in one module.

### 6.2 Module skeleton

```python
"""
Description: Data Quality checks for <dataset_name> dataset.
Requirement(s): TICKET-1234
Author(s): <name>
"""

import pytest


@pytest.fixture(scope='module')
def source_data(db_connection):
    source_query = """
    -- expected query derived from mapping (grain + measures + joins)
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
    data_quality_library.check_duplicates(target_data)


@pytest.mark.parquet_data
@pytest.mark.<dataset_name>
def test_check_not_null_values(target_data, data_quality_library):
    data_quality_library.check_not_null_values(target_data, ['<col_1>', '<col_2>', '<col_3>'])
```

### 6.3 How to derive expected SQL from mapping

1. Identify 3NF tables and join keys (`visits` → `facilities` / `patients`).
2. List **dimensions** (GROUP BY / grain) from the mapping.
3. List **measures** (MIN / AVG / SUM / CONCAT, including required rounding).
4. Alias every output column to the mapping / Parquet name.
5. Include a mapping filter only if the mapping states it.
6. Stop. Do not “fix” the query to match parquet preview, and do not read ETL SQL.

### 6.4 Library methods (framework)

Implemented in `src/data_quality/data_quality_validation_library.py`. Tests **call** these methods; they do not reimplement pandas logic in the test body.

| Method | Meaning |
| --- | --- |
| `check_dataset_is_not_empty(df)` | Target has rows |
| `check_data_completeness(df_expected, df_actual)` | Same data, row order ignored |
| `check_count(df_expected, df_actual)` | Same number of rows |
| `check_duplicates(df, column_names=None)` | No duplicate rows (or subset of columns) |
| `check_not_null_values(df, column_names)` | Named columns have no nulls |

Assert messages must include enough detail to debug (mismatched rows, counts, column names with nulls).

### 6.5 Markers and run filter

Register markers used by the suite in `pytest.ini`. Production DQ run:

```bash
pytest tests -m "parquet_data" --db_host="localhost" --db_port="5434" \
  --db_name="mydatabase" --db_user="..." --db_password="..." \
  --html=html_report/report.html
```

`example` tests must not be selected by `-m parquet_data`.

---

## 7. Framework (summary)

Full design: [dq-framework-design.md](dq-framework-design.md).

| Component | Responsibility |
| --- | --- |
| `PostgresConnectorContextManager` | Session DB access; `get_data_sql` → DataFrame |
| `ParquetReader` | Read dataset folder including partition subfolders |
| `DataQualityLibrary` | Reusable asserts |
| `conftest.py` | CLI `--db_*`, session fixtures `db_connection`, `parquet_reader`, `data_quality_library` |
| `Jenkinsfile` | Install deps, run pytest, archive `html_report/**`, publish HTML |

Credentials: Jenkins Credentials Store (`POSTGRES_SECRET`). No passwords in repo.

---

## 8. Environments

| Environment | Postgres | Parquet path | Who runs |
| --- | --- | --- | --- |
| Local | `localhost:5434` | `/parquet_data/...` inside the Jenkins/data network layout used by the lab | Engineer |
| Jenkins agent | host `postgres`, port `5432` | same `/parquet_data/...` in the container network | CI |

Prerequisites: lab containers up; `data_dev` pipeline already produced the three parquet folders.

---

## 9. CI/CD and reporting

- Dedicated Jenkins job, `Jenkinsfile` stored in `PyTest DQ Framework/`.
- Stages: install → pytest (`-m parquet_data`) → archive HTML → `publishHTML`.
- HTML report is the evidence artifact (pass/fail, assertion text).
- Pipeline may be configured to keep the job green while the test stage fails (`catchError`); **assessment looks at the report**, not only the job ball color.

---

## 10. Defect reporting

For each failed check, record:

1. Dataset name and test name.
2. What the mapping expected.
3. What the parquet actually contains (from the assert message / a sample).
4. Root cause in the **transformation** (not “test is wrong”), if that is the case.

Do not silently change expected SQL to make the suite green.

---

## 11. Roles

| Role | Owns |
| --- | --- |
| DQ engineer | Mapping → expected SQL, skill quality, defect report |
| AI assistant | Boilerplate framework code; test modules **only when the skill is applied** |
| Reviewer / mentor | Design compliance, skill contract, that failures match mapping-vs-pipeline — not pixel match to a golden repo |

---

## 12. Entry and exit criteria

**Entry**

- Fork of the lab repo; containers running; `data_dev` has written the three parquet datasets.
- Mapping in `docs/parquet-aggregated-data-mapping.md` (Project Environment).

**Exit**

1. Framework matches the design (connectors, library, fixtures, CLI, Jenkins, HTML).
2. Skill exists at the path in section 5 and passes the skill review.
3. Three dataset modules exist, generated via the skill, with all mandatory test types.
4. Suite executed; HTML report stored.
5. Defect report explains failing checks as transformation issues where parquet disagrees with mapping.

**Not exit:** an all-green parquet run with no analysis. Green is acceptable only if expected SQL is mapping-correct **and** parquet truly matches — which must be justified, not assumed.

---

## 13. Document control

| Version | Date | Description |
| --- | --- | --- |
| 0.1 | 2026-09-07 | Initial TAS: scope, mapping-based expected, AI/skill contract, test design standard |

**Related**

- [dq-framework-design.md](dq-framework-design.md) — architecture, folders, fixtures, usage, dependencies.
- [parquet-aggregated-data-mapping.md](../../docs/parquet-aggregated-data-mapping.md) — data mapping for the three parquet datasets.
