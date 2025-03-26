# 数据收集模块

import numpy as np


class DATA_COLLECTOR:
    def __init__(self):
        self.GameInfoArray = None
        self.GameStatArray = None
        self.Description = None

    def newGame(self, info_list):
        if self.GameInfoArray is None:
            self.GameInfoArray = np.array([info_list])
        else:
            self.GameInfoArray = np.append(self.GameInfoArray, [info_list], axis=0)

    def endGame(self, stat_list):
        if self.GameStatArray is None:
            self.GameStatArray = np.array([stat_list])
        else:
            self.GameStatArray = np.append(self.GameStatArray, [stat_list], axis=0)

    def addDescription(self, describe):
        self.Description = describe

    def gameBatch(self, infos, stats):
        if self.GameInfoArray is None:
            self.GameInfoArray = np.array(infos)
        else:
            self.GameInfoArray = np.append(self.GameInfoArray, infos, axis=0)
        if self.GameStatArray is None:
            self.GameStatArray = np.array(stats)
        else:
            self.GameStatArray = np.append(self.GameStatArray, stats, axis=0)

    def filterData(self, game_filter: tuple, stat_filter: tuple) -> list:
        """
        提取实验记录数据
        不保证展平顺序
        列是信息，行是实验
        输入：
        实验过滤列表，顺序为代号-实验号-个体号（见主程序定义dcdc2），长度固定为gameinfo长度，不过滤为-1，(x,x,x)
        实验过滤列表，顺序为代号（dc1）
        数据过滤列表，不定长列表，(x,x,...)
        返回：
        数据列表[[data1],[data2],...]
        """
        if len(game_filter) != self.GameInfoArray.shape[1]:
            raise
        length = len(game_filter)
        num_default = game_filter.count(-1)
        if num_default == length:
            re = []
            for e in stat_filter:
                re.append(self.GameStatArray[:, e])
            return re
        elif num_default == length - 1:
            filter_index = game_filter.index(next(filter(lambda x: x != -1, game_filter)))
            condition = self.GameInfoArray[:, filter_index] == game_filter[filter_index]
            re = []
            for e in stat_filter:
                re.append(self.GameStatArray[condition][:, e])
            return re
        else:
            condition_text = ''
            for i in range(length):
                if game_filter[i] != -1:
                    condition_text += '(self.GameInfoArray[:,' + str(i) + ']==' + str(game_filter[i]) + ')&'
            condition_text = condition_text[0:-1]
            # print(condition_text)
            re = []
            for e in stat_filter:
                re.append(self.GameStatArray[eval(condition_text)][:, e])
            return re
