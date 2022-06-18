import json
import os
from urllib import request
import logging
import socket
from multiprocessing import Pool
from tqdm import tqdm

socket.setdefaulttimeout(30)

logger = logging.getLogger()
logger.setLevel('WARNING')
logger.addHandler(logging.StreamHandler())

def download(url, path):
    fname = os.path.split(path)[-1]
    logger.info(f'Start downloading {fname}')
    for i in range(10):
        try:
            if not os.path.exists(path):
                request.urlretrieve(url,path+'.tmp')
                os.rename(path+'.tmp',path)
        except:
            logger.warning(f'Failed to download {fname} for {i+1}/10 tries')
            continue
        else:
            logger.info(f'Successfully downloaded {fname}')
            break
    else:
        logger.error(f'Exceeded max retry times, failed to download {fname} from {url}')
    return path

def download_multitask(x):
    return download(*x)


if __name__=="__main__":
    out_dir = r"C:\Users\ZeroRin\Nox_share\Download\New"
    region = 'ch'
    os.makedirs(out_dir,exist_ok=True)
    resdata_url = f'https://raw.githubusercontent.com/ZeroRin/gfl-data-miner-python/main/data/{region}/resdata.json'
    resdata_path = os.path.join(out_dir,'resdata.json')
    print('Fetching resdata from github')
    download(resdata_url, resdata_path)

    with open(resdata_path,'r',encoding='utf-8') as f:
        res_data = json.load(f)
    resurl = res_data['resUrl']

    tasks = []
    for bundle in res_data['BaseAssetBundles']:
        resname = bundle['resname']+'.ab'
        size = bundle['sizeOriginal']
        res_path = os.path.join(out_dir,resname)
        if os.path.exists(res_path):
            if os.path.getsize(res_path) == size:
                logger.info(f'File {resname} already exists, thus will be skipped')
                continue
            else:
                os.remove(res_path)
        logger.info(f'Downloading {resname}')
        tasks.append((resurl+resname,res_path))

    for bundle in res_data['bytesData']:
        if bundle['fileInABC']==0:
            resname = bundle['resname']+'.dat'
            size = bundle['sizeOriginal']
            res_path = os.path.join(out_dir,resname)
            if os.path.exists(res_path):
                if os.path.getsize(res_path) == size:
                    logger.info(f'File {resname} already exists, thus will be skipped')
                    continue
                else:
                    os.remove(res_path)
            logger.info(f'Downloading {resname}')
            tasks.append((resurl+resname,res_path))

    pool = Pool(processes=16)
    for i in tqdm(pool.imap_unordered(download_multitask, tasks),total=len(tasks)): 
        pass