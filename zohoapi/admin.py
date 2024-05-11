from django.contrib import admin
from .models import (
    InvoiceData,
    Vendor,
    AccessToken,
    InvoiceStatusUpdate,
    PoReminder,
    OrdersAndProjectMapping,
    ZohoCustomer,
    ZohoVendor,
    SalesOrder,
    SalesOrderLineItem,
    PurchaseOrder,
    PurchaseOrderLineItem,
    ClientInvoice,
    ClientInvoiceLineItem,
    Bill,
    BillLineItem,
    LineItems,
)

# Register your models here.
admin.site.register(InvoiceData)
admin.site.register(Vendor)
admin.site.register(AccessToken)
admin.site.register(PoReminder)
admin.site.register(InvoiceStatusUpdate)
admin.site.register(OrdersAndProjectMapping)
admin.site.register(LineItems)
admin.site.register(ZohoCustomer)
admin.site.register(ZohoVendor)
admin.site.register(SalesOrder)
admin.site.register(SalesOrderLineItem)
admin.site.register(PurchaseOrderLineItem)
admin.site.register(PurchaseOrder)
admin.site.register(ClientInvoice)
admin.site.register(ClientInvoiceLineItem)
admin.site.register(BillLineItem)
admin.site.register(Bill)
