#!/usr/bin/python3
# coding: utf-8

# Import libraries
import traceback
from colorama import Fore, Style

# Import classes
from src.controllers.Config import Config
from src.controllers.Args import Args
from src.controllers.App import App
from src.controllers.Nftables.Nftables import Nftables
from src.controllers.Rule.Rule import Rule
from src.controllers.Service import Service

try:
    exit_code = 0

    # Initialize controllers
    configController = Config()
    argsController = Args()
    appController = App()
    nftablesController = Nftables()
    ruleController = Rule()
    serviceController = Service()

    # Print logo
    appController.print_logo()

    # Get current configuration
    config = configController.get()

    # Parse arguments
    argsController.parse()

    # Backup actual nftables configuration
    nftablesController.backup()

    # Apply rules (allow, drop)
    ruleController.apply(config, Args.dry_run, Args.quiet)

    # Now that the rules have been applied
    if Args.dry_run == False:
        # TODO
        # Print the applied rules
        # if Args.quiet == False:
        #     nftablesController.print_table(Args.quiet)

        # Restart services
        serviceController.restart(config['restart_services'])

# If an exception is raised, print the error message
except Exception as e:
    # If debug mode is enabled, print the stack trace
    if Args.debug:
        print(Fore.RED + ' ✕ ' + str(e) + Style.RESET_ALL + '\n' + 'Stack trace:' + '\n' + traceback.format_exc())
    else:
        print(Fore.RED + ' ✕ ' + str(e) + Style.RESET_ALL)

    # Try to restore the previous nftables configuration
    try:
        nftablesController.backup_restore()
    except Exception as e:
        print('\n' + Fore.RED + ' ✕ ' + str(e) + Style.RESET_ALL + '\n')

    exit_code = 1

# Exit with exit code
exit(exit_code)
