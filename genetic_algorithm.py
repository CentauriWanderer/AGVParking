# 基因算法模块

import copy
import random
import math
import numpy as np


class GENETIC_ALGORITHM:

    def __init__(self, pop_size, stripe_length, stripe_type, dim):

        # on population
        # 种群大小
        self.PopulationSize = pop_size
        # 种群下标序列
        self.PopSoluIndexRange = [i for i in range(self.PopulationSize)]
        # 种群健康度
        self.Fitness = [-1 for i in self.PopSoluIndexRange]
        # 交配池
        self.MatingPool = []
        self.MatingPoolSize = self.PopulationSize - 2  # 配合保留二精英
        self.TournamentSize = 4
        self.TournamentProb = 0.7

        # on solution
        # 条带数量
        self.NumStripes = len(stripe_length)
        # 条带下标序列
        self.SoluStripeIndexRange = [i for i in range(self.NumStripes)]
        # 条带长度列表
        self.StripeLenList = stripe_length

        # 条带类型
        self.StripeType = stripe_type

        # on stripe
        # 维度数量
        self.Dimension = dim  # 注意结构化条带长度必须与维度相同！
        # 维度下标序列
        self.DimensIndexRange = [i for i in range(self.Dimension)]
        # 结构化条带是否随机初始化
        self.RandomInit = True

        # on GA mutate
        # 变异算子条带抽样概率
        self.StripeChoiceProb = 0.2
        # 变异算子是否至少抽一个条带变异（结构化/非结构化）
        self.AtLeastOneStripeMut = False
        # 变异算子抽中条带（结构化）是否至少产生一个变异
        self.AtLeastOneBitMut = False
        # 变异算子结构化条带变异幅度数学期望（长度的百分比）
        self.MutDistProb = 0.1
        # 变异算子非结构化条带比特翻转概率
        self.BitFlipRate = 0.1

        # on GA crossover
        # 交叉算子条带抽样概率
        self.CrossOverRate = 0.5
        # 交叉算子两个解之间是否至少抽一个条带交换
        self.AtLeastOneStripeExchg = False

        # on solution space
        # 解空间向外扩展距离为1，坐标变化量的所有组合
        # 选取两个位置为-1和+1，其他位置为0
        # 排列组合问题
        self.OffsetTableLen = self.Dimension * (self.Dimension - 1)
        li = []
        elem = [0 for i in range(self.Dimension)]
        indices = [i for i in range(self.Dimension)]
        for i in range(self.Dimension):
            ind = copy.deepcopy(indices)
            ind.remove(i)
            for j in ind:
                e = copy.deepcopy(elem)
                e[i] = 1
                e[j] = -1
                li.append(e)  # 形成一个坐标
        self.OffsetTable = np.array(li)

        # Population矩阵，pop_size*num_stripes*3
        self.Population = [np.zeros((self.NumStripes, max(self.Dimension, max(self.StripeLenList))), dtype='int8') for i
                           in range(self.PopulationSize)]

    def initPop(self):
        for i in self.PopSoluIndexRange:
            for j in self.SoluStripeIndexRange:
                length = self.StripeLenList[j]
                # 结构化条带
                if self.StripeType[j] == 0:
                    # 根据维度数量生成随机的长度段,注意区分维度长度和条带长度
                    if self.RandomInit:
                        s = 0  # 累计长度
                        solu = []
                        for k in range(self.Dimension - 1):
                            new = random.randrange(0, length - s)
                            solu.append(new)
                            s += new
                        solu.append(length - s)  # 最后一个
                        random.shuffle(solu)  # 乱序
                        for k in range(self.Dimension):
                            self.Population[i][j, k] = solu[k]
                    # 按比例生成长度段
                    else:
                        s = 0
                        for k in range(self.Dimension - 1):
                            new = math.floor(length * self.InitPercent[k])
                            self.Population[i][j, k] = new
                            s += new
                        self.Population[i][j, self.Dimension - 1] = length - s  # 考虑到向下取整的情况，最后一段不比例生成，而是补齐
                # 非结构化条带
                else:
                    for k in range(length):
                        self.Population[i][j, k] = random.choice(self.DimensIndexRange)

    def setNotRandomInit(self, init_perc):
        # 结构化条带初始化百分比
        self.InitPercent = init_perc
        # 结构化条带是否随机初始化
        self.RandomInit = False

    def getPopulation(self):

        re = []

        for i in range(self.PopulationSize):
            indv = []
            for j in range(self.NumStripes):
                if self.StripeType[j] == 0:
                    length = self.Dimension
                    indv.append(self.Population[i][j, 0:length].tolist())
                elif self.StripeType[j] == 1:
                    length = self.StripeLenList[j]
                    indv.append(self.Population[i][j, 0:length].tolist())
                else:
                    raise
            re.append(indv)

        return re

    def setFitness(self, fitness, normalization=False):

        if normalization:
            max_f = max(fitness)
            self.Fitness = [e / max_f for e in fitness]
        else:
            self.Fitness = fitness

    def mutate(self, solution):

        re = copy.deepcopy(solution)

        # stripe抽样
        stripe_list = []
        count = 0
        for i in self.SoluStripeIndexRange:
            if random.random() < self.StripeChoiceProb:
                stripe_list.append(i)
                count += 1
        if count == 0 and self.AtLeastOneStripeMut:
            stripe_list = [random.choice(self.SoluStripeIndexRange)]
        # print(stripe_list)

        # 变异
        # stripe挨个mutate
        for i in stripe_list:
            length = self.StripeLenList[i]
            # 结构化条带变异
            if self.StripeType[i] == 0:
                s = tuple(solution[i, 0:self.Dimension])  # 起点
                # print(s)
                # dt抽样
                dt = 0
                for j in range(length):
                    if random.random() < self.MutDistProb:
                        dt += 1  # 由于是按位抽样，变异幅度与条带长度成比例
                if dt == 0 and self.AtLeastOneBitMut:
                    dt = 1
                if dt == 0:
                    return re
                # dt裁剪
                max_dist = length - min(s)  # max_dist = length - min(x,y,z)，最大变异幅度=条带长度-子段最小长度
                if dt > max_dist:
                    dt = max_dist
                # print(dt)
                # 求dt等距点集
                Q = {s}  # 开放队列
                Pt = []  # 目标点集
                while len(Q) != 0:
                    # print(Q)
                    p = Q.pop()  # 从点集中取点
                    dp = 0
                    for j in self.DimensIndexRange:
                        dp += abs(p[j] - s[j])  # 求距离
                    dp = dp * 0.5  # 该点距离
                    for j in range(self.OffsetTableLen):
                        # 生成新点
                        n = []
                        flag = True
                        dn = 0
                        for k in self.DimensIndexRange:  # 挨个求坐标
                            new_coord = p[k] + self.OffsetTable[j, k]
                            if not (0 <= new_coord <= length):  # 如果不是有效点
                                flag = False
                                # break
                            n.append(new_coord)
                            dn += abs(new_coord - s[k])
                        # print(n)
                        # print(dn)
                        dn = 0.5 * dn  # 新点距离
                        if not flag:
                            continue
                        if dn == dt:
                            Pt.append(tuple(n))
                        elif dn < dt and dn == dp + 1:
                            Q.add(tuple(n))
                # 随机选择
                # 修改
                re[i, 0:self.Dimension] = random.choice(Pt)

            else:
                for j in range(length):
                    if random.random() < self.BitFlipRate:
                        li = copy.deepcopy(self.DimensIndexRange)
                        li.remove(solution[i, j])
                        re[i, j] = random.choice(li)

        return re

    def crossover(self, solution1, solution2):

        re1 = copy.deepcopy(solution1)
        re2 = copy.deepcopy(solution2)

        stripe_list = []
        count = 0
        for i in self.SoluStripeIndexRange:
            if random.random() < self.CrossOverRate:
                stripe_list.append(i)
                count += 1
        if count == 0 and self.AtLeastOneStripeExchg:
            stripe_list = [random.choice(self.SoluStripeIndexRange)]

        # print(stripe_list)
        for i in stripe_list:
            re1[i] = solution2[i]
            re2[i] = solution1[i]

        return re1, re2

    def tournamentSelection(self):
        if self.Fitness[0] == -1:
            raise
        re = []
        while len(re) < self.MatingPoolSize:
            tournament = []
            tournament_fitness = []
            while len(tournament) != self.TournamentSize:
                player = random.choice(range(self.PopulationSize))
                if player not in tournament:
                    tournament.append(player)
                    tournament_fitness.append(self.Fitness[player])
            tournament_sorted_ind = sorted(range(self.TournamentSize), key=lambda k: tournament_fitness[k],
                                           reverse=True)
            for i in range(self.TournamentSize):
                if random.random() < self.TournamentProb * ((1 - self.TournamentProb) ** i):
                    re.append(tournament[tournament_sorted_ind[i]])  # rank index→player index→player(solu index)
                    if len(re) == self.MatingPoolSize:
                        return re

    def genMatingPool(self):
        pool_ind = self.tournamentSelection()
        self.MatingPool = [self.Population[i] for i in pool_ind]

    def poolCrossover(self):

        for i in range(int(self.MatingPoolSize / 2)):
            a1 = self.MatingPool[2 * i]
            a2 = self.MatingPool[2 * i + 1]
            s1, s2 = self.crossover(a1, a2)
            self.MatingPool[2 * i] = s1
            self.MatingPool[2 * i + 1] = s2
        if self.MatingPoolSize % 2:  # 如果数量不成对，则最后一个随机与池中任意一个crossover
            i1 = self.MatingPoolSize - 1
            i2 = random.choice(range(i1))
            a1 = self.MatingPool[i1]
            a2 = self.MatingPool[i2]
            s1, s2 = self.crossover(a1, a2)
            self.MatingPool[i1] = s1
            self.MatingPool[i2] = s2

    def poolMutate(self):
        for i in range(self.MatingPoolSize):
            s = self.mutate(self.MatingPool[i])
            self.MatingPool[i] = s

    def replace(self):
        max_id1 = self.Fitness.index(max(self.Fitness))
        f = copy.deepcopy(self.Fitness)
        f[max_id1] = -999999
        max_id2 = f.index(max(f))
        # print(max_id1,max_id2)
        count = 0
        for i in range(self.PopulationSize):
            if i != max_id1 and i != max_id2:
                self.Population[i] = self.MatingPool[count]
                count += 1
        self.MatingPool = []
