# -*- coding: utf-8 -*-
"""
技术指标模块 - 统计函数和其他技术指标
包含统计函数等基础技术指标（已移除有问题的希尔伯特变换指标）
"""
import numpy as np
import pandas as pd
import talib
from .base_factor import BaseFactor


class TechnicalFactors(BaseFactor):
    """技术指标因子 - 包含统计函数"""
    
    def __init__(self):
        super().__init__()
    
    # ========== 统计函数 ==========
    
    def beta_5(self, close: pd.DataFrame, benchmark_close: pd.DataFrame, window: int = 5) -> pd.DataFrame:
        """Beta系数 (需要基准价格)
        
        Args:
            close: 收盘价矩阵
            benchmark_close: 基准收盘价矩阵
            window: 计算窗口
            
        Returns:
            Beta因子矩阵
        """
        if not self.validate_input_data(close):
            return pd.DataFrame()
        
        result = pd.DataFrame(index=close.index, columns=close.columns)
        # 简化版本：使用市场平均作为基准
        market_avg = close.mean(axis=1)
        
        for col in close.columns:
            series_data = close[col].dropna()
            if len(series_data) >= window + 5:
                try:
                    # 对齐数据
                    common_index = series_data.index.intersection(market_avg.index)
                    if len(common_index) >= window + 5:
                        calc_result = talib.BETA(
                            series_data[common_index].values,
                            market_avg[common_index].values,
                            timeperiod=window
                        )
                        result.loc[common_index, col] = calc_result
                except Exception as e:
                    print(f"BETA calculation failed for {col}: {e}")
                    continue
        
        return result
    
    def correl_5(self, close: pd.DataFrame, window: int = 5) -> pd.DataFrame:
        """皮尔逊相关系数 (与市场平均的相关性)
        
        Args:
            close: 收盘价矩阵
            window: 计算窗口
            
        Returns:
            相关性因子矩阵
        """
        if not self.validate_input_data(close):
            return pd.DataFrame()
        
        result = pd.DataFrame(index=close.index, columns=close.columns)
        market_avg = close.mean(axis=1)
        
        for col in close.columns:
            series_data = close[col].dropna()
            if len(series_data) >= window + 5:
                try:
                    # 对齐数据
                    common_index = series_data.index.intersection(market_avg.index)
                    if len(common_index) >= window + 5:
                        calc_result = talib.CORREL(
                            series_data[common_index].values,
                            market_avg[common_index].values,
                            timeperiod=window
                        )
                        result.loc[common_index, col] = calc_result
                except Exception as e:
                    print(f"CORREL calculation failed for {col}: {e}")
                    continue
        
        return result
    
    def linearreg_14(self, close: pd.DataFrame, window: int = 14) -> pd.DataFrame:
        """线性回归
        
        Args:
            close: 收盘价矩阵
            window: 计算窗口
            
        Returns:
            线性回归因子矩阵
        """
        if not self.validate_input_data(close):
            return pd.DataFrame()
        return self.apply_talib_to_dataframe(talib.LINEARREG, close, timeperiod=window)
    
    def stddev_20(self, close: pd.DataFrame, window: int = 20) -> pd.DataFrame:
        """标准差
        
        Args:
            close: 收盘价矩阵
            window: 计算窗口
            
        Returns:
            标准差因子矩阵
        """
        if not self.validate_input_data(close):
            return pd.DataFrame()
        return self.apply_talib_to_dataframe(talib.STDDEV, close, timeperiod=window)
    
    def tsf_14(self, close: pd.DataFrame, window: int = 14) -> pd.DataFrame:
        """时间序列预测
        
        Args:
            close: 收盘价矩阵
            window: 计算窗口
            
        Returns:
            TSF因子矩阵
        """
        if not self.validate_input_data(close):
            return pd.DataFrame()
        return self.apply_talib_to_dataframe(talib.TSF, close, timeperiod=window)
    
    def var_20(self, close: pd.DataFrame, window: int = 20) -> pd.DataFrame:
        """方差
        
        Args:
            close: 收盘价矩阵
            window: 计算窗口
            
        Returns:
            方差因子矩阵
        """
        if not self.validate_input_data(close):
            return pd.DataFrame()
        return self.apply_talib_to_dataframe(talib.VAR, close, timeperiod=window)
    
    def linearreg_angle(self, close: pd.DataFrame, window: int = 14) -> pd.DataFrame:
        """线性回归角度
        
        Args:
            close: 收盘价矩阵
            window: 计算窗口
            
        Returns:
            线性回归角度因子矩阵
        """
        if not self.validate_input_data(close):
            return pd.DataFrame()
        
        return self.apply_talib_to_dataframe(talib.LINEARREG_ANGLE, close, timeperiod=window)
    
    def linearreg_intercept(self, close: pd.DataFrame, window: int = 14) -> pd.DataFrame:
        """线性回归截距
        
        Args:
            close: 收盘价矩阵
            window: 计算窗口
            
        Returns:
            线性回归截距因子矩阵
        """
        if not self.validate_input_data(close):
            return pd.DataFrame()
        
        return self.apply_talib_to_dataframe(talib.LINEARREG_INTERCEPT, close, timeperiod=window)
    
    def linearreg_slope(self, close: pd.DataFrame, window: int = 14) -> pd.DataFrame:
        """线性回归斜率
        
        Args:
            close: 收盘价矩阵
            window: 计算窗口
            
        Returns:
            线性回归斜率因子矩阵
        """
        if not self.validate_input_data(close):
            return pd.DataFrame()
        
        return self.apply_talib_to_dataframe(talib.LINEARREG_SLOPE, close, timeperiod=window)
