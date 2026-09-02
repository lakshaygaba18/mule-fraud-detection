# 🛡️ MuleShield
### AI-Powered Mule Fraud Detection & Transaction Network Intelligence

*Detect suspicious accounts. Trace the network. Explain the risk. Monitor when fraud behavior changes — and prove that fixing it actually works.*

MuleShield is an end-to-end fraud intelligence platform that identifies suspicious mule accounts by combining **GraphSAGE-based graph learning**, **transaction-network analysis**, **behavioral explainability**, **model-drift monitoring**, and **adversarial robustness testing** into an investigator-oriented dashboard.

The goal isn't just to predict whether an account is fraudulent — it's to show investigators *why*, show them the surrounding network, and prove the system knows when its own judgment is starting to go stale.

---

## 🚀 Quick Links

| Component | Link |
|---|---|
| 🌐 Frontend (Flutter Web dashboard) | https://mule-fraud-frontend.onrender.com |
| 🤖 ML Service (FastAPI) | https://mule-fraud-ml.onrender.com |
| ☕ Backend (Spring Boot API) | https://mule-fraud-backend.onrender.com |
| 💻 Source Code | https://github.com/lakshaygaba18/mule-fraud-detection |

ML service health check:
```json
GET https://mule-fraud-ml.onrender.com
{
  "service": "Fraud Detection ML Service",
  "status": "running",
  "mode": "production"
}
```

---

## 📊 Results & Key Findings

This is the core evidence for why this system is more than a classifier — it's a system that catches its own blind spots and recovers from them.

| Scenario | What happened | Result |
|---|---|---|
| **New fraud pattern appears** ("structuring" — money spread across many small, slow transfers instead of a fast mule-ring pile-up) | Model recall dropped silently, but the **aggregate risk-score distribution stayed "stable"** (PSI = 0.045) | Score-based drift monitoring alone **missed** the problem |
| **Topology-level monitoring added** (`is_passthrough` — flags pass-through chain accounts) | Same structuring batch re-checked at the feature level | **Caught immediately** (PSI = 0.583, `MAJOR_SHIFT`) — before any labeled data confirmed the recall drop |
| **Adversarial red-team test** — a fraud pattern deliberately engineered to evade the `is_passthrough` check (each account splits its outbound transfer in two) | Original model (v1) recall on this **genuinely unseen** pattern | **67.1%** |
| **Retrain loop closes** — model retrained on baseline + structuring data (never shown the adversarial pattern) | v2 model tested on the same unseen adversarial batch | **100% recall** — up from 67.1%, with zero exposure to that exact pattern during training |

**Why this matters:** most student/portfolio fraud projects stop at "here's my model's accuracy." MuleShield instead demonstrates the full lifecycle a real fraud team cares about — *detect → notice you're wrong → fix it → prove the fix generalizes* — with real numbers at every step, including an honest account of where the first-line defense (score drift) failed and a second layer (topology drift) had to catch it.

*(v2 was deliberately **not** hot-swapped into production without a full validation/rollout process — a real MLOps discipline point, not an oversight.)*

---

## 🎯 Problem Statement

Traditional fraud detection systems often evaluate transactions or accounts independently. Mule accounts, however, frequently operate as part of a transaction network:

```
Account A
    │
    ▼
Mule Account
    │
    ├──────────► Account C
    │
    └──────────► Account D
```

An account that receives money from many senders, quickly forwards it, has a high pass-through ratio, and acts as a bridge between other suspicious accounts is often only recognizable when viewed as part of a network — not as an isolated transaction.

MuleShield combines account-level behavioral features with graph-based learning and network intelligence to provide that broader view.

---

## 💡 Core Idea

A traditional system answers: **"Is this account suspicious?"**

MuleShield answers: **"Why is this account suspicious, who is it connected to, how is money moving through the network, and has the underlying behavior changed since the model was trained?"**

```
Fraud Detection + Network Intelligence + Explainability
     + Risk Propagation + Adversarial Testing + Drift Monitoring
```

---

## ✨ Key Features

- 🧠 Graph Neural Network fraud detection using **GraphSAGE**
- 🔗 Interactive transaction-network visualization
- 🚨 Account-level risk scoring with an explicit **uncertain / escalate-to-human-review** band (not just binary allow/block)
- 🕵️ Mule / structured / outbound account type identification
- 🔍 Explainable, plain-language behavioral risk reasons
- 📈 Feature- and model-drift monitoring using **PSI** and **Jensen-Shannon divergence**
- 🧪 Adversarial fraud simulation to red-team the system's own detectors
- 🔄 Retrain loop with **before/after validation on a genuinely unseen pattern**
- 🌐 Network-based risk propagation (explicit, auditable business rule on top of the GNN score)
- 📋 Investigator-oriented fraud dashboard
- 📝 Drift-event audit logging with retrain recommendations
- ⚙️ REST APIs for fraud scoring, network data, drift reports, and audit history
- ☁️ Independently deployable, cloud-hosted services (Render)

---

## 🏗️ System Architecture

```
                    ┌──────────────────────────┐
                    │       Flutter Web         │
                    │  Investigation Dashboard  │
                    └────────────┬──────────────┘
                                 │ REST API
                                 ▼
                    ┌──────────────────────────┐
                    │        Spring Boot        │
                    │      Application API      │
                    └────────────┬──────────────┘
                                 │ REST
                                 ▼
                    ┌──────────────────────────┐
                    │          FastAPI          │
                    │        ML Service         │
                    └────────────┬──────────────┘
                                 │
              ┌──────────────────┼──────────────────┐
              ▼                  ▼                  ▼
       ┌─────────────┐    ┌─────────────┐    ┌──────────────┐
       │  GraphSAGE  │    │    Drift    │    │Explainability│
       │     GNN     │    │  Monitoring │    │   Signals    │
       └─────────────┘    └─────────────┘    └──────────────┘
```

**Why three separate services instead of one?** This mirrors how fintechs actually structure fraud systems: Java/Spring Boot owns business logic, orchestration, and auditability; the ML layer is an independently deployable, independently scalable microservice. It's not overengineering — it's the realistic shape of the problem.

---

## 🧩 System Components

### 1. Flutter Web Frontend
Investigator-facing interface: fraud dashboard, risk-score visualization, account investigation, behavioral explanations, transaction-network graph with filters, drift-monitoring alerts, and audit-log visibility.

### 2. Spring Boot Backend
The application/API layer between frontend and ML service. Exposes REST endpoints, calls the ML service, returns fraud predictions/drift reports/network data/audit logs, and **records drift events into an audit trail** — the retrain-trigger logic lives here. Independently deployable via Docker.

### 3. FastAPI ML Service
Fraud prediction, GraphSAGE inference, feature processing, explainability, network data generation, and drift analysis. Deployed independently so the ML layer can be scaled and iterated on without touching the application layer.

---

## 🧠 Machine Learning Pipeline

Transaction-level data is transformed into account-level behavioral features:

| Feature | What it captures |
|---|---|
| `in_degree` | Number of incoming transaction relationships |
| `out_degree` | Number of outgoing transaction relationships |
| `unique_senders` | Number of distinct sending accounts |
| `unique_receivers` | Number of distinct receiving accounts |
| `pass_through_ratio` | How much received money is subsequently passed onward |
| `velocity_hours` | Timing/velocity of transaction activity |
| `in_span_hours` | Time span of incoming activity |
| `is_passthrough` | Whether an account is a pure 1-in-1-out chain link (topology signal, not fed to the model — used purely for monitoring) |

## 🔗 Graph Neural Network

```
Nodes    → Accounts
Edges    → Transactions
Features → Account behavioral statistics
```

GraphSAGE learns representations from both an account's own behavioral features **and** the structure/features of its neighbors:

```
Account Features → GraphSAGE Layer → ReLU → GraphSAGE Layer → Fraud Probability → Risk Score
```

## 🚨 Risk Classification

```
Risk Score >= 70   → HIGH
40 <= Score < 70   → UNCERTAIN — escalate to human review
Risk Score < 40    → LOW
```

The middle band is deliberate: a model that silently forces every borderline score into "allow" or "block" is quietly overconfident. Real fraud/compliance systems need an explicit "I'm not sure" path.

## 🔍 Explainability

Every flagged account comes with a plain-language reason, not just a number:

```
Risk Score: 87.4

Why flagged:
• received money from multiple senders
• forwarded funds shortly after receiving them
• passed through a high percentage of received funds
```

## 🕸️ Transaction Network Intelligence

The network view lets investigators trace an account's incoming/outgoing transactions, connected accounts, and risk relationships, filterable by **All / High Risk / Mule / Outbound**.

## 🔄 Risk Propagation

```
High-Risk Account → Connected Account → Network Context → Additional Risk Signal
```

If an account transacts directly with an already-flagged high-risk account, its own score is boosted — an explicit, auditable rule layered on top of the GNN's score, so the "risk spreads through the network" reasoning isn't buried inside model weights where a compliance officer can't inspect it.

## 📈 Model Drift Monitoring

Fraud patterns change over time. MuleShield uses **PSI** (Population Stability Index) to compare baseline vs. incoming feature/score distributions, and **Jensen-Shannon divergence** to check whether the *kind* of explanation the model gives is shifting.

```json
{
  "overall_status": "major_shift",
  "score_psi": 0.045,
  "feature_psi": {
    "is_passthrough": 0.583
  },
  "explanation_js_divergence": 0.0057
}
```

**The honest finding:** the risk-score distribution alone looked stable (PSI 0.045) even while a real fraud pattern was slipping through — because the drifted subgroup was a small fraction of total traffic, diluting the aggregate signal. Only the feature-level `is_passthrough` check caught it. This is why the system monitors multiple layers, not just the final score.

## 🧪 Adversarial Robustness Testing

To check whether the monitoring actually generalizes (rather than being overfit to one test case), MuleShield includes a red-team step: a synthetic fraud pattern was built specifically to **evade** the `is_passthrough` check by splitting each hop's outbound transfer in two.

```
Normal Data → Adversarial Simulation → Feature Generation → Model Scoring → Robustness Evaluation
```

Result: the evasion attempt still leaked signal at the final cash-out hop, so `is_passthrough` still fired (PSI = 0.975) — and after retraining, the GNN's own recall on this batch rose from 67.1% to 100% (see [Results](#-results--key-findings)).

## 📝 Audit & Retrain Trigger

When significant drift is detected, the backend logs an audit entry: timestamp, model version, drift metrics, and a plain-language recommendation (e.g. *"RETRAIN RECOMMENDED"*), with a `pending_review` status until a human acts on it. This is the compliance-facing half of the story — the kind of documented risk-management trail regulators (e.g. under the EU AI Act's high-risk-AI provisions) actually ask for.

---

## 🔄 End-to-End Investigation Flow

```
Fraud Report → Identify Risky Accounts → Review Reasons for Risk
    → Open Network View → Trace Connected Accounts
    → Review Network Risk Propagation → Check Model/Data Drift
```

---

## 🛠️ Technology Stack

| Layer | Tech |
|---|---|
| Frontend | Flutter, Dart, Material UI, GraphView |
| Backend | Java, Spring Boot, Maven, REST |
| ML | Python, FastAPI, PyTorch, PyTorch Geometric (GraphSAGE), Pandas, NumPy, Scikit-learn, SciPy |
| Deployment | GitHub, Render, Docker |

---

## 📡 API Endpoints

| Endpoint | Returns |
|---|---|
| `GET /api/fraud-report` | Account-level fraud predictions + behavioral explanations |
| `GET /api/drift-report` | Overall drift status, score PSI, feature PSI, explanation divergence, alerts |
| `GET /api/network` | Network nodes, risk scores/levels, account types, transaction edges |
| `GET /api/audit-log` | Recorded drift-related audit events and retrain recommendations |

---

## 📁 Project Structure

```
mule-fraud-detection/
├── backend/                    # Spring Boot application (Java)
├── frontend/                   # Flutter Web dashboard
│
├── fastapi_app.py              # ML service entrypoint
├── drift_monitor.py            # PSI / JS-divergence drift detection
├── risk_propagation.py         # Network-based risk boosting
├── risk_classification.py      # Allow / Uncertain / Block decision bands
├── explain.py                  # Rule-based explainability
│
├── train_baseline.py           # XGBoost baseline
├── train_gnn.py                # GraphSAGE v1
├── retrain_gnn_v2.py           # GraphSAGE v2 (retrained on combined data)
│
├── build_features.py / build_drift_features.py / build_adversarial_features.py
├── simulate_data.py / simulate_drift_batch.py / simulate_adversarial_batch.py
├── combine_training_data.py    # Merges baseline + structuring for retraining
│
├── run_drift_check.py / run_adversarial_drift_check.py
├── score_current_batch.py / score_adversarial_batch.py / score_adversarial_with_v2.py
│
├── requirements.txt
├── Procfile
└── .gitignore
```

Generated datasets and model artifacts are excluded from version control where appropriate via `.gitignore`, and are fully reproducible from the `simulate_*.py` / `build_*.py` scripts.

---

## ⚙️ Local Setup

**Prerequisites:** Python 3.x, Java 17+, Maven, Flutter SDK, Git

### ML Service
```bash
python -m venv venv
venv\Scripts\activate          # Windows
pip install -r requirements.txt
uvicorn fastapi_app:app --host 0.0.0.0 --port 8000
```
→ `http://localhost:8000`

### Spring Boot Backend
```bash
cd backend
mvnw clean package -DskipTests
java -jar target/backend-0.0.1-SNAPSHOT.jar
```
→ `http://localhost:8080`

### Flutter Frontend
```bash
cd frontend
flutter pub get
flutter run -d chrome
```

### Configurable API endpoint
```bash
flutter run -d chrome --dart-define=API_BASE_URL=http://localhost:8080
# or, pointed at a deployed backend:
flutter run -d chrome --dart-define=API_BASE_URL=https://your-backend-url
```

---

## 🐳 Docker Deployment

```dockerfile
FROM eclipse-temurin:17-jdk
WORKDIR /app
COPY . .
RUN chmod +x mvnw
RUN ./mvnw clean package -DskipTests
EXPOSE 8080
CMD ["java", "-jar", "target/backend-0.0.1-SNAPSHOT.jar"]
```

The ML service and Spring Boot backend are deployed as independent services (Render), keeping ML iteration decoupled from the application layer.

---

## 📸 Screenshots

**Fraud Intelligence Dashboard** — live drift alert banner, account list sorted by risk score, with plain-language reasons for every flag.

![Dashboard](<img width="959" height="475" alt="dashboard" src="https://github.com/user-attachments/assets/64bceaa8-be2a-43b1-9446-6f027f8ca872" />
)

**Transaction Network Graph** — interactive, filterable (All / High Risk / Mule / Outbound) live topology of the account graph.

![Network Graph](<img width="959" height="477" alt="network" src="https://github.com/user-attachments/assets/ed96f904-c8d8-4f2d-a3ef-da2b6b4f6fbc" />
)

**Account Investigation Panel** — click any node to see its risk score, account type, transaction volumes, and network connections.

![Account Investigation](<img width="959" height="477" alt="network" src="https://github.com/user-attachments/assets/640ae973-c3ec-4321-b10e-2b7fdc29139b" />
)

**Drift Monitoring Report** — per-feature PSI breakdown, showing `is_passthrough` catching a shift that the aggregate risk-score PSI missed.

![Drift Report](<img width="959" height="477" alt="network" src="https://github.com/user-attachments/assets/80356841-3f7a-43b5-b989-6165c0ac2aca" />
)

---

## 🚀 Future Improvements

- Real-time transaction-stream processing (rolling-window drift checks instead of batch)
- Automated model retraining pipeline (currently a manual, validated step by design)
- Case-management workflow for investigators
- Human-in-the-loop feedback loop back into the training data
- Production database integration

---

## 📌 Disclaimer

This project is a technical demonstration and research-oriented fraud intelligence platform. It is not intended to make autonomous real-world financial decisions without appropriate validation, governance, human review, regulatory controls, and production-grade security.

---

**MuleShield** — Built with Flutter • Java • Spring Boot • Python • FastAPI • PyTorch Geometric • GraphSAGE • Docker • Render
