# Grid-Guard Demonstration & Presentation Walkthrough

This guide provides an end-to-end technical narrative for presenting **Grid-Guard** to professors, technical evaluators, hackathon judges, and electrical utility executives.

---

## Executive Summary Script

> *"Grid-Guard is a financial-aware non-technical loss (NTL) detection and field inspection prioritization platform. Traditional electricity theft models treat all detection errors equally. In real-world distribution utilities, sending an inspection crew costs $100, while revenue leakage ranges from $5 on a rural lifeline meter to $150,000 on a heavy commercial account. Grid-Guard pairs a 60-feature temporal extraction pipeline and a financially weighted LightGBM objective with dynamic Expected Net Value (ENV) ranking and Tree-SHAP explainability to maximize utility net recovery."*

---

## 10-Step Presentation Walkthrough

### Step 1: Start Services & Launch Dashboard
1. Run the unified launcher from your terminal:
   ```bash
   uv run python scripts/run_services.py
   ```
2. Open your web browser to:
   - **Operational Dashboard**: `http://localhost:8501`
   - **FastAPI OpenAPI Docs**: `http://localhost:8000/docs`

---

### Step 2: Show Fleet Overview (The Business Problem)
1. In the sidebar, select **"📊 Fleet Overview"**.
2. Point out the top KPI row:
   - **Monitored Smart Meters**: `42,372` meters in the SGCC benchmark snapshot.
   - **Recommended Inspections**: `801` meters (1.89% of fleet).
   - **Expected Gross Recovery**: `$355,330.47`.
   - **Total Crew Dispatch Cost**: `$80,100.00`.
   - **Expected Net Value (ENV)**: **`+$275,230.47` Net ROI** after fully paying dispatch expenses.
3. Contrast with a naive fixed-threshold policy ($p \ge 0.50$):
   - Naive thresholding only captures $170 inspections and leaves massive unmetered leakage behind, suffering **$82,685** in operational loss compared to Grid-Guard's **$64,842** (a **21.6% reduction in operational loss**).

---

### Step 3: Prioritized Inspection Queue
1. In the sidebar, select **"📋 Inspection Queue"**.
2. Explain that candidate meters are ranked **strictly by Expected Net Value (ENV) descending**:
   $$\text{ENV}_i = p_i \times R_i - C_{\text{dispatch}}$$
3. Demonstrate live filtering:
   - Search for a specific meter ID (e.g. `1000282`).
   - Adjust the **Min Tamper Probability** slider from 0.0 to 0.70.
   - Adjust the **Min Expected Net Value** slider to show only high-yield cases ($>\$1,000$).
4. Click **"📥 Export Queue (CSV)"** to show how field operations can export work orders directly into their dispatch management system.
5. Click **"🔎 Investigate Selected Meter"** to demonstrate seamless drilldown into the detailed analysis view.

---

### Step 4: The 5 Demonstration Archetypes (Meter Analysis)
1. Navigate to **"🔬 Meter Analysis"**.
2. Grid-Guard includes **5 deterministic synthetic demo archetypes** illustrating core operational regimes:

| Archetype | Key Scenario | Tamper Probability | Modeled Recovery | Expected Net Value | Recommendation |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **1. Normal Residential** | Consistent 12–15 kWh/day usage | Low (~6.5%) | Minimal | Negative (-$494) | ⚪ Do Not Dispatch |
| **2. Sustained Step-Down** | 28 kWh/day drops to 1.2 kWh/day | High (~35.9%) | ~$28,600 | **+$9,756** | 🟢 Dispatch |
| **3. Flatline Invariance** | Unvarying constant 1.0 kWh/day | Elevated (~7.5%) | ~$8,200 | **+$521** | 🟢 Dispatch |
| **4. High-Value Commercial** | 240 kWh/day drops to 40 kWh/day | Very High (~87.4%)| ~$205,000 | **+$179,270** | 🟢 Dispatch (#1 Priority) |
| **5. Lifeline (High Prob / Low ENV)** | 0.25 kWh/day drops to 0.03 kWh | Detected Anomaly | ~$12 | **-$89 (Negative)** | ⚪ Do Not Dispatch |

---

### Step 5: Highlight the Core Innovation — The Lifeline Case
1. In the demo dropdown, select **"High Risk / Low Net Value (Lifeline)"**.
2. Click **"⚡ Score Meter & Generate Ticket"**.
3. **The Proof Point for Judges**:
   - The model clearly detects the relative drop.
   - However, because the consumer only uses 0.25 kWh/day, total 12-month recoverable revenue is only **~$12.00**.
   - Dispatching a two-person physical inspection crew costs **$100.00**.
   - A naive machine-learning system flags this meter because the percentage drop is high.
   - **Grid-Guard's ENV Engine rejects the inspection**: $\text{ENV} = -\$89 < 0$.
   - **Business Outcome**: Saves the distribution utility from throwing away $100 on an economically unviable field dispatch!

---

### Step 6: High-Value Commercial Account
1. Select **"High-Value Commercial Account"**.
2. Click **"⚡ Score Meter & Generate Ticket"**.
3. Point out the massive figures:
   - **Tamper Probability**: `87.4%`
   - **Expected Net Value**: **`+$179,270.29`**
   - The daily consumption time-series chart highlights the pre-drop baseline (~240 kWh/day) and the shaded 30-day evaluation window.

---

### Step 7: Tree-SHAP Local Feature Attribution
1. Scroll down to Section 4 of the Meter Analysis view: **"Local Tree-SHAP Attribution"**.
2. Explain the horizontal bar chart:
   - **Red bars (positive log-odds)**: Features that pushed the model toward predicting tampering (e.g. `Mean Consumption Ratio 30D Over Historical`, `Sustained Drop Duration Days`).
   - **Green bars (negative log-odds)**: Features that provided counter-evidence (e.g. `Historical Consumption Variance`).
3. Note that Tree-SHAP calculates exact Shapley values directly from the LightGBM tree structure in under 15ms.

---

### Step 8: Actionable Work Order Ticket & Field Safety Caveat
1. View the rendered **Field Work Order Ticket**:
   - Deterministic ticket ID (e.g. `TCK-2016-10-30-EF550F26`).
   - Identified Electrical Tampering Signatures (e.g. *"Sustained consumption reduction"*).
   - Audited narrative explanation.
   - **Operational Safety Disclaimer**: Explicitly instructs field staff that model signals warrant physical inspection but do not constitute legal accusation of theft.
2. Click **"📥 Export Work Order (JSON)"** to show integration with enterprise ERP/GIS.

---

### Step 9: Multi-Phase Machine Learning Progression
1. Navigate to **"📈 Model Insights"**.
2. Walk through the multi-phase engineering progression:
   - **Phase 4 (Unweighted Baseline)**: PR-AUC 0.3035, Total Loss $1,972,700.
   - **Phase 5 (SMOTE-Tomek Imbalance)**: Balanced sampling reduced false negatives but increased false alarms.
   - **Phase 6 (Cost-Sensitive Champion)**: Direct financial weighting reduced Total Operational Loss to **$1,489,400** (a **24.5% financial loss reduction** over the baseline).

---

### Step 10: System Introspection & Live Health Probes
1. Navigate to **"⚙️ System Status"**.
2. Show the live **Liveness (`/health`)** and **Readiness (`/ready`)** probe indicators connected to the running backend.
3. Show model checkpoint metadata (60 features, `phase6_cost_sensitive_dispatch_norm`, Tree-SHAP explainer).
4. Conclude by demonstrating that no secrets or local filesystem paths are exposed in the interface.
