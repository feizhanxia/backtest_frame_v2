# -*- coding: utf-8 -*-
"""
重叠研究指标模块 - 各种移动平均线和趋势指标
包含SMA、EMA、DEMA、WMA等重叠研究指标
"""
import numpy as np
import pandas as pd
import talib
from .base_factor import BaseFactor


class OverlapFactors(BaseFactor):
    """重叠研究指标因子"""
    
    def __init__(self):
        super().__init__()
    
    def sma_20(self, close: pd.DataFrame, window: int = 20) -> pd.DataFrame:
        """简单移动平均线
        
        Args:
            close: 收盘价矩阵
            window: 计算窗口
            
        Returns:
            SMA因子矩阵
        """
        if not self.validate_input_data(close):
            return pd.DataFrame()
        return close.rolling(window).mean()
    
    def ema_20(self, close: pd.DataFrame, window: int = 20) -> pd.DataFrame:
        """指数移动平均线
        
        Args:
            close: 收盘价矩阵
            window: 计算窗口
            
        Returns:
            EMA因子矩阵
        """
        if not self.validate_input_data(close):
            return pd.DataFrame()
        return self.apply_talib_to_dataframe(talib.EMA, close, timeperiod=window)
    
    def dema_20(self, close: pd.DataFrame, window: int = 20) -> pd.DataFrame:
        """双指数移动平均线
        
        Args:
            close: 收盘价矩阵
            window: 计算窗口
            
        Returns:
            DEMA因子矩阵
        """
        if not self.validate_input_data(close):
            return pd.DataFrame()
        return self.apply_talib_to_dataframe(talib.DEMA, close, timeperiod=window)
    
    def wma_20(self, close: pd.DataFrame, window: int = 20) -> pd.DataFrame:
        """加权移动平均线
        
        Args:
            close: 收盘价矩阵
            window: 计算窗口
            
        Returns:
            WMA因子矩阵
        """
        if not self.validate_input_data(close):
            return pd.DataFrame()
        return self.apply_talib_to_dataframe(talib.WMA, close, timeperiod=window)
    
    def trima_20(self, close: pd.DataFrame, window: int = 20) -> pd.DataFrame:
        """三角移动平均线
        
        Args:
            close: 收盘价矩阵
            window: 计算窗口
            
        Returns:
            TRIMA因子矩阵
        """
        if not self.validate_input_data(close):
            return pd.DataFrame()
        return self.apply_talib_to_dataframe(talib.TRIMA, close, timeperiod=window)
    
    def t3_20(self, close: pd.DataFrame, window: int = 20, vfactor: float = 0.7) -> pd.DataFrame:
        """三重指数移动平均线T3
        
        Args:
            close: 收盘价矩阵
            window: 计算窗口
            vfactor: 体积因子
            
        Returns:
            T3因子矩阵
        """
        if not self.validate_input_data(close):
            return pd.DataFrame()
        
        result = pd.DataFrame(index=close.index, columns=close.columns)
        
        for col in close.columns:
            series_data = close[col].dropna()
            if len(series_data) >= window * 3:  # T3需要更多数据
                try:
                    calc_result = talib.T3(series_data.values, timeperiod=window, vfactor=vfactor)
                    result.loc[series_data.index, col] = calc_result
                except Exception as e:
                    print(f"T3 calculation failed for {col}: {e}")
                    continue
        
        return result
    
    def midpoint_14(self, close: pd.DataFrame, window: int = 14) -> pd.DataFrame:
        """中点
        
        Args:
            close: 收盘价矩阵
            window: 计算窗口
            
        Returns:
            中点因子矩阵
        """
        if not self.validate_input_data(close):
            return pd.DataFrame()
        return self.apply_talib_to_dataframe(talib.MIDPOINT, close, timeperiod=window)
    
    def midprice_14(self, high: pd.DataFrame, low: pd.DataFrame, window: int = 14) -> pd.DataFrame:
        """中点价格
        
        Args:
            high: 最高价矩阵
            low: 最低价矩阵
            window: 计算窗口
            
        Returns:
            中点价格因子矩阵
        """
        if not self.validate_input_data(high, low):
            return pd.DataFrame()
        
        result = pd.DataFrame(index=high.index, columns=high.columns)
        
        for col in high.columns:
            if col in low.columns:
                high_series = high[col].dropna()
                low_series = low[col].dropna()
                common_index = high_series.index.intersection(low_series.index)
                
                if len(common_index) >= window:
                    try:
                        calc_result = talib.MIDPRICE(
                            high_series[common_index].values,
                            low_series[common_index].values,
                            timeperiod=window
                        )
                        result.loc[common_index, col] = calc_result
                    except Exception as e:
                        print(f"MIDPRICE calculation failed for {col}: {e}")
                        continue
        
        return result
    
    def ht_trendline(self, close: pd.DataFrame) -> pd.DataFrame:
        """希尔伯特变换趋势线
        
        Args:
            close: 收盘价矩阵
            
        Returns:
            HT趋势线因子矩阵
        """
        if not self.validate_input_data(close):
            return pd.DataFrame()
        
        result = pd.DataFrame(index=close.index, columns=close.columns)
        
        for col in close.columns:
            series_data = close[col].dropna()
            if len(series_data) >= 63:  # HT需要至少63个数据点
                try:
                    calc_result = talib.HT_TRENDLINE(series_data.values)
                    result.loc[series_data.index, col] = calc_result
                except Exception as e:
                    print(f"HT_TRENDLINE calculation failed for {col}: {e}")
                    continue
        
        return result
    
    def tema_20(self, close: pd.DataFrame, window: int = 20) -> pd.DataFrame:
        """三重指数移动平均线
        
        Args:
            close: 收盘价矩阵
            window: 计算窗口
            
        Returns:
            TEMA因子矩阵
        """
        if not self.validate_input_data(close):
            return pd.DataFrame()
        return self.apply_talib_to_dataframe(talib.TEMA, close, timeperiod=window)
    
    def kama_20(self, close: pd.DataFrame, window: int = 20) -> pd.DataFrame:
        """Kaufman 自适应移动平均线
        
        Args:
            close: 收盘价矩阵
            window: 计算窗口
            
        Returns:
            KAMA因子矩阵
        """
        if not self.validate_input_data(close):
            return pd.DataFrame()
        return self.apply_talib_to_dataframe(talib.KAMA, close, timeperiod=window)
    
    def sar(self, high: pd.DataFrame, low: pd.DataFrame, 
            acceleration: float = 0.02, maximum: float = 0.2) -> pd.DataFrame:
        """抛物线SAR
        
        Args:
            high: 最高价矩阵
            low: 最低价矩阵
            acceleration: 加速因子
            maximum: 最大加速因子
            
        Returns:
            SAR因子矩阵
        """
        if not self.validate_input_data(high, low):
            return pd.DataFrame()
        
        result = pd.DataFrame(index=high.index, columns=high.columns)
        
        for col in high.columns:
            if col in low.columns:
                high_series = high[col].dropna()
                low_series = low[col].dropna()
                common_index = high_series.index.intersection(low_series.index)
                
                if len(common_index) >= 10:
                    try:
                        calc_result = talib.SAR(
                            high_series[common_index].values,
                            low_series[common_index].values,
                            acceleration=acceleration, 
                            maximum=maximum
                        )
                        result.loc[common_index, col] = calc_result
                    except Exception as e:
                        print(f"SAR calculation failed for {col}: {e}")
                        continue
        
        return result
    
    # ========== 价格变换指标 ==========
    
    def avgprice(self, open_price: pd.DataFrame, high: pd.DataFrame, 
                 low: pd.DataFrame, close: pd.DataFrame) -> pd.DataFrame:
        """平均价格
        
        Args:
            open_price: 开盘价矩阵
            high: 最高价矩阵
            low: 最低价矩阵
            close: 收盘价矩阵
            
        Returns:
            平均价格因子矩阵
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
                    
                    if len(common_index) > 0:
                        calc_result = talib.AVGPRICE(
                            o_data[common_index].values,
                            h_data[common_index].values,
                            l_data[common_index].values,
                            c_data[common_index].values
                        )
                        result.loc[common_index, col] = calc_result
                except Exception as e:
                    print(f"AVGPRICE calculation failed for {col}: {e}")
                    continue
        
        return result
    
    def medprice(self, high: pd.DataFrame, low: pd.DataFrame) -> pd.DataFrame:
        """中位数价格
        
        Args:
            high: 最高价矩阵
            low: 最低价矩阵
            
        Returns:
            中位数价格因子矩阵
        """
        if not self.validate_input_data(high, low):
            return pd.DataFrame()
        
        result = pd.DataFrame(index=high.index, columns=high.columns)
        
        for col in high.columns:
            if col in low.columns:
                high_series = high[col].dropna()
                low_series = low[col].dropna()
                common_index = high_series.index.intersection(low_series.index)
                
                if len(common_index) > 0:
                    try:
                        calc_result = talib.MEDPRICE(
                            high_series[common_index].values,
                            low_series[common_index].values
                        )
                        result.loc[common_index, col] = calc_result
                    except Exception as e:
                        print(f"MEDPRICE calculation failed for {col}: {e}")
                        continue
        
        return result
    
    def typprice(self, high: pd.DataFrame, low: pd.DataFrame, close: pd.DataFrame) -> pd.DataFrame:
        """典型价格
        
        Args:
            high: 最高价矩阵
            low: 最低价矩阵
            close: 收盘价矩阵
            
        Returns:
            典型价格因子矩阵
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
                    
                    if len(common_index) > 0:
                        calc_result = talib.TYPPRICE(
                            h_data[common_index].values,
                            l_data[common_index].values,
                            c_data[common_index].values
                        )
                        result.loc[common_index, col] = calc_result
                except Exception as e:
                    print(f"TYPPRICE calculation failed for {col}: {e}")
                    continue
        
        return result
    
    def wclprice(self, high: pd.DataFrame, low: pd.DataFrame, close: pd.DataFrame) -> pd.DataFrame:
        """加权收盘价格
        
        Args:
            high: 最高价矩阵
            low: 最低价矩阵
            close: 收盘价矩阵
            
        Returns:
            加权收盘价格因子矩阵
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
                    
                    if len(common_index) > 0:
                        calc_result = talib.WCLPRICE(
                            h_data[common_index].values,
                            l_data[common_index].values,
                            c_data[common_index].values
                        )
                        result.loc[common_index, col] = calc_result
                except Exception as e:
                    print(f"WCLPRICE calculation failed for {col}: {e}")
                    continue
        
        return result
