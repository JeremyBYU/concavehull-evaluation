#!/bin/bash
# This script is meant to be executed on UMICH Great Lakes Super Computer Cluster
# It is there to measure timings of the Polylidar Algorithm

#SBATCH --job-name=polylidar_complexity
#SBATCH --mail-type=BEGIN,END
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --mem-per-cpu=24000m 
#SBATCH --time=120:00
#SBATCH --account=test
#SBATCH --partition=standard

# The application(s) to execute along with its input arguments and options:
module load python-anaconda3;
source activate concave;
python ./scripts/complexity_polylidar.py
