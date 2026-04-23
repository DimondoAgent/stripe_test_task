import stripe
from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render

from .models import Discount, Item, Order, Tax

def _get_stripe_keys(currency: str) -> tuple[str, str]:
    """Return (secret_key, publishable_key) for the given currency."""
    currency = currency.lower()
    if currency == 'eur':
        return settings.STRIPE_SECRET_KEY_EUR, settings.STRIPE_PUBLISHABLE_KEY_EUR
    return settings.STRIPE_SECRET_KEY_USD, settings.STRIPE_PUBLISHABLE_KEY_USD


def item_detail(request, pk):
    """GET /item/{id}/ — HTML page with item info and Buy button."""
    item = get_object_or_404(Item, pk=pk)
    _, pub_key = _get_stripe_keys(item.currency)
    return render(request, 'item.html', {
        'item': item,
        'stripe_publishable_key': pub_key,
    })


def buy_item(request, pk):
    """
    GET /buy/{id}/ — Create a Stripe Checkout Session for a single Item.
    Returns JSON: {"session_id": "cs_test_..."}
    """
    item = get_object_or_404(Item, pk=pk)
    secret_key, _ = _get_stripe_keys(item.currency)
    stripe.api_key = secret_key

    session = stripe.checkout.Session.create(
        payment_method_types=['card'],
        line_items=[
            {
                'price_data': {
                    'currency': item.currency,
                    'unit_amount': item.get_price_cents(),
                    'product_data': {
                        'name': item.name,
                        'description': item.description,
                    },
                },
                'quantity': 1,
            }
        ],
        mode='payment',
        success_url=settings.SITE_URL + '/success/',
        cancel_url=settings.SITE_URL + f'/item/{item.pk}/',
    )

    return JsonResponse({'session_id': session.id})


def order_detail(request, pk):
    """GET /order/{id}/ — HTML page for an Order (multiple items)."""
    order = get_object_or_404(Order, pk=pk)
    currency = order.get_currency()
    _, pub_key = _get_stripe_keys(currency)
    return render(request, 'order.html', {
        'order': order,
        'stripe_publishable_key': pub_key,
        'total': order.get_total(),
        'currency_symbol': '$' if currency == 'usd' else '€',
    })


def buy_order(request, pk):
    """
    GET /buy-order/{id}/ — Create a Stripe Checkout Session for a full Order.
    Applies Discount (coupon) and Tax (tax_rate) if set on the Order.
    Returns JSON: {"session_id": "cs_test_..."}
    """
    order = get_object_or_404(Order, pk=pk)
    currency = order.get_currency()
    secret_key, _ = _get_stripe_keys(currency)
    stripe.api_key = secret_key

    line_items = []
    for item in order.items.all():
        line_item = {
            'price_data': {
                'currency': currency,
                'unit_amount': item.get_price_cents(),
                'product_data': {
                    'name': item.name,
                    'description': item.description,
                },
            },
            'quantity': 1,
        }
        if order.tax and order.tax.stripe_tax_rate_id:
            line_item['tax_rates'] = [order.tax.stripe_tax_rate_id]

        line_items.append(line_item)

    session_kwargs = {
        'payment_method_types': ['card'],
        'line_items': line_items,
        'mode': 'payment',
        'success_url': settings.SITE_URL + '/success/',
        'cancel_url': settings.SITE_URL + f'/order/{order.pk}/',
    }

    if order.discount and order.discount.stripe_coupon_id:
        session_kwargs['discounts'] = [{'coupon': order.discount.stripe_coupon_id}]

    session = stripe.checkout.Session.create(**session_kwargs)
    return JsonResponse({'session_id': session.id})


def index_view(request):
    """Homepage — list all items and orders."""
    return render(request, 'index.html', {
        'items': Item.objects.all(),
        'orders': Order.objects.prefetch_related('items').select_related('discount', 'tax').all(),
    })


def success_view(request):
    return render(request, 'success.html')  


def cancel_view(request):
    return render(request, 'cancel.html')  