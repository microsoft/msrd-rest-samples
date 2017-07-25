# Springfield-sdk-samples

This repository contains samples of how to programmatically access the Springfield service SDK.

**Prerequisite:**
- Must have a Springfield account enabled for SDK use.
- Must have generated an API Token

*For detailed instructions [click here](https://github.com/Microsoft/springfield-sdk-samples/wiki/Prerequisites)*

---
## Samples

### PowershellSample.ps1

The Powershell script <PowerShellSample.ps1> below accesses the Springfield SDK using its REST API.
It demonstrates how to:
  - Create a job
  - Waits for preparation machine associated with the job to be ready
  - Injects test application to be fuzzed and associated seed files
  - Monitors the job progress until it starts fuzzing
  - Waits until at least one result is reported
  - Deletes the job

The sample below includes parameters of an Azure SubscriptionID and Storage Account.  *Note:  It is not a Springfield requirement to have an Azure subscription or an Azure storage account if the test files are already publically available from an http address.  You can instead upload your binaries and seed files to any internet location accessible from an HTTP URL.*

Calling the Powershell sample:

    . PowershellSample.ps1 `
        -springfieldUri "https://www.microsoftsecurityriskdetection.com" `
        -accountId <The GUID for your account goes here> `
        -apiToken <Your Api token goes here> `
        -subscriptionId <You Azure subscription ID goes here> `
        -storageAccountName <Name of the storage account used to upload the test driver> `
        -storageAccountKey <Your Azure storage account key> `
        -testFileFolder <Path to the local files on disk to be uploaded to the storage account and eventually the VM> `
---

## Swagger interface

Springfield SDK exposes its API through a documented Swagger interface. The URL for the Springfield swagger documentation is

https://www.microsoftsecurityriskdetection.com/swagger

Once navigated to the URL, expand the link 'ServiceApi' found at the top left of the page. The complete list of REST API operations are included there.  The Swagger UI lets you interact with the Springfield service and call the APIs dynamically.

---

*TODO:* Generating proxy class for your favorite languages using the swagger
