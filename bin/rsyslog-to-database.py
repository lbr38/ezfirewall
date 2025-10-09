#!/usr/bin/python3
# coding: utf-8

import sys
import sqlite3
import re
from datetime import datetime, timedelta
from pathlib import Path
import dateutil.parser
import yaml

# Global variables for batch processing
batch_data = []
BATCH_SIZE = 50 # Number of messages to wait before writing to database

# Function to parse a single message
def parse_message(message: str):
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

    # Ignore logs with no source port or destination port
    if 'SPT=' not in message or 'DPT=' not in message:
        return None

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
    try:
        date = dateutil.parser.parse(date).strftime('%Y-%m-%d')
        time = dateutil.parser.parse(time).strftime('%H:%M:%S')
    except:
        return None

    # Quit if some values are not set
    if not date or not time or not source_ip or not dest_ip or not source_port or not dest_port:
        return None

    return (date, time, interface_inbound, interface_outbound, mac, source_ip, dest_ip, source_port, dest_port, protocol)

# Function to write batch data to database
def write_batch_to_database(batch_data):
    if not batch_data:
        return

    con = sqlite3.connect('/var/lib/ezfirewall/ezfirewall.db')
    cursor = con.cursor()

    #
    # Set journal mode to WAL
    # This is needed to avoid database locked errors
    #
    cursor.execute("PRAGMA journal_mode=WAL;")

    #
    # Create nftables_drop table if it does not exist
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
    cursor.execute("CREATE INDEX IF NOT EXISTS nftables_drop_dest_port_protocol_index ON nftables_drop (Dest_port, Protocol)")
    cursor.execute("CREATE INDEX IF NOT EXISTS nftables_drop_source_ip_index ON nftables_drop (Source_ip)")

    #
    # Insert all messages in batch using executemany for better performance
    #
    cursor.executemany("INSERT INTO nftables_drop (Date, Time, Interface_inbound, Interface_outbound, Mac, Source_ip, Dest_ip, Source_port, Dest_port, Protocol) \
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", batch_data)
    
    con.commit()
    con.close()

    del con, cursor

# Function to add message to batch and write if batch is full
def add_to_batch(message: str):
    global batch_data
    
    parsed_data = parse_message(message)
    if parsed_data is None:
        return

    batch_data.append(parsed_data)

    # If batch is full, write to database and clear batch
    if len(batch_data) >= BATCH_SIZE:
        write_batch_to_database(batch_data)
        batch_data.clear()

# Function to flush remaining batch data
def flush_batch():
    global batch_data
    if batch_data:
        write_batch_to_database(batch_data)
        batch_data.clear()

# Clean logs older than X days, do it only once every sunday at midnight
def clean():
    last_cleanup = None
    cleanup_file = '/var/lib/ezfirewall/.ezfirewall.db.cleanup'
    # Default to 30 days if config file is not available or reading fails
    retention_days = 30

    # If today is not sunday and hour is not 0, skip cleanup
    if datetime.now().weekday() != 6 or datetime.now().hour != 0:
        return

    # Get latest cleanup run
    if Path(cleanup_file).exists():
        with open(cleanup_file, 'r') as f:
            last_cleanup = f.read().strip()

    # If last cleanup was today, skip cleanup
    if last_cleanup == datetime.now().strftime('%Y-%m-%d'):
        return

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

    # Vacuum database to free space
    cursor.execute("VACUUM;")

    # Analyze database to optimize query performance
    cursor.execute("ANALYZE;")

    # Commit changes and close connection
    con.commit()
    con.close()

    # Write last cleanup date to file
    try:
        with open(cleanup_file, 'w') as f:
            f.write(datetime.now().strftime('%Y-%m-%d'))
    except Exception:
        raise Exception('Could not write to cleanup file ' + cleanup_file)

    f.close()

    del con, cursor, date, last_cleanup, cleanup_file, retention_days

#
# Process rsyslog messages from stdin
#
try:
    for line in sys.stdin:
        # If rsyslog sends 'EOF' message, flush remaining batch and quit
        if 'EOF' == line.rstrip():
            flush_batch()
            break

        try:
            #
            # Create database directory if it does not exist
            #
            if not Path('/var/lib/ezfirewall').exists():
                Path('/var/lib/ezfirewall').mkdir(parents=True, exist_ok=True, mode=0o755)

            #
            # Add message to batch
            #
            add_to_batch(line.rstrip())

            #
            # Clean old logs (only called once per batch to reduce overhead)
            #
            if len(batch_data) == 1:  # Call cleanup only on first message of each batch
                clean()

            #
            # If line has been processed without error, acquit rsyslog message by writing 'OK' to stdout
            #
            print('OK')

        except Exception as e:
            #
            # If an error occurs, print it and flush current batch to avoid data loss
            #
            flush_batch()
            print('Error: ' + str(e))

except KeyboardInterrupt:
    # Flush remaining batch on interruption
    flush_batch()
    sys.exit(0)

# Flush any remaining data before exit
flush_batch()