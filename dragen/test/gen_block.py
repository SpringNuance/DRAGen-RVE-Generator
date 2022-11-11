import sys

import pandas as pd
from sklearn.neighbors import KernelDensity
from sklearn.model_selection import KFold, GridSearchCV
import numpy as np
from dragen.utilities.InputInfo import RveInfo
from scipy.stats import lognorm, truncnorm, uniform
import matplotlib.pyplot as plt
from typing import Tuple


class SubsDistribution:
    def __init__(self, estimator):
        self.estimator = estimator

    def pdf(self, x: [float, np.ndarray]) -> np.ndarray:
        x = np.array(x).reshape(-1, 1)
        if isinstance(self.estimator, KernelDensity):
            result = np.exp(self.estimator.score_samples(x))
        else:
            result = self.estimator.pdf(x)

        return result.reshape(-1, 1)


def dis_to_id(dis, bt_list):
    idx = np.where(bt_list > dis)
    if len(idx[0]) == 0:
        return str(len(bt_list))
    else:
        return str(int(idx[0][0] - 1))


def gen_block(packet: pd.DataFrame, bt_distribution: SubsDistribution) -> pd.DataFrame:
    # select a random norm direction for block boundary
    block_boundary_norm, bad_bt_flag = choose_block_boundary_norm(packet=packet)

    if not bad_bt_flag:
        # compute d of block boundary
        pd = -(packet['x'] * block_boundary_norm[..., 0] + packet['y'] * block_boundary_norm[..., 1] + packet['z'] *
               block_boundary_norm[..., 2])
        # compute the distance to the block boundary with maximum d
        packet.insert(6, 'pd', value=pd)
        sq = np.sqrt(block_boundary_norm[..., 0] ** 2 +
                     block_boundary_norm[..., 1] ** 2 +
                     block_boundary_norm[..., 2] ** 2)
        p_dis = (packet['pd'].max() - packet['pd']) / sq
        packet.insert(7, 'p_dis', value=p_dis)

        total_bt = packet['p_dis'].max()
        bt_list = bt_sampler(bt_distribution=bt_distribution,
                             total_bt=total_bt,
                             interval=[RveInfo.bt_min, RveInfo.bt_max])
        dis_list = np.cumsum(bt_list)
        dis_list = np.insert(dis_list, 0, 0)
        block_id = packet['p_dis'].map(lambda dis: dis_to_id(dis, dis_list))
        packet['block_id'] = packet['packet_id'] + block_id
        packet.drop('pd', axis=1, inplace=True)
    else:
        print("bad block thickness computation!")
        sys.exit()

    return packet


def block_data_parser() -> SubsDistribution:
    if RveInfo.block_file is not None:
        print("here")
        block_data = pd.read_csv(RveInfo.block_file)
        kFold = KFold(n_splits=10)  # k-folder cross-validation split data into 10 folds
        bandwidths = 10 ** np.linspace(-1, 1, 100)
        grid = GridSearchCV(estimator=KernelDensity(kernel="gaussian"),
                            param_grid={"bandwidth": bandwidths},
                            cv=kFold)
        grid.fit(np.array(block_data['block_thickness']).reshape(-1, 1))
        return SubsDistribution(grid.best_estimator_)
    else:
        return SubsDistribution(lognorm(s=RveInfo.b_sigma, scale=RveInfo.t_mu))  # check later


def test_block_data_parser():
    RveInfo.block_file = r"F:\DRAGen\ExampleInput\example_block_inp.csv"
    kde = block_data_parser()
    x = np.linspace(0, 5, 100).reshape(-1, 1)
    density = kde.pdf(x)
    plt.plot(x, density, label='file_data')

    RveInfo.block_file = None
    RveInfo.b_sigma = 0.3
    RveInfo.t_mu = 1.0

    LN = block_data_parser()
    x = np.linspace(LN.estimator.ppf(0.01),
                    LN.estimator.ppf(0.99), 100)

    plt.plot(x, LN.pdf(x), label='user_data')
    plt.legend()
    plt.savefig('./results/block_thickness_density.png')


def bt_sampler(bt_distribution: SubsDistribution, total_bt: float, interval: list) -> list:
    # set to be minimal block thickness at the beginning
    bts = [interval[0]]
    n = 0
    while total_bt - sum(bts) > interval[0]:
        n = n + 1
        bt_star = truncnorm.rvs(a=(interval[0] - bts[n - 1]) / 0.5, b=(interval[1] - bts[n - 1]) / 0.5, loc=bts[n - 1],
                                scale=0.5,
                                size=1)  # trial sample from proposal distribution
        alpha = min(1, bt_distribution.pdf(x=bt_star[0])[0, 0] / bt_distribution.pdf(x=bts[n - 1])[
            0, 0])  # accept probability
        u = uniform().rvs(1)[0]
        if u < alpha:  # accept sample
            if sum(bts) + bt_star[0] > total_bt:  # ensure the sum of bts equal total bt
                new_bt = total_bt - sum(bts)
            else:
                new_bt = bt_star[0]
        else:
            if sum(bts) + bts[n - 1] > total_bt:  # ensure the sum of bts equal total bt
                new_bt = total_bt - sum(bts)
            else:
                new_bt = bts[n - 1]
        bts.append(new_bt)
    print("get bts successfully!")
    return bts


def choose_block_boundary_norm(packet: pd.DataFrame) -> Tuple[np.ndarray, bool]:
    bad_bt_flag = False  # if the packet are subdivided into more than 4 parts the computation block thickness is wrong
    block_boundary_norm = np.random.uniform(0, 1, (1, 3))
    x_max = RveInfo.box_size
    y_max = RveInfo.box_size_y if RveInfo.box_size_y is not None else RveInfo.box_size
    z_max = RveInfo.box_size_y if RveInfo.box_size_z is not None else RveInfo.box_size
    if 0.0 in packet['x'].values and x_max in packet['x'].values:
        block_boundary_norm[0, 0] = 0.0

    if 0.0 in packet['y'].values and y_max in packet['y'].values:
        block_boundary_norm[0, 0] = 0.0

    if 0.0 in packet['z'].values and z_max in packet['z'].values:
        block_boundary_norm[0, 0] = 0.0

    if pd.DataFrame(block_boundary_norm.reshape(-1, 1)).value_counts()[0.0] == 3:  # count number of 0
        block_boundary_norm = np.array([[0, 0, 1]])
        bad_bt_flag = True

    return block_boundary_norm, bad_bt_flag


def test_choose_boundary_norm():
    subs_file = r"F:\DRAGen\OutputData\2022-11-10_000\substruct_data.csv"
    subs_data = pd.read_csv(subs_file)
    packet = subs_data.loc[subs_data["packet_id"] == 2]
    RveInfo.box_size = 35
    block_boundary_norm, bad_bt_flag = choose_block_boundary_norm(packet=packet)
    assert not bad_bt_flag
    assert block_boundary_norm[0, 0] == 0.0 and block_boundary_norm[0, 1] != 0.0 and block_boundary_norm[0, 2] != 0.0


if __name__ == "__main__":
    subs_file = r"F:\DRAGen\OutputData\2022-11-10_000\substruct_data.csv"
    subs_data = pd.read_csv(subs_file)
    # test_block_data_parser()
    RveInfo.block_file = r"F:\DRAGen\OutputData\2022-11-10_000\substruct_data.csv"
    bt_distribution = block_data_parser()
    print("get distribution")
    # packet = subs_data[subs_data['packet_id'] == 2]
    # gen_block(packet=packet, bt_distribution=bt_distribution)
    # print(packet)
    # ax = plt.figure().add_subplot(111, projection = '3d')
    # ax.scatter(packet['x'],packet['y'],packet['z'])
    # plt.show()
