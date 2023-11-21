import json

from scrapy import Spider, Request


class WeatherScrapingSpider(Spider):
    name = "weatherscraper"

    def __init__(self):
        self.days_to_scrape = 7  # Min 1, Max 10
        self.api_url = "https://weather.com/api/v1/p/redux-dal"
        self.latitude = 26.231
        self.longitude = -98.445
        self.headers = {
            "authority": "weather.com",
            "accept": "*/*",
            "accept-language": "en-US,en;q=0.9",
            "cache-control": "no-cache",
            "content-type": "application/json",
            "origin": "https://weather.com",
            "pragma": "no-cache",
            "referer": "https://weather.com/",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
        }
        self.payload = [
            {
                "name": "getSunV3DailyForecastWithHeadersUrlConfig",
                "params": {
                    "duration": f"{self.days_to_scrape}day",
                    "geocode": f"{self.latitude},{self.longitude}",
                    "units": "e",
                },
            }
        ]

    def start_requests(self):
        yield Request(
            url=self.api_url,
            method="POST",
            dont_filter=True,
            headers=self.headers,
            body=json.dumps(self.payload),
        )

    def scrape(self, response, data):
        try:
            item = {}
            yield item
        except Exception as ex:
            # As web scraping can be unpredictable we want to catch any exception
            self.logger.error("An error ocurred while scraping weather data. - %s", ex)
            return None

    def parse(self, response):
        try:
            data = json.loads(response.text)
            yield from self.scrape(response, data)
        except (json.JSONDecodeError, TypeError) as ex:
            self.logger.error("An error ocurred while parsing JSON data. - %s", ex)
            return None
