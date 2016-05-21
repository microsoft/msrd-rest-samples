#.SYNOPSIS
#   Unpack a .zip file to the spefied target and start 
#   the specified powershell script from the package
#
#.PARAMETER zipFile
#   filename of the zip archive
#.PARAMETER outputDir
#   target directory where to unzip the archive (optional, by default unzip to the system temp directory)
#.PARAMETER scripToRun
#   command to run once the package has been extracted. Expressed as relative to outputDir. 
#.PARAMETER scriptParameters
#   parameters to pass to the script
#
#.EXAMPLE
#   & ./UnzipAndRun.ps1 -zipFile sftemplatetools-2015-10-22.zip -scriptToRun SetupTemplateVm.ps1 -scriptParameters '-skipSysprep -unattend'
#
param(
    [Parameter(Mandatory=$true)]
    $zipfile, 
    $outputDir,
    $scriptToRun,
    $scriptParameters
)  

$ErrorActionPreference='stop'

# Get the executing script directory
$thisScript = $myInvocation.MyCommand.Definition
$thisDir = [System.IO.Path]::GetDirectoryName($thisScript)

$zipFilePath = Join-Path $thisDir $zipfile

if(-not $outputDir) {
    $fileName = [System.IO.Path]::GetFileNameWithoutExtension($zipFilePath)
    $outputDir = "$($Env:ProgramData)\Springfield\setup\$fileName"
}

if(Test-Path $outputDir) {
    rm -force -Recurse $outputDir
}
md $outputDir

[System.Reflection.Assembly]::LoadWithPartialName("System.IO.Compression.FileSystem") | Out-Null
[System.IO.Compression.ZipFile]::ExtractToDirectory($zipFilePath, $outputDir)

rm $zipFilePath
rm $thisScript

$scriptToRunFullPath = Join-Path $outputDir $scriptToRun
try {
    Invoke-Expression "$scriptToRunFullPath $scriptParameters"
} catch {
    throw "Error while running script [$scriptToRunFullPath $scriptParameters]: $_"
}