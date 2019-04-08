from .azure import AzureStorageContainer
from .filechecks import (file_exists, file_size_in_bytes, files_must_not_be_more_than, MAX_FILE_SIZE_FOR_PUT_API)


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

        if not file_exists(job_archive_path):
            self.log.error(
                'Job archive file %s does not exist.',
                job_archive_path
            )
            exit(1)

        if not file_exists(presubmit_script_path):
            self.log.error(
                'Presubmit script file %s does not exist.',
                presubmit_script_path
            )
            exit(1)

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
            files_must_not_be_more_than(
                self.log,
                [
                    job_archive_path,
                    presubmit_script_path
                ],
                limit=MAX_FILE_SIZE_FOR_PUT_API
            )

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
