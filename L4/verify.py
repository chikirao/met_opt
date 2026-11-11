"""Независимая проверка результатов через целочисленную модель дерева сценариев.

Это проверка, не основной алгоритм лабораторной. Нужен scipy.
Каждый узел имеет своё управление; одна история не знает будущих исходов.
"""

import json
from itertools import product

import numpy as np
from scipy.optimize import Bounds, LinearConstraint, milp
from scipy.sparse import lil_matrix

from portfolio import PortfolioModel
from read_data import BASE, read_data


def certificate(model, criterion):
    paths = [p for depth in range(3) for p in product(range(3), repeat=depth)]
    ids = {p: i for i, p in enumerate(paths)}
    # Для каждого узла: три покупки, три продажи, три остатка активов, деньги.
    n = 10*len(paths)+1
    rows, lower, upper = [], [], []

    def add(row, lo, hi):
        rows.append(row); lower.append(lo); upper.append(hi)

    for path, node in ids.items():
        t, off = len(path), 10*node
        for i in range(3):
            row = {off+6+i: 1, off+i: -model.lots[i]/1e6, off+3+i: model.lots[i]/1e6}
            rhs = model.initial.holdings[i]/1e6 if not path else 0
            if path:
                row[10*ids[path[:-1]]+6+i] = -model.rates[t-1,path[-1],i]/100
            add(row, rhs, rhs)
        row = {off+9: 1}
        for i in range(3):
            row[off+i] = (model.lots[i]+model.fees[i])/1e6
            row[off+3+i] = -(model.lots[i]-model.fees[i])/1e6
        rhs = model.initial.cash/1e6 if not path else 0
        if path:
            row[10*ids[path[:-1]]+9] = -1
        add(row, rhs, rhs)

    objective = np.zeros(n)
    lo = np.zeros(n); hi = np.full(n, np.inf)
    integrality = np.zeros(n)
    for path, node in ids.items():
        off = 10*node
        integrality[off:off+6] = 1
        lo[off+6:off+9] = model.required[len(path)]/1e6
        if len(path) == 2:
            p = np.prod([model.probabilities[t,j] for t,j in enumerate(path)])
            if criterion == "bayes":
                objective[off+6:off+9] = -p*(model.probabilities[-1] @ model.rates[-1]/100)
                objective[off+9] = -p
            else:
                for rate in model.rates[-1]:
                    row = {n-1: 1, off+9: -1}
                    row.update({off+6+i: -rate[i]/100 for i in range(3)})
                    add(row, -np.inf, 0)
    if criterion == "wald":
        objective[-1] = -1
    matrix = lil_matrix((len(rows), n))
    for j,row in enumerate(rows):
        for k,v in row.items(): matrix[j,k] = v
    result = milp(objective, integrality=integrality, bounds=Bounds(lo,hi),
                  constraints=LinearConstraint(matrix.tocsr(), lower, upper),
                  options={"mip_rel_gap": 1e-10, "time_limit": 120})
    if not result.success:
        raise RuntimeError(result.message)
    return -result.fun, result.mip_gap


def main():
    model = PortfolioModel(read_data())
    lines = ["Независимая целочисленная проверка на дереве сценариев"]
    for criterion in ["bayes", "wald"]:
        data = json.loads((BASE/f"results/{criterion}.json").read_text(encoding="utf-8"))
        value, gap = certificate(model, criterion)
        assert abs(value-data['value']) < 1e-5, (criterion,value,data['value'])
        leaves = data['leaves']
        reconstructed = (sum(r['wealth']*r['probability'] for r in leaves)
                         if criterion == "bayes" else min(r['wealth'] for r in leaves))
        assert abs(reconstructed-data['value']) < 1e-7
        assert abs(sum(r['probability'] for r in leaves)-1) < 1e-12
        lines.append(f"{criterion}: Беллман {data['value']:.9f}; MILP {value:.9f}; "
                     f"разность {abs(value-data['value']):.2g}; gap {gap:.2g}; 27 сценариев согласованы.")
    text="\n".join(lines)+"\n"
    (BASE/'results/verification.txt').write_text(text,encoding='utf-8',newline='\n')
    print(text)


if __name__ == '__main__':
    main()
