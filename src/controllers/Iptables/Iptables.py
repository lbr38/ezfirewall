# coding: utf-8

# Import libraries
from colorama import Fore, Style
from pathlib import Path
from datetime import datetime
import subprocess

class Iptables:
    def __init__(self):
        # Backup directory and files
        self.backup_dir = '/opt/ezfirewall/backups'

        date = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        self.ipv4_table_backup = self.backup_dir + '/' + date + '_iptables.save'
        self.ipv6_table_backup = self.backup_dir + '/' + date + '_ip6tables.save'

        # Create backup directory if it does not exist
        if not Path(self.backup_dir).exists():
            print('Creating backup directory: ', end = '')
            Path(self.backup_dir).mkdir(parents = True, exist_ok = True)
            print(Fore.GREEN + '✔' + Style.RESET_ALL)


    #-----------------------------------------------------------------------------------------------
    #
    #   Backup configuration
    #
    #-----------------------------------------------------------------------------------------------
    def backup(self):
        print(' ▪ Backing up actual IPv4 configuration ', end = '')

        # Backup IPv4 configuration
        result = subprocess.run(
            ['/sbin/iptables-save --counters > ' + self.ipv4_table_backup],
            capture_output = True,
            text = True,
            shell = True
        )

        # If backup failed, raise an exception
        if result.returncode != 0:
            raise Exception('error while backing up IPv4 configuration: ' + result.stderr)
        
        print('\r ' + Fore.GREEN + '✔' + Style.RESET_ALL)

        # Backup IPv6 configuration
        print(' ▪ Backing up actual IPv6 configuration ', end = '')

        result = subprocess.run(
            ['/sbin/ip6tables-save --counters > ' + self.ipv6_table_backup],
            stdout = subprocess.PIPE,
            stderr = subprocess.PIPE,
            universal_newlines = True,
            shell = True
        )

        # If backup failed, raise an exception
        if result.returncode != 0:
            raise Exception('error while backing up IPv6 configuration: ' + result.stderr)
        
        print('\r ' + Fore.GREEN + '✔' + Style.RESET_ALL)


    #-----------------------------------------------------------------------------------------------
    #
    #   Restore configuration
    #
    #-----------------------------------------------------------------------------------------------
    def backup_restore(self):
        print(' ▪ Restoring backup configuration ', end = '')

        # Restore IPv4 configuration
        result = subprocess.run(
            ['/sbin/iptables-restore --counters < ' + self.ipv4_table_backup],
            stdout = subprocess.PIPE,
            stderr = subprocess.PIPE,
            universal_newlines = True,
            shell = True
        )

        # If restore failed, raise an exception
        if result.returncode != 0:
            raise Exception('error while restoring IPv4 backup configuration: ' + result.stderr)
        
        # Restore IPv6 configuration
        result = subprocess.run(
            ['/sbin/ip6tables-restore --counters < ' + self.ipv6_table_backup],
            stdout = subprocess.PIPE,
            stderr = subprocess.PIPE,
            universal_newlines = True,
            shell = True
        )

        # If restore failed, raise an exception
        if result.returncode != 0:
            raise Exception('error while restoring IPv6 backup configuration: ' + result.stderr)

        print('\r ' + Fore.GREEN + '✔' + Style.RESET_ALL)


    #-----------------------------------------------------------------------------------------------
    #
    #   Print IPv4 table
    #
    #-----------------------------------------------------------------------------------------------
    def print_ipv4_table(self, quiet:bool = False):

        # Ask for confirmation if not in quiet mode
        if not quiet:
            print(' ▪ Print iptables IPv4 table? [y/N] ', end = '')
            answer = input().lower()

            if answer != 'y':
                return

        result = subprocess.run(
            ['/sbin/iptables', '-L', '-n', '--line-numbers', '-v'],
            stdout = subprocess.PIPE,
            stderr = subprocess.PIPE,
            universal_newlines = True
        )

        # If printing the table failed, raise an exception
        if result.returncode != 0:
            raise Exception('Error while printing IPv4 table: ' + result.stderr)

        print(result.stdout)

    
    #-----------------------------------------------------------------------------------------------
    #
    #   Print IPv6 table
    #
    #-----------------------------------------------------------------------------------------------
    def print_ipv6_table(self, quiet: bool = False):
        # Ask for confirmation if not in quiet mode
        if not quiet:
            print(' ▪ Print iptables IPv6 table? [y/N] ', end = '')
            answer = input().lower()

            if answer != 'y':
                return

        result = subprocess.run(
            ['/sbin/ip6tables', '-L', '-n', '--line-numbers', '-v'],
            stdout = subprocess.PIPE,
            stderr = subprocess.PIPE,
            universal_newlines = True
        )

        # If printing the table failed, raise an exception
        if result.returncode != 0:
            raise Exception('Error while printing IPv6 table: ' + result.stderr)

        print(result.stdout)


    #-----------------------------------------------------------------------------------------------
    #
    #   Print IPv4 table
    #
    #-----------------------------------------------------------------------------------------------
    def initialize(self, config):
        # Delete all filter table chains
        print(' ▪ Reset filters', end = ' ')
        
        cmds = [
            # Command to clear all tables
            '/sbin/iptables -F',
            '/sbin/iptables -X',
            '/sbin/iptables -Z',
            '/sbin/ip6tables -F',
            '/sbin/ip6tables -X',
            '/sbin/ip6tables -Z',

            # Vidage des règles de NAT :
            # Mesurer l'impact car il y a peut être des serveurs où des règles ont été ajoutées à la main de manière non persistante
            # '/sbin/iptables -t nat -F',

            # Default policy (-P) on INPUT and OUTPUT chains:
            # Drop everything on input chain, accept everything on output
            '/sbin/iptables  -t filter -P INPUT ' + str(config['ipv4']['input_default_policy']).upper(),
            '/sbin/iptables  -t filter -P OUTPUT ' + str(config['ipv4']['output_default_policy']).upper(),
            '/sbin/ip6tables -t filter -P INPUT ' + str(config['ipv6']['input_default_policy']).upper(),
            '/sbin/ip6tables -t filter -P OUTPUT ' + str(config['ipv6']['output_default_policy']).upper(),

            # Keep established connections (SSH for example)
            '/sbin/iptables -A INPUT -m state --state ESTABLISHED,RELATED -j ACCEPT',
            '/sbin/iptables -A OUTPUT -m state --state NEW,ESTABLISHED,RELATED -j ACCEPT',
            '/sbin/ip6tables -A INPUT -m state --state ESTABLISHED,RELATED -j ACCEPT',
            '/sbin/ip6tables -A OUTPUT -m state --state NEW,ESTABLISHED,RELATED -j ACCEPT',

            # Accept everything on loopback interface
            '/sbin/iptables  -t filter -A INPUT -i lo -j ACCEPT',
            '/sbin/ip6tables -t filter -A INPUT -i lo -j ACCEPT',

            # Accept ICMPv6 packets
            # '/sbin/ip6tables -t filter -A INPUT -p icmpv6 -j ACCEPT'
        ]

        # Execute all commands to clear tables
        for cmd in cmds:
            result = subprocess.run(
                [cmd],
                capture_output = True,
                text = True,
                shell = True
            )

            # If a command failed, raise an exception
            if result.returncode != 0:
                raise Exception('error while clearing tables, command ' + cmd + ' failed: ' + result.stderr)
        
        print('\r ' + Fore.GREEN + '✔' + Style.RESET_ALL)


    #-----------------------------------------------------------------------------------------------
    #
    #   Drop all (all interfaces)
    #
    #-----------------------------------------------------------------------------------------------
    def drop_all(self):
        self.execute('/sbin/iptables -t filter -A INPUT -j DROP')


    #-----------------------------------------------------------------------------------------------
    #
    #   Execute an iptables command
    #
    #-----------------------------------------------------------------------------------------------
    def execute(self, cmd: str):
        result = subprocess.run(
            [cmd],
            capture_output = True,
            text = True,
            shell = True
        )

        # If the command failed, raise an exception
        if result.returncode != 0:
            raise Exception('error while executing command: ' + cmd + ': ' + result.stderr)
        

    #-----------------------------------------------------------------------------------------------
    #
    #   Log dropped traffic
    #
    #-----------------------------------------------------------------------------------------------
    def log(self, config: dict):
        if config['ipv4']['enabled'] and config['ipv4']['log_dropped_traffic']:
            print(' ▪ Logging IPv4 dropped traffic: ', end = '')

            result = subprocess.run(
                ['/sbin/iptables -t filter -A INPUT -j LOG --log-prefix " [iptables-log-drop] "'],
                capture_output = True,
                text = True,
                shell = True
            )

            # If logging failed, raise an exception
            if result.returncode != 0:
                raise Exception('error while logging dropped traffic: ' + result.stderr)
            
            print(Fore.GREEN + '✔' + Style.RESET_ALL)

        if config['ipv6']['enabled'] and config['ipv6']['log_dropped_traffic']:
            print(' ▪ Logging IPv6 dropped traffic: ', end = '')

            result = subprocess.run(
                ['/sbin/ip6tables -t filter -A INPUT -j LOG --log-prefix " [ip6tables-log-drop] "'],
                capture_output = True,
                text = True,
                shell = True
            )

            # If logging failed, raise an exception
            if result.returncode != 0:
                raise Exception('error while logging dropped traffic: ' + result.stderr)
            
            print(Fore.GREEN + '✔' + Style.RESET_ALL)

    
    #-----------------------------------------------------------------------------------------------
    #
    #   Apply persistent iptables rules
    #
    #-----------------------------------------------------------------------------------------------
    def persistent(self):
        print(' ▪ Saving iptables rules ', end = '')

        if Path('/usr/libexec/iptables/iptables.init').exists():
            result = subprocess.run(
                ['/usr/libexec/iptables/iptables.init save'],
                capture_output = True,
                text = True,
                shell = True
            )
        elif Path('/sbin/iptables-save').exists():
            if not Path('/etc/iptables').exists():
                Path('/etc/iptables').mkdir(parents = True, exist_ok = True)

            result = subprocess.run(
                ['/sbin/iptables-save > /etc/iptables/rules.v4 && chown root:root /etc/iptables/rules.v4 && chmod 600 /etc/iptables/rules.v4'],
                capture_output = True,
                text = True,
                shell = True
            )
        else:
            raise Exception('no iptables persistent program found')
        
        # If saving failed, raise an exception
        if result.returncode != 0:
            raise Exception('error while saving iptables rules: ' + result.stderr)
        
        print('\r ' + Fore.GREEN + '✔' + Style.RESET_ALL)
        
        print(' ▪ Saving ip6tables rules ', end = '')

        if Path('/usr/libexec/iptables/ip6tables.init').exists():
            result = subprocess.run(
                ['/usr/libexec/iptables/ip6tables.init save'],
                capture_output = True,
                text = True,
                shell = True
            )
        elif Path('/sbin/ip6tables-save').exists():
            if not Path('/etc/iptables').exists():
                Path('/etc/iptables').mkdir(parents = True, exist_ok = True)

            result = subprocess.run(
                ['/sbin/ip6tables-save > /etc/iptables/rules.v6 && chown root:root /etc/iptables/rules.v6 && chmod 600 /etc/iptables/rules.v6'],
                capture_output = True,
                text = True,
                shell = True
            )
        else:
            raise Exception('no ip6tables persistent program found')
        
        # If saving failed, raise an exception
        if result.returncode != 0:
            raise Exception('error while saving ip6tables rules: ' + result.stderr)
        
        print('\r ' + Fore.GREEN + '✔' + Style.RESET_ALL)
