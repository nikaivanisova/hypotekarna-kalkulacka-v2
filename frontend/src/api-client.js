/**
 * Client for `POST /api/v1/calculations` (api/openapi.yaml).
 *
 * calculate(raw) resolves to one of:
 *   { kind: 'result', result }   200 with a CalculationResult
 *   { kind: 'invalid', errors }  422 with validation errors
 *   { kind: 'failure' }          any other status, a network error, or a body that breaks the contract
 * It never rejects, so the page needs no error handling of its own.
 */
import { isMoney } from './formatting.js';

const FIELDS = ['loanAmount', 'annualRate', 'termYears'];
const MONEY_FIELDS = ['regularPayment', 'finalPayment', 'totalPaid', 'totalInterest'];
const FAILURE = Object.freeze({ kind: 'failure' });

const isObject = (value) => typeof value === 'object' && value !== null && !Array.isArray(value);

function isResult(body) {
  return isObject(body)
    && Number.isInteger(body.numberOfPayments)
    && MONEY_FIELDS.every((field) => isMoney(body[field]));
}

function isErrorList(body) {
  return isObject(body)
    && Array.isArray(body.errors)
    && body.errors.length > 0
    && body.errors.every((e) => isObject(e) && typeof e.field === 'string' && typeof e.code === 'string');
}

async function readJson(response) {
  try {
    return await response.json();
  } catch {
    return undefined;
  }
}

export function createApiClient({ baseUrl = '', fetch = (...args) => globalThis.fetch(...args) } = {}) {
  return {
    async calculate(raw) {
      // Only the contract's properties, exactly as typed (anything else would be a 400). The extra
      // payments are sent only when there are some (contract: the frontend omits an empty list).
      const request = Object.fromEntries(FIELDS.map((field) => [field, raw[field]]));
      if (Array.isArray(raw.extraPayments) && raw.extraPayments.length > 0) {
        request.extraPayments = raw.extraPayments.map(({ month, amount }) => ({ month, amount }));
      }
      const body = JSON.stringify(request);
      let response;
      try {
        response = await fetch(`${baseUrl}/api/v1/calculations`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
          body,
        });
      } catch {
        return FAILURE;
      }

      if (response.status === 200) {
        const result = await readJson(response);
        return isResult(result) ? { kind: 'result', result } : FAILURE;
      }
      if (response.status === 422) {
        const invalid = await readJson(response);
        return isErrorList(invalid) ? { kind: 'invalid', errors: invalid.errors } : FAILURE;
      }
      return FAILURE;
    },
  };
}
