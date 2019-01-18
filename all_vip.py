"""
这是VIP检查的类
编写者：高鹏
2018-12-21
"""

from handler import *
from logger.Fun_log_create import  *
from global_pars.Class_global_pars import *
from my_exception.exception import *
from tool import *
import time
import sys


__all__ = ['all_vip']

class all_vip(Handller):
    """实现类"""
    def __init__(self):
        self.logger = None #日志系统指针
        self.parameter = None #全局参数指针
        self.set_fun = None #高阶函数指针 用于设置一个全局参数
        self.get_fun = None #高阶函数指针 用于获取一个全局参数
        self.local_ip = None #本地IP
        self.par_key = ["vip", "cluser_ip", "ip_gateway", "mysql_port", \
                        "inter_port", "passwd", "user", "platfrom","sleeptime","install_path"] #参数列表
    def env_init(self,env_par):
        '''
        本函数初始化各种参数包括日志系统、将解析的参数加入到全局参数
        :param env_par: 解析命令行得到的参数为一个key-value字典
        :return: 1 err 0 ok
        '''
        self.set_fun = global_par.set_global_pars
        self.get_fun = global_par.get_global_pars
        self.parameter = global_par.get_all_global_pars()

        self.logger =  self.get_fun("logger") #获取初始化好的日志系统logger指针

        if isinstance(env_par,dict) != 1:
            raise Data_type_err("dict require but type is {}".format(type(env_par)))
            return 1

        for par in env_par: #初始化全部参数变量到全集变量字典
            self.set_fun(par,env_par[par])
        self.logger.info("all_vip.env_init: All parameter [INIT] complete!! is:")

        for i in (self.parameter):
            if i == 'passwd':
                pass
            else:
                self.logger.info("parameter {} values is {}".format(i,self.parameter[i]))


        self.set_fun("eret", "unkown return values unkown error") #这里只是增加到全局参数列表便于方便书写
        return 0

    def check_stat(self):
        """
        本函数作为最主要的检查函数，通过检查还需要判断VIP是否已经启动来最终判断是否需要
        打开VIP或者关闭VIP或者维持现状，VIP检查函数见后面，这样做是为了让本函数支持keepalived
        检查。
        :return: 0  状态检查成功需要开启VIP 1 状态检查失败需要关闭VIP
        本函数平台无关可以用于windows和linux
        """

        ##[STAGE1]:
        ##检查本机IP是否在集群中 检查方法:通过获取本机的网卡地址和网卡名称和参数字典cluser_ip中的值网卡地址和名称进行对比
        ##如果在则继续
        ##如果不在则 return 1
        ##getl_ip_isincluter 函数成功放回本机IP地址,失败返回 1

        self.logger.info("all_vip.check_stat:[STAGE1]-------------------------------------")
        self.local_ip = getl_ip_isincluter(self.logger,self.get_fun('cluser_ip'))
        if self.local_ip != 1 :
            self.logger.info("all_vip.check_stat:[STAGE1] check scuess: local ip {} \
            is in cluster {}".format(self.local_ip,self.get_fun('cluser_ip')))
        else:
            self.logger.info("all_vip.check_stat:[STAGE1] check failed!: local ip {} \
            is not in cluster {}".format(self.local_ip,self.get_fun('cluser_ip')))
            return 1

        ##[STAGE2]:
        ##检查mysqld是否启动 检查方法:1、端口是否可用 2、mysqld是否可以连接
        ##如果启动则继续
        ##如果没有启动则 return 1
        ##connect_mysqld 函数成功返回0,失败返回1
        self.logger.info("all_vip.check_stat:[STAGE2]-------------------------------------")

        if connect_mysqld(self.logger, self.local_ip, self.get_fun('mysql_port'), self.get_fun('user'),self.get_fun('passwd')) == 0:
            self.logger.info("all_vip.check_stat:[STAGE2] mysqld ip:{} port:{} connect scuess".format(\
                self.local_ip,self.get_fun('mysql_port')))
        else:
            self.logger.info("all_vip.check_stat:[STAGE2] check failed!:mysqld ip:{} port{} connect \
            failed".format(self.local_ip,self.get_fun('mysql_port')))
            return 1

        ##[STAGE3]:
        ##检查MGR是否启动以及是否是本节点是主 检查方法:1、检查MGR的paxos通信端口是否可用 2、检查本机是否在MGR中且为online 3、通过脚本检查本节点是否是MGR的主节点
        ##如果是则继续
        ##如果不是则 return 1
        ##is_mgrok_master 函数成功返回0,失败返回1

        self.logger.info("all_vip.check_stat:[STAGE3]-------------------------------------")
        if is_mgrok_master(self.logger,self.local_ip,self.get_fun('inter_port'),self.get_fun('mysql_port'),self.get_fun('user'),\
                           self.get_fun('passwd')) == 0:
            self.logger.info("all_vip.check_stat:[STAGE3] check scuess: mysqld ip:{} is master \
            node".format(self.local_ip))
        else:
            self.logger.info("all_vip.check_stat:[STAGE3] check failed!: mysqld ip:{}  not master node check log!".format(self.local_ip))
            return 1

        ##[STAGE4]
        ##检查最后一种情况也就是如果出现了网络断开的情况,测试中这情况根据语句会查出2个主，但是不满足大多数节点的部分不能进行事物,因为收到不到
        ##回执的tickets,事物会一直hang住,因此数据不用担心.但是作为VIP检测程序还是需要判断这种情况,因为我们的服务器都是通过路由器连接因此可以简单
        ##的检测到网关的连通性。
        ##检查网络断开 检查方法:检查网关的连通性
        ##如果连通则继续
        ##否则 return 1
        ##is_connect_gateway 函数成功返回0,失败返回1
        self.logger.info("all_vip.check_stat:[STAGE4]-------------------------------------")

        if is_connect_gateway(self.logger,self.get_fun('ip_gateway'),self.get_fun('platfrom')) == 0:
            self.logger.info("all_vip.check_stat:[STAGE4] check sucess: gateway {} is connect sucess".\
                             format(self.get_fun('ip_gateway')))
        else:
            self.logger.info("all_vip.check_stat:[STAGE4] check failed!: gateway {} is connect failed".\
                                format(self.get_fun('ip_gateway')))
            return 1

        return 0 #最后 4 阶段检查通过 返回正常标示 0


    def check_vip(self,stat):
        """
        本函数主要用于拿到check_stat的返回值,然后做VIP操作的判断
        :param stat: check_stat函数返回的检测值
        :return: 0 关闭 1 维持 2 启动
        """
        self.logger.info("all_vip.check_vip:[STAGE5]-------------------------------------")
        # is_vip_local 返回0 vip在本地 1 vip不在本地
        temp_stat = is_vip_local(self.logger,self.get_fun('vip'))

        # 是否需要启动vip
        if stat == 0:  #如果需要启动VIP
            self.logger.info("all_vip.check_vip:Vip {} must start on this node".format(self.get_fun('vip')))
            # 虚拟VIP是否在本地
            if temp_stat == 0:  #如果在本地
                self.logger.info("all_vip.check_vip:Vip {} is on this node keep it".format(self.get_fun('vip')))
                return 1 #则维持现状即可
            elif temp_stat == 1: #如果不在本地
                self.logger.info("all_vip.check_vip:Vip {} is not on this node,check other node get this vip to start vip".format(self.get_fun('vip')))
                # 如果还能ping通VIP则本次循环维持现状,等待下次循环检测 这里还避免一种网络问题导致MGR分块的恢复网络后的问题
                if not(is_connect_ip(self.logger,self.get_fun('vip'),self.get_fun('platfrom'))) :
                    self.logger.warning("all_vip.check_vip:wait other node stop vip")
                    return 1 #维持现状
                ##下面做二次检查因为启动VIP是重要事件
                self.logger.warning("all_vip.check_vip:start vip is import event twice check begin-----")
                if self.check_stat() != 0:
                    self.logger.info("all_vip.check_vip:twice check to start vip failed! next check!")
                    return 1 #维持现状
                return 2  #这里就是如果ping不通了就可以启动VIP了
            else: #以外返回值控制
                self.logger.error("all_vip.check_vip[1]:"+self.get_fun("eret"))
                exit(-1)

        if stat == 1: #如果需要关闭VIP
            # 虚拟VIP是否在本地关闭
            self.logger.info("all_vip.check_vip:Vip {} must stop on this node".format(self.get_fun('vip')))
            if temp_stat == 0:  # 如果在本地
                self.logger.info("all_vip.check_vip:Vip {} is on this node stop it".format(self.get_fun('vip')))
                self.logger.warning("all_vip.check_vip:stop vip is import event twice check begin-----")
                ##下面做二次检查因为关闭VIP是重要事件
                if self.check_stat() != 1:
                    self.logger.info("all_vip.check_vip:twice to check stop vip failed! next check!")
                    return 1 #维持现状
                return 0 #需要关闭
            elif temp_stat == 1: #如果不在本地
                self.logger.info("all_vip.check_vip:Vip {} is not on this node keep it".format(self.get_fun('vip')))
                return 1 #维持现状
            else:  # 以外返回值控制
                self.logger.error("all_vip.check_vip[2]:" + self.get_fun("eret"))
                exit(-1)

        if stat not in (0,1): #以外返回值控制
            self.logger.error("all_vip.check_vip[3]:" + self.get_fun("eret"))
            exit(-1)

    def oper_vip(self,stat):
        """
        根据最终的状态,及check_vip返回的状态做操作VIP (0 关闭 1 维持 2 启动)
        :param stat: check_vip返回的状态
        :return: 没有返回值
        """
        self.logger.info("all_vip.oper_vip:[STAGE6]-------------------------------------")
        if stat == 0:

            fd_stat = self.get_fun("fd_stat") #写入监控文件
            fd_stat.seek(0,0)
            fd_stat.write("0")
            fd_stat.flush()

            if stop_vip(self.logger,self.get_fun('vip'),self.get_fun('platfrom'),self.local_ip,self.get_fun('mysql_port')) == 0:
                self.logger.warning("all_vip.oper_vip:Vip {} stop ok!".format(self.get_fun('vip')))
            else:
                pass #如果失败继续循环

        elif stat == 1:

            self.logger.info("all_vip.oper_vip:Vip opertion keep on ") #不做操作 保持现有状态

        elif stat == 2:

            fd_stat = self.get_fun("fd_stat") #写入监控文件
            fd_stat.seek(0,0)
            fd_stat.write("2")
            fd_stat.flush()

            #start_vip(logger,vip,platfrom,local_ip,port):
            if start_vip(self.logger,self.get_fun('vip'),self.get_fun('platfrom'),self.local_ip,self.get_fun('mysql_port')) == 0:
                self.logger.warning("all_vip.oper_vip:Vip {} start ok on {}".format(self.get_fun('vip'),self.local_ip))
            else:
                pass #如果ifconfig命令失败继续循环

        else:
            self.logger.error("all_vip.oper_vip[1]:" + self.get_fun("eret"))
            exit(-1)


    def check_par(self,par_var):
        """
        本函数用于检查参数列表是否合规
        :param 待检查的参数字典:
        :return: 没有返回值
        """
        if len(par_var) != len(self.par_key):
            self.logger.error("all_vip.check_par:parameter numbers is error req {} but is {}".format(len(self.par_key),len(par_var)))
            exit(-1)


        for i in par_var:  ##检查所有参数在参数列表中
            if i not in self.par_key:  # 字样检查通过
                self.logger.error("all_vip.check_par:parameter not in parameter list error parameter is: {}".format(i))
                exit(-1)

            if isinstance(i, str) != 1:  # key 类型检查通过
                self.logger.error("all_vip.check_par:parameter key type check error error parameter is: {}".format(i))
                exit(-1)

            if i == 'cluser_ip':
                if isinstance(par_var[i], dict) != 1:
                    self.logger.error(
                        "all_vip.check_par:parameter value type check error req dict but is {} error parameter is: {}".format(type(par_var[i]), i))
                    exit(-1)
            elif i == "sleeptime":
                if isinstance(par_var[i], int) != 1:
                    self.logger.error(
                        "all_vip.check_par:parameter value type check error req int but is {} error parameter is: {}".format(type(par_var[i]), i))
                    exit(-1)
            else:
                if isinstance(par_var[i], str) != 1:
                    self.logger.error(
                        "all_vip.check_par:parameter value type check error req int but is {} error parameter is: {}".format(type(par_var[i]), i))
                    exit(-1)
            if  i == 'install_path':
                if par_var['install_path'][-1:] != '/':
                    self.logger.error(
                        "all_vip.check_par:parameter value for parameter {} check error req '/' at end of path get path is".format(
                            'install_path' , par_var['install_path']))
                    print("all_vip.check_par:parameter value for parameter {} check error req '/' at end of path get path is{}".format(
                            'install_path' , par_var['install_path']))
                    sys.stdout.flush()
                    exit(-1)

        return

