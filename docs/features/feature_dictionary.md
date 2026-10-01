# Grid-Guard Feature Dictionary

This document provides the authoritative registry of all temporal features 
and tampering signatures extracted from smart-meter AMI time series.

**Total Features Registered**: 62

## Summary by Category

| Category | Count | Description |
|---|---|---|
| Calendar | 9 | Day-of-week, month, cyclical harmonic representations |
| Lag | 6 | Historical backward observation lags (1d, 7d, etc.) |
| Rolling | 16 | Trailing window statistics (mean, std, min, max) |
| Ratio | 3 | Multi-scale moving average ratios (e.g. 7d/30d, 14d/60d) |
| Peak | 2 | Peak-to-Average Ratios (PAR) over trailing windows |
| Behavior Shift | 2 | Week-over-week consumption and volatility shifts |
| Zero Streak | 5 | Zero-consumption counts, ratios, and streak tracking |
| Variability | 4 | Rolling coefficient of variation and flatline indicators |
| Step Down | 4 | Sustained collapse from historical baseline & duration |
| Autocorrelation | 3 | Weekly lag correlation & personal DOW profile deviation |
| Peer Context | 3 | Feeder/neighborhood group divergence (where metadata exists) |
| Data Quality | 5 | Coverage, missingness, and data-quality status indicators |

---

## Feature Specifications

| Feature Name | Category | Window | Lag | Dtype | Leakage Risk | Description |
|---|---|---|---|---|---|---|
| `day_of_week` | calendar | - | - | `Int8` | safe | Day of week (1=Monday, 7=Sunday) |
| `day_of_month` | calendar | - | - | `Int8` | safe | Day of month (1-31) |
| `month` | calendar | - | - | `Int8` | safe | Calendar month (1-12) |
| `quarter` | calendar | - | - | `Int8` | safe | Calendar quarter (1-4) |
| `is_weekend` | calendar | - | - | `Int8` | safe | Binary indicator for Saturday or Sunday (1=Weekend, 0=Weekday) |
| `dow_sin` | calendar | - | - | `Float32` | safe | Cyclical sine encoding of day of week |
| `dow_cos` | calendar | - | - | `Float32` | safe | Cyclical cosine encoding of day of week |
| `month_sin` | calendar | - | - | `Float32` | safe | Cyclical sine encoding of calendar month |
| `month_cos` | calendar | - | - | `Float32` | safe | Cyclical cosine encoding of calendar month |
| `consumption_kwh_lag_1d` | lag | - | 1d | `Float32` | warmup_dependent | Backward historical consumption reading shifted by 1 days |
| `consumption_kwh_lag_2d` | lag | - | 2d | `Float32` | warmup_dependent | Backward historical consumption reading shifted by 2 days |
| `consumption_kwh_lag_3d` | lag | - | 3d | `Float32` | warmup_dependent | Backward historical consumption reading shifted by 3 days |
| `consumption_kwh_lag_7d` | lag | - | 7d | `Float32` | warmup_dependent | Backward historical consumption reading shifted by 7 days |
| `consumption_kwh_lag_14d` | lag | - | 14d | `Float32` | warmup_dependent | Backward historical consumption reading shifted by 14 days |
| `consumption_kwh_lag_30d` | lag | - | 30d | `Float32` | warmup_dependent | Backward historical consumption reading shifted by 30 days |
| `rolling_mean_7d` | rolling | 7d | - | `Float32` | warmup_dependent | Trailing 7-day rolling mean consumption |
| `rolling_std_7d` | rolling | 7d | - | `Float32` | warmup_dependent | Trailing 7-day rolling standard deviation of consumption |
| `rolling_min_7d` | rolling | 7d | - | `Float32` | warmup_dependent | Trailing 7-day minimum consumption reading |
| `rolling_max_7d` | rolling | 7d | - | `Float32` | warmup_dependent | Trailing 7-day maximum (peak) consumption reading |
| `rolling_median_7d` | rolling | 7d | - | `Float32` | warmup_dependent | Trailing 7-day median (50th percentile) consumption |
| `rolling_mean_14d` | rolling | 14d | - | `Float32` | warmup_dependent | Trailing 14-day rolling mean consumption |
| `rolling_std_14d` | rolling | 14d | - | `Float32` | warmup_dependent | Trailing 14-day rolling standard deviation of consumption |
| `rolling_mean_30d` | rolling | 30d | - | `Float32` | warmup_dependent | Trailing 30-day rolling mean consumption |
| `rolling_std_30d` | rolling | 30d | - | `Float32` | warmup_dependent | Trailing 30-day rolling standard deviation of consumption |
| `rolling_min_30d` | rolling | 30d | - | `Float32` | warmup_dependent | Trailing 30-day minimum consumption reading |
| `rolling_max_30d` | rolling | 30d | - | `Float32` | warmup_dependent | Trailing 30-day maximum (peak) consumption reading |
| `rolling_median_30d` | rolling | 30d | - | `Float32` | warmup_dependent | Trailing 30-day median (50th percentile) consumption |
| `rolling_mean_60d` | rolling | 60d | - | `Float32` | warmup_dependent | Trailing 60-day rolling mean consumption |
| `rolling_std_60d` | rolling | 60d | - | `Float32` | warmup_dependent | Trailing 60-day rolling standard deviation of consumption |
| `rolling_mean_90d` | rolling | 90d | - | `Float32` | warmup_dependent | Trailing 90-day rolling mean consumption |
| `rolling_std_90d` | rolling | 90d | - | `Float32` | warmup_dependent | Trailing 90-day rolling standard deviation of consumption |
| `ratio_7d_30d` | ratio | 30d | - | `Float32` | warmup_dependent | Ratio of trailing 7-day mean to 30-day baseline mean |
| `ratio_14d_60d` | ratio | 60d | - | `Float32` | warmup_dependent | Ratio of trailing 14-day mean to 60-day baseline mean |
| `ratio_30d_90d` | ratio | 90d | - | `Float32` | warmup_dependent | Ratio of trailing 30-day mean to 90-day baseline mean |
| `wow_consumption_change` | behavior_shift | 14d | 7d | `Float32` | warmup_dependent | Absolute week-over-week difference in 7-day rolling mean |
| `wow_consumption_ratio` | behavior_shift | 14d | 7d | `Float32` | warmup_dependent | Ratio of current 7-day mean to preceding 7-day mean (lagged by 7d) |
| `par_7d` | peak | 7d | - | `Float32` | warmup_dependent | Peak-to-Average Ratio over trailing 7 days (max_7d / mean_7d) |
| `par_30d` | peak | 30d | - | `Float32` | warmup_dependent | Peak-to-Average Ratio over trailing 30 days (max_30d / mean_30d) |
| `zero_count_7d` | zero_streak | 7d | - | `Int8` | warmup_dependent | Number of zero or near-zero consumption days in trailing 7 days |
| `zero_ratio_7d` | zero_streak | 7d | - | `Float32` | warmup_dependent | Proportion of zero or near-zero days in trailing 7 days |
| `zero_count_30d` | zero_streak | 30d | - | `Int8` | warmup_dependent | Number of zero or near-zero consumption days in trailing 30 days |
| `zero_ratio_30d` | zero_streak | 30d | - | `Float32` | warmup_dependent | Proportion of zero or near-zero days in trailing 30 days |
| `current_zero_streak` | zero_streak | - | - | `Int32` | safe | Current trailing count of consecutive zero-consumption days |
| `rolling_cv_7d` | variability | 7d | - | `Float32` | warmup_dependent | Trailing 7-day coefficient of variation (std / safe(mean)) |
| `rolling_cv_30d` | variability | 30d | - | `Float32` | warmup_dependent | Trailing 30-day coefficient of variation (std / safe(mean)) |
| `daily_diff_abs_7d_mean` | variability | 7d | - | `Float32` | warmup_dependent | Trailing 7-day mean of absolute day-to-day consumption changes |
| `flatline_streak` | variability | - | - | `Int32` | safe | Trailing consecutive days of near-constant consumption (|diff| <= tol) |
| `baseline_deviation_ratio` | step_down | 74d | 14d | `Float32` | warmup_dependent | Ratio of recent 14-day consumption to historical baseline (60d shifted by 14d) |
| `sustained_drop_ratio` | step_down | 74d | 14d | `Float32` | warmup_dependent | Fractional drop from baseline: max(0, 1 - (recent_14d / safe(baseline_60d))) |
| `sustained_drop_magnitude` | step_down | 74d | 14d | `Float32` | warmup_dependent | Absolute consumption collapse: max(0, baseline_60d - recent_14d) in kWh |
| `sustained_drop_duration` | step_down | 74d | 14d | `Int32` | warmup_dependent | Trailing consecutive days where consumption < 50% of historical baseline |
| `dow_profile_deviation` | autocorrelation | 28d | 7d | `Float32` | warmup_dependent | Difference between current reading and average of past 4 same-weekday readings |
| `dow_profile_ratio` | autocorrelation | 28d | 7d | `Float32` | warmup_dependent | Ratio of current reading to average of past 4 same-weekday readings |
| `weekly_autocorr_30d` | autocorrelation | 30d | 7d | `Float32` | warmup_dependent | Trailing 30-day autocorrelation with 7-day backward lag |
| `peer_group_mean` | peer_context | - | - | `Float32` | context_dependent | Leave-one-out peer average consumption for the same timestamp and feeder |
| `meter_to_peer_ratio` | peer_context | - | - | `Float32` | context_dependent | Ratio of meter consumption to leave-one-out peer group average |
| `peer_group_deviation` | peer_context | - | - | `Float32` | context_dependent | Absolute difference between meter consumption and leave-one-out peer group mean |
| `coverage_ratio` | data_quality | - | - | `Float32` | safe | Historical proportion of valid observed days per meter |
| `missing_ratio` | data_quality | - | - | `Float32` | safe | Historical proportion of missing reading days per meter |
| `imputation_ratio` | data_quality | - | - | `Float32` | safe | Historical proportion of values linearly imputed during cleaning |
| `missing_count_30d` | data_quality | 30d | - | `Int8` | warmup_dependent | Trailing 30-day count of null / missing readings for this meter |
| `missing_ratio_30d` | data_quality | 30d | - | `Float32` | warmup_dependent | Trailing 30-day proportion of null / missing readings for this meter |
