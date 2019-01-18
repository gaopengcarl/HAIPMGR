"""
这是各种辅助和实现函数
编写者：高鹏
2018-12-21
"""


import socket
import pymysql.cursors
import psutil
import subprocess


__all__ = ['connect_mysqld','getl_ip_isincluter','is_mgrok_master','is_connect_gateway','is_vip_local','is_connect_ip','stop_vip','start_vip']

ipaddr = None #避免多次获取
g_ip_gateway = None #避免多次传递
##全部辅助函数




def return_cardname(logger,ipaddr,local_ip):
    """
    本辅助函数用于返回指定本地IP的网卡名
    :param ipaddr: ip_addr_get返回的信息如 [('192.168.99.101':'eth0'),]
    :return: 1 异常  正常网卡名称

    """
    logger.debug("fun:return_cardname: ipaddr {}".format(ipaddr))
    for i in ipaddr:
        if i[0] == local_ip:
            return i[1]
    return 1



def  is_connect_ip(logger,ip,platfrom):
    """
    本辅助函数用于检查指定IP是否能ping通
    :param logger: 日志系统
    :param ip: 待ping的IP地址
    :param platfrom: 平台
    :return: 0 能够ping通  1 不能ping通
    """
    try:
        assert platfrom in ['windows','linux'] #断言2种操作系统
    except Exception as e: #异常就需要退出了
        logger.error("fun:is_connect_ip: assert err {}".format(e), exc_info=True)
        exit(-1)

    if platfrom == 'windows':
        res = subprocess.getstatusoutput('ping -n 3'+ip)
        logger.info("fun:is_connect_ip: ping reslut is {}".format(res))

        if  '已接收 = 0' in res[1]:
            logger.info("fun:is_connect_ip: gateway ping is timeout".format(ip))
            return 1
        else:
            return 0

    if platfrom == 'linux':
        res = subprocess.getstatusoutput('/bin/ping -c 3 '+ip)
        logger.info("fun:is_connect_ip: ping reslut is {}".format(res))

        if  '0 received' in res[1]:
            logger.info("fun:is_connect_ip: {} ping is timeout".format(ip))
            return 1
        else:
            return 0


def err_conver(e):
    """
    这是一个辅助函数用于返回连接mysqld报错的错误码
    比如
    :param e:异常抛出
    :return: 错误码数字
    """
    list_a = list("{}".format(e))
    str_a = ''
    for i in range(1,5):
        str_a = str_a+list_a[i]
    #print(str_a)
    return int(str_a)

def ip_addr_get(info):
    """
    这是一个辅助函数用于输入一个psutil.net_if_addrs获得的IP信息转换一个
    列表信息，其中全是本机网卡对应的IP地址，最终返回
    :param info: psutil.net_if_addrs
    :return: 返回一个全部IP地址和网卡的列表 [('eth0':'192.168.99.101')]
    """
    netcard_info = []
    for k, v in info.items():
        for item in v:
            if item[0] == 2 and not item[1] == '127.0.0.1':
                netcard_info.append((item[1], k))
    return netcard_info

def is_port_up(logger,ip,port):
    """
    这是一个辅助函数用于检查端口存活性
    :param logger:日志系统
    :param ip: 检测服务器的IP
    :param port: 检测服务的端口
    :return: 0：正常 1：异常
    """
    s = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    try:
        if isinstance(ip,str) != 1 or isinstance(port,str) != 1:
            logger.error("fun:is_port_up:str req but type is ip:{} port:{}".format(type(ip),type(port)),exc_info = True)
            exit(-1)
        s.connect((ip,int(port)))
        s.shutdown(2)
        s.close()
        logger.info("fun:is_port_up:ip:{} port {} is test connect sucess!!".format(ip,port))
        return 0
    except Exception as e:
        logger.error("fun:is_port_up:{}".format(e),exc_info = True)
        return 1


##[STAGE1 检查函数]

def getl_ip_isincluter(logger,cluser_ip):
    """
    本函数用于返回本地IP地址,如果没有在集群列表中则返回1,需要比较IP地址和网卡名称两个方面
    :param logger:
    :param cluser_ip: 集群IP地址列表和网卡字典
    :return: 1 异常  成功返回匹配的本地地址
    """
    if isinstance(cluser_ip, dict) != 1:
        logger.error("fun:getl_ip_isincluter:dict req but type is {} ".format(type(cluser_ip)), exc_info=True)
        exit(-1)
    #
    info = psutil.net_if_addrs() #获取全部的网卡信息
    global  ipaddr #声明为全局变量
    ipaddr = ip_addr_get(info) #获得网卡信息形如 [('192.168.99.101':'eth0')]
    logger.info("fun:getl_ip_isincluter:local ip addr is {}".format(ipaddr)) #输出这些地址

    #print(list(cluser_ip.items()))
    for i in ipaddr:
        #print(i)
        if  i in (list(cluser_ip.items())): #如果这个网卡信息在cluster_ip字典中，及('192.168.99.101':'eth0')在cluster_ip字典中
            logger.info("fun:getl_ip_isincluter:local ip {} addr is in cluster {}".format(i[0],cluser_ip.items())) #则输出到日志
            return i[0]#并且返回这个IP信息 i[0]是IP信息 i[1]是网卡名

    logger.info("fun:getl_ip_isincluter:local ip addr {} [HAVE NO IP] in cluster {}".format(ipaddr,cluser_ip.items())) #否则找不到这个网卡信息
    return 1  #则代表在cluster_ip参数中不包含这个ip地址和网卡


##[STAGE2 检查函数]

def connect_mysqld(logger,*pars):
    """
    本函数用于检查是否能够连接上MYSQLD服务器进程，当前判断2个地方
    1、端口是否可用
    2、MYSQLD是否可连接
    :param logger:日志系统
    :param *pars:ip,port,user,passwd 的序列
    :return: 0 正常 1 异常
    """
    #is_port_up用于判断端口是否可用 is_mysqld_up用于判断mysqld是否可以连接
    #if is_port_up(logger,pars[0],pars[1]) == 0 and is_mysqld_up(logger,*pars) == 0:
    if is_mysqld_up(logger,*pars) == 0:
        return 0
    else:
        return 1

def is_mysqld_up(logger,*pars):
    """
    本函数用于检查MYSQLD线程在本地是否启动，如果没有启动MYSQLD其他检查的都是无谓的
    *pars 为ip,port,user,passwd
    :return: 0 关闭 1 启动
    """
    if len(pars) != 4:
        logger.error("fun:is_mysqld_up:req 5 parameter but {} give".format(len(pars)+1), exc_info=True)
        exit(-1)
    for i in pars:
        if isinstance(i,str) != 1:
            logger.error("fun:is_mysqld_up:str req but type is".format(type(i)), exc_info=True)
            exit(-1)
    #建立连接
    try:
        connect = pymysql.Connect(host=pars[0],port=int(pars[1]),user=pars[2],passwd=pars[3])
        connect.close()
        logger.info("fun:is_mysqld_up:{} connect mysqld sucess".format(pars[0]+' '+pars[1]+' '+ pars[2] ))
        return 0
    except Exception as e:
        #如果只是密码错误则说明mysqld可以连接，错误码为1045
        if err_conver(e) == 1045:
            logger.info("fun:is_mysqld_up:{} connect mysqld sucess but password error".format(pars))
            return 0
        else:
            logger.info("fun:is_mysqld_up:{}".format(e), exc_info=True)
            return 1

##[STAGE3 检查函数]

def is_mgrok_master(logger,ip,inter_port,port,user,passwd):
    """
    本函数用于检查MGR内部端口是否启动来检查MGR已经启动，然后判断本地节点是否为online状态并且在视图中，然后判断本节点是否是主节点
    :param logger: 日志系统
    :param ip: 本地ip
    :param inter_port: MGR paxos通信内部端口
    :param port: 本地mysqld端口
    :param user: 本地连接用户
    :param passwd: 用户名
    :return: 0 MGR内部端口存在且为主 1 MGR内部端口不存在或者不为主
    """

    #首先检查MGR内部端口是否存在
    results = [[None]] #初始化为None 避免访问数据失败的情况 master 节点查询结果
    results_local_online =  [[None]] #查看本地是否在集群中且状态为online


    #下面语句用于查询主节点在个节点上，不是主节点显然不应该启动VIP
    sql = """  select MEMBER_HOST MASTER_NODE from 
                     performance_schema.replication_group_members where MEMBER_ID in 
                    (select VARIABLE_VALUE from global_status where VARIABLE_NAME='group_replication_primary_member');
          """
    #下面语句用于查询本节点是否在集群中，并且状态正常对于recovering以及其他状态的显然不能启动VIP
    sql_local_online = """select count(*)  from replication_group_members where MEMBER_HOST='""" \
                       + socket.gethostname() + """' and MEMBER_STATE='ONLINE';"""

    #对内部端口的测试怕引起MGR故障
    # if is_port_up(logger, ip, inter_port) != 0:
    #     logger.info("fun:is_mgrok_master:{} MGR inter port {} test connect failed MGR is down?".format(ip,inter_port))
    #     return 1
    # else:
    #     logger.info("fun:is_mgrok_master: {} MGR inter port {} test connect sucess".format(ip, inter_port))

    #开始连接mysqld进行语句查询语句为

    try:
        connect = pymysql.Connect(host=ip,port=int(port),user=user,passwd=passwd,db="performance_schema")
        logger.info("fun:is_mgrok_master: connect mysqld sucess")
        cursor = connect.cursor()
        ##获取主节点信息 主节点可能为空值就是返回一个空元组()
        cursor.execute(sql)
        results = cursor.fetchall()

        ##获取本地在集群中且状态为online results_local_online应该为1为正常 必须=1 因为要么有结果count(*) = 1要么没结果
        ##count(*) = 0 都应该是一行
        cursor.execute(sql_local_online)
        results_local_online =  cursor.fetchall()

        connect.close()
    except Exception as e:
        logger.info("fun:is_mgrok_master:{}".format(e), exc_info=True)
        #exit(-1)# (到这里任何数据库的错误应该是退出，如果返回return 1 那么可能造成VIP异常关闭?)
        #return 1  # 数据库异常不做任何判断
        #这里2次跑数据 压力大？断开？
        # 依赖VIP操作的2次检查否则可能出现异常关闭VIP的情况

    try:
        assert len(results) < 2 #断言只有1行或者0行
        assert len(results_local_online) == 1 #断言只有1行
    except Exception as e:
            logger.error("fun:is_mgrok_master:{}".format(e), exc_info=True)
            exit(-1) # 断言失败应该退出

    try: ##bug IndexError: tuple index out of range 没有数据返回的时候
        if not(results): ##如果结果返回为空值()
            hostname = None
            logger.info("fun:is_mgrok_master: no data find {}")
        else:
            hostname = results[0][0] #第一个0代表第一行 第二个0代表是第一行的第一个字段 二维数组
    except Exception as e:
        logger.info("fun:is_mgrok_master: fin data error as {}".format(e), exc_info=True)
        hostname = None


    if results_local_online[0][0] != 1: #判断本地状态为online， 否则返回1
        logger.info(
            "fun:is_mgrok_master: current host {} is not in online status or not in replication_group_members view".format(
                socket.gethostname(), hostname))
        return 1

    logger.info("fun:is_mgrok_master: current host {} is MGR online node {}".format(socket.gethostname(), hostname))

    if socket.gethostname() != hostname:#如果语句获取的主机名字和获取的主机名不一致，那么不是主
        logger.info(
            "fun:is_mgrok_master: current host {} is not MGR master node {}".format(socket.gethostname(), hostname))
        return 1

    #否则 说明paxos inter端口可通并且是主
    logger.info("fun:is_mgrok_master: current host {} is MGR master node {}".format(socket.gethostname(),hostname))
    return 0


##[STAGE4 检查函数]
def  is_connect_gateway(logger,ip_gateway,platfrom):
    """
    :param logger: 日志系统
    :param ip_gateway: 网关
    :param platfrom: 平台
    :return: 0 能够ping通  1 不能ping通
    """
    global g_ip_gateway
    g_ip_gateway = ip_gateway
    return is_connect_ip(logger,ip_gateway,platfrom)



##[STAGE5]
def is_vip_local(logger,vip):
    """
    这个函数用于确认VIP是否在本地
    :param vip:参数设置中的VIP值
    :return: 0 vip在本地 1 vip不在本地
    """

    global ipaddr #已经在函数 getl_ip_isincluter 中获取过了
    #print(list(cluser_ip.items()))
    for i in ipaddr:
        #print(i)
        if  vip == i[0]: #如果vip和其中一个网卡IP相等说明在本地
            logger.info("fun:is_vip_local: check vip {} is hit local ip {}".format(vip,i))
            return 0 #代表在本地

    logger.info("fun:is_vip_local:check vip {} is not hit local ip".format(vip)) #否则找不到这个网卡信息
    return 1  #代表没在本地

##[STAGE6]

def stop_vip(logger,vip,platfrom,local_ip,port):
    """

    :param logger:日志系统
    :param vip: 虚拟IP
    :param platfrom: 系统平台
    :param local_ip: 绑定虚拟IP的本地IP
    :param port: 这里使用MYSQL的端口作为绑定的标示
    :return:0 启动正常 1 ifconfig命令失败
    """
    global ipaddr
    global g_ip_gateway
    netcard = return_cardname(logger,ipaddr, local_ip)
    try:
        assert platfrom in ['windows', 'linux']  # 断言2种操作系统
        assert netcard != 1  # 到这里localip 一定有一个本地网卡否则出现异常需要退出
    except Exception as e:  # 异常就需要退出了
        logger.error("fun:stop_vip: assert err {}".format(e), exc_info=True)
        exit(-1)

    if platfrom == 'windows': #windows 先不考虑了
        pass

    if platfrom == 'linux':
        #ifconfig eth0:3306 down
        res = subprocess.getstatusoutput('/sbin/ifconfig ' + netcard + ':' + port + " down")
        if res[0] != 0:
            logger.warning("fun:stop_vip: ifconfig command exe error! {}".format(res), exc_info=True)
            return 1 #执行ifconfig失败

        logger.info("fun:stop_vip: ifconfig command sucess Vip:{} is down from {}".format(vip, netcard + ':' + port))

    return 0



def start_vip(logger,vip,platfrom,local_ip,port):
    """
    启动虚拟IP
    :param logger: 日志系统
    :param vip: 虚拟IP
    :param platfrom: 系统平台
    :param local_ip: 绑定虚拟IP的本地IP
    :param port: 这里使用MYSQL的端口作为绑定的标示
    :return:0 启动正常 1 ifconfig命令失败
    """
    global ipaddr
    global g_ip_gateway
    netcard = return_cardname(logger,ipaddr, local_ip)

    try:
        assert platfrom in ['windows','linux'] #断言2种操作系统
        assert netcard != 1 #到这里localip 一定有一个本地网卡否则出现异常需要退出
    except Exception as e: #异常就需要退出了
        logger.error("fun:start_vip: assert err {}".format(e), exc_info=True)
        exit(-1)

    if platfrom == 'windows':  # windows 先不考虑了
        pass

    if platfrom == 'linux':
        #ifconfig eth0:3306 192.168.99.132
        res = subprocess.getstatusoutput('/sbin/ifconfig ' +netcard+':'+port+' ' + vip )
        if res[0] != 0:
            logger.warning("fun:start_vip: ifconfig command exe error! {}".format(res), exc_info=True)
            return 1 #执行ifconfig失败
        #arping -I eth0 -c 3 -s 192.168.99.132 192.168.99.10
        res = subprocess.getstatusoutput("/sbin/arping -I " + netcard + " -c 3 -s " + vip + " " + g_ip_gateway)
        logger.info("fun:start_vip:arping result is {}".format(res))
        logger.info("fun:start_vip: ifconfig command sucess Vip:{} is start on {}".format(vip, netcard + ':' + port))

    return 0 #正常标示

