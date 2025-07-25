# -*- coding: utf-8 -*-
"""
基础因子类 - 所有因子类的基类
提供通用的数据预处理和标准化功能
"""
import numpy as np
import pandas as pd
import talib
from typing import Dict, Optional
import warnings

# 抑制 pandas 版本兼容性警告
warnings.filterwarnings('ignore', category=FutureWarning, message='.*fillna.*method.*')
warnings.filterwarnings('ignore', category=FutureWarning, message='.*Downcasting.*')


class BaseFactor:
    """因子计算基类"""
    
    def __init__(self):
        """初始化基础因子类"""
        pass
    
    def standardize(self, factor: pd.DataFrame) -> pd.DataFrame:
        """标准化因子值
        
        Args:
            factor: 原始因子矩阵
            
        Returns:
            标准化后的因子矩阵
        """
        if factor.empty:
            return factor
            
        # 截面标准化
        standardized = factor.sub(factor.mean(axis=1), axis=0).div(factor.std(axis=1), axis=0)
        
        # 处理无限值和NaN
        standardized = standardized.replace([np.inf, -np.inf], np.nan)
        
        return standardized
    
    def winsorize(self, factor: pd.DataFrame, quantile: float = 0.05) -> pd.DataFrame:
        """去极值处理
        
        Args:
            factor: 因子矩阵
            quantile: 分位数阈值
            
        Returns:
            去极值后的因子矩阵
        """
        if factor.empty:
            return factor
            
        # 按行（时间）去极值
        def winsorize_row(row):
            if row.isna().all():
                return row
            q_low = row.quantile(quantile)
            q_high = row.quantile(1 - quantile)
            return row.clip(lower=q_low, upper=q_high)
        
        return factor.apply(winsorize_row, axis=1)
    
    def neutralize(self, factor: pd.DataFrame, market_cap: pd.DataFrame) -> pd.DataFrame:
        """市值中性化处理
        
        Args:
            factor: 因子矩阵
            market_cap: 市值矩阵
            
        Returns:
            中性化后的因子矩阵
        """
        if factor.empty or market_cap.empty:
            return factor
            
        # 对数市值
        log_market_cap = np.log(market_cap)
        
        # 按时间回归去除市值影响
        neutralized = factor.copy()
        for date in factor.index:
            if date in log_market_cap.index:
                y = factor.loc[date].dropna()
                x = log_market_cap.loc[date].reindex(y.index).dropna()
                
                # 确保数据对齐
                common_stocks = y.index.intersection(x.index)
                if len(common_stocks) > 1:
                    y_aligned = y[common_stocks]
                    x_aligned = x[common_stocks]
                    
                    # 线性回归
                    try:
                        coef = np.polyfit(x_aligned, y_aligned, 1)[0]
                        residual = y_aligned - coef * x_aligned
                        neutralized.loc[date, common_stocks] = residual
                    except:
                        # 回归失败时保持原值
                        pass
        
        return neutralized
    
    def fill_missing_values(self, factor: pd.DataFrame, method: str = 'median') -> pd.DataFrame:
        """填充缺失值
        
        Args:
            factor: 因子矩阵
            method: 填充方法 ('median', 'mean', 'zero', 'forward', 'backward')
            
        Returns:
            填充后的因子矩阵
        """
        if factor.empty:
            return factor
            
        if method == 'median':
            return factor.fillna(factor.median(axis=1), axis=0)
        elif method == 'mean':
            return factor.fillna(factor.mean(axis=1), axis=0)
        elif method == 'zero':
            return factor.fillna(0)
        elif method == 'forward':
            return factor.fillna(method='ffill')
        elif method == 'backward':
            return factor.fillna(method='bfill')
        else:
            return factor
    
    def safe_talib_call(self, func, *args, **kwargs):
        """安全调用TA-Lib函数
        
        Args:
            func: TA-Lib函数
            *args: 位置参数
            **kwargs: 关键字参数
            
        Returns:
            计算结果或None
        """
        try:
            return func(*args, **kwargs)
        except Exception as e:
            print(f"TA-Lib函数调用失败: {func.__name__}, 错误: {e}")
            return None
    
    def apply_talib_to_dataframe(self, func, data: pd.DataFrame, *args, **kwargs) -> pd.DataFrame:
        """将TA-Lib函数应用到DataFrame
        
        Args:
            func: TA-Lib函数
            data: 输入数据
            *args: 额外参数
            **kwargs: 关键字参数
            
        Returns:
            计算结果DataFrame
        """
        if data.empty:
            return pd.DataFrame()
            
        result = pd.DataFrame(index=data.index, columns=data.columns)
        
        for col in data.columns:
            series_data = data[col].dropna()
            if len(series_data) > 0:
                try:
                    calc_result = func(series_data.values, *args, **kwargs)
                    if calc_result is not None:
                        # 处理多个返回值的情况
                        if isinstance(calc_result, tuple):
                            calc_result = calc_result[0]  # 取第一个返回值
                        result.loc[series_data.index, col] = calc_result
                except Exception as e:
                    print(f"计算 {col} 时出错: {e}")
                    continue
        
        return result
    
    def validate_input_data(self, *data_frames) -> bool:
        """验证输入数据的有效性
        
        Args:
            *data_frames: 输入的DataFrame列表
            
        Returns:
            是否有效
        """
        for df in data_frames:
            if df is None or df.empty:
                return False
            if not isinstance(df, pd.DataFrame):
                return False
        return True
