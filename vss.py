import diff
import win32com.client
import os
import json
import itertools
import sys
import re

#vss constants
STATUS_CHECKEDOUT      	= 0x1        # from enum VSSFileStatus
STATUS_CHECKEDOUT_ME   	= 0x2        # from enum VSSFileStatus
STATUS_NOTCHECKEDOUT   	= 0x0        # from enum VSSFileStatus

TYPE_FILE            	= 0x1        # from enum VSSItemType
TYPE_PROJECT         	= 0x0        # from enum VSSItemType

FLAG_RECURSNO        	= 0x1000     # from enum VSSFlags
FLAG_RECURSYES       	= 0x2000     # from enum VSSFlags



VSS_ROOT = "$"

class SourceSafeAutomaton(object):

	def __init__( self, ss_root_folder,
						db_file  = os.environ["SSDIR"] + "\\srcsafe.ini",
						username = os.environ["SSUSER"]  , 
						password = os.environ["SSPWD"]						):
		"""
			Initialisation and configuration of the SourceSafe Manager.
			Parameters :
			 	- ss_root_folder (path) : path where the source files are stored on the hard drive.
			 	- db_file (path) : ptah to the file containing the ss database (.ini file)
			 	- username (str) : login
			 	- password (str) : password

			There are default values for the db_file, username, password referencing
			respectively the SSDIR, SSUSER and SSPWD environment variables.
		"""
		self.root_folder   = ss_root_folder
		self.database_file = db_file
		self.username      = username
		self.password 	   = password

		
	def connect(self):
		""" Open the selected SourceSafe db using COM object """
		self.vss = win32com.client.Dispatch("SourceSafe")
		self.vss.Open( SrcSafeIni = self.database_file		 ,
					   Username   = self.username			 ,
					   Password   = self.password			 )
		
		return ( None != self.vss )



	def to_vss_relpath(self, disk_path):
		""" convert a hard drive path to the relative path stored in SourceSafe database """
		return os.path.join( VSS_ROOT, os.path.relpath( os.path.normpath(disk_path), os.path.normpath(self.root_folder) ) )

	def to_disk_abspath(self, vss_path):
		"""convert a relative path from SourceSafe to it's absolute value on the hard drive"""
		return os.path.join( self.root_folder, os.path.normpath(vss_path).lstrip(VSS_ROOT) )

	def get_vss_item(self, path, fname):
		""" Return the COM VSSItem object respresenting the source file in SourceSafe at path+fname."""
		vss_path = self.to_vss_relpath(path)
		return self.vss.VSSItem( re.sub( r"\\", "/", os.path.join(vss_path,fname)) )

	def checkout(self, path, fname ):
		""" 
			Checkout a particular file given its name and its path on the hard drive.
			Return None if the file is already checkedout by someone else.
		"""
		
		item = self.get_vss_item(path, fname)
		
		if item.Type != TYPE_FILE or item.IsCheckedOut != STATUS_NOTCHECKEDOUT:
			return None
		else:
			item.Checkout()		
			return item.IsCheckedOut

	def checkin(self, path, fname ):
		""" 
			Checkin a particular file given its name and its path on the hard drive.
			Return None if the file wasn't checkedout.
		"""
		item = self.get_vss_item(path, fname)

		if item.Type != TYPE_FILE or  item.IsCheckedOut != STATUS_CHECKEDOUT:
			return None
		else:
			item.Checkin()		
			return item.IsCheckedOut



	def undocheckout(self, path, fname ):	
		""" 
			Undo a check out on a particular file given its name and its path on the hard drive.
			Return None if the file wasn't checkedout.
		"""
		item = self.get_vss_item(path, fname)

		if item.Type != TYPE_FILE or  item.IsCheckedOut != STATUS_CHECKEDOUT:
			return None
		else:
			item.Undocheckout()		
			return item.IsCheckedOut





if __name__ == '__main__':


	if len(sys.argv) > 1:
		current_dir =  sys.argv[1]
	else :
		current_dir = os.getcwd()


	ssbot = SourceSafeAutomaton(os.getcwd())

	ssbot.apply_diff( current_dir, "test.diff")