# Testing

To manually test this script, follow the directions in the README to create a
job using the `DemoFuzz` example. There are currently two cases to test:

1. No proxy
2. Proxied

## No proxy

Follow the README directions, without modification. When creating a
`Config.json`, omit the `proxies` key.

## Proxied

Edit `Config.json` to include a `proxies` key with the data:

```json
"proxies": {
    "http": "127.0.0.1:8888",
    "https": "127.0.0.1:8888"
}
```

These are the default proxy origins on Windows 10 when using Fiddler. First,
make sure the script is trying to use the proxy. Ensure Fiddler is not running,
and attempt to follow the non-proxy instructions to create a `DemoFuzz` job.
This should fail, because the script is trying to use a proxy, but one is not
running.

Now we will check that it passes. Set up a local HTTPS proxy:

1. Install the [Fidder][1] proxy/web debugging tool.
1. Configure Fiddler to intercept TLS traffic, as described [here][2]. Note that
   this will install an untrustworthy root certificate onto your computer!
1. Ensure Fiddler is running and actively recording and decrypting TLS traffic.

[1]: https://www.telerik.com/fiddler
[2]: https://docs.telerik.com/fiddler/Configure-Fiddler/Tasks/DecryptHTTPS

Now, with the `Config.json` from before, try to follow the `DemoFuzz` example
instructions. This time a job should be successfully created. Ensure that it
actually runs, which implies that the target archive and presubmission script
were correctly generated and uploaded to Azure Storage.

You can further check that the generated target archive and script look as
expected by getting their access URLs from the verbose script output, and
downloading them before they expire.
