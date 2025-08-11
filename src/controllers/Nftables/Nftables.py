# coding: utf-8

# Import libraries
import os
import shutil
import subprocess
from pathlib import Path
from datetime import datetime
from colorama import Fore, Style

class Nftables:
    def __init__(self):
        # Backup directory and file
        self.backup_dir = '/opt/ezfirewall/backups'
        self.nftables_backup = self.backup_dir + '/' + datetime.now().strftime('%Y-%m-%d_%H-%M-%S') + '_nftables.conf'

        # Create backup directory if it does not exist
        if not Path(self.backup_dir).exists():
            print('Creating backup directory: ', end = '')
            Path(self.backup_dir).mkdir(parents = True, exist_ok = True)
            print(Fore.GREEN + '✔' + Style.RESET_ALL)

        #
        # Prepare new ruleset file from template
        #
        if Path('/etc/nftables.conf.new').exists():
            try:
                os.remove('/etc/nftables.conf.new')
            except Exception as e:
                raise Exception('error while deleting /etc/nftables.conf.new: ' + str(e))

        try:
            shutil.copy2('/opt/ezfirewall/templates/nftables.conf', '/etc/nftables.conf.new')
        except Exception as e:
            raise Exception('error while copying /opt/ezfirewall/templates/netfilter.conf.template to /etc/nftables.conf.new: ' + str(e))


    #-----------------------------------------------------------------------------------------------
    #
    #   Backup configuration
    #
    #-----------------------------------------------------------------------------------------------
    def backup(self):
        # Backup current config if it exists
        if not Path('/etc/nftables.conf').exists():
            return

        print(' ▪ Backing up current configuration ', end = '')

        # copy the current configuration to the backup directory
        try:
            shutil.copy2('/etc/nftables.conf', self.nftables_backup)
        except Exception as e:
            raise Exception('error while backing up current configuration: ' + str(e))

        print('\r ' + Fore.GREEN + '✔' + Style.RESET_ALL)


    #-----------------------------------------------------------------------------------------------
    #
    #   Restore configuration
    #
    #-----------------------------------------------------------------------------------------------
    def backup_restore(self):
        print(' ▪ Restoring backup configuration ', end = '')

        # Check if backup files exist
        if not Path(self.nftables_backup).exists():
            raise Exception('backup file does not exist: ' + self.nftables_backup)

        # Delete current nftables configuration
        try:
            os.remove('/etc/nftables.conf.new')
        except Exception as e:
            raise Exception('error while deleting /etc/nftables.conf.new: ' + str(e))

        # Restore nftables configuration
        try:
            shutil.copy2(self.nftables_backup, '/etc/nftables.conf.new')
        except Exception as e:
            raise Exception('error while restoring nftables configuration to /etc/nftables.conf.new: ' + str(e))

        # Check the restored configuration
        self.check()

        # Apply the restored configuration
        self.apply()

        print('\r ' + Fore.GREEN + '✔' + Style.RESET_ALL)


    #-----------------------------------------------------------------------------------------------
    #
    #   Print IPv4 table
    #
    #-----------------------------------------------------------------------------------------------
    # TODO
    def print_table(self, quiet: bool = False):
        return


    #-----------------------------------------------------------------------------------------------
    #
    #   Check ngftables rules (/etc/nftables.conf.new)
    #
    #-----------------------------------------------------------------------------------------------
    def check(self, file: str = '/etc/nftables.conf.new'):
        #
        # Check config file
        #
        result = subprocess.run(
            ['nft', '-c', '-f', file],
            stdout = subprocess.PIPE,
            stderr = subprocess.PIPE,
            universal_newlines = True
        )

        # If the config file is not valid, raise an exception
        if result.returncode != 0:
            raise Exception('invalid nftables configuration found in ' + file + ': ' + result.stderr)


    #-----------------------------------------------------------------------------------------------
    #
    #   Apply nftables rules (/etc/nftables.conf)
    #
    #-----------------------------------------------------------------------------------------------
    def apply(self):
        #
        # Move the new configuration to the actual configuration
        #
        try:
            os.rename('/etc/nftables.conf.new', '/etc/nftables.conf')
        except Exception as e:
            raise Exception('error while copying /etc/nftables.conf.new to /etc/nftables.conf: ' + str(e))

        #
        # Apply the new configuration
        #
        result = subprocess.run(
            ['nft -f /etc/nftables.conf'],
            stdout = subprocess.PIPE,
            stderr = subprocess.PIPE,
            universal_newlines = True,
            shell = True
        )

        # If the command failed, raise an exception
        if result.returncode != 0:
            raise Exception('error while applying nftables rules: ' + result.stderr)
