/**
 * End to end: browser (Edge) → Vite → real FastAPI backend (playwright.config.js starts both).
 * Browser versions of the V1 CLI e2e tests 89–91 (docs/v1/03-test-scenarios.md), plus V2 cases.
 */
import { expect, test } from '@playwright/test';

const field = (page, label) => page.getByLabel(label, { exact: true });
const resultLines = (page) => page.getByTestId('result').getByRole('listitem');

async function calculate(page, loanAmount, annualRate, termYears) {
  await field(page, 'Loan amount (EUR)').fill(loanAmount);
  await field(page, 'Annual interest rate (%)').fill(annualRate);
  await field(page, 'Term (years)').fill(termYears);
  await page.getByRole('button', { name: 'Calculate' }).click();
}

test.beforeEach(async ({ page }) => {
  await page.goto('/');
});

test('test_e2e_web_standard_mortgage', async ({ page }) => {
  await calculate(page, '100 000', '3,5', '30');
  await expect(resultLines(page)).toHaveText([
    'Regular Monthly Payment: 449,04 €',
    'Final Payment: 452,02 €',
    'Total Paid: 161 657,38 €',
    'Total Interest: 61 657,38 €',
  ]);
});

test('test_e2e_web_zero_rate_hides_final_payment', async ({ page }) => {
  await calculate(page, '120000', '0', '10');
  await expect(resultLines(page)).toHaveText([
    'Regular Monthly Payment: 1 000,00 €',
    'Total Paid: 120 000,00 €',
    'Total Interest: 0,00 €',
  ]);
});

test('test_e2e_web_invalid_then_corrected_input', async ({ page }) => {
  await calculate(page, '1,000.50', '25', '10');
  await expect(page.locator('#loanAmount-error')).toHaveText('Loan amount must be a number.');
  await expect(page.locator('#annualRate-error')).toHaveText('Annual interest rate must be between 0,00 % and 20,00 %.');
  await expect(page.locator('#termYears-error')).toHaveText('');
  await expect(field(page, 'Loan amount (EUR)')).toHaveAttribute('aria-invalid', 'true');
  await expect(field(page, 'Term (years)')).not.toHaveAttribute('aria-invalid');
  await expect(page.getByTestId('result')).toBeHidden();
  await expect(field(page, 'Loan amount (EUR)')).toHaveValue('1,000.50');  // values are kept

  await field(page, 'Loan amount (EUR)').fill('1000,50');
  await field(page, 'Annual interest rate (%)').fill('2,5');
  await page.getByRole('button', { name: 'Calculate' }).click();
  await expect(resultLines(page)).toHaveText([
    'Regular Monthly Payment: 9,43 €',
    'Final Payment: 9,66 €',
    'Total Paid: 1 131,83 €',
    'Total Interest: 131,33 €',
  ]);
  await expect(page.locator('#loanAmount-error')).toHaveText('');
});

test('test_e2e_web_early_termination_hides_equal_final_payment', async ({ page }) => {
  await calculate(page, '1 075,15', '20', '30');
  await expect(resultLines(page)).toHaveText([
    'Regular Monthly Payment: 17,97 €',
    'Total Paid: 6 379,35 €',
    'Total Interest: 5 304,20 €',
  ]);
});

test('test_e2e_web_all_missing', async ({ page }) => {
  await page.getByRole('button', { name: 'Calculate' }).click();
  await expect(page.locator('.field-error')).toHaveText([
    'Loan amount is required.', 'Annual interest rate is required.', 'Term is required.']);
});

test('test_e2e_web_sends_text_exactly_as_typed', async ({ page }) => {
  const request = page.waitForRequest('**/api/v1/calculations');
  await calculate(page, ' 100 000 ', '3,5', '30');
  expect((await request).postDataJSON()).toEqual({ loanAmount: ' 100 000 ', annualRate: '3,5', termYears: '30' });
  await expect(resultLines(page)).toHaveCount(4);
});

test('test_e2e_web_enter_key_submits', async ({ page }) => {
  await field(page, 'Loan amount (EUR)').fill('100000');
  await field(page, 'Annual interest rate (%)').fill('3,5');
  await field(page, 'Term (years)').fill('30');
  await field(page, 'Term (years)').press('Enter');
  await expect(resultLines(page)).toHaveCount(4);
});

test('test_e2e_web_backend_unreachable_shows_general_error', async ({ page }) => {
  await page.route('**/api/v1/calculations', (route) => route.abort('connectionrefused'));
  await calculate(page, '100 000', '3,5', '30');
  await expect(page.getByTestId('general-error')).toHaveText('The calculation could not be completed. Please try again later.');
  await expect(page.getByTestId('result')).toBeHidden();
});

test('test_e2e_web_maxlength_stops_at_100_characters', async ({ page }) => {
  await field(page, 'Loan amount (EUR)').fill('1'.repeat(150));
  await expect(field(page, 'Loan amount (EUR)')).toHaveValue('1'.repeat(100));
});

// --- Phase 7: extra payments (docs/v2/04-extra-payments.md §6) --------------------------------

async function addExtra(page, month, amount) {
  await page.getByRole('button', { name: 'Add extra payment' }).click();
  const row = page.getByTestId('extra-row').last();
  await row.getByLabel('Month').fill(month);
  await row.getByLabel('Amount (EUR)').fill(amount);
}

const lines = (page) => page.getByTestId('result').locator('ul.lines li');

test('test_e2e_web_extra_payment_shortens_the_term (E1)', async ({ page }) => {
  await field(page, 'Loan amount (EUR)').fill('100 000');
  await field(page, 'Annual interest rate (%)').fill('3,5');
  await field(page, 'Term (years)').fill('30');
  await addExtra(page, '24', '5 000');
  await page.getByRole('button', { name: 'Calculate' }).click();
  await expect(lines(page)).toHaveText([
    'Regular Monthly Payment: 449,04 €',
    'Final Payment: 246,84 €',
    'Total Paid: 153 879,08 €',
    'Total Interest: 53 879,08 €',
    'Loan paid off after: 27 years 8 months (332 payments)',
    'Time saved: 2 years 4 months',
    'Interest saved: 7 778,30 €',
  ]);
  await expect(page.getByTestId('extra-notes').locator('li')).toHaveCount(0);
});

test('test_e2e_web_pay_off_notes (E3)', async ({ page }) => {
  await field(page, 'Loan amount (EUR)').fill('100 000');
  await field(page, 'Annual interest rate (%)').fill('3,5');
  await field(page, 'Term (years)').fill('30');
  await addExtra(page, '60', '50 000');
  await addExtra(page, '60', '50 000');
  await addExtra(page, '120', '1 000');
  await page.getByRole('button', { name: 'Calculate' }).click();
  await expect(lines(page).nth(4)).toHaveText('Loan paid off after: 5 years (60 payments)');
  await expect(lines(page).nth(5)).toHaveText('Time saved: 25 years');
  await expect(page.getByTestId('extra-notes').locator('li')).toHaveText([
    'Extra payment in month 60: only 39 697,38 € of 50 000,00 € was needed to pay off the loan.',
    'Extra payment in month 120 (1 000,00 €) was not used: the loan was already paid off.',
  ]);
});

test('test_e2e_web_item_error_lands_on_the_right_row_after_a_blank_row', async ({ page }) => {
  await field(page, 'Loan amount (EUR)').fill('100 000');
  await field(page, 'Annual interest rate (%)').fill('3,5');
  await field(page, 'Term (years)').fill('10');
  await addExtra(page, '', '');
  await addExtra(page, '121', '1,234');
  await page.getByRole('button', { name: 'Calculate' }).click();
  const second = page.getByTestId('extra-row').nth(1);
  await expect(second.locator('[data-error="month"]')).toHaveText('Extra payment 2: month must be between 1 and the last month of the loan term.');
  await expect(second.locator('[data-error="amount"]')).toHaveText('Extra payment 2: amount can have at most 2 decimal places.');
  await expect(page.getByTestId('extra-row').first().locator('[data-error="month"]')).toHaveText('');
  await expect(page.getByTestId('result')).toBeHidden();
});

test('test_e2e_web_at_most_ten_extra_payments', async ({ page }) => {
  for (let i = 0; i < 10; i++) await page.getByRole('button', { name: 'Add extra payment' }).click();
  await expect(page.getByTestId('extra-row')).toHaveCount(10);
  await expect(page.getByRole('button', { name: 'Add extra payment' })).toBeDisabled();
});
