from ibapi.wrapper import EWrapper

class IBWrapper(EWrapper):
    def __init__(self):
        EWrapper.__init__(self)
        self.historical_data = {}
        self.market_data = {}
        self.nextValidOrderID = None
        self.account_values = {}
        self.positions = {}
        self.account_pnl = {}
        self.portfolio_returns = None
    
    def historicalData(self, reqId, bar):
        bar_data = (bar.date, bar.open, bar.high,
                    bar.low, bar.close, bar.volume)
        if reqId not in self.historical_data.keys():
            self.historical_data[reqId] = []
        self.historical_data[reqId].append(bar_data)

    def nextValidId(self, orderId):
        super().nextValidId(orderId)
        self.nextValidOrderID = orderId

    def orderStatus(self, order_id, status, filled, remaining,
                    avg_fill_price, perm_id, parent_id,
                    last_fill_price, client_id, why_held, mkt_cap_price):
        print(f"order: {order_id} status: {status} filled: {filled} remaining: {remaining} last fill price: {last_fill_price}")
    
    def openOrder(self, order_id, contract, order, order_state):
        print(f"openOrder id: {order_id} {contract.symbol} {contract.secType} @ {contract.exchange}: {order.action} {order.orderType} {order.totalQuantity} {order_state.status}")
    def execDetails(self, reqId, contract, execution):
        print(f"Order Executed: {reqId} {contract.symbol} {contract.secType} {contract.currency} {execution.execId} {execution.orderId} {execution.shares} {execution.lastLiquidity}")
    
    def updateAccountValue(self, key, val, currency, accountName):
        try:
            val_ = float(val)
        except:
            val_ = val
        self.account_values[key] = (val_, currency)
    
    def updatePortfolio(self, contract, position, market_price, market_value, 
                        average_cost, unrealized_pnl, realized_pnl, account_name):
        portfolio_data = {
            "contract": contract,
            "symbol": contract.symbol,
            "position": position,
            "market_price": market_price,
            "market_value": market_value,
            "average_cost": average_cost,
            "unrealized_pnl": unrealized_pnl,
            "realized_pnl": realized_pnl
        }
        self.positions[contract.symbol] = portfolio_data
    def pnl(self, request_id, daily_pnl, unrealized_pnl, realized_pnl):
        pnl_data = {
            "daily_pnl": daily_pnl,
            "unrealized_pnl": unrealized_pnl,
            "realized_pnl": realized_pnl
        }
        self.account_pnl[request_id] = pnl_data
    