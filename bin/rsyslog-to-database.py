#!/usr/bin/python3
# coding: utf-8

import sys
import sqlite3
import dateutil.parser
import re
from pathlib import Path

# Function to write message to database
def write_to_database(message: str):
    date = None
    time = None
    source_ip = None
    dest_ip = None
    source_port = None
    dest_port = None

    con = sqlite3.connect('/var/lib/ezfirewall/db/ezfirewall.db')

    cursor = con.cursor()

    #
    # Create table if it does not exist
    #
    cursor.execute("CREATE TABLE IF NOT EXISTS nftables_drop ( \
        Id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, \
        Date DATE NOT NULL, \
        Time TIME NOT NULL, \
        Source_ip CHAR(15), \
        Dest_ip CHAR(15), \
        Source_port CHAR(5), \
        Dest_port CHAR(5))")

    #
    # Create indexes if they do not exist
    #
    cursor.execute("CREATE INDEX IF NOT EXISTS nftables_drop_index ON nftables_drop (Date, Time, Source_ip, Dest_ip, Source_port, Dest_port)")
    cursor.execute("CREATE INDEX IF NOT EXISTS nftables_drop_dest_port_index ON nftables_drop (Dest_port)")

    # Ignore logs with no source port or destination port
    if 'SPT=' not in message or 'DPT=' not in message:
        return

    #
    # Split message into fields, to get the date and time
    #
    fields = message.split(' ')

    # Get date
    date = fields[0]

    # Get time
    time = fields[0]

    # Get source IP
    if re.search(r'SRC=([\d\.]+)', message):
        source_ip = re.search(r'SRC=([\d\.]+)', message).group(1)

    # Get destination ip
    if re.search(r'DST=([\d\.]+)', message):
        dest_ip = re.search(r'DST=([\d\.]+)', message).group(1)

    # Get source port
    if re.search(r'SPT=(\d+)', message):
        source_port = re.search(r'SPT=(\d+)', message).group(1)

    # Get destination port
    if re.search(r'DPT=(\d+)', message):
        dest_port = re.search(r'DPT=(\d+)', message).group(1)

    # Convert date to Y-M-D format
    date = dateutil.parser.parse(date).strftime('%Y-%m-%d')

    # Convert time to H:M:S format
    time = dateutil.parser.parse(time).strftime('%H:%M:%S')

    # Quit if some values are not set
    if not date or not time or not source_ip or not dest_ip or not source_port or not dest_port:
        return

    #
    # Insert message into database
    #
    cursor.execute("INSERT INTO nftables_drop (Date, Time, Source_ip, Dest_ip, Source_port, Dest_port) VALUES (?, ?, ?, ?, ?, ?)", (date, time, source_ip, dest_ip, source_port, dest_port))
    con.commit()
    con.close()

    del con, cursor, fields, date, time, source_ip, dest_ip, source_port, dest_port

#
# Process rsyslog messages from stdin
#
for line in sys.stdin:
    # If rsyslog sends 'EOF' message, quit
    if 'EOF' == line.rstrip():
        break

    try:
        #
        # Create database directory if it does not exist
        #
        if not Path('/var/lib/ezfirewall/db').exists():
            Path('/var/lib/ezfirewall/db').mkdir(parents=True, exist_ok=True, mode=0o755)

        #
        # Write message to database
        #
        write_to_database(line.rstrip())

        #
        # If line has been written without error, acquit rsyslog message by writing 'OK' to stdout
        #
        print('OK')

    except Exception as e:
        #
        # If an error occurs, print it
        #
        print(f"Failed to write log: {e}\n")
