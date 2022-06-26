import zipfile
import os
from pathlib import Path
os.chdir(Path(__file__).resolve().parent)

f = zipfile.ZipFile('resdata.zip','w')
data_dir = '../data'
regions = ['ch','jp','tw','us','kr']
for region in regions:
    f.write(os.path.join(data_dir,region,'resdata.json'),f'{region}_resdata.json',compress_type=zipfile.ZIP_BZIP2)

