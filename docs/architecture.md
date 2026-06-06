# TFT Analytics Data Platform

## Default data flow

```text
Riot API -> crawler -> MinIO tft-raw
  -> Spark normalize and validate
  -> MinIO tft-silver participants + quarantine
  -> Spark Gold aggregates
  -> MinIO tft-gold versioned snapshots
  -> Elasticsearch versioned indices
  -> atomic tft_* alias swap
  -> FastAPI -> React
```

PostgreSQL stores pipeline metadata, watermarks, data-quality reports and crawler progress.
Elasticsearch remains a serving layer and can be rebuilt from Gold data.

## Silver migration

The default `SILVER_FORMAT=parquet` mode is intended for the first backfill and low-risk rollout.
Set `SILVER_FORMAT=iceberg` before the initial Silver backfill to use the bundled Iceberg Hadoop catalog.
Do not switch an existing Silver warehouse between formats without running an explicit backfill.

The ETL reads only Raw objects missing from `processed_silver_objects`. Gold aggregation still scans
Silver so the output remains deterministic while Raw JSON scan cost is removed.

## Operations

```bash
make monitoring
make backup
make republish-gold VERSION=v20260603115304790860
make cleanup-gold RETENTION=2
make rollback VERSION=v20260602134300153925
```

Prometheus is exposed on `:9090` and Grafana on `:3000` when the `monitoring` profile is enabled.
The backend publishes pipeline metrics at `/metrics` and JSON status at `/api/operations/status`.
Use `republish-gold` when Elasticsearch aliases or documents need to be rebuilt from an existing
Gold snapshot. This path reads `tft-gold/data_version=...` and writes Elasticsearch/PostgreSQL
metadata only; it does not crawl, normalize Raw, or rebuild Silver/Gold.

## Optional scale profile

```bash
make scale
```

The `scale` profile starts a Spark master plus three Spark workers by default. The Spark services use
the same `tft-airflow-spark` image as the Airflow driver so PySpark executor tasks run with the same
Python and dependency set. Kafka and Trino remain optional scale-profile services and are intentionally
not part of the default runtime. Kafka should only be connected to crawler ingestion when API throughput
or retry isolation requires it. Trino catalog configuration is a starting point for ad-hoc lakehouse
access and must be aligned with the chosen production Iceberg catalog before relying on it for queries.
