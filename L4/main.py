"""Запуск расчёта: python main.py --criterion all.

bayes: максимальный ожидаемый итог; wald: максимальный худший итог.
Результаты каждого критерия сохраняются отдельно, программа печатает весь план.
"""

import argparse
import csv
import json
import time
from dataclasses import asdict
from itertools import product
from pathlib import Path

from portfolio import BellmanSolver, Criterion, PortfolioModel, SCALE
from read_data import BASE, read_data

NAMES = ["Б", "Н", "О"]


def path_text(path):
    return "".join(NAMES[i] for i in path) or "начало"


def baseline(model):
    leaves = []
    for path in product(range(3), repeat=model.horizon):
        state, p = model.initial, 1.
        for t, j in enumerate(path):
            state = model.transition(t, state, j)
            p *= model.probabilities[t, j]
        leaves.append((state.wealth/SCALE, p))
    return {"expected": float(sum(w*p for w, p in leaves)), "worst": float(min(w for w, p in leaves))}


def save(result, elapsed, model):
    folder = BASE / "results"
    folder.mkdir(exist_ok=True)
    data = asdict(result)
    data["time"] = elapsed
    data["initial_wealth"] = model.initial.wealth/SCALE
    data["profit"] = result.value-data["initial_wealth"]
    data["expected_wealth"] = sum(l["wealth"]*l["probability"] for l in result.leaves)
    data["worst_wealth"] = min(l["wealth"] for l in result.leaves)
    data["best_wealth"] = max(l["wealth"] for l in result.leaves)
    (folder / f"{result.criterion}.json").write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")
    for name, rows in [("policy", result.policy), ("scenarios", result.leaves)]:
        with (folder / f"{result.criterion}_{name}.csv").open("w", encoding="utf-8-sig", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=list(rows[0]))
            writer.writeheader()
            for row in rows:
                row = dict(row)
                row["path"] = path_text(row["path"])
                writer.writerow(row)
    return data


def describe(data):
    lines = [f"== {data['criterion']} ==",
             f"Критерий по конечному капиталу: {data['value']:.9f} д.е.",
             f"Доход по выбранному критерию: {data['profit']:.9f} д.е.",
             f"Ожидаемый капитал: {data['expected_wealth']:.9f}; худший: {data['worst_wealth']:.9f}",
             f"Время: {data['time']:.3f} с", "План: k = (ЦБ1, ЦБ2, депозит), суммы после сделки включают свободные деньги."]
    for row in data["policy"]:
        money = ", ".join(f"{v:.6f}".rstrip('0').rstrip('.') for v in row["after"])
        lines.append(f"  этап {row['stage']}, история {path_text(row['path'])}: k={row['trade']}, "
                     f"комиссия {row['fee']:.2f}, после ({money})")
    lines.append(f"Проверено {len(data['leaves'])} конечных сценариев; статистика: {data['stats']}")
    return "\n".join(lines)


def plot_results(results):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(10, 4.5))
    colors = {"bayes": "#1f4d63", "wald": "#b45309"}
    labels = {"bayes": "Байес: ожидаемый доход", "wald": "Вальд: худший доход"}
    for data in results:
        ax.plot(range(1, 28), [r['profit'] for r in data['leaves']], marker="o", ms=3,
                color=colors[data['criterion']], label=labels[data['criterion']])
    ax.axhline(0, color="#555", linewidth=.8)
    ax.set(xlabel="Номер сценария (порядок Б, Н, О; всего 27)", ylabel="Доход за три этапа, д.е.")
    ax.legend()
    ax.grid(alpha=.25)
    fig.tight_layout()
    (BASE / "img").mkdir(exist_ok=True)
    fig.savefig(BASE / "img/scenarios.png", dpi=160)
    plt.close(fig)


def main():
    ap = argparse.ArgumentParser(description="Управление портфелем методом Беллмана")
    ap.add_argument("--criterion", choices=["bayes", "wald", "all"], default="all")
    args = ap.parse_args()
    source = read_data()
    model = PortfolioModel(source)
    lines = ["Лабораторная работа 4. Динамическое программирование",
             f"Исходный капитал: {model.initial.wealth/SCALE:g} д.е.",
             f"Пакеты: {source['lots']}; комиссии, %: {source['commission_percent']}",
             f"Минимумы: {source['minimum']}; неотрицательный остаток денег.",
             "Границы контролируются после сделки и после каждого исхода рынка.",
             "Цена сделки равна фиксированной сумме пакета; конечные активы оцениваются без продажи."]
    results = []
    for criterion in (["bayes", "wald"] if args.criterion == "all" else [args.criterion]):
        start = time.perf_counter()
        result = BellmanSolver(model, Criterion(criterion)).solve()
        data = save(result, time.perf_counter()-start, model)
        results.append(data)
        lines.append(describe(data))
    lines.append(f"Без сделок: {baseline(model)}")
    text = "\n\n".join(lines)+"\n"
    (BASE / "output.txt").write_text(text, encoding="utf-8", newline="\n")
    print(text)
    plot_results(results)


if __name__ == "__main__":
    main()
