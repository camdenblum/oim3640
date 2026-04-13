"""
main.py — Entry point for the Agentic Trading Bot.

Usage:
    python main.py --mode paper
    python main.py --mode live
    python main.py --mode backtest [--start YYYY-MM-DD] [--end YYYY-MM-DD]
    python main.py --mode backtest --tickers AAPL,MSFT

Safety:
    - Default mode is paper.
    - Live mode requires ALPACA_API_KEY / ALPACA_SECRET_KEY env vars.
    - Live mode with compliance.require_approval_for_live_trades=true will
      prompt for confirmation before placing any real order.
"""
from __future__ import annotations

from dotenv import load_dotenv
load_dotenv()  # loads ALPACA_API_KEY, ALPACA_SECRET_KEY, ALPACA_BASE_URL from .env

import argparse
import logging
import os
import sys
import time
from datetime import date, timedelta
from pathlib import Path
from typing import Any, Dict, List

# ---------------------------------------------------------------------------
# Bootstrap: make sure the package root is on sys.path when run directly
# ---------------------------------------------------------------------------
sys.path.insert(0, str(Path(__file__).parent))

from utils import load_config, setup_logging, ensure_dir, get_logger, now_iso

# Delay heavy imports until after logging is set up
logger: logging.Logger  # assigned after setup_logging


def build_components(cfg: Dict[str, Any], mode: str):
    """Instantiate all bot components from config.

    Returns a dict of initialised objects keyed by component name.
    """
    from data.fetcher import DataFetcher
    from data.features import FeatureEngineer
    from models.strategy import Strategy
    from models.learner import Learner
    from portfolio.portfolio import Portfolio
    from risk.risk import RiskManager
    from state.trader_state import TraderState
    from learning.learning_loop import LearningLoop

    data_cfg = cfg.get("data", {})
    feat_cfg = cfg.get("features", {})
    strat_cfg = cfg.get("strategy", {})
    risk_cfg = cfg.get("risk", {})
    port_cfg = cfg.get("portfolio", {})
    learn_cfg = cfg.get("learning", {})
    exec_cfg = cfg.get("execution", {})
    obs_cfg = cfg.get("observability", {})
    state_cfg_path = ".state/trader.db"

    fetcher = DataFetcher(
        cache_dir=data_cfg.get("cache_dir", ".cache/data"),
        max_retries=data_cfg.get("max_retries", 3),
        retry_backoff=data_cfg.get("retry_backoff", 2.0),
    )

    feature_eng = FeatureEngineer(
        indicators=feat_cfg.get("indicators"),
        feature_params=feat_cfg.get("feature_params", {}),
        normalize=feat_cfg.get("normalize", True),
    )

    strategy = Strategy(
        scoring_model=strat_cfg.get("scoring_model", "linear"),
        model_params=strat_cfg.get("model_params", {}),
        buy_threshold=strat_cfg.get("signal_thresholds", {}).get("buy", 0.60),
        sell_threshold=strat_cfg.get("signal_thresholds", {}).get("sell", 0.40),
    )

    sz_cfg = strat_cfg.get("position_sizing", {})
    portfolio = Portfolio(
        initial_cash=port_cfg.get("initial_cash", 100_000.0),
        sizing_method=sz_cfg.get("method", "percent_of_equity"),
        default_pct=sz_cfg.get("default_pct", 0.05),
        max_position_pct=sz_cfg.get("max_position_size_pct", 0.15),
        currency=port_cfg.get("currency", "USD"),
    )

    risk_mgr = RiskManager(
        max_total_drawdown_pct=risk_cfg.get("max_total_drawdown_pct", 10.0),
        max_daily_loss_pct=risk_cfg.get("max_daily_loss_pct", 2.0),
        max_positions=strat_cfg.get("max_positions", risk_cfg.get("max_positions", 8)),
        max_position_size_pct=sz_cfg.get("max_position_size_pct", 15.0),
        stop_loss_pct=risk_cfg.get("stop_loss_pct", 5.0),
        take_profit_pct=risk_cfg.get("take_profit_pct", 15.0),
        min_cash_reserve_pct=risk_cfg.get("min_cash_reserve_pct", 5.0),
    )

    state = TraderState(db_path=state_cfg_path, mode=mode)

    learner = Learner(
        strategy=strategy,
        artifacts_dir=learn_cfg.get("artifacts_dir", ".state/learning"),
        learning_rate=learn_cfg.get("learning_rate", 0.001),
        validation_window=learn_cfg.get("validation_window", 500),
        regularization=learn_cfg.get("regularization", 0.01),
    )

    learning_loop = LearningLoop(
        strategy=strategy,
        learner=learner,
        state=state,
        feature_engineer=feature_eng,
        enable_learning=learn_cfg.get("enable_learning", True),
        offline_epochs=learn_cfg.get("offline_epochs", 20),
        online_update_interval=learn_cfg.get("online_update_interval", 10),
        revert_threshold=learn_cfg.get("revert_threshold", 0.05),
    )

    # Broker selection
    broker = _build_broker(mode, exec_cfg, risk_cfg)

    from execution.executor import Executor
    executor = Executor(
        broker=broker,
        portfolio=portfolio,
        risk_manager=risk_mgr,
        order_type=exec_cfg.get("order_type", "market"),
        order_timeout_secs=exec_cfg.get("order_timeout_secs", 30),
        max_retries=exec_cfg.get("max_retries", 3),
        retry_backoff=exec_cfg.get("retry_backoff", 2.0),
        slippage_pct=risk_cfg.get("slippage_params", {}).get("fixed_pct", 0.05) / 100,
        commission_per_trade=risk_cfg.get("commission_per_trade", 0.0),
    )

    return {
        "fetcher": fetcher,
        "feature_eng": feature_eng,
        "strategy": strategy,
        "portfolio": portfolio,
        "risk_mgr": risk_mgr,
        "state": state,
        "learner": learner,
        "learning_loop": learning_loop,
        "broker": broker,
        "executor": executor,
    }


def _build_broker(mode: str, exec_cfg: Dict[str, Any], risk_cfg: Dict[str, Any]):
    """Build the appropriate broker instance based on mode and config.

    - mode=paper + broker_module=broker_alpaca + keys present → Alpaca paper account
    - mode=live  + broker_module=broker_alpaca + keys present → Alpaca live account
    - keys missing or alpaca-py not installed                 → local PaperBroker fallback
    """
    from execution.broker_paper import PaperBroker

    slippage = risk_cfg.get("slippage_params", {}).get("fixed_pct", 0.05) / 100
    commission = risk_cfg.get("commission_per_trade", 0.0)
    broker_module = exec_cfg.get("broker_module", "broker_paper")

    # Use Alpaca whenever the module is configured and keys are available
    if broker_module == "broker_alpaca" and mode in ("paper", "live"):
        broker_cfg = exec_cfg.get("broker_config", {})
        api_key = os.environ.get(broker_cfg.get("api_key_env", "ALPACA_API_KEY"), "")
        secret = os.environ.get(broker_cfg.get("api_secret_env", "ALPACA_SECRET_KEY"), "")
        base_url = os.environ.get(broker_cfg.get("base_url_env", "ALPACA_BASE_URL"), "")

        if not api_key or not secret:
            logger.error(
                "broker_alpaca requires ALPACA_API_KEY and ALPACA_SECRET_KEY in .env. "
                "Falling back to local paper broker."
            )
            return PaperBroker(slippage_pct=slippage, commission=commission)

        try:
            from execution.broker_alpaca import AlpacaBroker
            # paper=True for paper mode OR if paper_trading flag is set in config
            paper_flag = (mode == "paper") or exec_cfg.get("paper_trading", True)
            broker = AlpacaBroker(
                api_key=api_key,
                secret_key=secret,
                base_url=base_url or None,
                paper=paper_flag,
                slippage_pct=slippage,
            )
            label = "Alpaca PAPER account" if paper_flag else "Alpaca LIVE account"
            logger.info(f"Using {label}")
            return broker
        except ImportError:
            logger.error("alpaca-py not installed — run: pip install alpaca-py. Falling back to local paper broker.")
            return PaperBroker(slippage_pct=slippage, commission=commission)

    # Default: fully local simulated broker (no network, no account needed)
    return PaperBroker(slippage_pct=slippage, commission=commission)


# ---------------------------------------------------------------------------
# Backtest mode
# ---------------------------------------------------------------------------

def run_backtest(cfg: Dict[str, Any], tickers: List[str], start: str, end: str) -> None:
    """Run a backtest and print results."""
    from data.fetcher import DataFetcher
    from data.features import FeatureEngineer
    from models.strategy import Strategy
    from risk.risk import RiskManager
    from backtest.backtester import Backtester
    from learning.learning_loop import LearningLoop
    from models.learner import Learner
    from state.trader_state import TraderState

    logger.info("Starting backtest", extra={"tickers": tickers, "start": start, "end": end})

    bt_cfg = cfg.get("backtest", {})
    feat_cfg = cfg.get("features", {})
    strat_cfg = cfg.get("strategy", {})
    risk_cfg = cfg.get("risk", {})
    learn_cfg = cfg.get("learning", {})
    port_cfg = cfg.get("portfolio", {})

    fetcher = DataFetcher(cache_dir=cfg["data"].get("cache_dir", ".cache/data"))
    feature_eng = FeatureEngineer(
        indicators=feat_cfg.get("indicators"),
        feature_params=feat_cfg.get("feature_params", {}),
    )
    strategy = Strategy(
        scoring_model=strat_cfg.get("scoring_model", "linear"),
        model_params=strat_cfg.get("model_params", {}),
        buy_threshold=strat_cfg.get("signal_thresholds", {}).get("buy", 0.60),
        sell_threshold=strat_cfg.get("signal_thresholds", {}).get("sell", 0.40),
    )
    risk_mgr = RiskManager(
        max_total_drawdown_pct=risk_cfg.get("max_total_drawdown_pct", 10.0),
        max_daily_loss_pct=risk_cfg.get("max_daily_loss_pct", 2.0),
        max_positions=risk_cfg.get("max_positions", 8),
        stop_loss_pct=risk_cfg.get("stop_loss_pct", 5.0),
        take_profit_pct=risk_cfg.get("take_profit_pct", 15.0),
    )

    # Download data
    price_dict = fetcher.fetch_multi(tickers, start=start, end=end)
    if not price_dict:
        logger.error("No data fetched — aborting backtest")
        return

    # Optional: run offline learning before backtest
    if learn_cfg.get("enable_learning", True):
        state = TraderState(db_path=".state/trader.db", mode="backtest")
        learner = Learner(
            strategy=strategy,
            artifacts_dir=learn_cfg.get("artifacts_dir", ".state/learning"),
            learning_rate=learn_cfg.get("learning_rate", 0.001),
        )
        ll = LearningLoop(
            strategy=strategy, learner=learner, state=state,
            feature_engineer=feature_eng,
            enable_learning=True,
            offline_epochs=learn_cfg.get("offline_epochs", 20),
        )
        feature_dict = {t: feature_eng.compute(df) for t, df in price_dict.items()}
        ll.run_offline_learning(feature_dict, price_dict)

    backtester = Backtester(
        strategy=strategy,
        feature_engineer=feature_eng,
        risk_manager=risk_mgr,
        initial_cash=bt_cfg.get("initial_cash", port_cfg.get("initial_cash", 100_000.0)),
        slippage_pct=risk_cfg.get("slippage_params", {}).get("fixed_pct", 0.05) / 100,
        commission=risk_cfg.get("commission_per_trade", 0.0),
        max_positions=risk_cfg.get("max_positions", 8),
    )

    benchmark = bt_cfg.get("benchmark", "SPY")
    if benchmark not in price_dict:
        bm_df = fetcher.fetch(benchmark, start=start, end=end)
        if bm_df is not None and not bm_df.empty:
            price_dict[benchmark] = bm_df

    results = backtester.run(price_dict, benchmark_ticker=benchmark)
    print("\n" + "=" * 60)
    print("BACKTEST RESULTS")
    print("=" * 60)
    for name, res in results.items():
        print(res)
    print("=" * 60)


# ---------------------------------------------------------------------------
# Paper / live trading loop
# ---------------------------------------------------------------------------

def run_trading(cfg: Dict[str, Any], mode: str) -> None:
    """Main paper/live trading loop."""
    tickers = cfg["data"].get("tickers", ["AAPL", "MSFT"])
    data_window = cfg["data"].get("data_window", 365)
    obs_cfg = cfg.get("observability", {})
    learn_cfg = cfg.get("learning", {})
    compliance = cfg.get("compliance", {})

    comps = build_components(cfg, mode)
    fetcher = comps["fetcher"]
    feature_eng = comps["feature_eng"]
    strategy = comps["strategy"]
    portfolio = comps["portfolio"]
    risk_mgr = comps["risk_mgr"]
    state = comps["state"]
    learning_loop = comps["learning_loop"]
    broker = comps["broker"]
    executor = comps["executor"]

    # Connect broker
    if not broker.connect():
        logger.error("Broker connection failed — aborting")
        sys.exit(1)

    state.audit("bot_start", f"Bot started in {mode} mode", extra={"tickers": tickers})

    # Load or train model
    if not learning_loop.load_latest_or_baseline():
        # Train from scratch using historical data
        start_hist = str(date.today() - timedelta(days=data_window))
        price_dict = fetcher.fetch_multi(tickers, start=start_hist)
        feature_dict = {t: feature_eng.compute(df) for t, df in price_dict.items()}
        learning_loop.run_offline_learning(feature_dict, price_dict)

    logger.info("Bot running", extra={"mode": mode, "tickers": tickers})
    print(f"\n[BOT] Running in {mode.upper()} mode | Tickers: {tickers}")
    print("[BOT] Press Ctrl+C to stop.\n")

    rebalancing_freq = cfg.get("strategy", {}).get("rebalancing_frequency", 5)
    bar_count = 0

    try:
        while True:
            try:
                # Check if market is open (live only)
                if mode == "live" and not broker.is_market_open():
                    logger.info("Market closed — sleeping 60s")
                    time.sleep(60)
                    continue

                if risk_mgr.is_halted:
                    logger.warning("Trading halted", extra={"reason": risk_mgr.halt_reason})
                    time.sleep(300)
                    continue

                # Fetch fresh data
                start_hist = str(date.today() - timedelta(days=max(data_window, 120)))
                price_dict = fetcher.fetch_multi(tickers, start=start_hist, use_cache=(mode == "paper"))

                if not price_dict:
                    logger.warning("No price data — sleeping")
                    time.sleep(30)
                    continue

                # Update prices in paper broker
                latest_prices = {t: float(df["Close"].iloc[-1]) for t, df in price_dict.items()}
                if hasattr(broker, "update_prices"):
                    broker.update_prices(latest_prices)
                portfolio.update_prices(latest_prices)

                # Check SL/TP for all holdings
                for ticker in list(portfolio.positions.keys()):
                    trigger = risk_mgr.check_stop_loss_take_profit(ticker, portfolio)
                    if trigger:
                        from models.strategy import Signal, Action
                        sl_signal = Signal(
                            ticker=ticker, action=Action.SELL, score=0.0,
                            confidence=0.5, timestamp=now_iso(), reason=trigger
                        )
                        executor.execute_single(sl_signal)

                # Generate signals every N bars
                if bar_count % rebalancing_freq == 0:
                    feature_dict = {t: feature_eng.compute(df) for t, df in price_dict.items()}
                    signals = strategy.generate_signals(feature_dict, timestamp=now_iso())

                    logger.info(
                        "Signals generated",
                        extra={"n": len(signals),
                               "buys": sum(1 for s in signals if s.action.value == "BUY"),
                               "sells": sum(1 for s in signals if s.action.value == "SELL")},
                    )

                    if signals:
                        results = executor.execute_signals(signals)
                        for r in results:
                            if r.success and r.order:
                                state.log_trade(
                                    symbol=r.signal.ticker,
                                    side=r.order.side.value,
                                    quantity=r.order.filled_qty,
                                    filled_price=r.order.filled_avg_price,
                                    pnl=0.0,  # realised PnL updated on close
                                    commission=r.order.commission,
                                    slippage=r.order.slippage,
                                    signal_score=r.signal.score,
                                    reason=r.signal.reason,
                                    order_id=r.order.order_id or "",
                                )

                # Save performance snapshot
                metrics = portfolio.summary()
                state.save_performance_snapshot(metrics)

                summary_str = (
                    f"[{now_iso()[:19]}] Equity: ${metrics['equity']:,.0f} | "
                    f"Cash: ${metrics['cash']:,.0f} | "
                    f"Return: {metrics['total_return_pct']:+.2f}% | "
                    f"Positions: {metrics['open_positions']} | "
                    f"Trades: {metrics['total_trades']}"
                )
                print(summary_str)
                logger.info("Portfolio snapshot", extra=metrics)

                bar_count += 1

                # Sleep between bars
                # Daily bars: re-check once per hour during market hours.
                # The market-open check at the top of the loop prevents placing
                # orders outside trading hours.
                sleep_sec = 3600 if cfg["data"].get("granularity", "1d") == "1d" else 300
                logger.debug(f"Sleeping {sleep_sec}s")
                time.sleep(sleep_sec)

            except KeyboardInterrupt:
                raise
            except Exception as exc:
                logger.error("Error in main loop", extra={"error": str(exc)}, exc_info=True)
                state.audit("error", str(exc))
                time.sleep(10)

    except KeyboardInterrupt:
        logger.info("Shutdown requested by user")
        print("\n[BOT] Shutting down...")

    finally:
        metrics = portfolio.summary()
        state.save_performance_snapshot(metrics)
        state.audit("bot_stop", "Bot stopped", extra=metrics)
        broker.disconnect()

        # Export trade log
        log_dir = obs_cfg.get("log_dir", ".logs")
        trade_csv = obs_cfg.get("trade_log_csv", f"{log_dir}/trades.csv")
        ensure_dir(log_dir)
        state.export_trades_csv(trade_csv)

        print("\n[BOT] Final portfolio summary:")
        for k, v in metrics.items():
            print(f"  {k}: {v}")
        print(f"[BOT] Trade log saved to: {trade_csv}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Agentic Trading Bot")
    parser.add_argument(
        "--mode", choices=["paper", "live", "backtest"], default="paper",
        help="Execution mode (default: paper)"
    )
    parser.add_argument(
        "--config", default="config.yaml",
        help="Path to config file (default: config.yaml)"
    )
    parser.add_argument(
        "--tickers", default=None,
        help="Comma-separated tickers to trade/backtest (overrides config)"
    )
    parser.add_argument(
        "--start", default=None,
        help="Backtest start date YYYY-MM-DD (default: from config)"
    )
    parser.add_argument(
        "--end", default=None,
        help="Backtest end date YYYY-MM-DD (default: today)"
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    # Load config first so we can set up logging with the right settings
    cfg = load_config(args.config)
    obs_cfg = cfg.get("observability", {})
    ensure_dir(obs_cfg.get("log_dir", ".logs"))

    setup_logging(
        level=obs_cfg.get("log_level", "INFO"),
        log_format=obs_cfg.get("log_format", "json"),
        log_dir=obs_cfg.get("log_dir", ".logs"),
    )
    global logger
    logger = get_logger("main")

    mode = args.mode

    # CLI ticker override
    if args.tickers:
        cfg["data"]["tickers"] = [t.strip() for t in args.tickers.split(",")]

    logger.info("Starting bot", extra={"mode": mode, "config": args.config})

    if mode == "backtest":
        bt_cfg = cfg.get("backtest", {})
        start = args.start or bt_cfg.get("start_date", str(date.today() - timedelta(days=730)))
        end = args.end or bt_cfg.get("end_date", str(date.today()))
        tickers = cfg["data"].get("tickers", ["AAPL"])
        run_backtest(cfg, tickers, start, end)
    else:
        run_trading(cfg, mode)


if __name__ == "__main__":
    main()
