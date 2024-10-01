# Usage Workflow

## Installation
1. `python -m pip install --user ansible`

## Fetch the goss.yaml files
To validate a model, `playboook.yaml` files are required. These files can be decentralised, but must exist on the FS for Ansible validation. For cos-lite-bundle these files exist in [cos-lite-bundle/ansible](https://github.com/canonical/cos-lite-bundle/tree/investigate-ansible/ansible).

2. `git clone --branch investigate-ansible https://github.com/canonical/cos-lite-bundle.git`

## Collect with Ansible
3. `ansible-playbook -c local -i localhost, ansible/playbook.yaml`

See the ansible/output directory for collection results

## Contributing

1. `git clone --branch investigate-ansible https://github.com/canonical/cos-lite-bundle.git`
2. Modify the contents of the ansible directory according to your needs.
   1. See the docs for [playbook guide](https://docs.ansible.com/ansible/latest/playbook_guide/) and [ansible-core builtin](https://docs.ansible.com/ansible/latest/collections/ansible/builtin/) modules.
