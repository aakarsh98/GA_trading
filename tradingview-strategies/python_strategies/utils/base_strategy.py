"""Base strategy class for all trading strategies"""
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Tuple
import numpy as np
import pandas as pd
from dataclasses import dataclass


@dataclass
class Signal:
    """Trading signal with metadata"""
    timestamp: pd.Timestamp
    signal_type: str  # 'LONG', 'SHORT', 'EXIT_LONG', 'EXIT_SHORT'
    price: float
    confidence: float
    metadata: Dict = None


@dataclass
class Trade:
    """Trade execution record"""
    entry_time: pd.Timestamp
    exit_time: Optional[pd.Timestamp]
    entry_price: float
    exit_price: Optional[float]
    position_type: str
    size: float
    pnl: Optional[float] = None
    pnl_pct: Optional[float] = None


class BaseStrategy(ABC):
    """Base class for all trading strategies"""
    
    def __init__(self, name: str, initial_capital: float = 10000):
        self.name = name
        self.initial_capital = initial_capital
        self.current_capital = initial_capital
        self.signals: List[Signal] = []
        self.trades: List[Trade] = []
        self.positions: Dict = {}
        
    @abstractmethod
    def generate_signals(self, data: pd.DataFrame) -> List[Signal]:
        """Generate trading signals from market data"""
        pass
    
    @abstractmethod
    def calculate_position_size(self, signal: Signal, current_price: float) -> float:
        """Calculate position size based on risk management"""
        pass
    
    def backtest(self, data: pd.DataFrame) -> Dict:
        """Run backtest on historical data"""
        self.signals = self.generate_signals(data)
        self.execute_signals(data)
        return self.calculate_performance_metrics()
    
    def execute_signals(self, data: pd.DataFrame):
        """Execute signals and manage trades"""
        for signal in self.signals:
            if signal.signal_type in ['LONG', 'SHORT']:
                position_size = self.calculate_position_size(signal, signal.price)
                trade = Trade(
                    entry_time=signal.timestamp,
                    exit_time=None,
                    entry_price=signal.price,
                    exit_price=None,
                    position_type=signal.signal_type,
                    size=position_size
                )
                self.trades.append(trade)
                self.positions[signal.signal_type] = trade
            
            elif signal.signal_type in ['EXIT_LONG', 'EXIT_SHORT']:
                position_type = 'LONG' if signal.signal_type == 'EXIT_LONG' else 'SHORT'
                if position_type in self.positions:
                    trade = self.positions.pop(position_type)
                    trade.exit_time = signal.timestamp
                    trade.exit_price = signal.price
                    
                    if position_type == 'LONG':
                        trade.pnl = (trade.exit_price - trade.entry_price) * trade.size
                    else:
                        trade.pnl = (trade.entry_price - trade.exit_price) * trade.size
                    
                    trade.pnl_pct = trade.pnl / (trade.entry_price * trade.size) * 100
                    self.current_capital += trade.pnl
    
    def calculate_performance_metrics(self) -> Dict:
        """Calculate strategy performance metrics"""
        completed_trades = [t for t in self.trades if t.exit_time is not None]
        
        if not completed_trades:
            return {
                'strategy_name': self.name,
                'total_trades': 0,
                'winning_trades': 0,
                'losing_trades': 0,
                'win_rate': 0,
                'net_profit': 0,
                'net_profit_pct': 0,
                'avg_win': 0,
                'avg_loss': 0,
                'sharpe_ratio': 0,
                'max_drawdown': 0,
                'max_drawdown_pct': 0,
                'final_capital': self.current_capital,
                'return_pct': 0
            }
        
        pnls = [t.pnl for t in completed_trades]
        winning_trades = [t for t in completed_trades if t.pnl > 0]
        
        total_pnl = sum(pnls)
        win_rate = len(winning_trades) / len(completed_trades) * 100
        
        returns = np.array([t.pnl_pct for t in completed_trades])
        sharpe_ratio = (np.mean(returns) / np.std(returns)) * np.sqrt(252) if np.std(returns) > 0 else 0
        
        cumulative = np.cumsum(pnls)
        running_max = np.maximum.accumulate(cumulative)
        drawdown = cumulative - running_max
        max_drawdown = abs(min(drawdown)) if len(drawdown) > 0 else 0
        max_drawdown_pct = (max_drawdown / self.initial_capital) * 100
        
        return {
            'strategy_name': self.name,
            'total_trades': len(completed_trades),
            'winning_trades': len(winning_trades),
            'losing_trades': len(completed_trades) - len(winning_trades),
            'win_rate': win_rate,
            'net_profit': total_pnl,
            'net_profit_pct': (total_pnl / self.initial_capital) * 100,
            'avg_win': np.mean([t.pnl for t in winning_trades]) if winning_trades else 0,
            'avg_loss': np.mean([t.pnl for t in completed_trades if t.pnl < 0]) if any(t.pnl < 0 for t in completed_trades) else 0,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': max_drawdown,
            'max_drawdown_pct': max_drawdown_pct,
            'final_capital': self.current_capital,
            'return_pct': ((self.current_capital - self.initial_capital) / self.initial_capital) * 100
        }
