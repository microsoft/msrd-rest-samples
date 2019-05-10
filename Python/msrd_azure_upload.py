#!/usr/bin/env python3
"""
General Utility for managing Azure Powered File Uploads for MSRD.
"""
import json
from pathlib import Path
import datetime
import os
import click

from azure.storage.blob import BlobPermissions, BlockBlobService


class AzureStorageContainer: # pylint: disable=too-few-public-methods
    """
    Client for Azure Storage.

    Encapsulates a subset of the Microsoft Azure Storage API.
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
        """
        Try to create the expected container.
        If it already exists, this will fail without throwing an exception.
        If the container name contains characters that are not alphanumeric, or
        it contains dashes, a 'AzureHttpError' is raised as this is an invalid name.
        Azure enforces this per:
        https://blogs.msdn.microsoft.com/jmstall/2014/06/12/azure-storage-naming-rules/
        """
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
        return blob_url


def print_response(response):
    """
    Pretty-Print response data
    """
    try:
        print(json.dumps(response.json(), indent=2))
    except json.JSONDecodeError:
        print(response.text)
    except AttributeError:
        print(response)


def update_file_info_in_job(job, file_infos):
    """
    Update the 'setup.package.fileInformations' data in the JSON to append new file information.
    """
    for file_info in file_infos:
        try:
            job['setup']['package']['fileInformations'].append(file_info)
        except (KeyError, TypeError, AttributeError):
            # If we get here, 'setup.package.fileInformations' does not exist yet.
            print('Job file input is missing required setup.package.fileInformations data.')
            exit(1)

    return job


def upload_file_and_generate_file_info(client, job, files):
    """
    Upload every file in 'files' using the Azure 'client' and collect the generated url.
    Add that url, the file name, and the action 'DownloadOnly' to the 'job' file data.
    """
    file_info = []

    for file in files:
        path = Path(file)
        url = client.upload_file(file)

        info = {
            'action': 'DownloadOnly',
            'name': path.name,
            'url': url,
        }

        file_info.append(info)

    if file_info:
        job = update_file_info_in_job(job, file_info)

    return job


@click.group()
@click.option('storage_account',
              '-a', '--account',
              envvar='AZURE_STORAGE_ACCOUNT',
              prompt='Azure Storage Account?')
@click.option('storage_key',
              '-k', '--key',
              envvar='AZURE_STORAGE_KEY',
              prompt='Azure Storage Key?')
@click.option('container_name',
              '-c', '--container',
              envvar='AZURE_CONTAINER_NAME',
              prompt='Azure Container Name?')
@click.pass_context
def main(ctx, storage_account, storage_key, container_name):
    """Construct the Azure Storage Container client and continue."""
    ctx.obj = AzureStorageContainer(storage_account, storage_key, container_name)


@main.command()
@click.option('file_path',
              '-f', '--file',
              envvar='AZURE_LOCAL_FILE_PATH',
              prompt='Azure local file path?')
@click.pass_obj
def upload_file(client, file_path):
    """
    Upload a single file to Azure and get its URL.
    """
    print_response(client.upload_file(file_path))


@main.command()
@click.option('input_job_path',
              '-i', '--in_job_file',
              envvar='MSRD_LOCAL_JOB_FILE_INPUT_PATH',
              prompt='Path to job JSON')
@click.option('output_job_path',
              '-o', '--out_job_file',
              required=False,
              default=None)#  Only Print Instead by default.
@click.argument('files', nargs=-1)
@click.pass_obj
def update_job_file(client, input_job_path, output_job_path, files):
    """
    Update a job file to include files from the command line.
    Appends the following file information data to the outputted
    'setup.package.fileInformations' data:

    file_information = {
        url: 'URL Generated By Azure for the file.'
        name: 'The original file's base name.'
        action: 'DownloadOnly'
    }
    """
    with open(input_job_path) as file:
        job = json.load(file)

    job = upload_file_and_generate_file_info(client, job, files)

    if output_job_path:
        with open(output_job_path, 'w+') as out_file:
            json.dump(job, out_file, indent=2)

    print_response(job)


if __name__ == '__main__':
    main()  # pylint: disable=no-value-for-parameter
