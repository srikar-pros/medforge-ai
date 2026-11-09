# Experiment protocol and model card

MedForge AI classifies the binary label derived from the original Cleveland `num` field: 0 is negative and 1-4 are positive. This is historical disease presence, not future risk, a diagnosis, or a treatment decision.

## Data provenance

- Original processed Cleveland data: https://archive.ics.uci.edu/ml/machine-learning-databases/heart-disease/processed.cleveland.data
- Dataset documentation and attribution: https://archive.ics.uci.edu/dataset/45/heart+disease
- Creators: Andras Janosi, William Steinbrunn, Matthias Pfister, Robert Detrano. UCI Heart Disease dataset (1988), DOI 10.24432/C52P4X. Consult UCI for its CC BY 4.0 terms.
- Expected shape: 303 observations, 13 predictors and one target. `?` denotes missing values. SHA-256 is saved with every experiment.

## Leakage controls

Fixed stratified 80/20 train/test split, seed 42. Numerical median imputation and scaling, and categorical mode imputation and one-hot encoding, are inside each estimator pipeline. Five-fold stratified shuffled cross-validation uses training data only. Preprocessing is refitted independently within each fold. Models use fixed documented hyperparameters; there is no test-based tuning. The highest mean training CV ROC AUC selects the deployed model. The 61-row held-out set is used only for reporting. No retraining on the full cohort is performed.

Candidates are logistic regression, random forest and gradient boosting. See `ml/train.py` for exact settings. Accuracy, precision, recall, F1, ROC AUC, Brier score, ROC coordinates and confusion matrices are computed from real held-out predictions. CV standard deviation is variation across folds, not a confidence interval. All classifiers use threshold 0.50. The test set is small; differences between models should not be treated as conclusive. Saved package versions and the dependency lock file support reproduction.

## Explainability

SHAP permutation explanations operate on the 13 original inputs and positive-class predicted probability. The background is 30 training records sampled with seed 42. Global importance is mean absolute SHAP across held-out records, using one permutation cycle per record. Local explanations use ten cycles for greater stability. Both are approximations; background and feature dependence affect them. Baseline plus local contributions equals the predicted probability; integration tests check this. SHAP contributions are model associations, never causal effects. Reference: Lundberg and Lee (2017), https://proceedings.neurips.cc/paper/2017/hash/8a20a8621978632d76c43dfd28b67767-Abstract.html.

## Limitations and intended use

Historical referral selection, small sample size, encoded sex categories, limited demographic information and lack of external validation prevent claims of clinical utility or general population performance. There is no prospective validation, fairness certification or clinical probability calibration. Brier score is reported but is not evidence of calibration across populations. No treatment recommendations are generated. Use only fictional structured examples. Never submit identifiable patient information.

## Evidence review

The assistant uses TF-IDF cosine similarity against three curated methodological summaries and returns source links. It is deterministic extractive retrieval, with an explicit no-match response. It has no generative LLM, no live literature retrieval and no claim of systematic review coverage. TRIPOD+AI reference: https://www.bmj.com/content/385/bmj-2023-078378.
