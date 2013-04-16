=========================
account_payment_type_move
=========================

Este módulo permite configurar una cuenta contable de clientes y una de
proveedores en los tipos de pago de forma que el sistema genera un asiento
automáticamente a esta nueva cuenta cuando se valida un asiento con apuntes
con el correspondiente tipo de pago.

Por ejemplo, si creamos una factura con un tipo de pago Recibo, el cual hemos
definido con la cuenta de cliente 431000, el sistema generará el asiento
correspondiente a la factura (430000 - 700000) y inmediatamente después el
asiento: 431000 - 430000 y conciliará los dos apuntes de la cuenta 430000.

El módulo también cambia la forma en la que se considera que una factura está
como pagada puesto que la conciliación automática daría la factura como pagada.
El nuevo criterio aplicado busca en todos los apuntes contables que tienen
indicado como origen dicha factura.
