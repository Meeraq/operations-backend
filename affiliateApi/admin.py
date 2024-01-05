from django.contrib import admin
from .models import Affiliate
from .models import Lead

# Register your models here.
admin.site.register(Affiliate)
admin.site.register(Lead)