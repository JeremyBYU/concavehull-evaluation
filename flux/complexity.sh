#!/bin/bash
# The interpreter used to execute the script

#“#SBATCH” directives that convey submission options:

#SBATCH --job-name=polylidar_complexity
#SBATCH --mail-type=BEGIN,END
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --mem-per-cpu=8000m 
#SBATCH --time=10:00
#SBATCH --account=jdcasta
#SBATCH --partition=standard

# The application(s) to execute along with its input arguments and options:
module load python-anaconda3;
source activate concave;
python ./scripts/complexity_polylidar.py
