# -*- coding: utf-8 -*-
"""
动量指标模块 - 各种动量和震荡指标
包含RSI、MACD、Stochastic等动量指标
"""
import numpy as np
import pandas as pd
import talib
from .base_factor import BaseFactor


class MomentumFactors(BaseFactor):
    """动量指标因子"""
    
    def __init__(self):
        super().__init__()
    
    def rsi_14(self, close: pd.DataFrame, window: int = 14) -> pd.DataFrame:
        """相对强弱指标RSI
        
        Args:
            close: 收盘价矩阵
            window: 计算窗口
            
        Returns:
            RSI因子矩阵
        """
        if not self.validate_input_data(close):
            return pd.DataFrame()
        return self.apply_talib_to_dataframe(talib.RSI, close, timeperiod=window)
    
    def apo_12_26(self, close: pd.DataFrame, fast: int = 12, slow: int = 26) -> pd.DataFrame:
        """绝对价格振荡器
        
        Args:
            close: 收盘价矩阵
            fast: 快线周期
            slow: 慢线周期
            
        Returns:
            APO因子矩阵
        """
        if not self.validate_input_data(close):
            return pd.DataFrame()
        
        result = pd.DataFrame(index=close.index, columns=close.columns)
        
        for col in close.columns:
            series_data = close[col].dropna()
            if len(series_data) >= max(fast, slow) + 5:
                try:
                    calc_result = talib.APO(series_data.values, 
                                          fastperiod=fast, slowperiod=slow)
                    result.loc[series_data.index, col] = calc_result
                except Exception as e:
                    print(f"APO calculation failed for {col}: {e}")
                    continue
        
        return result
    
    def aroonosc_14(self, high: pd.DataFrame, low: pd.DataFrame, window: int = 14) -> pd.DataFrame:
        """Aroon 振荡器
        
        Args:
            high: 最高价矩阵
            low: 最低价矩阵
            window: 计算窗口
            
        Returns:
            Aroon振荡器因子矩阵
        """
        if not self.validate_input_data(high, low):
            return pd.DataFrame()
        
        result = pd.DataFrame(index=high.index, columns=high.columns)
        
        for col in high.columns:
            if col in low.columns:
                high_series = high[col].dropna()
                low_series = low[col].dropna()
                common_index = high_series.index.intersection(low_series.index)
                
                if len(common_index) >= window + 5:
                    try:
                        calc_result = talib.AROONOSC(
                            high_series[common_index].values,
                            low_series[common_index].values,
                            timeperiod=window
                        )
                        result.loc[common_index, col] = calc_result
                    except Exception as e:
                        print(f"AROONOSC calculation failed for {col}: {e}")
                        continue
        
        return result
    
    def bop(self, open_price: pd.DataFrame, high: pd.DataFrame, 
            low: pd.DataFrame, close: pd.DataFrame) -> pd.DataFrame:
        """力量平衡指标
        
        Args:
            open_price: 开盘价矩阵
            high: 最高价矩阵
            low: 最低价矩阵
            close: 收盘价矩阵
            
        Returns:
            BOP因子矩阵
        """
        if not self.validate_input_data(open_price, high, low, close):
            return pd.DataFrame()
        
        result = pd.DataFrame(index=close.index, columns=close.columns)
        
        for col in close.columns:
            if all(col in df.columns for df in [open_price, high, low]):
                try:
                    o_data = open_price[col].dropna()
                    h_data = high[col].dropna()
                    l_data = low[col].dropna()
                    c_data = close[col].dropna()
                    
                    common_index = o_data.index.intersection(h_data.index).intersection(
                        l_data.index).intersection(c_data.index)
                    
                    if len(common_index) >= 10:
                        calc_result = talib.BOP(
                            o_data[common_index].values,
                            h_data[common_index].values,
                            l_data[common_index].values,
                            c_data[common_index].values
                        )
                        result.loc[common_index, col] = calc_result
                except Exception as e:
                    print(f"BOP calculation failed for {col}: {e}")
                    continue
        
        return result
    
    def cmo_14(self, close: pd.DataFrame, window: int = 14) -> pd.DataFrame:
        """Chande动量振荡器
        
        Args:
            close: 收盘价矩阵
            window: 计算窗口
            
        Returns:
            CMO因子矩阵
        """
        if not self.validate_input_data(close):
            return pd.DataFrame()
        return self.apply_talib_to_dataframe(talib.CMO, close, timeperiod=window)
    
    def dx_14(self, high: pd.DataFrame, low: pd.DataFrame, close: pd.DataFrame, window: int = 14) -> pd.DataFrame:
        """方向性运动指标
        
        Args:
            high: 最高价矩阵
            low: 最低价矩阵
            close: 收盘价矩阵
            window: 计算窗口
            
        Returns:
            DX因子矩阵
        """
        if not self.validate_input_data(high, low, close):
            return pd.DataFrame()
        
        result = pd.DataFrame(index=close.index, columns=close.columns)
        
        for col in close.columns:
            if col in high.columns and col in low.columns:
                try:
                    h_data = high[col].dropna()
                    l_data = low[col].dropna()
                    c_data = close[col].dropna()
                    
                    common_index = h_data.index.intersection(l_data.index).intersection(c_data.index)
                    
                    if len(common_index) >= window + 10:
                        calc_result = talib.DX(
                            h_data[common_index].values,
                            l_data[common_index].values,
                            c_data[common_index].values,
                            timeperiod=window
                        )
                        result.loc[common_index, col] = calc_result
                except Exception as e:
                    print(f"DX calculation failed for {col}: {e}")
                    continue
        
        return result
    
    def mfi_14(self, high: pd.DataFrame, low: pd.DataFrame, close: pd.DataFrame, 
               vol: pd.DataFrame, window: int = 14) -> pd.DataFrame:
        """资金流量指标
        
        Args:
            high: 最高价矩阵
            low: 最低价矩阵
            close: 收盘价矩阵
            vol: 成交量矩阵
            window: 计算窗口
            
        Returns:
            MFI因子矩阵
        """
        if not self.validate_input_data(high, low, close, vol):
            return pd.DataFrame()
        
        result = pd.DataFrame(index=close.index, columns=close.columns)
        
        for col in close.columns:
            if all(col in df.columns for df in [high, low, vol]):
                try:
                    h_data = high[col].dropna()
                    l_data = low[col].dropna()
                    c_data = close[col].dropna()
                    v_data = vol[col].dropna()
                    
                    common_index = h_data.index.intersection(l_data.index).intersection(
                        c_data.index).intersection(v_data.index)
                    
                    if len(common_index) >= window + 5:
                        calc_result = talib.MFI(
                            h_data[common_index].values.astype(np.float64),
                            l_data[common_index].values.astype(np.float64),
                            c_data[common_index].values.astype(np.float64),
                            v_data[common_index].values.astype(np.float64),
                            timeperiod=window
                        )
                        result.loc[common_index, col] = calc_result
                except Exception as e:
                    print(f"MFI calculation failed for {col}: {e}")
                    continue
        
        return result
    
    def ppo_12_26(self, close: pd.DataFrame, fast: int = 12, slow: int = 26) -> pd.DataFrame:
        """价格振荡器百分比
        
        Args:
            close: 收盘价矩阵
            fast: 快线周期
            slow: 慢线周期
            
        Returns:
            PPO因子矩阵
        """
        if not self.validate_input_data(close):
            return pd.DataFrame()
        
        result = pd.DataFrame(index=close.index, columns=close.columns)
        
        for col in close.columns:
            series_data = close[col].dropna()
            if len(series_data) >= max(fast, slow) + 5:
                try:
                    calc_result = talib.PPO(series_data.values, 
                                          fastperiod=fast, slowperiod=slow)
                    result.loc[series_data.index, col] = calc_result
                except Exception as e:
                    print(f"PPO calculation failed for {col}: {e}")
                    continue
        
        return result
    
    def stochf_14(self, high: pd.DataFrame, low: pd.DataFrame, close: pd.DataFrame, 
                  k_period: int = 14, d_period: int = 3) -> pd.DataFrame:
        """快速随机指标
        
        Args:
            high: 最高价矩阵
            low: 最低价矩阵
            close: 收盘价矩阵
            k_period: K线周期
            d_period: D线周期
            
        Returns:
            快速随机指标因子矩阵
        """
        if not self.validate_input_data(high, low, close):
            return pd.DataFrame()
        
        result = pd.DataFrame(index=close.index, columns=close.columns)
        
        for col in close.columns:
            if col in high.columns and col in low.columns:
                try:
                    h_data = high[col].dropna()
                    l_data = low[col].dropna()
                    c_data = close[col].dropna()
                    
                    common_index = h_data.index.intersection(l_data.index).intersection(c_data.index)
                    
                    if len(common_index) >= max(k_period, d_period) + 5:
                        k_values, d_values = talib.STOCHF(
                            h_data[common_index].values,
                            l_data[common_index].values,
                            c_data[common_index].values,
                            fastk_period=k_period, fastd_period=d_period
                        )
                        result.loc[common_index, col] = k_values
                except Exception as e:
                    print(f"STOCHF calculation failed for {col}: {e}")
                    continue
        
        return result
    
    def stoch_k(self, high: pd.DataFrame, low: pd.DataFrame, close: pd.DataFrame, 
                k_period: int = 14, d_period: int = 3, smooth_k: int = 3) -> pd.DataFrame:
        """慢速随机指标K值
        
        Args:
            high: 最高价矩阵
            low: 最低价矩阵
            close: 收盘价矩阵
            k_period: K线周期
            d_period: D线周期
            smooth_k: K线平滑周期
            
        Returns:
            慢速随机指标K值因子矩阵
        """
        if not self.validate_input_data(high, low, close):
            return pd.DataFrame()
        
        result = pd.DataFrame(index=close.index, columns=close.columns)
        
        for col in close.columns:
            if col in high.columns and col in low.columns:
                try:
                    h_data = high[col].dropna()
                    l_data = low[col].dropna()
                    c_data = close[col].dropna()
                    
                    common_index = h_data.index.intersection(l_data.index).intersection(c_data.index)
                    
                    if len(common_index) >= max(k_period, d_period, smooth_k) + 5:
                        k_values, d_values = talib.STOCH(
                            h_data[common_index].values,
                            l_data[common_index].values,
                            c_data[common_index].values,
                            fastk_period=k_period, slowk_period=smooth_k, 
                            slowd_period=d_period
                        )
                        result.loc[common_index, col] = k_values
                except Exception as e:
                    print(f"STOCH calculation failed for {col}: {e}")
                    continue
        
        return result
    
    def trix_14(self, close: pd.DataFrame, window: int = 14) -> pd.DataFrame:
        """TRIX 指标
        
        Args:
            close: 收盘价矩阵
            window: 计算窗口
            
        Returns:
            TRIX因子矩阵
        """
        if not self.validate_input_data(close):
            return pd.DataFrame()
        return self.apply_talib_to_dataframe(talib.TRIX, close, timeperiod=window)
    
    def ultosc_7_14_28(self, high: pd.DataFrame, low: pd.DataFrame, close: pd.DataFrame,
                       period1: int = 7, period2: int = 14, period3: int = 28) -> pd.DataFrame:
        """终极振荡器
        
        Args:
            high: 最高价矩阵
            low: 最低价矩阵
            close: 收盘价矩阵
            period1: 第一个周期
            period2: 第二个周期
            period3: 第三个周期
            
        Returns:
            终极振荡器因子矩阵
        """
        if not self.validate_input_data(high, low, close):
            return pd.DataFrame()
        
        result = pd.DataFrame(index=close.index, columns=close.columns)
        
        for col in close.columns:
            if col in high.columns and col in low.columns:
                try:
                    h_data = high[col].dropna()
                    l_data = low[col].dropna()
                    c_data = close[col].dropna()
                    
                    common_index = h_data.index.intersection(l_data.index).intersection(c_data.index)
                    
                    if len(common_index) >= max(period1, period2, period3) + 10:
                        calc_result = talib.ULTOSC(
                            h_data[common_index].values,
                            l_data[common_index].values,
                            c_data[common_index].values,
                            timeperiod1=period1, timeperiod2=period2, timeperiod3=period3
                        )
                        result.loc[common_index, col] = calc_result
                except Exception as e:
                    print(f"ULTOSC calculation failed for {col}: {e}")
                    continue
        
        return result
    
    def williams_r(self, high: pd.DataFrame, low: pd.DataFrame, close: pd.DataFrame, window: int = 14) -> pd.DataFrame:
        """威廉指标
        
        Args:
            high: 最高价矩阵
            low: 最低价矩阵
            close: 收盘价矩阵
            window: 计算窗口
            
        Returns:
            威廉指标因子矩阵
        """
        if not self.validate_input_data(high, low, close):
            return pd.DataFrame()
        
        result = pd.DataFrame(index=close.index, columns=close.columns)
        
        for col in close.columns:
            if col in high.columns and col in low.columns:
                try:
                    h_data = high[col].dropna()
                    l_data = low[col].dropna()
                    c_data = close[col].dropna()
                    
                    common_index = h_data.index.intersection(l_data.index).intersection(c_data.index)
                    
                    if len(common_index) >= window + 5:
                        calc_result = talib.WILLR(
                            h_data[common_index].values,
                            l_data[common_index].values,
                            c_data[common_index].values,
                            timeperiod=window
                        )
                        result.loc[common_index, col] = calc_result
                except Exception as e:
                    print(f"WILLR calculation failed for {col}: {e}")
                    continue
        
        return result
    
    def cci_14(self, high: pd.DataFrame, low: pd.DataFrame, close: pd.DataFrame, window: int = 14) -> pd.DataFrame:
        """商品通道指标
        
        Args:
            high: 最高价矩阵
            low: 最低价矩阵
            close: 收盘价矩阵
            window: 计算窗口
            
        Returns:
            CCI因子矩阵
        """
        if not self.validate_input_data(high, low, close):
            return pd.DataFrame()
        
        result = pd.DataFrame(index=close.index, columns=close.columns)
        
        for col in close.columns:
            if col in high.columns and col in low.columns:
                try:
                    h_data = high[col].dropna()
                    l_data = low[col].dropna()
                    c_data = close[col].dropna()
                    
                    common_index = h_data.index.intersection(l_data.index).intersection(c_data.index)
                    
                    if len(common_index) >= window + 5:
                        calc_result = talib.CCI(
                            h_data[common_index].values,
                            l_data[common_index].values,
                            c_data[common_index].values,
                            timeperiod=window
                        )
                        result.loc[common_index, col] = calc_result
                except Exception as e:
                    print(f"CCI calculation failed for {col}: {e}")
                    continue
        
        return result
    
    def adx_14(self, high: pd.DataFrame, low: pd.DataFrame, close: pd.DataFrame, window: int = 14) -> pd.DataFrame:
        """平均趋向指标
        
        Args:
            high: 最高价矩阵
            low: 最低价矩阵
            close: 收盘价矩阵
            window: 计算窗口
            
        Returns:
            ADX因子矩阵
        """
        if not self.validate_input_data(high, low, close):
            return pd.DataFrame()
        
        result = pd.DataFrame(index=close.index, columns=close.columns)
        
        for col in close.columns:
            if col in high.columns and col in low.columns:
                try:
                    h_data = high[col].dropna()
                    l_data = low[col].dropna()
                    c_data = close[col].dropna()
                    
                    common_index = h_data.index.intersection(l_data.index).intersection(c_data.index)
                    
                    if len(common_index) >= window + 15:
                        calc_result = talib.ADX(
                            h_data[common_index].values,
                            l_data[common_index].values,
                            c_data[common_index].values,
                            timeperiod=window
                        )
                        result.loc[common_index, col] = calc_result
                except Exception as e:
                    print(f"ADX calculation failed for {col}: {e}")
                    continue
        
        return result
    
    def adxr_14(self, high: pd.DataFrame, low: pd.DataFrame, close: pd.DataFrame, window: int = 14) -> pd.DataFrame:
        """ADX评级
        
        Args:
            high: 最高价矩阵
            low: 最低价矩阵
            close: 收盘价矩阵
            window: 计算窗口
            
        Returns:
            ADXR因子矩阵
        """
        if not self.validate_input_data(high, low, close):
            return pd.DataFrame()
        
        result = pd.DataFrame(index=close.index, columns=close.columns)
        
        for col in close.columns:
            if col in high.columns and col in low.columns:
                try:
                    h_data = high[col].dropna()
                    l_data = low[col].dropna()
                    c_data = close[col].dropna()
                    
                    common_index = h_data.index.intersection(l_data.index).intersection(c_data.index)
                    
                    if len(common_index) >= window + 20:
                        calc_result = talib.ADXR(
                            h_data[common_index].values,
                            l_data[common_index].values,
                            c_data[common_index].values,
                            timeperiod=window
                        )
                        result.loc[common_index, col] = calc_result
                except Exception as e:
                    print(f"ADXR calculation failed for {col}: {e}")
                    continue
        
        return result
    
    def macdext_12_26_9(self, close: pd.DataFrame, fast: int = 12, slow: int = 26, signal: int = 9) -> pd.DataFrame:
        """可控MA类型的MACD
        
        Args:
            close: 收盘价矩阵
            fast: 快线周期
            slow: 慢线周期
            signal: 信号线周期
            
        Returns:
            MACDEXT因子矩阵
        """
        if not self.validate_input_data(close):
            return pd.DataFrame()
        
        result = pd.DataFrame(index=close.index, columns=close.columns)
        
        for col in close.columns:
            series_data = close[col].dropna()
            if len(series_data) >= max(fast, slow, signal) + 10:
                try:
                    macd, signal_line, histogram = talib.MACDEXT(
                        series_data.values,
                        fastperiod=fast, fastmatype=0, slowperiod=slow, slowmatype=0,
                        signalperiod=signal, signalmatype=0
                    )
                    result.loc[series_data.index, col] = histogram  # 使用柱状图
                except Exception as e:
                    print(f"MACDEXT calculation failed for {col}: {e}")
                    continue
        
        return result
    
    def macdfix_9(self, close: pd.DataFrame, signal: int = 9) -> pd.DataFrame:
        """MACD固定12/26
        
        Args:
            close: 收盘价矩阵
            signal: 信号线周期
            
        Returns:
            MACDFIX因子矩阵
        """
        if not self.validate_input_data(close):
            return pd.DataFrame()
        
        result = pd.DataFrame(index=close.index, columns=close.columns)
        
        for col in close.columns:
            series_data = close[col].dropna()
            if len(series_data) >= 26 + signal:
                try:
                    macd, signal_line, histogram = talib.MACDFIX(
                        series_data.values, signalperiod=signal
                    )
                    result.loc[series_data.index, col] = histogram
                except Exception as e:
                    print(f"MACDFIX calculation failed for {col}: {e}")
                    continue
        
        return result
    
    def minus_di_14(self, high: pd.DataFrame, low: pd.DataFrame, close: pd.DataFrame, window: int = 14) -> pd.DataFrame:
        """负向指标
        
        Args:
            high: 最高价矩阵
            low: 最低价矩阵
            close: 收盘价矩阵
            window: 计算窗口
            
        Returns:
            负向指标因子矩阵
        """
        if not self.validate_input_data(high, low, close):
            return pd.DataFrame()
        
        result = pd.DataFrame(index=close.index, columns=close.columns)
        
        for col in close.columns:
            if col in high.columns and col in low.columns:
                try:
                    h_data = high[col].dropna()
                    l_data = low[col].dropna()
                    c_data = close[col].dropna()
                    
                    common_index = h_data.index.intersection(l_data.index).intersection(c_data.index)
                    
                    if len(common_index) >= window + 15:
                        calc_result = talib.MINUS_DI(
                            h_data[common_index].values,
                            l_data[common_index].values,
                            c_data[common_index].values,
                            timeperiod=window
                        )
                        result.loc[common_index, col] = calc_result
                except Exception as e:
                    print(f"MINUS_DI calculation failed for {col}: {e}")
                    continue
        
        return result
    
    def minus_dm_14(self, high: pd.DataFrame, low: pd.DataFrame, window: int = 14) -> pd.DataFrame:
        """负向运动
        
        Args:
            high: 最高价矩阵
            low: 最低价矩阵
            window: 计算窗口
            
        Returns:
            负向运动因子矩阵
        """
        if not self.validate_input_data(high, low):
            return pd.DataFrame()
        
        result = pd.DataFrame(index=high.index, columns=high.columns)
        
        for col in high.columns:
            if col in low.columns:
                high_series = high[col].dropna()
                low_series = low[col].dropna()
                common_index = high_series.index.intersection(low_series.index)
                
                if len(common_index) >= window + 10:
                    try:
                        calc_result = talib.MINUS_DM(
                            high_series[common_index].values,
                            low_series[common_index].values,
                            timeperiod=window
                        )
                        result.loc[common_index, col] = calc_result
                    except Exception as e:
                        print(f"MINUS_DM calculation failed for {col}: {e}")
                        continue
        
        return result
    
    def plus_di_14(self, high: pd.DataFrame, low: pd.DataFrame, close: pd.DataFrame, window: int = 14) -> pd.DataFrame:
        """正向指标
        
        Args:
            high: 最高价矩阵
            low: 最低价矩阵
            close: 收盘价矩阵
            window: 计算窗口
            
        Returns:
            正向指标因子矩阵
        """
        if not self.validate_input_data(high, low, close):
            return pd.DataFrame()
        
        result = pd.DataFrame(index=close.index, columns=close.columns)
        
        for col in close.columns:
            if col in high.columns and col in low.columns:
                try:
                    h_data = high[col].dropna()
                    l_data = low[col].dropna()
                    c_data = close[col].dropna()
                    
                    common_index = h_data.index.intersection(l_data.index).intersection(c_data.index)
                    
                    if len(common_index) >= window + 15:
                        calc_result = talib.PLUS_DI(
                            h_data[common_index].values,
                            l_data[common_index].values,
                            c_data[common_index].values,
                            timeperiod=window
                        )
                        result.loc[common_index, col] = calc_result
                except Exception as e:
                    print(f"PLUS_DI calculation failed for {col}: {e}")
                    continue
        
        return result
    
    def plus_dm_14(self, high: pd.DataFrame, low: pd.DataFrame, window: int = 14) -> pd.DataFrame:
        """正向运动
        
        Args:
            high: 最高价矩阵
            low: 最低价矩阵
            window: 计算窗口
            
        Returns:
            正向运动因子矩阵
        """
        if not self.validate_input_data(high, low):
            return pd.DataFrame()
        
        result = pd.DataFrame(index=high.index, columns=high.columns)
        
        for col in high.columns:
            if col in low.columns:
                high_series = high[col].dropna()
                low_series = low[col].dropna()
                common_index = high_series.index.intersection(low_series.index)
                
                if len(common_index) >= window + 10:
                    try:
                        calc_result = talib.PLUS_DM(
                            high_series[common_index].values,
                            low_series[common_index].values,
                            timeperiod=window
                        )
                        result.loc[common_index, col] = calc_result
                    except Exception as e:
                        print(f"PLUS_DM calculation failed for {col}: {e}")
                        continue
        
        return result
    
    def stoch_slow_k(self, high: pd.DataFrame, low: pd.DataFrame, close: pd.DataFrame,
                     fastk_period: int = 5, slowk_period: int = 3, slowd_period: int = 3) -> pd.DataFrame:
        """慢速随机指标K值
        
        Args:
            high: 最高价矩阵
            low: 最低价矩阵
            close: 收盘价矩阵
            fastk_period: 快速K周期
            slowk_period: 慢速K周期
            slowd_period: 慢速D周期
            
        Returns:
            慢速随机指标K值因子矩阵
        """
        if not self.validate_input_data(high, low, close):
            return pd.DataFrame()
        
        result = pd.DataFrame(index=high.index, columns=high.columns)
        
        for col in high.columns:
            if col in low.columns and col in close.columns:
                high_series = high[col].ffill().dropna()
                low_series = low[col].ffill().dropna()
                close_series = close[col].ffill().dropna()
                common_index = high_series.index.intersection(low_series.index)\
                                               .intersection(close_series.index)
                
                if len(common_index) >= max(fastk_period, slowk_period, slowd_period) + 5:
                    try:
                        slowk, slowd = talib.STOCH(
                            high_series[common_index].values,
                            low_series[common_index].values,
                            close_series[common_index].values,
                            fastk_period=fastk_period,
                            slowk_period=slowk_period,
                            slowk_matype=0,
                            slowd_period=slowd_period,
                            slowd_matype=0
                        )
                        result.loc[common_index, col] = slowk
                    except Exception as e:
                        print(f"STOCH slow K calculation failed for {col}: {e}")
                        continue
        
        return result
    
    def stoch_slow_d(self, high: pd.DataFrame, low: pd.DataFrame, close: pd.DataFrame,
                     fastk_period: int = 5, slowk_period: int = 3, slowd_period: int = 3) -> pd.DataFrame:
        """慢速随机指标D值
        
        Args:
            high: 最高价矩阵
            low: 最低价矩阵
            close: 收盘价矩阵
            fastk_period: 快速K周期
            slowk_period: 慢速K周期
            slowd_period: 慢速D周期
            
        Returns:
            慢速随机指标D值因子矩阵
        """
        if not self.validate_input_data(high, low, close):
            return pd.DataFrame()
        
        result = pd.DataFrame(index=high.index, columns=high.columns)
        
        for col in high.columns:
            if col in low.columns and col in close.columns:
                high_series = high[col].ffill().dropna()
                low_series = low[col].ffill().dropna()
                close_series = close[col].ffill().dropna()
                common_index = high_series.index.intersection(low_series.index)\
                                               .intersection(close_series.index)
                
                if len(common_index) >= max(fastk_period, slowk_period, slowd_period) + 5:
                    try:
                        slowk, slowd = talib.STOCH(
                            high_series[common_index].values,
                            low_series[common_index].values,
                            close_series[common_index].values,
                            fastk_period=fastk_period,
                            slowk_period=slowk_period,
                            slowk_matype=0,
                            slowd_period=slowd_period,
                            slowd_matype=0
                        )
                        result.loc[common_index, col] = slowd
                    except Exception as e:
                        print(f"STOCH slow D calculation failed for {col}: {e}")
                        continue
        
        return result
