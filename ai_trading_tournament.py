# { "Depends": "py-genlayer:test" }

import json
from genlayer import *


class AITradingTournament(gl.Contract):

    owner: Address
    round_counter: u256
    initialized: bool
    min_round_interval: u256
    last_round_timestamp: u256
    prize_pool: u256
    rollover_pool: u256
    agent_data: DynArray[str]
    trade_history: DynArray[str]
    round_log: DynArray[str]
    bets: DynArray[str]
    winners_data: DynArray[str]
    claimed: DynArray[str]

    def __init__(self, owner_address: Address):
        self.owner = owner_address
        self.round_counter = u256(0)
        self.initialized = False
        self.min_round_interval = u256(300)
        self.last_round_timestamp = u256(0)
        self.prize_pool = u256(0)
        self.rollover_pool = u256(0)

    @gl.public.view
    def get_agent(self, agent_id: str) -> str:
        name = self._aget(agent_id, "name")
        if not name:
            return "Agent not found"
        return (
            f"ID: {agent_id} | "
            f"Name: {name} | "
            f"Personality: {self._aget(agent_id, 'personality')} | "
            f"Cash: ${self._aget(agent_id, 'cash')} | "
            f"BTC: {self._aget(agent_id, 'btc')} | "
            f"ETH: {self._aget(agent_id, 'eth')} | "
            f"SOL: {self._aget(agent_id, 'sol')} | "
            f"BNB: {self._aget(agent_id, 'bnb')} | "
            f"HYPE: {self._aget(agent_id, 'hype')} | "
            f"Portfolio Value: ${self._aget(agent_id, 'portfolio_value')} | "
            f"Trades: {self._aget(agent_id, 'trade_count')} | "
            f"Wins: {self._aget(agent_id, 'wins')} | "
            f"Losses: {self._aget(agent_id, 'losses')}"
        )

    @gl.public.view
    def get_leaderboard(self) -> str:
        if not self.initialized:
            return "Tournament not initialized"
        leaderboard = []
        for i in range(5):
            aid = str(i)
            name = self._aget(aid, "name")
            value = self._aget(aid, "portfolio_value") or "10000"
            leaderboard.append(f"{name}=${value}")
        return f"Round {int(self.round_counter)} | {' | '.join(leaderboard)}"

    @gl.public.view
    def get_round_count(self) -> u256:
        return self.round_counter

    @gl.public.view
    def get_round(self, round_id: str) -> str:
        for i in range(len(self.round_log)):
            entry = self.round_log[i]
            if entry.startswith(f"{round_id}:"):
                return entry[len(round_id) + 1:]
        return "Round not found"

    @gl.public.view
    def get_agent_trades(self, agent_id: str) -> str:
        trades = []
        prefix = f"{agent_id}:"
        for i in range(len(self.trade_history)):
            entry = self.trade_history[i]
            if entry.startswith(prefix):
                trades.append(entry[len(prefix):])
        if not trades:
            return f"No trades for agent {agent_id}"
        return f"Agent {agent_id} has {len(trades)} trades: " + " || ".join(trades[-10:])

    @gl.public.view
    def get_pool_status(self) -> str:
        current_round = int(self.round_counter)
        return (
            f"Current Round: {current_round}\n"
            f"Active Prize Pool: {int(self.prize_pool)} GEN\n"
            f"Rollover Pool: {int(self.rollover_pool)} GEN\n"
            f"Min Interval: {int(self.min_round_interval)} seconds\n"
            f"Last Round Timestamp: {int(self.last_round_timestamp)}"
        )

    @gl.public.view
    def get_bets_for_round(self, round_id: str) -> str:
        total_bets = 0
        bets_per_agent = [0, 0, 0, 0, 0]
        prefix = f"{round_id}:"
        for i in range(len(self.bets)):
            entry = self.bets[i]
            if entry.startswith(prefix):
                parts = entry.split(":")
                if len(parts) >= 4:
                    agent_id = parts[2]
                    amount = int(parts[3])
                    if agent_id.isdigit() and 0 <= int(agent_id) < 5:
                        bets_per_agent[int(agent_id)] += amount
                        total_bets += amount
        result = f"Round {round_id} Bets - Total: {total_bets} GEN"
        for i in range(5):
            name = self._aget(str(i), "name") or f"Agent {i}"
            result += f" | {name}: {bets_per_agent[i]} GEN"
        return result

    @gl.public.view
    def get_my_bets(self, user_address: str) -> str:
        my_bets = []
        for i in range(len(self.bets)):
            entry = self.bets[i]
            parts = entry.split(":")
            if len(parts) >= 5 and parts[1].lower() == user_address.lower():
                my_bets.append(f"R{parts[0]} on Agent {parts[2]}: {parts[3]} GEN")
        if not my_bets:
            return "No bets found"
        return f"User has {len(my_bets)} bet(s): " + " || ".join(my_bets[-20:])

    @gl.public.view
    def get_round_winner(self, round_id: str) -> str:
        winner_data = ""
        for i in range(len(self.winners_data)):
            entry = self.winners_data[i]
            if entry.startswith(f"{round_id}:"):
                winner_data = entry[len(round_id) + 1:]
                break
        if not winner_data:
            return "Round winner not yet determined"
        return f"Round {round_id} winner: {winner_data}"

    @gl.public.view
    def get_summary(self) -> str:
        if not self.initialized:
            return "Tournament not initialized. Call initialize_tournament first."
        total_trades = len(self.trade_history)
        best_agent_id = "0"
        best_value = 0
        for i in range(5):
            aid = str(i)
            value_str = self._aget(aid, "portfolio_value") or "10000"
            try:
                value = int(value_str)
                if value > best_value:
                    best_value = value
                    best_agent_id = aid
            except ValueError:
                pass
        best_name = self._aget(best_agent_id, "name")
        return (
            f"GenLayer AI Trading Tournament - Live Stats\n"
            f"Current Round: {int(self.round_counter)}\n"
            f"Total Trades Executed: {total_trades}\n"
            f"Current Leader: {best_name} with ${best_value}\n"
            f"Active Prize Pool: {int(self.prize_pool)} GEN\n"
            f"Rollover Pool: {int(self.rollover_pool)} GEN\n"
            f"Agents Active: 5"
        )

    @gl.public.write
    def initialize_tournament(self) -> str:
        assert not self.initialized, "Tournament already initialized"

        agents = [
            ("0", "The Hawk", "Aggressive momentum trader who chases high-volatility opportunities. Buys aggressively when trends are strong upward, exits quickly at first sign of reversal. High risk, high reward style."),
            ("1", "The Owl", "Conservative long-term investor focused on blue chips. Prefers holding BTC and ETH, avoids volatile alts. Slow and steady wins the race philosophy."),
            ("2", "The Wolf", "Contrarian trader who buys fear and sells greed. Goes against market sentiment. Loads up when prices crash and takes profit during euphoria."),
            ("3", "The Fox", "Diversification specialist who balances portfolio across all available assets. Never puts more than 30% in any single asset. Reduces risk through spread."),
            ("4", "The Bear", "Bearish skeptic always looking for tops. Prefers staying in cash during uncertainty. Only enters positions with strong conviction of upside."),
        ]

        for agent_id, name, personality in agents:
            self._aset(agent_id, "name", name)
            self._aset(agent_id, "personality", personality)
            self._aset(agent_id, "cash", "10000")
            self._aset(agent_id, "btc", "0.00")
            self._aset(agent_id, "eth", "0.00")
            self._aset(agent_id, "sol", "0.00")
            self._aset(agent_id, "bnb", "0.00")
            self._aset(agent_id, "hype", "0.00")
            self._aset(agent_id, "portfolio_value", "10000")
            self._aset(agent_id, "trade_count", "0")
            self._aset(agent_id, "wins", "0")
            self._aset(agent_id, "losses", "0")

        self.initialized = True
        return "Tournament initialized. 5 agents ready with $10,000 each. Bets can now be placed for Round 0."

    @gl.public.write
    def set_round_interval(self, seconds: str) -> str:
        caller = str(gl.message.sender_address)
        assert caller.lower() == str(self.owner).lower(), "Only owner can change interval"
        new_interval = int(seconds)
        assert new_interval >= 60, "Minimum 60 seconds"
        self.min_round_interval = u256(new_interval)
        return f"Round interval updated to {new_interval} seconds"

    @gl.public.write
    def place_bet(self, agent_id: str) -> str:
        assert self.initialized, "Tournament not initialized"
        assert agent_id in ("0", "1", "2", "3", "4"), "Invalid agent ID"

        bet_amount = int(gl.message.value)
        assert bet_amount > 0, "Must send GEN to place a bet"

        caller = str(gl.message.sender_address)
        current_round = str(int(self.round_counter))

        self.bets.append(f"{current_round}:{caller}:{agent_id}:{bet_amount}:placed")
        self.prize_pool = u256(int(self.prize_pool) + bet_amount)

        agent_name = self._aget(agent_id, "name")
        return f"Bet placed: {bet_amount} GEN on {agent_name} for Round {current_round}. Total pool: {int(self.prize_pool)} GEN."

    @gl.public.write
    def claim_winnings(self, round_id: str) -> str:
        caller = str(gl.message.sender_address)

        winner_data = ""
        for i in range(len(self.winners_data)):
            entry = self.winners_data[i]
            if entry.startswith(f"{round_id}:"):
                winner_data = entry[len(round_id) + 1:]
                break
        assert winner_data, "Round not yet completed"

        parts = winner_data.split("|")
        winner_agent = parts[0].strip()
        prize_per_unit = int(parts[1].strip()) if len(parts) > 1 else 0

        claim_key = f"{round_id}:{caller.lower()}"
        for i in range(len(self.claimed)):
            if self.claimed[i].startswith(claim_key):
                return "Already claimed for this round"

        total_winnings = 0
        prefix = f"{round_id}:"
        for i in range(len(self.bets)):
            entry = self.bets[i]
            if entry.startswith(prefix):
                bet_parts = entry.split(":")
                if len(bet_parts) >= 4:
                    bettor = bet_parts[1]
                    bet_agent = bet_parts[2]
                    bet_amount = int(bet_parts[3])
                    if bettor.lower() == caller.lower() and bet_agent == winner_agent:
                        total_winnings += bet_amount * prize_per_unit

        if total_winnings == 0:
            return "No winnings to claim for this round"

        self.claimed.append(f"{claim_key}:{total_winnings}")
        return f"Claimed {total_winnings} GEN from Round {round_id}."

    @gl.public.write
    def execute_round(self) -> str:
        assert self.initialized, "Tournament not initialized"

        current_time = int(gl.message.block_timestamp) if hasattr(gl.message, 'block_timestamp') else 0
        if int(self.last_round_timestamp) > 0:
            elapsed = current_time - int(self.last_round_timestamp)
            assert elapsed >= int(self.min_round_interval), f"Wait {int(self.min_round_interval) - elapsed} more seconds before next round"

        round_id = str(int(self.round_counter))
        executor = str(gl.message.sender_address)

        old_values = {}
        for i in range(5):
            aid = str(i)
            old_values[aid] = int(self._aget(aid, "portfolio_value") or "10000")

        def leader_fn():
            prices = {"btc": 60000, "eth": 3000, "sol": 150, "bnb": 600, "hype": 30}
            try:
                response = gl.nondet.web.get("https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum,solana,binancecoin,hyperliquid&vs_currencies=usd")
                raw = response.body.decode("utf-8")
                price_data = json.loads(raw)
                prices["btc"] = price_data.get("bitcoin", {}).get("usd", 60000)
                prices["eth"] = price_data.get("ethereum", {}).get("usd", 3000)
                prices["sol"] = price_data.get("solana", {}).get("usd", 150)
                prices["bnb"] = price_data.get("binancecoin", {}).get("usd", 600)
                prices["hype"] = price_data.get("hyperliquid", {}).get("usd", 30)
            except Exception:
                pass

            prompt = f"""You are managing 5 AI trading agents in a tournament. Each agent has a unique personality
and must make trading decisions for this round based on current crypto prices.

CURRENT PRICES:
BTC: ${prices['btc']}
ETH: ${prices['eth']}
SOL: ${prices['sol']}
BNB: ${prices['bnb']}
HYPE: ${prices['hype']}

AGENT 0 - The Hawk (Aggressive momentum trader, high risk high reward)
AGENT 1 - The Owl (Conservative, prefers BTC and ETH only)
AGENT 2 - The Wolf (Contrarian, buys fear sells greed)
AGENT 3 - The Fox (Diversifier, max 30% per asset)
AGENT 4 - The Bear (Skeptic, mostly stays in cash)

For each agent, decide ONE action based on their personality.

Respond ONLY with this JSON:
{{
  "btc_price": {prices['btc']},
  "eth_price": {prices['eth']},
  "sol_price": {prices['sol']},
  "bnb_price": {prices['bnb']},
  "hype_price": {prices['hype']},
  "agent_0": {{"action": "BUY", "asset": "sol", "percentage": 50, "reason": "Strong momentum"}},
  "agent_1": {{"action": "BUY", "asset": "btc", "percentage": 40, "reason": "Long term play"}},
  "agent_2": {{"action": "HOLD", "asset": "none", "percentage": 0, "reason": "Waiting for fear"}},
  "agent_3": {{"action": "BUY", "asset": "eth", "percentage": 20, "reason": "Diversification"}},
  "agent_4": {{"action": "HOLD", "asset": "none", "percentage": 0, "reason": "Market uncertain"}}
}}

action must be exactly BUY, SELL, or HOLD.
asset must be btc, eth, sol, bnb, hype, or none.
percentage is an integer 0 to 100.
No extra text."""

            result = gl.nondet.exec_prompt(prompt)
            clean = result.strip().replace("```json", "").replace("```", "").strip()
            return clean

        def validator_fn(leader_result) -> bool:
            if not isinstance(leader_result, gl.vm.Return):
                return False
            try:
                data = json.loads(leader_result.calldata)
                for agent in ("agent_0", "agent_1", "agent_2", "agent_3", "agent_4"):
                    if agent not in data:
                        return False
                    if data[agent].get("action") not in ("BUY", "SELL", "HOLD"):
                        return False
                for price in ("btc_price", "eth_price", "sol_price", "bnb_price", "hype_price"):
                    if price not in data:
                        return False
                return True
            except Exception:
                return False

        raw = gl.vm.run_nondet_unsafe(leader_fn, validator_fn)
        data = json.loads(raw)

        prices = {
            "btc": data["btc_price"],
            "eth": data["eth_price"],
            "sol": data["sol_price"],
            "bnb": data["bnb_price"],
            "hype": data["hype_price"],
        }

        round_summary = []
        for agent_idx in range(5):
            agent_id = str(agent_idx)
            agent_key = f"agent_{agent_idx}"
            decision = data[agent_key]
            action = decision["action"]
            asset = decision.get("asset", "none")
            percentage = decision.get("percentage", 0)
            reason = decision.get("reason", "")

            cash = float(self._aget(agent_id, "cash") or "10000")
            trade_count = int(self._aget(agent_id, "trade_count") or "0")
            wins = int(self._aget(agent_id, "wins") or "0")
            losses = int(self._aget(agent_id, "losses") or "0")

            trade_record = f"R{round_id}:{action}:{asset}:{percentage}%"

            if action == "BUY" and asset in prices and prices[asset] > 0:
                spend = cash * (percentage / 100.0)
                if spend > 0:
                    asset_amount = float(self._aget(agent_id, asset) or "0")
                    new_amount = asset_amount + (spend / prices[asset])
                    self._aset(agent_id, asset, f"{new_amount:.4f}")
                    self._aset(agent_id, "cash", f"{cash - spend:.2f}")
                    trade_count += 1
                    self._aset(agent_id, "trade_count", str(trade_count))
                    self.trade_history.append(f"{agent_id}:{trade_record} bought ${spend:.2f} of {asset.upper()} - {reason}")
            elif action == "SELL" and asset in prices and prices[asset] > 0:
                asset_amount = float(self._aget(agent_id, asset) or "0")
                sell_amount = asset_amount * (percentage / 100.0)
                if sell_amount > 0:
                    proceeds = sell_amount * prices[asset]
                    self._aset(agent_id, asset, f"{asset_amount - sell_amount:.4f}")
                    self._aset(agent_id, "cash", f"{cash + proceeds:.2f}")
                    trade_count += 1
                    self._aset(agent_id, "trade_count", str(trade_count))
                    self.trade_history.append(f"{agent_id}:{trade_record} sold ${proceeds:.2f} of {asset.upper()} - {reason}")
            else:
                self.trade_history.append(f"{agent_id}:{trade_record} HOLD - {reason}")

            new_cash = float(self._aget(agent_id, "cash") or "10000")
            portfolio_value = new_cash
            for token in ("btc", "eth", "sol", "bnb", "hype"):
                amount = float(self._aget(agent_id, token) or "0")
                portfolio_value += amount * prices[token]

            old_value = old_values[agent_id]
            if portfolio_value > old_value:
                wins += 1
                self._aset(agent_id, "wins", str(wins))
            elif portfolio_value < old_value:
                losses += 1
                self._aset(agent_id, "losses", str(losses))

            self._aset(agent_id, "portfolio_value", f"{int(portfolio_value)}")
            name = self._aget(agent_id, "name")
            round_summary.append(f"{name}: {action} {asset.upper()} ({percentage}%) -> ${int(portfolio_value)}")

        winner_id = "0"
        best_gain = -999999999
        for i in range(5):
            aid = str(i)
            new_value = int(self._aget(aid, "portfolio_value") or "10000")
            gain = new_value - old_values[aid]
            if gain > best_gain:
                best_gain = gain
                winner_id = aid

        winner_name = self._aget(winner_id, "name")

        total_pool = int(self.prize_pool) + int(self.rollover_pool)
        executor_reward = (total_pool * 5) // 100
        winners_pool = total_pool - executor_reward

        winning_bets = 0
        prefix = f"{round_id}:"
        for i in range(len(self.bets)):
            entry = self.bets[i]
            if entry.startswith(prefix):
                parts = entry.split(":")
                if len(parts) >= 4 and parts[2] == winner_id:
                    winning_bets += int(parts[3])

        prize_per_unit = 0
        if winning_bets > 0:
            prize_per_unit = winners_pool // winning_bets
            self.rollover_pool = u256(0)
        else:
            self.rollover_pool = u256(winners_pool)

        self.winners_data.append(f"{round_id}:{winner_id}|{prize_per_unit}|executor={executor}|reward={executor_reward}")
        self.prize_pool = u256(0)

        round_record = (
            f"R{round_id} | Winner: {winner_name} (+${best_gain}) | "
            f"Prices: BTC=${prices['btc']} ETH=${prices['eth']} SOL=${prices['sol']} BNB=${prices['bnb']} HYPE=${prices['hype']} | "
            f"Pool: {total_pool} GEN | Executor Reward: {executor_reward} GEN | "
            + " | ".join(round_summary)
        )
        self.round_log.append(f"{round_id}:{round_record}")
        self.round_counter = u256(int(self.round_counter) + 1)
        self.last_round_timestamp = u256(current_time)

        return f"Round {round_id} executed. Winner: {winner_name} with +${best_gain}. Executor reward: {executor_reward} GEN."

    def _aget(self, agent_id: str, field: str) -> str:
        key = f"{agent_id}_{field}:"
        for i in range(len(self.agent_data)):
            if self.agent_data[i].startswith(key):
                return self.agent_data[i][len(key):]
        return ""

    def _aset(self, agent_id: str, field: str, value: str) -> None:
        key = f"{agent_id}_{field}:"
        for i in range(len(self.agent_data)):
            if self.agent_data[i].startswith(key):
                self.agent_data[i] = f"{key}{value}"
                return
        self.agent_data.append(f"{key}{value}")
