# Historic_Energy_Estimate

# STEP 1: Setup Environment
- In command line
- clone repo in a directory you want it
```linux
git clone https://github.com/josephseverino/Historic_Energy_Estimate.git
cd Historic_Energy_Estimate
```
activate environment from YAML(.yml) file
```linux
conda env create -f environment.yml
```
list your environments to ensure you have *energyPipeline*
```linux
conda env list
```
activate environment
```linux
conda activate energyPipeline
```
unzip your network files (Network.zip). You can do this by double clicking on zip file in MacOS. These are too big to be pushed on GitHub

# STEP 2: Pull Historic Data
In command line. Make sure you put your data in YYYY-MM-dd formatas string
```linux
python VolEstScript.py "2020-03-10"
```
This should take roughly 2 hours to complete due to TomTom having to prepare the data.

# STEP 3: Explore Data
go to notebook explore_data.ipynb
```linux
jupyter notebook
```
- See notebook for details
- Notice Energy Data is stored in EnergyData and TomTom original data is stored in it's own folder with a date as the name
