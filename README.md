# sublime_avault
Ansible vault plugin for Sublime Text.
You can encrypt / decrypt / view files using the Ansible Vault binary.

It supports the encrypt_string with Ansible 2.3.X, it was tested on Mac OS X ans Linux platforms.

This plugin was inspired from the Ansible Vault plugin from [adambullmer](https://github.com/adambullmer/sublime_ansible_vault)


## Pre-requisites
- [ansible](http://docs.ansible.com/ansible/) (from 2.3)

## Installation

### With Package Control:

1. Run the `Package Control: Install Package` command, find and install the Avault plugin.
1. Restart Sublime Text (if required)

### Manually:

1. Clone or download the git repo into your packages folder (in Sublime Text, find Browse Packages… menu item to open this folder)
1. Restart Sublime Text editor (if required)

## Usage

### Tools > AVault > Encrypt

If you have selected one or more values it will use the ansible_encrypt method and update the current file.

If nothing is selected it will encrypt the whole current file.

### Tools > AVault > Decrypt

If you have selected one or more values it will use Ansible to decrypt the data and update the current file.

If nothing is selected it will look the file for any !vault | ... string to decrypt, if nothing is found it will try to decrypt the full file.

### Tools > AVault > View

*It is only working on full encrypted file*

It will open a new readonly file on a different tab.

## Configuration
The following options are available:

Order| Option          | Description |
-----|-----------------|-------------|
1| `ansible.cfg` | The plugin will look into the current folder of the file being updated recursively to the root partition for an ansible.cfg file containing the `vault_password_file` option |
2| `password`      | Plain text ansible vault password. |
2| `password_file` | Absolute path to your ansible vault [password file](http://docs.ansible.com/ansible/playbooks_vault.html#running-a-playbook-with-vault) |
3| `password input box`      | If nothing was found, an input box asking for password will be prompted |
