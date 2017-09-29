<#
.SYNOPSIS
    This script demonstrate how to use the Springfield service from Powershell
    via the Springfield REST API.
.DESCRIPTION
  The script performs the following:
    - Create a Springfield job
    - Wait for preparation machine associated with the job to be ready
    - Inject test application to be fuzzed and associated seed files into the virtual machine
    - Submit the job
    - Monitor the job progress until it starts fuzzing
    - Wait until at least one result is reported
    - Delete the job
.REMARK
    The API token can be generated from the Springfield website on the setting page
#>
param(
    # URL to the Springfield service
    $springfieldUri = "https://www.microsoftsecurityriskdetection.com",

    # Springfield Account Id
    [Parameter(Mandatory=$true)]
    $accountId,

    # Springfield API token obtained from the settings page in Springfield portal
    [Parameter(Mandatory=$true)]
    $apiToken,

    # Azure subscription ID
    [Parameter(Mandatory=$true)]
    $subscriptionId,

    # The path to the folder containing the application and seed files to fuzz
    [Parameter(ParameterSetName='uploadBinariesToStorageAccount')]
    $testFileFolder = "$PSScriptRoot\..\SampleFuzzingJobs\Demofuzz",

    # Name of Azure storage account where to upload the test payload
    [Parameter(Mandatory=$true, ParameterSetName='uploadBinariesToStorageAccount')]
    $storageAccountName,

    # Azure storage account key
    [Parameter(Mandatory=$true, ParameterSetName='uploadBinariesToStorageAccount')]
    $storageAccountKey,

    # The name of the container in the storage account where the binaries will be uploaded.
    [Parameter(ParameterSetName='uploadBinariesToStorageAccount')]
    $containerName = "sample",

    # The list of urls containing the application to be fuzzed and its dependencies
    # The content at these urls will be downloaded to the fuzzing machine
    [Parameter(Mandatory=$true, ParameterSetName='testFileFolderUrl')]
    [Uri[]] $testFileUrls,

    # Optional command to execute before the submission of the job
    # this can be used to copy the the files to a specific location for example
    $preSubmissionCommand =
        "powershell.exe -ExecutionPolicy Unrestricted -Command `"" +
        "`$ErrorActionPreference='stop'; " +
        "`$zipFilePath = Join-Path (pwd).Path Demofuzz.zip; " +
        "`$outputDir = 'c:\DemoFuzz'; " +
        "if(Test-Path `$outputDir) { " +
            "rm -force -Recurse `$outputDir " +
        "} ;" +
        "md `$outputDir ;" +
        "[System.Reflection.Assembly]::LoadWithPartialName('System.IO.Compression.FileSystem') | Out-Null; " +
        "[System.IO.Compression.ZipFile]::ExtractToDirectory(`$zipFilePath, `$outputDir)`"" ,

    # Set of job parameters. This correspond to the answer to the wizard's questionnaire
    $jobParameters = @{
        seedDir = 'c:\DemoFuzz\Data'
        seedExtension = '.bin'
        testDriverExecutable = 'c:\DemoFuzz\demofuzz.exe'
        testDriverExeType = 'x86'
        testDriverParameters = '"%testfile%"'
        closesItself = $true
        maxDurationSeconds = 5
        runsInLessThan5 = $true
        canRunRepeat = $true
        canTestDriverBeRenamed = $true
        singleOsProcess = $true
        sysprepCompleted = $false
        promptValidationSysprep = $false
    },

    # Wether or not th job should be deleted after the first result is received
    [switch] $deleteJobAfterTheFirstResult
)

<#
.SYNOPSIS
    Helper function used to upload  files as blob to the azure storage account
#>
function UploadFileToAzure (
    # Path to the file to be uploaded to the storage account
    [Parameter(Mandatory=$true)] $sourceFileName
) {
    $destContext = New-AzureStorageContext -StorageAccountName $storageAccountName -StorageAccountKey $storageAccountKey
    $container = Get-AzureStorageContainer -Context $destContext -Name $containerName -ErrorAction SilentlyContinue
    if(-not $container) {
        $container = New-AzureStorageContainer -Name $containerName -Context $destContext
    }
    $blobName = Split-Path $sourceFileName -Leaf
    $blob = Set-AzureStorageBlobContent -Context $destContext -Container $containerName -File $sourceFileName -Blob $blobName -Force
    $blobSas = New-AzureStorageBlobSASToken -Context $destContext -Container $containerName -Blob $blobName -Permission r -FullUri -ExpiryTime ([System.DateTime]::Now.AddHours(1))
    Write-Host "Blob SAS: $blobSas"
    return $blobSas
}

<#
.SYNOPSIS
    Zip the test payload and add an script into the archive
    to automate job submission from the VM.
#>
function CreateTestZipFile(
    # Path to the source directory containing the test payload
    [Parameter(Mandatory=$true)] $testFileFolder,
    # The parameters of the job
    [Parameter(Mandatory=$true)] $jobParameters
) {
    # Extract name of sample from directory name
    $sampleName = $(Split-Path $testFileFolder -Leaf)

    Write-Host "Creating zip file containing the application to test"

    $tmpDir = [System.IO.Path]::GetTempFileName()
    Remove-Item $tmpDir
    $dir = mkdir $tmpDir

    # Copy test driver and seed files
    Copy-Item $testFileFolder $tmpDir -Recurse
    $testZipPath = "$tmpDir\$sampleName.zip"
    $directoryToZip = "$tmpDir\$sampleName"


    Add-Type -assembly "system.io.compression.filesystem"
    if (Test-Path $testZipPath){
        Write-host "$testZipPath already exist: removing it"
        Remove-Item $testZipPath
    }

    Write-host "Zipping folder $directoryToZip into $testZipPath"
    [io.compression.zipfile]::CreateFromDirectory($directoryToZip, $testZipPath)
    return $testZipPath
}

if ($testFileUrls) {
    $dependencyUris = $testFileUrls
} else {
    #####
    # Preparing the test payload to be copied onto the VM. This includes test driver binaries, seed files
    # and the job parameters (a Json blob containing answers to the wizard's questions)
    $testZipPath = CreateTestZipFile -testFileFolder $testFileFolder -jobParameters $jobParameters

    #####
    # Upload all the test files to the azure storage account
    Import-Module AzureRm.Storage
    $account = Login-AzureRmAccount -SubscriptionId $subscriptionId

    Write-Host "Uploading the archive with the test payload to a storage account"
    $dependencyUris = `
        @(
            UploadFileToAzure $testZipPath
            # You can add any URL to files to be uploaded to the VM here
        )
}

#####
# Create the Springfield Job and monitor progress
$pollingIntervalInSeconds = 60*1

$headers = @{
    "SpringfieldApiToken" = $apiToken
    "Content-Type" ="application/json"
    }

function Invoke-Rest(){
    param(
        [Microsoft.PowerShell.Commands.WebRequestMethod] $method,
        [System.Uri] $uri,
        [System.Object] $Body = $null,
        [string] $ContentType = "application/json",
        [switch] $Verbose)
    $result = Invoke-WebRequest -Method $method -Uri $uri -Headers $headers -Body $Body -ContentType $ContentType -Verbose:$Verbose
    if ($result.StatusCode -ge 200 -and $result.StatusCode -lt 300  ){
        if ($result.RawContentLength -gt 0) {
            return ConvertFrom-Json $result.Content
        } else {
            return ""
        }
    } else{
        throw "Request failed: $($result.RawContent)"
    }
}

$osImages = Invoke-Rest -Method GET -Uri "$springfieldUri/api/accounts/$accountId/osimages" -Verbose

Write-Host "Creating a job"
$jobInfo = Invoke-Rest -Method POST -Uri "$springfieldUri/api/accounts/$accountId/jobs?osImageId=$($osImages[0].Id)" -Verbose

$jobId = $jobInfo.Id
Write-Host "Job $jobId created"

while (-not $jobInfo.IsPreparationVMReady) {
    Write-Host "Waiting for the preparation vm to be ready"
    Start-Sleep -Seconds $pollingIntervalInSeconds
    $jobInfo = Invoke-Rest -Method GET -Uri "$springfieldUri/api/accounts/$accountId/jobs/$jobId" -Verbose
}

Write-Host "Retrieving the machine name"
$machineName = Invoke-Rest -Method GET -Uri "$springfieldUri/api/accounts/$accountId/jobs/$jobId/customermachine" -Verbose
Write-Host "Machine name $machineName retrieved"

# Preparing the command to execute on the job preparation machine
if (-not $preSubmissionCommand) {
    $preSubmissionCommand = "echo No Pre Submission command"
}
$createTheJobParameterFile = "echo $($jobParameters | ConvertTo-Json -Compress) > c:\Springfield\JobParams.json"
$submitTheJob = "c:\Springfield\Wizard\Springfield.Prevalidation.UI.Console.exe -unattend"

$commandParams = @{
    "command" = "$preSubmissionCommand & $createTheJobParameterFile & $submitTheJob"
    "dependencyUris" = $dependencyUris
} | ConvertTo-Json

Write-Host "Submitting command for execution $commandParams"
$commandInfo = Invoke-Rest -Method POST -Uri "$springfieldUri/api/accounts/$accountId/jobs/$jobId/machines/$machineName/command" -Body $commandParams -ContentType 'application/json' -Verbose
Write-Host "Command execution sent: $commandInfo"

while ($commandInfo.ExecutionState.IsPendingState) {
    Write-Host "Waiting for the command to finish executing"
    Start-Sleep -Seconds $pollingIntervalInSeconds
    $commandInfo = Invoke-Rest -Method GET -Uri "$springfieldUri/api/accounts/$accountId/jobs/$jobId/machines/$machineName/command/$($commandInfo.CommandId)" -Verbose
}

if ($commandInfo.ExecutionState.IsErrorState) {
    throw "Error during execution of custom command : $($commandInfo.ExecutionState.GetError)"
}

Write-Host "Monitoring command job status until fuzzing or error"
while (-not $jobInfo.IsFuzzing) {
    Write-Host "Waiting for the job to start fuzzing"
    Start-Sleep -Seconds $pollingIntervalInSeconds
    $jobInfo = Invoke-Rest -Method GET -Uri "$springfieldUri/api/accounts/$accountId/jobs/$jobId" -Verbose
}

Write-Host "Poll until we get at least one result"
$results = Invoke-Rest -Method GET -Uri "$springfieldUri/api/accounts/$accountId/jobs/$jobId/results" -Verbose

while ($results.Count -eq 0){
    Start-Sleep -Seconds $pollingIntervalInSeconds
    $results = Invoke-Rest -Method GET -Uri "$springfieldUri/api/accounts/$accountId/jobs/$jobId/results" -Verbose
}

Write-Host "Got $($results.Count) results $results"
Write-Host "Deleting the job"

if ($deleteJobAfterTheFirstResult) {
    Invoke-Rest -Method DELETE -Uri "$springfieldUri/api/accounts/$accountId/jobs/$jobId" -Verbose
}
