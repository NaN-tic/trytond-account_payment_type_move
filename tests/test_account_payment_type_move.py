#!/usr/bin/env python
# -*- coding: UTF-8 -*-
#This file is part of account_payment_type module for Tryton.
#The COPYRIGHT file at the top level of this repository contains
#the full copyright notices and license terms.

import sys
import os
DIR = os.path.abspath(os.path.normpath(os.path.join(__file__,
    '..', '..', '..', '..', '..', 'trytond')))
if os.path.isdir(DIR):
    sys.path.insert(0, os.path.dirname(DIR))

import datetime
from decimal import Decimal
import unittest
import doctest
import trytond.tests.test_tryton
from trytond.transaction import Transaction
from trytond.tests.test_tryton import test_view, test_depends
from trytond.tests.test_tryton import POOL, DB_NAME, USER, CONTEXT
from trytond.backend.sqlite.database import Database as SQLiteDatabase


class AccountPaymentTypeMoveTestCase(unittest.TestCase):
    '''
    Test AccountPaymentTypeMove module.
    '''

    def setUp(self):
        trytond.tests.test_tryton.install_module('account_payment_type_move')

    def test0005views(self):
        '''
        Test views.
        '''
        test_view('account_payment_type')

    def test0006depends(self):
        '''
        Test depends.
        '''
        test_depends()


def doctest_dropdb(test):
    '''
    Remove sqlite memory database
    '''
    database = SQLiteDatabase().connect()
    cursor = database.cursor(autocommit=True)
    try:
        database.drop(cursor, ':memory:')
        cursor.commit()
    finally:
        cursor.close()


def suite():
    suite = trytond.tests.test_tryton.suite()
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(
        AccountPaymentTypeMoveTestCase))
    suite.addTests(doctest.DocFileSuite(
            'scenario_payment_type_move.rst',
            setUp=doctest_dropdb, tearDown=doctest_dropdb, encoding='utf-8',
            optionflags=doctest.REPORT_ONLY_FIRST_FAILURE))
    return suite

if __name__ == '__main__':
    unittest.TextTestRunner(verbosity=2).run(suite())
