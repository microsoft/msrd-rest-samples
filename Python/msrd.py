#!/usr/bin/env python3
import json
from pathlib import Path
from urllib.parse import urljoin

import click
import requests


class Client:
    """
    Example REST API client.

    This client encapsulates the environment and authentication information
    required to use the MSRD REST API, includes the Files API.
    """

    def __init__(self, msrd_url, account_id, api_token):
        self.msrd_url = msrd_url
        self.account_id = account_id
        self.api_token = api_token

        accounts_url = urljoin(self.msrd_url, 'accounts')
        self.account_url = urljoin(accounts_url, self.account_id)

        self.headers = {
            'SpringfieldApiToken': self.api_token,
        }

        self.session = requests.Session()
        self.session.headers.update(self.headers)
        self.session.hooks.update({
            'response': lambda r, *args, **kwargs: print('{} {} {}'.format(r.status_code, r.reason, r.url))
        })

    def _url(self, fmt, *args, **kwargs):
        path = fmt.format(*args, **kwargs)
        return urljoin(self.msrd_url, path)

    def account_info(self):
        url = self._url('api/accounts/{}', self.account_id)
        return self.session.get(url)

    def os_images(self):
        url = self._url('api/accounts/{}/osimages', self.account_id)
        return self.session.get(url)

    def job_tiers(self):
        url = self._url('api/accounts/{}/jobtiers', self.account_id)
        return self.session.get(url)

    def jobs(self):
        url = self._url('api/accounts/{}/jobs', self.account_id)
        return self.session.get(url)

    def upload_file(self, file_path):
        url = self._url('files/accounts/{}/session', self.account_id)
        with open(file_path, 'rb') as f:
            return self.session.put(url, data=f)

    def submit_job(self, job):
        url = self._url('api/accounts/{}/jobs', self.account_id)
        return self.session.post(url, json=job)


def print_response(r):
    try:
        print(json.dumps(r.json(), indent=2))
    except json.JSONDecodeError:
        print(r.text)


DEFAULT_MSRD_URL='https://microsoftsecurityriskdetection.com'

@click.group()
@click.option('msrd_url',
              '-u', '--url',
              default=DEFAULT_MSRD_URL,
              envvar='MSRD_URL',
              prompt='MSRD base URL?')
@click.option('account_id',
              '-a', '--account',
              envvar='MSRD_ACCOUNT',
              prompt='Account ID?')
@click.option('api_token',
              '-t', '--token',
              envvar='MSRD_TOKEN',
              prompt='API Token?')
@click.pass_context
def main(ctx, msrd_url, account_id, api_token):
    ctx.obj = Client(msrd_url, account_id, api_token)


@main.command()
@click.pass_obj
def account_info(client):
    print_response(client.account_info())


@main.command()
@click.pass_obj
def os_images(client):
    print_response(client.os_images())


@main.command()
@click.pass_obj
def job_tiers(client):
    print_response(client.job_tiers())


@main.command()
@click.pass_obj
def jobs(client):
    print_response(client.jobs())


@main.command()
@click.option('file_path', '-f', '--file')
@click.pass_obj
def upload_file(client, file_path):
    print_response(client.upload_file(file_path))


MAX_FILE_SIZE = int(4e6)  # Bytes


def add_file_info_to_job(client, job, files):
    file_info = []

    # Upload each file to Azure Storage using the MSRD Files API.
    # Max file size is 4mb.
    for f in files:
        path = Path(f)
        size = path.stat().st_size

        if size > MAX_FILE_SIZE:
            print('ERROR: file "{}" has byte size {}, which exceeds limit of 4mb'.format(f, size))
            exit(1)

        name = path.name

        # Does not currently return JSON, but a double-quoted URL as text.
        # Remove the double-quotes to avoid errors later on.
        url = client.upload_file(f).text.strip('"')

        info = {
            'action': 'DownloadOnly',
            'name': name,
            'url': url,
        }

        file_info.append(info)

    if file_info:
        job['setup']['package']['fileInformations'] = file_info

    return job


@main.command()
@click.option('job_path', '-j', '--job', prompt='Path to job JSON')
@click.argument('files', nargs=-1)
@click.pass_obj
def submit(client, job_path, files):
    with open(job_path) as f:
        job = json.load(f)

    job = add_file_info_to_job(client, job, files)

    print_response(client.submit_job(job))


if __name__ == '__main__':
    main()