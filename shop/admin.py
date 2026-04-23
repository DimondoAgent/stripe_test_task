from django.contrib import admin
from django.utils.html import format_html

from .models import Discount, Item, Order, Tax


@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'price_display', 'currency', 'description_short')
    list_filter = ('currency',)
    search_fields = ('name', 'description')
    ordering = ('id',)

    def price_display(self, obj):
        symbol = obj.get_currency_symbol()
        return format_html('<strong>{}{}</strong>', symbol, obj.price)
    price_display.short_description = 'Price'

    def description_short(self, obj):
        return obj.description[:60] + '…' if len(obj.description) > 60 else obj.description
    description_short.short_description = 'Description'


@admin.register(Discount)
class DiscountAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'stripe_coupon_id', 'percent_off', 'amount_off')
    search_fields = ('name', 'stripe_coupon_id')


@admin.register(Tax)
class TaxAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'stripe_tax_rate_id', 'percentage', 'inclusive')
    search_fields = ('name', 'stripe_tax_rate_id')


class OrderItemInline(admin.TabularInline):
    model = Order.items.through
    extra  = 1
    verbose_name = 'Item'
    verbose_name_plural = 'Items in this order'


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'items_count', 'total_display', 'discount', 'tax', 'created_at')
    list_filter = ('discount', 'tax')
    readonly_fields = ('created_at', 'total_display')
    inlines = [OrderItemInline]
    exclude = ('items',)

    def items_count(self, obj):
        return obj.items.count()
    items_count.short_description = 'Items'

    def total_display(self, obj):
        symbol = '$' if obj.get_currency() == 'usd' else '€'
        return format_html('<strong>{}{}</strong>', symbol, obj.get_total())
    total_display.short_description = 'Total'
