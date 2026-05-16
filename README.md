# Trader Arena: AI Trading Tournament on GenLayer

Trader Arena is an on-chain AI trading tournament where five autonomous agents
compete by trading crypto with real market data. It runs as an Intelligent
Contract on [GenLayer](https://genlayer.com) and uses on-chain LLM calls, live web
access and Optimistic Democracy consensus, things a normal smart contract simply
cannot do.

Players bet symbolic points on the agent they think will win the round. The
contract fetches real prices, lets each AI agent make a trading decision, picks a
winner and splits the prize pool among the players who backed it.

## Live Deployment

| Item | Value |
|------|-------|
| Network | GenLayer Studio (chain `61999`) |
| Contract address | `0xA3af2C172615871e285012976A1A65914882a314` |
| Frontend repo | https://github.com/randyparrs/genlayer-trader-arena-frontend |

## Why GenLayer

A standard smart contract is deterministic and isolated. It cannot run AI models
and it cannot reach the internet. Trader Arena needs both, and that is exactly
what GenLayer Intelligent Contracts make possible:

- **On-chain LLM calls.** Every round the contract calls `gl.nondet.exec_prompt`
  so an LLM produces the trading decision for all five agents based on their
  personalities.
- **Live web access.** The contract reads current crypto prices straight from the
  CoinGecko API with `gl.nondet.web.get`, from inside on-chain code.
- **Optimistic Democracy.** The non-deterministic AI output is wrapped in
  `gl.vm.run_nondet_unsafe` together with a validator function, so several
  validators independently verify the result before it is accepted.

## The Agents

Five agents start the tournament with $10,000 each. Every agent has its own
trading personality, and that personality is fed into the LLM prompt:

| ID | Agent | Strategy |
|----|-------|----------|
| 0 | The Hawk | Aggressive momentum trader chasing high-volatility opportunities |
| 1 | The Owl | Conservative long-term investor focused on blue chips |
| 2 | The Wolf | Contrarian trader who buys fear and sells greed |
| 3 | The Fox | Diversification specialist |
| 4 | The Bear | Bearish skeptic that prefers staying in cash |

Tradable assets are BTC, ETH, SOL, BNB and HYPE.

## How a Round Works

1. Players call `place_bet` to back an agent. Each bet costs 1 point and you can
   bet multiple times to raise your stake.
2. Once enough time has passed, anyone can call `execute_round`.
3. The contract fetches live prices from CoinGecko.
4. An LLM produces a BUY, SELL or HOLD decision for each agent.
5. A validator function checks the AI output and validators reach consensus.
6. Each agent portfolio is recalculated and the agent with the best gain wins.
7. The prize pool is split among the players who backed the winner. The executor
   earns 5% of the pool. If nobody backed the winner, the pool rolls over to the
   next round.

## Round Timing

GenLayer Studio does not expose a reliable block timestamp, so round timing is
handled with an internal `block_counter` that increments on every write call.
`min_round_interval` (300 seconds by default) controls how long to wait between
rounds, and `can_execute_now` returns either `READY:0` or `WAIT:<seconds>` so the
frontend can show a live countdown.

## Deterministic Arithmetic

All math in the contract uses integers, never floats, because every validator has
to reach the exact same result for consensus to hold. Asset balances are stored as
integers scaled by 10,000 (so `10000` means 1.0 unit) and the `_fmt_asset` helper
formats them for display.

## Contract Interface

### Write methods

| Method | Description |
|--------|-------------|
| `initialize_tournament()` | Sets up the 5 agents. Call once after deploy |
| `place_bet(agent_id)` | Bet 1 point on an agent (`"0"` to `"4"`) |
| `execute_round()` | Run a round: fetch prices, AI decides, distribute pool |
| `claim_winnings(round_id)` | Claim your share of a finished round |
| `set_round_interval(seconds)` | Owner only. Change the wait time between rounds |

### View methods

| Method | Description |
|--------|-------------|
| `get_leaderboard()` | Current portfolio value of every agent |
| `get_agent(agent_id)` | Full detail for one agent |
| `get_pool_status()` | Prize pool, rollover, round and timing info |
| `can_execute_now()` | Whether a round can run yet (`READY` or `WAIT`) |
| `get_round(round_id)` | Detailed log of a past round |
| `get_round_count()` | Total rounds played |
| `get_active_bets_summary()` | Bets placed in the current round |
| `get_bets_for_round(round_id)` | Bets for a specific round |
| `get_my_bets(address)` | Betting history for an address |
| `get_user_profile(address)` | Aggregate stats for a player |
| `get_round_winner(round_id)` | Winner of a finished round |
| `get_round_winning_bets(round_id)` | Per-player payout for a finished round |
| `get_agent_trades(agent_id)` | Recent trades made by an agent |
| `get_summary()` | High-level tournament stats |

## Deploy and Test

The contract has two constructor variants. The Studio version takes
`owner_address` as a string and wraps it with `Address(owner_address)`, because
Studio passes the constructor argument as a primitive string. The GitHub version
takes `owner_address` directly as an `Address`, which is what the `genvm-lint`
toolchain expects.

The contract lives in `genlayer-trader-arena.py`. Steps to deploy on GenLayer
Studio:

1. Open [GenLayer Studio](https://studio.genlayer.com) and paste the contents of
   `genlayer-trader-arena.py`.
2. Deploy in Normal Full Consensus mode and pass your wallet as `owner_address`.
3. Call `initialize_tournament()` once.
4. Call `place_bet("0")` to add to the prize pool.
5. Optionally call `set_round_interval("60")` to shorten the wait while testing.
6. Wait for the interval and then call `execute_round()`.
7. Read `get_leaderboard()` to see the updated standings.

## Tech Stack

- Python Intelligent Contract on GenLayer (`py-genlayer:test`)
- `gl.nondet.exec_prompt` for AI agent decisions
- `gl.nondet.web.get` against the CoinGecko API for live prices
- `gl.vm.run_nondet_unsafe` with a JSON validating validator function
- React, Vite and genlayer-js frontend ([repo](https://github.com/randyparrs/genlayer-trader-arena-frontend))

## License

MIT
