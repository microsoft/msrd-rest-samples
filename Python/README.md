# MSRD Python 2 SDK Example

## Summary

This project is an example of using the Microsoft Security Risk Detection SDK
via Python 2. Using some configuration data and a path to a fuzzing target, it
uploads the files to Azure Storage, generates a script to install the targets
onto a fuzzing VM, and creates the fuzzing job.

We use the MSRD REST interface directly, together with the Azure Storage [Python
client library][1] to easily upload files (such as scripts and fuzz targets) and
obtain time-limited file download URLs using Azure [Shared Access
Signatures][2].

[1]: https://azure-storage.readthedocs.io/
[2]: https://docs.microsoft.com/en-us/azure/storage/common/storage-dotnet-shared-access-signature-part-1

## Setup

The following instructions assume a `bash` prompt, either directly on Linux or
via the Windows Subsystem for Linux (WSL). We describe how to get your Python
environment set up using `virtualenv`.

This example only requires that your system install has:

1. Python 2.7
2. `virtualenv`

On RHEL/CentOS 7.4, you can install these with:

```sh
sudo yum install python-virtualenv
```

On Debian or Ubuntu, e.g. if using WSL, you can invoke:

```sh
sudo apt install python-virtualenv
```

Now, in the same directoy as `msrd.py`, create the Python virtual environment
and install the script's dependencies:

```sh
virtualenv venv
. venv/bin/activate
pip install -r requirements.txt
```

Your are now ready to run the script.

## Script parameters

The `msrd.py` script has three required parameters:

- `--config`: Path to the script configuration file.
- `--job_path`: Path to the fuzzing job directory.
- `--job_params`: Path to a job parameter file.

There is also an optional flag `-v`, which enables verbose logging.

### Script configuration file

The script configuration is a JSON file that specifies the origin of the MSRD
REST API, the name of an Azure Storage "container" (which will be created if it
doesn't already exist), and Azure Storage and MSRD account authentication data
(which should **not** be tracked in version control). It also includes optional
HTTP(S) proxy configuration info for the client's execution environment.

A template for this file (illustrating its schema) can be found in
`ConfigTemplate.json`. Note that this file must be valid JSON, so your actual
configuration file should _not_ include any comment syntax (even though the
template does for the sake of documentation).

### Job directory path

This should be a path to a _directory_ containing both the target of the fuzzing
job and some seed data. This directory's contents will be archived and uploaded
to Azure Storage. The actual target binary and seed data are specified in the
job parameters file (see below).

### Job parameters file

The job parameters configuration file is part of the MSRD API. It contains the
job parameters that a user would _manually_ enter if using the MSRD job creation
wizard over RDP or SSH.

The `JobParams.json` file distributed with this example script works with the
`DemoFuzz` sample _target_ in the root of this same repo. `JobParams.json`
assumes that we have unzipped this sample target and seed data to particular
locations on the fuzzing VM. The `msrd.py` script generates a "job
presubmission" PowerShell script, which will be fetched and executed on the
fuzzing VM to do exactly this. See the `create_presubmit_script()` function for
in `msrd.py` for more info.

## Use with `DemoFuzz`

To use this script with the `DemoFuzz` sample target, create a file called
`Config.json`, based on `ConfigTemplate.json`. You _must_ specify all fields
except for `proxies`, which may be omitted. If you include a `proxies`, key,
make sure you specify an origin for both the `http` and `https` keys.

Once this is done, you can create a job by running the `test-demofuzz.sh` script
(which requires `bash`) from the directory `springfield-sdk-exampes/Python`.
This script just runs `msrd.py` with a fixed set of arguments to create a new
fuzzing job, with `DemoFuzz` as the target.
