"""Метод ломаных (метод Пиявского): глобальный минимум липшицевой функции на отрезке.

Запуск:
    python piyavsky.py "x + sin(3.14159*x)" -1 3 0.01
    python piyavsky.py "0.5*(x-2)**2 + sin(pi*x)" 0 4 1 --L 6

Схема шага (как на практике):
    верхние точки - где уже посчитали W(u);
    между соседними верхними u_лев, u_прав угол ломаной:
        x = (W_лев - W_прав) / (2L) + (u_лев + u_прав) / 2
        p = W_лев - L (x - u_лев)
    берём угол с наименьшим p (при ничьей - левый), считаем W(x),
    зазор delta = W(x) - p; стоп, когда delta < eps.
    Ответ - посчитанная точка с наименьшим W.
"""

import argparse
import re
import time

import numpy as np

# функции, которые можно писать в формуле
NAMES = {
    "sin": np.sin, "cos": np.cos, "tan": np.tan, "exp": np.exp, "log": np.log,
    "sqrt": np.sqrt, "abs": np.abs, "pi": np.pi, "e": np.e,
    "arctan": np.arctan, "sinh": np.sinh, "cosh": np.cosh, "tanh": np.tanh,
}


def parse(text):
    """Строка вида "f(x) = x + sin(3.14159*x)" -> функция f(x)."""
    expr = re.sub(r"^\s*\w+\s*\(\s*x\s*\)\s*=", "", text).strip()
    expr = expr.replace("^", "**")
    code = compile(expr, "<f>", "eval")
    for name in code.co_names:
        if name != "x" and name not in NAMES:
            raise ValueError(f"неизвестное имя в формуле: {name}")

    def f(x):
        return eval(code, {"__builtins__": {}}, {**NAMES, "x": x})

    f.text = expr
    return f


def estimate_L(f, a, b, n=10000, margin=1.2):
    """Оценка константы Липшица: max |dW/dx| по соседним точкам, с запасом.

    Сетка нужна только для L. Минимум по ней не ищется.
    """
    xs = np.linspace(a, b, n + 1)
    ys = f(xs)
    slope = np.max(np.abs(np.diff(ys)) / (xs[1] - xs[0]))
    return float(slope * margin), float(slope)


def corner(ul, wl, ur, wr, L):
    """Пересечение двух галочек между соседними верхними точками."""
    x = (wl - wr) / (2 * L) + (ul + ur) / 2
    p = wl - L * (x - ul)
    return x, p


def piyavsky(f, a, b, eps, L, max_iter=100000):
    """Возвращает словарь с ответом и историей проб."""
    t0 = time.perf_counter()
    pts = [(a, float(f(a))), (b, float(f(b)))]  # верхние точки, отсортированы по x
    history = []  # (номер, x, p, W, delta)

    k = 0
    while k < max_iter:
        # углы ломаной между соседними верхними
        best = None
        for i in range(len(pts) - 1):
            (ul, wl), (ur, wr) = pts[i], pts[i + 1]
            x, p = corner(ul, wl, ur, wr, L)
            if not (ul - 1e-12 <= x <= ur + 1e-12):
                raise ValueError("угол вышел за интервал: L слишком мало")
            # самый низкий угол; при ничьей остаётся левый (идём слева направо)
            if best is None or p < best[2] - 1e-12:
                best = (i, x, p)

        i, x, p = best
        w = float(f(x))
        delta = w - p
        k += 1
        history.append((k, x, p, w, delta))
        pts.insert(i + 1, (x, w))
        if delta < eps:
            break

    elapsed = time.perf_counter() - t0
    xb, wb = min(pts, key=lambda t: t[1])
    return {
        "x": xb, "W": wb, "iters": k, "evals": len(pts), "time": elapsed,
        "points": pts, "history": history, "L": L, "eps": eps, "a": a, "b": b,
        "last": history[-1],
    }


def saw(points, L, xs):
    """Ломаная (нижняя оценка): max по верхним точкам W(u) - L|x - u|."""
    lo = np.full_like(xs, -np.inf, dtype=float)
    for u, w in points:
        lo = np.maximum(lo, w - L * np.abs(xs - u))
    return lo


def plot(f, res, title, path, show=False):
    import matplotlib
    if not show:
        matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    a, b, L = res["a"], res["b"], res["L"]
    xs = np.linspace(a, b, 2000)  # только для рисунка
    us = np.array([u for u, _ in res["points"]])
    ws = np.array([w for _, w in res["points"]])

    fig, (ax, ax2) = plt.subplots(2, 1, figsize=(10, 7.5), height_ratios=[3, 1.2])
    ax.plot(xs, f(xs), color="#1f4d63", lw=2, label="W(x)")
    ax.plot(xs, saw(res["points"], L, xs), color="#b45309", lw=1, label="итоговая ломаная")
    ax.scatter(us, ws, s=14, color="#1c1916", zorder=3, label=f"пробы ({len(us)})")
    ax.scatter([res["x"]], [res["W"]], s=110, color="#3f6212", marker="*", zorder=4,
               label=f"минимум: x = {res['x']:.4f}, W = {res['W']:.4f}")
    ax.axvline(res["x"], color="#3f6212", lw=0.8, ls="--")
    lo = min(f(xs).min(), saw(res["points"], L, xs).min())
    hi = f(xs).max()
    ax.set_ylim(lo - 0.05 * (hi - lo), hi + 0.08 * (hi - lo))
    ax.set_title(title)
    ax.set_xlabel("x")
    ax.legend(loc="best", fontsize=9)
    ax.grid(alpha=0.3)

    hist = res["history"]
    ax2.semilogy([h[0] for h in hist], [max(h[4], 1e-12) for h in hist], color="#b45309", lw=1)
    ax2.axhline(res["eps"], color="#3f6212", ls="--", lw=1, label=f"eps = {res['eps']}")
    ax2.set_xlabel("итерация")
    ax2.set_ylabel("зазор delta")
    ax2.legend(fontsize=9)
    ax2.grid(alpha=0.3)

    fig.tight_layout()
    fig.savefig(path, dpi=130)
    if show:
        plt.show()
    plt.close(fig)


def report(f, res):
    k, x, p, w, d = res["last"]
    return "\n".join([
        f"W(x) = {f.text},  [{res['a']}, {res['b']}],  eps = {res['eps']},  L = {res['L']:.4g}",
        f"x* ~ {res['x']:.6f}",
        f"W(x*) ~ {res['W']:.6f}",
        f"итераций: {res['iters']}, вычислений W: {res['evals']}",
        f"время: {res['time'] * 1000:.2f} мс",
        f"последняя проба: x = {x:.6f}, W = {w:.6f}, p = {p:.6f}, delta = {d:.6f} < eps",
    ])


def main():
    ap = argparse.ArgumentParser(description="Метод ломаных (Пиявского)")
    ap.add_argument("func", help='функция одной переменной, например "x + sin(3.14159*x)"')
    ap.add_argument("a", type=float)
    ap.add_argument("b", type=float)
    ap.add_argument("eps", type=float)
    ap.add_argument("--L", type=float, help="константа Липшица (если не задана, оценивается)")
    ap.add_argument("--out", default="result.png", help="куда сохранить рисунок")
    ap.add_argument("--show", action="store_true", help="показать окно с графиком")
    args = ap.parse_args()

    f = parse(args.func)
    if args.L is None:
        L, slope = estimate_L(f, args.a, args.b)
        print(f"L не задана: max |dW/dx| ~ {slope:.4f}, берём L = {L:.4f} (запас 20%)")
    else:
        L = args.L
    res = piyavsky(f, args.a, args.b, args.eps, L)
    print(report(f, res))
    plot(f, res, f"W(x) = {f.text}", args.out, args.show)
    print(f"рисунок: {args.out}")


if __name__ == "__main__":
    main()
