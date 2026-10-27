/**
 * API client (api/openapi.yaml `createCalculation`), tested against a fake fetch.
 */
import { describe, expect, it, vi } from 'vitest';
import { createApiClient } from '../../src/api-client.js';

const RAW = { loanAmount: '100 000', annualRate: '3,5', termYears: '30' };
const RESULT = {
  id: null, numberOfPayments: 360, regularPayment: '449.04', finalPayment: '452.02',
  totalPaid: '161657.38', totalInterest: '61657.38',
};

function fakeFetch(status, body, contentType = 'application/json') {
  return vi.fn(async () => new Response(typeof body === 'string' ? body : JSON.stringify(body), {
    status, headers: { 'content-type': contentType },
  }));
}

describe('api client', () => {
  it('test_client_posts_the_raw_text_as_json', async () => {
    const fetch = fakeFetch(200, RESULT);
    await createApiClient({ baseUrl: 'http://api.test', fetch }).calculate(RAW);
    expect(fetch).toHaveBeenCalledTimes(1);
    const [url, init] = fetch.mock.calls[0];
    expect(url).toBe('http://api.test/api/v1/calculations');
    expect(init.method).toBe('POST');
    expect(init.headers['Content-Type']).toBe('application/json');
    expect(JSON.parse(init.body)).toEqual(RAW);
  });

  it('test_client_uses_the_same_origin_by_default', async () => {
    const fetch = fakeFetch(200, RESULT);
    await createApiClient({ fetch }).calculate(RAW);
    expect(fetch.mock.calls[0][0]).toBe('/api/v1/calculations');
  });

  it.each([
    ['an unknown property', { ...RAW, extra: 'x' }],
    ['extraPayments before Phase 7', { ...RAW, extraPayments: [] }],
  ])('test_client_sends_only_the_three_fields (%s)', async (_name, raw) => {
    const fetch = fakeFetch(200, RESULT);
    await createApiClient({ fetch }).calculate(raw);
    expect(Object.keys(JSON.parse(fetch.mock.calls[0][1].body))).toEqual(['loanAmount', 'annualRate', 'termYears']);
  });

  it('test_client_200_is_a_result', async () => {
    const outcome = await createApiClient({ fetch: fakeFetch(200, RESULT) }).calculate(RAW);
    expect(outcome).toEqual({ kind: 'result', result: RESULT });
  });

  it('test_client_ignores_unknown_response_properties', async () => {
    const outcome = await createApiClient({ fetch: fakeFetch(200, { ...RESULT, monthsSaved: 12 }) }).calculate(RAW);
    expect(outcome.kind).toBe('result');
  });

  it('test_client_422_is_invalid_with_errors', async () => {
    const errors = [{ field: 'annualRate', code: 'above_max' }];
    const outcome = await createApiClient({ fetch: fakeFetch(422, { errors }) }).calculate(RAW);
    expect(outcome).toEqual({ kind: 'invalid', errors });
  });

  it.each([400, 413, 415, 429, 500, 502, 404])('test_client_status_%i_is_a_failure', async (status) => {
    const body = { type: 'about:blank', title: 'x', status };
    const outcome = await createApiClient({ fetch: fakeFetch(status, body, 'application/problem+json') }).calculate(RAW);
    expect(outcome).toEqual({ kind: 'failure' });
  });

  it.each([
    ['network error', new TypeError('Failed to fetch')],
    ['aborted request', new DOMException('The operation was aborted.', 'AbortError')],
  ])('test_client_%s_is_a_failure', async (_name, error) => {
    const fetch = vi.fn(async () => { throw error; });
    expect(await createApiClient({ fetch }).calculate(RAW)).toEqual({ kind: 'failure' });
  });

  it.each([
    ['not json', '<html>proxy error</html>'],
    ['money as a number', { ...RESULT, regularPayment: 449.04 }],
    ['non-canonical money', { ...RESULT, totalPaid: '161657.4' }],
    ['money with three decimals', { ...RESULT, totalPaid: '161657.380' }],
    ['missing field', { ...RESULT, finalPayment: undefined }],
    ['array', [RESULT]],
  ])('test_client_malformed_200_is_a_failure (%s)', async (_name, body) => {
    expect(await createApiClient({ fetch: fakeFetch(200, body) }).calculate(RAW)).toEqual({ kind: 'failure' });
  });

  it.each([
    ['no errors array', {}],
    ['empty errors', { errors: [] }],
    ['error without code', { errors: [{ field: 'loanAmount' }] }],
  ])('test_client_malformed_422_is_a_failure (%s)', async (_name, body) => {
    expect(await createApiClient({ fetch: fakeFetch(422, body) }).calculate(RAW)).toEqual({ kind: 'failure' });
  });
});
