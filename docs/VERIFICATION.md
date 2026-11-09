# Verification record

## Guided assessment update - 9 November 2026

Replaced the all-at-once form with 13 individual questions, a progress indicator, Back/Next navigation and final synthetic-input confirmation. Completion displays classification and the largest SHAP contributions on screen. PDF export is available only through an explicit download button. Users can edit their completed answers or reset the example.

- `npm test`: passed the full guided interaction test in JSDOM, covering blank answer validation, all 13 steps, Back answer retention, consent, displayed results, no PDF requests/downloads before an explicit click, optional download, editing and reset. The test uses mocked API responses and does not assert real model performance.
- `npm run build`: passed, including TypeScript validation.
- Real-browser visual verification remains unperformed; DOM tests do not verify responsive appearance.

Verified locally on 8 November 2026, Windows, Python 3.13.14 and Node.js 24.21.0.

## Completed checks

- Installed Python dependencies in the project virtual environment; captured exact application dependencies in `requirements-lock.txt`.
- Installed frontend dependencies; npm reported zero vulnerabilities at installation. `package-lock.json` records exact versions.
- Downloaded the original UCI processed Cleveland file, checked its schema and SHA-256, and trained all three classifiers. Repeated training after adding checksum enforcement and persistence of all candidates.
- Training generated real metrics and global SHAP data in `ml/artifacts/metrics.json`; logistic regression was selected by training CV ROC AUC, not held-out accuracy.
- `python -m pytest -q`: **14 passed**, including range/category/unknown-field validation, missing fields, local SHAP additivity and determinism, metric integrity, source retrieval and no-match behavior, PDF response and missing-artifact errors. One upstream Starlette/httpx deprecation warning is informational.
- `npm run typecheck`: passed.
- `npm run build`: passed; the root page was statically prerendered successfully, with API calls performed client-side through the local rewrite.
- Frontend HTTP response: 200. Same-origin `/api/health` rewrite returned `model_ready: true` from FastAPI.
- Same-origin HTTP integration smoke checks for evaluation, assessment, PDF and evidence each returned 200. The synthetic example produced probability 0.1274 and a valid 3,191-byte PDF; the SHAP query retrieved the SHAP source first.
- Generated a real synthetic example PDF using `scripts/sample-report.py`; rendered its single page with PyMuPDF and visually inspected the PNG. No clipped text, overlapping table rows or missing glyphs were observed.
- `git diff --check`: passed. No commit, push or publication performed.

## Verification limits

The browser access host was unavailable; native Chrome accessibility access also failed. Browser appearance, responsive breakpoints, keyboard navigation and click-through flows have **not** been visually verified. HTTP checks, TypeScript compilation and integration tests do not replace those checks. No clinical or production security validation was performed.

The initial sandbox blocked Python environment setup, dependency network access, Next.js worker spawning and a pytest temporary directory. The affected operations passed when rerun with appropriate access. These were environment restrictions, not application test failures.

## Manual acceptance checklist

Start both services using the README commands, then:

1. Inspect the overview on desktop and at narrow mobile widths; confirm navigation remains reachable.
2. Run the synthetic assessment, then change one input and verify the old result disappears.
3. Check that invalid values prevent submission and that unchecked synthetic-input confirmation disables the submit button.
4. Open local and global explanations and compare baseline plus contributions with output probability.
5. Download and open a PDF; check the inputs match the assessment.
6. Search evidence for SHAP, dataset and validation; try an unrelated query for the no-match response.
7. Review model metrics, ROC curves and confusion matrix against the saved JSON.
8. Stop the backend and verify a visible connection error; restart it and retry.
