import logging
import traceback
from  global_pars.Class_global_pars import *

__all__ = ['create_logging']
def create_logging(file_name,name):
    try:
        if isinstance(name, str) != 1:
            raise TypeError
    except Exception:
        traceback.print_exc()
        exit()
    ##定义日志格式
    if global_par.get_global_pars('debug') != 1:
        logger = logging.getLogger(name)
        logger.setLevel(level=logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    else:
        logger = logging.getLogger(__name__)
        logger.setLevel(level=logging.DEBUG)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s file:%(filename)s line:%(lineno)d fun:%(funcName)s')
    ##设置日志打印
    handler = logging.FileHandler(file_name)
    if global_par.get_global_pars('debug') != 1:
        handler.setLevel(logging.INFO)
    else:
        handler.setLevel(logging.DEBUG)
    handler.setFormatter(formatter)

    ##定义控制台输出
    console = logging.StreamHandler()
    if global_par.get_global_pars('debug') != 1:
        console.setLevel(logging.INFO)
    else:
        console.setLevel(logging.DEBUG)
    console.setFormatter(formatter)

    ##为longger增加2种输出
    logger.addHandler(handler)
    #logger.addHandler(console)

    logger.info("Longger System Create Finish")
    return logger
