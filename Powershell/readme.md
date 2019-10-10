# MSRD REST API - Powershell Sample

MSRD supports two modes of job submissions: VM-based and package-based.
The Powershell scripts under this folder demonstrate how to submit jobs with each method.
For automated submission, the Package-based submission is preferred.
It is faster since no VM needs to be created, but does require you to automate
the installation and configuration of your test target.
Whereas the VM-based submission gives you the ability to connect to the VM and manually configure the test target before submitting the job.

## Package-based job submission

This sample demonstrate how to submit a Package-based job to MSRD using the REST API.

## Instructions

1 - Create a JSON file based off `Demofuzz-package.json` and change the fields to point to your executable, seed files and MSRD account guid

- Set `msrdUri` to the URL to MSRD instance you are targetting;
- Set `account` fields to your MSRD account Guid;
- To submit your own test target instead of the demo sample: update fields `package.app` and `package.seeds` to point to your local test target binary folder and seeds folder.

2 - Generate an MSRD API token from the MSRD website setting page
    and add it to the Windows Credential Manager:

```batch
cmdkey /generic:MSRD_TOKEN:https://www.microsoftsecurityriskdetection.com /username:me /pass:<INSERT_YOUR_TOKEN_HERE>
```

3 - Run the script to submit the job to MSRD

```batch
powershell ./SubmitPackageToMSRD.ps1
```

## VM-based submission with result polling

The Powershell script `PowerShellSample.ps1` demonstrates how to access MSRD REST API
to perform the following:

- Create a job (either Package-based or VM-based)
- Waits for preparation machine associated with the job to be ready
- Injects test application to be fuzzed and associated seed files
- Monitors the job progress until it starts fuzzing
- Waits until at least one result is reported
- Deletes the job

> NOTE: Although this sample includes Azure Subscription ID and Storage Account parameters,
it is not a MSRD requirement to have an Azure subscription or an Azure storage account
if the test files are already publicly available from an HTTP address.
You can instead upload your binaries and seed files to any internet location accessible from HTTP.

### Usage

```powershell
. PowershellSample.ps1 `
      -springfieldUri "https://www.microsoftsecurityriskdetection.com" `
      -accountId <The GUID for your account goes here> `
      -apiToken <Your Api token goes here> `
      -subscriptionId <You Azure subscription ID goes here> `
      -storageAccountName <Name of the storage account used to upload the test driver> `
      -storageAccountKey <Your Azure storage account key> `
      -testFileFolder <Path to the local files on disk to be uploaded to the storage account and eventually the VM> `
```

