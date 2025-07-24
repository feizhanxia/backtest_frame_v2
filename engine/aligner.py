import pandas as pd
import logging

# 设置pandas选项，选择未来行为，避免FutureWarning
pd.set_option('future.no_silent_downcasting', True)

def align_data(price_data: pd.DataFrame, fin_data: pd.DataFrame = None) -> pd.DataFrame:
    """对齐价格数据和财务数据（ETF/指数简化版）
    
    Args:
        price_data: 价格数据
        fin_data: 财务数据（对于ETF/指数可以为None）
        
    Returns:
        对齐后的数据
    """
    if fin_data is None or fin_data.empty:
        # ETF/指数情况：只返回价格数据
        return price_data
    else:
        # 股票情况：对齐财务数据到价格数据
        aligned_fin = align_financial_to_daily(fin_data, price_data.index)
        return price_data.join(aligned_fin, how='left')

def align_financial_to_daily(fin: pd.DataFrame, dates: pd.DatetimeIndex) -> pd.DataFrame:
    """将财报数据对齐到日线数据，确保无前视偏差
    
    Args:
        fin: 财务数据
        dates: 需要对齐到的日期索引（通常是价格数据的索引）
        
    Returns:
        对齐后的财务数据，以dates为索引
    """
    # 检查财务数据是否为空
    if fin.empty:
        # 如果财务数据为空，返回一个只包含空值的DataFrame
        aligned = pd.DataFrame(index=dates)
        aligned["roe_ttm"] = None
        aligned["pb"] = None
        return aligned
    
    # 每行财报向后对齐到 pub_date 当天收盘后可见 → 第二个交易日生效
    fin = fin.sort_values("pub_date").ffill()
    aligned = pd.DataFrame(index=dates)
    
    for col in ["roe_ttm", "pb"]:
        if col in fin.columns:
            # 显式指定数据类型，避免自动转换产生警告
            series = pd.Series(index=fin["pub_date"], data=fin[col].values, dtype='float64')
            # 使用明确的类型进行填充和偏移操作
            aligned[col] = series.reindex(dates).ffill().shift(1)
        else:
            # 如果列不存在，添加一个全为NaN的列，显式指定类型为float64
            logging.warning(f"财务数据中缺少 {col} 列，将创建空列")
            aligned[col] = pd.Series(index=dates, dtype='float64')
            
    return aligned
