# Frontend (JavaScript)

The web page: three input fields, the results and the error messages. It calls the backend API (`api/openapi.yaml`) and does no financial math: it sends the text exactly as typed and only formats the amounts it receives.

Vite + vanilla JavaScript; Vitest (unit, jsdom) and Playwright (end to end, in the installed Microsoft Edge).

## Run

Start the backend first (see `backend/README.md`), then:

```bash
cd frontend
npm.cmd install
npm.cmd run dev
```

Open http://localhost:5173. Vite forwards `/api` to the backend (`MORTGAGE_API_URL`, default `http://localhost:8000`), so the page and the API share one origin, as in the contract (`servers: /`).

## Test

```bash
npm.cmd test
npm.cmd run e2e
```

`npm.cmd run e2e` starts its own backend (port 8766) and Vite (port 5174). Playwright uses `channel: 'msedge'`, so no browser download is needed.

## Modules

| Module | V1 | Rule |
|---|---|---|
| `src/formatting.js` | M5 | `"1234.57"` → `1 234,57 €`. Accepts only canonical Money strings and never rounds. |
| `src/presentation.js` | M6 | V1 texts, labels and order. `shouldShowFinalPayment` compares strings. Unknown codes and fields get a generic message. Phase 7: `formatDuration`, `formatPayments`, the extra result lines, notes per status, item errors with the form row number; unknown statuses, codes and properties get generic texts. |
| `src/api-client.js` | — | `calculate(raw)` → `result` / `invalid` / `failure`; checks the response shape; never rejects. Sends `extraPayments` (month and amount only) only when there are some. |
| `src/page.js` | (M8) | The form; errors under each field (`aria-invalid`); one general error; `maxlength="100"`; one request at a time. Phase 7: up to 10 extra-payment rows (add/remove), blank rows skipped, a sent-index → row map for item errors, notes per status. |
| `src/main.js` | (M9) | Wires the page to the client (`VITE_API_BASE_URL`, default same origin). |

`tests/unit/no-money-math.test.js` fails if `src/` uses `parseFloat`, `Number(`, `toFixed`, `Math.`, `Intl` or `BigInt`.
