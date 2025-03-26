# AGV管理模块

import numpy as np
from utils import *

class AGV_SUPERAGENT:

    def __init__(self, tm, plm, rp, rt, rl):

        self.Timer = tm
        self.ParkingLotManager = plm
        self.RoutePlanner = rp
        self.ReserveTable = rt
        self.ReverseLookup = rl

        self.Actions = ((1, 0), (-1, 0), (0, 1), (0, -1), (0, 0))

        self.AGVRouteHistory = []
        self.RouteConflictCount = 0
        self.RouteStopCount = 0
        # self.ArrTaskTimeHistory = []
        # self.DepTaskTimeHistory = []

    def initInfo(self, agv_init_pos_list, charge_station_list, entrance_list, exit_list):

        # map初始信息
        self.ChargeStationList = charge_station_list
        self.EntranceList = entrance_list
        self.ExitList = exit_list

        # agv起始信息
        self.NumAGV = len(agv_init_pos_list)

        self.AGVTable = np.array(agv_init_pos_list)
        self.AGVTable = np.concatenate((self.AGVTable, np.full((self.NumAGV, 1), 0)), axis=1)

        self.AvailAGVs = [i for i in range(self.NumAGV)]

        self.AGVArrTaskList = [-1 for i in range(self.NumAGV)]
        self.AGVDepTaskList = [-1 for i in range(self.NumAGV)]

        self.AGVOrderList = [[2] for i in range(self.NumAGV)]  # 命令列表

        self.AGVDestiList = [[(-1, -1)] for i in range(self.NumAGV)]  # 目的地列表
        self.AGVDestiDescribList = [[''] for i in range(self.NumAGV)]  # 目的地text列表

        self.AGVActionList = [[-1] for i in range(self.NumAGV)]  # 动作列表
        self.AGVActionList1 = [[-1] for i in range(self.NumAGV)]  # 防死锁副列表

        # 到达和离开任务明细列表
        self.VehArrTaskList = []  # index: vid, pkid, entrance id, park type, arr time,  designate time, end time
        self.VehDepTaskList = []  # index: vid, pkid, exit id,     park type, call time, designate time, end time
        # 等待完成的到达和离开任务
        self.WaitingArrTask = []
        self.WaitingDepTask = []

    # 接受PLM发出的到达和离开任务
    def inputVehTask(self, arrivals, departures):

        for t in arrivals:
            self.VehArrTaskList.append([t[0], t[1], t[2], t[3], self.Timer.time(), -1, -1])
            self.WaitingArrTask.append(len(self.VehArrTaskList) - 1)
        for t in departures:
            self.VehDepTaskList.append([t[0], t[1], t[2], t[3], self.Timer.time(), -1, -1])
            self.WaitingDepTask.append(len(self.VehDepTaskList) - 1)

    def getNearestAGVToTask(self, agvid_list, target):
        dist_list = []
        for agvid in agvid_list:
            agv_pos = (self.AGVTable[agvid, 0], self.AGVTable[agvid, 1])
            dist_list.append(getDist(agv_pos, target))
        min_dist = min(dist_list)
        return dist_list.index(min_dist)

    # 对agv分配任务，填充agv的命令列表，填充agv的目的地列表
    # 在主循环中独立运行一次，作为任务分配
    def genAGVOrderList(self):

        # 优先处理离开任务
        # 先到停车位，然后到出口
        while self.WaitingDepTask and self.AvailAGVs:
            vtid = self.WaitingDepTask.pop(0)  # 任务id
            # 从任务列表中获取...
            vid = self.VehDepTaskList[vtid][0]  # 车辆id
            pkid = self.VehDepTaskList[vtid][1]  # 停车位id
            exid = self.VehDepTaskList[vtid][2]  # 出口id
            park_type = self.VehDepTaskList[vtid][3]  # 停车类型
            self.VehDepTaskList[vtid][5] = self.Timer.time()  # 记录分配时间
            start_coord = self.ParkingLotManager.getParkCoord(park_type, pkid)  # 出发坐标是车辆停放位置
            end_coord = self.ExitList[exid]  # 目标坐标是出口之一
            aid = self.AvailAGVs.pop(self.getNearestAGVToTask(self.AvailAGVs,start_coord))  # agvid
            self.AGVDepTaskList[aid] = vtid
            charge_coord = self.ChargeStationList[aid]
            if (self.AGVTable[aid, 0], self.AGVTable[aid, 1]) == start_coord:  # 如果已经在出发点
                self.AGVOrderList[aid] = [3, 1.1, 6, 4, 1.2, 8, 2]  # 装，寻，出，卸，寻，返，停
                self.AGVDestiList[aid] = [end_coord, charge_coord]  # 出，充
                self.AGVDestiDescribList[aid] = ['出' + str(exid), '充' + str(aid)]
            else:
                self.AGVOrderList[aid] = [1, 7, 3, 1.1, 6, 4, 1.2, 8, 2]  # 寻，取，装，寻，出，卸，寻，返，停
                self.AGVDestiList[aid] = [start_coord, end_coord, charge_coord]  # 停，出，充
                if park_type == -1:
                    self.AGVDestiDescribList[aid] = ['P' + str(pkid), '出' + str(exid), '充' + str(aid)]
                elif park_type == 1:
                    self.AGVDestiDescribList[aid] = ['A' + str(pkid), '出' + str(exid), '充' + str(aid)]
                elif park_type == 2:
                    self.AGVDestiDescribList[aid] = ['B' + str(pkid), '出' + str(exid), '充' + str(aid)]
                elif park_type == 3:
                    self.AGVDestiDescribList[aid] = ['C' + str(pkid), '出' + str(exid), '充' + str(aid)]
                elif park_type == 4:
                    self.AGVDestiDescribList[aid] = ['D' + str(pkid), '出' + str(exid), '充' + str(aid)]
                elif park_type == 5:
                    self.AGVDestiDescribList[aid] = ['E' + str(pkid), '出' + str(exid), '充' + str(aid)]
            # print(self.AGVOrderList)
            # print(tm.time())

        # 然后是到达任务
        # 先到入口，然后到停车位
        while self.WaitingArrTask and self.AvailAGVs:
            vtid = self.WaitingArrTask.pop(0)  # 任务id
            # 从任务列表中获取...
            vid = self.VehArrTaskList[vtid][0]  # 车辆id
            pkid = self.VehArrTaskList[vtid][1]  # 停车位id
            entid = self.VehArrTaskList[vtid][2]  # 入口id
            park_type = self.VehArrTaskList[vtid][3]  # 停车类型
            self.VehArrTaskList[vtid][5] = self.Timer.time()  # 记录分配时间
            start_coord = self.EntranceList[entid]  # 出发坐标是入口之一
            end_coord = self.ParkingLotManager.getParkCoord(park_type, pkid)  # 目标坐标是车辆停放位置
            aid = self.AvailAGVs.pop(self.getNearestAGVToTask(self.AvailAGVs, start_coord))  # agvid
            self.AGVArrTaskList[aid] = vtid
            charge_coord = self.ChargeStationList[aid]
            if (self.AGVTable[aid, 0], self.AGVTable[aid, 1]) == start_coord:  # 如果已经在出发点
                self.AGVOrderList[aid] = [3, 1, 7, 4, 1, 8, 2]  # 装，寻，放，卸，寻，返，停
                self.AGVDestiList[aid] = [end_coord, charge_coord]  # 入，充
                if park_type == -1:
                    self.AGVDestiDescribList[aid] = ['P' + str(pkid), '充' + str(aid)]
                elif park_type == 1:
                    self.AGVDestiDescribList[aid] = ['A' + str(pkid), '充' + str(aid)]
                elif park_type == 2:
                    self.AGVDestiDescribList[aid] = ['B' + str(pkid), '充' + str(aid)]
                elif park_type == 3:
                    self.AGVDestiDescribList[aid] = ['C' + str(pkid), '充' + str(aid)]
                elif park_type == 4:
                    self.AGVDestiDescribList[aid] = ['D' + str(pkid), '充' + str(aid)]
                elif park_type == 5:
                    self.AGVDestiDescribList[aid] = ['E' + str(pkid), '充' + str(aid)]
            else:
                self.AGVOrderList[aid] = [1.1, 5, 3, 1.2, 7, 4, 1, 8, 2]  # 寻，入，装，寻，放，卸，寻，返，停
                self.AGVDestiList[aid] = [start_coord, end_coord, charge_coord]  # 入，停，充
                if park_type == -1:
                    self.AGVDestiDescribList[aid] = ['入' + str(entid), 'P' + str(pkid), '充' + str(aid)]
                elif park_type == 1:
                    self.AGVDestiDescribList[aid] = ['入' + str(entid), 'A' + str(pkid), '充' + str(aid)]
                elif park_type == 2:
                    self.AGVDestiDescribList[aid] = ['入' + str(entid), 'B' + str(pkid), '充' + str(aid)]
                elif park_type == 3:
                    self.AGVDestiDescribList[aid] = ['入' + str(entid), 'C' + str(pkid), '充' + str(aid)]
                elif park_type == 4:
                    self.AGVDestiDescribList[aid] = ['入' + str(entid), 'D' + str(pkid), '充' + str(aid)]
                elif park_type == 5:
                    self.AGVDestiDescribList[aid] = ['入' + str(entid), 'E' + str(pkid), '充' + str(aid)]
            # print(self.AGVOrderList)
            # print(tm.time())

    def checkAvail(self, agvid):
        if self.AGVOrderList[agvid][0] in (0, 2, 8):
            self.AvailAGVs.append(agvid)
            if self.AGVArrTaskList[agvid] != -1:
                tid = self.AGVArrTaskList[agvid]
                self.VehArrTaskList[tid][6] = self.Timer.time()
                self.AGVArrTaskList[agvid] = -1
            if self.AGVDepTaskList[agvid] != -1:
                tid = self.AGVDepTaskList[agvid]
                self.VehDepTaskList[tid][6] = self.Timer.time()
                self.AGVDepTaskList[agvid] = -1

    def step(self):

        # 遍历，agv寻路
        ###################################

        li0 = []
        li1 = []
        li2 = []
        for i in range(self.NumAGV):
            if self.AGVOrderList[i][0] == 1:
                li0.append(i)
            if self.AGVOrderList[i][0] == 1.1:
                li1.append(i)
            if self.AGVOrderList[i][0] == 1.2:
                li2.append(i)

        for agvid in li0:
            start = (self.AGVTable[agvid][0], self.AGVTable[agvid][1])  # 当前位置
            end = self.AGVDestiList[agvid][0]  # 第一个目标位置
            path, length, actions = self.RoutePlanner.plan(self.Timer.time(), start, end, agvid)  # 寻路
            order = self.AGVOrderList[agvid][1]
            if path:
                self.AGVRouteHistory.append((self.Timer.time(), agvid, order, length, path, start, end))
                self.ReserveTable.update(path, actions, self.Timer.time(), agvid)
                self.AGVDestiList[agvid].pop(0)
                self.AGVActionList[agvid] = actions[1:]
                self.AGVOrderList[agvid].pop(0)  # 退出寻路状态
                self.RouteStopCount += actions.count(4)
            else:
                self.RouteConflictCount += 1
                # rc.setPause()

        for agvid in li1:

            start1 = (self.AGVTable[agvid][0], self.AGVTable[agvid][1])  # 当前位置
            end1 = self.AGVDestiList[agvid][0]  # 第一个目标位置
            path1, length1, actions1 = self.RoutePlanner.plan(self.Timer.time(), start1, end1, agvid)  # 寻路
            order1 = self.AGVOrderList[agvid][1]

            if path1:
                start2 = end1
                end2 = self.AGVDestiList[agvid][1]
                path2, length2, actions2 = self.RoutePlanner.plan(self.Timer.time() + length1, start2, end2,
                                                                  agvid)  # 寻路
                order2 = self.AGVOrderList[agvid][4]
                if path2:
                    # rc.setPause()
                    # recorder.record(str(self.Timer.time())+','+str(agvid)+','+str(path))
                    # 双重记录
                    self.AGVRouteHistory.append((self.Timer.time(), agvid, order1, length1, path1, start1, end1))
                    self.AGVRouteHistory.append((self.Timer.time() + length1, agvid, order2, length2, path2, start2, end2))
                    # 双重存路
                    self.ReserveTable.update(path1, actions1, self.Timer.time(), agvid)
                    self.ReserveTable.update(path2, actions2, self.Timer.time() + length1, agvid)
                    self.AGVDestiList[agvid].pop(0)
                    # 双重存路
                    self.AGVActionList[agvid] = actions1[1:]
                    self.AGVActionList1[agvid] = actions2[1:]
                    self.AGVOrderList[agvid].pop(0)  # 退出寻路状态
                    self.RouteStopCount += actions1.count(4)
                    self.RouteStopCount += actions2.count(4)
                else:
                    self.RouteConflictCount += 1
                    # rc.setPause()
            else:
                self.RouteConflictCount += 1
                # rc.setPause()

        for agvid in li2:
            # self.AGVRouteHistory.append((self.Timer.time(),agvid,order,length,path))
            # self.ReserveTable.update(path,actions,self.Timer.time(),agvid)
            self.AGVDestiList[agvid].pop(0)
            self.AGVActionList[agvid] = self.AGVActionList1[agvid]
            self.AGVActionList1[agvid] = [-1]
            self.AGVOrderList[agvid].pop(0)  # 退出寻路状态

        # 遍历，执行动作和状态转换
        ###################################
        for i in range(self.NumAGV):  # 2
            if self.AGVOrderList[i][0] == 0:
                pass
            elif self.AGVOrderList[i][0] == 1 or self.AGVOrderList[i][0] == 1.1 or self.AGVOrderList[i][0] == 1.2:
                pass
            elif self.AGVOrderList[i][0] == 2:
                pass
            elif self.AGVOrderList[i][0] == 3:  # 含状态转换
                self.AGVOrderList[i].pop(0)
                self.AGVTable[i, 2] = 1
                self.checkAvail(i)
            elif self.AGVOrderList[i][0] == 4:  # 含状态转换
                self.AGVOrderList[i].pop(0)
                self.AGVTable[i, 2] = 0
                self.checkAvail(i)
            else:  # 5678运动状态
                act = self.AGVActionList[i].pop(0)  # 执行一个动作
                delta = self.Actions[act]  # 获取偏移量
                self.AGVTable[i, 0] = self.AGVTable[i, 0] + delta[0]  # 修改坐标
                self.AGVTable[i, 1] = self.AGVTable[i, 1] + delta[1]
                # 如果动作序列完成，则执行状态(任务)转换
                if not self.AGVActionList[i]:
                    self.AGVOrderList[i].pop(0)
                    self.AGVDestiDescribList[i].pop(0)
                    if not self.AGVDestiDescribList[i]:
                        self.AGVDestiDescribList[i] = ['']
                    self.checkAvail(i)

        self.ReserveTable.step()

    def getData(self):

        st = ['止', '寻', '充', '装', '卸', '入', '出', '位', '站']
        agv_text_list = []
        for i in range(self.NumAGV):  # 3
            state_index = self.AGVOrderList[i][0]
            if state_index == 1.1 or state_index == 1.2:
                state_index = 1
            state_text = st[state_index]
            agv_text_list.append(((self.AGVTable[i, 0],
                                   self.AGVTable[i, 1]),
                                  str(i) + state_text,
                                  self.AGVDestiDescribList[i][0],
                                  self.AGVTable[i, 2]
                                  ))
        return agv_text_list

    def summary(self):
        sum_route_length = 0
        sum_wait_time_arr = 0
        sum_wait_time_dep = 0
        li = [0,0,0,0,0]
        for i in range(len(self.AGVRouteHistory)):
            sum_route_length += self.AGVRouteHistory[i][3]
        for i in range(len(self.VehArrTaskList)):
            sum_wait_time_arr += self.VehArrTaskList[i][6] - self.VehArrTaskList[i][4]
        for i in range(len(self.VehDepTaskList)):
            sum_wait_time_dep += self.VehDepTaskList[i][6] - self.VehDepTaskList[i][4]
        for record in self.AGVRouteHistory:
            start = record[5]
            end = record[6]
            length = record[3]
            type1 = self.ReverseLookup.get(start, -1)
            type2 = self.ReverseLookup.get(end, -1)
            type = max(type1, type2)
            if type != -1:
                li[type] = li[type] + length

        return sum_route_length, sum_wait_time_arr, sum_wait_time_dep, self.RouteConflictCount, self.RouteStopCount, li
