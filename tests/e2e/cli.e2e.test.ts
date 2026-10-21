/**
 * M9 — main, end to end (03-test-scenarios.md tests 89–92, 110).
 *
 * Spawns the real program through tsx with piped stdin/stdout. `process.execPath` with
 * `--import tsx` replaces `npx tsx`, which needs a shell on Windows (05-plan §6.2).
 */
import { spawn } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import { describe, expect, it } from 'vitest';

const PROJECT_ROOT = fileURLToPath(new URL('../..', import.meta.url));
const TIMEOUT = 30_000;

interface RunResult {
  stdout: string;
  stderr: string;
  code: number | null;
}

/** Runs `src/main.ts` with `stdin` piped in and closed, and collects its output and exit code. */
function runMain(stdin: string): Promise<RunResult> {
  return new Promise((resolve, reject) => {
    const child = spawn(process.execPath, ['--import', 'tsx', 'src/main.ts'], {
      cwd: PROJECT_ROOT,
      stdio: ['pipe', 'pipe', 'pipe'],
    });
    let stdout = '';
    let stderr = '';
    child.stdout.setEncoding('utf8').on('data', (chunk: string) => (stdout += chunk));
    child.stderr.setEncoding('utf8').on('data', (chunk: string) => (stderr += chunk));
    child.on('error', reject);
    child.on('close', (code) => resolve({ stdout, stderr, code }));
    child.stdin.end(stdin);
  });
}

describe('main (e2e)', () => {
  it(
    'test_e2e_cli_standard_mortgage',
    async () => {
      const { stdout, stderr, code } = await runMain('100 000\n3,5\n30\n');
      expect(stderr).toBe('');
      expect(stdout).toContain('Loan amount (EUR): ');
      expect(stdout).toContain('Annual interest rate (%): ');
      expect(stdout).toContain('Term (years): ');
      expect(stdout).toContain('Regular Monthly Payment: 449,04 €');
      expect(stdout).toContain('Final Payment: 452,02 €');
      expect(stdout).toContain('Total Paid: 161 657,38 €');
      expect(stdout).toContain('Total Interest: 61 657,38 €');
      expect(code).toBe(0);
    },
    TIMEOUT,
  );

  it(
    'test_e2e_cli_zero_rate_hides_final_payment',
    async () => {
      const { stdout, code } = await runMain('120000\n0\n10\n');
      expect(stdout).toContain('Regular Monthly Payment: 1 000,00 €');
      expect(stdout).toContain('Total Paid: 120 000,00 €');
      expect(stdout).toContain('Total Interest: 0,00 €');
      expect(stdout).not.toContain('Final Payment');
      expect(code).toBe(0);
    },
    TIMEOUT,
  );

  it(
    'test_e2e_cli_invalid_then_corrected_input',
    async () => {
      const { stdout, code } = await runMain('1,000.50\n25\n10\n1000,50\n2,5\n');
      expect(stdout).toContain('Loan amount must be a number.');
      expect(stdout).toContain('Annual interest rate must be between 0,00 % and 20,00 %.');
      // Loan and rate are asked twice, the valid term only once.
      expect(stdout.split('Loan amount (EUR): ')).toHaveLength(3);
      expect(stdout.split('Annual interest rate (%): ')).toHaveLength(3);
      expect(stdout.split('Term (years): ')).toHaveLength(2);
      expect(stdout).toContain('Regular Monthly Payment: 9,43 €');
      expect(stdout).toContain('Final Payment: 9,66 €');
      expect(stdout).toContain('Total Paid: 1 131,83 €');
      expect(stdout).toContain('Total Interest: 131,33 €');
      expect(code).toBe(0);
    },
    TIMEOUT,
  );

  it(
    'test_e2e_cli_input_closed_early',
    async () => {
      const { stdout, code } = await runMain('100000\n');
      expect(stdout).not.toContain('Regular Monthly Payment');
      expect(stdout).not.toContain('Final Payment');
      expect(stdout).not.toContain('Total Paid');
      expect(stdout).not.toContain('Total Interest');
      expect(code).toBe(1);
    },
    TIMEOUT,
  );

  it(
    'test_e2e_cli_early_termination',
    async () => {
      const { stdout, code } = await runMain('1000,29\n20\n30\n');
      expect(stdout).toContain('Regular Monthly Payment: 16,72 €');
      expect(stdout).toContain('Final Payment: 8,08 €');
      expect(stdout).toContain('Total Paid: 5 910,24 €');
      expect(stdout).toContain('Total Interest: 4 909,95 €');
      expect(code).toBe(0);
    },
    TIMEOUT,
  );
});
