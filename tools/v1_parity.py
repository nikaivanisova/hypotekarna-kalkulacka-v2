"""V1 ↔ V2 parity: runs the sweep loans through the V1 TypeScript code (legacy/cli) and the Python backend
and compares every output (plan §7, first risk). Run before deleting legacy/ in Phase 8.

Run from the repo root (needs `npm.cmd ci` in legacy/cli and `uv sync` in backend):
    backend/.venv/Scripts/python.exe tools/v1_parity.py
"""
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'backend'))

from mortgage.domain.calculation import calculate_mortgage  # noqa: E402
from mortgage.domain.types import LoanInput  # noqa: E402
from tests.sweep import sweep_inputs  # noqa: E402

# Reads [[principal, rate, years], ...] from stdin, prints V1's results as JSON.
V1_SCRIPT = """
import { Decimal } from 'decimal.js';
import { calculateMortgage } from './src/domain/calculation.ts';
let text = '';
for await (const chunk of process.stdin) text += chunk;
const out = JSON.parse(text).map(([p, rate, years]) => {
  const r = calculateMortgage({ principal: new Decimal(p), annualRatePercent: new Decimal(rate), termYears: years });
  return [r.numberOfPayments, r.regularPayment.toFixed(2), r.finalPayment.toFixed(2), r.totalPaid.toFixed(2), r.totalInterest.toFixed(2)];
});
process.stdout.write(JSON.stringify(out));
"""


def main() -> int:
    inputs = sweep_inputs()
    payload = json.dumps([[str(p), str(r), y] for p, r, y in inputs])
    node = subprocess.run(
        ['node', '--import', 'tsx', '--input-type=module', '-e', V1_SCRIPT],
        cwd=ROOT / 'legacy' / 'cli', input=payload, capture_output=True, text=True, check=True,
    )
    v1 = json.loads(node.stdout)
    mismatches = 0
    for (p, r, y), old in zip(inputs, v1, strict=True):
        x = calculate_mortgage(LoanInput(p, r, y))
        new = [x.number_of_payments, str(x.regular_payment), str(x.final_payment), str(x.total_paid), str(x.total_interest)]
        if new != old:
            mismatches += 1
            print(f'MISMATCH P={p} rate={r} years={y}: V1 {old} V2 {new}')
    print(f'compared {len(inputs)} loans, {mismatches} mismatches')
    return 1 if mismatches else 0


if __name__ == '__main__':
    sys.exit(main())
