# coding: utf-8

# Import libraries
import shutil
import subprocess
from colorama import Fore, Style

class Service:
    def __init__(self):
        # systemctl is located in /bin on systems without merged /usr (e.g. some Debian 11)
        self.systemctl = shutil.which('systemctl') or '/usr/bin/systemctl'

    #-----------------------------------------------------------------------------------------------
    #
    #   Restart services
    #
    #-----------------------------------------------------------------------------------------------
    def restart(self, services: list):
        # If no services are passed, ignore
        if not services:
            return

        print(' ▪ Restarting services... ')

        for service in services:
            # Accept both 'docker' and 'docker.service'
            if service.endswith('.service'):
                service = service[:-len('.service')]

            # Check if service is active
            result = subprocess.run(
                [self.systemctl, 'is-active', service + '.service', '--quiet'],
                stdout = subprocess.PIPE,
                stderr = subprocess.PIPE,
                universal_newlines = True
            )

            # If service is not active, ignore it
            if result.returncode != 0:
                print(Fore.YELLOW + ' ▪ Service ' + service + ' is not active, not restarting it' + Style.RESET_ALL)
                continue

            print(' ▪ Restarting ' + service + ' service ', end = '')

            # Restart service
            result = subprocess.run(
                [self.systemctl, 'restart', service + '.service'],
                stdout = subprocess.PIPE,
                stderr = subprocess.PIPE,
                universal_newlines = True
            )

            # If service has failed to restart
            if result.returncode != 0:
                raise Exception('Failed to restart ' + service + ' service: ' + result.stderr)

            print('\r ' + Fore.GREEN + '✔' + Style.RESET_ALL)
