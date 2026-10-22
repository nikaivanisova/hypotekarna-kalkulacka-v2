/**
 * M8 — ui/cli (03-test-scenarios.md tests 85–88, 111–112).
 */
import { PassThrough } from 'node:stream';
import { describe, expect, it } from 'vitest';
import { createNodeTerminalIo, runCli, type TerminalIo } from '../../src/ui/cli.js';

const PROMPTS = {
  loanAmount: 'Loan amount (EUR): ',
  annualRate: 'Annual interest rate (%): ',
  termYears: 'Term (years): ',
} as const;

const RESULT_LINES = [
  'Regular Monthly Payment: 449,04 €',
  'Final Payment: 452,02 €',
  'Total Paid: 161 657,38 €',
  'Total Interest: 61 657,38 €',
];

/** Scripted fake: answers `ask` calls in order, then reports a closed stream (`undefined`). */
function scriptedIo(answers: readonly string[]) {
  const asked: string[] = [];
  const printed: string[] = [];
  let closed = false;
  const io: TerminalIo = {
    ask: (question) => {
      asked.push(question);
      return Promise.resolve(answers[asked.length - 1]);
    },
    print: (line) => {
      printed.push(line);
    },
    close: () => {
      closed = true;
    },
  };
  return { io, asked, printed, isClosed: () => closed };
}

function streams() {
  const input = new PassThrough();
  const output = new PassThrough();
  let written = '';
  output.on('data', (chunk: Buffer) => {
    written += chunk.toString('utf8');
  });
  return { input, output, written: () => written };
}

describe('cli (M8)', () => {
  it('test_cli_prompts_in_order', async () => {
    const fake = scriptedIo(['100000', '3.5', '30']);
    await runCli(fake.io);
    expect(fake.asked).toEqual([PROMPTS.loanAmount, PROMPTS.annualRate, PROMPTS.termYears]);
  });

  it('test_cli_prints_results_and_exits_zero', async () => {
    const fake = scriptedIo(['100000', '3.5', '30']);
    const exitCode = await runCli(fake.io);
    expect(fake.printed).toEqual(RESULT_LINES);
    expect(exitCode).toBe(0);
    expect(fake.isClosed()).toBe(true);
  });

  it('test_cli_reprompts_only_invalid_fields', async () => {
    const fake = scriptedIo(['abc', '3,5', '31', '100000', '30']);
    const exitCode = await runCli(fake.io);
    expect(fake.asked).toEqual([
      PROMPTS.loanAmount,
      PROMPTS.annualRate,
      PROMPTS.termYears,
      PROMPTS.loanAmount,
      PROMPTS.termYears,
    ]);
    expect(fake.printed).toEqual([
      'Loan amount must be a number.',
      'Term must be between 1 and 30 years.',
      ...RESULT_LINES,
    ]);
    expect(exitCode).toBe(0);
  });

  it('test_cli_closed_input_exits_one', async () => {
    const fake = scriptedIo([]);
    const exitCode = await runCli(fake.io);
    expect(fake.asked).toEqual([PROMPTS.loanAmount]);
    expect(fake.printed).toEqual([]);
    expect(exitCode).toBe(1);
    expect(fake.isClosed()).toBe(true);
  });

  it('test_node_terminal_io_answers_all_piped_lines', async () => {
    const lf = streams();
    const io = createNodeTerminalIo(lf.input, lf.output);
    lf.input.end('100 000\n3,5\n30\n');
    expect(await io.ask(PROMPTS.loanAmount)).toBe('100 000');
    expect(await io.ask(PROMPTS.annualRate)).toBe('3,5');
    expect(await io.ask(PROMPTS.termYears)).toBe('30');
    expect(await io.ask(PROMPTS.loanAmount)).toBeUndefined();
    io.close();
    expect(lf.written()).toContain(PROMPTS.loanAmount + PROMPTS.annualRate + PROMPTS.termYears);

    // Windows pipes deliver CRLF line endings (05-plan §6.2): they must not leak into the answers.
    const crlf = streams();
    const crlfIo = createNodeTerminalIo(crlf.input, crlf.output);
    crlf.input.end('100 000\r\n3,5\r\n30\r\n');
    expect(await crlfIo.ask(PROMPTS.loanAmount)).toBe('100 000');
    expect(await crlfIo.ask(PROMPTS.annualRate)).toBe('3,5');
    expect(await crlfIo.ask(PROMPTS.termYears)).toBe('30');
    expect(await crlfIo.ask(PROMPTS.loanAmount)).toBeUndefined();
    crlfIo.close();
    crlfIo.close(); // idempotent
  });

  it('test_node_terminal_io_pending_ask_resolves_at_eof', { timeout: 1_000 }, async () => {
    const { input, output, written } = streams();
    const io = createNodeTerminalIo(input, output);
    const answer = io.ask(PROMPTS.loanAmount);
    input.end();
    await expect(answer).resolves.toBeUndefined();
    expect(written()).toContain(PROMPTS.loanAmount);
    io.close();
  });
});
