import base64
import logging
import os
from urllib.parse import urlparse

import boto3

LOG_LEVEL = os.getenv("LOG_LEVEL", logging.INFO)
AWS_DEFAULT_REGION = os.getenv("AWS_DEFAULT_REGION", "eu-west-2")
BACKENDS = ["PS", "SM", "S3"]
ENV_VAR_PREFIX = "CONFIG"

logging.basicConfig(level=logging.INFO)

s3_client = boto3.client('s3', region_name=AWS_DEFAULT_REGION)
ssm_client = boto3.client("ssm", region_name=AWS_DEFAULT_REGION)


def main():
    configs = get_configs_from_envs()
    for config in configs:
        for backend in BACKENDS:
            if config["type"] == backend:
                get(config["type"], config)


def get_configs_from_envs():
    configs = list({})
    for var in os.environ:
        if var.startswith(f"{ENV_VAR_PREFIX}_"):
            logging.info(f"Found ENV var: {var}")
            value = os.getenv(var)
            config = {
                "name": var,
                "type": var.split("_")[1],
                "source": value.split("|")[0],
                "target": value.split("|")[1]
            }
            configs.append(config)
    return configs


def get(backend, config):
    if backend.upper() == "PS":
        get_ps(config)
    elif backend.upper() == "SM":
        get_sm(config)
    elif backend.upper() == "S3":
        get_s3(config)
    else:
        logging.error(f"Type not supported: {backend}, {config}")


def get_ps(config):
    source = config["source"]
    logging.info(f"Getting config from: {source}")
    response = ssm_client.get_parameter(Name=source)
    write_file(config["target"], response["Parameter"]["Value"])


def get_sm(config):
    # get from SM = Secrets Manager
    logging.error(f"Unsupported: {config['name']}")


def get_s3(config):
    source = config["source"]
    target = config["target"]

    logging.info(f"Getting config from: {source}")
    url = urlparse(source)
    bucket_name = url.hostname
    object_name = url.path[1:]
    os.makedirs(os.path.dirname(target), exist_ok=True)
    s3_client.download_file(bucket_name, object_name, target)
    logging.info(f"Written config to: {target}")


def write_file(target, content):
    os.makedirs(os.path.dirname(target), exist_ok=True)
    file = open(target, "w")
    file.write(base64.standard_b64decode(content).decode("utf-8"))
    file.close()
    logging.info(f"Written config to: {target}")


if __name__ == "__main__":
    logging.info(f"Starting")
    main()
    logging.info(f"Complete")
