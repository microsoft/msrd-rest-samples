import json
from .error import error_out


class Config(object):
    """
    Encapsulates parsed MSRD client configuration data, such as API credentials.
    """

    def __init__(self, logger, config_path):
        """
        Args:
            config_path: Path a JSON file containing configuration data.
        """
        self.log = logger

        with open(config_path) as f:
            config = json.load(f)

        self.log.debug('Loaded config from `%s`', config_path)
        self.log.debug('Parsed config: `%s`', json.dumps(config, indent=2))

        try:
            self.msrd_origin = config['msrdOrigin']
            self.msrd_account_id = config['msrdAccountId']
            self.msrd_api_token = config['msrdApiToken']
            self.storage_account_id = config['azureStorageAccountId']
            self.storage_api_key = config['azureStorageApiKey']
            self.storage_container_name = config['azureStorageContainer']

            # The "proxies" key is optional, so we use `get()` to default to
            # returning `None` instead of throwing a `KeyError`.
            self.proxies = config.get('proxies')  # todo: check for proper structure.

            # Whether or not we should verify TLS certificates, or a root
            # certificate (or bundle) to trust. Supports use cases where HTTP
            # proxies cause certificate errors.
            #
            # See: http://docs.python-requests.org/en/latest/user/advanced/#ssl-cert-verification
            self.verifyCerts = config.get('verifyCerts', True)
        except KeyError as e:
            error_out(self.log, "Unable to find config key {}".format(e))
