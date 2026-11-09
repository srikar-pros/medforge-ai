'use client';

import { useEffect, useRef, useState, type FormEvent } from 'react';
import { ArrowLeft, ArrowRight, RotateCcw, ShieldCheck } from 'lucide-react';

type Field = {
  key: string;
  label: string;
  unit?: string;
  min?: number;
  max?: number;
  options?: (string | number)[][];
};

const questions: Record<string, string> = {
  age: 'What is the age?',
  sex: 'What is the recorded sex?',
  cp: 'Which chest pain category is recorded?',
  trestbps: 'What is the resting blood pressure?',
  chol: 'What is the serum cholesterol level?',
  fbs: 'Is fasting glucose above 120 mg/dL?',
  restecg: 'What is the resting ECG result?',
  thalach: 'What is the maximum heart rate?',
  exang: 'Is exercise-induced angina recorded?',
  oldpeak: 'What is the exercise ST depression?',
  slope: 'What is the peak exercise ST slope?',
  ca: 'How many major vessels are recorded?',
  thal: 'What is the thallium test category?',
};

export default function AssessmentWizard({ fields, initialValues, example, busy, onComplete }: {
  fields: Field[];
  initialValues: Record<string, number>;
  example: Record<string, number>;
  busy: boolean;
  onComplete: (values: Record<string, number>) => Promise<void>;
}) {
  const [step, setStep] = useState(0);
  const [answers, setAnswers] = useState<Record<string, string>>(
    () => Object.fromEntries(Object.entries(initialValues).map(([key, value]) => [key, String(value)])),
  );
  const [consent, setConsent] = useState(false);
  const heading = useRef<HTMLHeadingElement>(null);
  const field = fields[step];
  const isLast = step === fields.length - 1;

  useEffect(() => { heading.current?.focus(); }, [step]);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (busy) return;
    if (!isLast) { setStep(step + 1); return; }
    if (!consent) return;
    await onComplete(Object.fromEntries(fields.map(({ key }) => [key, Number(answers[key])])));
  }

  function reset() {
    setAnswers(Object.fromEntries(Object.entries(example).map(([key, value]) => [key, String(value)])));
    setConsent(false);
    setStep(0);
  }

  return <section className="panel question-panel" aria-label="Synthetic research assessment">
    <div className="wizard-meta"><span>SYNTHETIC RESEARCH RECORD</span><span aria-live="polite">Question {step + 1} of {fields.length}</span></div>
    <div className="wizard-progress" role="progressbar" aria-label="Assessment progress" aria-valuemin={0} aria-valuemax={fields.length} aria-valuenow={step + 1}>
      <span style={{ width: `${(step + 1) / fields.length * 100}%` }} />
    </div>
    <form onSubmit={submit}>
      <fieldset disabled={busy} className="wizard-fieldset">
        <div className="question-body" key={field.key}>
          <span className="question-number">{String(step + 1).padStart(2, '0')}</span>
          <h2 ref={heading} tabIndex={-1}>{questions[field.key]}</h2>
          <p id="question-help">{field.options ? 'Choose the value for your fictional research record.' : `Enter a value between ${field.min} and ${field.max}${field.unit ? ` (${field.unit})` : ''}.`}</p>
          <label className="field wizard-input" htmlFor={`assessment-${field.key}`}>
            <span>{field.label}</span>
            {field.options ? <select id={`assessment-${field.key}`} required aria-describedby="question-help" value={answers[field.key]} onChange={event => setAnswers({ ...answers, [field.key]: event.target.value })}>
              {field.options.map(option => <option key={option[0]} value={option[0]}>{option[1]}</option>)}
            </select> : <div className="number-field">
              <input id={`assessment-${field.key}`} required type="number" min={field.min} max={field.max} step={field.key === 'oldpeak' ? 0.1 : 1} aria-describedby="question-help" value={answers[field.key]} onChange={event => setAnswers({ ...answers, [field.key]: event.target.value })} />
              <span>{field.unit}</span>
            </div>}
          </label>
        </div>
        {isLast && <label className="consent wizard-consent"><input required type="checkbox" checked={consent} onChange={event => setConsent(event.target.checked)} /> I confirm these are synthetic demonstration inputs.</label>}
        <div className="wizard-actions">
          <button type="button" className="secondary" disabled={step === 0} onClick={() => setStep(step - 1)}><ArrowLeft size={16} /> Back</button>
          <button type="submit" className="primary" disabled={isLast && !consent}>{busy ? 'Preparing your results…' : isLast ? 'Show results' : 'Next question'}<ArrowRight size={16} /></button>
        </div>
        <div className="wizard-foot"><span><ShieldCheck size={14} /> Your answers stay in this session.</span><button type="button" onClick={reset}><RotateCcw size={13} /> Reset example</button></div>
      </fieldset>
    </form>
    <p className="wizard-download-note">Results appear on screen after the final question. You can choose to download a PDF afterwards.</p>
    {busy && <p className="wizard-status" role="status">Computing the classification and SHAP explanation. This may take a few seconds.</p>}
  </section>;
}
