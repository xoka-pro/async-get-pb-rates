import platform
import aiohttp
import asyncio
import argparse

# pretty logging
from loguru import logger
# pretty print json
from pprint import pprint
from datetime import date, timedelta

PB_API_URL = "https://api.privatbank.ua/p24api/exchange_rates?json&date="


class PBRatesArchive:

    def __init__(self):
        self.received_jsons = []

    async def get_currencies(self, days_to_get: int):
        """Get data from server and call function to format data"""
        tasks = []
        async with aiohttp.ClientSession() as session:
            for day in range(days_to_get):
                date_to_get = (date.today() - timedelta(day)).strftime('%d.%m.%Y')
                url = f'{PB_API_URL}{date_to_get}'
                tasks.append(self.get_one_day_json(session, url))
            await asyncio.gather(*tasks)

        return await self.format_result()

    async def get_one_day_json(self, session, url_of_the_day):
        """Preparing requests to server for interested days"""
        try:
            async with session.get(url_of_the_day) as response:
                if response.status == 200:
                    logger.debug('start request')
                    one_day_request = await response.json()
                    self.received_jsons.append(one_day_request)
        except aiohttp.ClientConnectorError:
            logger.error('Connection error')

    async def format_result(self):
        """Format received jsons to get only requested data"""
        result = []
        for day in sorted(self.received_jsons, key=lambda x: x['date']):
            result.append(day["date"])
            for currency in day['exchangeRate']:
                if currency['currency'] in {'EUR', 'USD'}:
                    day_rates = f'{currency["currency"]}: sale:{currency["saleRate"]}, purchase:{currency["purchaseRate"]}'
                    result.append(day_rates)
        return result


def arg_parser() -> int:
    """Parser for command prompt arguments"""
    parser = argparse.ArgumentParser(description='Application get USD and EUR exchange rates from PrivatBank public API')
    parser.add_argument('-d', help="How many days get from archive. Max = 10, default = 5", default=5)
    args = vars(parser.parse_args())
    input_days = int(args.get('d'))
    if 10 < input_days < 1:
        print("Return in period 1-10 days")
        quit(1)
    return input_days


async def main():
    pb_get = PBRatesArchive()
    currencies = await pb_get.get_currencies(days)

    pprint(currencies)


if __name__ == '__main__':
    # useful only for Windows OS
    if platform.system() == 'Windows':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    days = arg_parser()

    asyncio.run(main())
