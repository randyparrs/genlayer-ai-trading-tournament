# Trader Arena

An AI trading tournament running as an intelligent contract on GenLayer. Five AI agents with distinct personalities compete by trading cryptocurrencies in real time. Players bet on which agent will win each round and share the prize pool.

Live demo: https://genlayer-trader-arena.netlify.app

## What it does

Each round the contract:

1. Fetches live crypto prices from the CoinGecko API using `gl.nondet.web.get`
2. Calls an LLM via `gl.nondet.exec_prompt` so each agent decides to BUY, SELL, or HOLD based on its personality
3. Executes the trades using integer arithmetic and updates each portfolio
4. Determines the winner by portfolio gain and distributes the prize pool to winning bettors

The validator function checks that all validators agree on the AI result before it is written on chain, satisfying GenLayer's Optimistic Democracy consensus.

## The five agents

| ID | Name | Personality |
|----|------|-------------|
| 0 | The Hawk | Aggressive momentum trader |
| 1 | The Owl | Conservative long-term investor |
| 2 | The Wolf | Contrarian, buys fear and sells greed |
| 3 | The Fox | Diversification specialist |
| 4 | The Bear | Bearish skeptic, prefers cash |

Each agent starts with $10,000 and trades BTC, ETH, SOL, BNB, and HYPE.

## Key technical decisions

### Integer arithmetic instead of floats

The first version used floating point operations for the trading logic. This broke consensus because different validators running on different hardware got slightly different results for the same calculation, causing the round to fail.

The fix was to rewrite all trading arithmetic using integers scaled by 10000, where 10000 represents 1.0 unit of any asset:

```python
# BUY: spend dollars, get scaled asset units
spend = cash * percentage // 100
bought_scaled = spend * 10000 // prices[asset]

# SELL: convert scaled units back to dollars
proceeds = sell_scaled * prices[asset] // 10000

# Portfolio value: sum all positions in dollars
portfolio_value += scaled * prices[token] // 10000
```

This guarantees every validator produces the exact same result regardless of hardware or runtime environment.

### Internal block counter for round timing

GenLayer Studio does not expose a reliable block timestamp. To prevent rounds from being executed too frequently, the contract maintains its own `block_counter` that increments on every write call. The minimum interval between rounds is enforced in blocks, with an estimated conversion of 30 seconds per block.

### Rollover pool

If no player bet on the winning agent in a given round, the prize pool rolls over to the next round. This creates larger prize pools over time and incentivizes continued participation.

## Contract methods

### View methods

| Method | Description |
|--------|-------------|
| `get_agent(agent_id)` | Full agent state including portfolio and trade stats |
| `get_leaderboard()` | Current standings for all five agents |
| `get_round(round_id)` | Full log of a completed round |
| `get_agent_trades(agent_id)` | Last 10 trades for an agent |
| `get_bets_for_round(round_id)` | Bet totals per agent for a round |
| `get_my_bets(user_address)` | All bets placed by a user |
| `get_round_winner(round_id)` | Winner and prize per unit for a round |
| `get_round_winning_bets(round_id)` | All winning bettors and their prizes |
| `get_user_profile(user_address)` | Total bets, winnings, and favorite agent |
| `get_pool_status()` | Current prize pool, rollover, and timing info |
| `can_execute_now()` | Whether a new round can be triggered |
| `get_summary()` | Overall tournament stats and current leader |

### Write methods

| Method | Description |
|--------|-------------|
| `initialize_tournament()` | Sets up the five agents with starting portfolios |
| `place_bet(agent_id)` | Bet 1 point on an agent for the current round |
| `execute_round()` | Fetches prices, runs AI decisions, settles the round |
| `claim_winnings(round_id)` | Claims prize points for a winning bet |
| `set_round_interval(seconds)` | Owner only, updates the minimum round interval |

## How to run

1. Open GenLayer Studio
2. Deploy `genlayer-trader-arena.py` with your wallet address as `owner_address`
3. Call `initialize_tournament()` to set up the five agents
4. Call `place_bet(agent_id)` with any agent ID from 0 to 4
5. Call `execute_round()` to trigger a round with live prices and AI decisions
6. Call `get_leaderboard()` to see the standings
7. Call `claim_winnings(round_id)` if your agent won

## Storage

All data is stored in flat `DynArray[str]` arrays using a `key:value` pattern. This avoids the use of `dict` or `list` types which are not valid as GenLayer storage fields.

```
agent_data    -> agent portfolio and trade data
trade_history -> log of every trade executed
round_log     -> summary of every completed round
bets          -> all bets placed by all users
winners_data  -> winner and prize info per round
claimed       -> record of claimed winnings
user_stats    -> executor counts per user
```

## Dependencies

```python
# { "Depends": "py-genlayer:test" }
```

Requires the GenLayer Python SDK.
