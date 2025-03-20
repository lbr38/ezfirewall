#!/usr/bin/python3
# coding: utf-8

# Import libraries
import traceback
from colorama import Fore, Style

# Import classes
from src.controllers.Config import Config
from src.controllers.Args import Args
from src.controllers.App import App
from src.controllers.Iptables.Iptables import Iptables
from src.controllers.Rule.Rule import Rule
from src.controllers.Service import Service

try:
    exit_code = 0

    # Initialize controllers
    configController = Config()
    argsController = Args()
    appController = App()
    iptablesController = Iptables()
    ruleController = Rule()
    serviceController = Service()

    # Print logo
    appController.print_logo()

    # Get current configuration
    config = configController.get()

    # Parse arguments
    argsController.parse()

    # Backup actual iptables configuration
    iptablesController.backup()

    # Apply rules (allow, drop)
    ruleController.apply(config, Args.dry_run, Args.quiet)

    # Now that the rules have been applied
    if Args.dry_run == False:
        # Log all dropped traffic, if enabled
        iptablesController.log(config)

        # Drop all other traffic
        iptablesController.drop_all()

        # Print the applied IPv4 table
        if Args.quiet == False:
            if config['ipv4']['enabled']:
                iptablesController.print_ipv4_table(Args.quiet)
            if config['ipv6']['enabled']:            
                iptablesController.print_ipv6_table(Args.quiet)

        # Save iptables rules to make them persistent after reboot
        iptablesController.persistent()

        # Restart services
        serviceController.restart(config['restart_services'])

# If an exception is raised, print the error message
except Exception as e:
    # If debug mode is enabled, print the stack trace
    if Args.debug:
        print(Fore.RED + ' ✕ ' + str(e) + Style.RESET_ALL + '\n' + 'Stack trace:' + '\n' + traceback.format_exc())
    else:
        print(Fore.RED + ' ✕ ' + str(e) + Style.RESET_ALL)

    # Try to restore the previous iptables configuration
    try:
        iptablesController.backup_restore()
    except Exception as e:
        print('\n' + Fore.RED + ' ✕ ' + str(e) + Style.RESET_ALL + '\n')

    exit_code = 1

# Exit with exit code
exit(exit_code)
