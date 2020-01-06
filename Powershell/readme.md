# Submitting fuzzing jobs using the MSRD REST API via Powershell

MSRD supports two modes of job submissions: VM-based and package-based.
The Powershell scripts under this folder demonstrate how to submit jobs with each method.
For automated submission, the Package-based submission is preferred.
It is faster since no VM needs to be created, but does require you to automate
the installation and configuration of your test target.
The VM-based submission is slower overall but lets you connect to the VM
and manually configure the virtual machine before submitting the job.

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

## Submitting an ASAN-compiled test targets

To submit a test target compiled with the new [MSVC Address Sanitizer](https://devblogs.microsoft.com/cppblog/addresssanitizer-asan-for-windows-with-msvc/) library (VCAsan)
you need to first make sure that your MSRD account is enabled for it; contact the MSRD support team if you are not sure at msrd@microsoft.com.
Then add the following fields to the `jobParameters` section of the Json file:

```json
"jobParameters" : {
     "..." : "...",
     "ignoreFirstChanceExceptions": true,
     "options": {
            "asanOptions": "windows_hook_rtl_allocators=true",
            "asanSaveDumps": "true",
            "disableAppVerifier": "true",
            "useNewWindowsExecutionEngine": "true"
     }
}
```

You can refer to `MSRDPackageJob-ASAN.json` as a template, which assumes that your ASAN-compiled
test target is located at `MyVcAsanTarget\MyVcAsanTarget.exe`.
Sample ASAN-built binaries are not currently provided in our sample Git repository, so you
will need to compile your own sample using Visual Studio 16.4 or later with the `/fsanitize` compiler switch enabled.

To submit the job to MSRD then just run:

```batch
powershell ./SubmitPackageToMSRD.ps1 -Job MSRDPackageJob-ASAN.json
```

## Alternative script to submit jobs and poll for results

Alternatively, you can use the other Powershell script `PowerShellSample.ps1` to submit jobs to MSRD.
This script performs the following:

- Create a job (either Package-based or VM-based)
- If VM-based, waits for preparation machine associated with the job to be ready
- Injects test application to be fuzzed and associated seed files
- Monitors the job progress until it starts fuzzing
- Waits until at least one result is reported
- Deletes the job

### Usage for `PowershellSample.ps1`

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

> NOTE: Although this sample includes Azure Subscription ID and Storage Account parameters,
it is not a MSRD requirement to have an Azure subscription or an Azure storage account
if the test files are already publicly available from an HTTP address.
You can instead upload your binaries and seed files to any internet location accessible from HTTP.
