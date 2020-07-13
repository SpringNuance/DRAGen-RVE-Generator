import sys
import time
import os
import math
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import multiprocessing as mp

from random import randrange
from mpl_toolkits.mplot3d import Axes3D
from tqdm.auto import tqdm

from dragen.utilities.RVE_utils import RVE_utils

class DiscreteRSA:

    def __init__(self, box_size, points_on_edge, tolerance, number_of_bands, bandwidth = 0):
        # LOGGER initialization
        self.box_size = box_size
        self.points_on_edge = points_on_edge
        self.step_size = box_size/points_on_edge
        self.tolerance = tolerance
        self.step_half = self.step_size/2
        self.double_box = box_size*2
        self.number_of_bands = number_of_bands
        self.bandwidth = bandwidth
        self.radius = 1.0

    def RSA3D(self, store_path, phase1, phase2):
        utils_obj = RVE_utils(self.box_size, self.points_on_edge, self.bandwidth)
        total_number_of_grains = len(phase1)
        pbar = tqdm(total=total_number_of_grains)
        ############Generate Grid###############
        pool = mp.Pool(mp.cpu_count())
        seed_grid_xyz = np.arange(self.step_half, self.box_size, self.step_size)
        xyz = np.arange(-self.box_size + self.step_half, self.double_box, self.step_size)
        xyzmin = min(abs(xyz))

        pt, phase, accepted_grains_list, radii = ([] for i in range(4))
        accepted_grains = set()
        bandcontrolset = set()
        band = set()
        bandvol0 = 1

        mesh = np.meshgrid(seed_grid_xyz, seed_grid_xyz, seed_grid_xyz)
        seed_grid = list(zip(*(dim.flat for dim in mesh)))
        seed_grid = set(seed_grid)

        ##########Generate Ellipses###############
        Vol0 = len(seed_grid_xyz)*len(seed_grid_xyz)*len(seed_grid_xyz)
        n = 0
        count = 0
        trial = seed_grid
        while len(phase1) > 0 and len(phase2) > 0:
            if phase1[0][0] > phase2[0][0]:
                radii.append(phase1[0])
                phase.append(1)
                del phase1[0]
            else:
                radii.append(phase2[0])
                phase.append(2)
                del phase2[0]
        if len(phase2) == 0:
            for i in range(len(phase1)):
                radii.append(phase1[i])
                phase.append(1)
        elif len(phase1) == 0:
            for i in range(len(phase2)):
                radii.append(phase2[i])
                phase.append(2)

        ###############################
        #   Initialize Bands here     #
        ###############################
        for i in range(self.number_of_bands): #Works only for one band at the moment
            band = utils_obj.band_generator(seed_grid_xyz, plane='xy')
            bandcontrolset.update(band)
            bandvol0 = len(bandcontrolset)
            seed_grid.difference(band)

        while n < total_number_of_grains and len(trial) > 0:
            if n == 0:
                grid_index = randrange(len(trial))
                x0 = list(trial)[grid_index][0]
                y0 = list(trial)[grid_index][1]
                z0 = list(trial)[grid_index][2]
                A0 = (1. / radii[n][0]) ** 2
                B0 = (1. / radii[n][1]) ** 2
                C0 = (1. / radii[n][2]) ** 2

                grid_index = randrange(len(trial))
                x1 = list(trial)[grid_index][0]
                y1 = list(trial)[grid_index][1]
                z1 = list(trial)[grid_index][2]
                A1 = (1. / radii[n+1][0]) ** 2
                B1 = (1. / radii[n+1][1]) ** 2
                C1 = (1. / radii[n+1][2]) ** 2

                grainx, grainy, grainz = np.meshgrid(xyz, xyz, xyz)
                r = np.sqrt(A0*(grainx - x0)**2 + B0*(grainy - y0)**2 + C0*(grainz - z0)**2)
                r2 = np.sqrt(A1*(grainx - x1)**2 + B1*(grainy - y1)**2 + C1*(grainz - z1)**2)
                inside = r <= radius
                inside2 = r2 <= radius
                graincoord = [grainx[inside],grainy[inside],grainz[inside]]
                per_grain = [utils_obj.periodicity_RSA(graincoord, xyz) for graincoord in graincoord]
                graincoord2 = [grainx[inside2], grainy[inside2], grainz[inside2]]
                per_grain2 = [utils_obj.periodicity_RSA(graincoord2, xyz) for graincoord2 in graincoord2]
                grain1 = set(list(zip(per_grain[0],per_grain[1],per_grain[2])))
                grain2 = set(list(zip(per_grain2[0],per_grain2[1],per_grain2[2])))

                intersect = .intersection(grain2)
                bandintersect1 = grain1.intersection(band)
                bandintersect2 = grain2.intersection(band)

                if len(intersect) == 0 and len(bandintersect1) == 0 and len(bandintersect2) == 0:
                    accepted_grains.update(grain1)
                    accepted_grains.update(grain2)
                    accepted_grains_list.append(grain1)
                    accepted_grains_list.append(grain2)
                    seed_grid = seed_grid.difference(grain1)
                    seed_grid = seed_grid.difference(grain2)
                    pt.append((x0,y0,z0))
                    pt.append((x1,y1,z1))
                    vol = 4 / 3 * np.pi * radii[n][0] * radii[n][1] * radii[n][2]
                    vol = vol + 4 / 3 * np.pi * radii[n + 1][0] * radii[n + 1][1] * radii[n + 1][2]
                    n = n + 2

                elif len(bandintersect1)/bandvol0 < 0.40 and len(bandintersect2) == 0:
                    band = band.difference(grain1)
                    accepted_grains.update(grain1)
                    accepted_grains.update(grain2)
                    accepted_grains_list.append(grain1)
                    accepted_grains_list.append(grain2)
                    seed_grid = seed_grid.difference(grain1)
                    seed_grid = seed_grid.difference(grain2)
                    pt.append((x0, y0, z0))
                    pt.append((x1, y1, z1))
                    vol = 4 / 3 * np.pi * radii[n][0] * radii[n][1] * radii[n][2]
                    vol = vol + 4 / 3 * np.pi * radii[n + 1][0] * radii[n + 1][1] * radii[n + 1][2]
                    n = n + 2

                elif len(bandintersect1) == 0 and len(bandintersect2) /bandvol0 < 0.40:
                    band = band.difference(grain2)
                    accepted_grains.update(grain1)
                    accepted_grains.update(grain2)
                    accepted_grains_list.append(grain1)
                    accepted_grains_list.append(grain2)
                    seed_grid = seed_grid.difference(grain1)
                    seed_grid = seed_grid.difference(grain2)
                    pt.append((x0, y0, z0))
                    pt.append((x1, y1, z1))
                    vol = 4 / 3 * np.pi * radii[n][0] * radii[n][1] * radii[n][2]
                    vol = vol + 4 / 3 * np.pi * radii[n + 1][0] * radii[n + 1][1] * radii[n + 1][2]
                    n = n + 2

                elif (len(bandintersect1)+len(bandintersect2))/bandvol0 < 0.4:
                    band = band.difference(grain1)
                    band = band.difference(grain2)
                    accepted_grains.update(grain1)
                    accepted_grains.update(grain2)
                    accepted_grains_list.append(grain1)
                    accepted_grains_list.append(grain2)
                    seed_grid = seed_grid.difference(grain1)
                    seed_grid = seed_grid.difference(grain2)
                    pt.append((x0, y0, z0))
                    pt.append((x1, y1, z1))
                    vol = 4 / 3 * np.pi * radii[n][0] * radii[n][1] * radii[n][2]
                    vol = vol + 4 / 3 * np.pi * radii[n + 1][0] * radii[n + 1][1] * radii[n + 1][2]
                    n = n + 2
                else:
                    print('Intersection too big')
                trial = seed_grid
            else:
                grid_index = randrange(len(trial))
                x0 = list(trial)[grid_index][0]
                y0 = list(trial)[grid_index][1]
                z0 = list(trial)[grid_index][2]
                A = (1./radii[n][0])**2
                B = (1./radii[n][1])**2
                C = (1./radii[n][2])**2
                grainx, grainy, grainz = np.meshgrid(xyz, xyz, xyz)
                r = np.sqrt(A*(grainx - x0)**2 + B*(grainy - y0)**2 + C*(grainz - z0)**2)
                inside = r <= radius
                graincoord = [grainx[inside], grainy[inside], grainz[inside]]
                per_grain = [utils_obj.periodicity_RSA(graincoord, xyz) for graincoord in graincoord]
                grain1 = set(list(zip(per_grain[0], per_grain[1], per_grain[2])))
                intersect = accepted_grains.intersection(grain1)
                bandintersect = band.intersection(grain1)
                if 1 - (len(band) - len(bandintersect))/bandvol0 < 0.40 or band == set():
                    if len(bandintersect) !=0:
                        band = band.difference(grain1)

                    if len(intersect) != 0:
                        size = len(accepted_grains)-len(intersect)
                        frac = size/len(grain1)
                        if frac <= self.tolerance:
                            if len(grain1) == 0:
                                print('Error ', grain1, n) # LOGGER
                                sys.exit(0)

                            accepted_grains.update(grain1)
                            accepted_grains_list.append(grain1)
                            seed_grid = seed_grid.difference(grain1)
                            currvol = 4 / 3 * np.pi * radii[n][0] * radii[n][1] * radii[n][2]
                            vol = vol + currvol
                            pt.append((x0, y0, z0))
                            n = n + 1
                            trial = seed_grid
                            count = 0
                        else:
                            count = count+1
                            trialseed = {(x0, y0, z0)}
                            trial = trial.difference(trialseed)

                    else:
                        if len(grain1) == 0:
                            print('Error ', grain1) # LOGGER
                            sys.exit(0)
                        accepted_grains.update(grain1)
                        accepted_grains_list.append(grain1)
                        seed_grid = seed_grid.difference(grain1)
                        vol = vol + 4 / 3 * np.pi * radii[n][0] * radii[n][1] * radii[n][2]
                        pt.append((x0,y0,z0))
                        n = n + 1
                        trial = seed_grid
                        count = 0
                        pbar.update(1)
        pool.close()

        fig = plt.figure()
        ax = fig.add_subplot(111, projection='3d')
        ax.set_xlim3d(0, boxsize)
        ax.set_ylim3d(0, boxsize)
        ax.set_zlim3d(0, boxsize)
        ax.set_xlabel('x [µm]')
        ax.set_ylabel('y [µm]')
        ax.set_zlabel('z [µm]')

        rsa = pd.DataFrame()
        graindf = []
        for i, grain in enumerate(accepted_grains_list):
            graindf.append(pd.DataFrame(grain, columns=['x', 'y', 'z']))
            graindf[i]['GrainID'] = i
            graindf[i]['phaseID'] = phase[i]
            if phase[i] == 1:
                try:
                   ax.scatter(*zip(*grain))
                except:
                    print(grain)
                    sys.exit(0)

            if phase[i] == 2:
                ax.scatter(*zip(*grain), c='k')
            rsa = pd.concat([rsa, graindf[i]])

        if numberofbands > 0:
            ax.scatter(*zip(*band),c='k')

        rsa['Orientation'] = 0
        for i in tqdm(range(len(rsa.groupby(['GrainID'])) + 1)):
            rsa.loc[rsa.GrainID == i, 'Orientation'] = \
                np.random.randint(360)
        rsa.loc[rsa.phaseID == 2, 'Orientation'] = 720

        # Raumfüllung:
        Raumfuellung = 0
        for grain in accepted_grains_list:
            Raumfuellung = Raumfuellung + len(grain)
        Raumfuellung = Raumfuellung / Vol0 * 100
        print('Die Raumfüllung beträgt: ' + str(Raumfuellung) + '%')
        print(str(len(accepted_grains_list)) + ' Grains have been placed')
        if not os.path.isdir(store_path + '/Fig'):
            os.system('mkdir '+ store_path + '/Fig')
        plt.savefig(store_path + '/Fig/RSA')
        if len(accepted_grains_list) == total_number_of_grains:
            status = True
        else:
            status = False

        single_layer = rsa[rsa['x'] == xyzmin]
        print(single_layer)
        #sys.exit()
        fig, ax = plt.subplots()
        ax.set_xlim(0, boxsize)
        ax.set_ylim(0, boxsize)
        ax.set_xlabel('y (µm)')
        ax.set_ylabel('z (µm)')
        ax.scatter(single_layer['y'], single_layer['z'], c=single_layer['GrainID'], s=1, cmap='gist_rainbow')
        plt.savefig(store_path + '/Fig/2DRSA')

        return pt, radii, phase, band, status