from .azure import AzureStorageContainer

from pathlib import Path


class FileUpload():
    def __init__(self, logger_object, config, args, msrd_client):
        self.log = logger_object
        self.config = config
        self.args = args
        self.msrd = msrd_client

    def upload_files(self, job_archive_path, presubmit_script_path):
        """
        Upload files to remote endpoints so that the job submition can reference them via URL.
        Returns: tuple (job_blob_url, presubmit_blob_url, )
        """
        storage_type_lower = str(self.args.storage_type).lower()

        self.log.debug('storage_type_lower: %s', storage_type_lower)
        self.log.debug('job_archive_path: %s', job_archive_path)
        self.log.debug('presubmit_script_path: %s', presubmit_script_path)

        if storage_type_lower == 'azure':
            storage = AzureStorageContainer(
                self.log,
                self.config.storage_account_id,
                self.config.storage_api_key,
                self.config.storage_container_name,
            )

            # Upload the job archive and presubmission script. The resulting URLs have
            # time-limited access, via Azure Storage Shared Access Signature tokens.
            job_blob_url = storage.upload_file(job_archive_path)
            presubmit_blob_url = storage.upload_file(presubmit_script_path)

            self.log.debug('job_blob_url: %s', job_blob_url)
            self.log.debug('presubmit_blob_url: %s', presubmit_blob_url)

            return (job_blob_url, presubmit_blob_url, )
        elif storage_type_lower == 'api':
            job_blob_url = self.msrd.put_file_upload_via_api(job_archive_path)
            presubmit_blob_url = self.msrd.put_file_upload_via_api(presubmit_script_path)

            self.log.debug('job_blob_url: %s', job_blob_url)
            self.log.debug('presubmit_blob_url: %s', presubmit_blob_url)

            return (job_blob_url, presubmit_blob_url, )
        else:
            self.log.error(
                'Incorrect --storage_type selected for MSRD account with ID %s, must be API or AZURE and %s was used.',
                self.config.msrd_account_id,
                self.args.storage_type,
            )
            exit(1)
