from django.contrib import admin
from .models import *

@admin.register(Commodity)
class CommodityAdmin(admin.ModelAdmin):
    list_display = ['item__name', 'market_price', 'quantity', 'timestamp', 'origin']
    ordering = ['-timestamp', 'item__name']
    search_fields = ['item__name', 'item__id']

    def has_change_permission(self, request, obj=None):
        return False
