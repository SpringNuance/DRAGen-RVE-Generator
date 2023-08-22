#!/bin/bash -l
# Author: Xuan Binh
#SBATCH --job-name=dragen
#SBATCH --error=%j.err
#SBATCH --output=%j.out
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --mem-per-cpu=100G
#SBATCH --time=00:15:00
#SBATCH --partition=test
#SBATCH --account=project_2007935
#SBATCH --mail-type=ALL
#SBATCH --mail-user=binh.nguyen@aalto.fi

cd $PWD

module load python-data/3.8

filename="logging.out"

# Check if the file exists
if [ -f "$filename" ]; then
  # If it does, delete it
  rm "$filename"
  echo "$filename deleted."
fi

# Create a new empty file
touch "$filename"
echo "$filename created."

python -u DRAGen_nogui.py > logging.out