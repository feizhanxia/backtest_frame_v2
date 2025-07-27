# -*- coding: utf-8 -*-
"""
成交量指标模块 - 基于成交量的技术指标
包含OBV、AD、MFI等成交量相关指标
"""
import numpy as np
import pandas as pd
import talib
from .base_factor import BaseFactor


class VolumeFactors(BaseFactor):
    """成交量指标因子"""
    
    def __init__(self):
        super().__init__()
    
    def ad_line(self, high: pd.DataFrame, low: pd.DataFrame, 
                close: pd.DataFrame, vol: pd.DataFrame) -> pd.DataFrame:
        """累积/派发线
        
        Args:
            high: 最高价矩阵
            low: 最低价矩阵
            close: 收盘价矩阵
            vol: 成交量矩阵
            
        Returns:
            AD线因子矩阵
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
                    
                    if len(common_index) >= 20:
                        calc_result = talib.AD(
                            h_data[common_index].values.astype(np.float64),
                            l_data[common_index].values.astype(np.float64),
                            c_data[common_index].values.astype(np.float64),
                            v_data[common_index].values.astype(np.float64)
                        )
                        result.loc[common_index, col] = calc_result
                except Exception as e:
                    print(f"AD calculation failed for {col}: {e}")
                    continue
        
        return result
    
    def adosc_3_10(self, high: pd.DataFrame, low: pd.DataFrame, close: pd.DataFrame, 
                   vol: pd.DataFrame, fast: int = 3, slow: int = 10) -> pd.DataFrame:
        """累积/派发振荡器
        
        Args:
            high: 最高价矩阵
            low: 最低价矩阵
            close: 收盘价矩阵
            vol: 成交量矩阵
            fast: 快线周期
            slow: 慢线周期
            
        Returns:
            ADOSC因子矩阵
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
                    
                    if len(common_index) >= max(fast, slow) + 10:
                        calc_result = talib.ADOSC(
                            h_data[common_index].values.astype(np.float64),
                            l_data[common_index].values.astype(np.float64),
                            c_data[common_index].values.astype(np.float64),
                            v_data[common_index].values.astype(np.float64),
                            fastperiod=fast, slowperiod=slow
                        )
                        result.loc[common_index, col] = calc_result
                except Exception as e:
                    print(f"ADOSC calculation failed for {col}: {e}")
                    continue
        
        return result
    
    def obv_line(self, close: pd.DataFrame, vol: pd.DataFrame) -> pd.DataFrame:
        """净成交量指标
        
        Args:
            close: 收盘价矩阵
            vol: 成交量矩阵
            
        Returns:
            OBV因子矩阵
        """
        if not self.validate_input_data(close, vol):
            return pd.DataFrame()
        
        result = pd.DataFrame(index=close.index, columns=close.columns)
        
        for col in close.columns:
            if col in vol.columns:
                try:
                    c_data = close[col].dropna()
                    v_data = vol[col].dropna()
                    
                    common_index = c_data.index.intersection(v_data.index)
                    
                    if len(common_index) >= 20:
                        calc_result = talib.OBV(
                            c_data[common_index].values, 
                            v_data[common_index].values.astype(float)
                        )
                        result.loc[common_index, col] = calc_result
                except Exception as e:
                    print(f"OBV calculation failed for {col}: {e}")
                    continue
        
        return result
    
    def obv_signal(self, close: pd.DataFrame, vol: pd.DataFrame, window: int = 20) -> pd.DataFrame:
        """OBV信号线（OBV的移动平均）
        
        Args:
            close: 收盘价矩阵
            vol: 成交量矩阵
            window: 平滑窗口
            
        Returns:
            OBV信号线因子矩阵
        """
        obv = self.obv_line(close, vol)
        if obv.empty:
            return pd.DataFrame()
        
        return obv.rolling(window).mean()
    
    # ========== 波动率指标 ==========
    
    def atr_14(self, high: pd.DataFrame, low: pd.DataFrame, close: pd.DataFrame, window: int = 14) -> pd.DataFrame:
        """平均真实范围
        
        Args:
            high: 最高价矩阵
            low: 最低价矩阵
            close: 收盘价矩阵
            window: 计算窗口
            
        Returns:
            ATR因子矩阵
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
                        calc_result = talib.ATR(
                            h_data[common_index].values,
                            l_data[common_index].values,
                            c_data[common_index].values,
                            timeperiod=window
                        )
                        result.loc[common_index, col] = calc_result
                except Exception as e:
                    print(f"ATR calculation failed for {col}: {e}")
                    continue
        
        return result
    
    def natr_14(self, high: pd.DataFrame, low: pd.DataFrame, close: pd.DataFrame, window: int = 14) -> pd.DataFrame:
        """标准化平均真实范围
        
        Args:
            high: 最高价矩阵
            low: 最低价矩阵
            close: 收盘价矩阵
            window: 计算窗口
            
        Returns:
            NATR因子矩阵
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
                        calc_result = talib.NATR(
                            h_data[common_index].values,
                            l_data[common_index].values,
                            c_data[common_index].values,
                            timeperiod=window
                        )
                        result.loc[common_index, col] = calc_result
                except Exception as e:
                    print(f"NATR calculation failed for {col}: {e}")
                    continue
        
        return result
    
    def trange(self, high: pd.DataFrame, low: pd.DataFrame, close: pd.DataFrame) -> pd.DataFrame:
        """真实范围
        
        Args:
            high: 最高价矩阵
            low: 最低价矩阵
            close: 收盘价矩阵
            
        Returns:
            TRANGE因子矩阵
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
                    
                    if len(common_index) >= 2:
                        calc_result = talib.TRANGE(
                            h_data[common_index].values,
                            l_data[common_index].values,
                            c_data[common_index].values
                        )
                        result.loc[common_index, col] = calc_result
                except Exception as e:
                    print(f"TRANGE calculation failed for {col}: {e}")
                    continue
        
        return result
