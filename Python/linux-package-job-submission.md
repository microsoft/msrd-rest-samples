# AFL Linux fuzzing job submitted as package to MSRD

This article walks you through the submission of a
package-based fuzzing job on Linux.

## Preliminary: install python and sample repository

Install git and python dependencies.
On Debian/Ubuntu, this can be done via `apt-get`:

```bash
sudo apt-get update
sudo apt-get install git python3 python3-venv
```

```bash
# Clone the MSRD sample repository
git clone https://github.com/microsoft/msrd-rest-samples.git

# Configure MSRD target instance and account
export MSRD_TOKEN='******'
export MSRD_URL='https://microsoftsecurityriskdetection.com'
export MSRD_ACCOUNT='YOUR GUID'

## start python
cd ~/msrd-rest-samples/Python
python3 -m venv venv
. venv/bin/activate
pip install -r requirements.txt
```

## Submit `demofuzz` package-job on MSRD Linux

```bash
# Submit demofuzz to MSRD on Linux (e.g. here Ubuntu Experimental)
python ./msrd.py submit -j ../SampleFuzzingJobs/DemofuzzLinux//demofuzz-ubuntu.json ../SampleFuzzingJobs/DemofuzzLinux/install-demofuzz.sh ../SampleFuzzingJobs/DemofuzzLinux/demofuzz.exe  ../SampleFuzzingJobs/DemofuzzLinux/seeds/data.bin
```

## Submit `readelf` package-job on MSRD Linux with AFL

The AFL fuzzer can be used on both RedHat and Ubuntu Linux distributions in MSRD,
though the support on Ubuntu is considered experimental at this stage.
The instructions and commands that follow applied to both.

Building readelf with AFL:

```bash
sudo bash

# Build gcc and AFL
bash ../SampleFuzzingJobs/afl/build.sh

# Build readelf with AFL
bash ../SampleFuzzingJobs/readelf/build.sh

# Optional: verify that AFL works
bash -c 'echo /home/user/foo/core.%e.%p > /proc/sys/kernel/core_pattern'
/opt/afl-2.42b/afl-fuzz -i /opt/seeds -o /opt/fuzzoutput  /opt/binutils-2.28/binutils/readelf -a @@

# HIT CTRL+C to stop AFL
```

Packing some ELF files as seeds:

```bash
. ../SampleFuzzingJobs/readelf/prepareseeds.sh
```

Submitting the job to MSRD:

```bash
. venv/bin/activate
python ./msrd.py submit -j ../SampleFuzzingJobs/readelf/readelf-redhat.json ../SampleFuzzingJobs/readelf/install-readelf.sh /opt/binutils-2.28/binutils/readelf elfseeds.tgz
```

For Ubuntu Linux (experimental support), use `readelf-ubuntu.json` instead.

Expected output after submission:

```bash
200 OK https://sf-web-wiblum.fe-wiblum.p.azurewebsites.net/files/accounts/ed103462-69db-4bd2-9534-1ce318c2c5e4/session
200 OK https://sf-web-wiblum.fe-wiblum.p.azurewebsites.net/files/accounts/ed103462-69db-4bd2-9534-1ce318c2c5e4/session
200 OK https://sf-web-wiblum.fe-wiblum.p.azurewebsites.net/files/accounts/ed103462-69db-4bd2-9534-1ce318c2c5e4/session
201 Created https://sf-web-wiblum.fe-wiblum.p.azurewebsites.net/api/accounts/ed103462-69db-4bd2-9534-1ce318c2c5e4/jobs
{
  "id": "4184fcb8-c3e9-443b-b2c7-cac250852aca",
  "name": "readelf2.28",
  "created": "2019-10-31T05:18:53.013Z",
  "fuzzingStarted": null,
  "completed": null,
  "fuzzingDurationInMinutes": 10080,
  "preparationExpirationInMinutes": 20160,
  "runMetadata": null,
  "minimizationInfo": null,
  "osImageArchitecture": "x64",
  "osImageBuild": "7.2",
  "osImageEdition": "Redhat",
  "osImageType": "Linux",
  "osImageRevision": "7.2",
  "osImageBranch": "",
  "osImageIcon": "icons/Redhat.png",
  "supportsRdp": false,
  "isAsan": false,
  "isArchivable": false,
  "isClonable": false,
  "isArchived": false,
  "isActive": true,
  "isDeleted": false,
  "isSubmitted": false,
  "isPreparationVMReady": false,
  "isFuzzing": false,
  "isValidating": false,
  "isInitializing": true,
  "isPreparing": false,
  "isProvisioningPreparationVM": false,
  "isSubmissionPeriodExpired": false,
  "isQuotaExceeded": false,
  "isCloned": false,
  "tierCode": "AflLinux",
  "resultCount": 0,
  "submissionTypeCode": "Package",
  "errorMessage": "",
  "displayedStatus": {
    "displayName": "Initializing",
    "description": "The job entry has been created. No resources are being deployed a this time"
  }
}
(venv) root@SFC-9e82a5e3:~/msrd-rest-samples/Python#
```
