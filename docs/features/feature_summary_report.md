# Grid-Guard Feature Quality & Validation Report

**Total Records Processed**: 43,812,648
**Unique Meters**: 42,372
**Total Engineered Features**: 60
**Duplicate (meter_id, timestamp) Pairs**: 0
**Infinite Value Anomalies**: 0

## Integrity Checks
- **Finite Values**: PASSED (0 infinite values)
- **Timestamp Uniqueness**: PASSED (0 duplicates)
- **Constant Features**: 2 (missing_count_30d, missing_ratio_30d)

## Feature Distributions & Null Rates

| Feature | Dtype | Null % | Min | Max | Mean | Std |
|---|---|---|---|---|---|---|
| `consumption_kwh` | Float32 | 24.98% | 0.0 | 800003.3125 | 9.3475 | 311.823 |
| `coverage_ratio` | Float32 | 0.0% | 0.0 | 1.0 | 0.7502 | 0.2911 |
| `missing_ratio` | Float32 | 0.0% | 0.0 | 1.0 | 0.2498 | 0.2911 |
| `imputation_ratio` | Float32 | 0.0% | 0.0 | 0.1006 | 0.0066 | 0.0078 |
| `day_of_week` | Int8 | 0.0% | 1.0 | 7.0 | 3.999 | 1.9988 |
| `day_of_month` | Int8 | 0.0% | 1.0 | 31.0 | 15.7292 | 8.805 |
| `month` | Int8 | 0.0% | 1.0 | 12.0 | 6.2253 | 3.3217 |
| `quarter` | Int8 | 0.0% | 1.0 | 4.0 | 2.4197 | 1.0879 |
| `is_weekend` | Int8 | 0.0% | 0.0 | 1.0 | 0.2853 | 0.4516 |
| `dow_sin` | Float32 | 0.0% | -0.9749 | 0.9749 | -0.0009 | 0.7071 |
| `dow_cos` | Float32 | 0.0% | -0.901 | 1.0 | -0.0008 | 0.7071 |
| `month_sin` | Float32 | 0.0% | -1.0 | 1.0 | 0.0106 | 0.7209 |
| `month_cos` | Float32 | 0.0% | -1.0 | 1.0 | -0.0571 | 0.6906 |
| `consumption_kwh_lag_1d` | Float32 | 25.07% | 0.0 | 800003.3125 | 9.3489 | 312.0102 |
| `consumption_kwh_lag_2d` | Float32 | 25.17% | 0.0 | 800003.3125 | 9.3502 | 312.196 |
| `consumption_kwh_lag_3d` | Float32 | 25.26% | 0.0 | 800003.3125 | 9.3508 | 312.3813 |
| `consumption_kwh_lag_7d` | Float32 | 25.65% | 0.0 | 800003.3125 | 9.3499 | 313.1243 |
| `consumption_kwh_lag_14d` | Float32 | 26.32% | 0.0 | 800003.3125 | 9.3523 | 314.4539 |
| `consumption_kwh_lag_30d` | Float32 | 27.84% | 0.0 | 800003.3125 | 9.3568 | 317.5416 |
| `rolling_mean_7d` | Float32 | 25.89% | 0.0 | 228571.4219 | 9.3036 | 156.9974 |
| `rolling_std_7d` | Float32 | 25.89% | 0.0 | 314718.375 | 2.4305 | 248.2882 |
| `rolling_min_7d` | Float32 | 25.89% | 0.0 | 23880.0 | 6.5072 | 46.1167 |
| `rolling_max_7d` | Float32 | 25.89% | 0.0 | 800003.3125 | 13.0753 | 635.1364 |
| `rolling_median_7d` | Float32 | 25.22% | 0.0 | 800003.3125 | 9.0616 | 178.8091 |
| `rolling_mean_14d` | Float32 | 26.99% | 0.0 | 114285.7109 | 9.2681 | 114.691 |
| `rolling_std_14d` | Float32 | 26.99% | 0.0 | 231573.7344 | 2.8297 | 234.0621 |
| `rolling_mean_30d` | Float32 | 29.32% | 0.0 | 53333.332 | 9.1986 | 79.3812 |
| `rolling_std_30d` | Float32 | 29.32% | 0.0 | 161031.1719 | 3.1945 | 176.332 |
| `rolling_min_30d` | Float32 | 29.32% | 0.0 | 12780.0 | 4.7404 | 28.2236 |
| `rolling_max_30d` | Float32 | 29.32% | 0.0 | 800003.3125 | 17.652 | 831.1385 |
| `rolling_median_30d` | Float32 | 26.07% | 0.0 | 600003.3125 | 8.9816 | 170.687 |
| `rolling_mean_60d` | Float32 | 33.35% | 0.0 | 26666.666 | 9.1549 | 66.4796 |
| `rolling_std_60d` | Float32 | 33.35% | 0.0 | 114684.6016 | 3.6983 | 151.7974 |
| `rolling_mean_90d` | Float32 | 37.14% | 0.0 | 20393.334 | 9.0879 | 60.3052 |
| `rolling_std_90d` | Float32 | 37.14% | 0.0 | 93856.1406 | 3.9697 | 106.6012 |
| `missing_count_30d` | Int8 | 0.0% | 0.0 | 0.0 | 0.0 | 0.0 |
| `missing_ratio_30d` | Float32 | 0.0% | 0.0 | 0.0 | 0.0 | 0.0 |
| `ratio_7d_30d` | Float32 | 29.32% | 0.0 | 4.2857 | 1.0134 | 0.4684 |
| `ratio_14d_60d` | Float32 | 33.35% | 0.0 | 4.2857 | 1.0156 | 0.4994 |
| `ratio_30d_90d` | Float32 | 37.14% | 0.0 | 3.0 | 1.0106 | 0.4161 |
| `wow_consumption_change` | Float32 | 27.17% | -228571.4219 | 228571.4219 | -0.0057 | 182.2643 |
| `wow_consumption_ratio` | Float32 | 28.14% | 0.0 | 491621.0312 | 2.0219 | 217.873 |
| `par_7d` | Float32 | 25.89% | 1.0 | 7.0 | 1.4947 | 0.9042 |
| `par_30d` | Float32 | 29.32% | 1.0 | 30.0 | 2.6166 | 4.0142 |
| `zero_count_7d` | Int8 | 0.29% | 0.0 | 7.0 | 0.9304 | 2.2845 |
| `zero_ratio_7d` | Float32 | 0.29% | 0.0 | 1.0 | 0.1329 | 0.3264 |
| `zero_count_30d` | Int8 | 1.35% | 0.0 | 30.0 | 3.9588 | 9.4852 |
| `zero_ratio_30d` | Float32 | 1.35% | 0.0 | 1.0 | 0.132 | 0.3162 |
| `current_zero_streak` | Int32 | 0.0% | 0.0 | 1034.0 | 20.0524 | 90.8948 |
| `rolling_cv_7d` | Float32 | 25.89% | 0.0 | 2.6458 | 0.2934 | 0.4273 |
| `rolling_cv_30d` | Float32 | 29.32% | 0.0 | 5.4772 | 0.4916 | 0.8308 |
| `daily_diff_abs_7d_mean` | Float32 | 26.13% | 0.0 | 186714.7344 | 2.1794 | 159.8724 |
| `flatline_streak` | Int32 | 0.0% | 0.0 | 1033.0 | 21.4466 | 93.7773 |
| `baseline_deviation_ratio` | Float32 | 35.83% | 0.0 | 732574.25 | 4.4334 | 537.081 |
| `sustained_drop_ratio` | Float32 | 10.85% | 0.0 | 1.0 | 0.1066 | 0.2277 |
| `sustained_drop_magnitude` | Float32 | 4.16% | 0.0 | 26666.666 | 0.858 | 26.0907 |
| `sustained_drop_duration` | Int32 | 0.0% | 0.0 | 178.0 | 3.7344 | 12.4178 |
| `dow_profile_deviation` | Float32 | 29.69% | -200000.3281 | 53532.0 | -0.0895 | 107.8698 |
| `dow_profile_ratio` | Float32 | 30.08% | 0.0 | 2614967.75 | 1.7652 | 495.7411 |
| `weekly_autocorr_30d` | Float32 | 32.29% | -1.0 | 1.0 | 0.2004 | 0.3475 |
