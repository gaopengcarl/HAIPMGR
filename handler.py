
"""
这是接口类
编写者：高鹏
2018-12-21
"""

#python 3.6中也可以使用方便使用抽象类 from abc import ABC,abstractmethod
from abc import ABC, abstractmethod
from  logger.Fun_log_create import  *
from global_pars.Class_global_pars import *


__all__ = ['Handller','Wroker']

class Handller(ABC):
    """
    抽象接口
    """
    @abstractmethod
    def env_init(self,debug,env_par):
        """
        接口函数用于初始化各种子模块
        :return: 0 错误 1 正常
        """
        pass
    def check_stat(self):
        """
        接口函数用于检查所有的状态
        :return: 0 正常 1 失败
        """
        pass

    def check_vip(self,stat):
        """
        检查VIP的函数接口
        :return: 0 关闭 1 维持 2 启动
        """
        pass

    def oper_vip(self,stat):
        """
        启动VIP的函数接口
        :return:
        """
        pass

    def check_par(self,par_var):
        """
        检查参数接口
        :param par_var:
        :return:
        """
        pass


class Wroker():
    """
    调用类，做相应的解耦
    """
    def __init__(self,handler):
        self.vip_handler = handler
        self.logger = None
    def env_init(self,debug,env_par):
        """
        环境初始化辅助类主要用于初始化日志系统
        :param debug: 是否开启debug
        :param env_par: 自定义的环境变量字典列表
        :return: 无返回值
        """
        #下面初始化日志系统模块
        global_par.set_global_pars('debug', debug) #不开启debug 加入到全局参数
        self.logger =  create_logging(env_par['install_path']+'HAIPMGR'+str(env_par['mysql_port']+'.log'), 'HAIPMGR') #设置日志系统
        global_par.set_global_pars('logger', self.logger)  # 将日志指针加入到全局参数

        #下面初始化其他参数
        try:
            self.vip_handler.env_init(env_par)
        except Exception as e:
            self.logger.error(e,exc_info = True)
            exit(-1) #异常退出



    def check_stat(self):  #检查基本状态 4 阶段
        return self.vip_handler.check_stat()

    def check_vip(self,stat):#检查VIP状态
        return self.vip_handler.check_vip(stat)

    def oper_vip(self,stat): #做vip操作
        return self.vip_handler.oper_vip(stat)

    def check_par(self,par_var): #进行参数检查
        self.vip_handler.check_par(par_var)

