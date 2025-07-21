import pandas as pd
import numpy as np

def winsorize(df, q=(0.01,0.99)):
    """截断异常值（分位数法）
    
    Args:
        df: 输入数据框
        q: 分位数范围，默认为1%和99%分位数
        
    Returns:
        处理后的数据框
    """
    lo, hi = df.quantile(q[0], axis=1), df.quantile(q[1], axis=1)
    return df.clip(lower=lo, upper=hi, axis=0)

def zscore(df):
    """对数据进行标准化（横截面Z-Score）
    
    Args:
        df: 输入数据框
        
    Returns:
        标准化后的数据框
    """
    return (df.sub(df.mean(axis=1), axis=0)
              .div(df.std(axis=1, ddof=0), axis=0))

def clean_price(df):
    """清洗价格数据，去除停牌日
    
    Args:
        df: 价格数据
        
    Returns:
        清洗后的数据框
    """
    return df[df["vol"]>0]      # 停牌日剔除

def clean_factor(mat):
    """因子数据清洗标准流程：去极值+标准化
    
    Args:
        mat: 因子矩阵
        
    Returns:
        清洗后的因子矩阵
    """
    mat = winsorize(mat)
    mat = zscore(mat)
    return mat
