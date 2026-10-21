/**
 * Architecture guard (02-architecture.md §4, ADR-7; tests 93–95 in 03-test-scenarios.md).
 *
 * Reads every import in src/, checks it against an explicit allow-list per layer,
 * checks that domain/ performs no I/O, and checks the import graph for cycles.
 */
import { readdirSync, readFileSync } from 'node:fs';
import { builtinModules } from 'node:module';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { describe, expect, it } from 'vitest';

const SRC_DIR = fileURLToPath(new URL('../src/', import.meta.url));

type Layer = 'domain' | 'input' | 'output' | 'app' | 'ui' | 'main';

/** Project modules each layer may import (02 §4 rules 1–3, 5). `*` matches any module of that layer. */
const LAYER_IMPORTS: Readonly<Record<Layer, readonly string[]>> = {
  domain: ['domain/types'],
  input: ['domain/types'],
  output: ['domain/types'],
  app: ['domain/*', 'input/*', 'output/*'],
  ui: ['app/*', 'domain/types'],
  main: ['ui/*'],
};

/** The only allowed imports inside one layer, besides domain/types (02 §4 rule 6). */
const INTRA_LAYER_IMPORTS: Readonly<Record<string, readonly string[]>> = {
  'input/validation': ['input/parsing'],
  'output/presentation': ['output/formatting'],
};

/** External packages each layer may import. Node built-ins are handled separately (rule 4). */
const LAYER_PACKAGES: Readonly<Record<Layer, readonly string[]>> = {
  domain: ['decimal.js'],
  input: ['decimal.js'],
  output: ['decimal.js'],
  app: ['decimal.js'],
  ui: [],
  main: [],
};

/** Only ui/ and main may touch I/O (rule 4). */
const IO_LAYERS: readonly Layer[] = ['ui', 'main'];

const NODE_BUILTINS = new Set(builtinModules);

interface SourceFile {
  readonly id: string; // e.g. "domain/types", "main"
  readonly code: string; // comments stripped
}

function listSourceFiles(): SourceFile[] {
  return readdirSync(SRC_DIR, { recursive: true, encoding: 'utf8' })
    .filter((rel) => rel.endsWith('.ts'))
    .map((rel) => ({
      id: rel.replace(/\\/g, '/').replace(/\.ts$/, ''),
      code: stripComments(readFileSync(path.join(SRC_DIR, rel), 'utf8')),
    }))
    .sort((a, b) => a.id.localeCompare(b.id));
}

function stripComments(code: string): string {
  return code.replace(/\/\*[\s\S]*?\*\//g, '').replace(/(^|[^:'"`])\/\/.*$/gm, '$1');
}

/** Every module specifier in static imports/exports, dynamic import() and require(). */
function importSpecifiers(code: string): string[] {
  const patterns = [
    /\b(?:import|export)\s+(?:type\s+)?(?:[\w*{}\s,$]+?\s+from\s+)?['"]([^'"]+)['"]/g,
    /\bimport\s*\(\s*['"]([^'"]+)['"]\s*\)/g,
    /\brequire\s*\(\s*['"]([^'"]+)['"]\s*\)/g,
  ];
  return patterns.flatMap((re) => [...code.matchAll(re)].map((m) => m[1] ?? ''));
}

function layerOf(moduleId: string): Layer {
  if (moduleId === 'main') return 'main';
  const layer = moduleId.split('/')[0];
  if (layer === 'domain' || layer === 'input' || layer === 'output' || layer === 'app' || layer === 'ui') {
    return layer;
  }
  throw new Error(`Module "${moduleId}" is not in a known layer (02 §2).`);
}

type Target =
  | { readonly kind: 'project'; readonly id: string }
  | { readonly kind: 'node'; readonly name: string }
  | { readonly kind: 'package'; readonly name: string }
  | { readonly kind: 'outside'; readonly path: string };

function resolveTarget(fromId: string, specifier: string): Target {
  if (specifier.startsWith('.')) {
    const joined = path.posix.normalize(path.posix.join(path.posix.dirname(fromId), specifier));
    if (joined.startsWith('..')) return { kind: 'outside', path: joined };
    return { kind: 'project', id: joined.replace(/\.(js|ts)$/, '') };
  }
  if (specifier.startsWith('node:') || NODE_BUILTINS.has(specifier)) return { kind: 'node', name: specifier };
  const parts = specifier.split('/');
  const name = specifier.startsWith('@') ? parts.slice(0, 2).join('/') : (parts[0] ?? specifier);
  return { kind: 'package', name };
}

function matches(pattern: string, moduleId: string): boolean {
  return pattern.endsWith('/*') ? moduleId.startsWith(pattern.slice(0, -1)) : pattern === moduleId;
}

/** Returns a description of the broken rule, or null if the import is allowed. */
function importViolation(fromId: string, specifier: string): string | null {
  const layer = layerOf(fromId);
  const target = resolveTarget(fromId, specifier);
  const edge = `${fromId} → ${specifier}`;
  switch (target.kind) {
    case 'outside':
      return `${edge}: imports a file outside src/`;
    case 'node':
      return IO_LAYERS.includes(layer) ? null : `${edge}: only ui/ and main may import Node built-ins (rule 4)`;
    case 'package':
      return LAYER_PACKAGES[layer].includes(target.name)
        ? null
        : `${edge}: package "${target.name}" is not allowed in ${layer}/`;
    case 'project': {
      if (target.id === fromId) return `${edge}: imports itself`;
      if (INTRA_LAYER_IMPORTS[fromId]?.includes(target.id)) return null;
      if (LAYER_IMPORTS[layer].some((p) => matches(p, target.id))) return null;
      return `${edge}: ${layer}/ may not import ${target.id} (rules 1–3, 5, 6)`;
    }
  }
}

/** Uses of process / console, the I/O globals that rule 4 reserves for ui/ and main. */
function ioGlobalUses(code: string): string[] {
  return [...code.matchAll(/\b(process|console)\s*[.[]/g)].map((m) => m[1] ?? '');
}

/** Returns one cycle as a list of module ids (first = last), or null if the graph is acyclic. */
function findCycle(graph: ReadonlyMap<string, readonly string[]>): string[] | null {
  const state = new Map<string, 'visiting' | 'done'>();
  const stack: string[] = [];
  const visit = (node: string): string[] | null => {
    if (state.get(node) === 'done') return null;
    if (state.get(node) === 'visiting') return [...stack.slice(stack.indexOf(node)), node];
    state.set(node, 'visiting');
    stack.push(node);
    for (const next of graph.get(node) ?? []) {
      const cycle = visit(next);
      if (cycle) return cycle;
    }
    stack.pop();
    state.set(node, 'done');
    return null;
  };
  for (const node of graph.keys()) {
    const cycle = visit(node);
    if (cycle) return cycle;
  }
  return null;
}

function projectImportGraph(files: readonly SourceFile[]): Map<string, string[]> {
  const graph = new Map<string, string[]>();
  for (const file of files) {
    const targets = importSpecifiers(file.code)
      .map((s) => resolveTarget(file.id, s))
      .flatMap((t) => (t.kind === 'project' ? [t.id] : []));
    graph.set(file.id, targets);
  }
  return graph;
}

describe('architecture', () => {
  const files = listSourceFiles();

  it('test_architecture_dependency_direction', () => {
    // The checker itself must reject known-bad edges and accept the allowed ones.
    expect(importViolation('domain/types', '../ui/cli.js')).not.toBeNull();
    expect(importViolation('ui/cli', '../domain/calculation.js')).not.toBeNull();
    expect(importViolation('input/parsing', '../output/formatting.js')).not.toBeNull();
    expect(importViolation('input/parsing', './validation.js')).not.toBeNull();
    expect(importViolation('app/calculator', 'node:fs')).not.toBeNull();
    expect(importViolation('input/validation', './parsing.js')).toBeNull();
    expect(importViolation('output/presentation', './formatting.js')).toBeNull();
    expect(importViolation('app/calculator', '../domain/calculation.js')).toBeNull();
    expect(importViolation('ui/cli', 'node:readline')).toBeNull();
    expect(importViolation('main', './ui/cli.js')).toBeNull();

    expect(files.map((f) => f.id)).toContain('domain/types');
    const violations = files.flatMap((file) => [
      ...importSpecifiers(file.code)
        .map((s) => importViolation(file.id, s))
        .filter((v): v is string => v !== null),
      ...(IO_LAYERS.includes(layerOf(file.id))
        ? []
        : ioGlobalUses(file.code).map((g) => `${file.id}: uses ${g} (rule 4)`)),
    ]);
    expect(violations).toEqual([]);
  });

  it('test_architecture_domain_has_no_io', () => {
    const domainFiles = files.filter((f) => layerOf(f.id) === 'domain');
    expect(domainFiles.length).toBeGreaterThan(0);
    expect(ioGlobalUses('const x = 1; console.log(x);')).toEqual(['console']);

    for (const file of domainFiles) {
      for (const specifier of importSpecifiers(file.code)) {
        const target = resolveTarget(file.id, specifier);
        const ok =
          (target.kind === 'package' && target.name === 'decimal.js') ||
          (target.kind === 'project' && target.id === 'domain/types' && file.id !== 'domain/types');
        expect(ok, `${file.id} imports "${specifier}"`).toBe(true);
      }
      expect(ioGlobalUses(file.code), `${file.id} uses I/O globals`).toEqual([]);
    }
  });

  it('test_architecture_no_circular_dependencies', () => {
    expect(findCycle(new Map([['a', ['b']], ['b', ['c']], ['c', ['a']]]))).toEqual(['a', 'b', 'c', 'a']);
    expect(findCycle(new Map([['a', ['b']], ['b', []]]))).toBeNull();

    expect(findCycle(projectImportGraph(files))).toBeNull();
  });
});
