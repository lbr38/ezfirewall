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
serviceController = None
config = None

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

    nftablesController = Nftables()

    # Print the rules currently in place if --print param has been set
    if argsController.print_rules:
        nftablesController.print_table()
        sys.exit(0)

    configController = Config()
    serviceController = Service()

    # Get current configuration
    config = configController.get()

    # Restore a backup if --restore param has been set
    if argsController.restore is not None:
        backup_file = nftablesController.get_backup_file(argsController.restore)
        print(' ▪ Backup to restore: ' + backup_file)

        if argsController.dry_run:
            sys.exit(0)

        if not argsController.quiet and not appController.confirm(' ▪ Restore this backup? [y/N] '):
            sys.exit(0)

        # Backup the current ruleset first, so that the restore can be undone
        nftablesController.backup()
        nftablesController.backup_restore(backup_file, persist = not argsController.no_persist)

        # Restart services (e.g. docker re-creates its own rules)
        serviceController.restart(config['restart_services'])
        sys.exit(0)

    ruleController = Rule(nftablesController)

    # Backup actual nftables configuration only if not dry run
    if not argsController.dry_run:
        nftablesController.backup()

    # Apply rules (input, output, forward, nat)
    ruleController.apply(config, argsController.dry_run, argsController.quiet, argsController.no_persist)

    # Now that the rules have been applied
    if not argsController.dry_run:
        # TODO
        # Print the applied rules
        # if Args.quiet == False:
        #     nftablesController.print_table(Args.quiet)

        # Restart services
        serviceController.restart(config['restart_services'])

# If an exception is raised (or the user interrupts the script), print the error message
except (Exception, KeyboardInterrupt) as e:
    message = 'Interrupted' if isinstance(e, KeyboardInterrupt) else str(e)

    # If debug mode is enabled, print the stack trace
    if argsController and getattr(argsController, 'debug', False):
        print('\n' + Fore.RED + ' ✕ ' + message + Style.RESET_ALL + '\n' + 'Stack trace:' + '\n' + traceback.format_exc())
    else:
        print('\n' + Fore.RED + ' ✕ ' + message + Style.RESET_ALL)

    # Try to restore the previous nftables configuration only if rules were
    # actually applied to the live ruleset. If the failure happened before any
    # rule was applied (e.g. no rule files found), there is nothing to restore.
    if nftablesController is not None and ruleController is not None and getattr(ruleController, 'applied', False):
        try:
            nftablesController.backup_restore(persist = not argsController.no_persist)

            # Restart services (e.g. docker re-creates its own rules)
            serviceController.restart(config['restart_services'])
        except Exception as e:
            print('\n' + Fore.RED + ' ✕ ' + str(e) + Style.RESET_ALL + '\n')

    exit_code = 1

# Exit with exit code
sys.exit(exit_code)
