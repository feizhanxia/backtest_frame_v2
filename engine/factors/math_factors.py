# -*- coding: utf-8 -*-
"""
数学变换因子模块 - 数学函数和运算符
包含三角函数、对数函数、算术运算等数学变换
"""
import numpy as np
import pandas as pd
import talib
from .base_factor import BaseFactor


class MathFactors(BaseFactor):
    """数学变换因子"""
    
    def __init__(self):
        super().__init__()
    
    def sin_transform(self, close: pd.DataFrame) -> pd.DataFrame:
        """正弦变换
        
        Args:
            close: 收盘价矩阵
            
        Returns:
            正弦变换因子矩阵
        """
        if not self.validate_input_data(close):
            return pd.DataFrame()
        
        return self.apply_talib_to_dataframe(talib.SIN, close)
    
    def cos_transform(self, close: pd.DataFrame) -> pd.DataFrame:
        """余弦变换
        
        Args:
            close: 收盘价矩阵
            
        Returns:
            余弦变换因子矩阵
        """
        if not self.validate_input_data(close):
            return pd.DataFrame()
        
        return self.apply_talib_to_dataframe(talib.COS, close)
    
    def ln_transform(self, close: pd.DataFrame) -> pd.DataFrame:
        """自然对数变换
        
        Args:
            close: 收盘价矩阵
            
        Returns:
            对数变换因子矩阵
        """
        if not self.validate_input_data(close):
            return pd.DataFrame()
        
        # 确保数据为正值
        close_positive = close.clip(lower=0.001)
        return self.apply_talib_to_dataframe(talib.LN, close_positive)
    
    def log10_transform(self, close: pd.DataFrame) -> pd.DataFrame:
        """以10为底的对数变换
        
        Args:
            close: 收盘价矩阵
            
        Returns:
            log10变换因子矩阵
        """
        if not self.validate_input_data(close):
            return pd.DataFrame()
        
        # 确保数据为正值
        close_positive = close.clip(lower=0.001)
        return self.apply_talib_to_dataframe(talib.LOG10, close_positive)
    
    def sqrt_transform(self, close: pd.DataFrame) -> pd.DataFrame:
        """平方根变换
        
        Args:
            close: 收盘价矩阵
            
        Returns:
            平方根变换因子矩阵
        """
        if not self.validate_input_data(close):
            return pd.DataFrame()
        
        # 确保数据为非负值
        close_nonneg = close.clip(lower=0)
        return self.apply_talib_to_dataframe(talib.SQRT, close_nonneg)
    
    def exp_transform(self, close: pd.DataFrame) -> pd.DataFrame:
        """指数变换
        
        Args:
            close: 收盘价矩阵
            
        Returns:
            指数变换因子矩阵
        """
        if not self.validate_input_data(close):
            return pd.DataFrame()
        
        # 对输入进行缩放避免溢出
        close_scaled = close / close.abs().max().max() if close.abs().max().max() > 0 else close
        return self.apply_talib_to_dataframe(talib.EXP, close_scaled)
    
    def tanh_transform(self, close: pd.DataFrame) -> pd.DataFrame:
        """双曲正切变换
        
        Args:
            close: 收盘价矩阵
            
        Returns:
            双曲正切变换因子矩阵
        """
        if not self.validate_input_data(close):
            return pd.DataFrame()
        
        # 对输入进行标准化避免数值问题
        close_std = close.ffill()
        # 使用滚动标准化
        rolling_mean = close_std.rolling(window=20, min_periods=1).mean()
        rolling_std = close_std.rolling(window=20, min_periods=1).std()
        close_normalized = (close_std - rolling_mean) / (rolling_std + 1e-8)
        # 限制范围避免tanh溢出
        close_normalized = close_normalized.clip(-5, 5)
        
        return self.apply_talib_to_dataframe(talib.TANH, close_normalized)
    
    def floor_transform(self, close: pd.DataFrame) -> pd.DataFrame:
        """向下取整变换
        
        Args:
            close: 收盘价矩阵
            
        Returns:
            向下取整因子矩阵
        """
        if not self.validate_input_data(close):
            return pd.DataFrame()
        
        return self.apply_talib_to_dataframe(talib.FLOOR, close)
    
    def ceil_transform(self, close: pd.DataFrame) -> pd.DataFrame:
        """向上取整变换
        
        Args:
            close: 收盘价矩阵
            
        Returns:
            向上取整因子矩阵
        """
        if not self.validate_input_data(close):
            return pd.DataFrame()
        
        return self.apply_talib_to_dataframe(talib.CEIL, close)
    
    def max_value(self, close: pd.DataFrame, window: int = 30) -> pd.DataFrame:
        """滚动最大值
        
        Args:
            close: 收盘价矩阵
            window: 计算窗口
            
        Returns:
            滚动最大值因子矩阵
        """
        if not self.validate_input_data(close):
            return pd.DataFrame()
        
        return self.apply_talib_to_dataframe(talib.MAX, close, timeperiod=window)
    
    def min_value(self, close: pd.DataFrame, window: int = 30) -> pd.DataFrame:
        """滚动最小值
        
        Args:
            close: 收盘价矩阵
            window: 计算窗口
            
        Returns:
            滚动最小值因子矩阵
        """
        if not self.validate_input_data(close):
            return pd.DataFrame()
        
        return self.apply_talib_to_dataframe(talib.MIN, close, timeperiod=window)
    
    def sum_value(self, close: pd.DataFrame, window: int = 30) -> pd.DataFrame:
        """滚动求和
        
        Args:
            close: 收盘价矩阵
            window: 计算窗口
            
        Returns:
            滚动求和因子矩阵
        """
        if not self.validate_input_data(close):
            return pd.DataFrame()
        
        return self.apply_talib_to_dataframe(talib.SUM, close, timeperiod=window)
    
    def maxindex_value(self, close: pd.DataFrame, window: int = 30) -> pd.DataFrame:
        """滚动最大值索引
        
        Args:
            close: 收盘价矩阵
            window: 计算窗口
            
        Returns:
            滚动最大值索引因子矩阵
        """
        if not self.validate_input_data(close):
            return pd.DataFrame()
        
        return self.apply_talib_to_dataframe(talib.MAXINDEX, close, timeperiod=window)
    
    def minindex_value(self, close: pd.DataFrame, window: int = 30) -> pd.DataFrame:
        """滚动最小值索引
        
        Args:
            close: 收盘价矩阵
            window: 计算窗口
            
        Returns:
            滚动最小值索引因子矩阵
        """
        if not self.validate_input_data(close):
            return pd.DataFrame()
        
        return self.apply_talib_to_dataframe(talib.MININDEX, close, timeperiod=window)
    
    def minmax_range(self, close: pd.DataFrame, window: int = 30) -> pd.DataFrame:
        """滚动极差 (最大值-最小值)
        
        Args:
            close: 收盘价矩阵
            window: 计算窗口
            
        Returns:
            滚动极差因子矩阵
        """
        if not self.validate_input_data(close):
            return pd.DataFrame()
        
        result = pd.DataFrame(index=close.index, columns=close.columns)
        
        for col in close.columns:
            series_data = close[col].ffill().dropna()
            if len(series_data) >= window + 5:
                try:
                    min_vals, max_vals = talib.MINMAX(series_data.values, timeperiod=window)
                    result.loc[series_data.index, col] = max_vals - min_vals
                except Exception as e:
                    print(f"MINMAX range calculation failed for {col}: {e}")
                    continue
        
        return result
    
    def acos_transform(self, close: pd.DataFrame) -> pd.DataFrame:
        """反余弦变换
        
        Args:
            close: 收盘价矩阵
            
        Returns:
            反余弦变换因子矩阵
        """
        if not self.validate_input_data(close):
            return pd.DataFrame()
        
        # 标准化到[-1, 1]范围
        close_std = close.ffill()
        # 使用滚动标准化
        rolling_mean = close_std.rolling(window=20, min_periods=1).mean()
        rolling_std = close_std.rolling(window=20, min_periods=1).std()
        close_normalized = (close_std - rolling_mean) / (rolling_std + 1e-8)
        close_normalized = close_normalized.clip(-0.99, 0.99)  # 稍微收缩范围避免边界问题
        
        return self.apply_talib_to_dataframe(talib.ACOS, close_normalized)
    
    def asin_transform(self, close: pd.DataFrame) -> pd.DataFrame:
        """反正弦变换
        
        Args:
            close: 收盘价矩阵
            
        Returns:
            反正弦变换因子矩阵
        """
        if not self.validate_input_data(close):
            return pd.DataFrame()
        
        # 标准化到[-1, 1]范围
        close_std = close.ffill()
        # 使用滚动标准化
        rolling_mean = close_std.rolling(window=20, min_periods=1).mean()
        rolling_std = close_std.rolling(window=20, min_periods=1).std()
        close_normalized = (close_std - rolling_mean) / (rolling_std + 1e-8)
        close_normalized = close_normalized.clip(-0.99, 0.99)  # 稍微收缩范围避免边界问题
        
        return self.apply_talib_to_dataframe(talib.ASIN, close_normalized)
    
    def atan_transform(self, close: pd.DataFrame) -> pd.DataFrame:
        """反正切变换
        
        Args:
            close: 收盘价矩阵
            
        Returns:
            反正切变换因子矩阵
        """
        if not self.validate_input_data(close):
            return pd.DataFrame()
        
        return self.apply_talib_to_dataframe(talib.ATAN, close)
    
    def cosh_transform(self, close: pd.DataFrame) -> pd.DataFrame:
        """双曲余弦变换
        
        Args:
            close: 收盘价矩阵
            
        Returns:
            双曲余弦变换因子矩阵
        """
        if not self.validate_input_data(close):
            return pd.DataFrame()
        
        # 对输入进行缩放避免溢出
        close_scaled = close / (close.abs().max().max() + 1e-8) if close.abs().max().max() > 0 else close
        return self.apply_talib_to_dataframe(talib.COSH, close_scaled)
    
    def sinh_transform(self, close: pd.DataFrame) -> pd.DataFrame:
        """双曲正弦变换
        
        Args:
            close: 收盘价矩阵
            
        Returns:
            双曲正弦变换因子矩阵
        """
        if not self.validate_input_data(close):
            return pd.DataFrame()
        
        # 对输入进行缩放避免溢出
        close_scaled = close / (close.abs().max().max() + 1e-8) if close.abs().max().max() > 0 else close
        return self.apply_talib_to_dataframe(talib.SINH, close_scaled)
    
    def tan_transform(self, close: pd.DataFrame) -> pd.DataFrame:
        """正切变换
        
        Args:
            close: 收盘价矩阵
            
        Returns:
            正切变换因子矩阵
        """
        if not self.validate_input_data(close):
            return pd.DataFrame()
        
        return self.apply_talib_to_dataframe(talib.TAN, close)
    
    def price_add(self, close1: pd.DataFrame, close2: pd.DataFrame) -> pd.DataFrame:
        """价格相加
        
        Args:
            close1: 收盘价矩阵1
            close2: 收盘价矩阵2
            
        Returns:
            价格相加因子矩阵
        """
        if not self.validate_input_data(close1, close2):
            return pd.DataFrame()
        
        result = pd.DataFrame(index=close1.index, columns=close1.columns)
        
        for col in close1.columns:
            if col in close2.columns:
                series1 = close1[col].ffill().dropna()
                series2 = close2[col].ffill().dropna()
                common_index = series1.index.intersection(series2.index)
                
                if len(common_index) > 5:
                    try:
                        calc_result = talib.ADD(
                            series1[common_index].values,
                            series2[common_index].values
                        )
                        result.loc[common_index, col] = calc_result
                    except Exception as e:
                        print(f"ADD calculation failed for {col}: {e}")
                        continue
        
        return result
    
    def price_div(self, close1: pd.DataFrame, close2: pd.DataFrame) -> pd.DataFrame:
        """价格相除
        
        Args:
            close1: 收盘价矩阵1 (被除数)
            close2: 收盘价矩阵2 (除数)
            
        Returns:
            价格相除因子矩阵
        """
        if not self.validate_input_data(close1, close2):
            return pd.DataFrame()
        
        result = pd.DataFrame(index=close1.index, columns=close1.columns)
        
        for col in close1.columns:
            if col in close2.columns:
                series1 = close1[col].ffill().dropna()
                series2 = close2[col].ffill().dropna()
                common_index = series1.index.intersection(series2.index)
                
                if len(common_index) > 5:
                    try:
                        # 避免除零
                        series2_safe = series2[common_index].replace(0, 1e-8)
                        calc_result = talib.DIV(
                            series1[common_index].values,
                            series2_safe.values
                        )
                        result.loc[common_index, col] = calc_result
                    except Exception as e:
                        print(f"DIV calculation failed for {col}: {e}")
                        continue
        
        return result
    
    def price_mult(self, close1: pd.DataFrame, close2: pd.DataFrame) -> pd.DataFrame:
        """价格相乘
        
        Args:
            close1: 收盘价矩阵1
            close2: 收盘价矩阵2
            
        Returns:
            价格相乘因子矩阵
        """
        if not self.validate_input_data(close1, close2):
            return pd.DataFrame()
        
        result = pd.DataFrame(index=close1.index, columns=close1.columns)
        
        for col in close1.columns:
            if col in close2.columns:
                series1 = close1[col].ffill().dropna()
                series2 = close2[col].ffill().dropna()
                common_index = series1.index.intersection(series2.index)
                
                if len(common_index) > 5:
                    try:
                        calc_result = talib.MULT(
                            series1[common_index].values,
                            series2[common_index].values
                        )
                        result.loc[common_index, col] = calc_result
                    except Exception as e:
                        print(f"MULT calculation failed for {col}: {e}")
                        continue
        
        return result
    
    def price_sub(self, close1: pd.DataFrame, close2: pd.DataFrame) -> pd.DataFrame:
        """价格相减
        
        Args:
            close1: 收盘价矩阵1 (被减数)
            close2: 收盘价矩阵2 (减数)
            
        Returns:
            价格相减因子矩阵
        """
        if not self.validate_input_data(close1, close2):
            return pd.DataFrame()
        
        result = pd.DataFrame(index=close1.index, columns=close1.columns)
        
        for col in close1.columns:
            if col in close2.columns:
                series1 = close1[col].ffill().dropna()
                series2 = close2[col].ffill().dropna()
                common_index = series1.index.intersection(series2.index)
                
                if len(common_index) > 5:
                    try:
                        calc_result = talib.SUB(
                            series1[common_index].values,
                            series2[common_index].values
                        )
                        result.loc[common_index, col] = calc_result
                    except Exception as e:
                        print(f"SUB calculation failed for {col}: {e}")
                        continue
        
        return result
