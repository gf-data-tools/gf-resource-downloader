import pyjson5
import os
from urllib import request
import logging
import socket
from socket import timeout
from multiprocessing import Pool,freeze_support
from tqdm import tqdm
from pathlib import Path
import zipfile
from urllib.error import URLError
os.chdir(Path(__file__).resolve().parent)

with open('config.json5',encoding='utf-8') as f:
    config = pyjson5.load(f)

logger = logging.getLogger()
fh = logging.FileHandler('downloader.log')
fh.setLevel(config['log_level'])
fh.setFormatter(logging.Formatter('%(asctime)s %(levelname)s: %(message)s'))
logger.addHandler(fh)
sh = logging.StreamHandler()
sh.setLevel('WARNING')
sh.setFormatter(logging.Formatter('%(asctime)s %(levelname)s: %(message)s'))
logger.addHandler(sh)
logger.setLevel('DEBUG')

MAX_RETRY=config['max_retry']

socket.setdefaulttimeout(int(config['timeout']))

def download(url, path):
    fname = os.path.split(path)[-1]
    logger.info(f'Start downloading {fname}')
    for i in range(MAX_RETRY):
        try:
            if not os.path.exists(path):
                request.urlretrieve(url,path+'.tmp')
                os.rename(path+'.tmp',path)
        except (URLError, timeout):
            logger.warning(f'Failed to download {fname} for {i+1}/10 tries')
            continue
        else:
            logger.info(f'Successfully downloaded {fname}')
            break
    else:
        logger.error(f'Exceeded max retry times, failed to download {fname} from {url}')
    return path

def star_download(x):
    return download(*x)

def multiprocess_download(tasks, processes=16):
    pool = Pool(processes=processes)
    for _ in tqdm(pool.imap_unordered(star_download, tasks),total=len(tasks)): 
        pass

if __name__=='__main__':
    freeze_support()
    out_dir = config['destination']
    os.makedirs(out_dir,exist_ok=True)
    resdata_url = config['resdata_url']
    if config['download_resdata'] is True:
        print('Downloading compressed resdata from github')
        logger.info('Downloading compressed resdata from github')
        download(resdata_url, './resdata.zip')
    elif not os.path.exists('./resdata.zip'):
        raise FileNotFoundError(f'./resdata.zip does not exist, you should download it from {resdata_url} or set download_resdata to true in config')
    else:
        logging.warning('Using local resdata.zip, please ensure that it is up-to-date')
    data = zipfile.ZipFile('resdata.zip').read(f'{config["region"]}_resdata.json')
    res_data = pyjson5.loads(data.decode('utf-8'))
    resurl = res_data['resUrl']

    tasks = []
    selected_id = []
    selected_id += [0] if config['download_base_assets'] else []
    selected_id += [1] if config['download_add_assets'] else []
    selected_id += [2] if config['download_passivity_assets'] else []
    ab_keys = ['BaseAssetBundles', 'AddAssetBundles', 'passivityAssetBundles']

    print('Collecting resource urls')
    logger.info('Collecting resource urls')
    for d in selected_id:
        key = ab_keys[d]
        for bundle in res_data[key]:
            resname = bundle['resname']+'.ab'
            size = bundle['sizeOriginal']
            res_path = os.path.join(out_dir,resname)
            if os.path.exists(res_path):
                if os.path.getsize(res_path) == size:
                    logger.info(f'File {resname} already exists, thus will be skipped')
                    continue
                else:
                    os.remove(res_path)
            tasks.append((resurl+resname,res_path))

    for bundle in res_data['bytesData']:
        if bundle['fileInABC'] in selected_id:
            resname = bundle['resname']+'.dat'
            size = bundle['sizeCompress']
            res_path = os.path.join(out_dir,resname)
            if os.path.exists(res_path):
                if os.path.getsize(res_path) == size:
                    logger.info(f'File {resname} already exists, thus will be skipped')
                    continue
                else:
                    os.remove(res_path)
            tasks.append((resurl+resname,res_path))

    print('Start downloading')
    logger.info('Start downloading')
    multiprocess_download(tasks,config['processes'])