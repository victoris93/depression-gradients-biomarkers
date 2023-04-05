#!/bin/bash 
#SBATCH --job-name=PostFmriprep
#SBATCH -o ./logs/PostFmriprep-%j.out
#SBATCH -p short
#SBATCH --constraint="skl-compat"
#SBATCH --cpus-per-task=2
#SBATCH --array 1-21:1

module load Python/3.9.6-GCCcore-11.2.0
source /well/margulies/users/cpy397/env/ClinicalGrads/bin/activate
### source /well/margulies/users/mnk884/python/corrmats-skylake/bin/activate

echo Executing job ${SLURM_ARRAY_JOB_ID} on `hostname` as user ${USER} 

echo Executing task ${SLURM_ARRAY_TASK_ID} of job ${SLURM_ARRAY_JOB_ID} on `hostname` as user ${USER} 
echo the job id is $SLURM_ARRAY_JOB_ID

group=controls
SUBJECT_LIST=/gpfs3/well/margulies/projects/data/MDD_bezmaternykh/"${group}"/Bezmaternykh_"${group}"_subjects.txt
sub=$(sed -n "${SLURM_ARRAY_TASK_ID}p" $SUBJECT_LIST)
n_parcels=1000

python -u post_fmriprep_preproc.py $sub $n_parcels $group
