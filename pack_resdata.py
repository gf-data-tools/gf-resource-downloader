import zipfile
import os
from pathlib import Path
from urllib import request
os.chdir(Path(__file__).resolve().parent)

f = zipfile.ZipFile('resdata.zip','w')
os.makedirs('./resdata',exist_ok=True)
regions = ['ch','jp','tw','us','kr']
for region in regions:
    url = f'https://github.com/gf-data-tools/gf-data-{region}/raw/main/resdata.json'
    request.urlretrieve(url,f'./resdata/{region}_resdata.json')
    f.write(f'./resdata/{region}_resdata.json',f'{region}_resdata.json',compress_type=zipfile.ZIP_BZIP2)

