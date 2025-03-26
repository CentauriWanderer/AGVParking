# 寻路模块

from utils import *
import numpy as np
import heapq


class SPACE_TIME_NODE:

    def __init__(self, x, y, t, g, h, la):
        self.X = x  # x坐标
        self.Y = y  # y坐标
        self.T = t  # time坐标
        self.G = g  # 现有成本
        self.H = h  # 估计成本
        self.F = g + h  # f值
        self.Valid = True  # 有效性
        self.LastAction = la  # 到达该位置的动作
        self.CameFrom = -1  # 上一个位置

    def __lt__(self, other):
        if self.F < other.F:
            return True
        elif self.F == other.F:
            return self.H < other.H  # 靠近终点的stn优先，这样能降低迭代次数
        else:
            return False


class RESERVE_TABLE:
    def __init__(self, init_time_steps, mp):

        self.XLength = mp.XLength
        self.YLength = mp.YLength

        self.SpaceReserveTable = np.full((init_time_steps, self.XLength, self.YLength), -1, dtype='int8')
        self.TransArrayH = np.full((init_time_steps, self.XLength - 1, self.YLength), -1, dtype='int8')
        self.TransArrayV = np.full((init_time_steps, self.XLength, self.YLength - 1), -1, dtype='int8')
        self.TransArrayHExpandUnit = np.full((self.XLength - 1, self.YLength), -1).tolist()
        self.TransArrayVExpandUnit = np.full((self.XLength, self.YLength - 1), -1).tolist()
        self.SpanTill = init_time_steps - 1  # 当前expand到的step
        self.CurrentTime = 0

        self.TempSRT = None
        self.TempTAH = None
        self.TempTAV = None

    def initPos(self, li):
        for vid in range(len(li)):
            self.SpaceReserveTable[:, li[vid][0], li[vid][1]] = vid

    def expandArray(self, length):
        r1 = np.append(self.SpaceReserveTable, [self.SpaceReserveTable[-1].tolist() for i in range(length)], axis=0)
        r2 = np.append(self.TransArrayH, [self.TransArrayHExpandUnit for i in range(length)], axis=0)
        r3 = np.append(self.TransArrayV, [self.TransArrayVExpandUnit for i in range(length)], axis=0)
        return r1, r2, r3

    # 这里输入的path序列和action序列应包括时间起点的位置和last动作，即起点坐标和-1
    def update(self, path, actions, start_time, vid):

        length = len(actions) - 1  # 路径长度定义为动作序列长度
        expand = (start_time - self.CurrentTime + length) - (self.SpanTill - self.CurrentTime)

        if expand > 0:
            self.SpaceReserveTable = np.pad(self.SpaceReserveTable, ((0, expand), (0, 0), (0, 0)), mode='edge')
            # self.SpaceReserveTable = np.pad(self.SpaceReserveTable, ((0,expand),(0,0),(0,0)), mode='constant', constant_values=-1)
            self.TransArrayH = np.pad(self.TransArrayH, ((0, expand), (0, 0), (0, 0)), mode='constant',
                                      constant_values=-1)
            self.TransArrayV = np.pad(self.TransArrayV, ((0, expand), (0, 0), (0, 0)), mode='constant',
                                      constant_values=-1)
            # self.SpaceReserveTable,self.TransArrayH,self.TransArrayV = self.expandArray(expand)
            self.SpanTill = start_time + length

        # 抹除agv本身在table中扩展出的静止位置占用
        # 并且注册agv位置
        pointer = 0
        for i in range(start_time - self.CurrentTime, start_time - self.CurrentTime + length + 1):  # +1是range函数本身特性
            self.SpaceReserveTable[i][
                self.SpaceReserveTable[i] == vid] = -1  # 对于agv本身，需要抹除默认静止位置，改到输入的路径位置。该循环执行length+1次，即时间起点也被抹除
            self.SpaceReserveTable[i, path[pointer][0], path[pointer][1]] = vid
            pointer += 1
        # 拖尾处理
        # 即使路径长度没有达到目前rt延伸到的位置，也需要延长结尾位置至占满spacert，以便step函数的延拓
        for i in range(start_time - self.CurrentTime + length, self.SpanTill - self.CurrentTime + 1):
            self.SpaceReserveTable[i][self.SpaceReserveTable[i] == vid] = -1  # 同样需要抹除
            self.SpaceReserveTable[i, path[length][0], path[length][1]] = vid

        # 注册agv动作
        pointer = 1
        for i in range(start_time - self.CurrentTime + 1, start_time - self.CurrentTime + length + 1):
            action = actions[pointer]
            coord = path[pointer - 1]
            # 直接注册动作就行了，不需要抹除
            if action == 0:
                self.TransArrayH[(i, coord[0], coord[1])] = vid
            elif action == 1:
                self.TransArrayH[(i, coord[0] - 1, coord[1])] = vid
            elif action == 2:
                self.TransArrayV[(i, coord[0], coord[1])] = vid
            elif action == 3:
                self.TransArrayV[(i, coord[0], coord[1] - 1)] = vid
            pointer += 1

    def step(self):
        self.CurrentTime += 1
        self.SpanTill += 1
        self.SpaceReserveTable = self.SpaceReserveTable[1:, :, :]
        self.TransArrayH = self.TransArrayH[1:, :, :]
        self.TransArrayV = self.TransArrayV[1:, :, :]

        self.SpaceReserveTable = np.pad(self.SpaceReserveTable, ((0, 1), (0, 0), (0, 0)), mode='edge')
        # self.SpaceReserveTable = np.pad(self.SpaceReserveTable, ((0,1),(0,0),(0,0)), mode='constant', constant_values=-1)
        self.TransArrayH = np.pad(self.TransArrayH, ((0, 1), (0, 0), (0, 0)), mode='constant', constant_values=-1)
        self.TransArrayV = np.pad(self.TransArrayV, ((0, 1), (0, 0), (0, 0)), mode='constant', constant_values=-1)
        # self.SpaceReserveTable,self.TransArrayH,self.TransArrayV = self.expandArray(1)

    # 这里输入的length应当包含时间起点，即length=1时仅返回单个step的切片
    def clip(self, start_time, length, vid):

        expand = (start_time - self.CurrentTime + length) - (self.SpanTill - self.CurrentTime)

        if expand > 0:
            temp1 = np.pad(self.SpaceReserveTable, ((0, expand), (0, 0), (0, 0)), mode='edge')
            # temp1 = np.pad(self.SpaceReserveTable, ((0,expand),(0,0),(0,0)), mode='constant', constant_values=-1)
            temp2 = np.pad(self.TransArrayH, ((0, expand), (0, 0), (0, 0)), mode='constant', constant_values=-1)
            temp3 = np.pad(self.TransArrayV, ((0, expand), (0, 0), (0, 0)), mode='constant', constant_values=-1)

            # temp1, temp2, temp3= self.expandArray(expand)

        temp1 = temp1[(start_time - self.CurrentTime):(start_time - self.CurrentTime + length), :, :]
        temp2 = temp2[(start_time - self.CurrentTime):(start_time - self.CurrentTime + length), :, :]
        temp3 = temp3[(start_time - self.CurrentTime):(start_time - self.CurrentTime + length), :, :]

        # 保险起见，抹除agv本身的位置占用，方便重新规划路径？或者回到原点，虽然可能性微
        if vid != -1:
            for i in range(temp1.shape[0]):
                temp1[i][temp1[i] == vid] = -1

        # 注意！！！！！
        # clip之后的临时占用表时间base从0（寻路起点）开始
        self.TempSRT = temp1
        self.TempTAH = temp2
        self.TempTAV = temp3

        # return self.TempSRT, self.TempTAH, self.TempTAV

    def verifyPos(self, time, coord):
        return self.TempSRT[time, coord[0], coord[1]]

    def verifyAction(self, time, coord, action):
        if action == 0:
            return self.TempTAH[(time, coord[0], coord[1])]
        elif action == 1:
            return self.TempTAH[(time, coord[0] - 1, coord[1])]
        elif action == 2:
            return self.TempTAV[(time, coord[0], coord[1])]
        elif action == 3:
            return self.TempTAV[(time, coord[0], coord[1] - 1)]
        elif action == 4:
            return -1

    def clear(self):
        self.TempSRT, self.TempTAH, self.TempTAV = None, None, None


class ROUTE_PLANNER:
    def __init__(self, mp, reserve_table):
        self.MaxIter = 500
        self.Actions = ((1, 0), (-1, 0), (0, 1), (0, -1), (0, 0))
        self.MaxTimeStep = 100
        self.Map = mp
        self.ReserveTable = reserve_table

    # 注意这里的时间base为0
    def plan(self, start_time, start, end, vid):

        self.ReserveTable.clip(start_time, self.MaxTimeStep, vid)

        sx = start[0]
        sy = start[1]
        tx = end[0]
        ty = end[1]

        # 开放的stn堆和array

        # 矩阵是为了迅速从"空间关系"(动作和下一个位置)取到stn
        # 临时构造寻路空间
        # 占用表已经在init函数中构造了，尺寸相同
        map_size = self.Map.size()
        os_array = np.empty((self.MaxTimeStep, map_size[0], map_size[1]), dtype=SPACE_TIME_NODE)

        # heap堆是为了迅速从"数值关系"取到stn
        os_heap = []
        heapq.heapify(os_heap)

        # 起始位置stn
        stn = SPACE_TIME_NODE(sx, sy, 0, 0, getDist(start, end), -1)

        # 起始位置放入矩阵
        os_array[0, sx, sy] = stn
        # 起始位置放入heap
        heapq.heappush(os_heap, stn)

        it = 0

        # 如果stn堆不为空而且未曾到达最大探索步数
        while os_heap and it < self.MaxIter:

            it = it + 1

            # 从堆中取出下一个，直到取到有效stn
            # 因为成本更新，堆中会出现无效stn
            current = heapq.heappop(os_heap)
            if not current.Valid:
                continue

            # 如果到达目的地
            if current.X == tx and current.Y == ty:
                break

            # 取出stn的时空坐标值
            x = current.X
            y = current.Y
            t = current.T
            # print((x,y,t))

            for i in range(5):
                # print(i)
                # 计算next坐标
                nx = x + self.Actions[i][0]
                ny = y + self.Actions[i][1]
                nt = t + 1

                if nt == self.MaxTimeStep:
                    continue

                if not self.Map.verifyPos((nx, ny)) and not (nx, ny) == end:  # 既在禁行区又不是终点
                    # print('g')
                    continue

                if self.ReserveTable.verifyPos(nt, (nx, ny)) != -1:
                    # print('p')
                    # rc.setPause()
                    continue

                if self.ReserveTable.verifyAction(nt, (x, y), i) != -1:
                    # print('a')
                    # rc.setPause()
                    continue

                if i == current.LastAction:
                    new_cost = current.G + 1
                else:
                    new_cost = current.G + 1.1
                """
                if act == LaneMap[x,y] or LaneMap[x,y] == 0:
                    new_cost = current.G+1
                else:
                    new_cost = current.G+1.5
                """

                # 如果空，向新的时空位置建立stn
                if not os_array[nt, nx, ny]:
                    # 新建
                    stn = SPACE_TIME_NODE(nx, ny, nt, new_cost, getDist((nx, ny), end), i)
                    # 放入时空array
                    os_array[nt, nx, ny] = stn
                    # 放入堆
                    heapq.heappush(os_heap, stn)
                    # 记录路径关系
                    # came_from[stn] = current
                    stn.CameFrom = current
                # 如果非空，在成本变小的情况下替换stn
                elif os_array[nt, nx, ny].G > new_cost:
                    # 原有的stn直接标记为无效，因为从堆中修改element很麻烦
                    os_array[nt, nx, ny].Valid = False
                    # 新建stn
                    stn = SPACE_TIME_NODE(nx, ny, nt, new_cost, getDist((nx, ny), end), i)
                    # 放入时空array，直接覆盖
                    os_array[nt, nx, ny] = stn
                    # 放入堆
                    heapq.heappush(os_heap, stn)
                    # 记录路径关系
                    # came_from[stn] = current
                    stn.CameFrom = current
                # 如果成本大于或者等于，则什么都不做
                else:
                    pass

        if current.X == tx and current.Y == ty:
            return self.reconstruct_path(current)
        else:
            return None, None, None

    def reconstruct_path(self, current):
        total_path = [(current.X, current.Y)]
        action_history = [current.LastAction]
        while current.CameFrom != -1:
            current = current.CameFrom
            total_path.append((current.X, current.Y))
            action_history.append(current.LastAction)
        total_path = list(reversed(total_path))  # [1:]
        action_history = list(reversed(action_history))  # [1:]
        return total_path, len(total_path), action_history
