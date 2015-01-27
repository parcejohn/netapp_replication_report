#!/usr/bin/env python

"""
Netapp.py

Author: John Gallo


Class to interact with the NetApp SDK API 
The main purpose of this class is to Generate
a volume snapmirror protection report 

"""

import sys
import datetime

# Path to NetApp Python Library
# sys.path.append("../../../../lib/python/NetApp")

from NaServer import *

class Filer(object):
  """ NetApp Filer """

  def __init__(self, hostname, user, passwd):
      self.api = NaServer(hostname, 1, 3)
      response = self.api.set_style('LOGIN')

      if (response and response.results_errno() != 0):
        r = response.results_reason()
        print ("Unable to set authentication style " + r + "\n")
        sys.exit (2)

      self.api.set_admin_user(user, passwd)
      self.api.set_transport_type('HTTP')

      self.name = hostname

  def get_name(self):
    return self.name

  # Get list of volumes (OBJECTS)
  def get_volumes(self):
    volume_list_info = self.api.invoke("volume-list-info")

    if(volume_list_info.results_status() == "failed"):
        print (volume_list_info.results_reason() + "\n")
        sys.exit (2)

    volumes = volume_list_info.child_get("volumes")

    # Create a list of volumes based off the 'volumes' XML representation
    volume_list = volumes.children_get()
    return volume_list
                     
  # Return BOOL for volume protected/SnapMirrored status
  def is_vol_snapmirror_source(self, volume):
    if not isinstance(volume, str):
      volume = volume.child_get_string("name")

    snapmirror_vol_status = self.api.invoke("snapmirror-get-volume-status", "volume", volume)

    if(snapmirror_vol_status.results_status() == "failed"):
      print(snapmirror_vol_status.results_reason() + "\n")
      sys.exit(2)

    if snapmirror_vol_status.child_get_string("is-source") == 'true':
      return True
    else:
      return False

  # Get snapmirror_status_info object
  def get_vol_snapmirror_status_info(self,volume):
    if not isinstance(volume, str):
      volume = volume.child_get_string("name")

    snapmirror_get_status = self.api.invoke("snapmirror-get-status","location",volume)
    if(snapmirror_get_status.results_status() == "failed"):
      print(snapmirror_get_status.results_reason() + "\n")
      sys.exit(2)

    snapmirror_status = snapmirror_get_status.child_get("snapmirror-status")

    if (not(snapmirror_status == None)):
      snapmirror_status_info = snapmirror_status.child_get('snapmirror-status-info')
    else:
      sys.exit(0)

    return snapmirror_status_info

  # Source location string
  def get_vol_snapmirror_source(self, volume):
    snapmirror_status_info = self.get_vol_snapmirror_status_info(volume)
    return snapmirror_status_info.child_get_string('source-location')

  # Destination location string
  def get_vol_snapmirror_destination(self, volume):
    snapmirror_status_info = self.get_vol_snapmirror_status_info(volume)
    return snapmirror_status_info.child_get_string('destination-location')

  # Lag time in seconds
  def get_vol_snapmirror_lag(self, volume):
    snapmirror_status_info = self.get_vol_snapmirror_status_info(volume)
    return snapmirror_status_info.child_get_int('lag-time')

  # Size in KB (int)
  def get_vol_snapmirror_last_transfer_size(self, volume):
    snapmirror_status_info = self.get_vol_snapmirror_status_info(volume)
    return snapmirror_status_info.child_get_int('last-transfer-size')

  # Duration in seconds
  def get_vol_snapmirror_last_transfer_duration(self, volume):
    snapmirror_status_info = self.get_vol_snapmirror_status_info(volume)
    return snapmirror_status_info.child_get_int('last-transfer-duration')

  # Current progress status
  def get_vol_snapmirror_progress(self, volume): 
    snapmirror_status_info = self.get_vol_snapmirror_status_info(volume)
    return snapmirror_status_info.child_get_string('transfer-progress')

  # List of Snapmirrored Volumes
  def get_snapmirrored_volumes(self):
    snapmirrored_vols = []
    vols = self.get_volumes()

    for vol in vols:
      if self.is_vol_snapmirror_source(vol):
        snapmirrored_vols.append(vol)
    
    return snapmirrored_vols

  # List of non-Snapmirrored Volumes
  def get_non_snapmirrored_volumes(self):
    non_snapmirrored_vols = []
    vols = self.get_volumes()

    for vol in vols:
      if not self.is_vol_snapmirror_source(vol):
        non_snapmirrored_vols.append(vol)

    return non_snapmirrored_vols

  # Volume protection report
  def vol_snapmirror_report(self, ignore_volumes=[]):
    # Get list of Volume Objects
    vols = self.get_volumes()

    # Initialize [non]snapmirrored volumes arrays
    snapmirrored_vols = self.get_snapmirrored_volumes()
    non_snapmirrored_vols = self.get_non_snapmirrored_volumes()

    # Apply ignore_volumes exclusion
    snapmirrored_vols = [vol for vol in snapmirrored_vols if vol.child_get_string("name") not in ignore_volumes]
    non_snapmirrored_vols = [vol for vol in non_snapmirrored_vols if vol.child_get_string("name") not in ignore_volumes]

    # Generate report for non protected volumes
    # non_snapmirrored_vols_report 'string'
    if non_snapmirrored_vols:
      non_snapmirrored_vols_report = "The following volumes are not protected by SnapMirror:\n"
      non_snapmirrored_vols_report += "------------------------------------------------------\n"

      # Output volumes not snapmirrored
      for vol in sorted(non_snapmirrored_vols, key=lambda elm: elm.child_get_string("name")):
         non_snapmirrored_vols_report += vol.child_get_string("name") + "\n"

    # Generate report for protected volumes that have a lag
    if snapmirrored_vols:
      report_lag = ''
      for vol in sorted(snapmirrored_vols, key=lambda elm: elm.child_get_string("name")):
        if self.get_vol_snapmirror_lag(vol) > 86400:
          report_lag += "%30s | %40s | %12s | %18.2f(GB) | %20s | %12s " % (
                                                      self.get_vol_snapmirror_source(vol),
                                                      self.get_vol_snapmirror_destination(vol),
                                                      str(datetime.timedelta(seconds=self.get_vol_snapmirror_lag(vol))),
                                                      float(self.get_vol_snapmirror_last_transfer_size(vol))/1048576,
                                                      str(datetime.timedelta(seconds=self.get_vol_snapmirror_last_transfer_duration(vol))),
                                                      self.get_vol_snapmirror_progress(vol)
                                                      )
          report_lag += "\n"

      if report_lag:
        # Output Volumes snapmirrored with more than 24h RPO
        snapmirrored_vols_report = "\n\nThe following volumes are over 24h RPO:\n"
        
        header = "%30s | %40s | %12s | %20s | %20s | %12s \n" % ('source-location','destination-location','lag-time(h)','last-transfer-size(GB)','last-transfer-duration(h)','transfering')
        separator = "-" * len(header) + "\n"

        snapmirrored_vols_report += separator + header + separator
        snapmirrored_vols_report += report_lag

    # Report Filer Name/Header + non protected vols + reported lag
    if report_lag or non_snapmirrored_vols:
      report = "\n" + "="*10 + self.get_name().upper() + "="*10 + "\n"
      report += "------------------------------------------------------\n"
      report += non_snapmirrored_vols_report
      report += report_lag
      return report
    else:
      return ''

