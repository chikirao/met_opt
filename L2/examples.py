"""Демонстрация метода ломаных на тестовых функциях.

Результаты печатаются в консоль (сохранены в output.txt), рисунки в img/.
"""

import os

import numpy as np

from piyavsky import estimate_L, parse, piyavsky, plot, report, saw

EXAMPLES = [
    # (имя файла, заголовок, формула, a, b, eps, L или None)
    ("practice", "Пример с практики",
     "0.5*(x-2)**2 + sin(pi*x)", 0, 4, 1, 6),
    ("rastrigin", "Функция Растригина (одномерная)",
     "x**2 - 10*cos(2*pi*x) + 10", -1.3, 2.7, 0.01, None),
    ("ackley", "Функция Экли (одномерная)",
     "-20*exp(-0.2*abs(x)) - exp(cos(2*pi*x)) + e + 20", -3, 4, 0.01, None),
    ("task", "Функция из задания",
     "x + sin(3.14159*x)", -1, 3, 0.01, None),
]


def steps_figure(f, a, b, L, path, n=4):
    """Первые n шагов метода на одном рисунке: как растёт ломаная."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    res = piyavsky(f, a, b, 0, L, max_iter=n)
    xs = np.linspace(a, b, 1000)
    fig, axes = plt.subplots(2, 2, figsize=(10, 6.5), sharex=True, sharey=True)
    pts = [(a, float(f(a))), (b, float(f(b)))]
    for k, ax in enumerate(axes.flat):
        hk = res["history"][k]
        ax.plot(xs, f(xs), color="#1f4d63", lw=2)
        ax.plot(xs, saw(pts, L, xs), color="#b45309", lw=1.2)
        ax.scatter([u for u, _ in pts], [w for _, w in pts], color="#1c1916", s=22, zorder=3)
        ax.scatter([hk[1]], [hk[2]], color="#b45309", s=40, zorder=4)
        ax.vlines(hk[1], hk[2], hk[3], color="#b45309", ls="--", lw=1)
        ax.scatter([hk[1]], [hk[3]], color="#3f6212", s=40, zorder=4)
        w = round(hk[3], 2) + 0.0  # убираем "-0.00"
        ax.set_title(f"шаг {k + 1}: x = {hk[1]:.3f}, p = {hk[2]:.2f}, W = {w:.2f}", fontsize=10)
        ax.grid(alpha=0.3)
        pts.append((hk[1], hk[3]))
        pts.sort()
    fig.suptitle("Первые шаги: чёрные - посчитанные точки, оранжевое - ломаная и её нижний угол, "
                 "зелёное - новая проба", fontsize=10)
    fig.tight_layout()
    fig.savefig(path, dpi=130)
    plt.close(fig)


def main():
    os.makedirs("img", exist_ok=True)
    for name, title, expr, a, b, eps, L in EXAMPLES:
        f = parse(expr)
        print(f"== {title} ==")
        if L is None:
            L, slope = estimate_L(f, a, b)
            print(f"max |dW/dx| ~ {slope:.4f}, берём L = {L:.4f} (запас 20%)")
        else:
            print(f"L = {L} задана (как на практике)")
        res = piyavsky(f, a, b, eps, L)
        print(report(f, res))
        plot(f, res, f"{title}: W(x) = {expr}", f"img/{name}.png")
        print()
    f = parse(EXAMPLES[0][2])
    steps_figure(f, 0, 4, 6, "img/steps.png")


if __name__ == "__main__":
    main()
