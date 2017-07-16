from functools import partial
import logging
import subprocess
import sublime
import sublime_plugin
import os
import fnmatch

try:
    from configparser import ConfigParser
except ImportError:
    from ConfigParser import ConfigParser

log = logging.getLogger(__name__)

ANSIBLE_COMMAND_TEMPLATE = '/usr/local/bin/ansible-vault {vault_password} {command} "{vault_file}"'


########################################################
# Utility functions                                    #
########################################################

# Return True if we want to work on the full file. False if only a string (useful for Ansible 2.3.X)
def working_on_file(view):
    """
    :param selection: sublime.Selection 
    :return: bool
    """
    for region in view.sel():
        if not region.empty():
            return False
    # Does the file contains some vars econded ie: !vault | ...
    if view.find(r"!vault", 0).empty() == False:
        return False
    return True


def get_setting(key, default=None):
    settings = sublime.load_settings('AVault.sublime-settings')
    os_specific_settings = {}

    os_name = sublime.platform()
    if os_name == 'osx':
        os_specific_settings = sublime.load_settings('AVault (OSX).sublime-settings')
    elif os_name == 'windows':
        os_specific_settings = sublime.load_settings('AVault (Windows).sublime-settings')
    else:
        os_specific_settings = sublime.load_settings('AVault (Linux).sublime-settings')

    return os_specific_settings.get(key, settings.get(key, default))


def init_decrypt_file(string_to_decode):
    tmp_file = open(get_decrypt_inline_file(), "wb")
    tmp_file.write(bytes(string_to_decode, 'UTF-8'))
    tmp_file.close()
    return get_decrypt_inline_file()


def get_content_decrypt_file():
    with open(get_decrypt_inline_file(), 'r') as content_file:
        return content_file.read()


def get_pw_inline_file():
    return sublime.cache_path()+'/avault.tmp'


def get_decrypt_inline_file():
    return sublime.cache_path()+'/avaultd.tmp'


def init_pw_inline_file(password):
    tmp_file = open(get_pw_inline_file(), "wb")
    tmp_file.write(bytes(password, 'UTF-8'))
    tmp_file.close()
    return get_pw_inline_file()


def get_password_from_ansible_cfg(src_folder):
    afile = find_ansible_cfg_file(src_folder)
    if afile is not None:
        config = ConfigParser()
        config.read(afile)
        try:
            if config.has_option('defaults', 'vault_password_file'):
                return src_folder
        except ConfigParser.NoOptionError:
            return None
    return None


def find_ansible_cfg_file(src_folder):
    for root, dirnames, filenames in os.walk(src_folder, topdown=False):
        for filename in fnmatch.filter(filenames, 'ansible.cfg'):
            return os.path.join(root, filename)
    return None


class AVaultBase:
    open_new_tab = False
    command = None
    project_settings = None
    password = None
    vault_file_path = None
    cwd = None
    selects = False


    def prompt_vault_password(self, vault_file_path):
        bound_vault_command = partial(self.run_vault_command, vault_file_path)
        self.view.window().show_input_panel('Vault Password', '', bound_vault_command, self.on_change, self.on_cancel)

    def on_change(self, password):
        pass

    def on_cancel(self):
        pass

    def get_password(self):
        # First thing to do, look if we found an ansible.cfg file with a vault_password_file in it
        # From current folder and searching recursivly to the top folder
        pass_config = {'password': '', 'file': True}

        self.cwd = os.path.dirname(self.view.file_name())
        ansible_cfg_folder = get_password_from_ansible_cfg(self.cwd)
        if ansible_cfg_folder is not None:
            self.cwd = ansible_cfg_folder
            return pass_config

        # We haven't found anything. Now we are looking for a password setted into the plugin conf
        password = get_setting('password')
        if password != '':
            pass_config['password'] = password
            pass_config['file'] = False
            return pass_config

        # Still nothing, what about a password file setted directly into the plugin conf
        password_file = get_setting('password_file')
        if password_file != '':
            pass_config['password'] = password_file
            return pass_config

        return None


    def ansible_vault(self, vault_file_path, region=None):
        
        # Determine which password configuration we are using
        password_config = self.get_password()
        if password_config is not None:
            self.run_vault_command(vault_file_path, password_config['password'], password_config['file'], region)
        else:
            self.prompt_vault_password(vault_file_path)

    def run_vault_command(self, vault_file_path, password, password_from_file=False, region=None):

        if password_from_file is False and password != '':
            password = init_pw_inline_file(password)

        if password != '':
            vault_password_flag = '--vault-password-file "{}"'.format(password)
        else:
            vault_password_flag = ''

        try:
            output = subprocess.check_output(ANSIBLE_COMMAND_TEMPLATE.format(
                vault_password=vault_password_flag,
                command=self.command,
                vault_file=vault_file_path,
            ),stderr=subprocess.STDOUT, shell=True, cwd=self.cwd)
            
        except subprocess.CalledProcessError as e:
            sublime.error_message(e.output.decode('utf-8'))
        finally:
            if password_from_file is False and password != '':
                os.remove(get_pw_inline_file())
        
        if self.open_new_tab is True:
            self.view.run_command('avault_output', {'output': output.decode("UTF-8"), 'title': vault_file_path})
        if self.selects is True:
            de_value = output.decode("UTF-8")
            if self.command == "decrypt":
                de_value = get_content_decrypt_file()
            self.view.run_command('avault_destring', {'output': de_value, 'regiona': region.a, 'regionb': region.b})

########################################################
# All command methods callable from Sublime Text #######
########################################################

# Display the decrypted file into a read-only tab
class AvaultViewCommand(AVaultBase, sublime_plugin.TextCommand):

    def run(self, edit):
        self.command = 'view'
        self.open_new_tab = True
        vault_file = self.view.file_name()
        self.ansible_vault(vault_file)

# Encrypt current file / string
class AvaultEncryptCommand(AVaultBase, sublime_plugin.TextCommand):

    def run(self, edit):
        wfile = working_on_file(self.view)
        self.command = 'encrypt' if wfile else 'encrypt_string'
        if wfile:
            self.ansible_vault(self.view.file_name())
        else:
            self.selects = True
            for region in self.view.sel():
                if not region.empty():
                    self.ansible_vault(self.view.substr(region), region)

# Decrypt current file / string
class AvaultDecryptCommand(AVaultBase, sublime_plugin.TextCommand):
    
    def run(self, edit):
        wfile = working_on_file(self.view)
        self.command = 'decrypt'
        if wfile:
            self.ansible_vault(self.view.file_name())
        else:
            self.selects = True
            for region in self.view.sel():
                if not region.empty():
                    s = self.view.substr(region)
                    file = init_decrypt_file(s.replace("!vault |\n", "").replace(' ', ''))
                    self.ansible_vault(file, region=region)
            if region.empty():
                for region in self.view.find_all(r"(?s)!vault.+?(?=(\n^[\w\d_]+:)|\Z)"):
                    if not region.empty(): 
                        s = self.view.substr(region)
                        file = init_decrypt_file(s.replace("!vault |\n", "").replace(' ', ''))
                        self.ansible_vault(file, region=region)


#######################
# Callbacks functions #
#######################


class AvaultDestring(sublime_plugin.TextCommand):
    def run(self, edit, output=None, regiona=None, regionb=None):
        region = sublime.Region(regiona, regionb)
        self.view.replace(edit, region, output)
        self.view.add_regions("mark", [region], "mark", "dot", sublime.HIDDEN | sublime.PERSISTENT)

class AvaultOutputCommand(sublime_plugin.TextCommand):
    def run(self, edit, output=None, title=None):
        output_view = self.view.window().new_file()
        output_view.set_name(title)
        output_view.insert(edit, 0, output)
        output_view.set_read_only(True)

