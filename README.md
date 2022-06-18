# Resource Downloader
A script that can be used to manually download all resource data for GFL.  
It utilized multiprocessing to increase speed, and will auto retry for failed tasks.

## Performance
On my PC the script spent around 5 minutes to download base assets which are required to open the game, 
and about 20 minutes in total to download all assets (including hd resources).
In comparison, I spent 20 minutes downloading the base assets using the game client and encountered 5 crashes in total.

## Usage
Probably due to the use of multiprocessing, I failed to pack this using pyinstaller. So a python environment is required.  
Run `pip install -r requirements.txt` to install all requirements, and then simply run `python downloader.py`.
All settings are stored in `config.json5`.