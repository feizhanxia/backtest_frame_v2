import pandas as pd, datetime as dt
from pathlib import Path
from tqdm import tqdm
import logging
import concurrent.futures
import sys
import os

# 将项目根目录添加到 Python 路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine import data_fetcher as F, aligner as A, cleaner as C, storage as S

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("data_build.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("etf_data_warehouse")

# 配置参数
START = "20220101"
START_Q = "20210101"
BASE  = Path(__file__).resolve().parents[1]   # 项目根目录
THREADS = 5  # 并行线程数

def process_target(code):
    """处理单个ETF/指数的数据获取和清洗流程
    
    Args:
        code: ETF/指数代码
        
    Returns:
        成功处理返回True，否则返回False
    """
    try:
        # 获取日线数据（自动识别资产类型）
        price = F.fetch_daily(code, START, dt.date.today().strftime("%Y%m%d"))
        
        # 保存原始价格数据
        S.save_raw_data(price, BASE, code, "price")
        
        # 清洗价格数据
        price = C.clean_price(price)
        
        # ETF/指数不需要财务数据，直接进行数据对齐和存储
        if not price.empty:
            # 对齐数据（简化版，只处理价格数据）
            aligned_data = A.align_data(price, None)  # 不传入财务数据
            
            # 存储processed数据
            S.save_processed_data(aligned_data, BASE, code)
            
            logger.info(f"✅ {code} 数据处理完成")
            return True
        else:
            logger.warning(f"⚠️ {code} 价格数据为空")
            return False
            
    except Exception as e:
        logger.error(f"❌ 处理 {code} 时出错: {str(e)}")
        return False

def main():
    logger.info("开始构建ETF/指数数据仓库...")
    
    # 读取标的池
    try:
        codes = pd.read_csv(BASE/"config/universe.csv")["ts_code"].tolist()
        logger.info(f"标的池读取成功，共 {len(codes)} 个标的")
    except Exception as e:
        logger.error(f"读取标的池失败: {str(e)}")
        return
    
    # 并行处理各标的数据
    success_count = 0
    with concurrent.futures.ThreadPoolExecutor(max_workers=THREADS) as executor:
        # 提交所有任务
        futures = {executor.submit(process_target, code): code for code in codes}
        
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
