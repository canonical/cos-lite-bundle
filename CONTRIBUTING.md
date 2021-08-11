# Overview

This documents explains the processes and practices recommended for contributing enhancements to the LMA Light bundle.

- Generally, before developing enhancements to this charm, you should consider [opening an issue](https://github.com/canonical/lma-light-bundle) explaining your use case.
- If you would like to chat with us about your use cases or proposed implementation, you can reach us on the [Charmhub Mattermost](https://chat.charmhub.io/charmhub/channels/charm-dev) or [Discourse](https://discourse.charmhub.io/).
- All enhancements require review before being merged.
  Besides the code quality and test coverage, the review will also take into  account the resulting user experience for Juju administrators using this charm.
  Please simplify the code-review process by rebasing onto the `main` branch and avoid merge commits so we can enjoy a linear Git history!

## Development

### Deploy from a local bundle file

```shell
juju deploy ./bundle.yaml
```

### Deploy with local charms

```shell
juju deploy ./bundle-local.yaml
```

## Testing
Integration tests can be run with
```shell
tox -e integration
```

To keep the model and applications running after the tests completed,
```shell
tox -e integration -- --keep-models
```


Please refer to the [project page on GitHub](https://github.com/canonical/lma-light-bundle) for further details.
