// @vitest-environment jsdom
/**
 * Phase 7 — the extra-payment rows on the page (docs/v2/04-extra-payments.md §2, §4.2–4.3).
 */
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { mountCalculator } from '../../src/page.js';

const RESULT = {
  id: null, numberOfPayments: 60, regularPayment: '449.04', finalPayment: '90146.42', totalPaid: '116639.78',
  totalInterest: '16639.78', monthsSaved: 300, interestSaved: '45017.60',
  extraPayments: [
    { month: 60, amount: '50000.00', usedAmount: '39697.38', status: 'partly_used' },
    { month: 120, amount: '1000.00', usedAmount: '0.00', status: 'after_payoff' },
  ],
};

let root;
let client;

function mount(...outcomes) {
  client = { calculate: vi.fn() };
  for (const outcome of outcomes) client.calculate.mockResolvedValueOnce(outcome);
  mountCalculator(root, client);
}

const addButton = () => root.querySelector('[data-testid="add-extra"]');
const rows = () => [...root.querySelectorAll('[data-testid="extra-row"]')];
const rowInput = (n, prop) => rows()[n - 1].querySelector(`[data-property="${prop}"]`);
const rowError = (n, prop) => rows()[n - 1].querySelector(`[data-error="${prop}"]`).textContent;
const notes = () => [...root.querySelectorAll('[data-testid="extra-notes"] li')].map((li) => li.textContent);
const resultLines = () => [...root.querySelectorAll('[data-testid="result"] ul.lines li')].map((li) => li.textContent);

function fillBase() {
  root.querySelector('#loanAmount').value = '100 000';
  root.querySelector('#annualRate').value = '3,5';
  root.querySelector('#termYears').value = '30';
}

function addRow(month, amount) {
  addButton().click();
  const n = rows().length;
  rowInput(n, 'month').value = month;
  rowInput(n, 'amount').value = amount;
}

async function submit() {
  root.querySelector('form').requestSubmit();
  await vi.waitFor(() => expect(root.querySelector('button[type="submit"]').disabled).toBe(false));
}

beforeEach(() => {
  document.body.innerHTML = '<main id="app"></main>';
  root = document.getElementById('app');
});

describe('extra-payment rows', () => {
  it('test_page_starts_with_no_rows_and_a_help_text', () => {
    mount();
    expect(rows()).toHaveLength(0);
    expect(root.textContent).toContain('If several extra payments are in the same month, the first one entered is used first.');
  });

  it('test_rows_have_labelled_month_and_amount_with_maxlength', () => {
    mount();
    addButton().click();
    for (const prop of ['month', 'amount']) {
      const input = rowInput(1, prop);
      expect(input.getAttribute('maxlength')).toBe('100');
      expect(root.querySelector(`label[for="${input.id}"]`).textContent).toBe(prop === 'month' ? 'Month' : 'Amount (EUR)');
    }
  });

  it('test_at_most_ten_rows', () => {
    mount();
    for (let i = 0; i < 12; i++) if (!addButton().disabled) addButton().click();
    expect(rows()).toHaveLength(10);
    expect(addButton().disabled).toBe(true);
    rows()[0].querySelector('[data-testid="remove-extra"]').click();
    expect(rows()).toHaveLength(9);
    expect(addButton().disabled).toBe(false);
  });

  it('test_remove_deletes_that_row', () => {
    mount();
    addRow('1', 'a');
    addRow('2', 'b');
    addRow('3', 'c');
    rows()[1].querySelector('[data-testid="remove-extra"]').click();
    expect(rows().map((r) => r.querySelector('[data-property="month"]').value)).toEqual(['1', '3']);
  });

  it('test_rows_are_sent_exactly_as_typed_and_blank_rows_are_skipped', async () => {
    mount({ kind: 'result', result: RESULT });
    fillBase();
    addRow(' ', '  ');
    addRow(' 60 ', '50 000');
    addRow('', '');
    addRow('120', '');
    await submit();
    expect(client.calculate).toHaveBeenCalledWith({
      loanAmount: '100 000', annualRate: '3,5', termYears: '30',
      extraPayments: [{ month: ' 60 ', amount: '50 000' }, { month: '120', amount: '' }],
    });
  });

  it('test_no_rows_sends_no_extra_payments', async () => {
    mount({ kind: 'result', result: { ...RESULT, monthsSaved: 0, interestSaved: '0.00', extraPayments: [] } });
    fillBase();
    await submit();
    expect(client.calculate.mock.calls[0][0].extraPayments).toEqual([]);
  });

  it('test_item_errors_go_to_the_right_row_after_a_blank_row', async () => {
    mount({ kind: 'invalid', errors: [{ field: 'extraPayments', index: 0, property: 'month', code: 'not_a_number' }] });
    fillBase();
    addRow('', '');
    addRow('abc', '100');
    await submit();
    expect(rowError(2, 'month')).toBe('Extra payment 2: month must be a number.');
    expect(rowError(1, 'month')).toBe('');
    expect(rowInput(2, 'month').getAttribute('aria-invalid')).toBe('true');
    expect(rowInput(2, 'amount').hasAttribute('aria-invalid')).toBe(false);
    expect(rowInput(2, 'month').value).toBe('abc');
  });

  it('test_result_shows_extra_lines_and_notes', async () => {
    mount({ kind: 'result', result: RESULT });
    fillBase();
    addRow('60', '50 000');
    addRow('120', '1 000');
    await submit();
    expect(resultLines().slice(-3)).toEqual([
      'Loan paid off after: 5 years (60 payments)',
      'Time saved: 25 years',
      'Interest saved: 45 017,60 €',
    ]);
    expect(notes()).toEqual([
      'Extra payment in month 60: only 39 697,38 € of 50 000,00 € was needed to pay off the loan.',
      'Extra payment in month 120 (1 000,00 €) was not used: the loan was already paid off.',
    ]);
  });

  it('test_old_errors_and_notes_are_cleared_on_the_next_result', async () => {
    mount({ kind: 'invalid', errors: [{ field: 'extraPayments', index: 0, property: 'amount', code: 'required' }] },
      { kind: 'result', result: { ...RESULT, extraPayments: [] } });
    fillBase();
    addRow('60', '');
    await submit();
    expect(rowError(1, 'amount')).toBe('Extra payment 1: amount is required.');
    await submit();
    expect(rowError(1, 'amount')).toBe('');
    expect(rowInput(1, 'amount').hasAttribute('aria-invalid')).toBe(false);
    expect(notes()).toEqual([]);
  });

  it('test_removing_a_row_clears_stale_mapping', async () => {
    mount({ kind: 'invalid', errors: [{ field: 'extraPayments', index: 0, property: 'month', code: 'required' }] });
    fillBase();
    addRow('1', '1');
    addRow('', '5');
    rows()[0].querySelector('[data-testid="remove-extra"]').click();
    await submit();
    expect(rows()).toHaveLength(1);
    expect(rowError(1, 'month')).toBe('Extra payment 1: month is required.');
  });

  it('test_whitespace_only_rows_are_blank', async () => {
    mount({ kind: 'result', result: RESULT });
    fillBase();
    addRow('	', ' ');
    addRow('　', ' ');
    await submit();
    expect(client.calculate.mock.calls[0][0].extraPayments).toEqual([]);
  });

  it('test_a_failure_clears_row_errors_and_notes', async () => {
    mount({ kind: 'result', result: RESULT },
      { kind: 'invalid', errors: [{ field: 'extraPayments', index: 0, property: 'amount', code: 'required' }] },
      { kind: 'failure' });
    fillBase();
    addRow('60', '');
    await submit();
    expect(notes()).toHaveLength(2);
    await submit();
    expect(notes()).toEqual([]);
    expect(rowError(1, 'amount')).toBe('Extra payment 1: amount is required.');
    expect(rowInput(1, 'amount').getAttribute('aria-invalid')).toBe('true');
    await submit();
    expect(rowError(1, 'amount')).toBe('');
    expect(rowInput(1, 'amount').hasAttribute('aria-invalid')).toBe(false);
  });
});
