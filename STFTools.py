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
                                                                                                                                                                  
                                                                                                                                                                  
# STFTools.py - Python routines to read and process VELOCIraptor (Elahi+19) and TreeFrog (Elahi+19) outputs. 
# Author: RUBY WRIGHT 

# PREAMBLE
import os
import numpy as np
import h5py
import pickle
import astropy.units as u
import time
from astropy.cosmology import FlatLambdaCDM,z_at_value
from os import path

# VELOCIraptor python tools etc
from VRPythonTools import *
from GenPythonTools import *

########################### CREATE BASE HALO DATA ###########################

def gen_base_halo_data(partdata_filelist,partdata_filetype,vr_filelist,vr_filetype,tf_filelist,outname='',temporal_idval=10**12):
    
    """

    gen_base_halo_data : function
	----------

    Generate halo data from velociraptor property and particle files.

	Parameters
	----------

    outname : str
        Suffix for output file. 

    partdata_filelist : list of str
        List of the particle data file paths. None if if we don't have data for a certain isnap.
        This file needs to be PADDED with None to be of the same length as the actual snaps. 

    partdata_filetype : str
        Type of particle data we are using. 
        One of "EAGLE", "GADGET", "SWIFT" (so far)

    vr_filelist : list of str
        List of the velociraptor data file paths. None if if we don't have data for a certain isnap.
        This file needs to be PADDED with None to be of the same length as the actual snaps. 

    vr_filetype : int
        The filetype of the VELOCIraptor inputs: (2 = hdf5)

    tf_filelist : list of str
        List of the treefrog data file paths. None if if we don't have data for a certain isnap.
        This file needs to be PADDED with None to be of the same length as the actual snaps. 

    temporal_idval : int
        The multiplier used by TreeFrog to create unique temporal halo IDs. 

    Returns
	-------
    base_halo_data: list of dicts...
        A list (for each snap desired) of dictionaries which contain halo data with the following fields:
        'ID'
        'hostHaloID'
        'Snap'
        'Head'*
        'Tail'
        'HeadSnap'*
        'TailSnap'*
        'RootHead'*
        'RootTail'*
        'RootHeadSnap'*
        'RootTailSnap'*
        'HeadRank'*
        'Num_descen'*
        'Num_progen'*
        'SimulationInfo'
            'h_val'
            'Hubble_unit'
            'Omega_Lambda'
            'ScaleFactor'
            'z'
            'LookbackTime'
        'UnitInfo'
        'VR_FilePath'
        'VR_FileType'
        'Part_FilePath'
        'Part_FileType'
        'outname'

    * items will be removed from V1 file
    
    Will save to file at: 
    B1_HaloData_outname.dat 
    B2_HaloData_outname.dat 

	"""

    base_fields=['ID','hostHaloID','Structuretype',"numSubStruct"]#default halo fields

    # File lists
    part_list=partdata_filelist#particle data filepaths -- padded with None for snaps we don't have
    vr_list=vr_filelist#velociraptor data filepaths -- padded with None for snaps we don't have
    tf_list=tf_filelist#treefrog data filepaths -- padded with None for snaps we don't have

    # Get snapshot indices from number of particle data files 
    sim_snaps=list(range(len(part_list)))
    halo_data_all=[]#initialise halo data list
    have_halo_data=[]#initialise flag list indicating existence of halo data at given snaps
    
    print('Reading halo data using VR python tools ...')
    for snap in sim_snaps:
        try:#attempt to find vr file from file list -if passes test, continues
            vr_list[snap].startswith('/')
            print(f'Searching for halo data at snap {snap} ...')
            print(f'[File: {vr_list[snap]}]')
        except:#if can't find vr file, skip this iteration and save empty halo data 
            have_halo_data.append(False)
            print(f'No halo data for snap {snap} (not given a file)')
            continue
           
        #use VR python tools to load in halo data for this snap
        halo_data_snap=ReadPropertyFile(vr_list[snap],ibinary=vr_filetype,iseparatesubfiles=0,iverbose=0, desiredfields=base_fields, isiminfo=True, iunitinfo=True)
        halo_data_snap[0]["Snap"]=snap
        #if data is found
        if not halo_data_snap==[]:
            halo_data_all.append(halo_data_snap)#will be length n_valid_snaps
            have_halo_data.append(True)#will be length n_ALL_snaps

        #if data is not found
        else:
            print("Couldn't find velociraptor files for snap = ",snap)
            return []#exit program if can't find vr files

    # List of number of halos detected for each snap and list isolated data dictionary for each snap (in dictionaries)
    halo_data_counts=[item[1] for item in halo_data_all]#will be length n_valid_snaps
    halo_data_all=[item[0] for item in halo_data_all]#will be length n_valid_snaps

    # Use TreeFrog IDs and convert hostHaloIDs if we don't have the temporal IDval integrated
    for isnap,item in enumerate(halo_data_all):#for the valid snaps
        halo_data_all[isnap]['Count']=halo_data_counts[isnap]#n_halos at this snap
        snap=halo_data_all[isnap]['Snap']
        try:
            if item["ID"][0]<temporal_idval:#if the first ID is less than the temporal IDval then do the conversion
                #read in IDs from TreeFrog
                treefile_compressed_isnap=tf_filelist[snap]+'.tree'
                treefile_isnap=h5py.File(treefile_compressed_isnap,'r+')
                treefile_ids=treefile_isnap["/ID"].value
                halo_data_all[isnap]["ID"]=treefile_ids
                treefile_isnap.close()
            if item["hostHaloID"][0]<temporal_idval:#if the first hostHaloID is less than the temporal IDval then do the conversion
                #read in IDs from TreeFrog
                for ihalo,hosthaloid in enumerate(halo_data_all[isnap]["hostHaloID"]):
                    if hosthaloid<0:
                        halo_data_all[isnap]["hostHaloID"][ihalo]=-1
                    else:
                        halo_data_all[isnap]["hostHaloID"][ihalo]=np.int64(isnap*temporal_idval)+hosthaloid
        except:
            pass

    # We have halo data, now load the trees
    # Import tree data from TreeFrog, build temporal head/tails from descendants -- adds to halo_data_all (all halo data)
    print('Now assembling descendent tree using VR python tools')
    tf_filelist=np.compress(have_halo_data,tf_filelist)#compressing the TreeFrog filelist to valid snaps only 
    snap_no=len(tf_filelist)
    np.savetxt('tf_filelist_compressed.txt',tf_filelist,fmt='%s')
    tf_filelist="tf_filelist_compressed.txt"

    # Read in tree data
    halo_tree=ReadHaloMergerTreeDescendant(tf_filelist,ibinary=vr_filetype,iverbose=1,imerit=True,inpart=False)

    # Now build trees and add onto halo data array (for the valid, unpadded snaps)
    BuildTemporalHeadTailDescendant(snap_no,halo_tree,halo_data_counts,halo_data_all,iverbose=1,TEMPORALHALOIDVAL=temporal_idval)
    
    print('Finished assembling descendent tree using VR python tools')
    print('Adding timesteps & filepath information')
    
    # Adding timesteps and filepath information
    first_true_index=np.where(have_halo_data)[0][0]#finding first valid snap index to extract simulation data 
    H0=halo_data_all[first_true_index]['SimulationInfo']['h_val']*halo_data_all[first_true_index]['SimulationInfo']['Hubble_unit']#extract hubble constant
    Om0=halo_data_all[first_true_index]['SimulationInfo']['Omega_Lambda']#extract omega_lambda
    cosmo=FlatLambdaCDM(H0=H0,Om0=Om0)

    # Now tidy up and add extra details for output. 
    halo_data_output=[]
    isnap=-1
    for snap in sim_snaps:#for valid snaps, return the halo data dictionary and extra information
        if have_halo_data[snap]:
            isnap=isnap+1
            scale_factor=halo_data_all[isnap]['SimulationInfo']['ScaleFactor']
            redshift=z_at_value(cosmo.scale_factor,scale_factor,zmin=-0.5)
            lookback_time=cosmo.lookback_time(redshift).value
            halo_data_all[isnap]['SimulationInfo']['z']=redshift
            halo_data_all[isnap]['SimulationInfo']['LookbackTime']=lookback_time
            halo_data_all[isnap]['VR_FilePath']=vr_list[snap]
            halo_data_all[isnap]['VR_FileType']=vr_filetype
            halo_data_all[isnap]['Part_FilePath']=part_list[snap]
            halo_data_all[isnap]['Part_FileType']=partdata_filetype
            halo_data_all[isnap]['outname']=outname
            halo_data_all[isnap]['Snap']=snap
            halo_data_all[isnap]['SimulationInfo']['BoxSize_Comoving']=halo_data_all[isnap]['SimulationInfo']['Period']/scale_factor
            halo_data_output.append(halo_data_all[isnap])
        else:
            halo_data_output.append({'Snap':snap,'Part_FilePath':part_list[snap],'Part_FileType':partdata_filetype})#for padded snaps, return particle data and snapshot 

    # Now save all the data (with detailed TreeFrog fields) as "B2"
    print('Saving B2 halo data to file (contains detailed TreeFrog data)')
    if path.exists('B2_HaloData_'+outname+'.dat'):
        print('Overwriting existing V2 halo data ...')
        os.remove('B2_HaloData_'+outname+'.dat')
    with open('B2_HaloData_'+outname+'.dat', 'wb') as halo_data_file:
        pickle.dump(halo_data_output, halo_data_file)
        halo_data_file.close()

    # Now save all the data (with detailed TreeFrog fields removed) as "B1" (saves memory for accretion calculations)
    fields_to_keep=['Count','Snap','Structuretype','numSubStruct','ID','hostHaloID','Tail','Head','VR_FilePath','VR_FileType','Part_FilePath','Part_FileType','UnitInfo','SimulationInfo','outname']
    halo_data_all_truncated=[]
    for snap,halo_data_snap in enumerate(halo_data_output):
        if have_halo_data[snap]:
            halo_data_all_truncated_snap={}
            for field in fields_to_keep:
                halo_data_all_truncated_snap[field]=halo_data_snap[field]
        else:
            halo_data_all_truncated_snap={'Snap':snap,'Part_FilePath':part_list[snap],'Part_FileType':partdata_filetype}
        halo_data_all_truncated.append(halo_data_all_truncated_snap)

    print('Saving B1 halo data to file (removing detailed TreeFrog data)')
    if path.exists('B1_HaloData_'+outname+'.dat'):
        print('Overwriting existing V1 halo data ...')
        os.remove('B1_HaloData_'+outname+'.dat')
    with open('B1_HaloData_'+outname+'.dat', 'wb') as halo_data_file:
        pickle.dump(halo_data_all_truncated, halo_data_file)
        halo_data_file.close()
    print('Done generating base halo data')

    return halo_data_output #returns the B2 version

########################### ADD DETAILED HALO DATA ###########################

def gen_detailed_halo_data(base_halo_data,snap_indices,vr_halo_fields=None,outname=None,extra_halo_fields=[]):
    
    """
    
    gen_detailed_halo_data : function
	----------

    Add detailed halo data to base halo data from property files.

    Parameters
    ----------

    base_halo_data_snap : list of dicts

        Dictionary for a snap containing basic halo data generated from gen_base_halo_data. 

    vr_halo_fields : list of str

        List of dictionary keys for halo properties (from velociraptor) to be added to the base halo data. 

    extra_halo_fields : list of str

        List of keys to add to halo data. Currently just supports 'R_rel', 'N_Peers', 'Subhalo_rank'

    Returns
    --------

    V3_HaloData_outname_snap.dat : list of dict

    A list (for each snap desired) of dictionaries which contain halo data with the following fields:
        'ID'
        'hostHaloID'
        'Snap'
        'Head'
        'Tail'

        'SimulationInfo'
            'h_val'
            'Hubble_unit'
            'Omega_Lambda'
            'ScaleFactor'
            'z'
            'LookbackTime'

        'UnitInfo'
        'VR_FilePath'
        'VR_FileType'
        'Part_FilePath'
        'Part_FileType'

        AND ANY EXTRAS from vr_property_fields

	"""
    t1=time.time()
    if not os.path.exists('job_logs'):
        os.mkdir('job_logs')

    isnaps=snap_indices['indices']
    iprocess=snap_indices['iprocess']
    print(f'iprocess {iprocess} has snaps {isnaps}')

    for isnap in isnaps:
        base_halo_data_snap=base_halo_data[snap]
        snap=base_halo_data_snap["Snap"]
        fname_log=f"job_logs/halodata_progress_{str(snap).zfill(3)}.log"

        if os.path.exists(fname_log):
            os.remove(fname_log)
        
        if not os.path.exists('halo_data'):
            os.mkdir('halo_data')

        try:
            outfilename='halo_data/B3_HaloData_'+base_halo_data_snap['outname']+f'_{str(snap).zfill(3)}.dat'
        except:
            if outname==None:
                outname=''
            outfilename='halo_data/B3_HaloData_'+outname+f'_{str(snap).zfill(3)}.dat'


        # If we're not given vr halo fields, find all of the available data fields
        if vr_halo_fields==None:
            try:
                print('Grabbing detailed halo data for snap',snap)
                property_filename=base_halo_data_snap['VR_FilePath']+".properties.0"
                property_file=h5py.File(property_filename)
                all_props=list(property_file.keys())
                vr_halo_fields=all_props
                if path.exists(outfilename):
                    print('Will overwrite existing B3 halo data ...')
                    os.remove(outfilename)
            except:
                print(f'Skipping padded snap ',snap)
                new_halo_data_snap=base_halo_data_snap
                dump_pickle(data=new_halo_data_snap, path=outfilename)
                return new_halo_data_snap
        
                
        print('Adding the following fields from properties file:')
        print(np.array(vr_halo_fields))

        base_fields=list(base_halo_data_snap.keys())
        fields_needed_from_prop=np.compress(np.logical_not(np.in1d(vr_halo_fields,base_fields)),vr_halo_fields)

        print('Will also collect the following fields from base halo data:')
        print(np.array(base_fields))

        # Loop through each snap and add the extra fields
        t1=time.time()    
        n_halos_snap=len(base_halo_data_snap['ID'])#number of halos at this snap

        # Read new halo data
        print(f'Adding detailed halo data for snap ',snap,' where there are ',n_halos_snap,' halos')
        new_halo_data_snap=ReadPropertyFile(base_halo_data_snap['VR_FilePath'],ibinary=base_halo_data_snap["VR_FileType"],iseparatesubfiles=0,iverbose=0, desiredfields=fields_needed_from_prop, isiminfo=True, iunitinfo=True)[0]

        for new_field in list(new_halo_data_snap.keys()):
            if ('ass_' in new_field or 'M_' in new_field) and 'R_' not in new_field and 'rhalfmass' not in new_field:
                print(f'Converting {new_field} values to physical')
                new_halo_data_snap[new_field]=new_halo_data_snap[new_field]*10**10/base_halo_data_snap['SimulationInfo']['h_val']

        # Adding old halo data from V1 calcs
        print(f'Adding fields from base halo data')
        for field in base_fields:
            new_halo_data_snap[field]=base_halo_data_snap[field]
        print('Done adding base fields')
                
        # Add extra halo fields -- post-process velociraptor files   
        if n_halos_snap>0:
            if 'R_rel' in extra_halo_fields: #Relative radius to host
                print('Adding R_rel information for subhalos')
                new_halo_data_snap['R_rel']=np.zeros(n_halos_snap)+np.nan #initialise to nan if field halo
                for ihalo in range(n_halos_snap):
                    hostID_temp=new_halo_data_snap['hostHaloID'][ihalo]
                    if not hostID_temp==-1:
                        #if we have a subhalo 
                        hostindex_temp=np.where(new_halo_data_snap['ID']==hostID_temp)[0][0]
                        host_radius=new_halo_data_snap['R_200crit'][hostindex_temp]
                        host_xyz=np.array([new_halo_data_snap['Xc'][hostindex_temp],new_halo_data_snap['Yc'][hostindex_temp],new_halo_data_snap['Zc'][hostindex_temp]])
                        sub_xy=np.array([new_halo_data_snap['Xc'][ihalo],new_halo_data_snap['Yc'][ihalo],new_halo_data_snap['Zc'][ihalo]])
                        group_centric_r=np.sqrt(np.sum((host_xyz-sub_xy)**2))
                        r_rel_temp=group_centric_r/host_radius
                        new_halo_data_snap['R_rel'][ihalo]=r_rel_temp
                print('Done with R_rel')

            if 'N_peers' in extra_halo_fields: #Number of peer subhalos
                print('Adding N_peers information for subhalos')
                new_halo_data_snap['N_peers']=np.zeros(len(new_halo_data_snap['ID']))+np.nan #initialise to nan if field halo
                for ihalo in range(n_halos_snap):
                    hostID_temp=new_halo_data_snap['hostHaloID'][ihalo]
                    if not hostID_temp==-1:
                        #if we have a subhalo
                        N_peers=np.sum(new_halo_data_snap['hostHaloID']==hostID_temp)-1
                        new_halo_data_snap['N_peers'][ihalo]=N_peers           
                print('Done with N_peers')

            if 'Subhalo_rank' in extra_halo_fields:# mass ordered rank for subhalos in a group/cluster
                print('Adding Subhalo_rank information for subhalos')
                new_halo_data_snap['Subhalo_rank']=np.zeros(len(new_halo_data_snap['ID']))+np.nan
                processed_hostIDs=[]
                for ihalo in range(n_halos_snap):
                    hostID_temp=new_halo_data_snap['hostHaloID'][ihalo]
                    #if we have a subhalo
                    if not hostID_temp==-1:
                        if hostID_temp not in processed_hostIDs:
                            processed_hostIDs.append(hostID_temp)
                            mass=new_halo_data_snap['Mass_200crit'][ihalo]
                            peer_indices=np.where(new_halo_data_snap['hostHaloID']==hostID_temp)[0]
                            peer_ranks=rank_list([new_halo_data_snap['Mass_200crit'][ihalo_peer] for ihalo_peer in peer_indices])
                            for ipeer_index,peer_index in enumerate(peer_indices):
                                new_halo_data_snap["Subhalo_rank"][peer_index]=peer_ranks[ipeer_index]
                print('Done with Subhalo_rank')

        else: #if insufficient halos at snap
            print('Skipping adding the extra halo fields for this snap (insufficient halo count)')

        t2=time.time()

        with open(fname_log,"a") as progress_file:
            progress_file.write(f"Done with snap {snap}: num halos = {len(base_halo_data_snap['ID'])} ({np.sum(base_halo_data_snap['hostHaloID']>0)} subhalos), took {t2-t1:.2f} sec \n")
            progress_file.close()

        # Save data to file
        print('Saving full halo data to file ...')
        dump_pickle(data=new_halo_data_snap, path=outfilename)
        return new_halo_data_snap

def postprocess_detailed_halo_data(path=None):

    if path==None:
        path='halo_data/'
    
    if not path.endswith('/')
        path=path+'/'
    
    halo_data_files=sorted(os.listdir(path))
    halo_data_files_wdir=[path+halo_data_file for halo_data_file in halo_data_files]
    outfilename=halo_data_files[-1][:-7]+'.dat'
    print('Will save to: ',outfilename)
    print(f'Number of halo data snaps: {len(halo_data_files_wdir)}')
    
    full_halo_data=[[] for i in range(len(halo_data_files_wdir))]
    for isnap,halo_data_file in enumerate(halo_data_files_wdir):
        print(f'Adding data for isnap {isnap}')
        halo_data_snap=open_pickle(halo_data_file)
        full_halo_data[isnap]=halo_data_snap
        
    dump_pickle(data=full_halo_data,path=outfilename)
    return full_halo_data

########################### COMPRESS DETAILED HALO DATA ###########################

def compress_halo_data(detailed_halo_data,fields=[]):
        
    """
    
    compress_halo_data : function
	----------

    Compress halo data list of dicts for desired fields. 

    Parameters
    ----------

    detailed_halo_data : list of dicts

        List (for each snap) of dictionaries containing full halo data generated from gen_detailed_halo_data. 

    fields : list of str

        List of dictionary keys for halo properties (from velociraptor) to be saved to the compressed halo data. 

    Returns
    --------

    B4_HaloData_outname.dat : list of dict

    A list (for each snap desired) of dictionaries which contain halo data with the desired fields, which by default will always contain:
        'ID'
        'hostHaloID'
        'Snap'
        'Head'
        'Tail'
        'SimulationInfo'
            'h_val'
            'Hubble_unit'
            'Omega_Lambda'
            'ScaleFactor'
            'z'
            'LookbackTime'
        'UnitInfo'
        'VR_FilePath'
        'VR_FileType'
        'Part_FilePath'
        'Part_FileType'
        'outname'
        
        And any extras -- defaults:
        "Mass_tot"
        "Mass_gas"
        "Mass_200crit"
        "Mass_200mean"
        "Npart"
        
        """

    #process fields to include defaults + those desired
    default_fields=['ID',
    'hostHaloID',
    'Snap',
    'Head',
    'Tail',
    'SimulationInfo',
    'UnitInfo',
    'outname',
    "Mass_tot",
    "M_gas",
    "Mass_200crit",
    "Mass_200mean",
    "N_part"]

    fields_compound=np.unique(flatten([default_fields,fields]))
    fields=fields_compound

    no_snaps=len(detailed_halo_data)
    snap_mask=[len(detailed_halo_data_snap)>5 for detailed_halo_data_snap in detailed_halo_data]

    output_halo_data=[{field:[] for field in fields} for isnap in range(no_snaps)]
    outname=detailed_halo_data[-1]['outname']

    for snap, detailed_halo_data_snap in enumerate(detailed_halo_data):
        if snap_mask[snap]:
            print(f'Processing halo data for snap {snap} ({outname}) ...')
            for field in fields:
                print(f'Field: {field}')
                try:
                    output_halo_data[snap][field]=detailed_halo_data_snap[field]
                except:
                    pass
        else:
            output_halo_data[snap]=detailed_halo_data_snap
    
    file_outname='EAGLE_L25N376-'+outname.split('-')[-1]+f'/B4_HaloData_{outname}.dat'
    if os.path.exists(file_outname):
        os.remove(file_outname)
    dump_pickle(path=file_outname,data=output_halo_data)
    return output_halo_data

########################### RETRIEVE PARTICLE LISTS ###########################

def get_particle_lists(base_halo_data_snap,halo_index_list=None,include_unbound=True,add_subparts_to_fofs=False):
    
    """

    get_particle_lists : function
	----------

    Retrieve the particle lists for each halo for the provided halo data dictionary 
    (and corresponding snapshot) from velociraptor.

	Parameters
    ----------

    base_halo_data_snap : dictionary
        The halo data dictionary for the relevant snapshot.

    add_subparts_to_fof : bool
        Flag as to whether to add subhalo particles to their fof halos.

    Returns
    ----------
    part_data_temp : dictionary 
        The particle IDs, Types, and counts for the given snapshot in a dictionary
        Keys: 
            "Particle_IDs" - list (for each halo) of lists of particle IDs
            "Particle_Types" - list (for each halo) of lists of particle Types
            "Npart" - list (for each halo) of the number of particles belonging to the object

	"""

    snap=int(base_halo_data_snap["Snap"])#grabs snap from the halo data dictionary

    print('Reading halo particle lists for snap = ',snap)
    halo_index_list_for_load=list(range(len(base_halo_data_snap["hostHaloID"])))#always need to load all particle lists (in case we need to add subparticles)

    # Use VR python tools to grab particle data
    try:
        part_data_temp=ReadParticleDataFile(base_halo_data_snap['VR_FilePath'],halo_index_list=halo_index_list_for_load,ibinary=base_halo_data_snap['VR_FileType'],iverbose=0,iparttypes=1,unbound=include_unbound)
    
        if part_data_temp==[]:
            part_data_temp={"Npart":[],"Npart_unbound":[],'Particle_IDs':[],'Particle_Types':[]}
            print('Particle data not found for snap = ',snap)
            return part_data_temp

    except: #if we can't load particle data
        print('Particle data not included in hdf5 file for snap = ',snap)
        part_data_temp={"Npart":[],"Npart_unbound":[],'Particle_IDs':[],'Particle_Types':[]}
        return part_data_temp
    
    # Now (if desired) add particles from substructure to field halos (only do this for field halos)
    if add_subparts_to_fofs:
        print('Appending FOF particle lists with substructure')
        field_halo_indices_temp=np.where(base_halo_data_snap['hostHaloID']==-1)[0]#find field/fof halos
        for i_field_halo,field_halo_ID in enumerate(base_halo_data_snap['ID'][field_halo_indices_temp]):#go through each field halo
            sub_halos_temp=(np.where(base_halo_data_snap['hostHaloID']==field_halo_ID)[0])#find the indices of its subhalos
            if len(sub_halos_temp)>0:#where there is substructure
                field_halo_temp_index=field_halo_indices_temp[i_field_halo]
                field_halo_plist=part_data_temp['Particle_IDs'][field_halo_temp_index]
                field_halo_tlist=part_data_temp['Particle_Types'][field_halo_temp_index]
                sub_halos_plist=np.concatenate([part_data_temp['Particle_IDs'][isub] for isub in sub_halos_temp])#list all particles IDs in substructure
                sub_halos_tlist=np.concatenate([part_data_temp['Particle_Types'][isub] for isub in sub_halos_temp])#list all particles types substructure
                part_data_temp['Particle_IDs'][field_halo_temp_index]=np.concatenate([field_halo_plist,sub_halos_plist])#add particles to field halo particle list
                part_data_temp['Particle_Types'][field_halo_temp_index]=np.concatenate([field_halo_tlist,sub_halos_tlist])#add particles to field halo particle list
                part_data_temp['Npart'][field_halo_temp_index]=len(part_data_temp['Particle_IDs'][field_halo_temp_index])#update Npart for each field halo
        print('Finished appending FOF particle lists with substructure')

    # Output just the halo_index_list halos (to save memory)
    if halo_index_list==None:
        return part_data_temp#if not provided - just return all halo data 
    else: 
        truncated_IDs=[]
        truncated_Types=[]
        truncated_Npart=[]
        for ihalo in halo_index_list:#add particle data for each halo in halo_index_list
            if ihalo>-1:#if valid halo index
                truncated_IDs.append(part_data_temp["Particle_IDs"][int(ihalo)])
                truncated_Types.append(part_data_temp["Particle_Types"][int(ihalo)])
                truncated_Npart.append(part_data_temp["Npart"][int(ihalo)])
            else:#if not valid, add a np.nan
                truncated_IDs.append(np.nan)
                truncated_Types.append(np.nan)
                truncated_Npart.append(np.nan)
        part_data_temp_truncated={"Particle_IDs":truncated_IDs,"Particle_Types":truncated_Types,"Npart":truncated_Npart}

        return part_data_temp_truncated

########################### FIND PROGENITOR AT DEPTH ###########################

def find_progen_index(base_halo_data,index2,snap2,depth): ### given halo index2 at snap 2, find progenitor index at snap1=snap2-depth
    
 
    """

    find_progen_index : function
	----------

    Find the index of the best matching progenitor halo at the previous snap. 

	Parameters
    ----------

    base_halo_data : dictionary
        The halo data dictionary for the relevant snapshot.

    index2 : int
        The index of the halo at the current (accretion) snap. 

    snap2 : int
        The snapshot index of the current (accretion) snap.
    
    depth : int
        The number of snapshots for which to scroll back. 

    Returns
    ----------
    index1 : int
        The index of the best matched halo at the desired snap. 

	"""

    padding=np.sum([len(base_halo_data[isnap])<5 for isnap in range(len(base_halo_data))])
    index_idepth=index2
    for idepth in range(depth):
        current_ID=base_halo_data[snap2-idepth]["ID"][index_idepth]
        tail_ID=base_halo_data[snap2-idepth]["Tail"][index_idepth]
        index_idepth=np.where(base_halo_data[snap2-idepth-1]["ID"]==tail_ID)[0]
        if len(index_idepth)==0:
            index_idepth=np.nan
            break
        else:
            index_idepth=index_idepth[0]
            if idepth==depth-1:
                return index_idepth
    return index_idepth

########################### FIND DESCENDANT AT DEPTH ###########################

def find_descen_index(base_halo_data,index2,snap2,depth): ### given halo index2 at snap 2, find descendant index at snap3=snap2+depth
    
    """

    find_descen_index : function
	----------

    Find the index of the best matching descendent halo at the following snap. 

	Parameters
    ----------

    base_halo_data : dictionary
        The halo data dictionary for the relevant snapshot.

    index2 : int
        The index of the halo at the current (accretion) snap. 

    snap2 : int
        The snapshot index of the current (accretion) snap.
    
    depth : int
        The number of snapshots for which to scroll forward. 

    Returns
    ----------
    index3 : int
        The index of the best matched halo at the desired snap. 

	"""

    padding=np.sum([len(base_halo_data[isnap])<5 for isnap in range(len(base_halo_data))])
    index_idepth=index2
    for idepth in range(depth):
        current_ID=base_halo_data[snap2+idepth]["ID"][index_idepth]
        head_ID=base_halo_data[snap2+idepth]["Head"][index_idepth]
        index_idepth=np.where(base_halo_data[snap2+idepth+1]["ID"]==head_ID)[0]
        if len(index_idepth)==0:
            index_idepth=np.nan
            break
        else:
            index_idepth=index_idepth[0]
            if idepth==depth-1:
                return index_idepth
    return index_idepth

