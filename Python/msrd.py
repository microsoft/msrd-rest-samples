#!/usr/bin/env python2
from __future__ import print_function

import argparse
import datetime
import json
import logging
import os
import shutil
import sys
import tempfile
import textwrap

from azure.storage.blob import BlobPermissions, BlockBlobService
import requests


logging.basicConfig(
    format='[%(asctime)s] MSRD: %(levelname)s: %(message)s',
    level=logging.WARNING,
)
log = logging.getLogger('msrd')
log.setLevel(logging.INFO)


PRESUBMIT_COMMAND = 'powershell.exe -ExecutionPolicy Unrestricted -File Presubmit.ps1'


class MSRDClient(object):
    def __init__(self, msrd_origin, account_id, api_token, proxies=None):
        self.msrd_origin = msrd_origin
        self.account_id = account_id
        self.api_token = api_token
        self.proxies = proxies

        self.api_base_url = '{}/api/accounts/{}'.format(self.msrd_origin, self.account_id)

        self._init_session()

    def _init_session(self):
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'SpringfieldApiToken': self.api_token,
        })

        if self.proxies:
            log.debug('Disabling TLS cert validation, using proxies: %s',
                      json.dumps(self.proxies, indent=2))
            self.session.proxies = self.proxies
            self.session.verify = False

    def display_account_info(self):
        r = self.session.get(self.api_base_url)
        info = r.json()

        log.info('%s', json.dumps(info, indent=2))

    def get_os_images(self):
        url = '{}/osimages'.format(self.api_base_url)
        r = self.session.get(url)
        os_images = r.json()

        log.debug('OS images: %s', json.dumps(os_images, indent=2))

        return os_images

    def create_job(self, job_path, job_params_path, download_urls, os_image):
        job_name = os.path.basename(os.path.normpath(job_path))

        with open(job_params_path) as f:
            job_params = json.load(f)

        data = {
            'setup': {
                'command': PRESUBMIT_COMMAND,
                'downloadUris': download_urls,
            },
            'testDriverParameters': job_params,
        }

        log.debug('Sending job data: %s', json.dumps(data, indent=2))

        params = {
            'osImageId': os_image['id'],
        }

        url = '{}/jobs'.format(self.api_base_url)
        r = self.session.post(url, json=data, params=params)

        log.debug('Sent request: %s', r.request.body)

        job = r.json()

        log.debug('Created job: %s', json.dumps(job, indent=2))

        return job


class StorageContainer(object):
    def __init__(self, storage_account, storage_key, container_name):
        self.storage_account = storage_account
        self.storage_key = storage_key
        self.container_name = container_name

        self.blob_service = BlockBlobService(self.storage_account, self.storage_key)

        self._create_container()

    def _create_container(self):
        self.blob_service.create_container(self.container_name)

    def upload_file(self, file_path, access_time=3600):
        blob_name = os.path.basename(os.path.normpath(file_path))
        self.blob_service.create_blob_from_path(self.container_name, blob_name, file_path)

        log.debug('Created blob `%s` in container `%s`', blob_name, self.container_name)

        start = datetime.datetime.utcnow()
        expiry = start + datetime.timedelta(seconds=access_time)
        sas_token = self.blob_service.generate_blob_shared_access_signature(
            self.container_name,
            blob_name,
            permission=BlobPermissions.READ,
            start=start,
            expiry=expiry,
        )
        blob_url = self.blob_service.make_blob_url(
            self.container_name,
            blob_name,
            sas_token=sas_token,
        )
        log.debug('Blob readable at `%s`', blob_url)

        return blob_url


def create_archive(src_dir, archive_base_name):
    archive_formats = (fmt for (fmt, _) in shutil.get_archive_formats())

    if 'zip' not in archive_formats:
        log.error('Unable to create `.zip` files, aborting.')
        exit(1)

    log.debug(
        'Creating zip archive with base name `%s` and root dir `%s`.',
        archive_base_name,
        src_dir,
    )

    return shutil.make_archive(
        archive_base_name,
        'zip',
        logger=log,
        root_dir=src_dir,
    )


def render_presubmit_install_script(job_name):
    template = '''
    $ErrorActionPreference='stop';
    $zipFilePath = Join-Path (pwd).Path {job_name}.zip;
    $outputDir = 'C:\\{job_name}';
    if(Test-Path $outputDir) {{
        rm -force -Recurse $outputDir
    }};
    md $outputDir;
    [System.Reflection.Assembly]::LoadWithPartialName('System.IO.Compression.FileSystem') | Out-Null;
    [System.IO.Compression.ZipFile]::ExtractToDirectory($zipFilePath, $outputDir);
    '''

    return textwrap.dedent(template.format(job_name=job_name)).strip()


def create_presubmit_script(save_dir, job_name):
    script_text = render_presubmit_install_script(job_name)
    script_path = os.path.join(save_dir, 'Presubmit.ps1')

    with open(script_path, 'w') as script:
        script.write(script_text)

    return script_path


class Config(object):
    def __init__(self, config_path):
        with open(config_path) as f:
            config = json.load(f)

        log.debug('Loaded config from `%s`', config_path)
        log.debug('Parsed config: `%s`', json.dumps(config, indent=2))

        try:
            self.msrd_origin = config['msrdOrigin']
            self.msrd_account_id = config['msrdAccountId']
            self.msrd_api_token = config['msrdApiToken']
            self.storage_account_id = config['azureStorageAccountId']
            self.storage_api_key = config['azureStorageApiKey']
            self.storage_container_name = config['azureStorageContainer']
            self.proxies = config.get('proxies')
        except KeyError as e:
            log.error('Unable to find config key %s', e)
            exit(1)


def parse_args():
    arg_parser = argparse.ArgumentParser(
        description='Microsoft Security Risk Detection (MSRD) job creation client'
    )

    required_flag_defs = [
        ('--config', 'JSON file containing MSRD client config data'),
        ('--job_path', 'Path to directory of executable and seed data for the MSRD job'),
        ('--job_params', 'JSON file containing job parameters'),
    ]

    for flag, flag_help in required_flag_defs:
        arg_parser.add_argument(flag, required=True, help=flag_help)

    arg_parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Use debug-level logging'
    )

    return arg_parser.parse_args()


def main():
    args = parse_args()

    if args.verbose:
        log.setLevel(logging.DEBUG)

    config = Config(args.config)

    storage = StorageContainer(
        config.storage_account_id,
        config.storage_api_key,
        config.storage_container_name,
    )

    job_name = os.path.basename(os.path.normpath(args.job_path))

    tmp_dir = tempfile.mkdtemp()

    tmp_job_path = os.path.join(tmp_dir, job_name)
    shutil.copytree(args.job_path, tmp_job_path)

    job_archive_path = create_archive(tmp_job_path, job_name)
    presubmit_script_path = create_presubmit_script(tmp_dir, job_name)

    job_blob_url = storage.upload_file(job_archive_path)
    presubmit_blob_url = storage.upload_file(presubmit_script_path)

    shutil.rmtree(tmp_dir, ignore_errors=True)

    download_urls = [
        job_blob_url,
        presubmit_blob_url,
    ]
    msrd = MSRDClient(
        config.msrd_origin,
        config.msrd_account_id,
        config.msrd_api_token,
        proxies=config.proxies,
    )

    os_images = msrd.get_os_images()

    if not os_images:
        log.error(
            'No OS images associated with MSRD account with ID %s',
            config.msrd_account_id,
        )
        exit(1)

    windows_images = [img for img in os_images
                      if img['osType'] == 'Windows']

    job = msrd.create_job(
        args.job_path,
        args.job_params,
        download_urls, windows_images[0]
    )


if __name__ == '__main__':
    main()
