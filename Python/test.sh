#!/usr/bin/env bash
set -e -o pipefail

. venv/bin/activate
set -u

readonly config='ExampleConfig.json'
readonly job_path='../SampleFuzzingJobs/Demofuzz'
readonly job_params='JobParams.json'

python msrd.py -v \
  --config="${config}" \
  --job_path="${job_path}" \
  --job_params="${job_params}"
