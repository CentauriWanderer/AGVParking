# 停车场管理模块
# 加入状态转换时刻

import pandas as pd
import copy
import heapq


class VEHICLE_TO_DEPART:

    def __init__(self, vid, depart_time):
        self.VehicleId = vid
        self.DepartTime = depart_time

    def __lt__(self, other):
        return self.DepartTime < other.DepartTime


# 停车场管理类
# 功能：
# ①储存到达表，并在对应的step生成进入（如有空）和离开事件，
# ②维护场内外车辆信息表，跟踪车辆信息
# ③维护停车车位表，进行停车位分配，生成搬运task

class PARKING_LOT_MANAGER:

    def __init__(self, cp, p, pt, vl, aq, sort, mct=-1):

        self.Sorting = sort
        self.ModeChangeTime = mct

        self.Capacity = cp
        self.TypeACapacity = len(p[0])
        self.TypeBCapacity = len(p[1])
        self.TypeCCapacity = len(p[2])
        self.TypeDCapacity = len(p[3])
        self.TypeECapacity = len(p[4])

        self.CapacityPlot = []
        self.TypeACapacityPlot = []
        self.TypeBCapacityPlot = []
        self.TypeCCapacityPlot = []
        self.TypeDCapacityPlot = []
        self.TypeECapacityPlot = []

        # 停车位管理表，内部动态信息
        tlist = ['x坐标', 'y坐标', '距离入口1', '距离入口2', '距离入口3', '距离出口1', '距离出口2', '距离出口3',
                 '是否占用', '占用车辆id']
        self.AllParkingTable = pd.DataFrame(pt, columns=tlist)
        self.ParkingTableA = pd.DataFrame(p[0], columns=tlist)
        self.ParkingTableB = pd.DataFrame(p[1], columns=tlist)
        self.ParkingTableC = pd.DataFrame(p[2], columns=tlist)
        self.ParkingTableD = pd.DataFrame(p[3], columns=tlist)
        self.ParkingTableE = pd.DataFrame(p[4], columns=tlist)

        # 车辆表，外部准静态信息
        tlist = ['类型', '分配类型', '到达时间', '离开时间', '入口', '出口', '实际出口', '是否进场', '停车位id']
        self.VehicleTable = pd.DataFrame(vl, columns=tlist)
        self.ArriveQueue = copy.deepcopy(aq)  # 这个列表会被修改

        self.ParkCount = 0
        self.TypeAParkCount = 0
        self.TypeBParkCount = 0
        self.TypeCParkCount = 0
        self.TypeDParkCount = 0
        self.TypeEParkCount = 0

        self.DepartQueue = []

        self.EnterCount = 0
        self.ReallocateCount = 0

        self.TypeAActivityCount = 0
        self.TypeBActivityCount = 0
        self.TypeCActivityCount = 0
        self.TypeDActivityCount = 0
        self.TypeEActivityCount = 0

    def getParkCoord(self, typ, num):

        if typ == 1:
            li = self.ParkingTableA
        elif typ == 2:
            li = self.ParkingTableB
        elif typ == 3:
            li = self.ParkingTableC
        elif typ == 4:
            li = self.ParkingTableD
        elif typ == 5:
            li = self.ParkingTableE
        elif typ == -1:
            li = self.AllParkingTable
        return li.loc[num, 'x坐标'], li.loc[num, 'y坐标']

    # 车辆进入时的分配，同时向离开队列填入
    def vehicleAllocate(self, vid, typ, ent, ext):

        self.EnterCount += 1

        # 分区溢出处理
        reallocate_flag = False

        if typ == 1:
            if self.TypeAParkCount < self.TypeACapacity:
                t = 1
            elif self.TypeBParkCount < self.TypeBCapacity:
                t = 2
                reallocate_flag = True
            elif self.TypeCParkCount < self.TypeCCapacity:
                t = 3
                reallocate_flag = True
            elif self.TypeDParkCount < self.TypeDCapacity:
                t = 4
                reallocate_flag = True
            elif self.TypeEParkCount < self.TypeECapacity:
                t = 5
                reallocate_flag = True
            else:
                raise

        elif typ == 2:
            if self.TypeBParkCount < self.TypeBCapacity:
                t = 2
            elif self.TypeCParkCount < self.TypeCCapacity:
                t = 3
                reallocate_flag = True
            elif self.TypeDParkCount < self.TypeDCapacity:
                t = 4
                reallocate_flag = True
            elif self.TypeEParkCount < self.TypeECapacity:
                t = 5
                reallocate_flag = True
            elif self.TypeAParkCount < self.TypeACapacity:
                t = 1
                reallocate_flag = True
            else:
                raise

        elif typ == 3:
            if self.TypeCParkCount < self.TypeCCapacity:
                t = 3
            elif self.TypeDParkCount < self.TypeDCapacity:
                t = 4
                reallocate_flag = True
            elif self.TypeEParkCount < self.TypeECapacity:
                t = 5
                reallocate_flag = True
            elif self.TypeBParkCount < self.TypeBCapacity:
                t = 2
                reallocate_flag = True
            elif self.TypeAParkCount < self.TypeACapacity:
                t = 1
                reallocate_flag = True
            else:
                raise

        elif typ == 4:
            if self.TypeDParkCount < self.TypeDCapacity:
                t = 4
            elif self.TypeEParkCount < self.TypeECapacity:
                t = 5
                reallocate_flag = True
            elif self.TypeCParkCount < self.TypeCCapacity:
                t = 3
                reallocate_flag = True
            elif self.TypeBParkCount < self.TypeBCapacity:
                t = 2
                reallocate_flag = True
            elif self.TypeAParkCount < self.TypeACapacity:
                t = 1
                reallocate_flag = True
            else:
                raise

        elif typ == 5:
            if self.TypeEParkCount < self.TypeECapacity:
                t = 5
            elif self.TypeDParkCount < self.TypeDCapacity:
                t = 4
                reallocate_flag = True
            elif self.TypeCParkCount < self.TypeCCapacity:
                t = 3
                reallocate_flag = True
            elif self.TypeBParkCount < self.TypeBCapacity:
                t = 2
                reallocate_flag = True
            elif self.TypeAParkCount < self.TypeACapacity:
                t = 1
                reallocate_flag = True
            else:
                raise

        else:
            raise

        if reallocate_flag:
            self.ReallocateCount += 1

        # 列选择
        if ent == 0:
            col = '距离入口1'
        elif ent == 1:
            col = '距离入口2'
        elif ent == 2:
            col = '距离入口3'

        if t == 1:
            parking_pos_list = self.ParkingTableA
            self.TypeAParkCount += 1
            self.TypeAActivityCount += 1
        elif t == 2:
            parking_pos_list = self.ParkingTableB
            self.TypeBParkCount += 1
            self.TypeBActivityCount += 1
        elif t == 3:
            parking_pos_list = self.ParkingTableC
            self.TypeCParkCount += 1
            self.TypeCActivityCount += 1
        elif t == 4:
            parking_pos_list = self.ParkingTableD
            self.TypeDParkCount += 1
            self.TypeDActivityCount += 1
        elif t == 5:
            parking_pos_list = self.ParkingTableE
            self.TypeEParkCount += 1
            self.TypeEActivityCount += 1

        # 找到距离最短的停车位
        pkid = parking_pos_list[parking_pos_list['是否占用'] == 0].sort_values(by=col).head(1).index.item()

        # 修改停车位表
        parking_pos_list.loc[pkid, '是否占用'] = 1
        parking_pos_list.loc[pkid, '占用车辆id'] = vid
        # 修改车辆表
        self.VehicleTable.loc[vid, '是否进场'] = 1
        self.VehicleTable.loc[vid, '停车位id'] = pkid
        self.VehicleTable.loc[vid, '分配类型'] = t

        # 离开队列
        # 创建类实例并且放入heapq
        vtd = VEHICLE_TO_DEPART(vid, self.VehicleTable.loc[vid, '离开时间'])
        heapq.heappush(self.DepartQueue, vtd)

        return pkid, t

    # 对比，无停车分区，处理总表
    # typ参数放弃
    def vehicleAllocate_(self, vid, typ, ent, ext):

        self.EnterCount += 1

        parking_pos_list = self.AllParkingTable

        # 列选择
        if ent == 0:
            col = '距离入口1'
        elif ent == 1:
            col = '距离入口2'
        elif ent == 2:
            col = '距离入口3'

        # 找到距离最短的停车位
        pkid = parking_pos_list[parking_pos_list['是否占用'] == 0].sort_values(by=col).head(1).index.item()

        # 修改停车位表
        parking_pos_list.loc[pkid, '是否占用'] = 1
        parking_pos_list.loc[pkid, '占用车辆id'] = vid
        # 修改车辆表
        self.VehicleTable.loc[vid, '是否进场'] = 1
        self.VehicleTable.loc[vid, '停车位id'] = pkid
        self.VehicleTable.loc[vid, '分配类型'] = -1

        # 离开队列
        # 创建类实例并且放入heapq
        vtd = VEHICLE_TO_DEPART(vid, self.VehicleTable.loc[vid, '离开时间'])
        heapq.heappush(self.DepartQueue, vtd)

        return pkid, -1

    # 车辆离开时的操作
    def deallocate(self, vid, typ, ent, ext):

        # 找到正确的停车位表
        if typ == 1:
            parking_pos_list = self.ParkingTableA
            self.TypeAParkCount -= 1
        elif typ == 2:
            parking_pos_list = self.ParkingTableB
            self.TypeBParkCount -= 1
        elif typ == 3:
            parking_pos_list = self.ParkingTableC
            self.TypeCParkCount -= 1
        elif typ == 4:
            parking_pos_list = self.ParkingTableD
            self.TypeDParkCount -= 1
        elif typ == 5:
            parking_pos_list = self.ParkingTableE
            self.TypeEParkCount -= 1

        pkid = self.VehicleTable.loc[vid, '停车位id']
        parking_pos_list.loc[pkid, '是否占用'] = 0
        parking_pos_list.loc[pkid, '占用车辆id'] = -1

        return pkid, self.VehicleTable.loc[vid, '分配类型']

    # 对比
    def deallocate_(self, vid, typ, ent, ext):

        parking_pos_list = self.AllParkingTable

        pkid = self.VehicleTable.loc[vid, '停车位id']
        parking_pos_list.loc[pkid, '是否占用'] = 0
        parking_pos_list.loc[pkid, '占用车辆id'] = -1

        return pkid, -1

    # 生成到达和离开事件
    def step(self, stp):

        arrivals = []

        while self.ArriveQueue and self.ArriveQueue[0][0] == stp:
            v = self.ArriveQueue.pop(0)  # 从到达队列中取元组(step,vid)
            if self.ParkCount < self.Capacity:
                self.ParkCount += 1
                vehicle_id = v[1]
                vehicle_type = self.VehicleTable.loc[vehicle_id, '类型']
                vehicle_entrance = self.VehicleTable.loc[vehicle_id, '入口']
                vehicle_exit = self.VehicleTable.loc[vehicle_id, '出口']
                if self.Sorting:
                    if self.ModeChangeTime != -1 and stp >= self.ModeChangeTime:
                        vehicle_type = 1
                    pkid, parking_type = self.vehicleAllocate(vehicle_id, vehicle_type, vehicle_entrance, vehicle_exit)
                else:
                    pkid, parking_type = self.vehicleAllocate_(vehicle_id, vehicle_type, vehicle_entrance, vehicle_exit)
                arrivals.append((vehicle_id, pkid, vehicle_entrance, parking_type))
            else:
                pass  # 抛弃超额到达

        departures = []

        while self.DepartQueue and self.DepartQueue[0].DepartTime == stp:
            v = heapq.heappop(self.DepartQueue)  # 从离开队列中取VEHICLE_TO_DEPART对象实例
            self.ParkCount -= 1
            vehicle_id = v.VehicleId
            vehicle_type = self.VehicleTable.loc[vehicle_id, '分配类型']
            vehicle_entrance = self.VehicleTable.loc[vehicle_id, '入口']
            vehicle_exit = self.VehicleTable.loc[vehicle_id, '出口']
            if self.Sorting:
                pkid, parking_type = self.deallocate(vehicle_id, vehicle_type, vehicle_entrance, vehicle_exit)
            else:
                pkid, parking_type = self.deallocate_(vehicle_id, vehicle_type, vehicle_entrance, vehicle_exit)
            departures.append((vehicle_id, pkid, vehicle_exit, parking_type))

        if not stp % 10:
            self.CapacityPlot.append(self.ParkCount)
            self.TypeACapacityPlot.append(self.TypeAParkCount)
            self.TypeBCapacityPlot.append(self.TypeBParkCount)
            self.TypeCCapacityPlot.append(self.TypeCParkCount)
            self.TypeDCapacityPlot.append(self.TypeDParkCount)
            self.TypeECapacityPlot.append(self.TypeEParkCount)

        return arrivals, departures

    def getData(self):

        parking_text_list = []

        if self.Sorting:
            for i in range(len(self.ParkingTableA)):
                parking_text_list.append(((self.ParkingTableA.iloc[i]['x坐标'], self.ParkingTableA.iloc[i]['y坐标']),
                                          'A' + str(i), str(self.ParkingTableA.iloc[i]['占用车辆id']), 0))
            for i in range(len(self.ParkingTableB)):
                parking_text_list.append(((self.ParkingTableB.iloc[i]['x坐标'], self.ParkingTableB.iloc[i]['y坐标']),
                                          'B' + str(i), str(self.ParkingTableB.iloc[i]['占用车辆id']), 1))
            for i in range(len(self.ParkingTableC)):
                parking_text_list.append(((self.ParkingTableC.iloc[i]['x坐标'], self.ParkingTableC.iloc[i]['y坐标']),
                                          'C' + str(i), str(self.ParkingTableC.iloc[i]['占用车辆id']), 2))
            for i in range(len(self.ParkingTableD)):
                parking_text_list.append(((self.ParkingTableD.iloc[i]['x坐标'], self.ParkingTableD.iloc[i]['y坐标']),
                                          'D' + str(i), str(self.ParkingTableD.iloc[i]['占用车辆id']), 3))
            for i in range(len(self.ParkingTableE)):
                parking_text_list.append(((self.ParkingTableE.iloc[i]['x坐标'], self.ParkingTableE.iloc[i]['y坐标']),
                                          'E' + str(i), str(self.ParkingTableE.iloc[i]['占用车辆id']), 4))

        else:
            for i in range(len(self.AllParkingTable)):
                parking_text_list.append(
                    ((self.AllParkingTable.iloc[i]['x坐标'], self.AllParkingTable.iloc[i]['y坐标']),
                     str(i), str(self.AllParkingTable.iloc[i]['占用车辆id']), 3))

        return parking_text_list

    def getPlot(self):
        return self.CapacityPlot, self.TypeACapacityPlot, self.TypeBCapacityPlot, self.TypeCCapacityPlot, self.TypeDCapacityPlot, self.TypeECapacityPlot

    def summary(self):
        return self.ReallocateCount / self.EnterCount, [self.TypeAActivityCount, self.TypeBActivityCount,
                                                        self.TypeCActivityCount, self.TypeDActivityCount,
                                                        self.TypeEActivityCount]
