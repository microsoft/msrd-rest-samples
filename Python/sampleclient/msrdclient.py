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
import requests

from .scripting import _get_presubmit_command, _get_remote_drop_path_root


class MSRDClient(object):
    """
    The Microsoft Security Risk Detection client.

    Encapsulates a subset of the MSRD HTTP API.
    """

    def __init__(
        self,
        msrd_origin,
        account_id,
        api_token,
        logger_object,
        proxies=None,
        verifyCerts=True
    ):
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
        self.verifyCerts = verifyCerts
        self.logger = logger_object

        self.api_base_url = '{}/api/accounts/{}'.format(self.msrd_origin, self.account_id)
        self.files_upload_url = '{}/files/accounts/{}/session/'.format(self.msrd_origin, self.account_id)

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
            self.logger.debug('Using proxies: %s', json.dumps(self.proxies, indent=2))
            self.session.proxies = self.proxies

            # WARNING: Though we verify TLS certificates by default, we allow
            # skipping validation for cases when the Requests library is unable
            # to validate certificates, e.g. when using TLS interception with a
            # self-signed root certificate. Users can also pass a path to a root
            # certificate (or bundle) to trust.
            #
            # See: http://docs.python-requests.org/en/latest/user/advanced/#ssl-cert-verification
            self.session.verify = self.verifyCerts

            if not self.verifyCerts:
                self.logger.log.warning('Disabling TLS certificate validation')

    def display_account_info(self):
        """
        Get info about the configured user account.

        Wraps the HTTP request `GET /api/accounts/{account-id}`.
        """

        r = self.session.get(self.api_base_url)
        info = r.json()

        self.logger.info('%s', json.dumps(info, indent=2))

    def get_os_images(self):
        """
        Get the list of OS images allowed for job creation.

        Wraps the HTTP request `GET /api/accounts/{account-id}/osimages`.
        """

        url = '{}/osimages'.format(self.api_base_url)
        r = self.session.get(url)
        os_images = r.json()

        self.logger.debug('OS images URL: %s', url)
        self.logger.debug('OS images: %s', json.dumps(os_images, indent=2))

        return os_images

    def put_file_upload_via_api(self, file_name):
        """
        Put HTTP File Upload.

        Returns the internal-access only URL. You will not be able to
        reference this URL or its files content in public.

        TODO - Validate
        """
        self.logger.debug('Files Upoad URL: %s', self.files_upload_url)
        self.logger.debug('File to upload: %s', file_name)

        with open(file_name, 'rb') as f:
            r = self.session.put(self.files_upload_url, data=f)

        upload_url = r.json()

        self.logger.debug('File upload result URL: %s', upload_url)

        return upload_url

    def create_job_parameters(self, job_params_path, submission_type, os_image, job_name, job_blob_url, presubmit_blob_url):
        """
        Create the parameters for the job submission

        Args:
            job_params_path: Path to JSON file containing job parameters.
            submission_type: the type of submission (VM or package)
            image: the image that will be used for the submission (from API)
            job_name: the name of the job.
            job_blob_url: url to the zip file containing the package dependency.
            presubmit_blob_url: url to the presubmission script
        """
        with open(job_params_path) as f:
            job_params = json.load(f)

            if submission_type == 'VM':
                return {
                    'setup': {
                        'command': _get_presubmit_command(self.logger, os_image),
                        'downloadUris': [job_blob_url, presubmit_blob_url]
                    },
                    'testDriverParameters': job_params
                }
            elif submission_type == 'package':
                return {
                    'setup': {
                        'package': {
                            'command': '',
                            'destinationFolder': "{}{}".format(_get_remote_drop_path_root(self.logger, os_image), job_name),
                            'fileInformations': [
                                {
                                    'name': "{}.zip".format(job_name),
                                    'url': job_blob_url,
                                    'action': "Unzip"
                                }
                            ]
                        }
                    },
                    "submit": {
                        'testDriverParameters': job_params
                    }
                }
            else:
                error = 'Invalid submission type {}'.format(submission_type)
                raise ValueError(error)

    def create_job(self, job_path, os_image, job_submission_parameters, submission_type):
        """
        Create a new job from a fuzzing target, a JSON file of job parameters,
        a list of job dependency URLs, and an OS image.

        Wraps the HTTP request `POST /api/accounts/{account-id}/jobs`.

        Args:
            job_path: Path to directory of target application and seed data.
            job_submission_parameters: The paramters of the job submission.
            os_image: Type of OS image to use, as a dict from `get_os_images()`.
        """
        # Query parameters.
        params = {
            'osImageId': os_image['id'],
            'submission_type': submission_type
        }

        url = '{}/jobs'.format(self.api_base_url)

        self.logger.debug('create_job->url: %s', url)
        self.logger.debug('create_job->job_submission_parameters: %s', job_submission_parameters)
        self.logger.debug('create_job->params: %s', params)

        r = self.session.post(url, json=job_submission_parameters, params=params)

        self.logger.debug('Sent request: %s body %s', r.url, r.request.body)

        job = r.json()

        self.logger.debug('Created job: %s', json.dumps(job, indent=2))

        return job
