/**
 * The calculator page (docs/v2/01-functional.md §2.1).
 *
 * mountCalculator(root, client) renders the form into `root` and wires it to an API client
 * (src/api-client.js). Every dynamic text is set with textContent, never as HTML.
 */
import { FIELDS, INPUT_LABELS, MESSAGES, toErrorView, toResultView } from './presentation.js';

const TEMPLATE = `
  <form novalidate>
    ${FIELDS.map((field) => `
      <div class="field">
        <label for="${field}">${INPUT_LABELS[field]}</label>
        <input id="${field}" name="${field}" type="text" inputmode="decimal" maxlength="100"
               autocomplete="off" aria-describedby="${field}-error">
        <p class="field-error" id="${field}-error"></p>
      </div>`).join('')}
    <button type="submit">${MESSAGES.calculate}</button>
    <p class="general-error" data-testid="general-error" role="alert"></p>
  </form>
  <section class="result" data-testid="result" aria-live="polite" hidden>
    <h2>${MESSAGES.resultHeading}</h2>
    <ul></ul>
  </section>`;

export function mountCalculator(root, client) {
  root.innerHTML = TEMPLATE;
  const form = root.querySelector('form');
  const button = form.querySelector('button[type="submit"]');
  const generalError = form.querySelector('[data-testid="general-error"]');
  const resultSection = root.querySelector('[data-testid="result"]');
  const resultList = resultSection.querySelector('ul');
  const inputs = Object.fromEntries(FIELDS.map((field) => [field, form.querySelector(`#${field}`)]));
  const fieldErrors = Object.fromEntries(FIELDS.map((field) => [field, form.querySelector(`#${field}-error`)]));
  let busy = false;

  function clear() {
    for (const field of FIELDS) {
      fieldErrors[field].textContent = '';
      inputs[field].removeAttribute('aria-invalid');
    }
    generalError.textContent = '';
    resultList.replaceChildren();
    resultSection.hidden = true;
  }

  function showResult(result) {
    resultList.replaceChildren(...toResultView(result).lines.map((line) => {
      const item = document.createElement('li');
      item.textContent = `${line.label}: ${line.value}`;
      return item;
    }));
    resultSection.hidden = false;
  }

  function showErrors(errors) {
    const view = toErrorView(errors);
    for (const { field, message } of view.errors) {
      fieldErrors[field].textContent = message;
      inputs[field].setAttribute('aria-invalid', 'true');
    }
    if (view.general) generalError.textContent = view.general;
  }

  function render(outcome) {
    clear();
    if (outcome.kind === 'result') {
      try {
        showResult(outcome.result);
      } catch {
        clear();
        generalError.textContent = MESSAGES.failure;
      }
    } else if (outcome.kind === 'invalid') {
      showErrors(outcome.errors);
    } else {
      generalError.textContent = MESSAGES.failure;
    }
  }

  form.addEventListener('submit', async (event) => {
    event.preventDefault();
    if (busy) return;
    busy = true;
    button.disabled = true;
    form.setAttribute('aria-busy', 'true');
    try {
      // The text exactly as typed: the backend owns parsing and validation (D3).
      const raw = Object.fromEntries(FIELDS.map((field) => [field, inputs[field].value]));
      render(await client.calculate(raw));
    } catch {
      render({ kind: 'failure' });
    } finally {
      busy = false;
      button.disabled = false;
      form.removeAttribute('aria-busy');
    }
  });
}
