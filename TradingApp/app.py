import os
import sqlite3
import threading
import time
import empyrical as ep
import exchange_calendars as xcals
import numpy as np
import pandas as pd
from dotenv import load_dotenv
from zipline.data import bundles
from zipline.data.bundles.core import load
from zipline.pipeline import Pipeline
from zipline.pipeline.data import USEquityPricing
from zipline.pipeline.engine import SimplePipelineEngine
from zipline.pipeline.factors import AverageDollarVolume,CustomFactor, Returns
from zipline.pipeline.loaders import USEquityPricingLoader
from zipline.utils.run_algo import load_extensions

from client import IBClient
from contract import stock
from order import market
from wrapper import IBWrapper

load_dotenv()


class IBApp(IBWrapper, IBClient):
    def __init__(self,ip,port, client_id, account,interval=5):
        IBWrapper.__init__(self)
        IBClient.__init__(self,wrapper=self)
        self.connect(ip,port, client_id)
        self.account = account
        threading.Thread(target= self.run, daemon= True).start()
        time.sleep(10)
        # threading.Thread(target=self.get_streaming_returns, args=(99, interval, "unrealized_pnl"), daemon=True).start()

    @property
    def cumulative_returns(self):
        return ep.cum_returns(self.portfolio_returns,1)
    @property
    def volatility(self):
        return self.portfolio_returns.std(ddof=1)
    @property
    def max_drawdown(self):
        return ep.max_drawdown(self.portfolio_returns)
    @property
    def sharpeRatio(self):
        return self.portfolio_returns.mean() / self.portfolio_returns.std(ddof=1)
    @property
    def omega_ratio(self):
        return ep.omega_ratio(self.portfolio_returns,annualization=1)
    @property
    def cvar(self):
        net_liquidation = self.get_account_values("NetLiquidation")[0]
        cvar_ = ep.conditional_value_at_risk(self.portfolio_returns)
        return (cvar_, cvar_ * net_liquidation)

class MomentumFactor(CustomFactor):
    inputs = [USEquityPricing.close, Returns(window_length=126)]
    window_length = 252
    def compute(self, today, assets, out, prices, returns):
        out[:] = ( (prices[-21] - prices[-252]) / prices[-252]
                  - (prices[-1] - prices[-21]) / prices[-21] )/np.nanstd(returns, axis=0)

def make_pipeline():
    momentum = MomentumFactor()
    return Pipeline(columns={
    "factor": momentum, "longs": momentum.top(num_longs),
    "shorts": momentum.bottom(num_shorts), "ranking": momentum.rank(ascending=False)}
    )        

if __name__ == "__main__":
    app = IBApp("127.0.0.1", 7497, client_id= 12, account="DUH104164")
    num_longs = num_shorts = 10
    xnys = xcals.get_calendar("XNYS")
    today = "2025-01-03"
    start_date = xnys.session_offset(today, count=-252).strftime("%Y-%m-%d")

    load_extensions(True, [], False, os.environ)
    bundles.ingest("quotemedia")
    bundle_data = load("quotemedia", os.environ, None)
    pipeline_loader = USEquityPricingLoader(
        bundle_data.equity_daily_bar_reader,
        bundle_data.adjustment_reader,
        fx_reader=None,
    )

    engine = SimplePipelineEngine(
        get_loader=lambda col: pipeline_loader, asset_finder=bundle_data.asset_finder
    )
    results = engine.run_pipeline(make_pipeline(), start_date, today)
    results.dropna(subset="factor", inplace=True)
    results.index.names = ["date", "symbol"]
    results.sort_values(by=["date", "factor"], inplace=True)
    longs = results.xs(today, level=0).query("longs == True")
    shorts = results.xs(today, level=0).query("shorts == True")
    weight = 1 / num_longs / 2
    print(f"Longs at weight {weight}:\n",longs)
    print(f"Shorts at weight {weight}:\n",shorts)
    time.sleep(30)
    app.disconnect()
