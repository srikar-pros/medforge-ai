import { test } from 'node:test';
import assert from 'node:assert/strict';
import { JSDOM } from 'jsdom';
import React from 'react';

test('guided assessment validates each answer, preserves Back navigation, and downloads only on request', async () => {
  const dom = new JSDOM('<!doctype html><html><body></body></html>', { url: 'http://localhost:3000' });
  Object.defineProperty(globalThis, 'window', { value: dom.window, configurable: true });
  Object.defineProperty(globalThis, 'document', { value: dom.window.document, configurable: true });
  Object.defineProperty(globalThis, 'navigator', { value: dom.window.navigator, configurable: true });
  Object.assign(globalThis, { HTMLElement: dom.window.HTMLElement, HTMLInputElement: dom.window.HTMLInputElement, IS_REACT_ACT_ENVIRONMENT: true });
  const calls: { path: string; body?: Record<string, unknown> }[] = [];
  let downloads = 0;
  const originalFetch = globalThis.fetch;
  const originalCreate = URL.createObjectURL;
  const originalRevoke = URL.revokeObjectURL;
  const originalClick = dom.window.HTMLAnchorElement.prototype.click;
  URL.createObjectURL = () => 'blob:synthetic-report';
  URL.revokeObjectURL = () => {};
  dom.window.HTMLAnchorElement.prototype.click = function () { downloads++; };
  globalThis.fetch = async (input, init) => {
    const path = String(input);
    calls.push({ path, body: init?.body ? JSON.parse(String(init.body)) : undefined });
    if (path === '/api/evaluation') return Response.json({ rows: 303, models: [], global_importance: [] });
    if (path === '/api/evidence') return Response.json({ sources: [] });
    if (path === '/api/assess') return Response.json({ probability: 0.1274, classification: 0, model: 'Test classifier', baseline: 0.4, contributions: [{ feature: 'age', value: -0.2726, input: 54 }] });
    if (path === '/api/report') return new Response('%PDF-test', { headers: { 'Content-Type': 'application/pdf' } });
    throw new Error(`Unexpected request: ${path}`);
  };
  const { render, screen, cleanup, waitFor } = await import('@testing-library/react');
  const userEvent = (await import('@testing-library/user-event')).default;
  const Home = (await import('../app/page')).default;
  const user = userEvent.setup({ document: dom.window.document });
  try {
    render(<Home />);
    await user.click(screen.getByRole('button', { name: 'Research assessment' }));
    assert.ok(screen.getByRole('heading', { name: 'What is the age?' }));
    assert.equal(screen.queryAllByRole('spinbutton').length, 1);
    assert.equal(screen.queryAllByRole('combobox').length, 0);
    const age = screen.getByRole('spinbutton', { name: /^Age/  });
    await user.clear(age);
    await user.click(screen.getByRole('button', { name: 'Next question' }));
    assert.ok(screen.getByRole('heading', { name: 'What is the age?' }));
    await user.type(age, '54');
    await user.click(screen.getByRole('button', { name: 'Next question' }));
    await user.selectOptions(screen.getByRole('combobox', { name: 'Recorded sex' }), '0');
    await user.click(screen.getByRole('button', { name: 'Next question' }));
    await user.click(screen.getByRole('button', { name: 'Back' }));
    assert.equal((screen.getByRole('combobox', { name: 'Recorded sex' }) as HTMLSelectElement).value, '0');
    // Continue through every remaining question; no request is made for intermediate steps.
    for (let step = 1; step < 12; step++) {
      await user.click(screen.getByRole('button', { name: 'Next question' }));
    }
    assert.ok(screen.getByRole('heading', { name: 'What is the thallium test category?' }));
    assert.equal(calls.filter(call => call.path === '/api/assess').length, 0);
    assert.ok((screen.getByRole('button', { name: 'Show results' }) as HTMLButtonElement).disabled);
    await user.click(screen.getByRole('checkbox', { name: /synthetic demonstration inputs/ }));
    await user.click(screen.getByRole('button', { name: 'Show results' }));
    await screen.findByRole('heading', { name: 'Your research results' });
    assert.ok(screen.getByText('12.7%'));
    assert.ok(screen.getByText('Negative model classification'));
    const submitted = calls.find(call => call.path === '/api/assess')?.body;
    assert.equal(submitted?.sex, 0);
    assert.equal(Object.keys(submitted ?? {}).length, 13);
    assert.equal(calls.filter(call => call.path === '/api/report').length, 0);
    assert.equal(downloads, 0);
    await user.click(screen.getByRole('button', { name: 'Download PDF report' }));
    await waitFor(() => assert.equal(downloads, 1));
    assert.equal(calls.filter(call => call.path === '/api/report').length, 1);
    await user.click(screen.getByRole('button', { name: 'Edit answers' }));
    assert.equal((screen.getByRole('spinbutton', { name: /^Age/  }) as HTMLInputElement).value, '54');
    assert.equal(screen.queryByText('Negative model classification'), null);
    await user.click(screen.getByRole('button', { name: 'Next question' }));
    assert.equal((screen.getByRole('combobox', { name: 'Recorded sex' }) as HTMLSelectElement).value, '0');
    await user.click(screen.getByRole('button', { name: 'Reset example' }));
    assert.ok(screen.getByRole('heading', { name: 'What is the age?' }));
  } finally {
    cleanup();
    globalThis.fetch = originalFetch;
    URL.createObjectURL = originalCreate;
    URL.revokeObjectURL = originalRevoke;
    dom.window.HTMLAnchorElement.prototype.click = originalClick;
    dom.window.close();
  }
});
