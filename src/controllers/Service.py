# coding: utf-8

# Import libraries
from colorama import Fore, Style
import subprocess

class Service:
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
            # Check if service is active
            result = subprocess.run(
                ['/usr/bin/systemctl', 'is-active', service + '.service', '--quiet'],
                capture_output = True,
                text = True,
            )

            # If service is not active, ignore it
            if result.returncode != 0:
                continue

            print(' ▪ Restarting ' + service + ' service ', end = '')

            # Restart service
            result = subprocess.run(
                ['/usr/bin/systemctl', 'restart', service + '.service'],
                capture_output = True,
                text = True,
            )

            # If servcie has failed to restart
            if result.returncode != 0:
                raise Exception('Failed to restart ' + service + ' service: ' + result.stderr)
            
            print('\r ' + Fore.GREEN + '✔' + Style.RESET_ALL)
