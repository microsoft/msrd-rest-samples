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
