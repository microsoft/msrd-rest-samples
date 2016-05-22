<#
.SYNOPSIS
    This script demonstrate how to use the Springfield service from Powershell

.NOTE
    The API token can be generated from the Springfield website on the setting page
#>
param(
    # URL to the Springfield service
    $springfieldUri = "https://www.alamosand.azurewebsites.net",
    
    # Springfield Account Id
    [Parameter(Mandatory=$true)]
    $accountId,
    
    # Springfield API token obtained from the settings page in Springfield portal
    [Parameter(Mandatory=$true)]
    $apiToken,
    
    # The Azure subscription ID
    [Parameter(Mandatory=$true)]
    $subscriptionId,
    
    # Resource group containing the stroage account
    [Parameter(Mandatory=$true)]
    $resourceGroup,

    # The resource group of the storage account
    [Parameter(Mandatory=$true)]
    $storageAccountName,

    # The key of the storageAccount
    [Parameter(Mandatory=$true)]
    $storageAccountKey,

    # The path to the folder containing the application to fuzz
    $testFileFolder="$PSScriptRoot\..\SampleFuzzingJobs\Demofuzz",

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
    } 

)

# Extract name of sample from directory name
$sampleName = $(Split-Path $testFileFolder -Leaf)


<#
.SYNOPSIS
    Helper function used to upload  files as blob to the azure storage account
#>
function UploadFileToAzure (
    # Path to the file to be uploaded to the storageAccount
    [Parameter(Mandatory=$true)] $sourceFileName
) {

    $targetStorage = Get-AzureRmStorageAccount -Name $storageAccountName -ResourceGroupName $resourceGroup

    $destContext = New-AzureStorageContext -StorageAccountName $storageAccountName -StorageAccountKey $storageAccountKey

    $containerName = "sample"
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
    Compress the test file to zip and inject an install script into the archive
#>
function CreateTestZipFile(
    # Path to the source directory containing the test payload
    [Parameter(Mandatory=$true)] $testFileFolder,
    # The paramters of the job
    [Parameter(Mandatory=$true)] $jobParameters
) {
    Write-Host "Creating zip file containing the application to test"

   $installScriptContent = @"
        '$($jobParameters | ConvertTo-Json)' | Set-Content c:\Springfield\JobParams.json
        & c:\Springfield\Springfield.Prevalidation.UI.Console\Springfield.Prevalidation.UI.Console.exe -unattend
"@

    $tmpDir = [System.IO.Path]::GetTempFileName()
    rm $tmpDir
    $dir = md $tmpDir
    Copy-Item $testFileFolder $tmpDir -Recurse
    $testZipPath = "$tmpDir\$sampleName.zip"
    $directoryToZip = "$tmpDir\$sampleName"

    Set-Content -Path "$directoryToZip\install.ps1" -Value $installScriptContent
    
    Add-Type -assembly "system.io.compression.filesystem"
    
    if (Test-Path $testZipPath ){
        Write-host "$testZipPath already exist: removing it"
        Remove-Item $testZipPath
    }

    Write-host "Zipping folder $directoryToZip into $testZipPath"
    [io.compression.zipfile]::CreateFromDirectory($directoryToZip, $testZipPath)
    return $testZipPath
}

<#
.SYNOPSIS
    This function shows how to interact with the Springfield service via the SDK
.DESCRIPTION
  The function does the following:
    - Create a job 
    - Wait for preparation machine associated with the job to be ready 
    - Inject test application to be fuzzed and associated seed files
    - Monitor the job progress until it starts fuzzing
    - Wait until at least one result is reported
    - Delete the job 
#>
function CreateAndMonitorJob {
    param(
        # The list of uris of the dependencies that needs to be donwloaded on the preparation machine 
        [Parameter(Mandatory=$true)] $dependencyUris
    )
    
    $uri = $springfieldUri

    $pollingInternavalInSeconds = 60*3
    
    $headers = @{
        "SpringfieldApiToken" = $apiToken 
        "Content-Type" ="application/json"
        }

    $osImages = Invoke-RestMethod -Method GET -Uri "$uri/api/accounts/$accountId/osimages" -Headers $headers -Verbose
    
    Write-Host "Creating a job"
    $jobInfo = Invoke-RestMethod -Method POST -Uri "$uri/api/accounts/$accountId/jobs?osImageId=$($osImages[0].Id)" -Headers $headers -Verbose

    $jobId = $jobInfo.Id
    Write-Host "job $jobId created"
    
    while (-not $jobInfo.IsPreparationVMReady) {
        Write-Host "Waiting for the preparation vm to be ready"
        Start-Sleep -Seconds $pollingInternavalInSeconds
        $jobInfo = Invoke-RestMethod -Method GET -Uri "$uri/api/accounts/$accountId/jobs/$jobId" -Headers $headers -Verbose
    }

    Write-Host "Retrieving the machine name"
    $machineName = Invoke-RestMethod -Method GET -Uri "$uri/api/accounts/$accountId/jobs/$jobId/customermachine" -Headers $headers -Verbose
    Write-Host "Machine name $machineName retrieved"
    
    # The command to execute on the job preparation machine 
    $executionCommand = "powershell.exe -ExecutionPolicy Unrestricted -Command `".\UnzipAndRun.ps1 -zipFile $sampleName.zip -scriptToRun install.ps1 -outputDir 'c:\$sampleName'`""

    $commandParams = @{
        "command" = $executionCommand
        "dependencyUris" = $dependencyUris
    } | ConvertTo-Json

    Write-Host "Submitting command for execution $commandParams"
    $commandInfo = Invoke-RestMethod -Method POST -Uri "$uri/api/accounts/$accountId/jobs/$jobId/machines/$machineName/command" -Headers $headers -Body $commandParams -ContentType 'application/json' -Verbose

    while ($commandInfo.ExecutionState.IsPendingState) {
        Write-Host "Waiting for the command to finish executing"
        Start-Sleep -Seconds $pollingInternavalInSeconds
        $commandInfo = Invoke-RestMethod -Method GET -Uri "$uri/api/accounts/$accountId/jobs/$jobId/machines/$machineName/command/$($commandInfo.CommandId)" -Headers $headers -Verbose
    }

    if ( $commandInfo.ExecutionState.IsErrorState ) {
        throw "Error during execution of custom command : $($commandInfo.ExecutionState.GetError)"
    }

    Write-Host "Monitoring command job status until fuzzing or error"
    while (-not $jobInfo.IsFuzzing ) {
        Write-Host "Waiting for the job to start fuzzing"
        Start-Sleep -Seconds $pollingInternavalInSeconds
        $jobInfo = Invoke-RestMethod -Method GET -Uri "$uri/api/accounts/$accountId/jobs/$jobId" -Headers $headers -Verbose
    }

    Write-Host "Poll until we get at least one result"
    $results = Invoke-RestMethod -Method GET -Uri "$uri/api/accounts/$accountId/jobs/$jobId/results" -Headers $headers -Verbose

    while ($results.Count -eq 0){
        Start-Sleep -Seconds $pollingInternavalInSeconds
        $results = Invoke-RestMethod -Method GET -Uri "$uri/api/accounts/$accountId/jobs/$jobId/results" -Headers $headers -Verbose
    }
    
    Write "Got $($results.Count) results $results"
    Write-Host "Deleting the job"

    Invoke-RestMethod -Method DELETE -Uri "$uri/api/accounts/$accountId/jobs/$jobId" -Headers $headers -Verbose
}

##### Login into Azure
Import-Module AzureRm.Storage
$account = Login-AzureRmAccount -SubscriptionId $subscriptionId

#####
# Preparing the test payload to be copied onto the VM. This includes test driver binaries, seed files
# and the job prameters (a Json blob containing answer to the wizard's questions)
$testZipPath = CreateTestZipFile -testFileFolder $testFileFolder -jobParameters $jobParameters


#####
# Upload all the test files to the azure storage account
Write-Host "Uploading the zip file contianing the application to test"
$dependencyUris = `
    @(
        UploadFileToAzure $testZipPath
        UploadFileToAzure "$PSScriptRoot\UnzipAndRun.ps1"
        # You can add any URL to files to be uploaded to the VM here
    )

#####
# Create the Springfield Job and monitor progress
CreateAndMonitorJob $dependencyUris 