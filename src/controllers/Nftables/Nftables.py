# coding: utf-8

# Import libraries
import os
import json
import subprocess
from pathlib import Path
from datetime import datetime
from colorama import Fore, Style
from nftables import Nftables as NftablesLib

class Nftables:
    def __init__(self):
        # Initialize nftables library
        self.nft = NftablesLib()
        self.nft.set_json_output(True)
        self.nft.set_handle_output(True)
        
        # Backup directory and file
        self.backup_dir = '/opt/ezfirewall/backups'
        self.ruleset_backup = self.backup_dir + '/' + datetime.now().strftime('%Y-%m-%d_%H-%M-%S') + '_ruleset.json'

        # Path to nftables configuration file
        self.nftables_conf_path = '/etc/nftables.conf'

        # Create backup directory if it does not exist
        if not Path(self.backup_dir).exists():
            print('Creating backup directory: ', end = '')
            Path(self.backup_dir).mkdir(parents = True, exist_ok = True)
            print(Fore.GREEN + '✔' + Style.RESET_ALL)

    #-----------------------------------------------------------------------------------------------
    #
    #   Backup current ruleset
    #
    #-----------------------------------------------------------------------------------------------
    def backup(self):
        """Backup current nftables ruleset to JSON"""
        print(' ▪ Backing up current ruleset ', end = '')

        try:
            # Get current ruleset
            rc, output, error = self.nft.cmd('list ruleset')
            
            if rc != 0:
                raise Exception('error retrieving current ruleset: ' + error)

            if rc == 0 and output:
                # Save backup
                with open(self.ruleset_backup, 'w') as f:
                    f.write(output)

            # Delete older backups (keep last 15 days)
            now = datetime.now()
            for backup_file in Path(self.backup_dir).glob('*'):
                file_time = datetime.fromtimestamp(backup_file.stat().st_mtime)
                if (now - file_time).days > 15:
                    backup_file.unlink()
            
            print('\r ' + Fore.GREEN + '✔' + Style.RESET_ALL)
                
        except Exception as e:
            raise Exception('error during backup: ' + str(e))

    #-----------------------------------------------------------------------------------------------
    #
    #   Restore configuration from backup
    #
    #-----------------------------------------------------------------------------------------------
    def backup_restore(self):
        """Restore nftables configuration from backup"""
        print(' ▪ Restoring backup configuration ', end = '')

        try:
            # Check if backup files exist
            if not Path(self.ruleset_backup).exists():
                raise Exception('backup file does not exist: ' + self.ruleset_backup)

            # Load backup JSON
            with open(self.ruleset_backup, 'r') as f:
                backup_ruleset = f.read()

            # Apply the backup ruleset
            rc, output, error = self.nft.cmd(backup_ruleset)

            if rc != 0:
                raise Exception('could not apply backup ruleset: ' + error)
                
        except Exception as e:
            raise Exception('error while restoring backup configuration: ' + str(e))

        print('\r ' + Fore.GREEN + '✔' + Style.RESET_ALL)

    #-----------------------------------------------------------------------------------------------
    #
    #   Print current ruleset
    #
    #-----------------------------------------------------------------------------------------------
    def print_table(self, quiet: bool = False):
        """Print current nftables ruleset"""
        if quiet:
            return
            
        try:
            rc, output, error = self.nft.cmd('list ruleset')
            
            if rc != 0:
                raise Exception('error retrieving ruleset: ' + error)

            if output:
                # Pretty print JSON
                ruleset_data = json.loads(output)
                print(json.dumps(ruleset_data, indent=2))
            else:
                print('No ruleset configured')
           
        except Exception as e:
            print('Error printing ruleset: ' + str(e))

    #-----------------------------------------------------------------------------------------------
    #
    #   Check nftables rules using JSON
    #
    #-----------------------------------------------------------------------------------------------
    def check(self, ruleset_json=None):
        """Check if nftables ruleset is valid WITHOUT applying it"""
        if ruleset_json is None:
            return  # Nothing to check
            
        try:
            # Test the ruleset syntax without applying it
            # We need to use the JSON validation functionality

            # First, validate it's proper JSON
            ruleset_data = json.loads(ruleset_json)
            
            # Validate the structure has required nftables format
            if not isinstance(ruleset_data, dict) or 'nftables' not in ruleset_data:
                raise Exception('invalid nftables JSON structure: missing "nftables" key')
            
            if not isinstance(ruleset_data['nftables'], list):
                raise Exception('invalid nftables JSON structure: "nftables" must be a list')
            
        except json.JSONDecodeError as e:
            raise Exception('invalid JSON format: ' + str(e))
        except Exception as e:
            raise Exception('error while checking nftables rules: ' + str(e))

    #-----------------------------------------------------------------------------------------------
    #
    #   Apply nftables rules using JSON
    #
    #-----------------------------------------------------------------------------------------------
    def apply(self, ruleset_json):
        """Apply nftables rules using JSON"""
        try:
            # Apply the ruleset
            rc, output, error = self.nft.cmd(ruleset_json)

            # If the command failed, raise an exception
            if rc != 0:
                raise Exception(error)
                
        except Exception as e:
            raise Exception(f'error while applying nftables rules: {str(e)}')

    #-----------------------------------------------------------------------------------------------
    #
    #   Save current ruleset to /etc/nftables.conf for persistence
    #
    #-----------------------------------------------------------------------------------------------
    def save_to_nftables_conf(self):
        """Save current applied ruleset to /etc/nftables.conf for persistence"""
        
        try:
            # Use nft command to get current ruleset in native format (and not JSON)
            result = subprocess.run(
                ['nft', 'list', 'ruleset'],
                capture_output=True,
                text=True
            )

            if result.returncode != 0:
                raise Exception('error getting native format: ' + result.stderr)
            
            # Write to /etc/nftables.conf with proper header
            with open(self.nftables_conf_path, 'w') as f:
                f.write("#!/usr/sbin/nft -f\n")
                f.write("# Generated by ezfirewall on " + datetime.now().strftime('%Y-%m-%d %H:%M:%S') + "\n")
                f.write("# This file ensures rules persistence across reboots\n\n")
                f.write(result.stdout)
                f.write("\n")

        except Exception as e:
            raise Exception('error saving to ' + self.nftables_conf_path + ':' + str(e))
