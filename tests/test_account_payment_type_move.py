# This file is part of the account_payment_type_move module for Tryton.
# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
import unittest
import trytond.tests.test_tryton
from trytond.tests.test_tryton import ModuleTestCase


class AccountPaymentTypeMoveTestCase(ModuleTestCase):
    'Test Account Payment Type Move module'
    module = 'account_payment_type_move'


def suite():
    suite = trytond.tests.test_tryton.suite()
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(
        AccountPaymentTypeMoveTestCase))
    return suite