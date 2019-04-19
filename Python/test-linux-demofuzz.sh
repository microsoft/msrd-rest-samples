#!/usr/bin/env bash
set -e -o pipefail

. venv/bin/activate
set -u

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
