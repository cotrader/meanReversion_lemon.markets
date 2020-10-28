import requests
from lemon_markets.token import Token
from lemon_markets.order import Order
import statistics
import datetime
from datetime import timedelta
import time


def seconds_till_market_opens(entered_time):
    if entered_time.weekday() in range(0, 4):
        d = (entered_time + timedelta(days=1)).date()
    else:
        days_till_market_opens = 0 - time.weekday() + 7
        d = (entered_time + timedelta(days=days_till_market_opens)).date()
    # slightly later than actual market open time to avoid unstable market
    next_day = datetime.datetime.combine(d, datetime.time(10, 30))
    seconds = (next_day - entered_time).total_seconds()  # number of seconds until market reopens
    return seconds  # we can then later combine this function with the time.sleep()-function to determine
    # how long we need to wait until our next execution


def mean_reversion():
    while True:
        # initialize market_open variable
        market_open = False
        # check if market is open
        # we only execute our algo on weekdays (i.e. Mon-Fri).
        # Feel free to change the code so it also runs on weekends or only on specific days
        # works for Central European timezone (CET; Berlin, Paris, Rome and so on).
        # Please alter for yourself if you need a different timezone
        current_day_time = datetime.datetime.now()
        if current_day_time.weekday() in range(0, 4):
            if current_day_time.hour in range(8, 23):
                print('market open, order creation possible')
                market_open = True
            else:
                print('market currently not open, checking again soon')
                market_open = False
                time.sleep(seconds_till_market_opens(datetime.datetime.now()))  # sleep until market reopens

        # if market is open, execute mean reversion strategy
        if market_open:
            # insert your desired token here
            my_token = Token("YOUR_TOKEN_HERE")
            # access the account related to that token
            my_account = my_token.account
            # specify your instrument
            instrument = "US88160R1014"  # this is TESLA, Inc. but you can obviously set any ISIN you want
            # set the current time
            current_time = int(time.time())
            # specify the period you wish to base the mean reversion on (e.g. 2 weeks, as in our example)
            start_time_mean_reversion = int(time.time() - 604800)
            # specify the params for your data request
            request_params = {'date_from': start_time_mean_reversion, 'date_until': current_time}
            try:
            # get the m1 data for your desired period
                m1_data = requests.get("https://api.lemon.markets/rest/v1/data/instruments/US88160R1014/candle/m1/",
                                       params=request_params)
                # transform the response results to json format
                m1_data_json_results = m1_data.json()["results"]
                # get average high value from the period you specified
                prices_high = [x["high"] for x in m1_data_json_results]  # you can obviously change that to low, close or open
                # this is your mean high price over the specified period
                mean_price = statistics.mean(prices_high)
                print('Mean price:', mean_price)
                # get the latest price for your instrument
                m1_data_latest = requests.get("https://api.lemon.markets/rest/v1/data/instruments/US88160R1014/candle/m1"
                                              "/latest", params=request_params)
                m1_latest_high = m1_data_latest.json()["high"]
                print('Lates Price:', m1_latest_high)
                # get portfolio items for specific ISIN
                portfolio_items = requests.get("https://api.lemon.markets/rest/v1/accounts/{}/"
                                               "portfolio/{}/aggregated/".format(my_account, instrument),
                                               headers={"Authorization": "Token {}".format(my_token)}
                                               )
                # check number of portfolio items for specific instrument
                if len(portfolio_items.json()) == 0:
                    # set number of portfolio items = 0
                    number_items = 0
                else:
                    # get number of portfolio items for specific ISIN
                    number_items = portfolio_items.json()["quantity"]
                # get cash to invest for account
                cash_to_invest = my_account.cash_in_invest
                # this is a very simple "if price lower than mean value: buy, else sell" strategy.
                # Feel free to make it more complex ;)
                if m1_latest_high < mean_price:

                    # this is a buffer so we do not get into "purchasing trouble".
                    # change value if your buy quantity > 1
                    if cash_to_invest > 2 * m1_latest_high:
                        # specify your order (you can also add a limit/stop price and change the instrument or how long
                        # you want your order to be valid
                        # important is that your side is "buy", as in a mean reversion strategy we assume that prices will
                        # converge towards the mean value eventually, meaning that we buy if the current price is lower
                        # than the mean and sell if it is higher
                        new_order = Order(
                            instrument=instrument,
                            quantity=1,
                            side="buy",
                            valid_until=datetime.datetime.now() + datetime.timedelta(days=1),
                            account=my_account
                        )
                        # place your order
                        new_order.create()
                        print("instrument bought")
                        print('Sleeping', round(seconds_till_market_opens(datetime.datetime.now()) / 60 / 60, 2), 'hours')
                        time.sleep(seconds_till_market_opens(datetime.datetime.now()))  # execute again the next day
                    else:
                        print('not enough cash to buy instrument')
                        time.sleep(seconds_till_market_opens(datetime.datetime.now()))  # check again tomorrow
                # if the current price is higher than the mean price, enter else clause of function.
                else:
                    # we can only sell shares if we have more than one ;)
                    if number_items >= 1:
                        new_order = Order(
                            instrument=instrument,
                            quantity=1,
                            side="sell",
                            valid_until=datetime.datetime.now() + datetime.timedelta(days=1),
                            account=my_account
                        )
                        # place your order
                        new_order.create()
                        print("instrument sold")
                        print('Sleeping', round(seconds_till_market_opens(datetime.datetime.now()) / 60 / 60, 2), 'hours')
                        time.sleep(seconds_till_market_opens(datetime.datetime.now()))  # execute again the next day
                    else:
                        print('not enough portfolio items to sell')
                        print('Sleeping', round(seconds_till_market_opens(datetime.datetime.now()) / 60 / 60, 2), 'hours')
                        time.sleep(seconds_till_market_opens(datetime.datetime.now()))  # execute again the next day
            except Exception as e:
                print('Cannot process order right now', e)
                print('Sleeping', round(seconds_till_market_opens(datetime.datetime.now()) / 60 / 60, 2), 'hours')
                time.sleep(seconds_till_market_opens(datetime.datetime.now()))  # execute again the next day
        # if market is not open, stop code until it reopens
        else:
            print('Market not open. Sleeping', round(seconds_till_market_opens(datetime.datetime.now()) / 60 / 60, 2),
                  'hours')
            time.sleep(seconds_till_market_opens(datetime.datetime.now()))  # execute again the next day


def execute_order():
    try:
        mean_reversion()
    except Exception:
        print('Cannot process order right now')
        time.sleep(60)


mean_reversion()
