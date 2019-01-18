"""
这是入口函数
编写者：高鹏
2018-12-21
"""

#2018-12-25 add :
# 1、状态日志文件用于监控
# 2、stage3加入online状态的监控
#2018-12-26 add
#1、去除mysql port端口检测

import fcntl
import socket
import time
import sys
from all_vip import *
from handler import *
from global_pars.Class_global_pars import *
from parameter import par_var

DEBUG = 1

def main():
    vip_wrok=all_vip()
    wrok = Wroker(vip_wrok)
    wrok.env_init(DEBUG,par_var) #初始化 参数已经进入 global全局参数
    logger = global_par.get_global_pars("logger")
    sleeptime = global_par.get_global_pars("sleeptime")
    wrok.check_par(par_var) #做参数检查,检查参数的合法性检查的是 par_var用户参数

    ##以下做文件锁避免多次调用启动
    try:
        hostname = socket.gethostname()
        fd = open("/root/HAIPMGR"+hostname+".lock","w+",encoding='utf-8') #文件锁文件

        fd_stat = open(global_par.get_global_pars("install_path")+"stat_" +str(global_par.get_global_pars("mysql_port")), "w+", encoding='utf-8') #监控文件
        fd_stat.seek(0, 0)
        fd_stat.write("1")
        fd_stat.flush()

        global_par.set_global_pars("fd_stat",fd_stat)

    except Exception as e:
        logger.error("fun:main: file {} create error .except:{}".format("/root/HAIPMGR"+hostname+".lock",e))
        print("fun:main: file {} create error .except:{}".format("/root/HAIPMGR"+hostname+".lock",e))
        sys.stdout.flush()
        exit(-1)



    try:
        fd.write(time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time())))
        fd.flush()
        #fd.write('\n'+str(par_var))
        fcntl.lockf(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except Exception as e:
        logger.error("fun:main: file lock on {} get error .except:{}".format("/root/HAIPMGR"+hostname+".lock",e))
        print("fun:main: file lock on {} get error other process lock it .except:{}".format("/root/HAIPMGR"+hostname+".lock",e))
        sys.stdout.flush()
        exit(-1)

    n = 0

    while 1: ##大循环检查
        if n ==  20: ##自动恢复 设定为20*sleeptime 秒 我们监控是1分钟报警可以报错出来
            fd_stat.seek(0, 0)
            if fd_stat.read(1).strip() != '1':
                fd_stat.seek(0, 0)
                fd_stat.write("1")
                fd_stat.flush()
                logger.warning("fun:main: stat file reset to '1' atfer 20*sleeptime")
            n = 0


        logger.info('\n'*4+'*'*35+"HAIPMGR:One loop begin:"+'*'*35)
        c_stat = wrok.check_stat()
        v_stat = wrok.check_vip(c_stat)
        wrok.oper_vip(v_stat)
        time.sleep(sleeptime)

        fd_stat.seek(0, 0)
        if fd_stat.read(1).strip() != '1':
            n += 1


    return


##程序开始
if __name__ == '__main__':
    main()