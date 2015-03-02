# netapp_replication_report
NetApp Replication Reporting tool

This project allows you generate a report about your volume protection and replication health and lag.

It can take arguments via command line or you can pass a configuration file in yaml format.

# Usage

usage: netapp_replication_report.py [-h] [-c CONFIG] [-s HOSTNAME]
                                    [-u USERNAME] [-p PASSWORD] [-r RPO]

```
>>>> NetApp Replication Report <<<

optional arguments:
  -h, --help            show this help message and exit

If using config yaml file:
  -c CONFIG, --config CONFIG
                        Use config yaml file

If using CLI for single controller:
  -s HOSTNAME, --server HOSTNAME
                        Filer hostname
  -u USERNAME, --user USERNAME
                        Filer username
  -p PASSWORD, --password PASSWORD
                        Filer password
  -r RPO, --rpo RPO     RPO in seconds (default 24h)

```

# Cli usage

$ ./netapp_replication_report.py -s filer1 -uroot -psecret -r 86400

FILER1

The following volumes are not protected by SnapMirror:

* vol0
* testvol
* backupvol


The following volumes are over 24.0h RPO:

| source-location |                     destination-location |        lag-time(h) | last-transfer-size(GB) | last-transfer-duration(h) |  transfering

| FILER1:vmstore |              DRFILER:vmstore |     1 day, 7:20:14 |               4.21(GB) |                   0:39:48 |    40.72(GB)


# Configuration file usage

You can also use a configuration file with all the information needed, including multiple controllers, multiple credentials, RPO, notification settings and also add volumes to ignore (volumes you already know are not protected and dont need to protect)

```yaml
Sample config.yaml file:

notification_settings:
    smtp_server: 'smtp.example.com'
    from_address: 'netapp_replication_report@example.com'
    to_address: 'user@example.com, user2@example.com'
    subject: "NetApp volume replication report"

netapp_controllers:
    filer1:
        user: root
        pw: root
        rpo: 86400
        ignore_volumes:
            - vol0
            - testvol
    filer2:
        user: user1
        pw: secret
        rpo: 172800
```
You can call the above from the command line or use it as a CRON job (that is how I use it)

0 7 * * *  /home/john/netapp_replication_report/netapp_replication_report.py -c /home/john/netapp_replication_report/config.yaml

