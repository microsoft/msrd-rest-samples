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


# This is the shell command we'll use to invoke the job presubmission script.
# See the documentation for `create_presubmit_script()`.
PRESUBMIT_COMMAND = 'powershell.exe -ExecutionPolicy Unrestricted -File Presubmit.ps1'


class MSRDClient(object):
    """
    The Microsoft Security Risk Detection client.

    Encapsulates a subset of the MSRD HTTP API.
    """

    def __init__(self, msrd_origin, account_id, api_token, proxies=None):
        """
        Args:
            msrd_origin: Origin for the API of the MSRD service.
            account_id: MSRD account ID.
            api_token: API token for the given MSRD account.
            proxies: Optional. Dict that maps the strings 'http' and 'https' to
                the proxy URL for each protocols.
        """

        self.msrd_origin = msrd_origin
        self.account_id = account_id
        self.api_token = api_token
        self.proxies = proxies

        self.api_base_url = '{}/api/accounts/{}'.format(self.msrd_origin, self.account_id)

        self._init_session()

    def _init_session(self):
        # Create a session with headers that will authenticate our MSRD requests
        # and advertise the correct content type.
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'SpringfieldApiToken': self.api_token,
        })

        # Configure our session to use proxies, if we have them.
        if self.proxies:
            log.debug('Disabling TLS cert validation, using proxies: %s',
                      json.dumps(self.proxies, indent=2))
            self.session.proxies = self.proxies

            # WARNING: we disable TLS cert validation under the assumption that
            # the Requests library is unable to validate a proxy's self-signed
            # cert.
            #
            # More info: http://docs.python-requests.org/en/latest/user/advanced/#ssl-cert-verification
            self.session.verify = False

    def display_account_info(self):
        """
        Get info about the configured user account.

        Wraps the HTTP request `GET /api/accounts/{account-id}`.
        """

        r = self.session.get(self.api_base_url)
        info = r.json()

        log.info('%s', json.dumps(info, indent=2))

    def get_os_images(self):
        """
        Get the list of OS images allowed for job creation.

        Wraps the HTTP request `GET /api/accounts/{account-id}/osimages`.
        """

        url = '{}/osimages'.format(self.api_base_url)
        r = self.session.get(url)
        os_images = r.json()

        log.debug('OS images: %s', json.dumps(os_images, indent=2))

        return os_images

    def create_job(self, job_path, job_params_path, download_urls, os_image):
        """
        Create a new job from a fuzzing target, a JSON file of job parameters,
        a list of job dependency URLs, and an OS image.

        Wraps the HTTP request `POST /api/accounts/{account-id}/jobs`.

        Args:
            job_path: Path to directory of target application and seed data.
            job_params_path: Path to JSON file containing job parameters.
            download_urls: List of URLs to be downloaded on fuzzing VM.
            os_image: Type of OS image to use, as a dict from `get_os_images()`.
        """

        job_name = os.path.basename(os.path.normpath(job_path))

        with open(job_params_path) as f:
            job_params = json.load(f)

        # Serialized as JSON for POST body.
        data = {
            'setup': {
                'command': PRESUBMIT_COMMAND,
                'downloadUris': download_urls,
            },
            'testDriverParameters': job_params,
        }

        log.debug('Sending job data: %s', json.dumps(data, indent=2))

        # Query parameters.
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
    """
    Client for Azure Storage.

    Encapsulates a subset of the Azure Storage API.
    """

    def __init__(self, storage_account, storage_key, container_name):
        """
        Args:
            storage_account: Azure Storage account ID.
            storage_key: API key for the given Azure Storage account.
            container_name: Name of the container to use for uploads. If it does
                not exist, it will be created.
        """

        self.storage_account = storage_account
        self.storage_key = storage_key
        self.container_name = container_name

        # The blob service is the object used to interact with Azure Storage.
        self.blob_service = BlockBlobService(self.storage_account, self.storage_key)

        # Ensure the expected container exists.
        self._create_container()

    def _create_container(self):
        # Try to create the expected container. If it already exists, this will
        # fail without throwing an exception.
        self.blob_service.create_container(self.container_name)

    def upload_file(self, file_path, access_time=3600):
        """
        Upload a file to Azure Storage, returning a URL to the uploaded file.
        File accessibility via this URL is time-limited via the Azure Storage
        shared access signature mechanism.

        Args:
            file_path: Path to the file to upload.
            access_time: Shared access signature lifetime for the returned URL.
        """

        blob_name = os.path.basename(os.path.normpath(file_path))
        self.blob_service.create_blob_from_path(self.container_name, blob_name, file_path)

        log.debug('Created blob `%s` in container `%s`', blob_name, self.container_name)

        # Created a shared access signature token with an access time of
        # `access_time` seconds from now. This will be used to create a URL with
        # time-limited read-only permissions.
        start = datetime.datetime.utcnow()
        expiry = start + datetime.timedelta(seconds=access_time)
        sas_token = self.blob_service.generate_blob_shared_access_signature(
            self.container_name,
            blob_name,
            permission=BlobPermissions.READ,
            start=start,
            expiry=expiry,
        )

        # Create the actual (time-limited) URL for the file.
        blob_url = self.blob_service.make_blob_url(
            self.container_name,
            blob_name,
            sas_token=sas_token,
        )
        log.debug('Blob readable at `%s`', blob_url)

        return blob_url


def create_archive(src_dir, archive_base_name):
    """
    Create a compressed .zip archive of a directory.

    Args:
        src_dir: Path to the directory to archive. This will be the root of the
            resulting archive.
        archive_base_name: The name of the resulting archive. For example, an
            argument of "data" will result in an archive named "data.zip".
    """

    # Get a generator of names of supported archive formats.
    archive_formats = (fmt for (fmt, _) in shutil.get_archive_formats())

    # We could use other formats, but just require `zip` for now.
    if 'zip' not in archive_formats:
        log.error('Unable to create `.zip` files, aborting.')
        exit(1)

    log.debug(
        'Creating zip archive with base name `%s` and root dir `%s`.',
        archive_base_name,
        src_dir,
    )

    # The archive will be created in the working directory, and we return the
    # full name (including extension) of the created file.
    return shutil.make_archive(
        archive_base_name,
        'zip',
        logger=log,
        root_dir=src_dir,
    )


def render_presubmit_install_script(job_name):
    """
    Render the text of the presubmission PowerShell script.

    Args:
        job_name: Name of the job that the script operates on. This implicitly
            determines the name of the archived fuzzing target to unzip, as well
            as the directory to unzip it to.
    """

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


# The job presubmission script is a PowerShell script to place. We will generate
# it when creating the job, store it in Azure, then fetch and execute it from
# the fuzzing VM.
def create_presubmit_script(save_dir, job_name):
    """
    Generate a job presubmission PowerShell script named "Presubmit.ps1".

    This will unzip the fuzzing target and its data into a directory that should
    be pointed to by the "testDriverExecutable" and "seedDir" keys of the job
    parameters JSON file.

    Args:
        save_dir: The directory in which to create the script.
        job_name: The name of the job, which determines the naming of various
            files that the generated script will expect and create.
    """

    script_text = render_presubmit_install_script(job_name)
    script_path = os.path.join(save_dir, 'Presubmit.ps1')

    with open(script_path, 'w') as script:
        script.write(script_text)

    return script_path


class Config(object):
    """
    Encapsulates parsed MSRD client configuration data, such as API credentials.
    """

    def __init__(self, config_path):
        """
        Args:
            config_path: Path a JSON file containing confirugation data.
        """

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

            # The "proxies" key is optional, so we use `get()` to default to
            # returning `None` instead of throwing a `KeyError`.
            self.proxies = config.get('proxies')  # todo: check for proper structure.
        except KeyError as e:
            log.error('Unable to find config key %s', e)
            exit(1)


def parse_args():
    """
    Parse arguments for command-line invocation of the script.
    """

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

    # If `job_path` is `some/dir/myjob/`, the job name will be `myjob`.
    job_name = os.path.basename(os.path.normpath(args.job_path))

    # Create a temporary directory to set up job dependencies.
    tmp_dir = tempfile.mkdtemp()

    # Copy the entire job directory into our temporary directory.
    # TODO: Avoid this.
    tmp_job_path = os.path.join(tmp_dir, job_name)
    shutil.copytree(args.job_path, tmp_job_path)

    # Create an archive of the job target and its seed data.
    job_archive_path = create_archive(tmp_job_path, job_name)

    # Create a script to deploy the above archive on the fuzzing VM.
    presubmit_script_path = create_presubmit_script(tmp_dir, job_name)

    # Upload the job archive and presubmission script. The resulting URLs have
    # time-limited access, via Azure Storage Shared Access Signature tokens.
    job_blob_url = storage.upload_file(job_archive_path)
    presubmit_blob_url = storage.upload_file(presubmit_script_path)

    # We're done with our working directory, so clean it up.
    # TODO: Don't just ignore an error here, but catch and log it.
    shutil.rmtree(tmp_dir, ignore_errors=True)

    # These files will be downloaded on the fuzzing VM.
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
