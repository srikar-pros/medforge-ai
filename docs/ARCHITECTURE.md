# Architecture and implementation notes

Next.js App Router + React + TypeScript + Tailwind CSS 4 serves an accessible responsive dashboard. A same-origin `/api/*` rewrite forwards requests to the loopback-only FastAPI service on port 8000. The browser holds the current synthetic inputs and results in memory; changing inputs invalidates the displayed result. All charts derive from API results, never hard-coded metric values.

FastAPI validates all 13 structured fields with Pydantic, rejects unknown fields, loads a locally trained trusted joblib artifact, computes positive-class scores and permutation SHAP values, and generates PDF reports in memory with ReportLab. Raw inputs are not written to disk. The UCI dataset cache is separate and ignored by Git. Do not load untrusted joblib files: pickle-based artifacts can execute code.

`ml/train.py` downloads/caches the original data and generates `ml/artifacts/model.joblib` and `metrics.json`. Restart the API after retraining, as the artifact is cached in process. `model.joblib` and downloaded data are ignored; evaluation JSON is retained for auditability. The API returns 503 with training instructions if artifacts are absent.

## Local demonstration security

No external AI API or secrets are required. No patient storage, accounts, uploads or database are implemented. Uvicorn and Next bind to loopback in documented commands. CORS allows only local frontend origins. POST prediction/report bodies should never contain names or identifiers. PDF results include the complete synthetic input record through the explanation table. Results remain in browser memory until navigation/reload; no localStorage is used.

This is not a hardened multi-user service: authentication, rate limiting, TLS, audit logging, per-user isolation and formal security review are prerequisites for any hosted deployment. SHAP is CPU-bound and requests may take seconds. The evidence corpus is intentionally small and cannot answer arbitrary clinical questions. Input ranges provide basic research schema checks, not a clinical plausibility guarantee.

## API

| Route | Behavior |
| --- | --- |
| GET `/api/health` | Service and artifact readiness |
| GET `/api/evaluation` | Actual experiment metadata and metrics |
| POST `/api/assess` | Validated synthetic inputs to score and explanation |
| GET `/api/evidence` | Local curated sources |
| POST `/api/evidence` | `{ "question": "..." }` to ranked excerpts |
| POST `/api/report` | Same assessment payload to downloadable PDF |

Interactive API documentation: http://127.0.0.1:8000/docs.
