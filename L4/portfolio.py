"""Трёхэтапное управление портфелем методом Беллмана.

Суммы хранятся целыми числами в миллионных долях д.е.
Пакеты заданы в денежных суммах, а не в количестве акций.
"""

from dataclasses import dataclass
from enum import Enum
from itertools import product

import numpy as np

SCALE = 1_000_000


class Criterion(str, Enum):
    BAYES = "bayes"
    WALD = "wald"

    def combine(self, values, probabilities):
        if self == Criterion.WALD:
            return np.min(values, axis=0)
        # Недопустимость хотя бы одной ветви исключает управление.
        return np.sum(values * np.asarray(probabilities)[:, None], axis=0)


@dataclass(frozen=True)
class State:
    holdings: tuple
    cash: int

    @property
    def wealth(self):
        return sum(self.holdings) + self.cash


@dataclass
class Decision:
    value: float
    trade: tuple


@dataclass
class SolveResult:
    criterion: str
    value: float
    policy: list
    leaves: list
    stats: dict


class PortfolioModel:
    def __init__(self, data):
        self.data = data
        self.lots = np.array(data["lots"], dtype=np.int64) * SCALE
        self.minimum = np.array(data["minimum"], dtype=np.int64) * SCALE
        self.fees = self.lots * np.array(data["commission_percent"], dtype=np.int64) // 100
        self.rates = np.array(data["rates_percent"], dtype=np.int64)
        self.probabilities = np.array(data["probabilities"], dtype=float)
        self.horizon = len(self.rates)
        self.initial = State(tuple(v*SCALE for v in data["initial_holdings"]), data["cash"]*SCALE)
        # Минимумы должны соблюдаться и после любого рыночного исхода.
        worst = self.rates.min(axis=1)
        self.required = np.maximum(self.minimum, (100*self.minimum + worst - 1)//worst)
        assert np.allclose(self.probabilities.sum(axis=1), 1)

    def cost(self, trades):
        return np.sum(trades*self.lots + np.abs(trades)*self.fees, axis=-1)

    def actions(self, stage, state):
        """Все допустимые изменения в целых пакетах, в лексикографическом порядке."""
        h = np.array(state.holdings, dtype=np.int64)
        low = -np.floor_divide(h-self.required[stage], self.lots)
        low_cost = low*self.lots + np.abs(low)*self.fees
        ranges = []
        for i in range(3):
            budget = state.cash - (low_cost.sum()-low_cost[i])
            if budget >= 0:
                high = budget // (self.lots[i]+self.fees[i])
            else:
                high = budget // (self.lots[i]-self.fees[i])
            if high < low[i]:
                return np.empty((0, 3), dtype=np.int64)
            ranges.append(np.arange(low[i], high+1, dtype=np.int64))
        trades = np.stack(np.meshgrid(*ranges, indexing="ij"), axis=-1).reshape(-1, 3)
        return trades[self.cost(trades) <= state.cash]

    def rebalance(self, state, trade):
        k = np.array(trade, dtype=np.int64)
        return State(tuple(np.array(state.holdings)+k*self.lots), int(state.cash-self.cost(k)))

    def transition(self, stage, state, outcome):
        h = np.array(state.holdings)*self.rates[stage, outcome]
        if np.any(h % 100):
            raise ValueError("недостаточный масштаб целых сумм")
        return State(tuple(h//100), state.cash)


class BellmanSolver:
    def __init__(self, model, criterion=Criterion.BAYES):
        self.model = model
        self.criterion = Criterion(criterion)
        self.cache = {}
        self.stats = {"states": 0, "actions": 0, "last_states": 0, "last_fallback": 0}

    def final_values(self, holdings, cash):
        """Последний слой Беллмана для массива состояний.

        Если покупать сверх минимума невыгодно, минимум/ноль/продажа до границы
        дают точный максимум. Недостающие деньги можно получить продажей пакета.
        В остальных случаях используется полный перебор последнего слоя.
        """
        m = self.model
        self.stats["last_states"] += len(cash)
        rates = m.rates[-1]/100
        if self.criterion == Criterion.BAYES:
            factors = m.probabilities[-1] @ rates
        else:
            # Все активы одновременно имеют худший исход в одной строке.
            if not np.any(np.all(m.rates[-1] == m.rates[-1].min(axis=0), axis=1)):
                return self.final_enumerate(holdings, cash)
            factors = rates.min(axis=0)
        buy = 1 + m.fees/m.lots
        sell = 1 - m.fees/m.lots
        if np.any(factors > buy + 1e-12):
            return self.final_enumerate(holdings, cash)
        low = -np.floor_divide(holdings-m.required[-1], m.lots)
        trade = np.where(factors < sell-1e-12, low, np.maximum(low, 0))
        after_cash = cash-m.cost(trade)
        after_h = holdings+trade*m.lots
        values = (after_cash + after_h @ factors)/SCALE
        deficit = -after_cash
        need = deficit > 0
        # Когда любой один пакет покрывает дефицит, достаточно выбрать самую
        # дешёвую по потерянному результату допустимую продажу.
        small = need & (deficit <= np.min(m.lots-m.fees))
        if np.any(small):
            losses = m.lots*factors-(m.lots-m.fees)
            eligible = trade[small] > low[small]
            best_loss = np.min(np.where(eligible, losses, np.inf), axis=1)
            values[small] -= best_loss/SCALE
        other = need & ~small
        if np.any(other):
            values[other] = self.final_enumerate(holdings[other], cash[other])
        return values

    def final_enumerate(self, holdings, cash):
        """Общий точный расчёт последнего слоя без сокращения вариантов."""
        m = self.model
        out = np.full(len(cash), -np.inf)
        for j, (h, c) in enumerate(zip(holdings, cash)):
            self.stats["last_fallback"] += 1
            state = State(tuple(h), int(c))
            trades = m.actions(m.horizon-1, state)
            if not len(trades):
                continue
            hh = h+trades*m.lots
            cc = c-m.cost(trades)
            branch = np.array([(cc + (hh*r//100).sum(axis=1))/SCALE for r in m.rates[-1]])
            out[j] = np.max(self.criterion.combine(branch, m.probabilities[-1]))
        return out

    def decide(self, stage, state):
        key = (stage, state)
        if key in self.cache:
            return self.cache[key]
        self.stats["states"] += 1
        m = self.model
        trades = m.actions(stage, state)
        self.stats["actions"] += len(trades)
        if not len(trades):
            return Decision(-np.inf, ())
        hh = np.array(state.holdings)+trades*m.lots
        cc = state.cash-m.cost(trades)
        if stage == m.horizon-1:
            branch = np.array([(cc+(hh*r//100).sum(axis=1))/SCALE for r in m.rates[stage]])
        elif stage == m.horizon-2:
            branch = np.array([self.final_values(hh*r//100, cc) for r in m.rates[stage]])
        else:
            branch = np.empty((3, len(trades)))
            for outcome, rate in enumerate(m.rates[stage]):
                for j, h in enumerate(hh*rate//100):
                    branch[outcome, j] = self.decide(stage+1, State(tuple(h), int(cc[j]))).value
        values = self.criterion.combine(branch, m.probabilities[stage])
        j = int(np.argmax(values))
        decision = Decision(float(values[j]), tuple(int(v) for v in trades[j]))
        self.cache[key] = decision
        return decision

    def solve(self):
        m = self.model
        first = self.decide(0, m.initial)
        if not np.isfinite(first.value):
            raise ValueError("нет стратегии, допустимой при всех исходах")
        policy, leaves = [], []

        def forward(stage, state, path, probability):
            if stage == m.horizon:
                leaves.append({"path": path, "probability": probability,
                               "wealth": state.wealth/SCALE, "profit": (state.wealth-m.initial.wealth)/SCALE})
                return
            d = self.decide(stage, state)
            after = m.rebalance(state, d.trade)
            assert after.cash >= 0
            assert np.all(np.array(after.holdings) >= m.required[stage])
            policy.append({"stage": stage+1, "path": path, "value": d.value,
                           "before": [int(v)/SCALE for v in (*state.holdings, state.cash)],
                           "trade": list(d.trade),
                           "fee": int(np.dot(np.abs(d.trade), m.fees))/SCALE,
                           "after": [int(v)/SCALE for v in (*after.holdings, after.cash)]})
            for outcome in range(3):
                nxt = m.transition(stage, after, outcome)
                assert np.all(np.array(nxt.holdings) >= m.minimum)
                forward(stage+1, nxt, path+[outcome], probability*m.probabilities[stage, outcome])

        forward(0, m.initial, [], 1.)
        return SolveResult(self.criterion.value, first.value, policy, leaves, self.stats.copy())
