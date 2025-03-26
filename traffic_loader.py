# 交通模块

import pickle


class TRAFFIC_LOADER:
    def __init__(self, num_exp, path, ignore_numexp):
        with open(path, 'rb') as f:
            self.VehicleList, _ = pickle.load(f)
            if len(self.VehicleList) != num_exp and not ignore_numexp:
                raise

        self.Path = path

    def getVehicleList(self):
        return self.VehicleList
