<#
.SYNOPSIS
    Package and submit a test package for fuzzing to Microsoft Security Risk Detection (MSRD)).
.DESCRIPTION
    Pre-requisites: From the MSRD portal setting page, generate an MSRD API token
    and add it to the Windows Credential Manager with

        cmdkey /generic:MSRD_TOKEN:https://www.microsoftsecurityriskdetection.com /username:me /pass:<INSERT_YOUR_TOKEN_HERE>

    The script takes a JSON file with all the configuration parameters to package and submit the job.
    Running the script for the first time under a directory will create a sample
    JSON file that can be used as a template.

.NOTES
    This script can be configured to run as a VC++ postbuild command by
    setting the post-build step in VC++ project under `Configuration Properties\ Build Events\Post-Build Event`
    with the command-line
        powershell ./SubmitPackageToMSRD.ps1
#>
param(
    # MSRD job configuration file
    $Job = "$PSScriptRoot\MSRDPackageJob.json"
)
$ErrorActionPreference = 'stop'

$JobConfigTemplate = @"
{
    "package" : {
        "name" : "FuzzTargetPackage",
        "app": "Release\\",
        "seeds" : "seedfiles\\"
    },
    "msrdUri" : "https://www.microsoftsecurityriskdetection.com",
    "account" : "<YOU_ACCOUNT_GUID>",
    "jobParameters" : {
        "seedDir": "c:\\FuzzTargetPackage\\seedFiles",
        "seedExtension": ".bin",
        "testDriverExecutable": "c:\\FuzzTargetPackage\\FuzzTarget.exe",
        "testDriverExeType": "x86",
        "testDriverParameters": "\"%testfile%\"",
        "closesItself": true,
        "maxDurationSeconds": 5,
        "runsInLessThan5": true,
        "canRunRepeat": true,
        "canTestDriverBeRenamed": true,
        "singleOsProcess": true,
        "sysprepCompleted": false,
        "promptValidationSysprep": false
    }
}
"@

if (-not (Test-Path $Job)) {
    Write-Warning "MSRD job configuration file not found: $Job. Sample created at '$($Job.sample)'. Edit the file, rename it to '$Job' and try again to submit the job to MSRD."
    $JobConfigTemplate | Set-Content -Path "$Job.sample"
    return
}

Write-Host "Reading MSRD job configuration file $Job"
$jobConfiguration = Get-Content $Job -Raw | ConvertFrom-Json

# URL to the MSRD service. e.g. "https://www.microsoftsecurityriskdetection.com"
$msrdUri = $jobConfiguration.msrdUri

# MSRD Account Id. E.g., fba73e77-cdfd-457d-ae04-d4514483edae
$accountId = $jobConfiguration.account

# MSRD job OS platform edition
$osEdition = $jobConfiguration.osEdition

# MSRD API token obtained from the settings page in MSRD portal
# If not specified the script tries to get the token from the Credential Store under key MSRD_TOKEN
$apiToken = $jobConfiguration.apiToken

# Path to the folder containing the application and seed files to package and fuzz
$sourcePackageApp = $jobConfiguration.package.app

# Path to the folder containing the test seed files
$sourcePackageSeeds = $jobConfiguration.Package.seeds

# Base name of the generated package
$packageBaseName = $jobConfiguration.package.name

# MSRD job parameters (wizard questionaire response)
$jobParameters = $jobConfiguration.jobParameters


Write-Host "[SubmitPackageToMSRD] Job = $Job, packageBaseName = $packageBaseName, sourcePackageApp = $sourcePackageApp, sourcePackageSeeds = $sourcePackageSeeds, msrdUri = $msrdUri, accountId = $accountId, osEdition = $osEdition"

if (-not (Test-Path $sourcePackageApp)) {
    throw "Package app directory does not exist: $sourcePackageApp"
}

if (-not (Test-Path $sourcePackageSeeds)) {
    throw "Package seed directory does not exist: $sourcePackageSeeds"
}


# Read a generic credential password from the Windows Credential Manager for the specified target/address name.
# Adapted from: https://blogs.msdn.microsoft.com/peerchan/2005/11/01/application-password-security-2/
function Get-StoredCredential ($name) {
    $memberDefinition = @"
[StructLayout(LayoutKind.Sequential, CharSet = CharSet.Unicode)]
public struct NativeCredential
{
    public UInt32 Flags;
    public int Type;
    public IntPtr TargetName;
    public IntPtr Comment;
    public System.Runtime.InteropServices.ComTypes.FILETIME LastWritten;
    public UInt32 CredentialBlobSize;
    public IntPtr CredentialBlob;
    public UInt32 Persist;
    public UInt32 AttributeCount;
    public IntPtr Attributes;
    public IntPtr TargetAlias;
    public IntPtr UserName;
}
public class CriticalCredentialHandle : Microsoft.Win32.SafeHandles.CriticalHandleZeroOrMinusOneIsInvalid
{
    public CriticalCredentialHandle(IntPtr preexistingHandle) { SetHandle(preexistingHandle); }
    public string GetPassword() {
        if (!IsInvalid) {
            NativeCredential ncred = (NativeCredential)Marshal.PtrToStructure(handle, typeof(NativeCredential));
            return Marshal.PtrToStringUni(ncred.CredentialBlob, (int)ncred.CredentialBlobSize / 2);
        } else {
            throw new InvalidOperationException("Invalid CriticalHandle!");
        }
    }
    override protected bool ReleaseHandle() {
        if (!IsInvalid) {
            CredFree(handle);
            SetHandleAsInvalid();
        }
        return !IsInvalid;
    }
}
[DllImport("Advapi32.dll", EntryPoint = "CredReadW", CharSet = CharSet.Unicode, SetLastError = true)]
public static extern bool CredRead(string target, int type, int reservedFlag, out IntPtr CredentialPtr);
[DllImport("Advapi32.dll", EntryPoint = "CredFree", SetLastError = true)]
public static extern bool CredFree([In] IntPtr cred);
"@

    Write-Host "Retrieving token from credential store"
    Add-Type -MemberDefinition $memberDefinition -Namespace "ADVAPI32" -Name 'Util' -ErrorAction Stop
    $nCredPtr = New-Object IntPtr
    $success = [ADVAPI32.Util]::CredRead($name, 1, 0, [ref] $nCredPtr)

    if ($success) {
        $critCredHandle = New-Object ADVAPI32.Util+CriticalCredentialHandle $nCredPtr
        return $critCredHandle.GetPassword()
    }
    else {
        Write-Warning "Credential not found for TargetName: $name"
    }
}

if (-not $apiToken) {
    $apiToken = Get-StoredCredential "MSRD_TOKEN:$msrdUri"
}

if (-not $apiToken) {
    $apiToken = Get-StoredCredential "MSRD_TOKEN"
}

if (-not $apiToken) {
    throw "MSRD token missing. Make sure to set the MSRD API token in the credential store under key MSRD_TOKEN:$msrdUri"
}

if (-not $packageBaseName) {
    $packageBaseName = [System.IO.Path]::GetFileNameWithoutExtension($jobParameters.testDriverExecutable)
}

$testTargetLocation = [System.IO.Path]::GetDirectoryName($jobParameters.testDriverExecutable)
$testZipPath = Join-Path ([System.IO.Path]::GetTempPath()) "$packageBaseName.zip"

Write-host "Zipping $sourcePackageApp and $sourcePackageSeeds into $testZipPath"
Compress-Archive -Path $sourcePackageApp, $sourcePackageSeeds -DestinationPath $testZipPath -Force

$headers = @{
    "SpringfieldApiToken" = $apiToken
    "Content-Type"        = "application/json"
}

function Invoke-Rest (
    [Microsoft.PowerShell.Commands.WebRequestMethod] $method,
    [System.Uri] $uri,
    [System.Object] $Body = $null,
    [switch] $Verbose
) {
    $response = Invoke-WebRequest -Method $method -Uri $uri -Headers $headers -Body $Body -ContentType "application/json" -Verbose:$Verbose
    if ($response.StatusCode -lt 200 -or $response.StatusCode -ge 300) {
        throw "Request failed: $($response.RawContent) with status code $($response.StatusCode)"
    }
    elseif ($response.RawContentLength -gt 0) {
        return ConvertFrom-Json $response.Content
    }
}

Write-Host "Retrieving list of MSRD supported OS platforms"
$osImages = Invoke-Rest -Method GET -Uri "$msrdUri/api/accounts/$accountId/osimages" -Verbose
Write-Host "Supported OS platforms: $($osImages.osEdition)"
$os = $osImages | Where-Object { $_.osEdition -eq $osEdition } | Select-Object -First 1
if (-not $os) {
    throw "Requested OS edition not supported by this MSRD account: $osEdition"
}

Write-Host "Uploading package to MSRD..."
$response = Invoke-WebRequest -Headers $headers -Method POST -Uri "$msrdUri/api/accounts/$accountId/files" -InFile $testZipPath -ContentType 'multipart/form-data' -Verbose:$Verbose
if ($response.StatusCode -lt 200 -or $response.StatusCode -ge 300) {
    throw "Request failed: $($response.RawContent)"
}
$uploadedPackage = ConvertFrom-Json $response.Content

Write-Host "Submitting fuzzing job to MSRD"
$submissionParameters = @{
    name   = "Package $packageBaseName by $($Env:USERNAME) from $($Env:COMPUTERNAME)"
    setup  = @{
        package = @{
            command           = ''
            destinationFolder = $testTargetLocation
            fileInformations  = @(
                @{
                    name   = "$packageBaseName.zip"
                    url    = $uploadedPackage.fileUrl
                    action = "Unzip"
                }
            )
        }
    }
    submit = @{
        testDriverParameters = $jobParameters
    }
} | ConvertTo-Json -Depth 5
Write-Host "Job parameters: $submissionParameters"
$jobInfo = Invoke-Rest -Method POST -Uri "$msrdUri/api/accounts/$accountId/jobs?osImageId=$($os.Id)&submissionType=package" -Verbose:$Verbose -Body $submissionParameters

Write-Verbose "Jobinfo: $jobInfo"

Write-Host -ForegroundColor Green "Microsoft Security Risk Detection Fuzzing Job created with ID $($jobInfo.Id)"

Write-Host "You can view the MSRD job at $msrdUri/accounts/$accountId/jobs/$($jobInfo.Id)"
