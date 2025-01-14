import matplotlib.pyplot as plt
import numpy as np
import datetime
from dragen.utilities.InputInfo import RveInfo
from dragen.utilities.Helpers import HelperFunctions


class Tesselation3D(HelperFunctions):

    def __init__(self, grains_df):
        super().__init__()

        self.grains_df = grains_df
        self.a = grains_df['a'].tolist()
        self.b = grains_df['b'].tolist()
        self.c = grains_df['c'].tolist()
        self.alpha = grains_df['alpha'].tolist()
        self.x_0 = grains_df['x_0'].tolist()
        self.y_0 = grains_df['y_0'].tolist()
        self.z_0 = grains_df['z_0'].tolist()
        self.final_volume = grains_df['final_discrete_volume'].tolist()
        self.n_grains = len(self.a)
        self.a_max = max(self.a)
        self.b_max = max(self.b)
        self.c_max = max(self.c)

        self.x_grid, self.y_grid, self.z_grid = super().gen_grid()


    def grow(self, iterator, a, b, c):

        alpha = self.alpha[iterator-1]
        x_0 = self.x_0[iterator-1]
        y_0 = self.y_0[iterator-1]
        z_0 = self.z_0[iterator-1]
        a_i = a[iterator - 1]
        b_i = b[iterator - 1]
        c_i = c[iterator - 1]
        a_i = a_i + a_i / self.a_max * RveInfo.bin_size
        b_i = b_i + b_i / self.b_max * RveInfo.bin_size
        c_i = c_i + c_i / self.c_max * RveInfo.bin_size
        a[iterator - 1] = a_i
        b[iterator - 1] = b_i
        c[iterator - 1] = c_i

        ellipsoid = super().ellipsoid(a_i, b_i, c_i, x_0, y_0, z_0, alpha=alpha)

        return ellipsoid, a, b, c

    def tesselation_plotter(self, array, epoch):
        t_0 = datetime.datetime.now()
        n_grains = self.n_grains
        rve_x, rve_y, rve_z = np.where((array >= 1) | (array == -200))

        grain_tuples = [*zip(rve_x, rve_y, rve_z)]

        grains_x = [self.x_grid[grain_tuples_i[0]][grain_tuples_i[1]][grain_tuples_i[2]]
                    for grain_tuples_i in grain_tuples]
        grains_y = [self.y_grid[grain_tuples_i[0]][grain_tuples_i[1]][grain_tuples_i[2]]
                    for grain_tuples_i in grain_tuples]
        grains_z = [self.z_grid[grain_tuples_i[0]][grain_tuples_i[1]][grain_tuples_i[2]]
                    for grain_tuples_i in grain_tuples]

        fig = plt.figure()
        ax = fig.add_subplot(111, projection='3d')
        ax.scatter(grains_x, grains_y, grains_z, c=array[np.where((array >= 1) | (array == -200))], s=1, vmin=-20,
                   vmax=n_grains, cmap='seismic')

        rve_x, rve_y, rve_z = np.where((array == 0))

        free_space_tuples = [*zip(rve_x, rve_y, rve_z)]

        free_space_x = [self.x_grid[free_space_tuples_i[0]][free_space_tuples_i[1]][free_space_tuples_i[2]]
                    for free_space_tuples_i in free_space_tuples]
        free_space_y = [self.y_grid[free_space_tuples_i[0]][free_space_tuples_i[1]][free_space_tuples_i[2]]
                    for free_space_tuples_i in free_space_tuples]
        free_space_z = [self.z_grid[free_space_tuples_i[0]][free_space_tuples_i[1]][free_space_tuples_i[2]]
                    for free_space_tuples_i in free_space_tuples]
        ax.scatter(free_space_x, free_space_y, free_space_z, color='grey', alpha=0.01)

        ax.set_xlim(-5, RveInfo.box_size + 5)
        ax.set_ylim(-5, RveInfo.box_size + 5)
        ax.set_zlim(-5, RveInfo.box_size + 5)
        ax.set_xlabel('x (µm)')
        ax.set_ylabel('y (µm)')
        ax.set_zlabel('z (µm)')
        # ax.view_init(90, 270) #facing against z-direction (counterclockwise rotation)
        # plt.show()
        plt.savefig(RveInfo.store_path + '/Figs/3D_Tesselation_Epoch_{}.png'.format(epoch))
        plt.close(fig)
        time_elapse = datetime.datetime.now() - t_0
        if RveInfo.debug:
            RveInfo.LOGGER.info('time spent on plotter for epoch {}: {}'.format(epoch, time_elapse.total_seconds()))

    def run_tesselation(self, rsa, grain_df=None, band_idx_start=None):
        if RveInfo.gui_flag:
            RveInfo.infobox_obj.emit('starting Tesselation')
            RveInfo.progress_obj.emit(0)

        # set some variables
        status = False
        repeat = False
        packingratio = 0
        epoch = 0
        band_vol_0 = np.count_nonzero(rsa == -200)  # This volume is already affected by the First band ratio
        # So total Band ratio is band_ratio_rsa * band_ratio_tesselator

        # load some variables
        a = self.a
        b = self.b
        c = self.c
        n_grains = len(self.a)
        rve = rsa
        if band_idx_start is None:
            band_idx = []
        else:
            band_idx = [i for i in range(band_idx_start, n_grains+1)]
            #print(band_idx)

        # define boundaries and empty rve array
        empty_rve = super().gen_array()
        empty_rve = super().gen_boundaries_3D(empty_rve)
        rve_boundaries = empty_rve.copy()  # empty rve grid with defined boundaries
        vol_0 = np.count_nonzero(empty_rve == 0)

        freepoints = np.count_nonzero(rve == 0)
        grain_idx = [i for i in range(1, n_grains + 1)]
        grain_idx_backup = grain_idx.copy()
        while freepoints > 0:
            freepoints_old = freepoints   # Zum Abgleich
            i = 0
            np.random.shuffle(grain_idx)
            while i < len(grain_idx):
                idx = grain_idx[i]
                ellipsoid, a, b, c = self.grow(idx, a, b, c)
                grain = rve_boundaries.copy()
                grain[(ellipsoid <= 1) & (grain == 0)] = idx
                periodic_grain = super().make_periodic_3D(grain, ellipsoid, iterator=idx)
                band_vol = np.count_nonzero(rve == -200)

                if band_vol_0 > 0:
                    band_ratio = band_vol / band_vol_0
                    if band_ratio > RveInfo.band_ratio_final:
                        rve[((periodic_grain == idx) & (rve == 0)) | ((periodic_grain == idx) & (rve == -200))] = idx
                    else:
                        rve[((periodic_grain == idx) & (rve == 0))] = idx
                else:
                    rve[((periodic_grain == idx) & (rve == 0))] = idx

                freepoints = np.count_nonzero(rve == 0)
                grain_vol = np.count_nonzero(rve == idx) * RveInfo.bin_size ** 3
                if freepoints == 0:
                    break

                '''
                Grow control: 
                1.) If a grain reaches Maximum Volume, the index gets deleted
                2.) If a grain is not growing in reality (difference between freepoints and freepoints_old), the 
                grain is deleted. This avoids background growing and dumb results
                Counting (i = i + 1) up only if no deletion happens
                '''
                # TODO: Aus irgendeinem Grund funktioniert das immer noch nicht mit den Bandpunkten.
                # Als Workaround werden alle Bandpunkte nach 8 Epochen gelöscht, damit funktioniert es
                delta_grow = freepoints_old - freepoints
                if (idx in band_idx) and (epoch == 8):
                    #print('Del because of epoch')
                    grain_idx.remove(idx)
                    grain_idx_backup.remove(idx)
                elif (grain_vol > self.final_volume[idx-1]) and not repeat:
                    grain_idx.remove(idx)
                    if idx in band_idx:
                        #print('Del from Backup')
                        grain_idx_backup.remove(idx)
                elif delta_grow == 0: # and not repeat:    # and not repeat beobachten
                    grain_idx.remove(idx)
                    #grain_idx_backup.remove(idx)
                else:
                    i += 1

            if not grain_idx:
                repeat = True
                if RveInfo.gui_flag:
                    RveInfo.infobox_obj.emit('grain growth had to be reset at {}% of volume filling'.format(packingratio))
                if packingratio < 90:
                    if RveInfo.gui_flag:
                        RveInfo.infobox_obj.emit('your microstructure data does not contain \n'
                                              'enough data to fill this boxsize\n'
                                              'please decrease the boxsize for reasonable results')
                grain_idx = grain_idx_backup.copy()
            if RveInfo.anim_flag:
                self.tesselation_plotter(rve, epoch)
            epoch += 1
            packingratio = (1 - freepoints / vol_0) * 100
            # print('packingratio:', packingratio, '%')
            if RveInfo.gui_flag:
                RveInfo.progress_obj.emit(packingratio)
            else:
                if RveInfo.gui_flag:
                    RveInfo.progress_obj.emit('packingratio: ', packingratio)
                else:
                    RveInfo.LOGGER.info('packingratio: {}'.format(packingratio))

        if packingratio == 100:
            status = True

        # Save for further usage
        np.save(RveInfo.store_path + '/' + 'RVE_Numpy.npy', rve)
        return rve, status


if __name__ == '__main__':
    a = [10,10,10,10,10,10,10,10,10,10,10,10,10,10,10,10,10,10,10,10,10,10,10,10,10]
    b = [5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5]
    c = [5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5]
    # Define Box-dimension
    box_size = 100
    # Define resolution of Grid
    n_pts = 100

    shrinkfactor = 0.01

    x0_path = './3D_x0_list.npy'
    y0_path = './3D_y0_list.npy'
    z0_path = './3D_z0_list.npy'
    x_0 = np.load(x0_path)
    y_0 = np.load(y0_path)
    z_0 = np.load(z0_path)

    tesselation_obj = Tesselation3D(box_size, n_pts, a, b, c, x_0, y_0, z_0, shrinkfactor)
    tesselation_obj.run_tesselation()



