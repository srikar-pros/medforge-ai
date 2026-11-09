# MedForge AI

**Explainable Machine Learning for Heart Disease Classification and Clinical Evidence Review**

A personal machine learning research demo built with Next.js, TypeScript, Tailwind CSS, FastAPI, Scikit-learn and SHAP. Includes a responsive dashboard, synthetic-record assessment, local/global contribution charts, actual model comparison and ROC curves, a cited evidence assistant, and downloadable PDF research reports.

**Research and educational demonstration only. Not for medical diagnosis or real patient care. Use synthetic inputs only.**

## Run locally (Windows PowerShell)

Requirements: Python 3.13 and Node.js 22 or newer (tested with Node 24). Run from the repository root. No API keys are needed.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-lock.txt
npm --prefix frontend ci
.\.venv\Scripts\python.exe -m ml.train
```

The first training run downloads the original UCI Cleveland data. Internet access is needed for dependencies and this download. Later training uses the cache. The pipeline verifies a fixed dataset checksum and creates the model artifact and actual evaluation JSON. Training normally takes under a few minutes. Never load model files from untrusted sources.

Start the backend in one terminal:

```powershell
.\.venv\Scripts\python.exe -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

Start the frontend in a second terminal:

```powershell
cd frontend
npm run dev
```

Open **http://127.0.0.1:3000**. API documentation: **http://127.0.0.1:8000/docs**. Stop each service with Ctrl+C. Equivalent launch scripts are `scripts/start-backend.ps1` and `scripts/start-frontend.ps1`. On Linux/macOS use `.venv/bin/python` instead of the Windows path.

## Demonstration workflow

1. Check the overview for dataset provenance and real experiment statistics.
2. Open **Research assessment** and answer one question at a time. Use **Back** to revisit answers; the progress bar tracks the 13 questions.
3. On the final question, confirm the inputs are synthetic and choose **Show results**. The classification and key SHAP contributions appear on screen. The output is a model probability, not a clinical risk estimate.
4. Open **Explainability** for signed local contributions and global SHAP importance. Changing inputs clears the old result.
5. If you want a copy, select **Download PDF report** on the results screen. No PDF downloads automatically. The optional report contains the synthetic record, explanation, actual evaluation and limitations. Choose **Edit answers** to revisit the questions.
6. Explore **Evidence assistant** for cited excerpts from three curated sources. It uses local TF-IDF retrieval, without live literature search or generated medical advice.
7. Open **Model evaluation** for all three classifiers, training CV scores, test metrics, ROC curves and the selected confusion matrix.

## Actual baseline results

303 Cleveland records; stratified training/test split 242/61; seed 42. Positive label: original `num > 0`. Model selection uses only mean five-fold training ROC AUC.

| Model | Training CV ROC AUC | Test ROC AUC | Test accuracy | Test recall |
| --- | ---: | ---: | ---: | ---: |
| Logistic regression (selected) | 0.9025 | 0.9665 | 88.52% | 92.86% |
| Random forest | 0.8957 | 0.9524 | 86.89% | 89.29% |
| Gradient boosting | 0.8630 | 0.9621 | 90.16% | 92.86% |

These computed results are recorded in `ml/artifacts/metrics.json`. Selection uses training CV, even when another model has higher test accuracy. The held-out set is small and cannot establish clinical utility or external validity. No confidence interval or fairness claim is implied.

## Verify and build

```powershell
.\.venv\Scripts\python.exe -m pytest -q
npm --prefix frontend test
npm --prefix frontend run typecheck
npm --prefix frontend run build
```

Production frontend after building: `npm --prefix frontend start`. The backend must also be running. API tests require the trained artifact and cover validation, SHAP additivity/determinism, metric consistency, evidence retrieval/no-match behavior, PDF generation and a missing-model error. The frontend interaction test uses an isolated DOM with mocked API responses to check the 13-question flow, validation, Back navigation, result display, editing, reset, and explicit-only PDF downloads. Production predictions and metrics always come from the trained backend.

## Repository structure

```text
frontend/   Next.js application, responsive dashboard and charts
backend/    FastAPI routes, schemas, retrieval and PDF export
ml/         Deterministic training, data cache and model artifacts
tests/      API and ML integration tests
docs/       Architecture, methodology and verification record
scripts/    Local launch scripts and sample report generator
```

See [methodology and model card](docs/METHODOLOGY.md), [architecture and API](docs/ARCHITECTURE.md), and [verification record](docs/VERIFICATION.md). Python packages are frozen in `requirements-lock.txt`; npm dependencies are locked in `frontend/package-lock.json`. `requirements.txt` declares direct dependency ranges. Restart the API after retraining. Data and binary models are ignored by Git; reproduce them with the training command.

## Data and safety

Source: [UCI Heart Disease](https://archive.ics.uci.edu/dataset/45/heart+disease), Janosi, Steinbrunn, Pfister and Detrano (1988), DOI 10.24432/C52P4X. The original Cleveland subset is used. Consult UCI for CC BY 4.0 licensing and attribution.

No external AI service, secrets, database, patient upload or patient storage is needed. Only structured synthetic values are accepted; unknown fields such as names are rejected. Requests are processed locally and responses use `Cache-Control: no-store`. Keep future secrets server-side and out of Git; `.env*` is ignored. This local demonstration has no authentication or rate limiting and must not be exposed as a clinical or public multi-user service.

## Troubleshooting

- **503 model unavailable:** run training from the root and restart the API.
- **API connection failure:** verify port 8000 and `/api/health`; Next forwards `/api/*` to it.
- **Port already in use:** stop the previous service. If changing ports, update `frontend/next.config.ts` and CORS.
- **Dataset download blocked:** download the exact original file from the URL in `ml/train.py` into `ml/data/processed.cleveland.data`; training checks its SHA-256.
- **Windows `spawn EPERM` or pytest temp permissions:** run checks in a normal local terminal with access to process/temp directories.
- **Slow SHAP:** explanations run on the CPU and may take seconds; the interface shows progress.

No GitHub push or deployment is performed by setup.
