import multiprocessing
import socket
import time
from tqdm import tqdm

from utils import *
# from map_class import *
from map_class_2 import *
from traffic_loader import *
from route_planner import *
from genetic_algorithm import *
# from parking_lot_manager import *
from parking_lot_manager_3 import *
from agv_super_agent import *
from data_collector import *


# 日志模块

class LOG:

    def __init__(self, on=False, length=-1):
        self.On = on
        if self.On:
            self.Record = []
            self.Length = length

    def record(self, info):
        if self.On:
            self.Record.append(info)
            if self.Length != -1 and len(self.Record) > self.Length:
                self.Record.pop(0)

    def history(self, last=-1):
        if self.On:
            if last == -1:
                return self.Record
            else:
                return self.Record[-last:]
        else:
            return None

    def clear(self):
        if self.On:
            self.Record.clear()

    def save(self):
        if self.On:
            pass


# 发送端模块

class TCP_SENDER:

    def __init__(self, on=False, sleep_time=0.005):
        self.On = on
        if self.On:
            self.SleepTime = sleep_time
            self.Sender = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    def register(self, mp, agvs, plm, tm):
        if self.On:
            self.Map = mp
            self.AgvSuperAgent = agvs
            self.ParkingLotManager = plm
            self.Timer = tm

    def step(self):
        if self.On:
            # clear_output(wait=True)
            # print(printTime(self.Timer.time()))

            en, ex, cs, ob, l, lu, ld, ll, lr = self.Map.getData()
            p = self.ParkingLotManager.getData()
            a = self.AgvSuperAgent.getData()
            t = self.Timer.printTime()
            data = (en, ex, cs, ob, l, lu, ld, ll, lr, p, a, t)

            self.Sender.sendto(pickle.dumps(data), ('127.0.0.1', 8081))

            time.sleep(self.SleepTime)

    def close(self):
        if self.On:
            self.Sender.close()
        self.On = False


# 控制器模块
# 0-运行，1-暂停，2-步进运行，3-步进暂停

class RUN_CONTROLLER:
    def __init__(self, on=False, path="pause.txt"):
        self.On = on
        if self.On:
            self.Path = path
            with open(self.Path, "w") as f:
                f.write("0")

    def pausePoint(self):
        if self.On:
            # 一暂停部分
            with open(self.Path, "r") as f:
                pause = f.read()
            while pause == "1":
                time.sleep(1)
                with open(self.Path, "r") as f:
                    pause = f.read()
            # 一暂停部分结束
            # 二步进自锁部分
            if pause == "2":
                ##################
                """
                with open('analysis.bin','wb') as f:
                    pickle.dump((rt.SpaceReserveTable,rt.TransArrayH,rt.TransArrayV,agvs.AGVRouteHistory),f)
                """
                ##################
                with open(self.Path, "w") as f:
                    f.write("3")  # 自锁，需要monitor解锁
                with open(self.Path, "r") as f:
                    pause = f.read()
                while pause == "3":
                    time.sleep(1)
                    with open(self.Path, "r") as f:
                        pause = f.read()
            # 二步进自锁部分结束

    def setPause(self):
        if self.On:
            with open(self.Path, "w") as f:
                f.write("2")


# 计时器模块

class TIMER:
    def __init__(self):
        self.Step = 0

    def step(self):
        self.Step += 1

    def time(self):
        return self.Step

    def printTime(self):
        seconds = self.Step * 5
        num_h = seconds // 3600
        num_m = (seconds - num_h * 3600) // 60
        num_s = seconds - num_h * 3600 - num_m * 60
        return "{:02d}:{:02d}:{:02d}".format(num_h, num_m, num_s)


# 蒙特卡洛仿真主函数
# 自定义实验次数

def monteCarloSim(gen_idx, indv_idx, NumExp, MaxStep, mp, ai, cs, en, ex, cp, p, pt, rl, vlaq, sd, rc, sort):
    infos = []
    stats = []
    stats1 = []

    for exp_idx in range(NumExp):

        # 初始化实验资源
        tm = TIMER()  # 计时器
        rt = RESERVE_TABLE(10, mp)  # 占位表
        rt.initPos(ai) #
        rp = ROUTE_PLANNER(mp, rt)  # 寻路器
        # plm = PARKING_LOT_MANAGER(cp, p, pt, vlaq[exp_idx][0], vlaq[exp_idx][1], sort) # 停车场管理类
        plm = PARKING_LOT_MANAGER(cp, p, pt, vlaq[exp_idx][0], vlaq[exp_idx][1], sort, mct=9999999)  # 停车场管理类
        agvs = AGV_SUPERAGENT(tm, plm, rp, rt, rl)  # agv超级类
        agvs.initInfo(ai, cs, en, ex)  # 读入地图列表信息

        # recorder = LOG()  # 记录

        sd.register(mp, agvs, plm, tm)
        sd.step()

        for stp in range(MaxStep + 1):  # for step in MaxStep
            arr, dep = plm.step(tm.time())
            agvs.inputVehTask(arr, dep)

            agvs.genAGVOrderList()
            agvs.step()  # (for agv)
            # rt.step()
            tm.step()
            sd.step()
            rc.pausePoint()

        d1, d2, d3, d4, d6, d7 = agvs.summary()  # 总路程，到达等待时间，离开等待时间，路径冲突计数，路径停止计数，分类路径长度
        d5, d8 = plm.summary()  # 重分配率，分类活动计数
        infos.append((gen_idx, exp_idx, indv_idx))
        stats.append((d1, d2, d3, d4, d5, d6))
        stats1.append(d7 + d8)

    return infos, stats, stats1, plm.getPlot()


# 主程序

if __name__ == "__main__":

    # 是否渲染，是否向monitor传输数据并且接受运行控制
    render = False
    # 基因算法代数
    NumGen = 48
    # 蒙特卡洛实验数
    NumExp = 48
    # 基因算法种群大小
    NumIndv = 24
    # 是否分类
    sort = True
    # 交通文件路径
    traf_path = 'traffics/traffic012.bin'
    # 地图路径
    map_path = "maps/map016.xlsx"

    MaxStep = int(24 * 60 * (60 / 5))

    save_pop_every = 6
    SavedPop = []

    # 初始化仿真平台
    mp = MAP_CLASS(path=map_path)  # 地图
    traf = TRAFFIC_LOADER(num_exp=NumExp, path=traf_path, ignore_numexp=render)  # 交通
    ai, cs = mp.getAGVInfo()
    en, ex = mp.getEEInfo()
    sl, st = mp.getStripeInfo()
    dim = mp.getDimension()
    sender = TCP_SENDER(on=render)  # 发送端
    run_controller = RUN_CONTROLLER(on=render)  # 运行控制
    dc = DATA_COLLECTOR()  # 数据收集
    dc.addDescription(
        'sum agv route len,sum arrival waiting time,sum departure waiting time,route conflict count,parking reallocate rate,route stop count')
    dc1 = DATA_COLLECTOR()  # 代际数据收集
    dc1.addDescription('fitness for every individual in each gen')
    dc2 = DATA_COLLECTOR()  # 分类数据收集
    dc2.addDescription('total route length for each class and access count')

    # 进度条
    pbar = tqdm(total=NumGen, desc='进度', ncols=80, leave=True)

    # 基因算法框架
    GA = GENETIC_ALGORITHM(NumIndv, sl, st, dim)  # 基因算法
    GA.initPop()
    init_pop = GA.getPopulation()

    # for世代
    for gen_idx in range(NumGen):
        popl = GA.getPopulation()

        if save_pop_every and not (gen_idx + 1) % save_pop_every:
            SavedPop.append(popl)

        # fitness计算过程开始，跳出基因算法
        ###############################

        # 设置进程启动参数
        vlaq = traf.getVehicleList()
        processParams = []
        for indv_idx in range(NumIndv):
            #with open('best060.bin', 'rb') as f:
                #indv = pickle.load(f)
            indv = popl[indv_idx]
            cp, p, pt, rl = mp.genParkingPosListFromChromos(indv)  # 静态资源
            processParams.append((gen_idx, indv_idx, NumExp, MaxStep, mp, ai, cs, en, ex, cp, p, pt, rl, vlaq,
                                  sender, run_controller, sort))

        # 进程池运行
        with multiprocessing.Pool(processes=24) as pool:
            results = pool.starmap(monteCarloSim, processParams)

        # 进程池运行结束，读取结果
        for re in results:
            infos = re[0]
            stats = re[1]
            dc.gameBatch(infos, stats)
            stats1 = re[2]
            dc2.gameBatch(infos, stats1)

        capplot = re[3]

        pbar.update(1)

        # 数据处理
        # 注意有四处同步要改

        arll = []  # agv路径长度
        #awtl = []  # 到达等待时间
        #dwtl = []  # 离开等待时间
        #rcl = []  # 路径冲突计数
        #rrl = []  # 重分配率
        #rscl = []  # 路径停止计数
        #rif = [] # 路径干涉指标

        for i in range(NumIndv):
            pass
            # 滤出 当前世代，全部实验，给定个体i 的统计数据
            arll.append(np.mean(dc.filterData((gen_idx, -1, i), (0,))))  # 路径总长度
            #awtl.append(np.mean(dc.filterData((gen_idx, -1, i), (1,))))  # 到达等待时间
            #dwtl.append(np.mean(dc.filterData((gen_idx, -1, i), (2,))))  # 离开等待时间
            #rcl.append(np.mean(dc.filterData((gen_idx, -1, i), (3,))))  # 路径冲突计数
            #rrl.append(np.mean(dc.filterData((gen_idx, -1, i), (4,))))  # 重新分配率
            #rscl.append(np.mean(dc.filterData((gen_idx, -1, i), (5,))))  # 路径停止计数
            #rif.append(np.mean(dc.filterData((gen_idx, -1, i), (4,)))+np.mean(dc.filterData((gen_idx, -1, i), (5,))))

        # 下面的操作会破坏原始数据，仅用于健康度计算

        #arll = inverse(arll)
        #arll = inverse(level(arll))
        arll = inverse(arll)
        #awtl = inverse(awtl)
        #dwtl = inverse(dwtl)
        #rcl = inverse(rcl)
        #rrl = oneMinus(rrl)
        #rscl = inverse(rscl)
        #rif = inverse(rif)

        fitness = []
        for i in range(NumIndv):
            pass
            fitness.append(arll[i])
            # fitness.append(awtl[i])
            # fitness.append(dwtl[i])
            # fitness.append(rcl[i])
            # fitness.append(rrl[i])
            #fitness.append(rscl[i])
            #fitness.append(rif[i])

        # print(fitness)

        dc1.newGame((gen_idx,))
        dc1.endGame(fitness)
        end_popl = GA.getPopulation() # 最后一次种群不经变异直接保存

        if NumIndv == 1:
            break  # 单个体试运行无有效基因算法操作

        # 回到基因算法
        ###############################
        GA.setFitness(fitness)
        GA.genMatingPool()
        GA.poolCrossover()
        GA.poolMutate()
        GA.replace()

    info_dict = {'init population': init_pop, 'end population': end_popl, 'pattern': mp.PartitionPattern,
                 'data collector 0': dc, 'data collector 1': dc1, 'genetic algorithm ': GA,
                 'number of generations': NumGen, 'number of experiments': NumExp, 'number of individuals': NumIndv,
                 'traffic filename': traf.Path, 'map filename': mp.Path, 'population history': SavedPop,
                 'data collector 2': dc2}

    with open('result.bin', 'wb') as f:
        pickle.dump(info_dict, f)

    with open('capacity_plot.bin', 'wb') as f:
        pickle.dump(capplot, f)

    sender.close()
