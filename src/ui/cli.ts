/**
 * M8 — ui/cli (02-architecture.md §3, M8 and ADR-10; 01-functional.md FR-1–FR-3).
 *
 * Terminal adapter: the only module that exchanges text with the user.
 */
import { createInterface } from 'node:readline';
import { runCalculator } from '../app/calculator.js';
import type { Field, RawLoanInput } from '../domain/types.js';

/** Port: the only way the CLI touches the outside world (injectable for tests). */
export interface TerminalIo {
  ask(question: string): Promise<string | undefined>; // undefined = input stream closed
  print(line: string): void;
  close(): void;
}

/** Exact prompt texts from 03-test-scenarios.md, "Expected UI texts". */
const PROMPTS: Readonly<Record<Field, string>> = {
  loanAmount: 'Loan amount (EUR): ',
  annualRate: 'Annual interest rate (%): ',
  termYears: 'Term (years): ',
};

/** Fields in the order they are asked. */
const FIELD_ORDER: readonly Field[] = ['loanAmount', 'annualRate', 'termYears'];

/**
 * Event-driven line queue over node:readline (ADR-10). Lines arriving before an `ask` are queued,
 * and at EOF the pending `ask` and every later one resolve to `undefined`, so no promise is left unsettled.
 */
export function createNodeTerminalIo(
  input: NodeJS.ReadableStream = process.stdin,
  output: NodeJS.WritableStream = process.stdout,
): TerminalIo {
  const rl = createInterface({ input, terminal: false, crlfDelay: Infinity });
  const lines: string[] = [];
  let pending: ((line: string | undefined) => void) | undefined;
  let ended = false;

  rl.on('line', (line) => {
    if (pending) {
      const resolve = pending;
      pending = undefined;
      resolve(line);
    } else {
      lines.push(line);
    }
  });
  rl.on('close', () => {
    ended = true;
    const resolve = pending;
    pending = undefined;
    resolve?.(undefined);
  });

  return {
    ask(question) {
      output.write(question);
      if (lines.length > 0) return Promise.resolve(lines.shift());
      if (ended) return Promise.resolve(undefined);
      return new Promise((resolve) => {
        pending = resolve;
      });
    },
    print(line) {
      output.write(`${line}\n`);
    },
    close() {
      rl.close(); // a no-op once the interface is closed
    },
  };
}

/** Asks for the inputs until all are valid, prints the result, and returns the process exit code. */
export async function runCli(io: TerminalIo): Promise<number> {
  try {
    const answers: Record<Field, string | undefined> = {
      loanAmount: undefined,
      annualRate: undefined,
      termYears: undefined,
    };
    let toAsk: readonly Field[] = FIELD_ORDER;
    for (;;) {
      for (const field of toAsk) {
        const answer = await io.ask(PROMPTS[field]);
        if (answer === undefined) return 1; // input closed before all answers were valid (FR-3)
        answers[field] = answer;
      }
      const raw: RawLoanInput = { ...answers };
      const outcome = runCalculator(raw);
      if (outcome.kind === 'result') {
        for (const line of outcome.view.lines) io.print(`${line.label}: ${line.value}`);
        return 0;
      }
      for (const error of outcome.view.errors) io.print(error.message);
      toAsk = outcome.view.errors.map((error) => error.field);
    }
  } finally {
    io.close();
  }
}
