"""Проверки денежного баланса, ограничений и последнего слоя Беллмана."""

import unittest

import numpy as np

from portfolio import BellmanSolver, PortfolioModel, SCALE, State
from read_data import read_data


class PortfolioTests(unittest.TestCase):
    def setUp(self):
        self.model = PortfolioModel(read_data())

    def test_trade_and_market_balance(self):
        m = self.model
        state = m.rebalance(m.initial, (1,0,0))
        self.assertEqual(state, State((125*SCALE,800*SCALE,400*SCALE),574*SCALE))
        self.assertEqual(state.wealth,m.initial.wealth-SCALE)
        self.assertEqual(m.transition(0,state,2).wealth,1834*SCALE)

    def test_credit_and_minimum(self):
        actions = {tuple(v) for v in self.model.actions(0,self.model.initial)}
        self.assertIn((23,0,0),actions)
        self.assertNotIn((24,0,0),actions)
        self.assertNotIn((-3,0,0),actions)
        self.assertIn((-2,0,0),actions)

    def test_repair_needs_cash_and_cheapest_funding(self):
        solver=BellmanSolver(self.model)
        holdings=np.array([[30,171,100],[30,400,200]],dtype=np.int64)*SCALE
        cash=np.zeros(2,dtype=np.int64)
        fast=solver.final_values(holdings,cash)
        self.assertEqual(fast[0],-np.inf)
        self.assertAlmostEqual(fast[1],643.5)
        np.testing.assert_allclose(fast,solver.final_enumerate(holdings,cash),atol=1e-8,rtol=0)

    def test_last_layer_against_complete_enumeration(self):
        rng=np.random.default_rng(12)
        states=[]
        m=self.model
        root_actions=m.actions(0,m.initial)
        for idx in rng.choice(len(root_actions),12,replace=False):
            first=m.rebalance(m.initial,root_actions[idx])
            state=m.transition(0,first,int(rng.integers(3)))
            actions=m.actions(1,state)
            second=m.rebalance(state,actions[int(rng.integers(len(actions)))])
            states.append(m.transition(1,second,int(rng.integers(3))))
        hh=np.array([s.holdings for s in states])
        cc=np.array([s.cash for s in states])
        for criterion in ['bayes','wald']:
            solver=BellmanSolver(m,criterion)
            np.testing.assert_allclose(solver.final_values(hh,cc),solver.final_enumerate(hh,cc),atol=1e-8,rtol=0)


if __name__=='__main__':
    unittest.main()
