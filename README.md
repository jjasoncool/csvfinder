# Conda
## rebuild the conda env
- First, change to the project path
- `conda env create -p ./env -f environment.yml`

## Using conda command line
- `conda activate ./env`
- `python main.py`

## Add package
- `conda install [package_name]`
- `conda install -c conda-forge [package_name]`

## Update dependency
- `conda update --all`

## Remove the env
- `conda env remove -p ./env -y`

## Backup the env info
- `conda env export -p ./env > environment.yml`

# Pyinstaller
## generate main.spec (manual stop)
- `pyinstaller --onefile main.py`
## build executable file
- `pyinstaller main.spec --clean`
