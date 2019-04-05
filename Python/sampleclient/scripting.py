import textwrap
import os
import json


# File names used for presubmit script.
WINDOWS_PRESUBMIT_FILENAME = "Presubmit.ps1"
LINUX_PRESUBMIT_FILENAME = "Presubmit.sh"

# This is the shell command we'll use to invoke the job presubmission script
# when using Azure Storage with submition of Windows hosted jobs.
# See the documentation for `create_presubmit_script()`.
WINDOWS_PRESUBMIT_COMMAND = 'powershell.exe -ExecutionPolicy Unrestricted -File Presubmit.ps1'
LINUX_PRESUBMIT_COMMAND = 'chmod 755 Presubmit.sh && sudo bash Presubmit.sh'

# This is the base directory used to place uncompressed files on the resulting VM.
WINDOWS_DROP_PATH_ROOT = 'c:\\'
LINUX_DROP_PATH_ROOT = "/"


def is_linux(log, os_image):
    if not os_image or 'osType' not in os_image:
        if log:
            log.error('Malformed image selected for is_linux check. Image: %s', json.dumps(os_image))
        exit(1)

    os_type = str(os_image['osType']).lower()

    return os_type and os_type == 'linux'


def _get_presubmit_script_name(log, os_image):
    if is_linux(log, os_image):
        return LINUX_PRESUBMIT_FILENAME

    return WINDOWS_PRESUBMIT_FILENAME


def _get_presubmit_command(log, os_image):
    if is_linux(log, os_image):
        return LINUX_PRESUBMIT_COMMAND

    return WINDOWS_PRESUBMIT_COMMAND


def _get_remote_drop_path_root(log, os_image):
    if is_linux(log, os_image):
        return LINUX_DROP_PATH_ROOT

    return WINDOWS_DROP_PATH_ROOT


def render_presubmit_install_script_for_windows(log, job_name, os_image):
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


def render_presubmit_install_script_for_linux(log, job_name, os_image):
    """
    Render the text of the presubmission BASH script for linux.

    Args:
        job_name: Name of the job that the script operates on. This implicitly
            determines the name of the archived fuzzing target to unzip, as well
            as the directory to unzip it to.
    """

    template = '''
    #!/bin/bash
    set -euo pipefail
    IFS=$'\n\t'
    zipFilePath=`pwd`/{job_name}.zip;
    echo $zipFilePath
    outputDir = "/{job_name}";
    if [ -d $outputDir ]
    then
        rm -rf $outputDir
    fi
    mkdir -p $outputDir;
    yum install unzip || echo ""
    unzip $zipFilePath -d $outputDir
    '''

    return textwrap.dedent(template.format(job_name=job_name)).strip()


def render_presubmit_install_script(log, job_name, os_image):
    """
    Render the text of the presubmission script based on its OS Type.

    Args:
        job_name: Name of the job that the script operates on. This implicitly
            determines the name of the archived fuzzing target to unzip, as well
            as the directory to unzip it to.
        os_image: OS Image dict entry from MSDR API client.
    """
    if is_linux(log, os_image):
        log.debug('Linux Presubmit Install Script Detected.')
        return render_presubmit_install_script_for_linux(log, job_name, os_image)

    log.debug('Windows Presubmit Install Script Detected.')
    return render_presubmit_install_script_for_windows(log, job_name, os_image)


# The job presubmission script unzips the fuzz target and seed data to a fixed
# location on the fuzzing VM. We will generate it when creating the job, store
# it in Azure, then fetch and execute it from the fuzzing VM. The target and
# data job parameters, `seedDir` and `testDriverExecutable`, can then be given
# under the assumption that the presubmission script has been run.
def create_presubmit_script(log, save_dir, job_name, args, os_image):
    """
    Generate a job presubmission script named:
        - "Presubmit.ps1" on Windows
        - "Presubmit.sh" on Linux

    This will unzip the fuzzing target and its data into a directory that should
    be pointed to by the "testDriverExecutable" and "seedDir" keys of the job
    parameters JSON file.

    Args:
        save_dir: The directory in which to create the script.
        job_name: The name of the job, which determines the naming of various
            files that the generated script will expect and create.
    """
    script_text = render_presubmit_install_script(log, job_name, os_image)
    script_path = os.path.join(save_dir, _get_presubmit_script_name(log, os_image))

    log.debug('create_presubmit_script: script_path=%s', script_path)
    log.debug('create_presubmit_script: script_text=%s', script_text)

    with open(script_path, 'w') as script:
        script.write(script_text)

    return script_path
