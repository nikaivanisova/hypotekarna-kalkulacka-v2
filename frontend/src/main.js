import './styles.css';
import { createApiClient } from './api-client.js';
import { mountCalculator } from './page.js';

// Same origin by default (contract `servers: /`); set VITE_API_BASE_URL to call another origin.
const client = createApiClient({ baseUrl: import.meta.env.VITE_API_BASE_URL ?? '' });
mountCalculator(document.getElementById('app'), client);
