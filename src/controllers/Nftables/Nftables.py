# coding: utf-8

# Import libraries
import os
import json
import shutil
import subprocess
from pathlib import Path
from datetime import datetime
from colorama import Fore, Style
from nftables import Nftables as NftablesLib

class Nftables:
    # libnftables context, shared by all instances
    # With libnftables < 1.0 (e.g. Debian 11), creating several contexts in the same process leads to
    # a "double free or corruption" crash when they are freed at exit, so only one must be created
    nft = None

    def __init__(self):
        # Initialize nftables library (only once)
        if Nftables.nft is None:
            Nftables.nft = NftablesLib()
            Nftables.nft.set_json_output(True)
            Nftables.nft.set_handle_output(True)

        # Backup directory and files
        self.backup_dir = '/opt/ezfirewall/backups'
        backup_prefix = self.backup_dir + '/' + datetime.now().strftime('%Y-%m-%d_%H-%M-%S')

        # Never overwrite an existing backup (e.g. two runs within the same second)
        suffix = 1
        unique_prefix = backup_prefix
        while Path(unique_prefix + '_ruleset.json').exists():
            suffix += 1
            unique_prefix = backup_prefix + '_' + str(suffix)

        self.ruleset_backup = unique_prefix + '_ruleset.json'
        self.nftables_conf_backup = unique_prefix + '_nftables.conf'

        # Path to nftables configuration file
        self.nftables_conf_path = '/etc/nftables.conf'

        # Path to the nft binary (not always in PATH, e.g. when run from cron)
        self.nft_bin = shutil.which('nft') or '/usr/sbin/nft'

        # Create backup directory if it does not exist
        if not Path(self.backup_dir).exists():
            print('Creating backup directory: ', end = '')
            Path(self.backup_dir).mkdir(parents = True, exist_ok = True)
            print(Fore.GREEN + '✔' + Style.RESET_ALL)

    #-----------------------------------------------------------------------------------------------
    #
    #   Backup current ruleset (and /etc/nftables.conf)
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

            # Save backup (even if the current ruleset is empty, so that it can be restored)
            with open(self.ruleset_backup, 'w') as f:
                f.write(output if output else '{"nftables": []}')

            # Save /etc/nftables.conf, so that the persisted rules can be restored too
            if Path(self.nftables_conf_path).is_file():
                shutil.copyfile(self.nftables_conf_path, self.nftables_conf_backup)

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
    #   Get the path of a backup file
    #   If no name is specified, the most recent backup is returned
    #
    #-----------------------------------------------------------------------------------------------
    def get_backup_file(self, name: str = '') -> str:
        """Return the path of the backup file to restore"""
        if not name:
            backups = sorted(Path(self.backup_dir).glob('*_ruleset.json'), key = lambda file: (file.stat().st_mtime, file.name))

            if not backups:
                raise Exception('no backup found in ' + self.backup_dir)

            return str(backups[-1])

        # The backup can be specified by its full path or by its name in the backup directory
        for path in [Path(name), Path(self.backup_dir) / name]:
            if path.is_file():
                return str(path)

        raise Exception('backup file ' + name + ' not found (available backups are in ' + self.backup_dir + ')')

    #-----------------------------------------------------------------------------------------------
    #
    #   Restore configuration from backup
    #
    #-----------------------------------------------------------------------------------------------
    def backup_restore(self, backup_file: str = '', persist: bool = True):
        """Restore nftables configuration from backup"""
        if not backup_file:
            backup_file = self.ruleset_backup

        print(' ▪ Restoring backup configuration ', end = '')

        try:
            # Check if backup files exist
            if not Path(backup_file).exists():
                raise Exception('backup file does not exist: ' + backup_file)

            # Load backup JSON
            with open(backup_file, 'r') as f:
                backup_content = f.read()

            # Parse the backup content as JSON. The backup was produced by 'list ruleset' with JSON output enabled
            try:
                backup_ruleset = json.loads(backup_content)
            except json.JSONDecodeError as e:
                raise Exception('backup file is not valid JSON: ' + str(e))

            if not isinstance(backup_ruleset, dict) or 'nftables' not in backup_ruleset:
                raise Exception('invalid backup structure: missing "nftables" key')

            # Rebuild the command list: flush the current ruleset first, then re-apply every object from the backup:
            # - the read-only 'metainfo' element that 'list ruleset' prepends to its output is skipped
            # - handles are removed, they are assigned by the kernel and must not be reused
            # - rules containing xtables compat expressions (created by iptables-nft, e.g. by docker) are skipped
            #   because nftables cannot re-create them. They will be re-created by the service that created them.
            commands = [{"flush": {"ruleset": None}}]
            skipped_rules = 0

            for item in backup_ruleset['nftables']:
                if not isinstance(item, dict) or 'metainfo' in item:
                    continue

                if 'rule' in item and self._has_xt_expression(item['rule']):
                    skipped_rules += 1
                    continue

                commands.append(self._remove_handles(item))

            # Apply the backup ruleset
            rc, output, error = self.nft.json_cmd({"nftables": commands})

            if rc != 0:
                raise Exception('could not apply backup ruleset: ' + str(error))

        except Exception as e:
            raise Exception('error while restoring backup configuration: ' + str(e))

        print('\r ' + Fore.GREEN + '✔' + Style.RESET_ALL)

        if skipped_rules:
            print(Fore.YELLOW + ' ▪ ' + str(skipped_rules) + ' rule(s) created by iptables-nft (e.g. by docker) could not be restored, restart the services that created them to re-create them' + Style.RESET_ALL)

        if not persist:
            return

        # Restore /etc/nftables.conf from the backup made at the same time
        nftables_conf_backup = backup_file.replace('_ruleset.json', '_nftables.conf')

        if nftables_conf_backup == backup_file or not Path(nftables_conf_backup).is_file():
            print(Fore.YELLOW + ' ▪ No backup of ' + self.nftables_conf_path + ' was found for this backup, ' + self.nftables_conf_path + ' was left unchanged' + Style.RESET_ALL)
            return

        print(' ▪ Restoring ' + self.nftables_conf_path + ' ', end = '')

        try:
            with open(nftables_conf_backup, 'r') as f:
                self._write_nftables_conf(f.read())
        except Exception as e:
            raise Exception('the ruleset has been restored but ' + self.nftables_conf_path + ' could not be restored from ' + nftables_conf_backup + ': ' + str(e))

        print('\r ' + Fore.GREEN + '✔' + Style.RESET_ALL)

    #-----------------------------------------------------------------------------------------------
    #
    #   Helper: Check if a JSON object contains an xtables compat expression
    #
    #-----------------------------------------------------------------------------------------------
    def _has_xt_expression(self, data) -> bool:
        if isinstance(data, dict):
            return 'xt' in data or any(self._has_xt_expression(value) for value in data.values())
        if isinstance(data, list):
            return any(self._has_xt_expression(value) for value in data)
        return False

    #-----------------------------------------------------------------------------------------------
    #
    #   Helper: Remove handles from a JSON object
    #
    #-----------------------------------------------------------------------------------------------
    def _remove_handles(self, data):
        if isinstance(data, dict):
            return {key: self._remove_handles(value) for key, value in data.items() if key != 'handle'}
        if isinstance(data, list):
            return [self._remove_handles(value) for value in data]
        return data

    #-----------------------------------------------------------------------------------------------
    #
    #   Print current ruleset
    #
    #-----------------------------------------------------------------------------------------------
    def print_table(self, quiet: bool = False):
        """Print current nftables ruleset as tables"""
        if quiet:
            return

        # Imported here as it is only needed by this method
        from src.controllers.Nftables.Display import Display

        rc, output, error = self.nft.cmd('list ruleset')

        if rc != 0:
            raise Exception('error retrieving current ruleset: ' + error)

        Display().print_ruleset(json.loads(output)['nftables'] if output else [])

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
            # Validate JSON structure first
            ruleset_data = json.loads(ruleset_json)

            if not isinstance(ruleset_data, dict) or 'nftables' not in ruleset_data:
                raise Exception('invalid nftables JSON structure: missing "nftables" key')

            if not isinstance(ruleset_data['nftables'], list):
                raise Exception('invalid nftables JSON structure: "nftables" must be a list')

            # Use nft -c (check mode) to validate without applying
            result = subprocess.run(
                [self.nft_bin, '-c', '-j', '-f', '-'],
                input=ruleset_json,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True
            )

            if result.returncode != 0:
                raise Exception('invalid nftables ruleset: ' + result.stderr.strip())

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
                [self.nft_bin, 'list', 'ruleset'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True
            )

            if result.returncode != 0:
                raise Exception('error getting native format: ' + result.stderr)

            # The file starts by flushing the ruleset, so that it can be loaded several times
            # (e.g. 'systemctl reload nftables') without duplicating the rules
            content  = "#!/usr/sbin/nft -f\n"
            content += "# Generated by ezfirewall on " + datetime.now().strftime('%Y-%m-%d %H:%M:%S') + "\n"
            content += "# This file ensures rules persistence across reboots\n\n"
            content += "flush ruleset\n\n"
            content += result.stdout
            content += "\n"

            self._write_nftables_conf(content, check = True)

        except Exception as e:
            raise Exception('error saving to ' + self.nftables_conf_path + ': ' + str(e))

    #-----------------------------------------------------------------------------------------------
    #
    #   Helper: Write /etc/nftables.conf atomically
    #   If check is True, the file is validated with nft before replacing the current one
    #
    #-----------------------------------------------------------------------------------------------
    def _write_nftables_conf(self, content: str, check: bool = False):
        # If /etc/nftables.conf is a symlink, write to its target
        target = os.path.realpath(self.nftables_conf_path)
        tmp_file = target + '.ezfirewall.tmp'

        try:
            with open(tmp_file, 'w') as f:
                f.write(content)

            # Set restrictive permissions (root-only read/write)
            Path(tmp_file).chmod(0o600)

            # Check that the file can be loaded by nftables (at boot)
            if check:
                result = subprocess.run(
                    [self.nft_bin, '-c', '-f', tmp_file],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    universal_newlines=True
                )

                if result.returncode != 0:
                    raise Exception('generated file is not valid: ' + result.stderr.strip())

            # Replace the current file
            os.replace(tmp_file, target)

        finally:
            if Path(tmp_file).exists():
                Path(tmp_file).unlink()
