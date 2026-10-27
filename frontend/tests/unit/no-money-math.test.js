/**
 * Guard for the contract rule "clients MUST NOT do arithmetic on Money" (api/openapi.yaml) and
 * CLAUDE.md "the frontend only formats amounts it receives": the source uses no number conversion,
 * no rounding and no Intl formatting.
 */
import { readdirSync, readFileSync } from 'node:fs';
import { describe, expect, it } from 'vitest';

const SRC = new URL('../../src/', import.meta.url);
const FORBIDDEN = [/parseFloat/, /parseInt/, /\bNumber\(/, /toFixed/, /toPrecision/, /\bMath\./, /\bIntl\b/, /\bBigInt\b/];

describe('no money arithmetic', () => {
  it('test_frontend_source_does_no_number_conversion_or_rounding', () => {
    const files = readdirSync(SRC).filter((name) => name.endsWith('.js'));
    expect(files.length).toBeGreaterThanOrEqual(4);
    const hits = files.flatMap((name) => {
      const code = readFileSync(new URL(name, SRC), 'utf8').replace(/\/\*[\s\S]*?\*\/|\/\/.*$/gm, '');
      return FORBIDDEN.filter((pattern) => pattern.test(code)).map((pattern) => `${name}: ${pattern}`);
    });
    expect(hits).toEqual([]);
  });
});
