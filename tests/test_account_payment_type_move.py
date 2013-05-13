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
import trytond.tests.test_tryton
from trytond.transaction import Transaction
from trytond.tests.test_tryton import test_view, test_depends
from trytond.tests.test_tryton import POOL, DB_NAME, USER, CONTEXT


class AccountPaymentTypeMoveTestCase(unittest.TestCase):
    '''
    Test AccountPaymentTypeMove module.
    '''

    def setUp(self):
        trytond.tests.test_tryton.install_module('account_payment_type_move')
        self.account_template = POOL.get('account.account.template')
        self.tax_code_template = POOL.get('account.tax.code.template')
        self.tax_template = POOL.get('account.tax.code.template')
        self.account = POOL.get('account.account')
        self.account_create_chart = POOL.get(
            'account.create_chart', type='wizard')
        self.company = POOL.get('company.company')
        self.currency = POOL.get('currency.currency')
        self.user = POOL.get('res.user')
        self.fiscalyear = POOL.get('account.fiscalyear')
        self.sequence = POOL.get('ir.sequence')
        self.sequence_strict = POOL.get('ir.sequence.strict')
        self.move = POOL.get('account.move')
        self.move_line = POOL.get('account.move.line')
        self.payment_type = POOL.get('account.payment.type')
        self.payment_term = POOL.get('account.invoice.payment_term')
        self.journal = POOL.get('account.journal')
        self.account_type = POOL.get('account.account.type')
        self.invoice = POOL.get('account.invoice')
        self.party = POOL.get('party.party')
        self.reconciliation = POOL.get('account.move.reconciliation')
        self.period = POOL.get('account.period')

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

    def test0010account_chart(self):
        'Test creation of minimal chart of accounts'
        with Transaction().start(DB_NAME, USER,
                context=CONTEXT) as transaction:
            account_template, = self.account_template.search([
                    ('parent', '=', None),
                    ])
            company, = self.company.search([('rec_name', '=', 'B2CK')])
            self.user.write([self.user(USER)], {
                    'main_company': company.id,
                    'company': company.id,
                    })
            CONTEXT.update(self.user.get_preferences(context_only=True))

            session_id, _, _ = self.account_create_chart.create()
            create_chart = self.account_create_chart(session_id)
            create_chart.account.account_template = account_template
            create_chart.account.company = company
            create_chart.transition_create_account()
            receivable, = self.account.search([
                    ('kind', '=', 'receivable'),
                    ('company', '=', company.id),
                    ])
            payable, = self.account.search([
                    ('kind', '=', 'payable'),
                    ('company', '=', company.id),
                    ])
            create_chart.properties.company = company
            create_chart.properties.account_receivable = receivable
            create_chart.properties.account_payable = payable
            create_chart.transition_create_properties()
            transaction.cursor.commit()

    def test0020fiscalyear(self):
        '''
        Test fiscalyear.
        '''
        with Transaction().start(DB_NAME, USER,
                context=CONTEXT) as transaction:
            today = datetime.date.today()
            company, = self.company.search([('rec_name', '=', 'B2CK')])
            sequence, = self.sequence.create([{
                        'name': '%s' % today.year,
                        'code': 'account.move',
                        'company': company.id,
                        }])
            invoice_sequence, = self.sequence_strict.create([{
                        'name': '%s' % today.year,
                        'code': 'account.invoice',
                        'company': company.id,
                        }])
            fiscalyear, = self.fiscalyear.create([{
                        'name': '%s' % today.year,
                        'start_date': today.replace(month=1, day=1),
                        'end_date': today.replace(month=12, day=31),
                        'company': company.id,
                        'post_move_sequence': sequence.id,
                        'out_invoice_sequence': invoice_sequence.id,
                        'in_invoice_sequence': invoice_sequence.id,
                        'out_credit_note_sequence': invoice_sequence.id,
                        'in_credit_note_sequence': invoice_sequence.id,
                        }])
            self.fiscalyear.create_period([fiscalyear])
            self.assertEqual(len(fiscalyear.periods), 12)
            transaction.cursor.commit()

    def test0030payment_type(self):
        with Transaction().start(DB_NAME, USER,
                context=CONTEXT) as transaction:
            self.payment_type.create([{
                        'name': 'Transfer',
                        'kind': 'receivable',
                        }])
            root, = self.account.search([('parent', '=', None)])
            type_ = self.account_type.search([])[0]
            account, = self.account.create([{
                        'name': 'Receivable 2',
                        'kind': 'receivable',
                        'parent': root.id,
                        'type': type_,
                        'reconcile': True,
                        }])
            self.payment_type.create([{
                        'name': 'Receipt',
                        'account': account.id,
                        'kind': 'receivable',
                        }])
            transaction.cursor.commit()

    def test0040payment_term(self):
        with Transaction().start(DB_NAME, USER,
                context=CONTEXT) as transaction:

            cu1, = self.currency.create([{
                        'name': 'cu1',
                        'symbol': 'cu1',
                        'code': 'cu1'
                        }])

            self.payment_term.create([{
                        'name': '1 month, 2 months',
                        'lines': [
                            ('create', [{
                                        'sequence': 1,
                                        'type': 'percent_on_total',
                                        'divisor': 4,
                                        'percentage': 25,
                                        'months': 1,
                                        }, {
                                        'sequence': 3,
                                        'type': 'remainder',
                                        'months': 2,
                                        }])]
                        }])
            transaction.cursor.commit()

    def test0050move_lines(self):
        '''
        Test account debit/credit.
        '''
        with Transaction().start(DB_NAME, USER,
                context=CONTEXT):
            company, = self.company.search([('rec_name', '=', 'B2CK')])
            journal_revenue, = self.journal.search([
                    ('code', '=', 'REV'),
                    ])
            journal_expense, = self.journal.search([
                    ('code', '=', 'EXP'),
                    ])
            revenue, = self.account.search([
                    ('kind', '=', 'revenue'),
                    ])
            receivable, = self.account.search([
                    ('name', '=', 'Main Receivable'),
                    ])
            receivable2, = self.account.search([
                    ('name', '=', 'Receivable 2'),
                    ])
            expense, = self.account.search([
                    ('kind', '=', 'expense'),
                    ('company', '=', company.id),
                    ])
            payable, = self.account.search([
                    ('kind', '=', 'payable'),
                    ('company', '=', company.id),
                    ])
            cash, = self.account.search([
                    ('name', '=', 'Main Cash'),
                    ])
            period = self.period.search([])[0]

            party, = self.party.create([{
                        'name': 'NaN-tic',
                        'addresses': [('create', [{
                            'street': 'Riego, 122 2on 2a',
                            }])]
                        }])
            receipt, = self.payment_type.search([('name', '=', 'Receipt')])
            transfer, = self.payment_type.search([('name', '=', 'Transfer')])
            term, = self.payment_term.search([])
            invoice_receipt, = self.invoice.create([{
                        'party': party.id,
                        'invoice_address': party.addresses[0].id,
                        'payment_term': term.id,
                        'payment_type': receipt.id,
                        'account': receivable.id,
                        'lines': [('create', [{
                                        'description': 'Line',
                                        'quantity': 1,
                                        'unit_price': Decimal('50'),
                                        'account': revenue.id,
                                        }])]
                        }])
            invoice_transfer, = self.invoice.create([{
                        'party': party.id,
                        'invoice_address': party.addresses[0].id,
                        'payment_term': term.id,
                        'payment_type': transfer.id,
                        'account': receivable.id,
                        'lines': [('create', [{
                                        'description': 'Line',
                                        'quantity': 1,
                                        'unit_price': Decimal('50'),
                                        'account': revenue.id,
                                        }])]
                        }])
            self.invoice.post([invoice_receipt, invoice_transfer])
            moves = self.move.search([])
            self.assertEqual(len(moves), 3)
            lines_to_reconcile = self.move_line.search([
                    ('account.name', '=', 'Receivable 2'),
                    ('move.state', '=', 'posted'),
                    ('debit', '=', Decimal('37.50')),
                    ])
            self.assertEqual(len(lines_to_reconcile), 1)
            self.assertEqual(invoice_transfer.amount_to_pay, Decimal('50'))
            self.assertEqual(invoice_receipt.amount_to_pay, Decimal('50'))

            move, = self.move.create([{
                        'period': period.id,
                        'journal': journal_revenue.id,
                        'date': period.start_date,
                        }])
            self.move_line.create([{
                        'move': move.id,
                        'account': cash.id,
                        'debit': Decimal('37.50'),
                        }])
            lines_to_reconcile += self.move_line.create([{
                        'move': move.id,
                        'account': receivable2.id,
                        'credit': Decimal('37.50'),
                        }])
            self.move.post([move])
            self.reconciliation.create([{
                        'lines': [('add', lines_to_reconcile)]
                        }])
            self.assertEqual(invoice_receipt.amount_to_pay, Decimal('12.5'))


def suite():
    suite = trytond.tests.test_tryton.suite()
    from trytond.modules.company.tests import test_company
    for test in test_company.suite():
        if test not in suite:
            suite.addTest(test)
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(
        AccountPaymentTypeMoveTestCase))
    return suite

if __name__ == '__main__':
    unittest.TextTestRunner(verbosity=2).run(suite())
