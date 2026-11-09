import numpy as np
import pytest
from fastapi.testclient import TestClient
from backend.main import app, bundle
from ml.train import ARTIFACTS

client = TestClient(app)
SYNTHETIC = dict(age=54,sex=1,cp=3,trestbps=128,chol=238,fbs=0,restecg=0,thalach=162,exang=0,oldpeak=1.2,slope=2,ca=0,thal=3)

def test_health():
    response = client.get('/api/health')
    assert response.status_code == 200
    assert 'Not medical diagnosis' in response.json()['disclaimer']

@pytest.mark.parametrize('change',[{'age':-1},{'cp':0},{'thal':2},{'sex':3},{'oldpeak':8},{'name':'patient name'},{'chol':None}])
def test_invalid_record(change):
    assert client.post('/api/assess',json={**SYNTHETIC,**change}).status_code == 422

def test_missing_field():
    assert client.post('/api/assess',json={'age':54}).status_code == 422

def test_explanation_matches_prediction():
    r = client.post('/api/assess',json=SYNTHETIC)
    assert r.status_code == 200, r.text
    result = r.json()
    assert 0 <= result['probability'] <= 1
    assert len(result['contributions']) == 13
    assert abs(result['baseline']+sum(c['value'] for c in result['contributions'])-result['probability']) < 1e-6
    assert result['classification'] == int(result['probability']>=.5)
    assert client.post('/api/assess',json=SYNTHETIC).json() == result

def test_evaluation_integrity():
    r = client.get('/api/evaluation')
    assert r.status_code == 200
    d = r.json()
    assert d['rows'] == 303 and d['train_rows']+d['test_rows'] == 303
    assert len(d['sha256']) == 64
    assert d['selected_model'] == max(d['models'],key=lambda m:m['cv_auc'])['name']
    for model in d['models']:
        matrix = np.array(model['confusion_matrix'])
        assert matrix.sum() == d['test_rows']
        assert abs(matrix.trace()/matrix.sum()-model['accuracy']) < 1e-10
        assert 0 <= model['roc_auc'] <= 1

def test_evidence_retrieval_and_no_match():
    r = client.post('/api/evidence',json={'question':'SHAP feature contributions background'})
    assert r.status_code == 200
    assert r.json()['sources'][0]['id'] == 'shap'
    assert client.post('/api/evidence',json={'question':'xyzqwerty'}).json()['sources'] == []
    assert client.post('/api/evidence',json={'question':'x'}).status_code == 422

def test_pdf_report():
    r = client.post('/api/report',json=SYNTHETIC)
    assert r.status_code == 200
    assert r.headers['content-type'] == 'application/pdf'
    assert r.content.startswith(b'%PDF-') and len(r.content)>2000
    assert r.headers['cache-control'] == 'no-store'

def test_missing_model_is_actionable(monkeypatch,tmp_path):
    import backend.main as main
    bundle.cache_clear()
    monkeypatch.setattr(main,'ARTIFACTS',tmp_path)
    try:
        r = client.post('/api/assess',json=SYNTHETIC)
        assert r.status_code == 503
        assert 'ml.train' in r.json()['detail']
    finally:
        bundle.cache_clear()
