# Springfield-sdk-samples

This repository contains samples of how to programmatically access the Springfield service SDK.  Please review and complete the prerequisites found in the Wiki page.

## Samples

### PowershellSample.ps1

The Powershell script <PowerShellSample.ps1> below accesses the Springfield SDK using its REST API.
This sample demonstrates how to:
  - Create a job 
  - Waits for preparation machine associated with the job to be ready 
  - Injects test application to be fuzzed and associated seed files
  - Monitors the job progress until it starts fuzzing
  - Waits until at least one result is reported
  - Deletes the job 

The sample below includes parameters of an Azure subscription and storage account. These are used to upload the test driver and test files to the Springfield VM. 

Note:  It is not a requirement to have an Azure subscription or an Azure storage account if the test files are already publically available from an http address.  You can instead upload your binaries and seed files to any internet location accessible from an HTTP URL.  

Calling the Powershell sample:

    . PowershellSample.ps1 `
        -springfieldUri "https://www.alamohendersonville.com" `
        -accountId <The GUID for your account goes here> `
        -apiToken <Your Api token goes here> `
        -subscriptionId <You Azure subscription ID goes here> `
        -storageAccountName <Name of the storage account used to upload the test driver> `
        -storageAccountKey <Your Azure storage account key> `
        -testFileFolder <Path to the local files on disk to be uploaded to the storage account and eventually the VM> `

## Swagger interface

Springfield SDK exposes its API through a documented Swagger interface. The URL for the Springfield swagger documentation is

https://www.alamohendersonville.com/swagger

Navigate to this URL and expand the 'ServiceApi' node. The list of REST API operations are listed there.
The Swagger UI lets you interact with the service and call the API dynamically.

### TODO: Generating proxy class for your favorite languages using the swagger
