from app.services.currency_service import CurrencyService, CurrencyServiceError


def main():
    # Ако имаш ключ:
    # currency_service = CurrencyService(access_key="YOUR_KEY_HERE")
    currency_service = CurrencyService()

    try:
        print("Supported currencies (first 15):")
        currencies = currency_service.list_supported_currencies()
        print(currencies[:15])

        print("\n100 EUR -> USD =", currency_service.convert(100.0, to_currency="USD", from_currency="EUR"))
        print("100 USD -> GBP =", currency_service.convert(100.0, to_currency="GBP", from_currency="USD"))
        print("1 EUR rate in USD =", currency_service.get_rate("USD", from_currency="EUR"))

    except CurrencyServiceError as e:
        print("Currency error:", e)


if __name__ == "__main__":
    main()
