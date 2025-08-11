#!/usr/bin/python3
# coding: utf-8

import sys
import sqlite3
import re
from datetime import datetime, timedelta
from pathlib import Path
import dateutil.parser
import yaml

# Function to write message to database
def write_to_database(message: str):
    date = None
    time = None
    interface_inbound = None
    interface_outbound = None
    mac = None
    source_ip = None
    dest_ip = None
    source_port = None
    dest_port = None
    protocol = None

    con = sqlite3.connect('/var/lib/ezfirewall/ezfirewall.db')
    cursor = con.cursor()

    #
    # Set journal mode to WAL
    # This is needed to avoid database locked errors
    #
    cursor.execute("PRAGMA journal_mode=WAL;")

    #
    # Create table if it does not exist
    #
    cursor.execute("CREATE TABLE IF NOT EXISTS nftables_drop ( \
        Id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, \
        Date DATE NOT NULL, \
        Time TIME NOT NULL, \
        Interface_inbound VARCHAR(255), \
        Interface_outbound VARCHAR(255), \
        Mac VARCHAR(255), \
        Source_ip CHAR(15), \
        Dest_ip CHAR(15), \
        Source_port CHAR(5), \
        Dest_port CHAR(5), \
        Protocol CHAR(3))")

    #
    # Create indexes if they do not exist
    #
    cursor.execute("CREATE INDEX IF NOT EXISTS nftables_drop_index ON nftables_drop (Date, Time, Interface_inbound, Interface_outbound, Mac, Source_ip, Dest_ip, Source_port, Dest_port, Protocol)")
    cursor.execute("CREATE INDEX IF NOT EXISTS nftables_drop_date_index ON nftables_drop (Date)")
    cursor.execute("CREATE INDEX IF NOT EXISTS nftables_drop_dest_port_index ON nftables_drop (Dest_port)")
    cursor.execute("CREATE INDEX IF NOT EXISTS nftables_drop_source_ip_index ON nftables_drop (Source_ip)")

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

    # Get interface inbound
    if re.search(r'IN=([a-zA-Z0-9:]+)', message):
        interface_inbound = re.search(r'IN=([a-zA-Z0-9:]+)', message).group(1)

    # Get interface outbound
    if re.search(r'OUT=([a-zA-Z0-9:]+)', message):
        interface_outbound = re.search(r'OUT=([a-zA-Z0-9:]+)', message).group(1)

    # Get mac address
    if re.search(r'MAC=([a-zA-Z0-9:]+)', message):
        mac = re.search(r'MAC=([a-zA-Z0-9:]+)', message).group(1)

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

    # Get protocol
    if re.search(r'PROTO=([a-zA-Z]+)', message):
        protocol = re.search(r'PROTO=([a-zA-Z]+)', message).group(1)

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
    cursor.execute("INSERT INTO nftables_drop (Date, Time, Interface_inbound, Interface_outbound, Mac, Source_ip, Dest_ip, Source_port, Dest_port, Protocol) \
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", (date, time, interface_inbound, interface_outbound, mac, source_ip, dest_ip, source_port, dest_port, protocol))
    con.commit()
    con.close()

    del con, cursor, fields, date, time, interface_inbound, interface_outbound, mac, source_ip, dest_ip, source_port, dest_port, protocol

# Clean logs older than X days
def clean():

    # Default to 30 days if config file is not available or reading fails
    retention_days = 30

    # Get retention from config file
    try:
        if Path('/opt/ezfirewall/config.yml').exists():
            with open('/opt/ezfirewall/config.yml', 'r') as f:
                config = yaml.safe_load(f)
                if 'log_retention_days' in config:
                    retention_days = config['log_retention_days']

            del config, f
    except Exception:
        pass

    con = sqlite3.connect('/var/lib/ezfirewall/ezfirewall.db')
    cursor = con.cursor()

    # Calculate date x days ago
    date = (datetime.now() - timedelta(days=retention_days)).strftime('%Y-%m-%d')

    # Delete logs older than x days
    cursor.execute("DELETE FROM nftables_drop WHERE Date < ?", (date,))
    con.commit()
    con.close()

    del con, cursor, date

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
        if not Path('/var/lib/ezfirewall').exists():
            Path('/var/lib/ezfirewall').mkdir(parents=True, exist_ok=True, mode=0o755)

        #
        # Write message to database
        #
        write_to_database(line.rstrip())

        #
        # Clean old logs
        #
        clean()

        #
        # If line has been written without error, acquit rsyslog message by writing 'OK' to stdout
        #
        print('OK')

    except Exception as e:
        #
        # If an error occurs, print it
        #
        print('Failed to write log: ' + str(e))
