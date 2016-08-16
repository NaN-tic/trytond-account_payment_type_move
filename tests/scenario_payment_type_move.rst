================
Invoice Scenario
================

Imports::

    >>> import datetime
    >>> from dateutil.relativedelta import relativedelta
    >>> from decimal import Decimal
    >>> from operator import attrgetter
    >>> from proteus import config, Model, Wizard
    >>> from trytond.modules.company.tests.tools import create_company, \
    ...     get_company
    >>> from trytond.modules.account.tests.tools import create_fiscalyear, \
    ...     create_chart, get_accounts, create_tax, set_tax_code
    >>> from.trytond.modules.account_invoice.tests.tools import \
    ...     set_fiscalyear_invoice_sequences, create_payment_term
    >>> today = datetime.date.today()

Create database::

    >>> config = config.set_trytond()
    >>> config.pool.test = True

Install account_invoice::

    >>> Module = Model.get('ir.module')
    >>> account_invoice_module, = Module.find(
    ...     [('name', '=', 'account_payment_type_move')])
    >>> Module.install([account_invoice_module.id], config.context)
    >>> Wizard('ir.module.install_upgrade').execute('upgrade')

Create company::

    >>> _ = create_company()
    >>> company = get_company()

Reload the context::

    >>> User = Model.get('res.user')
    >>> config._context = User.get_preferences(True, config.context)

Create fiscal year::

    >>> fiscalyear = set_fiscalyear_invoice_sequences(
    ...     create_fiscalyear(company))
    >>> fiscalyear.click('create_period')
    >>> period = fiscalyear.periods[0]

Create chart of accounts::

    >>> _ = create_chart(company)
    >>> accounts = get_accounts(company)
    >>> receivable = accounts['receivable']
    >>> revenue = accounts['revenue']
    >>> expense = accounts['expense']
    >>> cash = accounts['cash']

Create tax::

    >>> tax = set_tax_code(create_tax(Decimal('.10')))
    >>> tax.save()

Create party::

    >>> Party = Model.get('party.party')
    >>> party = Party(name='Party')
    >>> party.save()

Create product::

    >>> ProductUom = Model.get('product.uom')
    >>> unit, = ProductUom.find([('name', '=', 'Unit')])
    >>> ProductTemplate = Model.get('product.template')
    >>> Product = Model.get('product.product')
    >>> product = Product()
    >>> template = ProductTemplate()
    >>> template.name = 'product'
    >>> template.default_uom = unit
    >>> template.type = 'service'
    >>> template.list_price = Decimal('50')
    >>> template.cost_price = Decimal('25')
    >>> template.account_expense = expense
    >>> template.account_revenue = revenue
    >>> template.customer_taxes.append(tax)
    >>> template.save()
    >>> product.template = template
    >>> product.save()

Create payment term::

    >>> payment_term = create_payment_term()
    >>> payment_term.save()

Create payment type::

    >>> Account = Model.get('account.account')
    >>> PaymentType = Model.get('account.payment.type')
    >>> AccountType = Model.get('account.account.type')
    >>> transfer = PaymentType(name='Transfer', kind='receivable')
    >>> transfer.save()
    >>> receivable2_type, = AccountType.find([], limit=1)
    >>> receivable2 = Account(name='Receivable 2', kind='receivable',
    ...    type=receivable2_type, reconcile=True)
    >>> receivable2.save()
    >>> receipt = PaymentType(name='Receipt', account=receivable2,
    ...     kind='receivable')
    >>> receipt.save()

Create invoices::

    >>> Invoice = Model.get('account.invoice')
    >>> InvoiceLine = Model.get('account.invoice.line')
    >>> invoice_receipt = Invoice()
    >>> invoice_receipt.party = party
    >>> invoice_receipt.payment_term = payment_term
    >>> line = invoice_receipt.lines.new()
    >>> line.product = product
    >>> line.quantity = 1
    >>> line.unit_price = Decimal('50.0')
    >>> invoice_receipt.payment_type = receipt
    >>> invoice_receipt.save()
    >>> invoice_receipt.total_amount
    Decimal('55.00')
    >>> invoice_receipt.click('post')
    >>> invoice_receipt.state
    u'posted'
    >>> invoice_transfer = Invoice()
    >>> invoice_transfer.party = party
    >>> invoice_transfer.payment_term = payment_term
    >>> line = invoice_transfer.lines.new()
    >>> line.product = product
    >>> line.quantity = 1
    >>> line.unit_price = Decimal('50.0')
    >>> invoice_transfer.payment_type = transfer
    >>> invoice_transfer.save()
    >>> invoice_transfer.total_amount
    Decimal('55.00')
    >>> invoice_transfer.click('post')
    >>> invoice_transfer.state
    u'posted'

Check and reconcile::

    >>> Move = Model.get('account.move')
    >>> MoveLine = Model.get('account.move.line')
    >>> Reconciliation = Model.get('account.move.reconciliation')
    >>> invoice_transfer.amount_to_pay
    Decimal('55.00')
    >>> invoice_receipt.amount_to_pay
    Decimal('55.00')
    >>> move = Move(journal=invoice_receipt.journal.id)
    >>> move.save()
    >>> line = move.lines.new(account=cash.id, debit=Decimal('55.00'))
    >>> line = move.lines.new(account=receivable2.id, credit=Decimal('55.00'))
    >>> move.click('post')
    >>> line, _ = move.lines
    >>> line.credit
    Decimal('55.00')
    >>> lines_to_reconcile = MoveLine.find([
    ...         ('account', '=', receivable2.id),
    ...         ('move.state', '=', 'posted'),
    ...         ('debit', '=', Decimal('55.00')),
    ...         ])
    >>> lines_to_reconcile.append(line)
    >>> len(lines_to_reconcile)
    2
    >>> reconcile_lines = Wizard('account.move.reconcile_lines',
    ...     lines_to_reconcile)
    >>> reconcile_lines.state == 'end'
    True
    >>> invoice_receipt.reload()
    >>> invoice_receipt.amount_to_pay
    Decimal('0.0')
