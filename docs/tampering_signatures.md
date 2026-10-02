# Grid-Guard Non-Technical Loss Tampering Signatures

## 1. Domain Background & Rationale

Machine learning models predict probability based on complex high-dimensional non-linear boundaries. However, in electricity distribution utilities, field inspection technicians evaluate physical meters and service drops based on recognizable physical and behavioral signatures.

Grid-Guard implements a deterministic rule-based signature detection layer that operates alongside Tree-SHAP. These signatures:
1. **Provide Domain Verification**: Confirm that high model scores correspond to recognizable electrical load anomalies.
2. **Quantify Evidence Duration & Magnitude**: Measure how long the anomaly has persisted and how many kWh/day have disappeared.
3. **Enhance Operational Trust**: Technicians receive intuitive engineering descriptions rather than purely abstract statistical weights.

---

## 2. Signature Specifications

### Signature 1: Sustained Step-Down (Consumption Collapse)
* **Electrical Mechanism**: Partial meter bypass, shunt calibration alteration, or secondary circuit bridging that diverts a fixed percentage of current around the measurement transducer.
* **Telemetry Pattern**: Electricity consumption drops abruptly and remains structurally below the historical baseline without recovering.
* **Detection Criteria**:
  * Trailing 14-day average vs. 60-day baseline: `ratio_14d_60d <= 0.50`, OR
  * Consecutive days below 50% baseline: `sustained_drop_duration >= 7` days, OR
  * Fractional drop: `sustained_drop_ratio >= 0.40`.
* **Severity Grading**:
  * **HIGH**: Consumption deficit $\ge 70\%$ or duration $\ge 14$ consecutive days.
  * **MODERATE**: Consumption deficit $\ge 50\%$ or duration $\ge 7$ consecutive days.
  * **LOW**: Consumption deficit $\ge 35\%$.
* **Example Output**:
  `[HIGH SEVERITY] Sustained Step-Down: Sustained consumption reduction of 100.0% below historical baseline (221.8 kWh/day deficit) persisting for 21 consecutive days.`

---

### Signature 2: Zero Streak (Total Bypass / Disconnection)
* **Electrical Mechanism**: Complete meter bypass, inverted current transformer (CT), physical disconnection of voltage reference, or unregistered direct tap.
* **Telemetry Pattern**: Telemetry registers zero or near-zero ($< 0.001$ kWh) consumption on consecutive days for a historically active account.
* **Detection Criteria**:
  * Active continuous streak: `current_zero_streak >= 3` consecutive days, OR
  * Weekly zero count: `zero_count_7d >= 3` days, OR
  * Monthly zero count: `zero_count_30d >= 10` days.
* **Severity Grading**:
  * **HIGH**: Streak $\ge 7$ consecutive days or $\ge 5$ zero days in past week.
  * **MODERATE**: Streak $\ge 3$ consecutive days or $\ge 3$ zero days in past week.
* **Example Output**:
  `[HIGH SEVERITY] Zero Streak: Active streak of 10 consecutive days with zero metered consumption.`

---

### Signature 3: Flatline (Artificial Load Invariance)
* **Electrical Mechanism**: Defective meter register stuck at a fixed value, illicit constant-load tapping, or simulated artificial load signals.
* **Telemetry Pattern**: Natural human consumption exhibits pronounced daily variance driven by weather, occupancy, and circadian rhythms. Flatline signatures exhibit near-zero variance across consecutive days.
* **Detection Criteria**:
  * Consecutive identical readings: `flatline_streak >= 7` days ($|\Delta| \le 0.01$ kWh), OR
  * Rolling Coefficient of Variation: `rolling_cv_7d < 0.05` where mean load $> 0.05$ kWh/day.
* **Severity Grading**:
  * **HIGH**: Flatline streak $\ge 14$ days or CV $< 0.01$.
  * **MODERATE**: Flatline streak $\ge 7$ days or CV $< 0.05$.
* **Example Output**:
  `[MODERATE SEVERITY] Flatline: Consumption has remained near-constant for 7 consecutive days with negligible daily load variance.`

---

### Signature 4: Behavioral Regime Shift (Abrupt Contraction)
* **Electrical Mechanism**: Recent installation of an unauthorized diversion tap or unmetered sub-panel.
* **Telemetry Pattern**: Sharp discontinuity between adjacent multi-day rolling periods (e.g. 7-day load relative to 30-day baseline).
* **Detection Criteria**:
  * Ratio: `ratio_7d_30d < 0.45`, OR
  * Week-over-week contraction: `wow_consumption_change < -0.50` (50% contraction).
* **Severity Grading**: Moderate.
* **Example Output**:
  `[MODERATE SEVERITY] Behavior Shift: Week-over-week consumption contracted by 100.0%.`

---

### Signature 5: Abnormal Peak-to-Average Load (PAR Collapse)
* **Electrical Mechanism**: Bypassing heavy domestic appliances (air conditioning, space heating, water heaters) while leaving lighting and light loads metered.
* **Telemetry Pattern**: Normal customer load profiles exhibit pronounced peak-to-average ratios ($> 1.30$). Bypassing high-draw appliances causes PAR to collapse to near-unity ($< 1.05$).
* **Detection Criteria**:
  * Trailing 7-day PAR: `par_7d < 1.05` while historical baseline `par_30d > 1.30`.
* **Severity Grading**: Low.
* **Example Output**:
  `[LOW SEVERITY] Abnormal Peak Behavior: Peak-to-Average Ratio collapsed from 30d baseline (1.42) to near-unity (1.02) over trailing 7 days.`

---

## 3. Strict Safety & Regulatory Boundary

> [!CAUTION]
> Tampering signatures describe **statistical and electrical patterns**, NOT proven physical facts. A sustained step-down can legitimately be caused by customer relocation, seasonal vacancy, solar PV installation, or energy efficiency retrofits. All signatures must be communicated as anomalous evidence requiring field verification.
