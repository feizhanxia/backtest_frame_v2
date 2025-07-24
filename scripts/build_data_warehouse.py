import pandas as pd, datetime as dt
from pathlib import Path
from tqdm import tqdm
import logging
import concurrent.futures
import sys
import os

# 将项目根目录添加到 Python 路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine import data_fetcher as F, cleaner as C, storage as S

# 确保logs目录存在
logs_dir = Path(__file__).resolve().parents[1] / "logs"
logs_dir.mkdir(exist_ok=True)

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(logs_dir / "data_build.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("etf_data_warehouse")

# 配置参数
BASE  = Path(__file__).resolve().parents[1]   # 项目根目录
THREADS = 1  # 并行线程数

def process_target(code, force_refresh=False):
    """处理单个ETF/指数的数据获取和清洗流程
    
    Args:
        code: ETF/指数代码
        force_refresh: 是否强制刷新数据
        
    Returns:
        成功处理返回True，否则返回False
    """
    try:
        # 获取日线数据（自动获取全部历史数据，带缓存检查）
        price = F.fetch_daily_with_cache(code, start=None, end=dt.date.today().strftime("%Y%m%d"), 
                                        base_dir=str(BASE), force_refresh=force_refresh)
        
        # 检查数据是否有效（至少要有一定的数据量）
        if price is None or price.empty:
            logger.warning(f"⚠️ {code} 无法获取到数据，可能是新上市或已退市")
            return False
            
        # 检查数据量是否足够（至少要有100个交易日的数据才有分析价值）
        if len(price) < 100:
            logger.warning(f"⚠️ {code} 数据量不足（仅{len(price)}个交易日），跳过处理")
            return False
        
        # 清洗价格数据（移除停牌日等）
        price = C.clean_price(price)
        
        # ETF/指数只需要价格数据，直接存储
        if price is not None and not price.empty:
            # 存储processed数据
            S.save_processed_data(price, BASE, code)
            
            logger.info(f"✅ {code} 数据处理完成 ({len(price)}个交易日)")
            return True
        else:
            logger.warning(f"⚠️ {code} 清洗后数据为空")
            return False
            
    except Exception as e:
        logger.error(f"❌ 处理 {code} 时出错: {str(e)}")
        return False

def main():
    logger.info("开始构建ETF/指数数据仓库...")
    
    # 读取标的池 - 可以选择使用小标的池进行测试
    universe_file = "universe_small.csv"  # 使用小标的池
    # universe_file = "universe.csv"      # 使用完整标的池
    
    # 检查是否需要强制刷新
    import sys
    force_refresh = "--force" in sys.argv or "-f" in sys.argv
    if force_refresh:
        logger.info("🔄 强制刷新模式：将重新下载所有数据")
    
    try:
        codes = pd.read_csv(BASE/f"config/{universe_file}")["ts_code"].tolist()
        logger.info(f"标的池读取成功，共 {len(codes)} 个标的 (来源: {universe_file})")
    except Exception as e:
        logger.error(f"读取标的池失败: {str(e)}")
        return
    
    # 修改process_target函数调用，传递force_refresh参数
    def process_target_with_cache(code):
        return process_target(code, force_refresh)
    
    # 并行处理各标的数据
    success_count = 0
    with concurrent.futures.ThreadPoolExecutor(max_workers=THREADS) as executor:
        # 提交所有任务
        futures = {executor.submit(process_target_with_cache, code): code for code in codes}
        
        # 处理结果
        for future in tqdm(concurrent.futures.as_completed(futures), total=len(codes), ncols=80):
            code = futures[future]
            try:
                if future.result():
                    success_count += 1
            except Exception as e:
                logger.error(f"{code} 处理失败: {str(e)}")
    
    logger.info(f"✅ 数据仓刷新完成，成功处理 {success_count}/{len(codes)} 只股票")

if __name__ == "__main__":
    main()
