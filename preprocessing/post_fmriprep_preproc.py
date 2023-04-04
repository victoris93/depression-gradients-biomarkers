import nilearn
from nilearn import datasets
import numpy as np
import pandas as pd
import os
import sys
import nibabel as nib
from nilearn import signal
from sklearn.impute import SimpleImputer
from nilearn.maskers import NiftiLabelsMasker

subject = sys.argv[1]

data_path = '/gpfs3/well/margulies/projects/data/MDD_bezmaternykh'
n_parcels = int(sys.argv[2])
group = sys.argv[3]

def impute_nans(dataframe, pick_columns = None):
    imputer = SimpleImputer(strategy='mean')
    if pick_columns is not None and isinstance(pick_columns, (list, np.ndarray)):
        df_no_nans = pd.DataFrame(imputer.fit_transform(dataframe), columns=dataframe.columns)[pick_columns]
    else:
        df_no_nans = pd.DataFrame(imputer.fit_transform(dataframe), columns=dataframe.columns)
    return df_no_nans

def get_confounds(subject, no_nans = True, pick_columns = None, data_dir = data_path, group = group):
    confound_paths = []
    confound_list = []
    subject_dir = os.path.join(data_dir, group,'derivatives', 'fmriprep', f'sub-{subject}', 'func')
    confound_paths = [f for f in os.listdir(subject_dir) if f.endswith('confounds_timeseries.tsv')]
    if no_nans == True:
        for confounds_path in confound_paths:
            confounds = pd.read_csv(f'{subject_dir}/{confounds_path}', sep = '\t')
            confounds = impute_nans(confounds, pick_columns = pick_columns)
            confound_list.append(confounds)
    else:
        for confounds_path in confound_paths:
            confounds = pd.read_csv(f'{subject_dir}/{confounds_path}', sep = '\t')
            confound_list.append(confounds)
    return confound_list

def parcellate(subject_ts_paths, confounds, parcellation = 'schaefer', n_parcels = n_parcels, gsr = False):
    parc_ts_list = []
    if parcellation == 'schaefer':
        atlas = datasets.fetch_atlas_schaefer_2018(n_rois=n_parcels, yeo_networks=7, resolution_mm=1, data_dir='/gpfs3/well/margulies/users/cpy397/nilearn_data', base_url= None, resume=True, verbose=1)
    masker =  NiftiLabelsMasker(labels_img=atlas.maps, standardize=True, memory='nilearn_cache', verbose=5)
    for subject_ts, subject_confounds in zip(subject_ts_paths, confounds):
        if gsr == False:
            parc_ts = masker.fit_transform(subject_ts, confounds = subject_confounds.drop("global_signal", axis = 1))
            parc_ts_list.append(parc_ts)
        else:
            parc_ts = masker.fit_transform(subject_ts, confounds = subject_confounds)
            parc_ts_list.append(parc_ts)
    return parc_ts_list

def clean_signal(parc_ts_list):
    clean_ts = []
    for parc_ts in parc_ts_list:
        clean_ts_s1 = signal.clean(parc_ts, t_r = 2, low_pass=0.08, high_pass=0.01, standardize=True, detrend=True)
        clean_ts.append(clean_ts_s1[10:]) # discarding first 10 volumes
    return clean_ts

def get_ts_paths(subject, data_dir = data_path, group = group):
    subject_dir = os.path.join(data_dir, group,'derivatives', 'fmriprep', f'sub-{subject}', 'func')
    ts_paths = [f'{subject_dir}/{i}' for i in os.listdir(subject_dir) if i.endswith('MNI152NLin2009cAsym_res-2_desc-preproc_bold.nii.gz')] #sub-01_task-rest_space-MNI152NLin2009cAsym_res-2_desc-preproc_bold.nii.gz
    return ts_paths

picked_confounds = np.loadtxt('confounds.txt', dtype = 'str')
confounds = get_confounds(subject, pick_columns = picked_confounds)
subject_ts_paths = get_ts_paths(subject)

parcellated_ts = parcellate(subject_ts_paths, confounds)
clean_parcellated_ts = clean_signal(parcellated_ts)
clean_parcellated_ts = np.row_stack(clean_parcellated_ts)
print('Shape of the timeseries: ', clean_parcellated_ts.shape)

output_dir = f'{data_path}/clean_data/{group}/schaefer{n_parcels}/sub-{subject}/func'
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

for i, ts in enumerate(clean_parcellated_ts):
    np.save(file = f'{output_dir}/sub-{subject}_task-rest_space-MNI152NLin2009cAsym_res-2_schaefer{n_parcels}_desc-clean_bold', arr = ts)