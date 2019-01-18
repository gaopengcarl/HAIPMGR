PYTHON3适用

一、错误查看
如果对于出现异常先查看日志文件,日志文件在当前目录下HAIPMGR.log,如果出现vip的切换可以

cat HAIPMGR.log|grep -i warn

因为只有切换日志才作为了warning,其他大部分为INFO信息。


二、参数
使用只需要更改parameter.py下的参数字典就可以了，不能新加。
par_var = {"vip":"192.168.250.39","cluser_ip":{"192.168.250.33":"bond0","192.168.250.37":"bond0","192.168.250.38":"bond0"},\
            "ip_gateway":"192.168.250.254","mysql_port":"4790","inter_port":"14790","passwd":"KRj$r748Lf","user":"haip_user",\
           "platfrom":"linux","sleeptime":7,"install_path":"/opt/HAIPMGR/"}

"vip":需要启动的虚拟ip地址
"cluser_ip":这是一个字典，需要写好IP地址和网卡名字，绑定的虚拟IP会在这个网卡上
"ip_gateway":网关，需要填写正确的网关
"mysql_port":mysql的服务端口，绑定网卡的标志会用mysql的端口标示比如eth0:3316
"inter_port":MGR 内部通信端口
"passwd":mysql用户的密码
"user":mysql的用户，本用户必须要能够访问performance_schema下的表权限
"platfrom":填写"linux"即可，当前只能是"linux"
"sleeptime":循环检测的秒
"install_path":安装路径日志文件和状态文件将会生成在下面,必须以'/'结尾


上面参数必须认真填写，填写错误将不能正常运行。

三、生成的文件


/root/HAIPMGR[hostname].lock：文件锁，不要手动更改本文件
"install_path"/HAIPMGR_[mysql_port].log：日志文件
"install_path"/stat_[mysql_port]：状态文件用于监控是否发生了VIP切换 ，会设置为 0为关闭 2为启动，将会在20*sleeptime后重置为1
不要手动更改本文件


四、运行和关闭


本程序使用python3.6 需要用到模块psutil、pymysql

解压后修改参数文件

启动
nohup python3 HAIPMGR.py &

关闭程序直接kill即可没有影响
关闭的话不会影响虚拟ip,启动也不会影响现有的虚拟ip


五、限制
本脚本程序只能用于LINUX下MGR单主的情况且
本脚本程序只支持每个MGR实例分布在单台服务器上，且数据库端口和paxos 内部通信端口一致
的MGR上，线上一般都是这种情况。


六、安装
配置parameter.py文件参数
mkdir -p /opt/HAIPMGR/
解压
nohup python3 HAIPMGR.py & 运行即可


七、判断逻辑

因为单主模式MGR可以保证数据的一致性因此判断逻辑如下:

阶段1[stage1]:
通过初始化参数cluser_ip中的配置判断本节点是否在集群中
阶段2[stage2]:
检查是否能够连接上MYSQLD服务器进程，主要检查mysqld(已经取消端口检测)可以连接(密码错误算可以连接)
阶段3[stage3]
判断内部通信端口是否启动，检查本机是否在MGR中且为online，检查本节点是否是MGR的主节点
阶段4[stage4]
通过检查网关的方式,来避免网络隔离出现2个主节点启动两个VIP的情况

上面4个阶段将会返回
0  状态检查成功需要开启VIP
1  状态检查失败需要关闭VIP

阶段5[stage5]
根据上面4个阶段的返回值来判断是否启动和关闭VIP又有如下判断

如果需要启动
    虚拟VIP是否在本地
        如果在本地
            则维持现状return 1
        如果不在本地
            如果还能ping通VIP则本次循环维持现状,等待下次循环检测 return 1
            如果不能ping通VIP则做2次检查将阶段1到4再次检查一遍
                如果检查失败 return1 维持现状
                如果检查成功 return2 启动VIP
如果需要关闭
    虚拟VIP是否在本地关闭
        如果在本地
            做二次检查阶段1到4再次检查一遍
                如果检查失败 return1 维持现状
                如果检查成功 return0 关闭VIP
        如果不在本地
            维持现状 return0

本阶段返回
0 关闭VIP
1 维持现状不启动也不关闭vip
2 启动VIP

阶段6[stage6]

根据阶段5的返回做相应的处理即可。

八、公司监控MGR

监控MGR成员通过SQL语句
select count(*) from replication_group_members where  MEMBER_STATE='ONLINE'
如果不等于3报警

监控VIP切换通过查看
stat_[mysql_port]
文件监控值不等于1报警 ，监控周期为1分钟，脚本会在20*sleeptime后重置为1。

监控VIP进程
监控MYSQLD进程


九、相关测试
1、关闭服务器
insert into gptest(name) values('gaopeng57');
insert into gptest(name) values('gaopeng58');
insert into gptest(name) values('gaopeng59');
test1:(2003, "Can't connect to MySQL server on '192.168.99.189' (timed out)")
test1:(2003, "Can't connect to MySQL server on '192.168.99.189' (timed out)")
insert into gptest(name) values('gaopeng60');
insert into gptest(name) values('gaopeng61');
insert into gptest(name) values('gaopeng62');
insert into gptest(name) values('gaopeng63');

2、关闭数据库

insert into gptest(name) values('gaopeng23');
insert into gptest(name) values('gaopeng24');
insert into gptest(name) values('gaopeng25');
test1:(2003, "Can't connect to MySQL server on '192.168.99.189' ([WinError 10061] 由于目标计算机积极拒绝，无法连接。)")
....
test1:(2003, "Can't connect to MySQL server on '192.168.99.189' ([WinError 10061] 由于目标计算机积极拒绝，无法连接。)")
test1:(2003, "Can't connect to MySQL server on '192.168.99.189' (timed out)")
test1:(2003, "Can't connect to MySQL server on '192.168.99.189' (timed out)")
insert into gptest(name) values('gaopeng26');
insert into gptest(name) values('gaopeng27');
insert into gptest(name) values('gaopeng28');
insert into gptest(name) values('gaopeng29');


3、关闭MGR

insert into gptest(name) values('gaopeng29');
insert into gptest(name) values('gaopeng30');
insert into gptest(name) values('gaopeng31');
test1:(3100, "Error on observer while running replication hook 'before_commit'.")
insert into gptest(name) values('gaopeng31');
test1:(1290, 'The MySQL server is running with the --super-read-only option so it cannot execute this statement')
.....
insert into gptest(name) values('gaopeng31');
test1:(1290, 'The MySQL server is running with the --super-read-only option so it cannot execute this statement')
insert into gptest(name) values('gaopeng31');
test1:(1290, 'The MySQL server is running with the --super-read-only option so it cannot execute this statement')
test1:(2013, 'Lost connection to MySQL server during query ([WinError 10060] 由于连接方在一段时间后没有正确答复或连接的主机没有反应，连接尝试失败。)')
insert into gptest(name) values('gaopeng31');
insert into gptest(name) values('gaopeng32');
insert into gptest(name) values('gaopeng33');
