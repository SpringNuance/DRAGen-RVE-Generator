from dragen.run import Run
dimension = 3
box_size = 700
box_size_y = None  # if this is None it will be set to the main box_size value
box_size_z = 300  # for sheet rve set z to None and y to different value than x the other way round is buggy
resolution = 0.07
number_of_rves = 1
smoothing_flag = True
# Banding Params
number_of_bands = 0
band_filling = 0.6
band_orientation = 'xy'
lower_band_bound = 2
upper_band_bound = 5
visualization_flag = False
root = r'E:\Sciebo\IEHK\Publications\ComputationalSci\DRAGen\matdata'
shrink_factor = 0.4
# Substructure params
equiv_d = 5
p_sigma = 0.1
t_mu = 1.0
b_sigma = 0.1
inclusion_flag = False
inclusion_ratio = 0.01
slope_offset = 0
# Example Files
#
#
###NO30
file1 = r'F:/OCAS/NO30_RVE_data/Data_processed.csv'

#DP800
#file1 = r'E:\Sciebo\IEHK\Publications\ComputationalSci\DRAGen\matdata\DP800/TrainedData_Ferrite.pkl'
#file2 = r'E:\Sciebo\IEHK\Publications\ComputationalSci\DRAGen\matdata\DP800/TrainedData_Martensite.pkl'

#Bainite
#PAGs

#Blocks

#Inclusions
file5 = r'E:\Sciebo\IEHK\Publications\ComputationalSci\DRAGen\matdata\Inclusions/Inclusions_DRAGen_Input.csv'

#Bands
#file6 = r'E:\Sciebo\IEHK\Publications\ComputationalSci\DRAGen\matdata\DP800/TrainedData_Martensite.pkl'
file6 = r'E:\Sciebo\IEHK\Publications\ComputationalSci\DRAGen\matdata\DP800/TrainedData_Ferrite.pkl'

# test pearlite phase
subs_flag = False
subs_file = 'C:/temp/substructdata/bainite_Seite1_Dicke.csv'
subs_file_flag = True
gui_flag = False
gan_flag = False
moose_flag = True
abaqus_flag = True
pbc_flag = True
submodel_flag = False
damask_flag = True
phase2iso_flag = True
element_type = 'HEX8'
anim_flag = False

files = {1: file1}  # , 2: file2, 6: file6}
phase_ratio = {1: 1}  # , 2: 0.2, 6: 0}  # Pass for bands
phases = ['Ferrite']  # , 'Martensite', 'Bands']

'''
specific number is fixed for each phase. 1->ferrite, 2->martensite so far. The order of input files should also have the 
same order as phases. file1->ferrite, file2->martensite. The substructures will only be generated in martensite.

Number 5 specifies the inclusions and number 6 the Band phase. Either .csv or .pkl
'''

Run(box_size, element_type=element_type, box_size_y=box_size_y, box_size_z=box_size_z, resolution=resolution,
    number_of_rves=number_of_rves,
    number_of_bands=number_of_bands, dimension=dimension, slope_offset=slope_offset, smoothing_flag = True,
    visualization_flag=visualization_flag, file_dict=files, equiv_d=equiv_d, p_sigma=p_sigma, t_mu=t_mu,
    b_sigma=b_sigma,
    phase_ratio=phase_ratio, root=root, shrink_factor=shrink_factor, gui_flag=gui_flag,
    gan_flag=gan_flag, pbc_flag=pbc_flag, submodel_flag=submodel_flag, phase2iso_flag=phase2iso_flag,
    info_box_obj=None, progress_obj=None, subs_file_flag=subs_file_flag, subs_file=subs_file, phases=phases,
    subs_flag=subs_flag, moose_flag=moose_flag, abaqus_flag=abaqus_flag, damask_flag=damask_flag,
    anim_flag=anim_flag, inclusion_flag=inclusion_flag,
    inclusion_ratio=inclusion_ratio, band_filling=band_filling, lower_band_bound=lower_band_bound,
    upper_band_bound=upper_band_bound, band_orientation=band_orientation,).run()
