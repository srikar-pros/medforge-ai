"""Run from root: .venv/Scripts/python.exe scripts/sample-report.py."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from backend.main import Assessment, report

record = Assessment(age=54,sex=1,cp=3,trestbps=128,chol=238,fbs=0,restecg=0,thalach=162,exang=0,oldpeak=1.2,slope=2,ca=0,thal=3)
target = Path('output/pdf/medforge-synthetic-example.pdf')
target.parent.mkdir(parents=True,exist_ok=True)
target.write_bytes(report(record).body)
print(target)
