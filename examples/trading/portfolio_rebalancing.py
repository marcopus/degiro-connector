# IMPORTATIONS
import datetime
import json
import logging
import degiro_connector.core.helpers.pb_handler as pb_handler
import pandas as pd

from IPython.display import display
from degiro_connector.trading.api import API as TradingAPI
from degiro_connector.trading.models.trading_pb2 import Credentials, ProductsInfo, TransactionsHistory, Update

# SETUP LOGGING LEVEL
logging.basicConfig(level=logging.WARNING)

# SETUP CONFIG DICT
with open("config/amaliasophia.json") as config_file:
    config_dict = json.load(config_file)

# SETUP CREDENTIALS
int_account = config_dict.get("int_account")
username = config_dict.get("username")
password = config_dict.get("password")

credentials = Credentials(
    int_account=int_account,
    username=username,
    password=password,
)

# SETUP TRADING API
trading_api = TradingAPI(credentials=credentials)

# CONNECT
trading_api.connect()


# SETUP REQUEST TRANSACTIONS
today = datetime.date.today()
from_date = TransactionsHistory.Request.Date(
    year=2021,
    month=1,
    day=1,
)
to_date = TransactionsHistory.Request.Date(
    year=today.year,
    month=today.month,
    day=today.day,
)
request = TransactionsHistory.Request(
    from_date=from_date,
    to_date=to_date,
)

# FETCH DATA TRANSACTIONS
transactions_history = trading_api.get_transactions_history(
    request=request,
    raw=False,
)

# DISPLAY DATA TRANSACTIONS
transactions_df = pd.DataFrame(
    [dict(transaction) for transaction in transactions_history.values]
)
transactions_df = transactions_df.groupby("productId").agg({"quantity": "sum", "total": "sum"})
transactions_df.index = transactions_df.index.astype(int).astype(str)
transactions_df["ratio"] = transactions_df.total/transactions_df.total.sum()


# SETUP REQUEST PRODUCTS INFO
request = ProductsInfo.Request()
request.products.extend([int(id) for id in transactions_df.index])

# FETCH DATA PRODUCTS INFO
products_info = trading_api.get_products_info(
    request=request,
    raw=True,
)
products_info_df = pd.DataFrame(products_info["data"]).transpose()[["name", "isin", "symbol"]]


# SETUP REQUEST PORTFOLIO
request_list = Update.RequestList()
request_list.values.extend(
    [
        Update.Request(option=Update.Option.PORTFOLIO, last_updated=0),
    ]
)

# FETCH DATA PORTFOLIO
update = trading_api.get_update(request_list=request_list, raw=False)
update_dict = pb_handler.message_to_dict(message=update)

# DISPLAY DATA PORTFOLIO
if "portfolio" not in update_dict:
    raise Exception("No portfolio data!")

portfolio_df = pd.DataFrame(update_dict["portfolio"]["values"])
portfolio_df


# PREPARE PORTFOLIO DATA
p = portfolio_df.loc[portfolio_df["positionType"] == "PRODUCT"][["id", "value", "price"]].set_index("id")
p["ratio"] = p.value / p.value.sum()
p = p.merge(transactions_df.ratio, how="inner", left_index=True, right_index=True, suffixes=("_current", "_initial"))
p = p.join(products_info_df)

# CALCULATE PORTFOLIO REBALANCING
cash = portfolio_df.loc[portfolio_df["positionType"] == "CASH",  "value"].sum()
p["buy/sell %"] = (1 - p.ratio_current / p.ratio_initial) * 100
p["buy/sell"] = p["buy/sell %"] / 100 * p.value
p["buy/sell units"] = (p["buy/sell"] / p.price).round().astype(int)
idx_min = p["buy/sell"].idxmin()
new_portfolio_value = p.value[idx_min] / p.ratio_initial[idx_min]
p["buy-only"] = new_portfolio_value * p.ratio_initial - p.value
p["buy-only units"] = (p["buy-only"] / p.price).round().astype(int)
display(p)
print(
    "\n".join((
        "Amount needed for buy-only rebalancing: €{:.2f}".format((p["buy-only units"] * p.price).sum()),
        "Currently available to trade: €{:.2f}".format(cash),
        "Amount needed for deposit €{:.2f}".format((p["buy-only units"] * p.price).sum() - cash),
    ))
)
