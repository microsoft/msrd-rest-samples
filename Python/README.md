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
3. Activate the virtualenv with `. venv/bin/activate`.
4. Install dependencies with `pip install -r requirements.txt`.

You are now ready to run the scripts.

## The msrd.py Script parameters

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

## The msrd_azure_upload.py Script parameters

The `msrd_azure_upload.py` script has three common parameters.
Each parameter has an associated environment variable.

1. Microsoft Azure Storage Account ID: set via the `a`/`--account` option or the `AZURE_STORAGE_ACCOUNT` environment variable.  You can get this using your Azure customer portal.

2. Microsoft Azure Storage Key: set via the `-k`/`--key` option or the `AZURE_STORAGE_KEY`
   environment variable. You can get this using your Azure customer portal.

3. Microsoft Azure Container Name: set via the `-c`/`--container` option or the `AZURE_CONTAINER_NAME` environment variable.  You can get this using your Azure customer portal.

The Azure credentials are a bit long for interactive use, so you may find
it most convenient to create a script that exports the parameters as environment
variables. For example, you may choose to define a file `azure-msrd-env.sh` like so:

```bash
export AZURE_STORAGE_ACCOUNT='your-storage-account-id-goes-here'
export AZURE_STORAGE_KEY='your-storage-key-goes-here'
export AZURE_CONTAINER_NAME='your-container-name-goes-here'
```

You can then pull this into a shell session via `. azure-msrd-env.sh`. If you do this,
consider adding a `.gitignore` entry to make sure you don't commit a file like
this to version control!

## Example usage: Single File Upload

To upload a single file invoke the script like so:

```
./msrd_azure_upload.py -a <azure_storage_account> -k <azure_storage_key> -c <azure_container_name> upload-file -f <single_file>
```

This will upload a single file to azure and print out the URL that was generated for it. This will also show that your script is correctly configured.

## Example usage: Upload multiple files and output the correct job json.

You can also use this script to take a MSRD job file formated in JSON as input and automatically generate a seperate job file that includes the correct file actions, urls, and names added to its `setup.package.fileInformations` path.

This can be used for a build system, such as a CI/CD pipeline.

The default will only print the newly generated JSON object that uses the input file as its template:

```
./msrd_azure_upload.py -a <azure_storage_account> -k <azure_storage_key> -c <azure_container_name> update-job-file -i ../job.json  <file1> <file2> <fileN>
```

If you want to output a file you must use the `-o` flag:

```
./msrd_azure_upload.py -a <azure_storage_account> -k <azure_storage_key> -c <azure_container_name>  update-job-file -i ../job.json -o out_job.json  <file1> <file2> <file3>
```

This will upload the files (Three in the example above) passed as the last positional arguments, 
load `../job.json` and update it in memeory to include the newly-created file information, then save the new json file as `out_job.json`.

Note: The above assumes that `msrd_azure_upload.py` has executable permissions.

Note: You can also make all required script parameters available through environment variables.  The optional `-o` script parameter is explicitly not included in this.
