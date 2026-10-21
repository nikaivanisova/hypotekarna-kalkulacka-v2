/**
 * M9 — main (02-architecture.md §3, M9).
 *
 * Composition root: wires the Node.js terminal to the CLI adapter.
 */
import { createNodeTerminalIo, runCli } from './ui/cli.js';

const io = createNodeTerminalIo(process.stdin, process.stdout);
// exitCode instead of process.exit(): the process ends once stdout has flushed.
process.exitCode = await runCli(io);
