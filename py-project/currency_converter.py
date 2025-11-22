#!/usr/bin/env python3
"""
Simple currency converter CLI.

Fetches rates from https://api.exchangerate.host and falls back to built-in
rates when network access fails. Provides a small CLI using `argparse`.
"""

from typing import Dict
import argparse
import sys

try:
    import requests
except Exception:
    requests = None

FALLBACK_RATES: Dict[str, float] = {
    'USD': 1.0,
    'EUR': 0.92,
    'GBP': 0.79,
    'JPY': 150.0,
    'CAD': 1.36,
    'AUD': 1.49,
}

def get_rates(base: str = 'USD') -> Dict[str, float]:
    """Return exchange rates keyed by currency code for the given base.

    Tries to fetch live rates from exchangerate.host. On any error returns a
    small built-in fallback table re-normalized to the requested base.
    """
    base = base.upper()
    if requests is None:
        base_rate = FALLBACK_RATES.get(base, None)
        if base_rate is None:
            # normalize via USD if requested base not present
            base_rate = FALLBACK_RATES['USD']
        return {k: v / base_rate for k, v in FALLBACK_RATES.items()}

    url = f'https://api.exchangerate.host/latest?base={base}'
    try:
        resp = requests.get(url, timeout=5)
        resp.raise_for_status()
        data = resp.json()
        rates = data.get('rates')
        if not rates:
            raise ValueError('No rates in response')
        return rates
    except Exception:
        base_rate = FALLBACK_RATES.get(base)
        if base_rate is None:
            base_rate = FALLBACK_RATES['USD']
        return {k: v / base_rate for k, v in FALLBACK_RATES.items()}

def convert(amount: float, from_currency: str, to_currency: str, rates: Dict[str, float]) -> float:
    """Convert amount from `from_currency` to `to_currency` using `rates`.

    `rates` is assumed to be a mapping where each rate is the amount of that
    currency equal to 1 unit of the base (i.e. rate[X] = X per base).
    """
    from_currency = from_currency.upper()
    to_currency = to_currency.upper()
    if from_currency not in rates or to_currency not in rates:
        raise ValueError(f"Unsupported currency: {from_currency} or {to_currency}")

    # Convert amount -> base -> target
    amount_in_base = amount / rates[from_currency]
    return amount_in_base * rates[to_currency]

def main() -> None:
    parser = argparse.ArgumentParser(description='Convert between currencies.')
    parser.add_argument('amount', type=float, help='Amount to convert')
    parser.add_argument('from_currency', help='Currency code to convert from (e.g. USD)')
    parser.add_argument('to_currency', help='Currency code to convert to (e.g. EUR)')
    parser.add_argument('--base', default='USD', help='Base currency for fetched rates (default: USD)')
    args = parser.parse_args()

    try:
        rates = get_rates(args.base)
        result = convert(args.amount, args.from_currency, args.to_currency, rates)
        print(f"{args.amount:.2f} {args.from_currency.upper()} = {result:.4f} {args.to_currency.upper()}")
    except Exception as e:
        print('Error:', e, file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()
