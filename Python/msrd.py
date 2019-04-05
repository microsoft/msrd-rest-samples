#!/usr/bin/env python3
from __future__ import print_function

# import datetime
import os
import json
import shutil
import tempfile

from sampleclient import (
    log, set_logging_debug, MSRDClient, FileUpload,
    create_archive, create_presubmit_script,
    render_presubmit_install_script, Config, parse_args)


def main():
    args = parse_args()

    if args.verbose:
        set_logging_debug(log)

    # Create our configuration data monad.
    config = Config(log, args.config)

    # Error checking. The --job_os arg is required.
    if not args.job_os:
        log.error(
            'Must use non-empty OS "osType" (--job_os) associated with MSRD account with ID %s',
            config.msrd_account_id,
        )
        exit(1)

    # Error checking. The --job_os_edition arg is required.
    if not args.job_os_edition:
        log.error(
            'Must use non-empty OS "osEdition" (--job_os_edition) associated with MSRD account with ID %s',
            config.msrd_account_id,
        )
        exit(1)

    # We want people to use package based submission as much as possible.
    if str(args.submission_type).lower() == 'vm':
        if str(args.job_os).lower() == 'linux':
            log.error('Must use Package submission and not VM submission with Linux based jobs.')
            exit(1)

        if str(args.storage_type).lower() == 'api':
            log.error('Must use Package submission with PUT API based storage jobs.')
            exit(1)
        # Must use Azure storage for Windows based VM submitted jobs.

    # Create our MSDR client.
    msrd = MSRDClient(
        config.msrd_origin,
        config.msrd_account_id,
        config.msrd_api_token,
        log,
        proxies=config.proxies,
        verifyCerts=config.verifyCerts,
    )

    # Get the provisioned os images for account.
    os_images = msrd.get_os_images()

    # Error checking. We must have a os_image allocated to use an os_image.
    if not os_images:
        log.error(
            'No OS images associated with MSRD account with ID %s',
            config.msrd_account_id,
        )
        exit(1)

    # Users query input.
    requested_os = str(args.job_os)
    requested_os_edition = str(args.job_os_edition)

    filtered_images = [img for img in os_images if str(img['osType']) == requested_os and str(img['osEdition']) == requested_os_edition]

    # Error checking. User must select an available OS and OS Edition.
    if not filtered_images:
        os_options = ["\n[--osType={}, --osEdition={}]".format(img['osType'], img['osEdition']) for img in os_images]
        log.error(
            'No OS images associated with MSRD account with ID %s and OS/Edition of %s/%s.  Options: %s',
            config.msrd_account_id,
            requested_os,
            requested_os_edition,
            os_options
        )
        exit(1)

    # Select the image to use from the available list.
    image = filtered_images[0]

    log.debug('Using Image: `%s`', json.dumps(image))

    # FileUpload abstracts where and how the data is uploaded so we have urls to reference.
    storage = FileUpload(log, config, args, msrd)

    # If `job_path` is `some/dir/myjob/`, the job name will be `myjob`.
    job_name = os.path.basename(os.path.normpath(args.job_path))

    # Create a temporary directory to set up job dependencies.
    tmp_dir = tempfile.mkdtemp()

    # The base path of the archive to create, excluding the extension.
    archive_base_path = os.path.join(tmp_dir, job_name)

    # Create an archive of the job target and its seed data.
    job_archive_path = create_archive(log, args.job_path, archive_base_path)

    # Create a script to deploy the above archive on the fuzzing VM.
    presubmit_script_path = create_presubmit_script(log, tmp_dir, job_name, args, image)

    # Upload job archive and the generated script to the file storage option selected.
    # Returns the urls the service will use for the file and its presubmit script.
    job_blob_url, presubmit_blob_url = storage.upload_files(job_archive_path, presubmit_script_path)

    # We're done with our working directory, so clean it up.
    try:
        shutil.rmtree(tmp_dir, ignore_errors=True)
    except Exception as e:
        log.debug(
            'Error while removing temp directory %s.  Files may need to be manually removed. Error: %s',
            tmp_dir,
            str(e)
        )

#    windows_images = [img for img in os_images
#                      if img['osType'] == 'Windows']

#    redhat_linux_images = [img for img in os_images
#                      if img['osType'] == 'Linux' and img['osEdition'] == 'Redhat']

    submission_parameters = msrd.create_job_parameters(args.job_params, args.submission_type, image, job_name, job_blob_url, presubmit_blob_url)

    log.debug('submission_parameters: %s', submission_parameters)

    job = msrd.create_job(
        args.job_path,
        image,
        submission_parameters,
        args.submission_type
    )

    if not job:
        log.error('No Job reply from create_job request.')
        exit(1)

    log.debug('job: %s', job)


if __name__ == '__main__':
    main()
