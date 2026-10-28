// @vitest-environment jsdom
/**
 * The page (01-functional V2 §2.1): three fields, result view, per-field errors, general error.
 * Uses a fake API client, so only the page's own behaviour is tested here.
 */
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { mountCalculator } from '../../src/page.js';
import { MESSAGES } from '../../src/presentation.js';

const RESULT = {
  id: null, numberOfPayments: 360, regularPayment: '449.04', finalPayment: '452.02',
  totalPaid: '161657.38', totalInterest: '61657.38',
};

let root;
let client;

function fakeClient(...outcomes) {
  const calculate = vi.fn();
  for (const outcome of outcomes) calculate.mockResolvedValueOnce(outcome);
  return { calculate };
}

function mount(...outcomes) {
  client = fakeClient(...outcomes);
  mountCalculator(root, client);
}

const input = (field) => root.querySelector(`#${field}`);
const fieldError = (field) => root.querySelector(`#${field}-error`).textContent;
const resultLines = () => [...root.querySelectorAll('[data-testid="result"] li')].map((li) => li.textContent);
const generalError = () => root.querySelector('[data-testid="general-error"]').textContent;

function fill(values) {
  for (const [field, value] of Object.entries(values)) input(field).value = value;
}

async function submit() {
  root.querySelector('form').dispatchEvent(new Event('submit', { cancelable: true, bubbles: true }));
  await vi.waitFor(() => expect(root.querySelector('button[type="submit"]').disabled).toBe(false));
}

beforeEach(() => {
  document.body.innerHTML = '<main id="app"></main>';
  root = document.getElementById('app');
});

describe('page', () => {
  it('test_page_has_three_empty_fields_with_labels_and_maxlength', () => {
    mount();
    for (const [field, label] of [['loanAmount', 'Loan amount (EUR)'], ['annualRate', 'Annual interest rate (%)'],
      ['termYears', 'Term (years)']]) {
      expect(input(field).value).toBe('');
      expect(input(field).getAttribute('maxlength')).toBe('100');
      expect(root.querySelector(`label[for="${field}"]`).textContent).toBe(label);
    }
  });

  it('test_page_sends_the_text_exactly_as_typed', async () => {
    mount({ kind: 'result', result: RESULT });
    fill({ loanAmount: ' 100 000 ', annualRate: '3,5', termYears: '' });
    await submit();
    // Phase 7: the page always passes the (here empty) extra-payment rows; the client omits an empty list.
    expect(client.calculate).toHaveBeenCalledWith({ loanAmount: ' 100 000 ', annualRate: '3,5', termYears: '', extraPayments: [] });
  });

  it('test_page_shows_result_lines', async () => {
    mount({ kind: 'result', result: RESULT });
    fill({ loanAmount: '100 000', annualRate: '3,5', termYears: '30' });
    await submit();
    expect(resultLines()).toEqual([
      'Regular Monthly Payment: 449,04 €',
      'Final Payment: 452,02 €',
      'Total Paid: 161 657,38 €',
      'Total Interest: 61 657,38 €',
    ]);
  });

  it('test_page_hides_an_equal_final_payment', async () => {
    mount({ kind: 'result', result: { ...RESULT, finalPayment: '449.04' } });
    await submit();
    expect(resultLines().some((line) => line.startsWith('Final Payment'))).toBe(false);
  });

  it('test_page_shows_one_message_under_each_invalid_field_and_keeps_values', async () => {
    mount({ kind: 'invalid', errors: [{ field: 'loanAmount', code: 'not_a_number' }, { field: 'termYears', code: 'above_max' }] });
    fill({ loanAmount: 'abc', annualRate: '3', termYears: '31' });
    await submit();
    expect(fieldError('loanAmount')).toBe('Loan amount must be a number.');
    expect(fieldError('annualRate')).toBe('');
    expect(fieldError('termYears')).toBe('Term must be between 1 and 30 years.');
    expect(input('loanAmount').getAttribute('aria-invalid')).toBe('true');
    expect(input('annualRate').hasAttribute('aria-invalid')).toBe(false);
    expect([input('loanAmount').value, input('annualRate').value, input('termYears').value]).toEqual(['abc', '3', '31']);
    expect(resultLines()).toEqual([]);
  });

  it('test_page_failure_shows_the_general_message_and_no_result', async () => {
    mount({ kind: 'result', result: RESULT }, { kind: 'failure' });
    await submit();
    expect(resultLines()).toHaveLength(4);
    await submit();
    expect(resultLines()).toEqual([]);
    expect(root.querySelector('[data-testid="result"]').hidden).toBe(true);
    expect(generalError()).toBe(MESSAGES.failure);
  });

  it('test_page_client_that_throws_is_a_failure', async () => {
    client = { calculate: vi.fn().mockResolvedValueOnce({ kind: 'result', result: RESULT }).mockRejectedValueOnce(new Error('x')) };
    mountCalculator(root, client);
    await submit();
    await submit();
    expect(root.querySelector('[data-testid="result"]').hidden).toBe(true);
    expect(generalError()).toBe(MESSAGES.failure);
  });

  it('test_page_invalid_after_result_hides_the_result_section', async () => {
    mount({ kind: 'result', result: RESULT }, { kind: 'invalid', errors: [{ field: 'termYears', code: 'required' }] });
    await submit();
    expect(root.querySelector('[data-testid="result"]').hidden).toBe(false);
    await submit();
    expect(root.querySelector('[data-testid="result"]').hidden).toBe(true);
  });

  it('test_page_rapid_submits_send_one_request', async () => {
    let resolve;
    client = { calculate: vi.fn(() => new Promise((r) => { resolve = r; })) };
    mountCalculator(root, client);
    for (let i = 0; i < 3; i++) root.querySelector('form').requestSubmit();
    expect(client.calculate).toHaveBeenCalledTimes(1);
    expect(root.querySelector('form').getAttribute('aria-busy')).toBe('true');
    resolve({ kind: 'failure' });
    await vi.waitFor(() => expect(root.querySelector('form').hasAttribute('aria-busy')).toBe(false));
  });

  it('test_page_clears_old_errors_on_success', async () => {
    mount({ kind: 'invalid', errors: [{ field: 'loanAmount', code: 'required' }] }, { kind: 'result', result: RESULT });
    await submit();
    expect(fieldError('loanAmount')).toBe('Loan amount is required.');
    await submit();
    expect(fieldError('loanAmount')).toBe('');
    expect(input('loanAmount').hasAttribute('aria-invalid')).toBe(false);
    expect(generalError()).toBe('');
  });

  it('test_page_unknown_error_field_shows_the_general_message', async () => {
    mount({ kind: 'invalid', errors: [{ field: 'extraPayments', code: 'x', index: 0 }] });
    await submit();
    expect(generalError()).toBe(MESSAGES.invalidInput);
  });

  it('test_page_disables_the_button_while_calculating', async () => {
    let resolve;
    client = { calculate: vi.fn(() => new Promise((r) => { resolve = r; })) };
    mountCalculator(root, client);
    const button = root.querySelector('button[type="submit"]');
    root.querySelector('form').dispatchEvent(new Event('submit', { cancelable: true, bubbles: true }));
    expect(button.disabled).toBe(true);
    root.querySelector('form').dispatchEvent(new Event('submit', { cancelable: true, bubbles: true }));
    expect(client.calculate).toHaveBeenCalledTimes(1);
    resolve({ kind: 'result', result: RESULT });
    await vi.waitFor(() => expect(button.disabled).toBe(false));
  });
});
