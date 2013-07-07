================
Invoice Scenario
================

Imports::

    >>> import datetime
    >>> from dateutil.relativedelta import relativedelta
    >>> from decimal import Decimal
    >>> from operator import attrgetter
    >>> from proteus import config, Model, Wizard
    >>> today = datetime.date.today()

Create database::

    >>> config = config.set_trytond()
    >>> config.pool.test = True

Install account_invoice::

    >>> Module = Model.get('ir.module.module')
    >>> account_invoice_module, = Module.find(
    ...     [('name', '=', 'account_payment_type_move')])
    >>> Module.install([account_invoice_module.id], config.context)
    >>> Wizard('ir.module.module.install_upgrade').execute('upgrade')

Create company::

    >>> Currency = Model.get('currency.currency')
    >>> CurrencyRate = Model.get('currency.currency.rate')
    >>> currencies = Currency.find([('code', '=', 'USD')])
    >>> if not currencies:
    ...     currency = Currency(name='US Dollar', symbol=u'$', code='USD',
    ...         rounding=Decimal('0.01'), mon_grouping='[]',
    ...         mon_decimal_point='.')
    ...     currency.save()
    ...     CurrencyRate(date=today + relativedelta(month=1, day=1),
    ...         rate=Decimal('1.0'), currency=currency).save()
    ... else:
    ...     currency, = currencies
    >>> Company = Model.get('company.company')
    >>> Party = Model.get('party.party')
    >>> company_config = Wizard('company.company.config')
    >>> company_config.execute('company')
    >>> company = company_config.form
    >>> party = Party(name='Dunder Mifflin')
    >>> party.save()
    >>> company.party = party
    >>> company.currency = currency
    >>> company_config.execute('add')
    >>> company, = Company.find([])

Reload the context::

    >>> User = Model.get('res.user')
    >>> config._context = User.get_preferences(True, config.context)

Create fiscal year::

    >>> FiscalYear = Model.get('account.fiscalyear')
    >>> Sequence = Model.get('ir.sequence')
    >>> SequenceStrict = Model.get('ir.sequence.strict')
    >>> fiscalyear = FiscalYear(name=str(today.year))
    >>> fiscalyear.start_date = today + relativedelta(month=1, day=1)
    >>> fiscalyear.end_date = today + relativedelta(month=12, day=31)
    >>> fiscalyear.company = company
    >>> post_move_seq = Sequence(name=str(today.year), code='account.move',
    ...     company=company)
    >>> post_move_seq.save()
    >>> fiscalyear.post_move_sequence = post_move_seq
    >>> invoice_seq = SequenceStrict(name=str(today.year),
    ...     code='account.invoice', company=company)
    >>> invoice_seq.save()
    >>> fiscalyear.out_invoice_sequence = invoice_seq
    >>> fiscalyear.in_invoice_sequence = invoice_seq
    >>> fiscalyear.out_credit_note_sequence = invoice_seq
    >>> fiscalyear.in_credit_note_sequence = invoice_seq
    >>> fiscalyear.save()
    >>> FiscalYear.create_period([fiscalyear.id], config.context)

Create chart of accounts::

    >>> AccountTemplate = Model.get('account.account.template')
    >>> Account = Model.get('account.account')
    >>> account_template, = AccountTemplate.find([('parent', '=', False)])
    >>> create_chart = Wizard('account.create_chart')
    >>> create_chart.execute('account')
    >>> create_chart.form.account_template = account_template
    >>> create_chart.form.company = company
    >>> create_chart.execute('create_account')
    >>> receivable, = Account.find([
    ...         ('kind', '=', 'receivable'),
    ...         ('company', '=', company.id),
    ...         ])
    >>> payable, = Account.find([
    ...         ('kind', '=', 'payable'),
    ...         ('company', '=', company.id),
    ...         ])
    >>> revenue, = Account.find([
    ...         ('kind', '=', 'revenue'),
    ...         ('company', '=', company.id),
    ...         ])
    >>> expense, = Account.find([
    ...         ('kind', '=', 'expense'),
    ...         ('company', '=', company.id),
    ...         ])
    >>> cash, = Account.find([
    ...         ('name', '=', 'Main Cash'),
    ...         ('company', '=', company.id),
    ...         ])
    >>> account_tax, = Account.find([
    ...         ('kind', '=', 'other'),
    ...         ('company', '=', company.id),
    ...         ('name', '=', 'Main Tax'),
    ...         ])
    >>> create_chart.form.account_receivable = receivable
    >>> create_chart.form.account_payable = payable
    >>> create_chart.execute('create_properties')

Create tax::

    >>> TaxCode = Model.get('account.tax.code')
    >>> Tax = Model.get('account.tax')
    >>> tax = Tax()
    >>> tax.name = 'Tax'
    >>> tax.description = 'Tax'
    >>> tax.type = 'percentage'
    >>> tax.rate = Decimal('.10')
    >>> tax.invoice_account = account_tax
    >>> tax.credit_note_account = account_tax
    >>> invoice_base_code = TaxCode(name='invoice base')
    >>> invoice_base_code.save()
    >>> tax.invoice_base_code = invoice_base_code
    >>> invoice_tax_code = TaxCode(name='invoice tax')
    >>> invoice_tax_code.save()
    >>> tax.invoice_tax_code = invoice_tax_code
    >>> credit_note_base_code = TaxCode(name='credit note base')
    >>> credit_note_base_code.save()
    >>> tax.credit_note_base_code = credit_note_base_code
    >>> credit_note_tax_code = TaxCode(name='credit note tax')
    >>> credit_note_tax_code.save()
    >>> tax.credit_note_tax_code = credit_note_tax_code
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

    >>> PaymentTerm = Model.get('account.invoice.payment_term')
    >>> PaymentTermLine = Model.get('account.invoice.payment_term.line')
    >>> payment_term = PaymentTerm(name='Term')
    >>> payment_term_line = PaymentTermLine(type='percent_on_total', months=1,
    ...     percentage=Decimal(25))
    >>> payment_term.lines.append(payment_term_line)
    >>> payment_term_line = PaymentTermLine(type='remainder', months=2)
    >>> payment_term.lines.append(payment_term_line)
    >>> payment_term.save()

Create payment type::

    >>> PaymentType = Model.get('account.payment.type')
    >>> AccountType = Model.get('account.account.type')
    >>> transfer = PaymentType(name='Transfer', kind='receivable')
    >>> transfer.save()
    >>> receivable2_type = AccountType.find([])[0]
    >>> receivable2_type.save()
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
    >>> invoice_receipt.payment_type = receipt
    >>> line = InvoiceLine()
    >>> invoice_receipt.lines.append(line)
    >>> line.product = product
    >>> line.quantity = 1
    >>> invoice_receipt.save()
    >>> invoice_receipt.total_amount == Decimal('55.0')
    True
    >>> invoice_transfer = Invoice()
    >>> invoice_transfer.party = party
    >>> invoice_transfer.payment_term = payment_term
    >>> invoice_transfer.payment_type = transfer
    >>> line = InvoiceLine()
    >>> invoice_transfer.lines.append(line)
    >>> line.product = product
    >>> line.quantity = 1
    >>> invoice_transfer.save()
    >>> invoice_transfer.total_amount == Decimal('55.0')
    True
    >>> Invoice.post([invoice_receipt.id, invoice_transfer.id], config.context)
    >>> invoice_receipt.reload()
    >>> invoice_transfer.reload()
    >>> invoice_receipt.state
    u'posted'
    >>> invoice_transfer.state
    u'posted'

Check and reconcile::

    >>> Move = Model.get('account.move')
    >>> MoveLine = Model.get('account.move.line')
    >>> Reconciliation = Model.get('account.move.reconciliation')
    >>> invoice_transfer.amount_to_pay == Decimal('55.0')
    True
    >>> invoice_receipt.amount_to_pay == Decimal('55.0')
    True
    >>> move = Move(journal=invoice_receipt.journal.id)
    >>> move.save()
    >>> line = MoveLine(move=move.id, account=cash.id, debit=Decimal('41.25'))
    >>> line.save()
    >>> line = MoveLine(move=move.id, account=receivable2.id,
    ...     credit=Decimal('41.25'))
    >>> line.save()
    >>> Move.post([move.id], config.context)
    >>> lines_to_reconcile = MoveLine.find([
    ...         ('account', '=', receivable2.id),
    ...         ('move.state', '=', 'posted'),
    ...         ('debit', '=', Decimal('41.25')),
    ...         ])
    >>> lines_to_reconcile.append(line)
    >>> len(lines_to_reconcile)
    2
    >>> reconcile_lines = Wizard('account.move.reconcile_lines',
    ...     lines_to_reconcile)
    >>> reconcile_lines.state == 'end'
    True
    >>> invoice_receipt.reload()
    >>> invoice_receipt.amount_to_pay == Decimal('13.75')
    True
