import argparse
import os
import zipfile
from pathlib import Path

import pyjson5
from gf_utils.download import Downloader

from logger_tt import logger, setup_logging

os.chdir(Path(__file__).resolve().parent)


def setup_mp_logging():
    setup_logging(config_path="logger_tt/log_config.json")


def parse_args():
    parser = argparse.ArgumentParser(description="Arguments will override corresponding settings in config.json5")
    parser.add_argument("--output", type=str, help="Output directory")
    parser.add_argument(
        "--region", type=str, help="Server region, the program will read resdata/{$REGION}_resdata.json to find assets"
    )
    parser.add_argument(
        "--downloadres", type=int, help="Whether to download resdata.zip, 1 for true and 0 for false", metavar="0/1"
    )
    parser.add_argument(
        "--url", type=str, help="URL for downloading resdata.zip, will override download_resdata if given"
    )
    parser.add_argument(
        "--abname",
        action="store_const",
        const=True,
        help="Save assets using assetBundleName instead of resname, useful for unpackers",
    )
    group = parser.add_argument_group(
        "Assets",
        description="Select assets you want to download (base/add/passivity), all settings in config.json5 will be overrided if any is passed",
    )
    group.add_argument("-b", action="store_true", help="Download base assets (required to open the game)")
    group.add_argument(
        "-a", action="store_true", help="Download additional assets (required for full gameplay experience)"
    )
    group.add_argument(
        "-p", action="store_true", help="Download passivity assets (optional assets: hd picture, voice, etc.)"
    )
    group = parser.add_argument_group("Downloader related")
    group.add_argument("--timeout", type=float, help="Timeout before retry")
    group.add_argument("--retry", type=int, help="Max retry times")
    group.add_argument("--njobs", type=int, help="Number of simutaneous processes")
    args = parser.parse_args()
    with open("config.json5", encoding="utf-8") as f:
        config = pyjson5.load(f)
    if args.output is not None:
        config["destination"] = args.output
    if args.region is not None:
        config["region"] = args.region
    if args.downloadres is not None:
        config["download_resdata"] = bool(args.downloadres)
    if args.url is not None:
        config["resdata_url"] = args.url
        config["download_resdata"] = True
    if args.abname is not None:
        config["use_abname"] = args.abname
    if args.b or args.a or args.p:
        config["download_base_assets"], config["download_add_assets"], config["download_passivity_assets"] = (
            args.b,
            args.a,
            args.p,
        )
    if args.timeout is not None:
        config["timeout"] = args.timeout
    if args.retry is not None:
        config["max_retry"] = args.retry
    if args.njobs is not None:
        config["processes"] = args.njobs
    return config


if __name__ == "__main__":
    config = parse_args()
    setup_mp_logging()
    downloader = Downloader(n_jobs=config["processes"], timeout=config["timeout"], retry=config["max_retry"])

    out_dir = config["destination"]
    os.makedirs(out_dir, exist_ok=True)
    resdata_url = config["resdata_url"]
    if config["download_resdata"] is True:
        print("Downloading compressed resdata from github")
        logger.info("Downloading compressed resdata from github")
        downloader.download([[resdata_url, "./resdata.zip"]])
    else:
        logger.warning(f'Using local resdata/{config["region"]}_resdata.json, please ensure that it is up-to-date')
    zipfile.ZipFile("resdata.zip").extractall("./resdata")
    data = zipfile.ZipFile("resdata.zip").read(f'{config["region"]}_resdata.json')
    with open(f'resdata/{config["region"]}_resdata.json', "r", encoding="utf-8") as f:
        res_data = pyjson5.load(f)
    resurl = res_data["resUrl"]
    tasks = []
    selected_id = []
    selected_id += [0] if config["download_base_assets"] else []
    selected_id += [1] if config["download_add_assets"] else []
    selected_id += [2] if config["download_passivity_assets"] else []
    ab_keys = ["BaseAssetBundles", "AddAssetBundles", "passivityAssetBundles"]

    print("Collecting resource urls")
    logger.info("Collecting resource urls")
    for d in selected_id:
        key = ab_keys[d]
        for bundle in res_data[key]:
            resname = bundle["resname"] + ".ab"
            abname = bundle["assetBundleName"] + ".ab"
            size = bundle["sizeOriginal"]
            res_path = os.path.join(out_dir, abname if config["use_abname"] else resname)
            if os.path.exists(res_path):
                if os.path.getsize(res_path) == size:
                    logger.info(f"File {resname} already exists, thus will be skipped")
                    continue
                else:
                    os.remove(res_path)
            tasks.append([resurl + resname, res_path])

    for bundle in res_data["bytesData"]:
        if bundle["fileInABC"] in selected_id:
            resname = bundle["resname"] + ".dat"
            abname = bundle["fileName"] + ".ab"
            size = bundle["sizeCompress"]
            res_path = os.path.join(out_dir, abname if config["use_abname"] else resname)
            if os.path.exists(res_path):
                if os.path.getsize(res_path) == size:
                    logger.info(f"File {resname} already exists, thus will be skipped")
                    continue
                else:
                    os.remove(res_path)
            tasks.append([resurl + resname, res_path])

    print("Start downloading")
    logger.info("Start downloading")
    downloader.download(tasks)
