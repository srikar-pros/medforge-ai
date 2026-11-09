"""Reproducible Cleveland experiment. Run from repository root: python -m ml.train."""
import hashlib
import io
import json
import platform
from pathlib import Path
from urllib.request import urlopen

import joblib
import numpy as np
import pandas as pd
import shap
import sklearn
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score, confusion_matrix, roc_curve, brier_score_loss
from sklearn.model_selection import StratifiedKFold, cross_val_score, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

ROOT = Path(__file__).resolve().parent
ARTIFACTS = ROOT / 'artifacts'
FEATURES = ['age','sex','cp','trestbps','chol','fbs','restecg','thalach','exang','oldpeak','slope','ca','thal']
NUMERIC = ['age','trestbps','chol','thalach','oldpeak']
URL = 'https://archive.ics.uci.edu/static/public/45/heart+disease.zip'
DATA_URL = 'https://archive.ics.uci.edu/ml/machine-learning-databases/heart-disease/processed.cleveland.data'

def train():
    data_path = ROOT / 'data' / 'processed.cleveland.data'
    data_path.parent.mkdir(exist_ok=True)
    if not data_path.exists():
        with urlopen(DATA_URL, timeout=60) as response:
            data_path.write_bytes(response.read())
    raw = data_path.read_bytes()
    df = pd.read_csv(io.BytesIO(raw), names=FEATURES + ['target'], na_values='?')
    if hashlib.sha256(raw).hexdigest() != 'a74b7efa387bc9d108d7d0115d831fe9b414b29ae7124f331b622b4efa0427c8':
        raise ValueError('Cleveland dataset checksum mismatch; inspect the source before training')
    if df.shape != (303,14) or not df.target.isin(range(5)).all():
        raise ValueError('Unexpected Cleveland data schema')
    X, y = df[FEATURES], (df.target > 0).astype(int)
    train_x, test_x, train_y, test_y = train_test_split(X,y,test_size=.2,stratify=y,random_state=42)
    categorical = [c for c in FEATURES if c not in NUMERIC]
    preprocess = ColumnTransformer([
        ('numeric', Pipeline([('impute',SimpleImputer(strategy='median')),('scale',StandardScaler())]), NUMERIC),
        ('category', Pipeline([('impute',SimpleImputer(strategy='most_frequent')),('encode',OneHotEncoder(handle_unknown='ignore',sparse_output=False))]), categorical),
    ])
    candidates = {'Logistic regression':LogisticRegression(max_iter=2000,random_state=42), 'Random forest':RandomForestClassifier(n_estimators=200,max_depth=5,min_samples_leaf=3,random_state=42,n_jobs=1), 'Gradient boosting':GradientBoostingClassifier(n_estimators=80,max_depth=2,random_state=42)}
    models, results = {}, []
    cv = StratifiedKFold(n_splits=5,shuffle=True,random_state=42)
    for name, estimator in candidates.items():
        pipe = Pipeline([('preprocess',preprocess),('model',estimator)])
        scores = cross_val_score(pipe,train_x,train_y,cv=cv,scoring='roc_auc')
        pipe.fit(train_x,train_y)
        p = pipe.predict_proba(test_x)[:,1]
        pred = (p >= .5).astype(int)
        fpr,tpr,_ = roc_curve(test_y,p)
        results.append(dict(name=name,cv_auc=float(scores.mean()),cv_std=float(scores.std()),accuracy=accuracy_score(test_y,pred),precision=precision_score(test_y,pred,zero_division=0),recall=recall_score(test_y,pred),f1=f1_score(test_y,pred),roc_auc=roc_auc_score(test_y,p),brier=brier_score_loss(test_y,p),confusion_matrix=confusion_matrix(test_y,pred).tolist(),roc={'fpr':fpr.tolist(),'tpr':tpr.tolist()}))
        models[name] = pipe
    winner = max(results,key=lambda r:r['cv_auc'])['name']
    model = models[winner]
    # Model agnostic permutation SHAP explains positive-class probability directly.
    background = train_x.sample(30,random_state=42).to_numpy()
    def predict(a):
        return model.predict_proba(pd.DataFrame(a,columns=FEATURES))[:,1]
    explainer = shap.Explainer(predict,background,algorithm='permutation',feature_names=FEATURES,seed=42)
    explanation = explainer(test_x.to_numpy(),max_evals=2*len(FEATURES)+1)
    importance = np.abs(explanation.values).mean(axis=0)
    metadata = dict(dataset='UCI Cleveland Heart Disease',source=DATA_URL,sha256=hashlib.sha256(raw).hexdigest(),seed=42,rows=len(df),train_rows=len(train_x),test_rows=len(test_x),positive_rows=int(y.sum()),missing_values=int(X.isna().sum().sum()),target='Original num > 0 = positive; num = 0 = negative',selected_model=winner,selection='Highest mean 5-fold training ROC AUC; test set unused for selection',threshold=.5,models=results,global_importance=[{'feature':f,'value':float(v)} for f,v in sorted(zip(FEATURES,importance),key=lambda z:-z[1])],versions={'python':platform.python_version(),'sklearn':sklearn.__version__,'shap':shap.__version__},limitations=['Small historical referral cohort; not representative of contemporary populations.','Single held-out split; uncertainty is substantial with 61 test records.','No external validation, prospective study, clinical calibration or fairness certification.','SHAP describes model associations, not causes or treatment effects.'])
    ARTIFACTS.mkdir(exist_ok=True)
    joblib.dump({'model':model,'models':models,'background':background},ARTIFACTS/'model.joblib')
    (ARTIFACTS/'metrics.json').write_text(json.dumps(metadata,indent=2))
    print(json.dumps(metadata,indent=2))

if __name__ == '__main__':
    train()
