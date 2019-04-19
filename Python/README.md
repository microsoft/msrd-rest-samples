# MSRD Job Submission with Python 3

- Uses **package-based** job submission
- Requires **Python 3**
- Assumes a **Linux** environment

## Summary

This project is an example of **package-based job submission** on **Linux**
using the Microsoft Security Risk Detection **REST API** and **Python 3**. It
exposes several API endpoints via a command line script. It also demonstrates
how the MSRD **Files API** can be used to upload files that will only be
available to fuzzing jobs.

## Setup

1. Ensure you have Python 3 installed.
2. Create a new virtualenv named `venv` with `python3 -m venv venv`.
3. Activate the virtualenv with `. venv/Scripts/activate`.
4. Install dependencies with `pip install -r requirements.txt`.

You are now ready to run the script.

## Script parameters

The `msrd.py` script has three common parameters.
Each parameter has an associated environment variable.

1. MSRD Account ID: set via the `a`/`--account` option or the `MSRD_ACCOUNT`
   environment variable.

2. MSRD API Token: set via the `-t`/`--token` option or the `MSRD_TOKEN`
   environment variable. You can generate API tokens via the Settings page of
   the MSRD customer portal.

3. MSRD URL (optional): set via the `-u`/`--url` option or the `MSRD_URL`
   environment variable. Defaults to `https://microsoftsecurityriskdetection.com`.

The Account ID and API Token are a bit long for interactive use, so you may find
it most convenient to create a script that exports the parameters as environment
variables. For example, you may choose to define a file `msrd-env.sh` like so:

```bash
export MSRD_ACCOUNT='your-account-id-goes-here'
export MSRD_TOKEN='your-api-token-goes-here'
```

You can then pull this into a shell session via `. msrd-env.sh`. If you do this,
consider adding a `.gitignore` entry to make sure you don't commit a file like
this to version control!

## Example usage: `Demofuzz`

To help you get up and running, we've provided a job JSON file for use with the
`DemofuzzLinux` target in `SampleFuzzingJobs`. This file can be found in the
`job-data` directory, alongside an `install-demofuzz.sh` script.

First, ensure you have followed the instructions in the Setup section above. You
can validate that the `msrd.py` script is correctly configured by running the
command `./msrd.py account-info`.

Then, to submit a job, invoke the script like so:

```bash
./msrd.py \
  -j job-data/demofuzz.json
  job-data/install-demofuzz.sh \
  ../SampleFuzzingJobs/DemofuzzLinux/demofuzz.exe \
  ../SampleFuzzingJobs/DemofuzzLinux/seeds/data.bin
```

This will upload the three files passed as positional arguments,
load `demofuzz.json` and update it to include the newly-created URLs
from the File API, and submit the job for fuzzing.

Note that the above assumes that `msrd.py` has executable permissions, and that
you've made the common script parameters available through environment
variables.