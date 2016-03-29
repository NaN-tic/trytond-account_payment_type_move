# This file is part of account_payment_type_move module for Tryton.
# The COPYRIGHT file at the top level of this repository contains
# the full copyright notices and license terms.
from sql import Cast
from sql.operators import Concat
from sql.conditionals import Case
from itertools import izip
from trytond.model import ModelView, fields
from trytond.pool import Pool, PoolMeta
from trytond.tools import grouped_slice, reduce_ids
from trytond.transaction import Transaction

__all__ = ['PaymentType', 'Move', 'Invoice']


class PaymentType:
    __metaclass__ = PoolMeta
    __name__ = 'account.payment.type'
    account = fields.Many2One('account.account', 'Account', help='If set, '
        'once a move with this payment type will be confirmed, a new move '
        'will be created that will move the balance from the '
        'payable/receivable to the account supplied here.')


class Move:
    __metaclass__ = PoolMeta
    __name__ = 'account.move'

    def auto_move_line_defaults(self):
        return {
            'move': self.id,
            'tax_lines': [],
            'payment_type': None,
            }

    def auto_move_counterpart_defaults(self):
        return {
            'move': self.id,
            'tax_lines': [],
            }

    @classmethod
    def create_payment_auto_move(cls, moves):
        Line = Pool().get('account.move.line')
        for move in moves:
            to_reconcile = []
            for line in move.lines:
                if (not line.payment_type
                        or line.account.kind not in ('receivable', 'payable')):
                    continue
                account = line.payment_type.account
                if not account or account == line.account:
                    continue
                to_reconcile.append(line)
            if not to_reconcile:
                continue
            new_move = cls()
            new_move.date = move.date
            new_move.period = move.period
            new_move.journal = move.journal
            new_move.origin = move.origin
            new_move.description = move.description
            new_move.save()
            new_lines = Line.copy(to_reconcile,
                new_move.auto_move_line_defaults())
            counterparts = Line.copy(to_reconcile,
                new_move.auto_move_counterpart_defaults())
            to_reconcile2 = []
            for line, new_line, counterpart in izip(to_reconcile, new_lines,
                    counterparts):
                new_line.debit = line.credit
                new_line.credit = line.debit
                if not line.account.party_required:
                    line.party = None
                new_line.save()
                counterpart.account = line.payment_type.account
                if not counterpart.account.party_required:
                    counterpart.party = None
                counterpart.save()
                to_reconcile2.append((line, new_line))

            cls.post([new_move])
            for l1, l2 in to_reconcile2:
                Line.reconcile([l1, l2])

    @classmethod
    @ModelView.button
    def post(cls, moves):
        super(Move, cls).post(moves)
        # Avoid infinite recursion by setting and checking for a
        # 'payment_type_move' in context
        if Transaction().context.get('payment_type_move', True):
            with Transaction().set_context(payment_type_move=False):
                cls.create_payment_auto_move(moves)


class Invoice:
    __metaclass__ = PoolMeta
    __name__ = 'account.invoice'

    @classmethod
    def get_lines_to_pay(cls, invoices, name):
        pool = Pool()
        Move = pool.get('account.move')
        Line = pool.get('account.move.line')
        Account = pool.get('account.account')
        line = Line.__table__()
        account = Account.__table__()
        move = Move.__table__()
        invoice = cls.__table__()
        cursor = Transaction().cursor
        _, origin_type = Move.origin.sql_type()

        lines = super(Invoice, cls).get_lines_to_pay(invoices, name)
        for sub_ids in grouped_slice(invoices):
            red_sql = reduce_ids(invoice.id, sub_ids)
            query = invoice.join(move,
                condition=((move.origin == Concat('account.invoice,',
                                Cast(invoice.id, origin_type))))
                    ).join(line, condition=(line.move == move.id)
                    ).join(account, condition=(
                        (line.account == account.id) &
                        Case((invoice.type.in_(
                                ['out_invoice', 'out_credit_note']),
                            account.kind == 'receivable'),
                            else_=account.kind == 'payable'))).select(
                    invoice.id, line.id,
                    where=(line.maturity_date != None) & red_sql,
                    order_by=(invoice.id, line.maturity_date))
            cursor.execute(*query)
            for invoice_id, line_id in cursor.fetchall():
                if not line_id in lines[invoice_id]:
                    lines[invoice_id].append(line_id)
        return lines
