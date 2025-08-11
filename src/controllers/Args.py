# coding: utf-8

# Import libraries
import argparse
import sys
from colorama import Fore, Style

# Import classes
from src.controllers.Source import Source

class Args:
    #-----------------------------------------------------------------------------------------------
    #
    #   Print help
    #
    #-----------------------------------------------------------------------------------------------
    def help(self):
        print('Available parameters:')
        print('  --help, -h          : Print this help')
        print('  --quiet, -q         : Enable quiet mode (answer yes to all questions)')
        print('  --debug             : Enable debug mode')
        print('  --dry-run, -d       : Enable dry run mode')
        print('  --list-sources, -ls : List current sources')
        #print('  --add-source, -as   : Add a source')


    #-----------------------------------------------------------------------------------------------
    #
    #   Parse arguments
    #
    #-----------------------------------------------------------------------------------------------
    def parse(self):
        Args.dry_run = False
        Args.quiet = False
        Args.debug = False

        try:
            # Parse arguments
            parser = argparse.ArgumentParser(add_help=False)

            # Define valid arguments
            # Help
            parser.add_argument("--help", "-h", action="store_true", default="null")
            # Quiet
            parser.add_argument("--quiet", "-q", action="store_true", default="null")
            # Debug
            parser.add_argument("--debug", action="store_true", default="null")
            # Dry run
            parser.add_argument("--dry-run", "-d", action="store_true", default="null")
            # Add source
            # TODO
            # parser.add_argument("--add-source", "-as", action="store_true", default="null")
            # List sources
            parser.add_argument("--list-sources", "-ls", action="store", nargs='?', default="null")

            # Parse arguments
            args, remaining_args = parser.parse_known_args()

            # If remaining_args arguments are passed
            if remaining_args:
                raise Exception('Invalid arguments: ' + ' '.join(remaining_args))
        except Exception as e:
            raise Exception(str(e))

        try:
            # If --help param has been set
            if args.help != "null":
                if args.help:
                    self.help()
                    sys.exit(0)

            # If --debug param has been set
            if args.debug != "null":
                Args.debug = True
                print(Fore.YELLOW + ' ▪ Debug mode is enabled' + Style.RESET_ALL)

            # If --quiet param has been set
            if args.quiet != "null":
                Args.quiet = True
                print(Fore.YELLOW + ' ▪ Quiet mode is enabled' + Style.RESET_ALL)

            # If --dry-run param has been set
            if args.dry_run != "null":
                Args.dry_run = True
                print(Fore.YELLOW + ' ▪ Dry run mode is enabled' + Style.RESET_ALL)

            # If --add-source param has been set
            # TODO

            # If --list-sources param has been set
            if args.list_sources != "null":
                try:
                    Source().list(args.list_sources)
                    sys.exit(0)
                except Exception as e:
                    print(Fore.RED + ' ✕ ' + str(e) + Style.RESET_ALL)
                    sys.exit(1)

        except Exception as e:
            raise Exception(str(e))
