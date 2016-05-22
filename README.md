# springfield-sdk-samples

This repository contains samples showing how to programmatically access the Springfield service SDK.

## Obtaining an SDK token

Contact the Springfield team at fuzzing@microsoft.com to have your Springfield account enabled for SDK use.
- Login to your Springfield account
- Click on 'Settings' at the top right corner og the page
- Under 'API Tokens' enter a token name, an expiration period and click add
- A dialog box shows up with the generated token. Keep note of it and save it for later.

## Samples

### PowershellSample.ps1

The Powershell script <PowerShellSample.ps1> shows how to programmatically access the Springfield SDK using its REST API.
This sample demonstrates how to do the following:
  - Create a job 
  - Wait for preparation machine associated with the job to be ready 
  - Inject test application to be fuzzed and associated seed files
  - Monitor the job progress until it starts fuzzing
  - Wait until at least one result is reported
  - Delete the job 

The sample requires you to have an Azure subscription and a storage account. This is used to upload the test driver 
and test files to the Springfield VM. If you don't have an Azure subscription you can instead upload your binaries and seed files
to any internet location accessible from an HTTP URL.

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

### TODO: Generating proxy class for your favourite languages using the swagger

