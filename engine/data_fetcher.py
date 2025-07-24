import os, datetime as dt, warnings, tushare as ts, pandas as pd
import pyarrow.parquet as pq
import hashlib
from pathlib import Path
from dotenv import load_dotenv; load_dotenv()

# 忽略来自pandas的FutureWarning
warnings.filterwarnings("ignore", category=FutureWarning, module="pandas")
# 忽略来自tushare的FutureWarning
warnings.filterwarnings("ignore", category=FutureWarning, module="tushare")

pro = ts.pro_api(os.getenv("TUSHARE_TOKEN"))

def _get_data_hash(ts_code: str, start: str = None, end: str = None) -> str:
    """生成数据请求的哈希标识
    
    Args:
        ts_code: 标的代码
        start: 起始日期，None表示全部历史
        end: 结束日期，None表示到今天
        
    Returns:
        数据请求的哈希字符串
    """
    start_str = start if start is not None else "all"
    end_str = end if end is not None else "today"
    request_str = f"{ts_code}_{start_str}_{end_str}"
    return hashlib.md5(request_str.encode()).hexdigest()[:12]

def _check_existing_data(ts_code: str, start: str = None, end: str = None, base_dir: str = None) -> pd.DataFrame:
    """检查是否已有相同时间范围的数据
    
    Args:
        ts_code: 标的代码
        start: 起始日期，格式YYYYMMDD。None表示从最早开始
        end: 结束日期，格式YYYYMMDD。None表示到今天
        base_dir: 基础目录（可选）
        
    Returns:
        如果存在且符合要求，返回现有数据；否则返回空DataFrame
    """
    if base_dir is None:
        # 默认查找当前工作目录的processed数据
        base_dir = Path.cwd()
    
    processed_path = Path(base_dir) / "data" / "processed" / f"{ts_code}.parquet"
    
    if not processed_path.exists():
        return pd.DataFrame()
    
    try:
        existing_df = pq.read_table(processed_path).to_pandas()
        if existing_df.empty:
            return pd.DataFrame()
        
        # 确保索引是datetime类型
        if not isinstance(existing_df.index, pd.DatetimeIndex):
            existing_df.index = pd.to_datetime(existing_df.index)
        
        # 设置默认结束日期为今天
        if end is None:
            import datetime as dt
            end = dt.date.today().strftime("%Y%m%d")
        
        end_date = pd.to_datetime(end, format='%Y%m%d')
        
        # 检查现有数据的时间范围
        data_start = existing_df.index.min()
        data_end = existing_df.index.max()
        
        # 如果start为None，表示要获取全部历史数据，不检查起始日期
        if start is None:
            # 只检查结束日期：现有数据应该足够新（最多滞后1天）
            end_gap = (end_date - data_end).days
            if end_gap <= 1:
                print(f"✅ {ts_code} 使用缓存数据 ({len(existing_df)}天, {data_start.strftime('%Y-%m-%d')}~{data_end.strftime('%Y-%m-%d')})")
                return existing_df
            else:
                print(f"🔄 {ts_code} 数据需要更新 (现有数据到: {data_end.strftime('%Y-%m-%d')}, 需要到: {end_date.strftime('%Y-%m-%d')})")
                return pd.DataFrame()
        else:
            # 转换请求的起始日期格式
            start_date = pd.to_datetime(start, format='%Y%m%d')
            
            # 检查数据覆盖情况：
            # 1. 起始日期：现有数据开始日期应该接近或早于请求日期（允许几天差异，因为交易日历差异）
            # 2. 结束日期：现有数据应该足够新（最多滞后1天）
            
            start_gap = (data_start - start_date).days
            end_gap = (end_date - data_end).days
            
            # 起始日期检查：允许现有数据稍晚开始（因为交易日历），但不超过5天
            start_ok = start_gap <= 5
            # 结束日期检查：允许最多滞后1天
            end_ok = end_gap <= 1
            
            if start_ok and end_ok:
                # 过滤到有效数据范围
                actual_start = max(start_date, data_start)
            actual_end = min(end_date, data_end)  
            mask = (existing_df.index >= actual_start) & (existing_df.index <= actual_end)
            filtered_df = existing_df[mask]
            
            # 验证数据质量
            if len(filtered_df) >= 100:  # 至少100个交易日
                print(f"✅ {ts_code} 使用缓存数据 ({len(filtered_df)}天, {data_start.date()}~{data_end.date()})")
                return filtered_df
        
        # 数据覆盖不足，需要更新
        print(f"🔄 {ts_code} 需要更新数据 (现有: {data_start.date()}~{data_end.date()}, 请求: {start_date.date()}~{end_date.date()}, 开始差{start_gap}天, 结束差{end_gap}天)")
        return pd.DataFrame()
        
    except Exception as e:
        print(f"⚠️ 检查 {ts_code} 缓存时出错: {e}")
        return pd.DataFrame()

def fetch_daily_with_cache(ts_code: str, start: str = None, end: str = None, asset_type: str = 'auto', 
                          base_dir: str = None, force_refresh: bool = False) -> pd.DataFrame:
    """获取日线数据（带缓存检查）
    
    Args:
        ts_code: 标的代码（如：000001.SZ, 510050.SH, 000300.SH）
        start: 起始日期，格式YYYYMMDD。None表示获取全部历史数据
        end: 结束日期，格式YYYYMMDD。None表示到今天
        asset_type: 资产类型，'stock'(股票), 'fund'(ETF), 'index'(指数), 'auto'(自动识别)
        base_dir: 基础目录路径
        force_refresh: 是否强制刷新数据
        
    Returns:
        前复权后的日线数据，以trade_date为索引
    """
    # 设置默认结束日期为今天
    if end is None:
        import datetime as dt
        end = dt.date.today().strftime("%Y%m%d")
    
    # 如果不强制刷新，先检查现有数据
    if not force_refresh:
        existing_data = _check_existing_data(ts_code, start, end, base_dir)
        if not existing_data.empty:
            return existing_data
    
    # 没有缓存或需要刷新，调用原有的获取逻辑
    print(f"🔄 {ts_code} 从API获取数据...")
    return fetch_daily(ts_code, start, end, asset_type)

def fetch_daily(ts_code: str, start: str = None, end: str = None, asset_type: str = 'auto') -> pd.DataFrame:
    """获取日线数据（股票/ETF/指数，已前复权）
    
    Args:
        ts_code: 标的代码（如：000001.SZ, 510050.SH, 000300.SH）
        start: 起始日期，格式YYYYMMDD。None表示获取全部历史数据
        end: 结束日期，格式YYYYMMDD。None表示到今天
        asset_type: 资产类型，'stock'(股票), 'fund'(ETF), 'index'(指数), 'auto'(自动识别)
        
    Returns:
        前复权后的日线数据，以trade_date为索引
    """
    try:
        # 设置默认结束日期为今天
        if end is None:
            import datetime as dt
            end = dt.date.today().strftime("%Y%m%d")
            
        # 自动识别资产类型
        if asset_type == 'auto':
            if ts_code.startswith(('510', '511', '512', '513', '515', '516', '518')):
                asset_type = 'fund'  # ETF
            elif (ts_code.startswith(('000', '399')) and ('SH' in ts_code or 'SZ' in ts_code)) or \
                 (ts_code.endswith('.CSI')):
                # 指数（000300.SH, 399001.SZ, 932000.CSI等）
                asset_type = 'index'
            else:
                asset_type = 'stock'  # 默认为股票
        
        # 根据资产类型选择合适的接口
        if asset_type == 'fund':
            # ETF使用fund_daily接口
            df = pro.fund_daily(ts_code=ts_code, start_date=start, end_date=end)
            if df is None or df.empty:
                # 备选：使用pro_bar接口
                df = ts.pro_bar(ts_code=ts_code, start_date=start, end_date=end, 
                               adj='qfq', freq='D', asset='FD')
            # !TODO: ETF数据需要获取复权因子来进行额外处理
        elif asset_type == 'index':
            # 指数使用index_daily接口
            df = pro.index_daily(ts_code=ts_code, start_date=start, end_date=end)
            if df is None or df.empty:
                # 备选：使用pro_bar接口
                df = ts.pro_bar(ts_code=ts_code, start_date=start, end_date=end, 
                               freq='D', asset='I')
        else:
            # 股票使用原有逻辑
            df = ts.pro_bar(ts_code=ts_code, start_date=start, end_date=end, 
                           adj='qfq', freq='D', asset='E')
        
        # 如果主要接口失败，尝试通用pro_bar接口
        if df is None or df.empty:
            print(f"警告：主接口获取 {ts_code} 的数据为空，尝试通用接口...")
            df = ts.pro_bar(ts_code=ts_code, start_date=start, end_date=end, 
                           adj='qfq', freq='D')
        
        # 如果数据仍然为空，则记录错误
        if df is None or df.empty:
            raise ValueError(f"无法获取 {ts_code} 的日线数据")
            
        # 确保数据按日期排序
        df = df.sort_values("trade_date")
        
        # 检查必要的列是否存在
        required_cols = ["open", "high", "low", "close"]
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            raise ValueError(f"获取的数据缺少必要的列：{missing_cols}")
        
        # 确保包含vol和amount列（某些指数可能没有）
        if 'vol' not in df.columns:
            df['vol'] = 0  # 指数没有成交量，设为0
        if 'amount' not in df.columns:
            df['amount'] = 0  # 指数没有成交额，设为0
        # 转换日期格式
        df["trade_date"] = pd.to_datetime(df["trade_date"])
        
        # 提取需要的列并返回
        return df.set_index("trade_date")
    except Exception as e:
        print(f"获取 {ts_code} 的日线数据时出错: {str(e)}")
        # 创建一个空的DataFrame作为替代
        return pd.DataFrame(columns=["ts_code", "open", "high", "low", "close", "vol", "amount"])

# 删除财务数据获取函数，ETF/指数不需要财务数据
# def fetch_financial() 函数已移除
