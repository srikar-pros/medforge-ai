import io
import json
from functools import lru_cache
from typing import Literal

import joblib
import numpy as np
import pandas as pd
import shap
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel, ConfigDict, Field
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from ml.train import ARTIFACTS, FEATURES

DISCLAIMER = 'Research and educational demonstration only. Not medical diagnosis or real patient care. Use synthetic inputs only.'
app = FastAPI(title='MedForge AI Research API',version='1.0.0',description=DISCLAIMER)
app.add_middleware(CORSMiddleware,allow_origins=['http://localhost:3000','http://127.0.0.1:3000'],allow_methods=['GET','POST'],allow_headers=['Content-Type'])

@app.middleware('http')
async def private_responses(request, call_next):
    response = await call_next(request)
    response.headers['Cache-Control'] = 'no-store'
    response.headers['X-Content-Type-Options'] = 'nosniff'
    return response

class Assessment(BaseModel):
    model_config = ConfigDict(extra='forbid',allow_inf_nan=False)
    age: float = Field(ge=18,le=100)
    sex: Literal[0,1]
    cp: Literal[1,2,3,4]
    trestbps: float = Field(ge=70,le=250)
    chol: float = Field(ge=80,le=650)
    fbs: Literal[0,1]
    restecg: Literal[0,1,2]
    thalach: float = Field(ge=50,le=230)
    exang: Literal[0,1]
    oldpeak: float = Field(ge=0,le=7)
    slope: Literal[1,2,3]
    ca: Literal[0,1,2,3]
    thal: Literal[3,6,7]

@lru_cache
def bundle():
    if not (ARTIFACTS/'model.joblib').exists():
        raise HTTPException(503,'Model unavailable. Run python -m ml.train from the repository root.')
    return joblib.load(ARTIFACTS/'model.joblib')

def metadata():
    path = ARTIFACTS/'metrics.json'
    if not path.exists():
        raise HTTPException(503,'Evaluation unavailable. Run python -m ml.train.')
    return json.loads(path.read_text())

@app.get('/api/health')
def health():
    return {'status':'ok','model_ready':(ARTIFACTS/'model.joblib').exists(),'disclaimer':DISCLAIMER}

@app.get('/api/evaluation')
def evaluation():
    return metadata()

def assess(data: Assessment):
    saved = bundle()
    model = saved['model']
    row = pd.DataFrame([data.model_dump()],columns=FEATURES)
    probability = float(model.predict_proba(row)[0,1])
    def predict(a):
        return model.predict_proba(pd.DataFrame(a,columns=FEATURES))[:,1]
    explainer = shap.Explainer(predict,saved['background'],algorithm='permutation',feature_names=FEATURES,seed=42)
    values = explainer(row.to_numpy(),max_evals=10*(2*len(FEATURES)+1))
    return {'probability':probability,'classification':int(probability>=.5),'threshold':.5,'model':metadata()['selected_model'],'baseline':float(values.base_values[0]),'contributions':[{'feature':name,'value':float(value),'input':float(row.iloc[0][name])} for name,value in sorted(zip(FEATURES,values.values[0]),key=lambda p:-abs(p[1]))],'disclaimer':DISCLAIMER}

@app.post('/api/assess')
def assessment(data: Assessment):
    return assess(data)

EVIDENCE = [
    {'id':'uci','title':'UCI Heart Disease dataset','url':'https://archive.ics.uci.edu/dataset/45/heart+disease','kind':'Dataset documentation','text':'The Cleveland subset has 303 observations and 13 predictor attributes. The original target has values 0 to 4. This project converts values above zero into a positive class. Historical referral data do not establish population screening performance.'},
    {'id':'shap','title':'SHAP: a unified approach to interpreting model predictions','url':'https://proceedings.neurips.cc/paper/2017/hash/8a20a8621978632d76c43dfd28b67767-Abstract.html','kind':'Methods paper · 2017','text':'SHAP assigns feature contributions relative to a background distribution. Contributions explain model output, not causality. Correlated predictors and the choice of background affect interpretation.'},
    {'id':'validation','title':'TRIPOD+AI reporting guidance','url':'https://www.bmj.com/content/385/bmj-2023-078378','kind':'Reporting guidance · 2024','text':'Prediction model reporting should describe data sources, participants, outcome definition, missing data, validation and performance. A single internal test set cannot establish transportability or clinical utility.'},
]

class EvidenceQuery(BaseModel):
    model_config = ConfigDict(extra='forbid')
    question: str = Field(min_length=3,max_length=500)

@app.get('/api/evidence')
def evidence():
    return {'sources':EVIDENCE,'mode':'Local curated research library; no live search or generative model'}

@app.post('/api/evidence')
def evidence_answer(query: EvidenceQuery):
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    corpus = [s['title']+' '+s['text'] for s in EVIDENCE]
    matrix = TfidfVectorizer(stop_words='english').fit_transform(corpus+[query.question])
    scores = cosine_similarity(matrix[-1],matrix[:-1])[0]
    ranked = [dict(EVIDENCE[i],relevance=float(scores[i])) for i in np.argsort(-scores) if scores[i]>.03][:3]
    return {'answer':'Relevant excerpts from the curated library are shown below.' if ranked else 'No matching evidence in the curated library. Try dataset, SHAP, missing data, or validation.','sources':ranked,'mode':'Extractive retrieval; not a clinical recommendation','disclaimer':DISCLAIMER}

@app.post('/api/report')
def report(data: Assessment):
    result = assess(data)
    meta = metadata()
    stream = io.BytesIO()
    styles = getSampleStyleSheet()
    story = [Paragraph('MedForge AI | Research report',styles['Title']),Paragraph(DISCLAIMER,styles['BodyText']),Spacer(1,16),Paragraph(f"Model: {result['model']} | Positive-class probability: {result['probability']:.3f}",styles['Heading2']),Paragraph('A model score on a synthetic record; not an individual disease risk estimate.',styles['BodyText'])]
    rows = [['Feature','Synthetic value','SHAP contribution']]+[[c['feature'],str(c['input']),f"{c['value']:+.4f}"] for c in result['contributions']]
    table = Table(rows,colWidths=[160,130,150]); table.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#d6f2ef')),('GRID',(0,0),(-1,-1),.3,colors.lightgrey),('BOTTOMPADDING',(0,0),(-1,-1),7)]))
    story += [Spacer(1,12),table,Spacer(1,12),Paragraph(f"SHAP baseline {result['baseline']:.4f}; baseline + contributions = probability. Units: probability points.",styles['BodyText']),Paragraph('Held-out model evaluation',styles['Heading2'])]
    for r in meta['models']:
        story.append(Paragraph(f"{r['name']}: ROC AUC {r['roc_auc']:.3f}, accuracy {r['accuracy']:.3f}, recall {r['recall']:.3f}; training CV AUC {r['cv_auc']:.3f}.",styles['BodyText']))
    story += [Paragraph(f"Dataset: {meta['rows']} records; train {meta['train_rows']}, test {meta['test_rows']}; random seed 42. Target: num > 0. Source: {meta['source']}",styles['BodyText']),Paragraph('Limitations',styles['Heading2'])]
    story += [Paragraph(x,styles['BodyText']) for x in meta['limitations']]
    SimpleDocTemplate(stream,title='MedForge AI Research Report').build(story)
    return Response(stream.getvalue(),media_type='application/pdf',headers={'Content-Disposition':'attachment; filename="medforge-research-report.pdf"','Cache-Control':'no-store'})
