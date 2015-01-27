#!/usr/bin/env python 

import argparse
import sys
import smtplib
from email.mime.text import MIMEText
import yaml

# Point to downloaded NetApp SDK
sys.path.append("netapp_sdk")
import Netapp

# Return dict woth config settings
def parse_config(filername):
  config = {}

  try:
    with open(filername, 'r') as ymlfile:
      cfg = yaml.load(ymlfile)
  except IOError, ie:
    sys.stderr.write('Cannot open configuration file\n')

  if cfg['notification_settings']:
    config['smtp_server'] =  cfg['notification_settings']['smtp_server']
    config['from_address']  = cfg['notification_settings']['from_address']
    config['to_address']    = cfg['notification_settings']['to_address']
    config['subject']       = cfg['notification_settings']['subject']

  if cfg['netapp_controllers']:
    config['netapp_controllers'] = cfg['netapp_controllers']

  return config

# send email report
def email_report(config, report_str):
  msg = MIMEText(report_str)
    
  smtp_server   = config['smtp_server']
  from_address  = config['from_address']
  to_address    = config['to_address'].split(',')
  subject       = config['subject']

  msg['Subject'] = subject
  msg['From'] =    from_address
  msg['To'] = ", ".join(to_address)


  s = smtplib.SMTP(smtp_server)
  s.sendmail(from_address, to_address, msg.as_string())
  s.quit()

# Parse Arguments
def parse_arguments():
  parser = argparse.ArgumentParser(description='>>> NetApp Replication Report <<<')

  config_group =  parser.add_argument_group(title='If using config yaml file')
  config_group.add_argument('-c', '--config',
                    action='store', dest='config',
                    help='Use config yaml file')

  cli_group =  parser.add_argument_group(title='If using CLI for single controller')

  cli_group.add_argument('-s', '--server',
                    action='store', dest='hostname',
                    help='Filer hostname')
  
  cli_group.add_argument('-u', '--user',
                  action='store', dest='username',
                  help='Filer username')

  cli_group.add_argument('-p', '--password',
                  action='store', dest='password',
                  help='Filer password')

  args = parser.parse_args()

  return args

def main():

  # Get arguments
  args = parse_arguments()

  # Start report
  report = ''

  if args.config:
    # Parse configuration file
    config = parse_config(args.config)

    # Loop thru all controllers
    for controller in config['netapp_controllers']:
      na_filer = Netapp.Filer(
                              controller,
                              config['netapp_controllers'][controller]['user'],
                              config['netapp_controllers'][controller]['pw']
                             )
      try:
         report += na_filer.vol_snapmirror_report(config['netapp_controllers'][controller]['ignore_volumes'])
      except KeyError, ke:
         report += na_filer.vol_snapmirror_report()

      # If there is data in report for the current filer in the for-loop, add a new line
      if report: report += "\n"

    # If there is data in report after traversing ALL filers
    if report: 
      email_report(config, report) 

  elif  (args.hostname and args.username and args.password):
    na_filer = Netapp.Filer(
                            args.hostname,
                            args.username,
                            args.password
                           )
    report += na_filer.vol_snapmirror_report() + "\n"
  else: 
    sys.stderr.write('You must choose valid config file (yaml) OR use -s -u -p for hostname, user, password respectively, use -h for detailed help\n')

  print report

if __name__ == '__main__':
  main() 


