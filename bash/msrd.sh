#!/usr/bin/env bash

# Check if the user is invoking the script under `bash`, vs. e.g. `sh`.
if [ -z "${BASH_VERSION}" ]; then
  echo 'ERROR: not using `bash` shell\n' >&2
  echo 'This script uses features specific to the `bash` shell.\n' >&2
  echo 'Please run this script using `bash msrd.sh` or `./msrd.sh`.' >&2
  exit 1
fi

# Fail fast on errors.
set -e -o pipefail

# Base origin of the MSRD environment in use, here set to production.
readonly MSRD_ORIGIN='https://www.microsoftsecurityriskdetection.com'

# User auth data used in MSRD API requests.
readonly ACCOUNT_ID='!!! set to your account ID'
readonly API_TOKEN='!!! set to a valid API token'

# Local location of the folder containing the fuzz target. The fuzz target must
# be an executable whose preparation VM location is set in `JobParams.json`.
readonly TARGET_PATH='../SampleFuzzingJobs/DemofuzzLinux'

# Name of the fuzz target, used for paths the prep VM.
readonly TARGET_NAME="$(basename ${TARGET_PATH})"

# Path to seeds for the fuzz target, which all must share a suffix that is also
# specified in `JobParams.json`.
readonly TARGET_SEED_PATH='../SampleFuzzingJobs/DemofuzzLinux/Data'

readonly API_BASE_URL="${MSRD_ORIGIN}/api/accounts/${ACCOUNT_ID}"


# Log an error and exit with a non-zero code.
error() {
  local ts=$(date -I)
  echo "[ERROR][${ts}]" "$@" >&2
  exit 1
}

# Log non-error information.
info() {
  local ts=$(date -Is)
  echo "[INFO][${ts}]" "$@" >&2
}

# Make an authenticated HTTP GET request to the MSRD API.
msrd_get() {
  local accept_header='Accept: application/json'
  local content_type_header='Content-Type: application/json'
  local api_token_header="SpringfieldApiToken: ${API_TOKEN}"

  curl -H "${accept_header}" \
       -H "${content_type_header}" \
       -H "${api_token_header}" \
       $@ \
       2>/dev/null
}

# Make an authenticated HTTP POST request to the MSRD API.
msrd_post() {
  local accept_header='Accept: application/json'
  local content_type_header='Content-Type: application/json'
  local api_token_header="SpringfieldApiToken: ${API_TOKEN}"

  curl -X POST \
       -H "${accept_header}" \
       -H "${content_type_header}" \
       -H "${api_token_header}" \
       $@ \
       2>/dev/null
}

# Get account info for $ACCOUNT_ID.
fetch_account_info() {
  local url="${API_BASE_URL}"

  msrd_get "${url}"
}

# Get OS images available to $ACCOUNT_ID.
fetch_available_os_images() {
  local url="${API_BASE_URL}/osimages"

  msrd_get "${url}"
}

# Get the ID of a Linux OS image, if one is available to the account. This
# function assumes that any Linux OS image found will work for the fuzz target,
# and doesn't check architecture, distro, &c.
fetch_linux_os_image_id() {
  # Fetch remote list of all available OS images.
  local os_images=$(fetch_available_os_images)

  # Filter to select only the first Linux OS image.
  local linux_os_images=$(echo "${os_images}" | jq '.[] | first(select(.osType == "Linux"))')

  # Get ID of first in list.
  echo ${linux_os_images} | jq -r '.id'
}

# Create a new Linux job from a given Linux OS image ID.
create_linux_job() {
  local linux_os_image_id=$1
  local url="${API_BASE_URL}/jobs?osImageId=${linux_os_image_id}&submissionType=Normal"

  msrd_post "${url}" -d {}
}

# Check if the preparation VM for $job_id is ready for login.
check_machine_ready() {
  local job_id="$1"
  local url="${API_BASE_URL}/jobs/${job_id}/machineready"

  msrd_get "${url}"
}

# Copy files to the preparation VM.
copy_to_vm() {
  local job_id=$1
  local src=$2
  local dst=$3

  local prep_vm_creds=$(cat "${job_id}/prep-creds.json")

  local username=$(echo ${prep_vm_creds} | jq -r '.username')
  local password=$(echo ${prep_vm_creds} | jq -r '.password')
  local prep_vm_addr=$(echo ${prep_vm_creds} | jq -r '.ipAddress')
  local port=$(echo ${prep_vm_creds} | jq -r '.port')

  sshpass -p "${password}" \
          scp -o "UserKnownHostsFile ${job_id}/known_hosts" \
          -P "${port}" \
          -r \
          "${src}" "${username}@${prep_vm_addr}:${dst}"
}

# Execute a command on the preparation VM.
vm_command() {
  job_id=$1
  shift
  local prep_vm_creds=$(cat "${job_id}/prep-creds.json")

  local username=$(echo ${prep_vm_creds} | jq -r '.username')
  local password=$(echo ${prep_vm_creds} | jq -r '.password')
  local prep_vm_addr=$(echo ${prep_vm_creds} | jq -r '.ipAddress')
  local port=$(echo ${prep_vm_creds} | jq -r '.port')

  sshpass -p "${password}" \
          ssh -o "UserKnownHostsFile ${job_id}/known_hosts" \
          -p "${port}" \
          "${username}@${prep_vm_addr}" \
          -- $@
}

# Fetch the credentials for preparation VM SSH access.
fetch_prep_vm_creds() {
  local url="${API_BASE_URL}/jobs/${job_id}/RemoteAccess"

  msrd_get "${url}"
}

# Check that a single script dependency is in the $PATH.
check_dep() {
  local dep="$1"

  info "    checking for \`${dep}\`..."
  if [[ ! $(which "${dep}") ]]; then
    error "please install \`${dep}\` and add to \$PATH"
  fi
  info '    ...ok'
}

# Check that required binaries are installed and in the $PATH.
check_script_deps() {
  check_dep 'curl'
  check_dep 'ssh'
  check_dep 'ssh-keyscan'
  check_dep 'scp'
  check_dep 'jq'
  check_dep 'sshpass'
}

# Fetch the host keys for the prep VM and save in `$job_id/known_hosts`.
#
# Used to support non-interactively trusting prep VM host keys on first use.
fetch_prep_vm_host_keys() {
  job_id=$1
  shift
  local prep_vm_creds=$(cat "${job_id}/prep-creds.json")

  local prep_vm_addr=$(echo ${prep_vm_creds} | jq -r '.ipAddress')
  local port=$(echo ${prep_vm_creds} | jq -r '.port')

  ssh-keyscan -p "${port}" "${prep_vm_addr}" > "${job_id}/known_hosts" 2>/dev/null
}

main() {
  info 'checking script dependencies...'
  check_script_deps
  info '...all script dependencies met.'

  # Note: the list of all available OS images can be fetched using the
  # `fetch_available_os_images()` function.
  local linux_os_image_id=$(fetch_linux_os_image_id)
  create_linux_job "${linux_os_image_id}" > 'job.json'
  job_id=$(jq -r '.id' < 'job.json')

  if [[ "${job_id}" == null ]]; then
    error 'unable to intialize prep VM'
  fi

  info 'creating linux job...'
  mkdir "${job_id}"
  mv 'job.json' "${job_id}/job.json"
  info "...created job: $job_id"

  info "waiting 5m while prep VM is deployed..."
  sleep 300

  while true; do
    info '    ...checking if prep VM ready'
    is_ready=$(check_machine_ready "${job_id}")

    if [[ "${is_ready}" == "true" ]]; then
      break
    fi

    info "    job not ready, retry in 60s..."
    sleep 60
  done

  info "prep VM ready for job ${job_id}"

  info "saving prep VM credentials to \`${job_id}/prep-creds.json\`"
  fetch_prep_vm_creds > "${job_id}/prep-creds.json"

  info "fetching prep VM host keys"
  fetch_prep_vm_host_keys "${job_id}"
  info '...done'

  info 'copying target to prep VM...'
  copy_to_vm "${job_id}" "${TARGET_PATH}" '~/'
  info '...done'

  info 'copying job parameters to prep VM...'
  copy_to_vm "${job_id}" 'JobParams.json' '~/'
  vm_command "${job_id}" 'sudo mv ~/JobParams.json /springfield/JobParams.json'
  info '...done'

  info 'copying fuzz target and seeds to prep VM'
  vm_command "${job_id}" "sudo cp -r ./${TARGET_NAME} /APP"
  info '...done'

  info 'validating and submitting job...'
  vm_command "${job_id}" "sfwizard -unattend" > "${job_id}/submit.log"

  info '...job successfully submitted!'
}


main
