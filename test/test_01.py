'''test generic FSM transitions that they match the diagram'''

import dip.basis.fsm
import unittest


class MockModel(dip.basis.fsm.AbstractModel):
    def __init__(self):
        dip.basis.fsm.AbstractModel.__init__(self)
        self.cons = True
        self.delg = dip.basis.fsm.ProductStatus.ALL
        self.genq = dip.basis.fsm.AlertStatus.SECURED
        self.pani = None
        self.sani = None
        self.ware = True
        self.what_happened = []

    def _do_construction(self):
        self.what_happened.append('c')
        if isinstance(self.cons, TypeError):
            raise self.cons
        return self.cons

    def _do_delegation(self) -> dip.basis.fsm.ProductStatus:
        self.what_happened.append('d')
        if isinstance(self.delg, TypeError):
            raise self.delg
        return self.delg

    def _do_general_quarters(self) -> dip.basis.fsm.AlertStatus:
        self.what_happened.append('gq')
        if self.genq == dip.basis.fsm.AlertStatus.RETRY:
            self.delg = dip.basis.fsm.ProductStatus.ALL
        if isinstance(self.genq, TypeError):
            raise self.genq
        return self.genq

    def _do_panic(self):
        self.what_happened.append('p')
        if isinstance(self.pani, TypeError):
            raise self.pani

    def _do_sanitization(self):
        self.what_happened.append('s')
        if isinstance(self.sani, TypeError):
            raise self.sani

    def _do_warehouse(self) -> bool:
        self.what_happened.append('w')
        if isinstance(self.ware, TypeError):
            raise self.ware
        return self.ware


class TestModel(unittest.TestCase):
    def test_nominal(self):
        model = MockModel()
        dip.basis.fsm.build(model)
        model.do()
        self.assertEqual(['c', 'd', 'w', 's'], model.what_happened)

    def test_bad_construction(self):
        model = MockModel()
        model.cons = False
        dip.basis.fsm.build(model)
        model.do()
        self.assertEqual(['c', 'p', 's'], model.what_happened)
        model = MockModel()
        model.cons = TypeError('handle exceptions correctly')
        dip.basis.fsm.build(model)
        model.do()
        self.assertEqual(['c', 'p', 's'], model.what_happened)

    def test_bad_delegation(self):
        model = MockModel()
        model.delg = False
        dip.basis.fsm.build(model)
        model.do()
        self.assertEqual(['c', 'd', 'gq', 's'], model.what_happened)
        model = MockModel()
        model.delg = dip.basis.fsm.ProductStatus.SOME
        dip.basis.fsm.build(model)
        model.do()
        self.assertEqual(['c', 'd', 'gq', 's'], model.what_happened)
        model = MockModel()
        model.delg = dip.basis.fsm.ProductStatus.NONE
        dip.basis.fsm.build(model)
        model.do()
        self.assertEqual(['c', 'd', 'p', 's'], model.what_happened)
        model = MockModel()
        model.delg = TypeError('handle exceptions correctly')
        dip.basis.fsm.build(model)
        model.do()
        self.assertEqual(['c', 'd', 'gq', 's'], model.what_happened)

    def test_bad_gq(self):
        model = MockModel()
        model.delg = dip.basis.fsm.ProductStatus.SOME
        model.genq = dip.basis.fsm.AlertStatus.FOUNDERED
        dip.basis.fsm.build(model)
        model.do()
        self.assertEqual(['c', 'd', 'gq', 'p', 's'], model.what_happened)
        model = MockModel()
        model.delg = dip.basis.fsm.ProductStatus.SOME
        model.genq = dip.basis.fsm.AlertStatus.RECOVERED
        dip.basis.fsm.build(model)
        model.do()
        self.assertEqual(['c', 'd', 'gq', 'w', 's'], model.what_happened)
        model = MockModel()
        model.delg = dip.basis.fsm.ProductStatus.SOME
        model.genq = dip.basis.fsm.AlertStatus.RETRY
        dip.basis.fsm.build(model)
        model.do()
        self.assertEqual(['c', 'd', 'gq', 'd', 'w', 's'], model.what_happened)
        model = MockModel()
        model.delg = dip.basis.fsm.ProductStatus.SOME
        model.genq = dip.basis.fsm.AlertStatus.SECURED
        dip.basis.fsm.build(model)
        model.do()
        self.assertEqual(['c', 'd', 'gq', 's'], model.what_happened)

    def test_bad_panic(self):
        model = MockModel()
        model.cons = False
        dip.basis.fsm.build(model)
        model.do()
        self.assertEqual(['c', 'p', 's'], model.what_happened)
        model = MockModel()
        model.cons = False
        model.pani = False
        dip.basis.fsm.build(model)
        model.do()
        self.assertEqual(['c', 'p', 's'], model.what_happened)
        model = MockModel()
        model.cons = False
        model.pani = TypeError('panic error')
        dip.basis.fsm.build(model)
        model.do()
        self.assertEqual(['c', 'p', 's'], model.what_happened)
        model = MockModel()
        model.cons = TypeError('handle exceptions correctly')
        dip.basis.fsm.build(model)
        model.do()
        self.assertEqual(['c', 'p', 's'], model.what_happened)
        model = MockModel()
        model.cons = TypeError('handle exceptions correctly')
        model.pani = False
        dip.basis.fsm.build(model)
        model.do()
        self.assertEqual(['c', 'p', 's'], model.what_happened)
        model = MockModel()
        model.cons = TypeError('handle exceptions correctly')
        model.pani = TypeError('panic error')
        dip.basis.fsm.build(model)
        model.do()
        self.assertEqual(['c', 'p', 's'], model.what_happened)

    def test_bad_warehouse(self):
        model = MockModel()
        model.ware = False
        dip.basis.fsm.build(model)
        model.do()
        self.assertEqual(['c', 'd', 'w', 'p', 's'], model.what_happened)
        model = MockModel()
        model.ware = TypeError('handle exceptions correctly')
        dip.basis.fsm.build(model)
        model.do()
        self.assertEqual(['c', 'd', 'w', 'p', 's'], model.what_happened)

    def test_bad_sanitization(self):
        model = MockModel()
        model.sani = False
        dip.basis.fsm.build(model)
        model.do()
        self.assertEqual(['c', 'd', 'w', 's'], model.what_happened)
        model = MockModel()
        model.sani = TypeError('handle exceptions correctly')
        dip.basis.fsm.build(model)
        model.do()
        self.assertEqual(['c', 'd', 'w', 's'], model.what_happened)
