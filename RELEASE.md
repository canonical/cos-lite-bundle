## Quality gates

| [Risk level]                  | Edge                            | Beta                         | Candidate                                                                                    | Stable                                                                                                                                            |
|-------------------------------|---------------------------------|------------------------------|----------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------|
| Meaning                       | Bleeding edge developer version | Most new features stabilized | Feature-ready, currently in testing                                                          | Well-tested, production-ready                                                                                                                     |
| Preconditions (quality gates) | Code review, CI                 |                              | Load tests                                                                                   |                                                                                                                                                   |
| Timing                        | Every merge to main             |                              | Charm reaches a state of feature completion with respect to the next planned stable release. | In consultation with product manager and engineering manager when the candidate revision has been well tested and is deemed ready for production. |
| Release process               | Automatic (on merge)            | Manual                       | Manual                                                                                       | Manual                                                                                                                                            |


## Publishing
```shell
tox -e render-edge
charmcraft pack
charmcraft upload cos-lite.zip
charmcraft release cos-lite --channel=edge --revision=N
```

### Promoting a revision to a lower risk level
```shell
charmcraft release cos-lite --channel=beta --revision=N
```

## A note on granularity of revisions

We believe in shipping often and with confidence. It is perfectly acceptable to have a new `latest/stable` release containing just one bug fix or a small new feature with respect to the last one.

[Risk level]: https://snapcraft.io/docs/channels#heading--risk-levels
