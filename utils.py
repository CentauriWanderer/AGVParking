# 辅助函数

import math


def getDist(a, b):
    if a[0] == -1 or b[0] == -1:  # 如果是虚拟点直接返回最大距离
        return 9999
    else:
        return abs(b[0] - a[0]) + abs(b[1] - a[1])


def showArray(array):
    if len(array.shape) == 2:
        array = array.T
        print(array[::-1, :])
    elif len(array.shape) == 3:
        for i in range(array.shape[0]):
            layer = array[i]
            layer = layer.T
            print(layer[::-1, :])


def printTime(stp):
    seconds = stp * 5
    num_h = seconds // 3600
    num_m = (seconds - num_h * 3600) // 60
    num_s = seconds - num_h * 3600 - num_m * 60
    return str(num_h) + ':' + str(num_m) + ':' + str(num_s)


def normalization(l):
    m = max(l)
    return [e / m for e in l]


def level(l):
    m = min(l)
    base = (max(l) - min(l)) / 2.0
    return [e - m + base for e in l]


def oneMinus(l):
    return [1.0 - e for e in l]


def inverse(l):
    return [1 / (e + 0.05) for e in l]


def power3(l):
    return [e ** 3 for e in l]


def maxMinus(l):
    m = max(l)
    return [m - e for e in l]


def logarithm(l):
    return [math.log10(e) for e in l]


def minus20k(l):
    return [e - 20000 for e in l]

def minus15k(l):
    return [e - 15000 for e in l]
