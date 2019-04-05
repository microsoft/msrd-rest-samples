
import os
import datetime

from azure.storage.blob import BlobPermissions, BlockBlobService


class AzureStorageContainer(object):
    """
    Client for Azure Storage.

    Encapsulates a subset of the Azure Storage API.
    """

    def __init__(self, logger_object, storage_account, storage_key, container_name):
        """
        Args:
            storage_account: Azure Storage account ID.
            storage_key: API key for the given Azure Storage account.
            container_name: Name of the container to use for uploads. If it does
                not exist, it will be created.
        """
        self.log = logger_object
        self.storage_account = storage_account
        self.storage_key = storage_key
        self.container_name = container_name

        # The blob service is the object used to interact with Azure Storage.
        self.blob_service = BlockBlobService(self.storage_account, self.storage_key)

        # Ensure the expected container exists.
        self._create_container()

    def _create_container(self):
        # Try to create the expected container. If it already exists, this will
        # fail without throwing an exception. If the container name contains
        # characters that are not alphanumaric or dashes a AzureHttpError is
        # raised and you get an exception as Azure enforces this.
        # https://blogs.msdn.microsoft.com/jmstall/2014/06/12/azure-storage-naming-rules/
        self.log.debug('Azure container %s attempt create..', self.container_name)
        self.blob_service.create_container(self.container_name)
        self.log.debug('Azure container %s should exist.', self.container_name)

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

        self.log.debug('Created blob `%s` in container `%s`', blob_name, self.container_name)

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
        self.log.debug('Blob readable at `%s`', blob_url)
        return blob_url
