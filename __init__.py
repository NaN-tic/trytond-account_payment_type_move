#This file is part of account_payment_type_move module for Tryton.
#The COPYRIGHT file at the top level of this repository contains
#the full copyright notices and license terms.

from trytond.pool import Pool
from .account import *


def register():
    Pool.register(
        PaymentType,
        Move,
        Invoice,
        module='account_payment_type_move', type_='model')
