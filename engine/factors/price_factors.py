# -*- coding: utf-8 -*-
"""
价格因子模块 - 基于价格数据的基础因子
包含动量、反转、波动率等价格相关因子
"""
import numpy as np
import pandas as pd
import talib
from .base_factor import BaseFactor


class PriceFactors(BaseFactor):
    """价格相关因子"""
    
    def __init__(self):
        super().__init__()
    
    def mom_20(self, close: pd.DataFrame, window: int = 20) -> pd.DataFrame:
        """动量因子：N日价格动量
        
        Args:
            close: 收盘价矩阵
            window: 计算窗口
            
        Returns:
            动量因子矩阵
        """
        if not self.validate_input_data(close):
            return pd.DataFrame()
        return close.pct_change(window, fill_method=None)
    
    def mom_10(self, close: pd.DataFrame, window: int = 10) -> pd.DataFrame:
        """动量因子：10日价格动量
        
        Args:
            close: 收盘价矩阵
            window: 计算窗口
            
        Returns:
            动量因子矩阵
        """
        if not self.validate_input_data(close):
            return pd.DataFrame()
        return self.apply_talib_to_dataframe(talib.MOM, close, timeperiod=window)
    
    def short_rev_5(self, close: pd.DataFrame, window: int = 5) -> pd.DataFrame:
        """短期反转因子：N日反转动量
        
        Args:
            close: 收盘价矩阵
            window: 计算窗口
            
        Returns:
            短期反转因子矩阵（取负值）
        """
        if not self.validate_input_data(close):
            return pd.DataFrame()
        return -close.pct_change(window, fill_method=None)
    
    def volatility_20(self, close: pd.DataFrame, window: int = 20) -> pd.DataFrame:
        """波动率因子：N日收益率标准差
        
        Args:
            close: 收盘价矩阵
            window: 计算窗口
            
        Returns:
            波动率因子矩阵
        """
        if not self.validate_input_data(close):
            return pd.DataFrame()
        returns = close.pct_change(fill_method=None)
        return returns.rolling(window).std()
    
    def macd_signal(self, close: pd.DataFrame, fast: int = 12, slow: int = 26, signal: int = 9) -> pd.DataFrame:
        """MACD信号线因子
        
        Args:
            close: 收盘价矩阵
            fast: 快线周期
            slow: 慢线周期  
            signal: 信号线周期
            
        Returns:
            MACD信号因子矩阵
        """
        if not self.validate_input_data(close):
            return pd.DataFrame()
        
        ema_fast = close.ewm(span=fast).mean()
        ema_slow = close.ewm(span=slow).mean()
        dif = ema_fast - ema_slow
        dea = dif.ewm(span=signal).mean()
        macd = 2 * (dif - dea)
        
        return macd
    
    def macd_histogram(self, close: pd.DataFrame, fast: int = 12, slow: int = 26, signal: int = 9) -> pd.DataFrame:
        """MACD柱状图因子
        
        Args:
            close: 收盘价矩阵
            fast: 快线周期
            slow: 慢线周期
            signal: 信号线周期
            
        Returns:
            MACD柱状图因子矩阵
        """
        if not self.validate_input_data(close):
            return pd.DataFrame()
        
        result = pd.DataFrame(index=close.index, columns=close.columns)
        
        for col in close.columns:
            series_data = close[col].dropna()
            if len(series_data) > max(fast, slow) + signal:
                try:
                    macd_line, macd_signal_line, macd_hist = talib.MACD(
                        series_data.values, fastperiod=fast, slowperiod=slow, signalperiod=signal
                    )
                    result.loc[series_data.index, col] = macd_hist
                except Exception as e:
                    print(f"MACD histogram calculation failed for {col}: {e}")
                    continue
        
        return result
    
    def turnover_mean(self, vol: pd.DataFrame, amount: pd.DataFrame, window: int = 20) -> pd.DataFrame:
        """换手率因子：N日换手率均值（基于成交量和成交额）
        
        Args:
            vol: 成交量矩阵
            amount: 成交额矩阵
            window: 计算窗口
            
        Returns:
            换手率因子矩阵
        """
        if not self.validate_input_data(vol, amount):
            return pd.DataFrame()
        
        # 使用成交量作为换手率的代理指标
        # 取对数避免极值影响
        log_vol = np.log(vol.replace(0, np.nan))
        return log_vol.rolling(window).mean()
    
    def amihud_20(self, close: pd.DataFrame, amount: pd.DataFrame, window: int = 20) -> pd.DataFrame:
        """Amihud流动性因子：N日非流动性指标
        
        Args:
            close: 收盘价矩阵
            amount: 成交额矩阵
            window: 计算窗口
            
        Returns:
            流动性因子矩阵（取负值，值越大流动性越好）
        """
        if not self.validate_input_data(close, amount):
            return pd.DataFrame()
        
        returns = close.pct_change(fill_method=None).abs()
        illiq = (returns / amount.replace(0, np.nan)).rolling(window).mean()
        return -illiq  # 取负值，大值表示流动性好
    
    def bollinger_position(self, close: pd.DataFrame, window: int = 20, std_dev: float = 2.0) -> pd.DataFrame:
        """布林带位置因子
        
        Args:
            close: 收盘价矩阵
            window: 计算窗口
            std_dev: 标准差倍数
            
        Returns:
            布林带位置因子矩阵
        """
        if not self.validate_input_data(close):
            return pd.DataFrame()
        
        ma = close.rolling(window).mean()
        std = close.rolling(window).std()
        upper_band = ma + std_dev * std
        lower_band = ma - std_dev * std
        
        # 计算价格在布林带中的位置 (0-1之间)
        position = (close - lower_band) / (upper_band - lower_band)
        return position.clip(0, 1)  # 限制在0-1之间
    
    def roc_10(self, close: pd.DataFrame, window: int = 10) -> pd.DataFrame:
        """变化率因子：N日价格变化率
        
        Args:
            close: 收盘价矩阵
            window: 计算窗口
            
        Returns:
            变化率因子矩阵
        """
        if not self.validate_input_data(close):
            return pd.DataFrame()
        return self.apply_talib_to_dataframe(talib.ROC, close, timeperiod=window)
    
    def rocp_10(self, close: pd.DataFrame, window: int = 10) -> pd.DataFrame:
        """变化率百分比因子：N日价格变化率百分比
        
        Args:
            close: 收盘价矩阵
            window: 计算窗口
            
        Returns:
            变化率百分比因子矩阵
        """
        if not self.validate_input_data(close):
            return pd.DataFrame()
        return self.apply_talib_to_dataframe(talib.ROCP, close, timeperiod=window)
    
    def rocr_10(self, close: pd.DataFrame, window: int = 10) -> pd.DataFrame:
        """变化率比率因子：N日价格变化率比率
        
        Args:
            close: 收盘价矩阵
            window: 计算窗口
            
        Returns:
            变化率比率因子矩阵
        """
        if not self.validate_input_data(close):
            return pd.DataFrame()
        return self.apply_talib_to_dataframe(talib.ROCR, close, timeperiod=window)
    
    def rocr100_10(self, close: pd.DataFrame, window: int = 10) -> pd.DataFrame:
        """变化率比率100因子：N日价格变化率比率*100
        
        Args:
            close: 收盘价矩阵
            window: 计算窗口
            
        Returns:
            变化率比率100因子矩阵
        """
        if not self.validate_input_data(close):
            return pd.DataFrame()
        return self.apply_talib_to_dataframe(talib.ROCR100, close, timeperiod=window)
