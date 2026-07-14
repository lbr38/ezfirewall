#!/usr/bin/python3
# coding: utf-8

# Import libraries
import traceback
import sys
from colorama import Fore, Style

# Import classes
from src.controllers.Config import Config
from src.controllers.Args import Args
from src.controllers.App import App
from src.controllers.Service import Service

argsController = None
nftablesController = None
ruleController = None

try:
    exit_code = 0

    # Initialize light controllers first
    argsController = Args()
    appController = App()

    # Print logo
    appController.print_logo()

    # Parse arguments first
    argsController.parse()

    # Import and initialize nftables-related controllers only when needed.
    # This avoids loading native bindings for commands that exit early (e.g. --help).
    from src.controllers.Nftables.Nftables import Nftables
    from src.controllers.Rule.Rule import Rule

    configController = Config()
    nftablesController = Nftables()
    ruleController = Rule()
    serviceController = Service()

    # Get current configuration
    config = configController.get()

    # Backup actual nftables configuration only if not dry run
    if not argsController.dry_run:
        nftablesController.backup()

    # Apply rules (allow, drop)
    ruleController.apply(config, argsController.dry_run, argsController.quiet, argsController.no_persist)

    # Now that the rules have been applied
    if not argsController.dry_run:
        # TODO
        # Print the applied rules
        # if Args.quiet == False:
        #     nftablesController.print_table(Args.quiet)

        # Restart services
        serviceController.restart(config['restart_services'])

# If an exception is raised, print the error message
except Exception as e:
    # If debug mode is enabled, print the stack trace
    if argsController and getattr(argsController, 'debug', False):
        print(Fore.RED + ' ✕ ' + str(e) + Style.RESET_ALL + '\n' + 'Stack trace:' + '\n' + traceback.format_exc())
    else:
        print(Fore.RED + ' ✕ ' + str(e) + Style.RESET_ALL)

    # Try to restore the previous nftables configuration only if rules were
    # actually applied to the live ruleset. If the failure happened before any
    # rule was applied (e.g. no rule files found), there is nothing to restore.
    if nftablesController is not None and ruleController is not None and getattr(ruleController, 'applied', False):
        try:
            nftablesController.backup_restore()
        except Exception as e:
            print('\n' + Fore.RED + ' ✕ ' + str(e) + Style.RESET_ALL + '\n')

    exit_code = 1

# Exit with exit code
sys.exit(exit_code)
