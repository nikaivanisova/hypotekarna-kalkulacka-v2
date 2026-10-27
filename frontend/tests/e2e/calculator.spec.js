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
