# mcc-trader

idea:
ticker_fetch_app will run and save ticks all the time to mongo.

app.py resample - can be used to resample data to proper timeframe

meanwhile app.py run_strategy will work in a loop doing things like:
1. read the data from given grouping range
   - skip last record (always!)
2. get open trades 
    - from DB + confirm with call to kraken? or
    - get order statuses in DB - open/closed/not confirmed
if not confirmed - it waits for some small piece of time and cancels the order?

3. calculate strategy - shall we open/close
- issue new order (closing position, opening position)
- wait until order is confirmed for some time, if it's not - calculate again is it worth it
- when recalculating check if conditions are still met OR check if we can take something from given orders.