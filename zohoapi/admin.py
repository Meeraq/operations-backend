from django.contrib import admin
from .models import InvoiceData, Vendor

# Register your models here.
admin.site.register(InvoiceData)
admin.site.register(Vendor)
