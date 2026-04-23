from django.db import models


class Discount(models.Model):
    """
    Скидка, привязанная к Stripe Coupon.
    Создайте купон в Stripe Dashboard и вставьте его ID сюда.
    https://dashboard.stripe.com/coupons
    """
    name= models.CharField(max_length=255, verbose_name='Name')
    stripe_coupon_id = models.CharField(
        max_length=255,
        verbose_name='Stripe Coupon ID',
        help_text='ID купона из Stripe Dashboard (например: SAVE10)',
        blank=True,
    )
    percent_off = models.DecimalField(
        max_digits=5, decimal_places=2,
        null=True, blank=True,
        verbose_name='Percent off (%)',
        help_text='Только для отображения. Реальное значение берётся из Stripe.',
    )
    amount_off = models.DecimalField(
        max_digits=10, decimal_places=2,
        null=True, blank=True,
        verbose_name='Amount off',
        help_text='Только для отображения. Реальное значение берётся из Stripe.',
    )

    class Meta:
        verbose_name = 'Discount'
        verbose_name_plural = 'Discounts'

    def __str__(self):
        if self.percent_off:
            return f'{self.name} (−{self.percent_off}%)'
        if self.amount_off:
            return f'{self.name} (−${self.amount_off})'
        return self.name


class Tax(models.Model):
    """
    Налог, привязанный к Stripe Tax Rate.
    Создайте tax rate в Stripe Dashboard и вставьте его ID сюда.
    https://dashboard.stripe.com/tax-rates
    """
    name = models.CharField(max_length=255, verbose_name='Name')
    stripe_tax_rate_id = models.CharField(
        max_length=255,
        verbose_name='Stripe Tax Rate ID',
        help_text='ID налоговой ставки из Stripe Dashboard (например: txr_xxxxx)',
        blank=True,
    )
    percentage = models.DecimalField(
        max_digits=5, decimal_places=2,
        verbose_name='Percentage (%)',
        help_text='Только для отображения. Реальное значение берётся из Stripe.',
    )
    inclusive = models.BooleanField(
        default=False,
        verbose_name='Inclusive (уже включён в цену)',
    )

    class Meta:
        verbose_name = 'Tax'
        verbose_name_plural = 'Taxes'

    def __str__(self):
        kind = 'incl.' if self.inclusive else 'excl.'
        return f'{self.name} ({self.percentage}% {kind})'


class Item(models.Model):
    CURRENCY_USD = 'usd'
    CURRENCY_EUR = 'eur'
    CURRENCY_CHOICES = [
        (CURRENCY_USD, 'USD — US Dollar'),
        (CURRENCY_EUR, 'EUR — Euro'),
    ]

    name = models.CharField(max_length=255, verbose_name='Name')
    description = models.TextField(verbose_name='Description')
    price = models.DecimalField(
        max_digits=10, decimal_places=2,
        verbose_name='Price',
    )
    currency = models.CharField(
        max_length=3,
        choices=CURRENCY_CHOICES,
        default=CURRENCY_USD,
        verbose_name='Currency',
    )

    class Meta:
        verbose_name = 'Item'
        verbose_name_plural = 'Items'

    def __str__(self):
        return f'{self.name} — {self.price} {self.currency.upper()}'

    def get_price_cents(self):
        """Return price in smallest currency unit (cents / euro-cents)."""
        return int(self.price * 100)

    def get_currency_symbol(self):
        return '$' if self.currency == self.CURRENCY_USD else '€'


class Order(models.Model):
    """
    Заказ, объединяющий несколько Item.
    К заказу можно прикрепить Discount и Tax — они отображаются в Stripe Checkout.
    """
    items = models.ManyToManyField(Item, verbose_name='Items', blank=False)
    discount = models.ForeignKey(
        Discount,
        null=True, blank=True,
        on_delete=models.SET_NULL,
        verbose_name='Discount',
    )
    tax = models.ForeignKey(
        Tax,
        null=True, blank=True,
        on_delete=models.SET_NULL,
        verbose_name='Tax',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Order'
        verbose_name_plural = 'Orders'

    def __str__(self):
        return f'Order #{self.pk} ({self.items.count()} items)'

    def get_total(self):
        """Total price in main currency units."""
        return sum(item.price for item in self.items.all())

    def get_total_cents(self):
        return int(self.get_total() * 100)

    def get_currency(self):
        """Use currency of the first item (all items should share the same currency)."""
        first = self.items.first()
        return first.currency if first else 'usd'
