# -*- coding: utf-8 -*-
"""Diff generator for the MSVC C++ Unicode updater script.
	* Iterates over every .h; .cpp and .inl files in the input folder (non recursively)
	* Look for non-unicode systel calls (like atoi or strcmp) and raw strings 
	* Generate a diff and json file with every calls replaced by their TCHAR-compliant equivalent and enclose raw strings with the _TEXT macro.

Usage:
	updater.py [-ar] [-n <gen_name>|--name <gen_name>] [-o <gen_path>|--output <gen_path>] (INPUT_FOLDER)
	updater.py -h | --help

Options:
	-h --help
	-n <gen_name> --name=<gen_name>
		choose the generated files' name, without extensions.
		By default it's the input folder base name.
	-o <gen_path> --output=<gen_path> 
		select where to output the generated files
	-a --apply
		apply modification to every remplacement found 
	-r
		look recursively (not implemented yet)
"""

from docopt import docopt
import sys 
import os
import diff
import sed
import vss
import json
import itertools

def get_last_folder (folder_path):
	""" Return the last folder on the path in order to create the diff filename """
	return os.path.basename(os.path.normpath( folder_path ))


def apply_diff(folder, sourcesafe_bot, diff_file ):
	""" 
		Given a diff file stored, checkout the files and apply the inline modifications.
		Optional checkin in the future.
	"""
	delta = json.loads(open(diff_file, "rb").read().decode('utf-8'))
	
	files_to_checkout = filter( lambda fname:  delta[fname] != {},  diff.multiple_file_types(*("*.h", "*.cpp", "*.inl")) )
	files_checkedout  = []	 

	with diff.cd(folder):

		for fname in files_to_checkout:
			print(fname)

			status = sourcesafe_bot.checkout( folder, fname )
			if None != status:
				diff.DiffManager.apply_modification( fname, delta[fname] )
				files_checkedout += fname

				print(fname, "checked out")
			else:
				print(fname, "already checked out by someone")

	return files_checkedout



def update_for_unicode( sourcesafe_bot, **args ):
	""" Unicode update procedure : list all the modifications, check out the files, apply the diff and opt-out checkin the files """

	# Create diff file
	diff_man = diff.DiffManager( **args )
	diff_man.process()
	diff_man.save()

	# apply modif
	diff_fname = os.path.join(args['<gen_path>'], args['<gen_name>']) + ".json"
	modified_files = apply_diff(args['INPUT_FOLDER'], sourcesafe_bot, diff_fname)




if __name__ == '__main__':

	# if len(sys.argv) > 1:
	# 	current_dir =  sys.argv[1]
	# else :
	# 	current_dir = os.getcwd()


	# #
	# update_for_unicode( current_dir, ss )

	arguments = docopt(__doc__)

	if arguments['<gen_name>'] == None :
		arguments['<gen_name>'] = os.path.basename(arguments['INPUT_FOLDER'])
	if arguments['<gen_path>'] == None :
		arguments['<gen_path>'] = os.getcwd()

	# Make sure the output folder exists
	if not os.path.isdir(arguments['<gen_path>']):
		try:
			os.makedirs(arguments['<gen_path>'])
		except OSError as exception:
			if exception.errno != errno.EEXIST:
					raise

	# Source Safe object
	ss = vss.SourceSafeAutomaton("Y:\Developpement\Advantys")
	ss.connect()

	update_for_unicode(ss, **arguments)