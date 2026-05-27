# TFT Analytics System - Full Stack Big Data Dashboard

## TL;DR

> **Quick Summary**: Xây dựng hệ thống phân tích dữ liệu TFT end-to-end từ ETL đến dashboard visualization, với 5 trang phân tích chính (Hồ sơ người chơi, Top Meta, Phân tích Tướng, Phân tích Đồ, Phân tích Chung), AI gợi ý đội hình, và trực quan hóa tối đa bằng ECharts.
> 
> **Deliverables**:
> - Spark ETL job hoàn chỉnh (calculated metrics: win rate, avg placement, pick rate, top 4 rate, per-unit/trait/item stats)
> - Airflow DAG orchestration (hourly batch)
> - Elasticsearch indices & mappings (6 indices)
> - FastAPI backend (15+ endpoints)
> - React + Vite + ECharts frontend (5 dashboard pages với 20+ charts)
> - PyTorch recommendation model (gợi ý đội hình)
> - Docker Compose deployment cho toàn bộ stack
> - Cleanup code từ project trước
> 
> **Estimated Effort**: Large
> **Parallel Execution**: YES - 5 waves
> **Critical Path**: Task 1 (Cleanup) → Task 3 (ETL) → Task 7 (Backend) → Task 9-13 (Dashboard pages) → Final Verification

---

## Context

### Original Request
Xây dựng hệ thống phân tích dữ liệu TFT với data crawl từ Riot API, trực quan hóa tối đa trên giao diện, theo 5 trang chính trong TFT_guide.pdf.

### Interview Summary
**Key Discussions**:
- Frontend: React + Vite + Apache ECharts (max visualization capability)
- Data freshness: Batch hourly via Airflow (stable, maintainable)
- Hard metrics: Cần thiết kế công thức cho meta score, flex score, item build accuracy
- AI/ML: PyTorch recommendation model cho team composition suggestion
- Testing: No unit tests, Agent QA scenarios only
- Deployment: Docker Compose

**Research Findings**:
- Crawler (tft_crawler.py) đang hoạt động, gửi data vào Kafka topic `tft-raw-matches`
- spark_processor.py chỉ做了 console output, không có Elasticsearch write, không có meaningful aggregations → cần viết lại hoàn toàn
- .env, check_data.py, mysql-connector-j/ là leftover từ ClassicModels assignment → cần cleanup
- etl_job.py là thư mục rỗng (directory, not file) → cần xóa và tạo file mới
- Sample data: TFT Set 17, queue_id 1100, nhiều fields phong phú (traits, units, items, augments, placement, gold_left, etc.)

### Metis Review
**Identified Gaps** (addressed):
- Cross-project contamination: .env có MySQL/Iceberg config từ project trước, check_data.py query classicmodels → Cleanup task added (Task 1)
- spark_processor.py useless for production (console-sink, no ES write) → Rewrite completely (Task 3)
- etl_job.py empty directory → Delete and recreate as file (Task 1)
- No Elasticsearch mapping design → Task 4 will define ES indices
- Missing Riot TFT static data integration (champion names, trait names, item names) → Task 2 will include static data mapping
- Augments field may be empty/null in some match versions → ETL handles null/missing augments gracefully

---

## Work Objectives

### Core Objective
Xây dựng hệ thống phân tích dữ liệu TFT hoàn chỉnh: từ ETL pipeline xử lý dữ liệu thô thành metrics phân tích, đến API backend phục vụ dữ liệu, đến frontend dashboard trực quan hóa với 5 trang phân tích chính.

### Concrete Deliverables
- Cleaned project directory (remove ClassicModels artifacts)
- Spark ETL job producing calculated metrics → Elasticsearch
- Airflow DAG running ETL hourly
- Elasticsearch with 6 indices: player_stats, comp_meta, champion_stats, item_stats, match_details, team_recommendations
- FastAPI with 15+ REST endpoints serving dashboard data
- React + Vite + ECharts dashboard with 5 pages and 20+ chart components
- PyTorch recommendation model for team composition suggestions
- Docker Compose for full stack deployment

### Definition of Done
- [ ] Crawler data flows through Kafka → Spark ETL → Elasticsearch
- [ ] Airflow DAG triggers ETL successfully on schedule
- [ ] All 5 dashboard pages render with real data (not mock)
- [ ] ECharts visualizations display interactive charts (hover, filter, drill-down)
- [ ] Team recommendation API returns valid suggestions
- [ ] Docker Compose starts entire stack with single `docker-compose up`

### Must Have
- 5 dashboard pages as described in TFT_guide.pdf
- ECharts visualizations: bar charts, heatmaps, treemaps, line charts, sunburst charts, radar charts
- Player profile with filter by game count (all/20/50/100 games)
- Composition meta page with core unit identification
- Champion analysis with per-build stats
- Item analysis with cross-reference to champions
- General analysis with champion+item filter for optimal builds
- Batch hourly data refresh via Airflow
- Docker Compose deployment

### Must NOT Have (Guardrails)
- **NO real-time streaming dashboard** - batch hourly only
- **NO user authentication/authorization** - public read-only dashboard
- **NO mobile app** - web dashboard only
- **NO unit/integration test framework** - Agent QA verification only
- **NO modifications to existing tft_crawler.py** - it works, don't touch it
- **NO ClassicModels artifacts** - remove all leftover files from previous project
- **NO hardcoded API keys** - use environment variables
- **NO mock/placeholder data in production** - all charts must render real data from ES

---

## Verification Strategy (MANDATORY)

> **ZERO HUMAN INTERVENTION** - ALL verification is agent-executed. No exceptions.

### Test Decision
- **Infrastructure exists**: NO (no test framework)
- **Automated tests**: None (per user choice)
- **Framework**: None
- **Agent-Executed QA**: ALWAYS - every task verified by running, curling, browser-testing

### QA Policy
Every task MUST include agent-executed QA scenarios.
Evidence saved to `.sisyphus/evidence/task-{N}-{scenario-slug}.{ext}`.

- **Frontend/UI**: Use Playwright - Navigate, click filters, assert chart renders, screenshot
- **API/Backend**: Use Bash (curl) - Send requests, assert JSON fields and status codes
- **ETL/Pipeline**: Use Bash - Check Elasticsearch indices, verify data counts
- **Infrastructure**: Use Bash - Docker container status, port availability

---

## Execution Strategy

### Parallel Execution Waves

```
Wave 1 (Foundation - cleanup + data models):
├── Task 1: Project cleanup & scaffolding [quick]
├── Task 2: TFT static data & reference tables [quick]
├── Task 3: Spark ETL job - core metrics calculation [deep]
├── Task 4: Elasticsearch setup & index mappings [quick]
├── Task 5: Docker Compose - infrastructure services [quick]
├── Task 6: FastAPI project skeleton & health endpoints [quick]

Wave 2 (Core services - after Wave 1):
├── Task 7: FastAPI analytics endpoints [unspecified-high]
├── Task 8: Airflow DAG - ETL orchestration [quick]
├── Task 9: React + Vite project setup & layout shell [visual-engineering]
├── Task 10: PyTorch recommendation model - training pipeline [ultrabrain]

Wave 3 (Dashboard pages - after Wave 2):
├── Task 11: Player Profile page (Hồ sơ người chơi) [visual-engineering]
├── Task 12: Top Meta Compositions page (Đội hình meta) [visual-engineering]
├── Task 13: Champion Analysis page (Phân tích tướng) [visual-engineering]
├── Task 14: Item Analysis page (Phân tích đồ) [visual-engineering]
├── Task 15: General Analysis page (Phân tích chung) [visual-engineering]

Wave 4 (Integration):
├── Task 16: Recommendation API integration [unspecified-high]
├── Task 17: Cross-page navigation & global filters [quick]
├── Task 18: Docker Compose - full stack integration [unspecified-high]

Wave FINAL (Verification - after ALL tasks):
├── Task F1: Plan compliance audit (oracle)
├── Task F2: Code quality review (unspecified-high)
├── Task F3: Real manual QA (unspecified-high)
└── Task F4: Scope fidelity check (deep)

Critical Path: Task 1 → Task 3 → Task 7 → Task 11-15 → F1-F4
Parallel Speedup: ~60% faster than sequential
Max Concurrent: 6 (Wave 1)
```

### Dependency Matrix

| Task | Depends On | Blocks | Wave |
|------|-----------|--------|------|
| 1 | - | 3, 4, 5, 6 | 1 |
| 2 | - | 3, 7 | 1 |
| 3 | 1, 2 | 7 | 1 |
| 4 | 1 | 7 | 1 |
| 5 | 1 | 8, 18 | 1 |
| 6 | 1 | 7 | 1 |
| 7 | 3, 4, 6 | 11-15 | 2 |
| 8 | 3, 5 | - | 2 |
| 9 | - | 11-15 | 2 |
| 10 | 2 | 16 | 2 |
| 11 | 7, 9 | 17 | 3 |
| 12 | 7, 9 | 17 | 3 |
| 13 | 7, 9 | 17 | 3 |
| 14 | 7, 9 | 17 | 3 |
| 15 | 7, 9 | 17 | 3 |
| 16 | 10, 7 | 17 | 4 |
| 17 | 11-15, 16 | 18 | 4 |
| 18 | 5, 17 | F1-F4 | 4 |

### Agent Dispatch Summary

- **Wave 1**: 6 tasks - T1 `quick`, T2 `quick`, T3 `deep`, T4 `quick`, T5 `quick`, T6 `quick`
- **Wave 2**: 4 tasks - T7 `unspecified-high`, T8 `quick`, T9 `visual-engineering`, T10 `ultrabrain`
- **Wave 3**: 5 tasks - T11-T15 all `visual-engineering`
- **Wave 4**: 3 tasks - T16 `unspecified-high`, T17 `quick`, T18 `unspecified-high`
- **FINAL**: 4 tasks - F1 `oracle`, F2 `unspecified-high`, F3 `unspecified-high`, F4 `deep`

---

## TODOs

- [x] 1. **Project Cleanup & Scaffolding**

  **What to do**:
  - Delete ClassicModels artifacts: `check_data.py`, `mysql-connector-j-8.0.33.jar/` directory, `etl_job.py/` directory (it's a dir not a file)
  - Update `.env` file: remove MySQL config, update Spark app name from `ClassicModels_ETL_Lakehouse` to `TFT_Analytics_ETL`, update Iceberg catalog config for TFT use, update MINIO configs for TFT bucket
  - Create project directory structure:
    ```
    backend/
    ├── app/
    │   ├── __init__.py
    │   ├── main.py
    │   ├── config.py
    │   ├── models/
    │   ├── routes/
    │   └── services/
    ├── requirements.txt
    └── Dockerfile
    frontend/
    ├── src/
    │   ├── components/
    │   ├── pages/
    │   ├── hooks/
    │   ├── api/
    │   └── App.tsx
    ├── package.json
    └── Dockerfile
    etl/
    ├── spark_jobs/
    │   └── tft_etl.py (rewrite spark_processor.py)
    ├── dags/
    │   └── tft_etl_dag.py
    ├── config/
    │   └── es_mappings/
    └── Dockerfile
    ml/
    ├── train.py
    ├── model.py
    ├── predict.py
    └── Dockerfile
    docker-compose.yml
    ```
  - Create `docker-compose.yml` skeleton with service definitions for: Elasticsearch, Kibana, Airflow (webserver, scheduler, worker), Spark, FastAPI backend, React frontend, MinIO, Kafka, Redis
  - Add `.gitignore` for Python, Node.js, and IDE artifacts
  - Add `requirements.txt` for backend (fastapi, uvicorn, elasticsearch, pydantic, etc.)
  - Add `package.json` skeleton for frontend (React, Vite, ECharts, TailwindCSS, react-router)

  **Must NOT do**:
  - Do NOT modify `tft_crawler.py` — it works, leave it alone
  - Do NOT modify `check_kafka.py` — useful debugging tool
  - Do NOT delete `sample_VN2_1375465383.json` — needed as reference data
  - Do NOT delete `.env` — update it, don't recreate

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: Straightforward file operations, directory creation, config updates
  - **Skills**: []
    - No special skills needed for scaffolding
  - **Skills Evaluated but Omitted**:
    - `frontend-ui-ux`: No UI work here
    - `playwright`: No browser testing at this stage

  **Parallelization**:
  - **Can Run In Parallel**: NO (foundation task, blocks everything)
  - **Parallel Group**: Wave 1 (but must complete before dependent tasks)
  - **Blocks**: Tasks 3, 4, 5, 6
  - **Blocked By**: None (can start immediately)

  **References**:

  **Pattern References** (existing code to follow):
  - `.env` - Current config; UPDATE in-place, don't recreate. Keep MinIO/Airflow/Redis sections, remove MySQL
  - `tft_crawler.py` - Reference ONLY (do NOT modify). Note the Kafka topic name `tft-raw-matches` and region `vn2`
  - `spark_processor.py` - Reference for existing Spark schema structure; the ETL rewrite will replace this file

  **API/Type References**:
  - `sample_VN2_1375465383.json` - Full match JSON structure. Extract all field names for ES mapping design

  **External References**:
  - FastAPI project structure: https://fastapi.tiangolo.com/tutorial/bigger-applications/
  - Docker Compose for Elasticsearch: https://www.elastic.co/guide/en/elasticsearch/reference/current/docker.html
  - Airflow Docker: https://airflow.apache.org/docs/apache-airflow/stable/howto/docker-compose/

  **WHY Each Reference Matters**:
  - `.env` must be updated not recreated because existing Airflow/MinIO config is correct and needed
  - `tft_crawler.py` is read-only reference — understanding the Kafka topic and data format is critical for downstream ETL
  - `sample_VN2_1375465383.json` contains the actual data shape that dictates all ES mappings

  **Acceptance Criteria**:

  **QA Scenarios (MANDATORY):**

  ```
  Scenario: ClassicModels artifacts removed
    Tool: Bash
    Preconditions: Project directory exists
    Steps:
      1. Run: ls /home/huu/Documents/ki8/bigData/TFT_analytics/ | grep -E "check_data|mysql-connector|etl_job"
      2. Assert: No output (files/dirs removed)
      3. Run: test -d etl_job.py && echo "DIR" || echo "FILE_OR_GONE"
      4. Assert: Output is "FILE_OR_GONE"
    Expected Result: All ClassicModels artifacts gone, etl_job.py dir removed
    Failure Indicators: Any ClassicModels file still present, or etl_job.py still a directory
    Evidence: .sisyphus/evidence/task-1-cleanup.txt

  Scenario: Project structure created
    Tool: Bash
    Preconditions: Cleanup done
    Steps:
      1. Run: ls -la backend/app/ frontend/src/ etl/spark_jobs/ etl/dags/ ml/
      2. Assert: All directories exist with __init__.py files in Python packages
      3. Run: cat backend/requirements.txt | grep -E "fastapi|uvicorn|elasticsearch"
      4. Assert: All 3 packages listed
      5. Run: cat frontend/package.json | grep -E "echarts|react-router|tailwindcss"
      6. Assert: All 3 dependencies listed
    Expected Result: Full directory tree exists, dependencies declared
    Failure Indicators: Missing directories or empty package files
    Evidence: .sisyphus/evidence/task-1-structure.txt

  Scenario: .env updated for TFT
    Tool: Bash
    Preconditions: .env file exists
    Steps:
      1. Run: cat .env | grep -i "mysql"
      2. Assert: No MySQL-related lines (removed)
      3. Run: cat .env | grep "SPARK_APP_NAME"
      4. Assert: Contains "TFT" not "ClassicModels"
    Expected Result: .env has TFT-appropriate config, no ClassicModels remnants
    Failure Indicators: MySQL config still present, or Spark app name still references ClassicModels
    Evidence: .sisyphus/evidence/task-1-env.txt
  ```

  **Commit**: YES (groups with Wave 1)
  - Message: `feat(infra): project cleanup, directory structure, docker-compose skeleton`
  - Files: `All new directories, .env, .gitignore, docker-compose.yml, requirements.txt, package.json`
  - Pre-commit: `ls backend/ frontend/ etl/ ml/`

- [x] 2. **TFT Static Data & Reference Tables**

  **What to do**:
  - Create `etl/config/tft_static_data.py` containing:
    - Champion name mapping: `TFT17_Vex` → `Vex`, etc. (all TFT Set 17 champions with character_id → display name)
    - Trait name mapping: `TFT17_AnimaSquad` → `Anima Squad`, etc. (all TFT Set 17 traits with internal name → display name)
    - Item name mapping: item IDs to display names (from Riot Data Dragon or manual mapping)
    - Augment name mapping: internal augment IDs → display names
    - Trait tier thresholds: which tier_current values correspond to bronze/silver/gold/chromatic activation
    - Set/patch mapping: game_version string → meaningful patch number
  - Create `etl/config/formulas.py` containing:
    - `calc_win_rate(wins, total_games)` — simple wins/total
    - `calc_top4_rate(top4s, total_games)` — top4 count / total
    - `calc_avg_placement(placements, total_games)` — sum of placements / total
    - `calc_pick_rate(games_with_champ, total_games)` — frequency metric
    - `calc_meta_score(...)` — weighted composite score: 0.4*win_rate + 0.3*top4_rate + 0.2*(1/avg_placement) + 0.1*pick_rate_normalized (normalize each component to 0-1 first)
    - `calc_flex_score(compositions, total_games)` — diversity metric: 1 - (most_used_comp_count / total_games). If player spams 1 comp, score near 0. If diverse, near 1.
    - `calc_item_accuracy(player_items, recommended_items)` — Jaccard similarity between player's items and the most frequent items on that champion among top 4 placements
    - `identify_core_units(comp_units, threshold=0.6)` — units appearing in >= threshold% of a composition's top 4 variants are "core"
  - All formulas must handle edge cases: division by zero, empty arrays, null values

  **Must NOT do**:
  - Do NOT hardcode reference data inline in ETL or API code — keep it in dedicated config modules
  - Do NOT download data from Riot Data Dragon at runtime — static mapping files only
  - Do NOT include champion/trait data from sets other than Set 17 unless explicitly needed

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: Data collection and mapping creation, straightforward but tedious
  - **Skills**: []
  - **Skills Evaluated but Omitted**:
    - `playwright`: No browser testing

  **Parallelization**:
  - **Can Run In Parallel**: YES (with Task 1, Task 4, Task 5, Task 6)
  - **Parallel Group**: Wave 1
  - **Blocks**: Tasks 3, 7
  - **Blocked By**: None (can start immediately)

  **References**:

  **Pattern References**:
  - `sample_VN2_1375465383.json` - Extract ALL champion character_id values, trait name values, and item IDs from actual match data. This is the ground truth for static name mappings
  - `spark_processor.py:24-43` - Existing trait_schema and unit_schema showing field names (character_id, tier, itemNames)

  **External References**:
  - Riot Data Dragon: https://developer.riotgames.com/docs/data-dragon (for TFT Set 17 champion/item/encounter names)
  - TFT Set 17 community data: https://github.com/CommunityDragon/Data (cross-reference champion IDs)

  **WHY Each Reference Matters**:
  - Sample data contains actual character_id values like `TFT17_Vex` that must be mapped — can't guess these
  - spark_processor.py shows what fields the ETL already processes — formulas need to consume the same data shape

  **Acceptance Criteria**:

  **QA Scenarios:**

  ```
  Scenario: Static data mappings are complete
    Tool: Bash
    Preconditions: Task 1 directory structure exists
    Steps:
      1. Run: python3 -c "from etl.config.tft_static_data import CHAMPION_NAMES; print(len(CHAMPION_NAMES))"
      2. Assert: Output is a number >= 30 (TFT set has many champions)
      3. Run: python3 -c "from etl.config.tft_static_data import TRAIT_NAMES; print(len(TRAIT_NAMES))"
      4. Assert: Output is a number >= 20
      5. Run: python3 -c "from etl.config.tft_static_data import CHAMPION_NAMES; print(CHAMPION_NAMES.get('TFT17_Vex', 'NOT_FOUND'))"
      6. Assert: Output is "Vex" not "NOT_FOUND"
    Expected Result: All mappings loaded, champion/trait names resolve correctly
    Failure Indicators: Missing champions, KeyError on known champions, import errors
    Evidence: .sisyphus/evidence/task-2-static-data.txt

  Scenario: Formulas work correctly with edge cases
    Tool: Bash
    Preconditions: formulas.py exists
    Steps:
      1. Run: python3 -c "from etl.config.formulas import calc_win_rate; print(calc_win_rate(10, 20))"
      2. Assert: Output is "0.5" (50% win rate)
      3. Run: python3 -c "from etl.config.formulas import calc_win_rate; print(calc_win_rate(0, 0))"
      4. Assert: Output is "0" (handles division by zero)
      5. Run: python3 -c "from etl.config.formulas import calc_flex_score; print(calc_flex_score({'comp_a': 8, 'comp_b': 2}, 10))"
      6. Assert: Output is approximately "0.2" (1 - 0.8 = 0.2, low diversity)
    Expected Result: All formulas return correct values, handle edge cases gracefully
    Failure Indicators: Division by zero errors, wrong calculations, negative values
    Evidence: .sisyphus/evidence/task-2-formulas.txt
  ```

  **Commit**: YES (groups with Wave 1)
  - Message: `feat(etl): TFT static data mappings and calculation formulas`
  - Files: `etl/config/tft_static_data.py, etl/config/formulas.py`

- [x] 3. **Spark ETL Job - Core Metrics Calculation**

  **What to do**:
  - Rewrite `etl/spark_jobs/tft_etl.py` completely (replace the console-sink spark_processor.py)
  - The ETL job reads from Kafka topic `tft-raw-matches`, parses JSON, calculates metrics, and writes to Elasticsearch
  - **Step 1: Read from MinIO Data Lake** (batch mode, not streaming — hourly batch via Airflow)
    - Read raw match JSON files from MinIO `s3a://lakehouse-bucket/tft-raw/`
    - Parse using the existing schema from spark_processor.py (extend it with ALL needed fields)
  - **Step 2: Explode and flatten** participant data from match-level to row-level:
    - Each match → 8 rows (one per participant)
    - Each participant row: match_id, puuid, placement, level, gold_left, last_round, total_damage_to_players, traits (array), units (array), augments (array), game_version, game_datetime, game_length, queue_id
  - **Step 3: Calculate aggregated metrics** per entity type:
    - **player_stats**: Group by puuid → total_games, wins (placement=1), top4_count (placement<=4), avg_placement, win_rate, top4_rate, meta_score, flex_score, item_accuracy
    - **champion_stats**: Group by champion (from units.character_id) → total_games, wins, top4_count, avg_placement, win_rate, top4_rate, pick_rate (games with champ / total games in dataset)
    - **item_stats**: Group by item name → total_games (with this item), wins, top4_count, avg_placement, most_common_champion (mode of champions holding this item in top4)
    - **comp_meta**: Identify compositions by grouping traits with style>=1 (active traits) → comp_signature, total_games, wins, top4_count, avg_placement, win_rate, top4_rate, core_units list, core_items list
    - **champion_item_combo**: Group by (champion, item) → total_games, wins, top4_count, avg_placement — enables "with this item, this champion has X avg placement"
    - **champion_trait_combo**: Group by (champion, trait) → total_games, wins, top4_count, avg_placement
  - **Step 4: Write to Elasticsearch** using `org.elasticsearch:elasticsearch-spark-30_2.12` connector
    - Write each DataFrame to its respective ES index
    - Use `es.mapping.id` to use natural keys (puuid for player_stats, champion_id for champion_stats, etc.)
  - Handle null/missing values gracefully (augments can be null/empty, some units have no items)
  - Use the formula functions from `etl/config/formulas.py`

  **Must NOT do**:
  - Do NOT use streaming mode (readStream) — this is batch hourly, use `spark.read` from MinIO, not Kafka streaming
  - Do NOT output to console — must write to Elasticsearch
  - Do NOT hardcode API keys or connection strings — read from environment variables
  - Do NOT skip the champion_item_combo and champion_trait_combo aggregations — these enable the cross-analysis pages

  **Recommended Agent Profile**:
  - **Category**: `deep`
    - Reason: Complex PySpark transformations with multiple aggregation types, null handling, ES connector config. Requires careful data engineering
  - **Skills**: []
  - **Skills Evaluated but Omitted**:
    - `frontend-ui-ux`: No UI in this task
    - `playwright`: No browser testing

  **Parallelization**:
  - **Can Run In Parallel**: NO (depends on Tasks 1, 2)
  - **Parallel Group**: Sequential (after Tasks 1, 2)
  - **Blocks**: Task 7 (FastAPI endpoints depend on ES data)
  - **Blocked By**: Tasks 1 (project structure), 2 (formulas and static data)

  **References**:

  **Pattern References**:
  - `spark_processor.py` — Current schema definitions for trait_schema, unit_schema, participant_schema. EXTEND these with additional fields (augments, gold_left, etc.) but keep the same structural approach
  - `etl/config/formulas.py` — Import and use calc_win_rate, calc_top4_rate, calc_meta_score, calc_flex_score, calc_item_accuracy, identify_core_units

  **API/Type References**:
  - `sample_VN2_1375465383.json` — Full match JSON with all field names. Use this to define complete PySpark schema for parsing

  **External References**:
  - Elasticsearch Spark connector: https://www.elastic.co/guide/en/elasticsearch/hadoop/current/spark.html
  - PySpark DataFrame aggregations: https://spark.apache.org/docs/latest/api/python/reference/pyspark.sql/grouping.html
  - MinIO with Spark: https://min.io/docs/minio/linux/integrations/spark.html

  **WHY Each Reference Matters**:
  - spark_processor.py shows the existing approach — need to follow similar pattern but add ALL needed fields and write to ES instead of console
  - sample JSON is the ONLY way to know exact field names and types for schema definition
  - ES Spark connector config is non-trivial — need correct JAR version and write mode settings

  **Acceptance Criteria**:

  **QA Scenarios:**

  ```
  Scenario: ETL reads from MinIO and processes match data
    Tool: Bash
    Preconditions: MinIO running with sample data in s3a://lakehouse-bucket/tft-raw/
    Steps:
      1. Run: spark-submit --master local[2] --packages org.elasticsearch:elasticsearch-spark-30_2.12:8.13.0,org.apache.hadoop:hadoop-aws:3.3.4 etl/spark_jobs/tft_etl.py
      2. Wait for completion (should take < 2 min for sample data)
      3. Check ES: curl localhost:9200/player_stats/_count
      4. Assert: count > 0
      5. Check ES: curl localhost:9200/champion_stats/_count
      6. Assert: count > 0
    Expected Result: All 6 ES indices populated with calculated metrics
    Failure Indicators: Spark job crashes, ES indices empty, import errors, schema mismatch
    Evidence: .sisyphus/evidence/task-3-etl-run.txt

  Scenario: ETL handles null/missing data gracefully
    Tool: Bash
    Preconditions: ES indices populated
    Steps:
      1. Run: curl -s localhost:9200/player_stats/_search?size=1 | python3 -m json.tool
      2. Assert: Response has _source with fields: puuid, total_games, win_rate, top4_rate, avg_placement, meta_score
      3. Check no NaN or null in numeric fields
      4. Run: curl -s localhost:9200/champion_stats/_search?size=1 | python3 -m json.tool
      5. Assert: Response has champion_id, display_name (from static mapping), total_games, win_rate, avg_placement
    Expected Result: Data has no null values in required fields, display names resolved from static mapping
    Failure Indicators: null/NaN values, unmapped character_id values showing as raw IDs
    Evidence: .sisyphus/evidence/task-3-etl-data-quality.txt

  Scenario: core_units identification works in comp_meta
    Tool: Bash
    Preconditions: comp_meta index populated
    Steps:
      1. Run: curl -s 'localhost:9200/comp_meta/_search?size=1' | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['hits']['hits'][0]['_source'].keys())"
      2. Assert: Output includes 'core_units', 'comp_signature', 'win_rate', 'top4_rate', 'avg_placement'
    Expected Result: comp_meta has core_units field with list of unit IDs, plus all metric fields
    Failure Indicators: Missing core_units, missing comp_signature, aggregation errors
    Evidence: .sisyphus/evidence/task-3-comp-meta.txt
  ```

  **Commit**: YES (groups with Wave 1)
  - Message: `feat(etl): Spark ETL job with metrics calculation and ES write`
  - Files: `etl/spark_jobs/tft_etl.py`
  - Pre-commit: `python3 -c "from etl.config.formulas import calc_win_rate; print(calc_win_rate(1,2))"`

- [x] 4. **Elasticsearch Setup & Index Mappings**

  **What to do**:
  - Create `etl/config/es_mappings/` directory with 6 JSON mapping files:
    - `player_stats.json` — fields: puuid (keyword), total_games (integer), wins (integer), top4_count (integer), avg_placement (float), win_rate (float), top4_rate (float), meta_score (float), flex_score (float), item_accuracy (float), last_updated (date), display_name (keyword), companion (keyword)
    - `comp_meta.json` — fields: comp_signature (keyword), traits (nested: name, tier_current, num_units), core_units (nested: character_id, display_name, frequency), core_items (nested: item_name, frequency), total_games (integer), wins (integer), top4_count (integer), avg_placement (float), win_rate (float), top4_rate (float), last_updated (date)
    - `champion_stats.json` — fields: champion_id (keyword), display_name (keyword), total_games (integer), wins (integer), top4_count (integer), avg_placement (float), win_rate (float), top4_rate (float), pick_rate (float), last_updated (date)
    - `item_stats.json` — fields: item_name (keyword), total_games (integer), wins (integer), top4_count (integer), avg_placement (float), most_common_champion (keyword), most_common_champion_display (keyword), last_updated (date)
    - `champion_item_combo.json` — fields: champion_id (keyword), item_name (keyword), total_games (integer), wins (integer), top4_count (integer), avg_placement (float), last_updated (date)
    - `champion_trait_combo.json` — fields: champion_id (keyword), trait_name (keyword), total_games (integer), wins (integer), top4_count (integer), avg_placement (float), last_updated (date)
  - Create `etl/scripts/init_es.py` script that:
    - Connects to Elasticsearch at `localhost:9200`
    - Creates each index with its mapping if it doesn't exist
    - Has `--drop` flag to delete and recreate indices (for dev resets)
  - All field types must match what Spark ETL will write

  **Must NOT do**:
  - Do NOT use dynamic mapping — explicitly define all fields
  - Do NOT skip the nested definitions for traits and core_units in comp_meta

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: Schema definition work, straightforward but must be precise
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES (with Tasks 2, 5, 6 after Task 1)
  - **Parallel Group**: Wave 1
  - **Blocks**: Task 7
  - **Blocked By**: Task 1 (project structure)

  **References**:
  - `sample_VN2_1375465383.json` — Field names and types from actual data
  - Task 3 description — ES index names and field definitions must match exactly what ETL writes

  **External References**:
  - Elasticsearch mapping types: https://www.elastic.co/guide/en/elasticsearch/reference/current/mapping-types.html

  **Acceptance Criteria**:

  **QA Scenarios:**

  ```
  Scenario: ES indices created with correct mappings
    Tool: Bash
    Preconditions: Elasticsearch running on localhost:9200
    Steps:
      1. Run: python3 etl/scripts/init_es.py
      2. Run: curl -s localhost:9200/_cat/indices?v | grep tft
      3. Assert: 6 indices listed (player_stats, comp_meta, champion_stats, item_stats, champion_item_combo, champion_trait_combo)
      4. Run: curl -s localhost:9200/player_stats/_mapping | python3 -c "import sys,json; m=json.load(sys.stdin); print(list(m['player_stats']['mappings']['properties'].keys()))"
      5. Assert: Output contains 'puuid', 'win_rate', 'meta_score', 'flex_score'
    Expected Result: All 6 indices created with explicit mappings, no dynamic mapping
    Failure Indicators: Missing indices, wrong field types, dynamic mapping enabled
    Evidence: .sisyphus/evidence/task-4-es-mappings.txt

  Scenario: init_es.py --drop works for dev reset
    Tool: Bash
    Preconditions: Indices already exist
    Steps:
      1. Run: python3 etl/scripts/init_es.py --drop
      2. Run: curl -s localhost:9200/player_stats/_count
      3. Assert: count is 0 (freshly created, empty)
    Expected Result: Indices deleted and recreated with empty data
    Failure Indicators: Indices still have old data, or deletion fails
    Evidence: .sisyphus/evidence/task-4-es-reset.txt
  ```

  **Commit**: YES (groups with Wave 1)
  - Message: `feat(es): Elasticsearch index mappings and init script`
  - Files: `etl/config/es_mappings/*.json, etl/scripts/init_es.py`

- [x] 5. **Docker Compose - Infrastructure Services**

  **What to do**:
  - Create/update `docker-compose.yml` with all infrastructure services:
    - **Elasticsearch** (port 9200): image `docker.elastic.co/elasticsearch/elasticsearch:8.13.0`, environment: discovery.type=single-node, xpack.security.enabled=false, ES_JAVA_OPTS="-Xms1g -Xmx1g"
    - **Kibana** (port 5601): linked to ES, for debugging/visualization of ES data
    - **MinIO** (ports 9000/9001): existing config from .env, bucket `tft-analytics`
    - **Redis** (port 6379): existing config from .env
    - **Apache Airflow** (ports 8080): webserver, scheduler, worker using CeleryExecutor with Redis backend. Mount `etl/dags/` volume
    - **Spark**: image with Kafka and ES connector JARs pre-installed. Mount `etl/spark_jobs/` volume
  - Create `docker-compose.override.yml` for development (frontend dev server, backend hot reload)
  - Each service must have healthcheck defined
  - Network: all services on same `tft-network` bridge network
  - Volumes: persistent data for ES, MinIO, Postgres (Airflow metadata DB)

  **Must NOT do**:
  - Do NOT include Kafka service in docker-compose (Kafka is already running externally via Kubernetes Strimzi as noted from Metis review)
  - Do NOT set xpack.security.enabled=true (development setup, no auth needed)
  - Do NOT use :latest tags — pin specific versions

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: Infrastructure config, well-documented patterns
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES (with Tasks 2, 4, 6 after Task 1)
  - **Parallel Group**: Wave 1
  - **Blocks**: Tasks 8, 18
  - **Blocked By**: Task 1 (project structure)

  **References**:
  - `.env` — Existing config for MinIO (port 9000, admin/password123), Redis (port 6379), Airflow (CeleryExecutor, PostgreSQL)
  - `spark_processor.py` — Notes Spark version 3.5.1 and Kafka connector package `org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.1`

  **External References**:
  - Elasticsearch Docker: https://www.elastic.co/guide/en/elasticsearch/reference/current/docker.html
  - Airflow Docker Compose: https://airflow.apache.org/docs/apache-airflow/stable/howto/docker-compose/

  **Acceptance Criteria**:

  **QA Scenarios:**

  ```
  Scenario: All infrastructure services start and become healthy
    Tool: Bash
    Preconditions: Docker running, ports 9200, 5601, 9000, 8080 available
    Steps:
      1. Run: docker-compose up -d
      2. Wait 60 seconds for services to initialize
      3. Run: curl -s localhost:9200/_cluster/health | python3 -c "import sys,json; print(json.load(sys.stdin)['status'])"
      4. Assert: Output is "green" or "yellow" (single-node is yellow by default)
      5. Run: curl -s localhost:5601/api/status | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['status']['overall']['level'])"
      6. Assert: Output is "available"
      7. Run: curl -s localhost:9000/minio/health/live
      8. Assert: HTTP 200
    Expected Result: ES, Kibana, MinIO, Airflow all running and healthy
    Failure Indicators: Container crashes, health checks fail, port conflicts
    Evidence: .sisyphus/evidence/task-5-docker-services.txt

  Scenario: Airflow webserver accessible and scheduler running
    Tool: Bash
    Preconditions: All containers up
    Steps:
      1. Run: curl -s -o /dev/null -w "%{http_code}" http://localhost:8080/health
      2. Assert: HTTP 200
    Expected Result: Airflow webserver responds
    Failure Indicators: HTTP 503, connection refused, scheduler not running
    Evidence: .sisyphus/evidence/task-5-airflow.txt
  ```

  **Commit**: YES (groups with Wave 1)
  - Message: `feat(infra): Docker Compose for Elasticsearch, Kibana, Airflow, MinIO, Spark`
  - Files: `docker-compose.yml, docker-compose.override.yml`

- [x] 6. **FastAPI Project Skeleton & Health Endpoints**

  **What to do**:
  - Create FastAPI backend in `backend/` directory:
    - `app/__init__.py`
    - `app/main.py` — FastAPI app with CORS middleware (allow localhost:5173), lifespan event (connect to ES on startup)
    - `app/config.py` — Settings class using pydantic-settings: ES_HOST, ES_PORT, KAFKA_BROKER, MINIO_ENDPOINT, AIRFLOW_URL, all from env vars with defaults
    - `app/services/es_client.py` — Async Elasticsearch client singleton, connects on startup, disconnects on shutdown
    - `app/routes/health.py` — GET `/health` returns `{status: "ok", elasticsearch: "connected"}`, GET `/ready` checks ES connection is alive
  - Create `backend/requirements.txt`:
    - fastapi>=0.110.0, uvicorn[standard]>=0.27.0, elasticsearch[async]>=8.13.0, pydantic>=2.5.0, pydantic-settings>=2.1.0, httpx>=0.27.0
  - Create `backend/Dockerfile` — Python 3.11 slim, install requirements, expose 8000
  - App should start with: `uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload`

  **Must NOT do**:
  - Do NOT implement analytics endpoints yet — only health/ready endpoints in this task
  - Do NOT use synchronous Elasticsearch client — must use async
  - Do NOT hardcode connection strings — use config.py with env vars

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: Standard FastAPI boilerplate, well-documented pattern
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES (with Tasks 2, 4, 5 after Task 1)
  - **Parallel Group**: Wave 1
  - **Blocks**: Task 7
  - **Blocked By**: Task 1 (project structure)

  **References**:
  - `.env` — Elasticsearch not configured yet but should be at localhost:9200 by default
  - Task 4 — ES indices must match (player_stats, comp_meta, champion_stats, item_stats, champion_item_combo, champion_trait_combo)

  **External References**:
  - FastAPI project structure: https://fastapi.tiangolo.com/tutorial/bigger-applications/
  - Async Elasticsearch client: https://elasticsearch-py.readthedocs.io/en/latest/async.html

  **Acceptance Criteria**:

  **QA Scenarios:**

  ```
  Scenario: FastAPI starts and health endpoints work
    Tool: Bash
    Preconditions: Elasticsearch running on localhost:9200
    Steps:
      1. Run: cd backend && pip install -r requirements.txt
      2. Run: cd backend && uvicorn app.main:app --host 0.0.0.0 --port 8000 &
      3. Wait 3 seconds
      4. Run: curl -s localhost:8000/health | python3 -m json.tool
      5. Assert: Output has {"status": "ok", "elasticsearch": "connected"}
      6. Run: curl -s localhost:8000/ready | python3 -m json.tool
      7. Assert: Output has {"status": "ready"}
    Expected Result: Health and ready endpoints return correct JSON
    Failure Indicators: Connection refused, ES not connected, import errors
    Evidence: .sisyphus/evidence/task-6-fastapi-health.txt
  ```

  **Commit**: YES (groups with Wave 1)
  - Message: `feat(backend): FastAPI project skeleton with health endpoints`
  - Files: `backend/app/main.py, backend/app/config.py, backend/app/services/es_client.py, backend/app/routes/health.py, backend/requirements.txt, backend/Dockerfile`

- [x] 7. **FastAPI Analytics Endpoints**

  **What to do**:
  - Create 15+ REST API endpoints in `backend/app/routes/` organized by domain:
    - **`routes/players.py`**:
      - `GET /api/players/{puuid}` — Player profile with all stats, can filter by game count (all/20/50/100)
      - `GET /api/players/{puuid}/champions` — Champion stats for specific player
      - `GET /api/players/{puuid}/traits` — Trait usage stats for specific player
      - `GET /api/players/{puuid}/items` — Item usage stats for specific player
      - `GET /api/players/search?name={riot_id}` — Search player by riot ID
    - **`routes/compositions.py`**:
      - `GET /api/compositions` — Top meta compositions with win_rate, top4_rate, pick_rate, core_units. Supports sorting and filtering (min_games, patch_version, sort_by)
      - `GET /api/compositions/{comp_signature}` — Full detail of specific composition with item builds
    - **`routes/champions.py`**:
      - `GET /api/champions` — All champion stats overview (sortable, filterable by patch)
      - `GET /api/champions/{champion_id}` — Detailed champion analysis: stats, best items, best trait combos, best item builds
      - `GET /api/champions/{champion_id}/items` — Per-item breakdown for this champion (avg placement by item)
      - `GET /api/champions/{champion_id}/traits` — Per-trait combo breakdown
    - **`routes/items.py`**:
      - `GET /api/items` — All item stats overview
      - `GET /api/items/{item_name}` — Detailed item analysis: avg placement, best champions to pair with
      - `GET /api/items/{item_name}/champions` — Champion-item combo breakdown
    - **`routes/analysis.py`**:
      - `GET /api/analysis/build` — General analysis with filters: champ_ids[], item_names[], returns optimal builds
      - `GET /api/analysis/meta-overview` — Overview stats: total matches, total players, current patch, meta diversity score
  - Create `backend/app/services/analytics.py` — Service layer that queries Elasticsearch and returns structured Pydantic response models
  - Create `backend/app/models/` — Pydantic response models for each endpoint group:
    - `models/player.py`: PlayerProfile, PlayerChampionStats, PlayerTraitStats, PlayerItemStats
    - `models/composition.py`: CompositionSummary, CompositionDetail, CoreUnit, CoreItem
    - `models/champion.py`: ChampionOverview, ChampionDetail, ChampionItemCombo, ChampionTraitCombo
    - `models/item.py`: ItemOverview, ItemDetail, ItemChampionCombo
    - `models/analysis.py`: BuildSuggestion, MetaOverview
  - All endpoints use async ES queries via `es_client.py`
  - Support query parameters: `patch` (filter by game version), `min_games` (minimum game count threshold), `sort_by` (win_rate, avg_placement, pick_rate), `limit` and `offset` for pagination

  **Must NOT do**:
  - Do NOT query Elasticsearch directly in route handlers — use service layer
  - Do NOT return raw ES responses — transform to Pydantic models
  - Do NOT skip pagination — all list endpoints must support limit/offset
  - Do NOT add authentication — this is a public read-only API

  **Recommended Agent Profile**:
  - **Category**: `unspecified-high`
    - Reason: Many endpoints with proper service layer, Pydantic models, and ES query construction. Moderate complexity
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: NO (depends on Tasks 3, 4, 6)
  - **Parallel Group**: Wave 2 (sequential)
  - **Blocks**: Tasks 11-15 (dashboard pages need API data)
  - **Blocked By**: Tasks 3 (ETL writes data to ES), 4 (ES indices), 6 (FastAPI skeleton)

  **References**:
  - Task 3 description — ES index names, field names, and calculated metrics that the API must query
  - Task 4 — ES mapping definitions — field types must match for correct ES queries
  - Task 2 — Static data mappings — champion display names, trait display names resolved by API

  **External References**:
  - FastAPI with Elasticsearch: https://fastapi.tiangolo.com/advanced/async-sql-databases/ (pattern for async database connections)
  - Elasticsearch Python async queries: https://elasticsearch-py.readthedocs.io/en/latest/async.html
  - Pydantic models: https://docs.pydantic.dev/latest/

  **Acceptance Criteria**:

  **QA Scenarios:**

  ```
  Scenario: API endpoints return structured data
    Tool: Bash
    Preconditions: ES populated with data from ETL, FastAPI running
    Steps:
      1. Run: curl -s localhost:8000/api/champions | python3 -c "import sys,json; d=json.load(sys.stdin); print(type(d), len(d.get('data', d.get('items', []))))"
      2. Assert: Returns JSON with champion data (list of objects with champion_id, display_name, win_rate, etc.)
      3. Run: curl -s "localhost:8000/api/compositions?min_games=5&sort_by=win_rate&limit=10" | python3 -m json.tool | head -20
      4. Assert: Returns list of compositions, sorted by win_rate, with core_units field
      5. Run: curl -s localhost:8000/api/analysis/meta-overview | python3 -m json.tool
      6. Assert: Returns total_matches, total_players, current_patch fields
    Expected Result: All endpoints return valid JSON with expected field structure
    Failure Indicators: 404, 500, missing fields, unsorted data, wrong types
    Evidence: .sisyphus/evidence/task-7-api-endpoints.txt

  Scenario: Pagination and filtering work
    Tool: Bash
    Preconditions: API loaded with data
    Steps:
      1. Run: curl -s "localhost:8000/api/champions?limit=5&offset=0" | python3 -c "import sys,json; d=json.load(sys.stdin); print(len(d.get('data', d.get('items', []))))"
      2. Assert: Returns exactly 5 items
      3. Run: curl -s "localhost:8000/api/compositions?min_games=10" | python3 -c "import sys,json; d=json.load(sys.stdin); items=d.get('data', d.get('items', [])); print(all(x['total_games']>=10 for x in items))"
      3. Assert: All compositions have total_games >= 10
    Expected Result: Pagination and filtering parameters respected
    Failure Indicators: Wrong item count, filter not applied
    Evidence: .sisyphus/evidence/task-7-api-filtering.txt
  ```

  **Commit**: YES (groups with Wave 2)
  - Message: `feat(backend): analytics API endpoints with ES query service layer`
  - Files: `backend/app/routes/*.py, backend/app/services/analytics.py, backend/app/models/*.py`

- [x] 8. **Airflow DAG - ETL Orchestration**

  **What to do**:
  - Create `etl/dags/tft_etl_dag.py` — Airflow DAG that runs the Spark ETL job hourly:
    - DAG ID: `tft_analytics_etl`
    - Schedule: `0 * * * *` (every hour)
    - Default args: retries=3, retry_delay=5 minutes, SLA=10 minutes
    - Task 1: `check_kafka_topic` — Sensor that checks Kafka topic `tft-raw-matches` has messages in the last hour
    - Task 2: `run_spark_etl` — SparkSubmitOperator that runs `etl/spark_jobs/tft_etl.py`
    - Task 3: `verify_es_indices` — PythonOperator that checks all 6 ES indices have documents and `last_updated` is within last hour
    - Task 4: `send_completion_notification` — DummyOperator (placeholder for future Slack/email notification)
    - Dependencies: check_kafka_topic >> run_spark_etl >> verify_es_indices >> send_completion_notification
  - Configure SparkSubmitOperator with correct JAR packages and ES write config
  - Add DAG to Airflow's `dags/` folder (already mounted in Docker Compose)

  **Must NOT do**:
  - Do NOT use streaming mode in DAG — this is batch hourly
  - Do NOT create complex branching logic — simple linear pipeline
  - Do NOT skip the verification step — must check ES indices after ETL

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: Standard Airflow DAG definition, well-documented patterns
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES (with Tasks 7, 9, 10)
  - **Parallel Group**: Wave 2
  - **Blocks**: None (monitoring/orchestration layer)
  - **Blocked By**: Tasks 3 (ETL job must exist), 5 (Docker Compose with Airflow)

  **References**:
  - `spark_processor.py` — Current Spark config (app name, packages, Kafka settings)
  - Task 3 — ETL job file path and expected behavior
  - `.env` — Airflow config: CeleryExecutor, PostgreSQL, Redis, schedule interval `*/5 * * * *`

  **External References**:
  - Airflow SparkSubmitOperator: https://airflow.apache.org/docs/apache-airflow-providers-apache-spark/stable/operators/spark_submit.html

  **Acceptance Criteria**:

  **QA Scenarios:**

  ```
  Scenario: DAG is loaded and has correct structure
    Tool: Bash
    Preconditions: Airflow running
    Steps:
      1. Run: curl -s http://localhost:8080/api/v1/dags/tft_analytics_etl | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('dag_id', 'NOT_FOUND'))"
      2. Assert: Output is "tft_analytics_etl"
      3. Run: curl -s http://localhost:8080/api/v1/dags/tft_analytics_etl/tasks | python3 -c "import sys,json; d=json.load(sys.stdin); print([t['task_id'] for t in d['tasks']])"
      4. Assert: Output includes 'check_kafka_topic', 'run_spark_etl', 'verify_es_indices'
    Expected Result: DAG loaded with all expected tasks in correct dependency order
    Failure Indicators: DAG not found, missing tasks, wrong dependency order
    Evidence: .sisyphus/evidence/task-8-airflow-dag.txt
  ```

  **Commit**: YES (groups with Wave 2)
  - Message: `feat(airflow): ETL orchestration DAG with verification steps`
  - Files: `etl/dags/tft_etl_dag.py`

- [x] 9. **React + Vite Project Setup & Layout Shell**

  **What to do**:
  - Initialize React + Vite + TypeScript project in `frontend/`:
    - `npm create vite@latest frontend -- --template react-ts`
    - Install dependencies: `npm install echarts echarts-for-react react-router-dom tailwindcss @tailwindcss/vite lucide-react`
    - Configure TailwindCSS with `@tailwindcss/vite` plugin
    - Configure path aliases in `vite.config.ts` and `tsconfig.json`: `@/` → `src/`
  - Create layout shell with:
    - `src/App.tsx`: Router with `<BrowserRouter>`, `<Routes>`, navigation
    - `src/components/Layout.tsx`: Sidebar navigation + main content area:
      - Sidebar: Logo ("TFT Analytics"), nav links (5 pages: Player Profile, Top Meta, Champions, Items, Analysis), dark theme
      - Main: `<Outlet />` for page content
      - Responsive: sidebar collapses on mobile
    - `src/pages/` — 5 placeholder pages that render "Coming Soon" with appropriate titles:
      - `PlayerProfilePage.tsx`
      - `TopMetaPage.tsx`
      - `ChampionAnalysisPage.tsx`
      - `ItemAnalysisPage.tsx`
      - `GeneralAnalysisPage.tsx`
    - `src/api/client.ts` — Axios/fetch client pointing to `http://localhost:8000/api` with base config
    - `src/hooks/useApi.ts` — Custom hook for data fetching with loading/error states
  - Dark theme base colors: TFT-style dark background (#0a0e1a), accent gold (#c8aa6e), accent blue (#0ac8b9), card background (#1a1d2e)
  - App must render in browser at localhost:5173 with sidebar and placeholder pages

  **Must NOT do**:
  - Do NOT implement actual chart components yet — only layout shell and placeholder pages
  - Do NOT use CSS modules — use TailwindCSS utility classes only
  - Do NOT use any state management library (Redux, Zustand) — React Query/SWR for server state, useState for local state only

  **Recommended Agent Profile**:
  - **Category**: `visual-engineering`
    - Reason: UI/UX work — layout, navigation, theme, responsive design
  - **Skills**: [`/frontend-ui-ux`]

  **Parallelization**:
  - **Can Run In Parallel**: YES (with Tasks 7, 8, 10)
  - **Parallel Group**: Wave 2
  - **Blocks**: Tasks 11-15 (all dashboard pages)
  - **Blocked By**: None (can start immediately — no dependency on backend data)

  **References**:
  - Task 7 — API endpoint definitions — the `src/api/client.ts` must match these URLs

  **External References**:
  - Vite React setup: https://vitejs.dev/guide/#scaffolding-your-first-vite-project
  - ECharts for React: https://github.com/hustcc/echarts-for-react
  - TailwindCSS v4: https://tailwindcss.com/docs

  **Acceptance Criteria**:

  **QA Scenarios:**

  ```
  Scenario: Frontend renders with navigation and placeholder pages
    Tool: Playwright
    Preconditions: Frontend dev server running at localhost:5173
    Steps:
      1. Navigate to http://localhost:5173
      2. Assert: Sidebar visible with "TFT Analytics" logo text
      3. Assert: 5 navigation links visible: "Player Profile", "Top Meta", "Champions", "Items", "Analysis"
      4. Click each nav link
      5. Assert: Each page renders its title ("Player Profile", "Top Meta Comps", etc.)
      6. Assert: Page background is dark (#0a0e1a or similar)
      7. Assert: Accent colors visible (gold text, teal highlights)
    Expected Result: Full layout shell renders, navigation works, dark theme applied
    Failure Indicators: Blank page, navigation broken, light theme, missing pages
    Evidence: .sisyphus/evidence/task-9-frontend-shell.png

  Scenario: Responsive sidebar collapses on mobile
    Tool: Playwright
    Preconditions: Frontend running
    Steps:
      1. Set viewport to 375x667 (iPhone SE)
      2. Navigate to http://localhost:5173
      3. Assert: Sidebar is collapsed or hidden (not full width)
      4. Click hamburger menu icon
      5. Assert: Sidebar expands or overlay appears
    Expected Result: Responsive sidebar works on mobile viewport
    Failure Indicators: Sidebar always full width on mobile, no toggle button
    Evidence: .sisyphus/evidence/task-9-responsive.png
  ```

  **Commit**: YES (groups with Wave 2)
  - Message: `feat(frontend): React Vite project setup with layout shell and navigation`
  - Files: `frontend/src/App.tsx, Layout.tsx, pages/*.tsx, api/client.ts, hooks/useApi.ts, package.json, vite.config.ts, tailwind.config.ts`

- [x] 10. **PyTorch Recommendation Model - Training Pipeline**

  **What to do**:
  - Create PyTorch model in `ml/` for team composition suggestion:
    - `ml/model.py` — Define the recommendation model:
      - Embedding layers for champions (character_id → embedding), items, and traits
      - Model architecture: Multi-layer neural network that takes current champions/items as input and outputs recommended additions
      - Input: list of champion_ids (already owned), optionally item_ids
      - Output: ranked list of recommended champion_ids with confidence scores
      - Training objective: Predict placement (regression) or top4 (binary classification) given a composition
    - `ml/train.py` — Training pipeline:
      - Read match data from MinIO (via PySpark or direct JSON read)
      - Feature engineering: convert compositions to feature vectors using embeddings, encode traits as multi-hot vectors
      - Split data: 80% train, 20% validation
      - Train with Adam optimizer, learning rate 0.001, batch size 256
      - Log training loss and validation loss per epoch
      - Save best model checkpoint to `ml/checkpoints/`
      - Save model metadata (input/output dimensions, champion mapping) alongside checkpoint
    - `ml/predict.py` — Inference pipeline:
      - Load model from checkpoint
      - Given partial team (list of champion_ids), recommend top-5 champion additions
      - Return: list of {champion_id, display_name, confidence}
    - `ml/Dockerfile` — Training environment with PyTorch, Spark dependencies
  - The model should be simple but functional — a 3-layer MLP is sufficient for this use case
  - Must handle cold start: if champion_id not in training data, use default embedding

  **Must NOT do**:
  - Do NOT build a complex transformer model — simple MLP for v1
  - Do NOT include model serving infrastructure (TF Serving, etc.) — API in Task 16 will load model directly
  - Do NOT train on production data yet — use sample data or a small subset

  **Recommended Agent Profile**:
  - **Category**: `ultrabrain`
    - Reason: ML model design requires careful architecture decisions, embedding design, and training pipeline setup
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES (with Tasks 7, 8, 9)
  - **Parallel Group**: Wave 2
  - **Blocks**: Task 16 (recommendation API integration)
  - **Blocked By**: Task 2 (formulas and static data mappings for feature engineering)

  **References**:
  - `sample_VN2_1375465383.json` — Match data structure for feature engineering: units[].character_id, units[].itemNames, traits[].name
  - Task 2 — `tft_static_data.py` — Champion name mappings needed for embedding layer vocabulary size

  **External References**:
  - PyTorch embeddings for recommendation: https://pytorch.org/tutorials/beginner/nlp/word_embeddings_tutorial.html
  - Collaborative filtering with PyTorch: https://pytorch.org/tutorials/intermediate/char_rnn_classification_tutorial.html

  **Acceptance Criteria**:

  **QA Scenarios:**

  ```
  Scenario: Model trains on sample data without errors
    Tool: Bash
    Preconditions: Sample match data available
    Steps:
      1. Run: cd ml && python train.py --epochs 5 --data-path ../sample_VN2_1375465383.json
      2. Assert: Training completes without errors
      3. Run: ls checkpoints/
      4. Assert: File best_model.pt exists
    Expected Result: Model trains successfully and saves checkpoint
    Failure Indicators: CUDA errors, shape mismatches, training loss NaN
    Evidence: .sisyphus/evidence/task-10-model-train.txt

  Scenario: Model produces recommendations
    Tool: Bash
    Preconditions: Model checkpoint exists
    Steps:
      1. Run: cd ml && python predict.py --champions TFT17_Vex,TFT17_Ezreal --top-k 5
      2. Assert: Output is JSON array with 5 items, each having champion_id, display_name, confidence
      3. Assert: confidence values are between 0 and 1
      4. Assert: display_names are human-readable (not TFT17_ prefixed)
    Expected Result: Model returns 5 recommended champions with confidence scores
    Failure Indicators: Empty output, KeyError, model not loading, confidence > 1 or < 0
    Evidence: .sisyphus/evidence/task-10-predict.txt
  ```

  **Commit**: YES (groups with Wave 2)
  - Message: `feat(ml): PyTorch recommendation model with training and inference pipeline`
  - Files: `ml/model.py, ml/train.py, ml/predict.py, ml/Dockerfile` (MANDATORY — after ALL implementation tasks)

> 4 review agents run in PARALLEL. ALL must APPROVE. Present consolidated results to user and get explicit "okay" before completing.

- [x] F1. **Plan Compliance Audit** — `oracle`
  Read the plan end-to-end. For each "Must Have": verify implementation exists (read file, curl endpoint, run command). For each "Must NOT Have": search codebase for forbidden patterns — reject with file:line if found. Check evidence files exist in .sisyphus/evidence/. Compare deliverables against plan.
  Output: `Must Have [N/N] | Must NOT Have [N/N] | Tasks [N/N] | VERDICT: APPROVE/REJECT`

- [x] F2. **Code Quality Review** — `unspecified-high`
  Run `tsc --noEmit` + linter if available. Review all changed files for: `as any`/`@ts-ignore`, empty catches, console.log in prod, commented-out code, unused imports. Check AI slop: excessive comments, over-abstraction, generic names (data/result/item/temp).
  Output: `Build [PASS/FAIL] | Lint [PASS/FAIL] | Files [N clean/N issues] | VERDICT`

- [x] F3. **Real Manual QA** — `unspecified-high` (+ `playwright` skill)
  Start from clean state (docker-compose down && docker-compose up). Execute EVERY QA scenario from EVERY task — follow exact steps, capture evidence. Test cross-page navigation. Test filters. Test edge cases: empty data, no results. Save to `.sisyphus/evidence/final-qa/`.
  Output: `Scenarios [N/N pass] | Integration [N/N] | Edge Cases [N tested] | VERDICT`

- [x] F4. **Scope Fidelity Check** — `deep`
  For each task: read "What to do", read actual diff. Verify 1:1 — everything in spec was built (no missing), nothing beyond spec was built (no creep). Check "Must NOT do" compliance. Flag unaccounted changes.
  Output: `Tasks [N/N compliant] | Contamination [CLEAN/N issues] | Unaccounted [CLEAN/N files] | VERDICT`

---

## Commit Strategy

- **Wave 1**: `feat(infra): project cleanup, ETL core, ES setup, docker compose, API skeleton`
- **Wave 2**: `feat(core): analytics endpoints, airflow DAG, frontend shell, recommendation model`
- **Wave 3**: `feat(dashboard): all 5 dashboard pages with ECharts visualizations`
- **Wave 4**: `feat(integration): recommendation API, nav/filters, full stack docker`

---

## Success Criteria

### Verification Commands
```bash
# Infrastructure
docker-compose ps                    # All services running
curl localhost:9200/_cat/indices     # 6 ES indices exist
curl localhost:8000/health           # FastAPI health check

# ETL Pipeline
curl "localhost:9200/player_stats/_count"          # Has documents
curl "localhost:9200/comp_meta/_count"             # Has documents  
curl "localhost:9200/champion_stats/_count"        # Has documents

# Frontend
curl localhost:5173                  # React app serves
# Playwright: each page renders, charts visible, filters work

# Recommendation
curl -X POST localhost:8000/api/recommend -H "Content-Type: application/json" -d '{"champions": ["TFT17_Vex"]}'  # Returns suggestions
```

### Final Checklist
- [ ] All "Must Have" present
- [ ] All "Must NOT Have" absent
- [ ] All 5 dashboard pages render with real data
- [ ] ECharts charts are interactive (hover tooltips, filters)
- [ ] Airflow DAG runs on schedule
- [ ] Docker Compose starts full stack