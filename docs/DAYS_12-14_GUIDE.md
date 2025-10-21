# Days 12-14: Copilot-Accelerated Completion Guide

**Status**: You're at 80% complete. These 3 days add the final 20% that transforms a great submission into a 1st place winner.

**Time Allocation**:
- Day 12: BigQuery ML (4-5 hours actual work, Copilot does 60%)
- Day 13: React Dashboard (3-4 hours, Copilot does 70%)
- Day 14: Demo Prep & Polish (2-3 hours, Copilot does 50%)

**Total time investment: 9-12 hours** (Copilot saves you 30-40 hours of work)

---

## Day 12: BigQuery ML - Predictive Anomaly Model

### What You're Building
ML model that learns from historical alerts to predict anomalies in new data. This adds ML badge to your hackathon submission.

### Setup (30 minutes)

1. **Create BigQuery ML directory**:
```bash
mkdir -p ml/models ml/training ml/evaluation
touch ml/__init__.py ml/bigquery_ml.py ml/training/train.py ml/evaluation/evaluate.py
```

2. **Enable BigQuery ML in your project** (already enabled, but verify):
```bash
gcloud bigquery ml list --dataset_id=osprey_data
```

### Copilot Task 1: Training Data Pipeline

**Prompt to give Copilot:**

```
Create a Python module that:
1. Connects to BigQuery osprey_data dataset
2. Creates a table 'training_data' with features:
   - sentiment_score (FLOAT)
   - title_length (INT64) - LENGTH(title)
   - content_length (INT64) - LENGTH(content)
   - num_stocks (INT64) - ARRAY_LENGTH of stock_symbols
   - age_hours (INT64) - hours since published
   - published_hour (INT64) - hour of day
   - is_test_data (BOOL) - label (1 if in quarantine, 0 if clean)

3. Query raw_news table and create labeled dataset
4. Handle null values appropriately
5. Split into train (70%) and test (30%)
6. Return statistics: total rows, positive examples, negative examples

File: ml/training/train.py
Class: TrainingDataPipeline
Methods: prepare_training_data(), get_statistics()
```

### Copilot Task 2: BigQuery ML Model Training

**Prompt to give Copilot:**

```
Create a BigQuery ML training module that:

1. Creates a LOGISTIC_REGRESSION model named 'anomaly_predictor_v1'
2. Trains on 'training_data' table with:
   - Input features: sentiment_score, title_length, content_length, num_stocks, age_hours, published_hour
   - Label: is_test_data
   - Train/test split: AUTO_SPLIT (70/30)

3. Evaluates model performance:
   - Accuracy
   - Precision
   - Recall
   - AUC-ROC

4. Generates predictions on recent data (last 7 days)

File: ml/models/train_model.sql and ml/bigquery_ml.py
Include functions:
- create_model()
- evaluate_model()
- predict_on_new_data(days_back=7)
- get_model_metrics()

Output metrics as JSON for dashboard consumption.
```

### Copilot Task 3: Integrate ML into Anomaly Detective

**Prompt to give Copilot:**

```
Modify agents/anomaly_detective.py to integrate BigQuery ML predictions:

1. Add method get_ml_predictions(confidence_threshold=0.7):
   - Query predictions from BigQuery model
   - Return articles with anomaly_probability > threshold
   - Include article_id, predicted_anomaly_prob, feature_importance

2. Add method combine_ml_and_ai_detection():
   - Get Gemini analysis results
   - Get ML predictions
   - Combine signals:
     * If both flag as anomaly: confidence = (gemini_conf + ml_prob) / 2
     * If only one flags: lower confidence
   - Return combined alert with both signals shown

3. Add historical tracking:
   - Store prediction accuracy over time
   - Warn if model accuracy drops below 85%

Return enriched anomaly alerts with both AI and ML evidence.
```

### Day 12 Checkpoint: Testing

```bash
# Test 1: Training data created
bq query --use_legacy_sql=false \
  "SELECT COUNT(*) as row_count FROM \`osprey-hackathon-2025.osprey_data.training_data\`"

# Test 2: Model exists
bq query --use_legacy_sql=false \
  "SELECT * FROM ML.EVALUATE(MODEL \`osprey-hackathon-2025.osprey_data.anomaly_predictor_v1\`)"

# Test 3: Predictions work
bq query --use_legacy_sql=false \
  "SELECT article_id, predicted_is_test_data_probs FROM ML.PREDICT(MODEL \`osprey-hackathon-2025.osprey_data.anomaly_predictor_v1\`, (SELECT * FROM \`osprey-hackathon-2025.osprey_data.raw_news\` LIMIT 10))"

# Test 4: Python integration
uv run python -c "from ml.bigquery_ml import BigQueryML; ml = BigQueryML('osprey-hackathon-2025'); print(ml.get_model_metrics())"
```

---

## Day 13: React Dashboard (Real-Time Monitoring UI)

### What You're Building
Professional monitoring dashboard showing:
- 3 agent status cards (live)
- Alert feed (real-time scrolling)
- Decision log with reasoning
- Agent communication visualization
- Executive summary

### Quick Setup (10 minutes)

```bash
cd dashboard
npx create-react-app . --template typescript
npm install recharts lucide-react axios @tanstack/react-query
npm install -D tailwindcss postcss autoprefixer
npx tailwindcss init -p
```

### Copilot Task 1: Agent Status Component

**Prompt to give Copilot:**

```
Create a React TypeScript component that displays real-time agent status.

Requirements:
1. Component: AgentStatus
2. Shows 3 cards in a grid:
   - Schema Guardian (with shield icon)
   - Anomaly Detective (with search icon)
   - Pipeline Orchestrator (with workflow icon)

3. Each card displays:
   - Agent name
   - Status badge (green=running, red=paused, yellow=warning)
   - Last check timestamp
   - Alerts today count
   - "Monitoring..." pulse animation when active

4. Refresh data every 5 seconds from http://localhost:8000/api/status endpoint

5. Style with Tailwind: dark background (gray-900), blue accents
6. Use Lucide React icons
7. Handle loading and error states

File: dashboard/src/components/AgentStatus.tsx
Export: AgentStatus component (no props needed)

Make it production-ready with proper TypeScript types.
```

### Copilot Task 2: Real-Time Alert Feed

**Prompt to give Copilot:**

```
Create a React component for real-time alert feed.

Requirements:
1. Component: AlertFeed
2. Displays last 20 alerts in reverse chronological order (newest first)
3. Fetches from http://localhost:8000/api/alerts endpoint every 3 seconds
4. Auto-scrolls to newest alerts

4. Each alert shows:
   - Agent name (Schema Guardian / Anomaly Detective / Orchestrator)
   - Severity badge with color: CRITICAL (red), HIGH (orange), MEDIUM (yellow), LOW (blue)
   - Timestamp (relative: "2 minutes ago")
   - Alert message (max 100 chars, with ellipsis)
   - Expandable details with evidence list

5. Severity colors as borders/accents
6. Smooth fade-in animations for new alerts
7. Show "No alerts in last 24 hours" message when empty

File: dashboard/src/components/AlertFeed.tsx
Export: AlertFeed component

Use Tailwind for styling, Lucide for icons (AlertCircle, CheckCircle, etc).
```

### Copilot Task 3: Decision Log Visualization

**Prompt to give Copilot:**

```
Create a React component showing decision history with reasoning.

Requirements:
1. Component: DecisionLog
2. Fetch from http://localhost:8000/api/orchestrator/decisions endpoint

3. Display timeline of orchestrator decisions:
   - Most recent at top

4. Each decision shows:
   - Timestamp
   - Decision action: QUARANTINE_AND_PAUSE / PAUSE_AND_ALERT / CONTINUE
   - Action icon (different for each type)
   - Reasoning (list of bullet points)
   - "Actions taken" collapsible section
   - Confidence score

5. Color code by decision severity:
   - Red for critical actions
   - Yellow for review
   - Green for safe continuation

6. Make it look like a vertical timeline

File: dashboard/src/components/DecisionLog.tsx
Export: DecisionLog component

Use Tailwind CSS for timeline. Lucide for icons.
```

### Copilot Task 4: Main Dashboard Layout

**Prompt to give Copilot:**

```
Create the main React dashboard layout that combines all components.

Requirements:
1. File: dashboard/src/App.tsx
2. Layout structure:
   - Header: "Osprey 🦅 - Multi-Agent Data Quality Guardian"
   - Grid layout:
     * Top row: 3 agent status cards (full width)
     * Middle row: Alert feed (left 2/3) + Metrics (right 1/3)
     * Bottom row: Decision log

3. Features:
   - Real-time data from API
   - Auto-refresh every 5 seconds
   - Error handling with fallback UI
   - Loading skeletons while fetching
   - Dark theme (gray-900 background, blue accents)
   - Responsive design
   - Footer with: uptime, avg detection time, alerts today

4. Styling:
   - Use Tailwind CSS utilities
   - Smooth animations on updates
   - Professional spacing and typography

Export default App component. Make it production-ready.
```

---

## Day 14: Demo Prep & Final Polish

### Part A: Create Demo Data (30 minutes)

Let me create the demo data generator:

File: scripts/prepare_demo_data.py

This will include:
- insert_clean_data(): Normal financial news
- insert_test_data(): Obvious test patterns
- insert_subtle_anomalies(): Statistical anomalies
- clear_demo_data(): Clean up

### Part B: Demo Script

**Create file**: `DEMO_SCRIPT.md`

Complete 3-minute demo script with timestamps and exact dialogue.

### Part C: Record Demo Video (1.5-2 hours)

**Recording checklist**:
- [ ] 1080p resolution minimum
- [ ] Clear audio (use external microphone)
- [ ] Include facecam for 30 seconds at start/end
- [ ] No system notifications visible
- [ ] Phone on silent

**Recording flow**:
```bash
# Terminal 1: Start backend
uv run python agents/run_orchestrator.py

# Terminal 2: Start dashboard
cd dashboard && npm start

# Terminal 3: Insert test data at right moment
uv run python scripts/prepare_demo_data.py --mode test --count 50
```

### Part D: README Polish

Update main README with:
- Hero section with badges
- Problem statement
- Architecture diagram
- Quick start guide
- Performance metrics
- Technologies used
- Demo video link

### Part E: Final Checklist

**Code Quality**
- [ ] All Python files properly formatted
- [ ] No hardcoded API keys
- [ ] Requirements.txt complete
- [ ] All error handling in place

**Functionality**
- [ ] All 3 agents run without errors
- [ ] Orchestrator makes autonomous decisions
- [ ] Dashboard displays live data
- [ ] BigQuery ML model works
- [ ] Demo video plays smoothly

**Documentation**
- [ ] README clear and complete
- [ ] Setup instructions work
- [ ] Architecture diagram accurate

**Deployment**
- [ ] Cloud Run deployment working
- [ ] API endpoints accessible
- [ ] Dashboard loads in browser

---

## Copilot Usage Tips

**When prompting Copilot:**

1. **Be specific about file paths**
   - ✓ "File: ml/training/train.py"
   - ✗ "Create a training module"

2. **Include context**
   - Show existing code patterns
   - Reference current architecture

3. **Request error handling**
   - "with proper error handling and logging"
   - Ask for try/except blocks explicitly

4. **Ask for types**
   - "Use TypeScript with proper types"
   - "Include type hints in Python"

**When Copilot generates code:**

1. **Review carefully** - Copilot sometimes hallucinates APIs
2. **Test incrementally** - Don't accept everything at once
3. **Ask for improvements** - Add missing error handling
4. **Reference your style** - Match existing patterns

---

## Day 12-14 Deliverables Checklist

**Day 12 Complete When:**
- [ ] BigQuery ML model created and evaluated
- [ ] Training data pipeline working
- [ ] Predictions integrated into Anomaly Detective
- [ ] Model metrics showing 85%+ accuracy
- [ ] API endpoint `/api/ml/predictions` working

**Day 13 Complete When:**
- [ ] Dashboard loads at http://localhost:3000
- [ ] Agent status cards updating every 5 seconds
- [ ] Alert feed showing real-time alerts
- [ ] Decision log showing orchestrator actions
- [ ] Agent flow diagram displaying

**Day 14 Complete When:**
- [ ] Demo data generator working
- [ ] Demo video recorded (under 3 minutes)
- [ ] README polished and comprehensive
- [ ] All code reviewed and cleaned
- [ ] Ready for Devpost submission

---

## Time Estimation

**If using Copilot efficiently:**
- Day 12 BigQuery ML: 3-4 actual hours (Copilot: 60%)
- Day 13 React Dashboard: 2-3 actual hours (Copilot: 70%)
- Day 14 Polish & Demo: 2-3 actual hours (Copilot: 50%)

**Total: 7-10 hours of your time** (vs 40+ hours without Copilot)

---

## You're Almost There!

**Current status**: 🟢 80% complete (Agents 1, 2, 3 working)
**After Day 14**: 🟢 100% complete (submission-ready)
**Expected placement**: Top 5 (likely 1st place)

The work ahead is execution, not innovation. Copilot does 60-70% of it. You provide the vision and review.
