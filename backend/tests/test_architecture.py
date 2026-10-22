"""Architecture guard (docs/v1/02-architecture.md §4, ADR-7; tests 93–95), ported from legacy/cli.

Reads every import in mortgage/, checks it against an explicit allow-list per layer,
checks that the core layers perform no I/O, and checks the import graph for cycles.
Phase 4 (api/) and Phase 6 (persistence/) add their layers to these tables.
"""
import ast
from pathlib import Path

PACKAGE_DIR = Path(__file__).resolve().parents[1] / 'mortgage'

# Project modules each layer may import. `*` matches any module of that layer.
LAYER_IMPORTS: dict[str, list[str]] = {
    'domain': ['domain.types'],
    'input': ['domain.types'],
    'app': ['domain.*', 'input.*'],
}

# The only allowed imports inside one layer, besides domain.types.
INTRA_LAYER_IMPORTS: dict[str, list[str]] = {
    'input.validation': ['input.parsing'],
}

# Standard-library and third-party modules each layer may import. Nothing here does I/O.
LAYER_PACKAGES: dict[str, set[str]] = {
    'domain': {'__future__', 'dataclasses', 'decimal', 'typing'},
    'input': {'__future__', 'dataclasses', 'decimal', 're', 'typing'},
    'app': {'__future__', 'dataclasses', 'typing'},
}

# Built-in functions that do I/O; forbidden in every layer listed above.
IO_BUILTINS = {'open', 'print', 'input', 'exec', 'eval', '__import__'}


def module_id(path: Path) -> str:
    rel = path.relative_to(PACKAGE_DIR).with_suffix('')
    parts = [p for p in rel.parts if p != '__init__']
    return '.'.join(parts)


def source_modules() -> dict[str, ast.Module]:
    modules = {module_id(p): ast.parse(p.read_text(encoding='utf-8')) for p in sorted(PACKAGE_DIR.rglob('*.py'))}
    modules.pop('', None)  # a package-root __init__.py, if one is ever added
    return modules


def imports_of(mod_id: str, tree: ast.Module) -> list[str]:
    """Absolute names of every import; project modules lose their `mortgage.` prefix and keep a leading ':'."""
    names = []
    package = mod_id.split('.')[:-1] if '.' in mod_id else []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names += [alias.name for alias in node.names]
        elif isinstance(node, ast.ImportFrom):
            if node.level:
                base = package[:len(package) - node.level + 1]
                names.append('mortgage.' + '.'.join(base + ([node.module] if node.module else [])))
            else:
                names.append(node.module or '')
    return [':' + n.removeprefix('mortgage.') if n.startswith('mortgage.') or n == 'mortgage' else n for n in names]


def layer_of(mod_id: str) -> str:
    return mod_id.split('.')[0]


def allowed_project_import(source: str, target: str) -> bool:
    if target == 'domain.types' or target in INTRA_LAYER_IMPORTS.get(source, []):
        return True
    if layer_of(target) == layer_of(source):
        return False
    return any(pattern == target or (pattern.endswith('.*') and layer_of(target) == pattern[:-2])
               for pattern in LAYER_IMPORTS[layer_of(source)])


def test_architecture_dependency_direction():
    modules = source_modules()
    assert {layer_of(m) for m in modules if m} >= {'domain', 'input', 'app'}
    violations = []
    for mod_id, tree in modules.items():
        layer = layer_of(mod_id)
        if layer not in LAYER_IMPORTS:
            violations.append(f'{mod_id}: unknown layer')
            continue
        for name in imports_of(mod_id, tree):
            if name.startswith(':'):
                if not allowed_project_import(mod_id, name[1:]):
                    violations.append(f'{mod_id} → {name[1:]}')
            elif name.split('.')[0] not in LAYER_PACKAGES[layer]:
                violations.append(f'{mod_id} → package {name}')
    assert violations == []


def test_architecture_domain_has_no_io():
    violations = []
    for mod_id, tree in source_modules().items():
        for node in ast.walk(tree):
            if isinstance(node, ast.Name) and node.id in IO_BUILTINS:
                violations.append(f'{mod_id}: {node.id}')
    assert violations == []


def test_architecture_no_circular_dependencies():
    modules = source_modules()
    graph = {m: {n[1:] for n in imports_of(m, t) if n.startswith(':') and n[1:] in modules and n[1:] != m}
             for m, t in modules.items()}
    visiting, done, cycles = set(), set(), []

    def visit(node: str, path: list[str]) -> None:
        if node in done:
            return
        if node in visiting:
            cycles.append(' → '.join(path[path.index(node):] + [node]))
            return
        visiting.add(node)
        for target in sorted(graph[node]):
            visit(target, path + [node])
        visiting.discard(node)
        done.add(node)

    for module in sorted(graph):
        visit(module, [])
    assert cycles == []
