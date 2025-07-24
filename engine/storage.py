import hashlib, pyarrow.parquet as pq, pyarrow as pa, os
import pandas as pd
from datetime import datetime

def _hash_df(df):
    """计算DataFrame的哈希值（用于检测变化）
    
    Args:
        df: 输入数据框
        
    Returns:
        哈希字符串，格式为"行数_列数_哈希值前6位"
    """
    h = hashlib.md5(pd.util.hash_pandas_object(df, index=True).values)
    return f"{len(df)}_{len(df.columns)}_{h.hexdigest()[:6]}"

def to_parquet_partition(df: pd.DataFrame, base_dir: str, name: str):
    """将数据按年月分区存储为Parquet格式
    
    Args:
        df: 需要存储的数据框
        base_dir: 基础目录路径
        name: 文件名（不含扩展名）
        
    Returns:
        None
    """
    # base_dir/data/processed/2025/07/  name.parquet
    ym = df.index[-1].strftime("%Y/%m")
    dir_ = os.path.join(base_dir, "data", "processed", ym)
    os.makedirs(dir_, exist_ok=True)
    path = f"{dir_}/{name}.parquet"
    if os.path.exists(path):
        old = pq.read_table(path).to_pandas()
        if _hash_df(old) == _hash_df(df): return  # 无变化
    pq.write_table(pa.Table.from_pandas(df), path)

def save_raw_data(df: pd.DataFrame, base_dir: str, name: str, data_type: str):
    """保存原始数据到raw目录
    
    Args:
        df: 需要存储的原始数据框
        base_dir: 基础目录路径
        name: 文件名前缀（通常是标的代码）
        data_type: 数据类型（如'price', 'financial'等）
        
    Returns:
        None
    """
    # base_dir/data/raw/  name_type_yyyymmdd.parquet
    today = datetime.now().strftime("%Y%m%d")
    dir_ = os.path.join(base_dir, "data", "raw")
    os.makedirs(dir_, exist_ok=True)
    path = f"{dir_}/{name}_{data_type}_{today}.parquet"
    pq.write_table(pa.Table.from_pandas(df), path)

def save_processed_data(df: pd.DataFrame, base_dir: str, name: str):
    """保存处理后的数据（等同于to_parquet_partition）
    
    Args:
        df: 需要存储的处理后数据框
        base_dir: 基础目录路径
        name: 文件名（不含扩展名）
        
    Returns:
        None
    """
    to_parquet_partition(df, base_dir, name)
