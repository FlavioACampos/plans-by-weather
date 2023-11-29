import json

from scrapy import Spider, Request
from datetime import datetime


class WeatherScrapingSpider(Spider):
    name = "weatherscraper"
    custom_settings = {
        "LOG_LEVEL": "DEBUG",
        "FEEDS": {"results.csv": {"format": "csv", "encoding": "utf8"}},
    }

    def __init__(self):
        self.days = 7  # Min 1, Max 10
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
        # e = Fahrenheit, m = Celsius
        self.units = "e"
        self.payload = [
            {
                "name": "getSunV3DailyForecastWithHeadersUrlConfig",
                "params": {
                    "duration": f"{self.days}day",
                    "geocode": f"{self.latitude},{self.longitude}",
                    "units": self.units,
                },
            }
        ]

    def create_item(self):
        item = dict(
            local_date=None,
            max_temp=None,
            min_temp=None,
            uv_index=None,
            cloud_cover_am=None,
            cloud_cover_pm=None,
            rain_chance_am=None,
            rain_chance_pm=None,
            wind_speed_am=None,
            wind_speed_pm=None,
            scrape_date=None,
            scrape_url=None,
            status=None,
        )
        return item

    def start_requests(self):
        yield Request(
            url=self.api_url,
            method="POST",
            dont_filter=True,
            headers=self.headers,
            body=json.dumps(self.payload),
        )

    def scrape_day(self, data, url):
        # Scrape the temperature data for each day
        for all_day_index, _ in enumerate(range(self.days), start=1):
            item = self.create_item()
            item["scrape_date"] = datetime.now().strftime("%Y-%m-%dT%H:%M")
            item["scrape_url"] = url
            item["status"] = "OK"
            try:
                # Index values
                am_index = all_day_index * 2
                pm_index = am_index + 1
                # Local date time
                item["local_date"] = data["validTimeLocal"][all_day_index][:-8]
                # Max temperature
                item["max_temp"] = data["temperatureMax"][all_day_index]
                # Min temperature
                item["min_temp"] = data["temperatureMin"][all_day_index]
                # UV Index (Day, night is always 0)
                item["uv_index"] = data["daypart"][0]["uvIndex"][am_index]
                # Cloud Coverage (Day/Night)
                item["cloud_cover_am"] = data["daypart"][0]["cloudCover"][am_index]
                item["cloud_cover_pm"] = data["daypart"][0]["cloudCover"][pm_index]
                # Rain chance (Day/Night)
                item["rain_chance_am"] = data["daypart"][0]["precipChance"][am_index]
                item["rain_chance_pm"] = data["daypart"][0]["precipChance"][pm_index]
                # Wind Speed (Day/Night)
                item["wind_speed_am"] = data["daypart"][0]["windSpeed"][am_index]
                item["wind_speed_pm"] = data["daypart"][0]["windSpeed"][pm_index]
                yield item
            # As web scraping can be unpredictable we want to catch any exception
            except Exception as ex:
                # Yield the item with an error message
                item["status"] = f"Failed: {ex}"
                yield item

    def scrape(self, response, data):
        try:
            # Main data
            data = data["dal"]["getSunV3DailyForecastWithHeadersUrlConfig"]
            data = data[
                f"duration:{self.days}day;geocode:{self.latitude},{self.longitude};units:{self.units}"
            ]["data"]
            yield from self.scrape_day(data, response.url)
        except Exception as ex:
            # As web scraping can be unpredictable we want to catch any exception
            self.logger.error(
                "An error ocurred while scraping the main weather data. - %s", ex
            )
            return None

    def parse(self, response):
        try:
            data = json.loads(response.text)
            yield from self.scrape(response, data)
        except (json.JSONDecodeError, TypeError) as ex:
            self.logger.error("An error ocurred while parsing JSON data. - %s", ex)
            return None
