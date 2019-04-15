# MSRD Python 3 SDK Example

## Summary

This project is an example of using the Microsoft Security Risk Detection SDK
via Python 3. Using some configuration data and a path to a fuzzing target, it
uploads the files to Azure Storage or to the MSRD File Upload API, generates a
script to install the targets onto a fuzzing VM, and creates the fuzzing job.

We use the MSRD REST interface directly.

For file upload you have multiple options:

You have the option of using the Azure Storage [Python client
library][1] to easily upload files (such as scripts and fuzz targets) and
obtain time-limited file download URLs using Azure [Shared Access Signatures][2].

You have the option of using the MSRD File Upload PUT based API for packages
that are under 4 mb in size.

[1]: https://azure-storage.readthedocs.io/
[2]: https://docs.microsoft.com/en-us/azure/storage/common/storage-dotnet-shared-access-signature-part-1

## Setup

The following instructions assume a `bash` prompt, either directly on Linux or
via the Windows Subsystem for Linux (WSL). We describe how to get your Python
environment set up using `virtualenv`.

This example only requires that your system install has:

1. Python 3
2. `virtualenv`

Please see your platform documentation on how to install python 3.

Now, in the same directoy as `msrd.py`, create the Python virtual environment
and install the script's dependencies:

```sh
virtualenv venv
. venv/bin/activate
pip install -r requirements.txt
```

Your are now ready to run the script.

## Script parameters

The `msrd.py` script has five required parameters:

- `--config`: Path to the script configuration file.
- `--job_path`: Path to the fuzzing job directory.
- `--job_params`: Path to a job parameter file.
- `--job_os`: Select the Operating System to use for job submission.
- `--job_os_edition`: Select the Operating System Edition to use for job submission.

There is also an optional flag `-v`, which enables verbose logging.

### Script configuration file

The script configuration is a JSON file that specifies the origin of the MSRD
REST API, optionally the name of an Azure Storage "container" (which will be
created if it doesn't already exist and is needed), and Azure Storage and MSRD account authentication data (which should **not** be tracked in version control).

The configuration file also includes optional HTTP(S) proxy configuration info
for the client's execution environment. By default, TLS certificates are
validated. The optional `verifyCerts` key can be set to `true` or `false` to
enable or disable TLS certificate validation when using a proxy. `verifyCerts`
can also be set to the path of a PEM-encoded root certificate or bundle to
trust. You can read more about this
[here](http://docs.python-requests.org/en/latest/user/advanced/#ssl-cert-verification).

A template for this file (illustrating its schema) can be found in
`ConfigTemplate.json`. Note that this file must be valid JSON, so your actual
configuration file should _not_ include any comment syntax (even though the
template does for the sake of documentation).

### Job directory path

This should be a path to a _directory_ containing both the target of the fuzzing
job and some seed data. This directory's contents will be archived and uploaded.
The actual target binary and seed data are specified in the job parameters
file (see below).

### Job parameters file

The job parameters configuration file is part of the MSRD API. It contains the
job parameters that a user would _manually_ enter if using the MSRD job creation
wizard over RDP or SSH.

The `JobParams.json` file distributed with this example script works with the
`DemoFuzz` sample _target_ in the root of this same repo. `JobParams.json`
assumes that we have unzipped this sample target and seed data to particular
locations on the fuzzing VM.

The `msrd.py` script generates a "job presubmission" script based on the OS
used, which will be fetched and executed on the fuzzing VM to do exactly this.

See the `create_presubmit_script()` function in `sampleclient/msrdclient.py`
for more info.

## Use with `DemoFuzz`

To use this script with the `DemoFuzz` sample target, create a file called
`Config.json`, based on `ConfigTemplate.json`. You _must_ specify all fields
except for `proxies`, which may be omitted. If you include a `proxies`, key,
make sure you specify an origin for both the `http` and `https` keys.

Once this is done, you can create a job by running the `test-demofuzz.sh` script
(which requires `bash`) from the directory `springfield-sdk-exampes/Python`.

This script just runs `msrd.py` with a fixed set of arguments to create two new
fuzzing jobs, one for Windows and one for Linux, with `DemoFuzz` and the Linux
`DemoFuzzLinux` projects as targets, respectively.
