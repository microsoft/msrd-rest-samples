# MSRD Linux Automation Example

## Overview

The `msrd.sh` shell script is an example of how to use the MSRD HTTP API to
perform automated Linux job submission. It should only be considered an example
of automation, and uses a mix of SDK API calls and regular shell scripting. In
the future, the job submission portion of this script will be replaced by API
calls that use the MSRD SDK.

This sample can be used as a starting point for custom Linux job submission
scripts. In a production scenario, it would be enhanced with additional logging,
exhaustive error handling, &c.

## Requirements

The following dependencies are likely already installed on your system, but
worth noting:

- `curl`
- `scp`
- `ssh`

Less likely to be installed by default are:

- `jq` (JSON parsing tool)
- `sshpass` (for easily using `ssh`/`scp` with password authentication)

These are all available on most popular Linux distros.

For example, on Debian/Ubuntu, just run:

```
sudo apt install curl jq sshpass
```

## Script Steps

To run the script against the sample fuzz target, set the `$ACCOUNT_ID` and
`$API_TOKEN` script variables, then invoke `./msrd.sh`.

The script then attempts to:

1. Initializes a new Linux job preparation VM
1. Fetches the address and SSH credentials for the prep VM
1. Upload a fuzz target, seeds, and fuzzing parameters
1. Submits the job for validation and fuzzing

## Details

### Job identifiers

The script attempts to create a new job using the given target data, and keeps
job-specific data in a subfolder alongside `msrd.sh`. This includes API-fetched
login credentials and a job-specific `known_hosts` file which is used for SSH
commands. The script does not attempt to modify the user `known_hosts`.

### Script globals

There are two global variables that must be set when using the script, even with
the default fuzz targets:

- `ACCOUNT_ID`: The GUID of a user account.
- `API_TOKEN`: An API token for the above user account, generated from the
  Account Settings > Api Tokens page.

These must be set to properly direct and authenticate API requests.

### Job parameters

The script expects a file named `JobParams.json` to be located alongside it. The
object in this file contains fuzzing parameters that would otherwise be obtained
from the user interacting with the `sfwizard` command line tool, after logging
into the prep VM. The paths in the file refer to the filesystem on the
preparation VM, not the environment where the `msrd.sh` script is being run.

### Fuzz target and seeds

This example script is designed to create a new fuzz job for the
`SampleFuzzingJob/DemofuzzLinux` target. This is reflected in two places:

1. The script globals `$TARGET_PATH`, `$TARGET_NAME`, and `$TARGET_SEED_PATH`
1. The `JobParams.json` config file

To use this script with your own job, you must update these values both in the
script and in the configuration file. Note that the configuration file paths are
on the remote preparation VM, and the script paths are on the local system being
used to create and submit the job.
