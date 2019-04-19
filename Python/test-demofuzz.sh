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
