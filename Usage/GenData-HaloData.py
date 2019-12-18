#   ______   __    __  __    __  __       __  __       __ 
#  /      \ /  |  /  |/  |  /  |/  \     /  |/  \     /  |
# /$$$$$$  |$$ |  $$ |$$ |  $$ |$$  \   /$$ |$$  \   /$$ |
# $$ |  $$/ $$ |__$$ |$$ |  $$ |$$$  \ /$$$ |$$$  \ /$$$ |
# $$ |      $$    $$ |$$ |  $$ |$$$$  /$$$$ |$$$$  /$$$$ |
# $$ |   __ $$$$$$$$ |$$ |  $$ |$$ $$ $$/$$ |$$ $$ $$/$$ |
# $$ \__/  |$$ |  $$ |$$ \__$$ |$$ |$$$/ $$ |$$ |$$$/ $$ |
# $$    $$/ $$ |  $$ |$$    $$/ $$ | $/  $$ |$$ | $/  $$ |
#  $$$$$$/  $$/   $$/  $$$$$$/  $$/      $$/ $$/      $$/

#    _____          _         __             _    _       _                        _    _ __  __       _       _   _                      __   __  __               
#   / ____|        | |       / _|           | |  | |     | |                      | |  | |  \/  |     | |     | | (_)                    / _| |  \/  |              
#  | |     ___   __| | ___  | |_ ___  _ __  | |__| | __ _| | ___     __ _  ___ ___| |  | | \  / |_   _| | __ _| |_ _  ___  _ __     ___ | |_  | \  / | __ _ ___ ___ 
#  | |    / _ \ / _` |/ _ \ |  _/ _ \| '__| |  __  |/ _` | |/ _ \   / _` |/ __/ __| |  | | |\/| | | | | |/ _` | __| |/ _ \| '_ \   / _ \|  _| | |\/| |/ _` / __/ __|
#  | |___| (_) | (_| |  __/ | || (_) | |    | |  | | (_| | | (_) | | (_| | (_| (__| |__| | |  | | |_| | | (_| | |_| | (_) | | | | | (_) | |   | |  | | (_| \__ \__ \
#   \_____\___/ \__,_|\___| |_| \___/|_|    |_|  |_|\__,_|_|\___/   \__,_|\___\___|\____/|_|  |_|\__,_|_|\__,_|\__|_|\___/|_| |_|  \___/|_|   |_|  |_|\__,_|___/___/
                                                                                                                                                                  
                                                                                                                                                                  
# GenData-HaloData.py - Script to generate halo data from VELOCIraptor & TreeFrog outputs in a given simulation. 
# Author: RUBY WRIGHT 

# File must be edited before use to specity directories of particle, VELOCIraptor and TreeFrog data. 

# PREAMBLE
import warnings
warnings.filterwarnings("ignore")
import numpy as np
import h5py
import time 
import os
import sys
import argparse

sys.path.append('/home/rwright/CHUMM/') # may need to specify
sys.path.append('/Users/ruby/Documents/GitHub/CHUMM/') # may need to specify
from STFTools import *
from AccretionTools import *
from VRPythonTools import *
from GenPythonTools import *
from multiprocessing import Process, cpu_count

# Parameters
extra_halo_fields=['R_rel','N_peers','Subhalo_rank','M_rel','halotype']#*
####################################################

# Parse arguments
parser=argparse.ArgumentParser()
parser.add_argument('-np', type=int, default=1,
                    help='number of processes to use')
parser.add_argument('-gen_bhd', type=int, default=0,
                    help='gen base halo data')
parser.add_argument('-gen_dhd', type=int, default=0,
                    help='gen detailed halo data')
parser.add_argument('-sum_dhd', type=int, default=0,
                    help='sum detailed halo data')
parser.add_argument('-com_dhd', type=int, default=0,
                    help='compress detailed halo data')
parser.add_argument('-add_hpd', type=int, default=0,
                    help='dump halo particle coordinates')


n_processes = parser.parse_args().np
gen_bhd=bool(parser.parse_args().gen_bhd)
gen_dhd=bool(parser.parse_args().gen_dhd)
sum_dhd=bool(parser.parse_args().sum_dhd)
com_dhd=bool(parser.parse_args().com_dhd)
add_hpd=bool(parser.parse_args().add_hpd)

run_name=os.getcwd().split('/')[-1]# takes the run name from the folder
# Decide particle data type from simulation title
if 'EAGLE' in run_name:
    partdata_filetype='EAGLE'
else:
    partdata_filetype='GADGET'

t1=time.time()

############ 1. GENERATE BASE HALO DATA (from STFTools.py) ############ 
# This is run in serial.
# Here we load in and save basic halo data from VELOCIraptor and TreeFrog. 
# File locations and padding of snaps must be updated in here.

if gen_bhd:
    print('Generating file lists...')

    ############ generate p filelist
    pfiles_directory="sim_data/snapshots/"
    pfiles_list_outer=os.listdir(pfiles_directory)
    pfiles_list_outer_trunc=[tempfile for tempfile in pfiles_list_outer if tempfile.startswith('snap')]
    pfiles_list_outer_trunc.sort()
    pfiles_list_wdir=[pfiles_directory+tempfile+'/snap_'+tempfile[-12:]+'.0.hdf5' for tempfile in pfiles_list_outer_trunc]
    print(np.array(pfiles_list_wdir))
    ############ generate vr filelist
    vrfiles_directory="sim_data/velociraptor/"
    vrfiles_list_all=os.listdir(vrfiles_directory)
    vrfiles_list_all.sort()
    vrfiles_list_split=np.unique([vrfiles_directory+tempfile.split('.')[0] for tempfile in vrfiles_list_all if '6dfof' in tempfile])[1:]#remove 0
    print(np.array(vrfiles_list_split))
    ############ generate tf filelist
    tffiles_directory="sim_data/treefrog/"
    tffiles_list_all=os.listdir(tffiles_directory)
    tffiles_list_trunc=[tffiles_directory+tempfile for tempfile in tffiles_list_all if tempfile.startswith(f'{run_name}-tfout.s')]
    tffiles_list_trunc.sort()
    tffiles_list=[tempfile[:-5] for tempfile in tffiles_list_trunc]#remove the .tree
    print(np.array(tffiles_list))
 
    ###########padding the lists
    pfiles_final=[None]*26
    pfiles_final.extend(pfiles_list_wdir)
    vrfiles_final=[None]*5
    vrfiles_final.extend(list(vrfiles_list_split))
    tffiles_final=[None]*5
    tffiles_final.extend(list(tffiles_list))

    print('Generating base halo data ...')
    gen_base_halo_data(partdata_filelist=pfiles_final,partdata_filetype=partdata_filetype,vr_filelist=vrfiles_final,vr_filetype=2,tf_filelist=tffiles_final,outname=run_name,temporal_idval=10**12)
    base_halo_data=open_pickle('B2_HaloData_'+run_name+'.dat')

else:
    base_halo_data=open_pickle('B2_HaloData_'+run_name+'.dat') 

############ 2. GENERATE DETAILED HALO DATA (from STFTools.py) ############ 
# This is run in parallel (multiple processes can do invidual snaps). 
# Here we add to the base halo data snap-wise with detailed fields, as per the parameters above. 

if gen_dhd:
    print('Generating detailed halo data ...')
    snaps=list(range(len(base_halo_data)))#*
    snap_indices=gen_mp_indices(indices=snaps,n=n_processes)

    # kwargs for gen_detailed_halo_data
    kwargs=[{'snaps':iprocess_snap_indices,'vr_halo_fields':None,'extra_halo_fields':extra_halo_fields} for iprocess_snap_indices in snap_indices]
    processes=[]
    if __name__ == '__main__':
        for iprocess in range(len(kwargs)):
            print(f'Starting process {iprocess}')
            p=Process(target=gen_detailed_halo_data, args=(base_halo_data,),kwargs=kwargs[iprocess])
            processes.append(p)
            p.start()
        for p in processes:
            p.join()
        
############ 3. COLLATE HALO DATA (from STFTools.py) ############ 
# This is run in serial.
# Here we simply collate all available detailed halo data from above into one file. 

if sum_dhd:#collate all the data
    print(f'Post-processing detailed halo data ...')
    detailed_halo_data=postprocess_detailed_halo_data(path='halo_data')

############ 4. COMPRESS HALO DATA (from STFTools.py) ############ 
# This is run in serial.
# Here we simply collate all the desired halo data from above into one file. 

if com_dhd:
    print(f'Compressing detailed halo data ...')
    if not sum_dhd:
        detailed_halo_data=open_pickle('B3_HaloData_'+run_name+'.dat')
    compressed_halo_data=compress_detailed_halo_data(detailed_halo_data,fields=None)

############ 5. DUMP HALO/SO PARTICLE COORDINATES (from ParticleTools.py) ############ 
# This is run in parallel.
if add_hpd:

    valid_snaps=np.where([(len(base_halo_data_snap)>5 and not base_halo_data_snap['Part_FilePath']==None) for base_halo_data_snap in base_halo_data])[0]
    snaps_for_mp=gen_mp_indices(indices=valid_snaps,n=n_processes)

    print(f'Dumping structure particle coordinates for snaps {valid_snaps}...')

    # Multiprocessing arguments
    processes=[]
    kwargs=[{'snaps':snaps_for_mp[iprocess],'ifof':True,'iso':True,'add_partdata':True} for iprocess in range(n_processes)]

    if __name__ == '__main__':
        for iprocess in range(len(kwargs)):
            print(f'Starting process {iprocess}')
            p=Process(target=dump_structure_particle_data, args=(base_halo_data,),kwargs=kwargs[iprocess])
            processes.append(p)
            p.start()
        for p in processes:
            p.join()

