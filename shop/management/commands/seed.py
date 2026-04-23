from django.core.management.base import BaseCommand
from shop.models import Discount, Item, Order, Tax

ITEMS = [
    {'name': 'Classic Tee',      'description': 'Premium 100% cotton t-shirt, unisex sizing, minimalist design. Perfect for everyday wear.', 'price': '29.99', 'currency': 'usd'},
    {'name': 'Matte Notebook',   'description': 'A5 dot-grid notebook, 192 pages, Smyth-sewn binding. Lays completely flat when open.',        'price': '14.99', 'currency': 'usd'},
    {'name': 'Ceramic Mug',      'description': '350 ml handcrafted ceramic mug, matte black glaze. Microwave and dishwasher safe.',           'price': '19.99', 'currency': 'usd'},
    {'name': 'Canvas Tote',      'description': 'Heavy-duty 12 oz natural canvas tote. Reinforced handles, 38×42 cm capacity.',                'price': '24.99', 'currency': 'usd'},
    {'name': 'Enamel Pin',       'description': 'Hard enamel collector pin, 3 cm, gold plating. Ships in a branded kraft box.',               'price': '9.99',  'currency': 'eur'},
    {'name': 'Art Print (A3)',   'description': 'Giclée fine art print on 300 gsm cotton paper. Signed and numbered edition of 50.',          'price': '49.99', 'currency': 'eur'},
]


class Command(BaseCommand):
    help = 'Seed the database with sample items, discounts, taxes, and orders'

    def handle(self, *args, **kwargs):
        if Item.objects.exists():
            self.stdout.write(self.style.WARNING('Data already exists — skipping seed.'))
            return

        # Items
        items = []
        for data in ITEMS:
            item = Item.objects.create(**data)
            items.append(item)
            self.stdout.write(self.style.SUCCESS(f'  Item: {item}'))

        # Discount (placeholder — needs real Stripe coupon ID to work)
        discount = Discount.objects.create(
            name='Summer Sale',
            stripe_coupon_id='',   # fill in after creating coupon in Stripe Dashboard
            percent_off=10,
        )
        self.stdout.write(self.style.SUCCESS(f'  Discount: {discount}'))

        # Tax (placeholder — needs real Stripe tax rate ID to work)
        tax = Tax.objects.create(
            name='VAT',
            stripe_tax_rate_id='',  # fill in after creating tax rate in Stripe Dashboard
            percentage=20,
            inclusive=False,
        )
        self.stdout.write(self.style.SUCCESS(f'  Tax: {tax}'))

        # Order (USD items, no discount/tax by default)
        order = Order.objects.create()
        order.items.set([items[0], items[1], items[2]])
        self.stdout.write(self.style.SUCCESS(f'  Order: {order} (${order.get_total()})'))

        self.stdout.write(self.style.SUCCESS('\nSeed complete.'))
        self.stdout.write(
            self.style.WARNING(
                '\nNOTE: To enable Discount and Tax in Stripe Checkout:\n'
                '  1. Create a Coupon at https://dashboard.stripe.com/coupons\n'
                '  2. Create a Tax Rate at https://dashboard.stripe.com/tax-rates\n'
                '  3. Set the IDs in Django Admin → Discounts / Taxes\n'
                '  4. Attach them to an Order in Admin → Orders\n'
            )
        )
