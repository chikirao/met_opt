"""Метод множителей Лагранжа для ограничений-равенств.

Производные и система строятся из исходных выражений SymPy.
Решения системы являются кандидатами. Характер экстремума проверяется отдельно.
"""

import sympy as sp


def solve(f, constraints, variables):
    """Возвращает функцию Лагранжа, систему и проверенные действительные корни."""
    m = len(constraints)
    multipliers = (sp.Symbol("lam", real=True),) if m == 1 else sp.symbols(f"lam1:{m + 1}", real=True)
    L = f + sum(lam * g for lam, g in zip(multipliers, constraints))
    derivatives = [sp.diff(L, v) for v in variables]
    equations = derivatives + [sp.diff(L, lam) for lam in multipliers]
    unknowns = tuple(variables) + multipliers
    jacobian = sp.Matrix(constraints).jacobian(variables)
    roots = sp.solve(equations, unknowns, dict=True)

    candidates = []
    for root in roots:
        if any(v not in root or root[v].free_symbols for v in unknowns):
            raise ValueError("получено семейство решений, требуется отдельное исследование")
        if any(root[v].is_real is False for v in unknowns):
            continue
        if any(root[v].is_real is not True for v in unknowns):
            raise ValueError("не удалось проверить действительность корня")
        residuals = [sp.simplify(eq.subs(root)) for eq in equations]
        if any(r != 0 for r in residuals):
            raise ValueError("найденный корень не прошёл подстановку в систему")
        candidates.append({
            "solution": root,
            "value": sp.simplify(f.subs(root)),
            "constraints": residuals[len(variables):],
            "stationarity": residuals[:len(variables)],
            "rank": jacobian.subs(root).rank(),
        })

    return {
        "L": L, "derivatives": derivatives, "equations": equations,
        "unknowns": unknowns, "jacobian": jacobian, "candidates": candidates,
    }
