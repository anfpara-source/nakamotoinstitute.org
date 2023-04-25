from datetime import timedelta
from decimal import Decimal

import click
import requests
from dateutil import parser
from flask import Blueprint

from app import db
from app.cli.utils import DONE, color_text
from app.models import Price, Skeptic

bp = Blueprint("skeptics", __name__)

bp.cli.help = "Update skeptics."

API_URL_BASE = "https://community-api.coinmetrics.io/v4/timeseries/asset-metrics"
API_URL_PARAMS = "?assets=btc&metrics=PriceUSD&frequency=1d&page_size=10000"
API_URL = API_URL_BASE + API_URL_PARAMS


def fetch_prices(start_date=None, done=True):
    click.echo("Fetching Prices...", nl=False)
    url = API_URL
    if start_date:
        url += f"&start_time={start_date}"
    resp = requests.get(url).json()
    click.echo("Adding Prices...", nl=False)
    series = resp["data"]
    for se in series:
        date = parser.parse(se["time"])
        price = se["PriceUSD"]
        new_price = Price(date=date, price=price)
        db.session.add(new_price)
    db.session.commit()
    if done:
        click.echo(DONE)


def update_skeptics():
    click.echo("Updating skeptics...", nl=False)
    skeptics = db.session.scalars(db.select(Skeptic))

    for skeptic in skeptics:
        filtered_prices = db.session.scalars(
            db.select(Price).filter(Price.date >= skeptic.date)
        ).all()
        date_diff = (
            filtered_prices[-1].date - skeptic.date
        ).days + 1  # Include first day
        total_btc = Decimal("0")
        for price_data in filtered_prices:
            btc = round(Decimal("1") / Decimal(price_data.price), 8)
            total_btc += btc
        usd_value = round(total_btc * Decimal(filtered_prices[-1].price), 2)
        percent_change = round(
            ((Decimal(usd_value) - Decimal(date_diff)) / Decimal(date_diff)) * 100, 2
        )
        skeptic._btc_balance = str(total_btc)
        skeptic._usd_invested = date_diff
        skeptic._usd_value = str(usd_value)
        skeptic._percent_change = str(percent_change)

        db.session.add(skeptic)
    db.session.commit()
    click.echo(DONE)


@bp.cli.command()
def update():
    """Fetch price data and update skeptics."""
    prices = db.session.scalars(db.select(Price)).all()
    start_date = None

    if prices:
        latest = prices[-1]
        start_date = latest.date + timedelta(days=1)

    fetch_prices(start_date=start_date, done=False)

    update_skeptics()
    click.echo(color_text("Finished updating!"))
