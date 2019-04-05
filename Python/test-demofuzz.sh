#!/usr/bin/env bash
set -e -o pipefail

. venv/bin/activate
set -u

readonly windows_config='Config.json'
readonly windows_job_path='../SampleFuzzingJobs/Demofuzz'
readonly windows_job_params='JobParams.json'
readonly windows_job_os='Windows'
readonly windows_job_os_edition='Server 2008 R2'

python msrd.py -v \
  --config="${windows_config}" \
  --job_path="${windows_job_path}" \
  --job_params="${windows_job_params}" \
  --job_os="${windows_job_os}" \
  --job_os_type="${windows_job_os_type}"

exit

readonly linux_config='ConfigLinux.json'
readonly linux_job_path='../SampleFuzzingJobs/DemofuzzLinux'
readonly linux_job_params='JobParams_Linux.json'
readonly linux_job_os='Linux'
readonly linux_os_edition='Redhat'

python msrd.py -v \
  --config="${linux_config}" \
  --job_path="${linux_job_path}" \
  --job_params="${linux_job_params}" \
  --job_os="${linux_job_os}" \
  --job_os_type="${linux_os_edition}"

# X -> "Linux using Put API" is not supported.
# X -> "Linux using VM Submission" is not supported.
# X -> "Linux using Package Submission and Azure Storage" is supported.

# Untested

# 03a3da09 - failed
# python .\msrd.py -v --config ConfigWindows.json --job_path ../SampleFuzzingJobs/Demofuzz --job_params=JobParams.json --job_os='Windows' --job_os_edition='Server 2008 R2' --storage_type='AZURE' --submission_type='VM'

# Error - No duplicate file allowed
# python .\msrd.py -v --config ConfigWindows.json --job_path ../SampleFuzzingJobs/Demofuzz --job_params=JobParams.json --job_os='Windows' --job_os_edition='Server 2008 R2' --storage_type='API' --submission_type='package'

# ea5fd80c - failed
# python .\msrd.py -v --config ConfigWindows.json --job_path ../SampleFuzzingJobs/Demofuzz --job_params=JobParams.json --job_os='Windows' --job_os_edition='Server 2016 Datacenter' --storage_type='AZURE' --submission_type='VM'

# 9f410943 - success but cant stop it now?
# python .\msrd.py -v --config ConfigWindows.json --job_path ../SampleFuzzingJobs/Demofuzz --job_params=JobParams.json --job_os='Windows' --job_os_edition='Server 2016 Datacenter' --storage_type='AZURE' --submission_type='package'

# Error - No duplicate file allowed
# python .\msrd.py -v --config ConfigWindows.json --job_path ../SampleFuzzingJobs/Demofuzz --job_params=JobParams.json --job_os='Windows' --job_os_edition='Server 2016 Datacenter' --storage_type='API' --submission_type='package'

# 6e907616 - failed
# python .\msrd.py -v --config ConfigLinux.json --job_path ../SampleFuzzingJobs/DemofuzzLinux --job_params=JobParams.json --job_os='Linux' --job_os_edition='Redhat' --storage_type='AZURE' --submission_type='package'

# Error - No duplicate file allowed
# python .\msrd.py -v --config ConfigLinux.json --job_path ../SampleFuzzingJobs/DemofuzzLinux --job_params=JobParams.json --job_os='Linux' --job_os_edition='Redhat' --storage_type='API' --submission_type='package'

# == Works ==
# python .\msrd.py -v --config ConfigWindows.json --job_path ../SampleFuzzingJobs/Demofuzz --job_params=JobParams.json --job_os='Windows' --job_os_edition='Server 2008 R2' --storage_type='AZURE' --submission_type='package'

# == Known to be Unsupported due to incompatability between API storage and submission type, or VM hosts for linux ==
#
# python .\msrd.py -v --config ConfigWindows.json --job_path ../SampleFuzzingJobs/Demofuzz --job_params=JobParams.json --job_os='Windows' --job_os_edition='Server 2008 R2' --storage_type='API' --submission_type='VM'
#
# python .\msrd.py -v --config ConfigWindows.json --job_path ../SampleFuzzingJobs/Demofuzz --job_params=JobParams.json --job_os='Windows' --job_os_edition='Server 2016 Datacenter' --storage_type='API' --submission_type='VM'
#
# python .\msrd.py -v --config ConfigLinux.json --job_path ../SampleFuzzingJobs/DemofuzzLinux --job_params=JobParams.json --job_os='Linux' --job_os_edition='Redhat' --storage_type='API' --submission_type='VM'
# python .\msrd.py -v --config ConfigLinux.json --job_path ../SampleFuzzingJobs/DemofuzzLinux --job_params=JobParams.json --job_os='Linux' --job_os_edition='Redhat' --storage_type='AZURE' --submission_type='VM'
