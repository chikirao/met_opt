"""Вариант 12: f = x**2 + y**2, 2*x + y = 10.

Запуск: python main.py
Программа печатает систему Лагранжа, все действительные корни и проверки.
Рисунок сохраняется в img/variant12.png.
"""

from pathlib import Path

import sympy as sp

from lagrange import solve

x, y = sp.symbols("x y", real=True)
f = x**2 + y**2
constraints = [2*x + y - 10]
BASE = Path(__file__).resolve().parent


def along_line():
    """Подстановка y из ограничения: функция на всей допустимой прямой."""
    t = sp.Symbol("t", real=True)
    y_line = sp.solve(constraints[0], y)[0]
    phi = sp.expand(f.subs(y, y_line).subs(x, t))
    return t, y_line, phi


def plot(res):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np

    root = res["candidates"][0]
    sol = root["solution"]
    xs, ys = float(sol[x]), float(sol[y])
    value = float(root["value"])
    t, y_line, phi = along_line()
    grid = np.linspace(-6, 11, 450)  # сетка используется только для рисунка
    X, Y = np.meshgrid(grid, grid)
    fig, (ax, ax2) = plt.subplots(1, 2, figsize=(10, 4.5))
    contour = ax.contour(X, Y, X**2 + Y**2, levels=[5, value, 50, 100],
                         colors="#1f4d63", linewidths=1)
    ax.clabel(contour, fontsize=9)
    ax.plot(grid, sp.lambdify(x, y_line, "numpy")(grid), color="#b45309", label="2x + y = 10")
    ax.scatter([xs], [ys], color="#3f6212", s=80, marker="*", zorder=4,
               label=f"минимум ({xs:g}, {ys:g})")
    ax.set(xlim=(-6, 11), ylim=(-6, 11), xlabel="x", ylabel="y",
           title="Линии уровня и ограничение")
    ax.set_aspect("equal")
    ax.legend(fontsize=9, loc="lower left")
    ts = np.linspace(xs - 4, xs + 4, 400)
    ax2.plot(ts, sp.lambdify(t, phi, "numpy")(ts), color="#1f4d63")
    ax2.scatter([xs], [value], color="#3f6212", marker="*", s=80, zorder=4)
    ax2.annotate(f"({xs:g}, {value:g})", (xs, value), xytext=(10, 12), textcoords="offset points")
    ax2.set(xlabel="t = x", ylabel="f(t, 10 - 2t)", title="Функция на допустимой прямой")
    for a in (ax, ax2):
        a.grid(alpha=0.3)
    fig.tight_layout()
    (BASE / "img").mkdir(exist_ok=True)
    fig.savefig(BASE / "img/variant12.png", dpi=160)
    plt.close(fig)


def main():
    res = solve(f, constraints, (x, y))
    print("Вариант 12. Метод множителей Лагранжа")
    print(f"f(x, y) = {f}")
    for g in constraints:
        print(f"h(x, y) = {g} = 0")
    print("Область: x, y - любые действительные числа")
    print(f"Якобиан ограничения: {res['jacobian'].tolist()}")
    print(f"Ранг Якобиана: {res['jacobian'].rank()} (постоянный)")
    print(f"L = {res['L']}")
    print("\nСистема Лагранжа:")
    for v, eq in zip(res["unknowns"], res["equations"]):
        print(f"  dL/d{v} = {eq} = 0")

    A, b = sp.linear_eq_to_matrix(res["equations"], res["unknowns"])
    print(f"\nМатрица системы: {A.tolist()}")
    print(f"Правая часть: {list(b)}")
    print(f"Определитель: {A.det()} != 0, решение единственное")
    print(f"Действительных кандидатов: {len(res['candidates'])}")
    for i, row in enumerate(res["candidates"], 1):
        print(f"\nКандидат {i}:")
        for v in res["unknowns"]:
            print(f"  {v} = {row['solution'][v]}")
        print(f"  f = {row['value']}")
        print(f"  невязки ограничений: {row['constraints']}")
        print(f"  невязки стационарности: {row['stationarity']}")
        print(f"  ранг Якобиана в точке: {row['rank']}")

    t, y_line, phi = along_line()
    print("\nПроверка на допустимой прямой:")
    print(f"  y = {y_line}, x = t")
    print(f"  phi(t) = {phi}")
    print(f"  phi'(t) = {sp.diff(phi, t)}")
    print(f"  phi''(t) = {sp.diff(phi, t, 2)} > 0")
    for t0 in sp.solve(sp.diff(phi, t), t):
        value = sp.simplify(phi.subs(t, t0))
        gap = sp.factor(phi - value)
        print(f"  phi(t) - {value} = {gap}")
        print(f"  минимум: x = {t0}, y = {y_line.subs(x, t0)}, f = {value}")
    for end in (-sp.oo, sp.oo):
        print(f"  предел phi(t) при t -> {end}: {sp.limit(phi, t, end)}")
    print("  На прямой функция не ограничена сверху, максимума нет.")
    print(f"\nSymPy {sp.__version__}. Вычисления точные, без округлений.")
    plot(res)
    print("Рисунок: img/variant12.png")


if __name__ == "__main__":
    main()
