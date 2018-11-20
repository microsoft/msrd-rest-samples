
### MSRD REST API - Powershell Sample

The Powershell script `PowerShellSample.ps1` below demonstrates how to access MSRD REST API:
  - Create a job
  - Waits for preparation machine associated with the job to be ready
  - Injects test application to be fuzzed and associated seed files
  - Monitors the job progress until it starts fuzzing
  - Waits until at least one result is reported
  - Deletes the job

> NOTE: Although this sample includes Azure Subscription ID and Storage Account parameters, 
it is not a MSRD requirement to have an Azure subscription or an Azure storage account 
if the test files are already publicly available from an http address.  
You can instead upload your binaries and seed files to any internet location accessible from an HTTP URL.

### Usage:

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
