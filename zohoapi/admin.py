from django.contrib import admin
from .models import InvoiceData, Vendor, AccessToken, InvoiceStatusUpdate, PoReminder

# Register your models here.
admin.site.register(InvoiceData)
admin.site.register(Vendor)
admin.site.register(AccessToken)
admin.site.register(PoReminder)
admin.site.register(InvoiceStatusUpdate)
