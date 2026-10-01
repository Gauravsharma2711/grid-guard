# Grid-Guard: AMI Smart-Meter Data Contract & Conceptual Schema

## 1. Executive Summary

This document defines the formal data contract for smart-meter Advanced Metering Infrastructure (AMI) time-series data ingested by the Grid-Guard Non-Technical Loss (NTL) detection and decision system.

Because real-world utility datasets vary widely in formatting, schema naming, sampling interval, and metadata availability, Grid-Guard establishes a clear boundary between:
1. **Conceptual Field Specifications** (the target domain model required by downstream ML and financial evaluation engines),
2. **Physical Ingestion Mappings** (how raw vendor/utility files map to the conceptual schema), and
3. **Field Availability Classifications** (source vs. derived vs. external vs. unavailable).

---

## 2. Conceptual Field Hierarchy

| Conceptual Field | Canonical Data Type | Physical Meaning | Requirement Level | Availability Classification | Downstream Pipeline Usage |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **`meter_id`** | `String` / `Utf8` | Unique alphanumeric identifier for consumer/meter (e.g. `CONS_NO`, `meter_serial`) | **Mandatory** | Source Dataset | Entity grouping, time-series aggregation, inspection dispatch key |
| **`timestamp`** | `Datetime` / `Date` | Timestamp or date of consumption recording | **Mandatory** | Source or Wide Columns | Temporal ordering, calendar feature engineering, seasonal decomposition |
| **`consumption`** | `Float64` | Energy consumption volume for the interval | **Mandatory** | Source or Wide Columns | Core anomaly signals, sudden drops, volatility metrics, loss estimation |
| **`unit`** | `String` (Enum) | Unit of measurement (`kWh`, `Wh`, `kW`) | **Expected** | Derived or Metadata Config | Financial loss calculation and normalization |
| **`frequency`** | `String` (Enum) | Sampling resolution (`daily`, `hourly`, `30min`, `15min`) | **Expected** | Derived or Configuration | Resampling, gap detection, rolling window span selection |
| **`tampering_label`** | `Int8` / `Boolean` | Ground-truth theft/tampering indicator (1 = Theft, 0 = Normal) | **Conditional** (Supervised training only) | Source Dataset | Classifier training target, ground-truth benchmark evaluation |
| **`tariff_rate`** | `Float64` | Effective electricity cost per kWh ($/kWh or local currency) | **Recommended** | External Metadata or Derived | Financial loss calculation ($L = \Delta\text{kWh} \times \text{Tariff}$) |
| **`customer_category`** | `Categorical` | Sector classification (`residential`, `commercial`, `industrial`) | **Optional** | Source or External Metadata | Stratified normalization, sector-specific tampering baselines |
| **`feeder_id`** | `String` / `Utf8` | Substation feeder / distribution transformer ID | **Optional** | External Metadata | Upstream energy balance audit, technical loss deduction |
| **`neighborhood_id`** | `String` / `Utf8` | Spatial grouping / postal code / district code | **Optional** | External Metadata | Inspection crew routing costs ($C_{dispatch}$), spatial clustering |

---

## 3. Field Availability Breakdown

### Group A: Fields Guaranteed / Expected in Raw Data
- **`meter_id`**: Always required in row-level records or wide-format headers.
- **`consumption` & `timestamp`**:
  - In **long-format** datasets (e.g., CER Ireland, London Smart Meter), these exist as two distinct columns: `timestamp` and `kwh_value`.
  - In **wide-format** datasets (e.g., State Grid Corporation of China [SGCC]), each column header represents a specific calendar date (e.g. `8/3/2014`, `8/4/2014`), and the cell value represents the daily consumption for that consumer.
- **`tampering_label`** (`FLAG`): Present in benchmark training datasets (such as SGCC), but explicitly **absent** during production deployment inference.

### Group B: Fields Typically Derived During Pipeline Execution
- **`unit` & `frequency`**: Inferred by inspecting timestamp delta intervals ($\Delta t$) or configured explicitly per data source in `configs/dataset_mappings.yaml`.
- **`tampering_drop_ratio`**: Derived during Feature Engineering (Phase 3) as historical consumption minus post-event consumption.
- **`financial_leakage`**: Derived in Evaluation (Phase 5) from unmetered volume multiplied by tariff rate.

### Group C: Fields Sourced from External Metadata
- **`tariff_rate`**: Generally sourced from utility billing rate tables (`data/external/tariffs.yaml` or `.parquet`).
- **`feeder_id` / Substation**: Sourced from GIS network topology.
- **`dispatch_cost`**: Operational cost to dispatch an inspection team to a given geographic district.

### Group D: Fields Unavailable in Specific Datasets
- *SGCC Dataset*: Feeder identifiers, geographical coordinates, and explicit customer classes are not provided in the public benchmark. Feature extraction must rely solely on temporal consumption dynamics and cross-consumer statistical clusters.

---

## 4. Layout Representations & Physical Ingestion

### Format 1: Wide Layout (e.g. SGCC China Benchmark)
```csv
CONS_NO,2014/1/1,2014/1/2,2014/1/3,...,2016/10/31,FLAG
4B75AC4F...,0.0,4.98,9.87,...,1.16,1
```
- Ingestion action: `DataIngestionEngine` verifies `CONS_NO` and `FLAG`, discovers date-formatted columns, and Phase 2 unpivots them to long format.

### Format 2: Long Layout (Standard Canonical AMI)
```csv
meter_id,timestamp,consumption_kwh,tariff_id,customer_class,is_tampered
MTR_001,2024-01-01 00:00:00,1.42,RES_T1,residential,0
```
- Ingestion action: Direct 1-to-1 mapping via `configs/dataset_mappings.yaml`.

---

## 5. Quality & Integrity Assertions

Downstream ML models depend on the following strict quality invariants validated by `DataValidator`:

1. **Uniqueness**:
   - Wide format: `CONS_NO` must be unique per row.
   - Long format: `(meter_id, timestamp)` composite key must be unique.
2. **Missing Values**:
   - `meter_id` must have 0% null values.
   - Time-series gaps must be quantified; imputation policies are configured in Phase 2.
3. **Negative Values**:
   - Negative consumption is flagged. By default, negative values indicate anomalies or sensor errors unless `allow_negative_consumption=True` is enabled for bidirectional net metering.
4. **Chronological Consistency**:
   - Timestamps must proceed in non-decreasing order per meter.
