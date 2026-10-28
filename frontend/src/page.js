/**
 * The calculator page (docs/v2/01-functional.md §2.1; extra payments: docs/v2/04-extra-payments.md §4.2).
 *
 * mountCalculator(root, client) renders the form into `root` and wires it to an API client
 * (src/api-client.js). Every dynamic text is set with textContent, never as HTML.
 */
import { FIELDS, INPUT_LABELS, MESSAGES, toErrorView, toResultView } from './presentation.js';

const MAX_EXTRA_PAYMENTS = 10;
const ITEM_PROPERTIES = ['month', 'amount'];

const TEMPLATE = `
  <form novalidate>
    ${FIELDS.map((field) => `
      <div class="field">
        <label for="${field}">${INPUT_LABELS[field]}</label>
        <input id="${field}" name="${field}" type="text" inputmode="decimal" maxlength="100"
               autocomplete="off" aria-describedby="${field}-error">
        <p class="field-error" id="${field}-error"></p>
      </div>`).join('')}
    <fieldset class="extras">
      <legend>${MESSAGES.extra.legend}</legend>
      <p class="help">${MESSAGES.extra.help}</p>
      <div class="extra-rows" data-testid="extra-rows"></div>
      <button type="button" class="secondary" data-testid="add-extra">${MESSAGES.extra.add}</button>
    </fieldset>
    <button type="submit">${MESSAGES.calculate}</button>
    <p class="general-error" data-testid="general-error" role="alert"></p>
  </form>
  <section class="result" data-testid="result" aria-live="polite" hidden>
    <h2>${MESSAGES.resultHeading}</h2>
    <ul class="lines"></ul>
    <ul class="notes" data-testid="extra-notes"></ul>
  </section>`;

let rowCounter = 0;

function createRow() {
  const id = `extra-${++rowCounter}`;
  const row = document.createElement('div');
  row.className = 'extra-row';
  row.dataset.testid = 'extra-row';
  for (const property of ITEM_PROPERTIES) {
    const inputId = `${id}-${property}`;
    const cell = document.createElement('div');
    cell.className = `field ${property}`;
    const label = document.createElement('label');
    label.htmlFor = inputId;
    label.textContent = MESSAGES.extra[property];
    const input = document.createElement('input');
    Object.assign(input, { id: inputId, type: 'text', autocomplete: 'off' });
    input.setAttribute('inputmode', property === 'month' ? 'numeric' : 'decimal');
    input.setAttribute('maxlength', '100');
    input.setAttribute('aria-describedby', `${inputId}-error`);
    input.dataset.property = property;
    const error = document.createElement('p');
    error.className = 'field-error';
    error.id = `${inputId}-error`;
    error.dataset.error = property;
    cell.append(label, input, error);
    row.append(cell);
  }
  const remove = document.createElement('button');
  remove.type = 'button';
  remove.className = 'secondary remove';
  remove.dataset.testid = 'remove-extra';
  remove.textContent = MESSAGES.extra.remove;
  row.append(remove);
  return row;
}

export function mountCalculator(root, client) {
  root.innerHTML = TEMPLATE;
  const form = root.querySelector('form');
  const button = form.querySelector('button[type="submit"]');
  const generalError = form.querySelector('[data-testid="general-error"]');
  const resultSection = root.querySelector('[data-testid="result"]');
  const resultList = resultSection.querySelector('ul.lines');
  const notesList = resultSection.querySelector('[data-testid="extra-notes"]');
  const extraRows = form.querySelector('[data-testid="extra-rows"]');
  const addButton = form.querySelector('[data-testid="add-extra"]');
  const inputs = Object.fromEntries(FIELDS.map((field) => [field, form.querySelector(`#${field}`)]));
  const fieldErrors = Object.fromEntries(FIELDS.map((field) => [field, form.querySelector(`#${field}-error`)]));
  let busy = false;
  // The form row each sent extra payment came from, by its index in the last request (04 §2).
  let sentRows = [];

  const rows = () => [...extraRows.querySelectorAll('[data-testid="extra-row"]')];
  const updateAddButton = () => { addButton.disabled = rows().length >= MAX_EXTRA_PAYMENTS; };

  addButton.addEventListener('click', () => {
    if (rows().length >= MAX_EXTRA_PAYMENTS) return;
    const row = createRow();
    row.querySelector('[data-testid="remove-extra"]').addEventListener('click', () => {
      row.remove();
      updateAddButton();
    });
    extraRows.append(row);
    updateAddButton();
    row.querySelector('input').focus();
  });

  function clear() {
    for (const field of FIELDS) {
      fieldErrors[field].textContent = '';
      inputs[field].removeAttribute('aria-invalid');
    }
    for (const row of rows()) {
      for (const error of row.querySelectorAll('[data-error]')) error.textContent = '';
      for (const input of row.querySelectorAll('input')) input.removeAttribute('aria-invalid');
    }
    generalError.textContent = '';
    resultList.replaceChildren();
    notesList.replaceChildren();
    resultSection.hidden = true;
  }

  const listItems = (texts) => texts.map((text) => {
    const item = document.createElement('li');
    item.textContent = text;
    return item;
  });

  function showResult(result) {
    const view = toResultView(result);
    resultList.replaceChildren(...listItems(view.lines.map((line) => `${line.label}: ${line.value}`)));
    notesList.replaceChildren(...listItems(view.notes));
    resultSection.hidden = false;
  }

  function showErrors(errors) {
    const rowOf = (index) => (sentRows[index] ? rows().indexOf(sentRows[index]) + 1 || undefined : undefined);
    const view = toErrorView(errors, rowOf);
    for (const { field, message } of view.errors) {
      fieldErrors[field].textContent = message;
      inputs[field].setAttribute('aria-invalid', 'true');
    }
    for (const { index, property, message } of view.itemErrors) {
      const row = sentRows[index];
      row.querySelector(`[data-error="${property}"]`).textContent = message;
      row.querySelector(`[data-property="${property}"]`).setAttribute('aria-invalid', 'true');
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

  /** The text exactly as typed; a row whose month and amount are both blank is not sent (04 §2). */
  function readExtraPayments() {
    const items = [];
    sentRows = [];
    for (const row of rows()) {
      const month = row.querySelector('[data-property="month"]').value;
      const amount = row.querySelector('[data-property="amount"]').value;
      if (month.trim() === '' && amount.trim() === '') continue;
      items.push({ month, amount });
      sentRows.push(row);
    }
    return items;
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
      raw.extraPayments = readExtraPayments();
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
