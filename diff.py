# -*- coding: utf-8 -*-
"""Diff generator for the MSVC C++ Unicode updater script.
	* Iterates over every .h; .cpp and .inl files in the input folder (non recursively)
	* Look for non-unicode systel calls (like atoi or strcmp) and raw strings 
	* Generate a diff and json file with every calls replaced by their TCHAR-compliant equivalent and enclose raw strings with the _TEXT macro.

Usage:
	diff.py [-arf] [-n <gen_name>|--name <gen_name>] [-o <gen_path>|--output <gen_path>] (INPUT_FOLDER)
	diff.py -h | --help

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
	-f
		work on a single file (instead of folder)
"""

from docopt import docopt

import sed
import itertools
import pickle
import sys
import os 
import glob
import json
import fileinput
import codecs



def multiple_file_types(*patterns):
	'''
		Return the list of files matching several patterns.
		Used to iterate over more than one type of file.
	'''
	return itertools.chain.from_iterable(glob.glob(pattern) for pattern in patterns)



class cd:
    """Context manager for changing the current working directory"""
    def __init__(self, newPath):
        self.newPath = newPath

    def __enter__(self):
        self.savedPath = os.getcwd()
        os.chdir(self.newPath)

    def __exit__(self, etype, value, traceback):
        os.chdir(self.savedPath)


def init_sed():
	"""Create the list of parsers we want to use to process the input files"""

	ms = sed.MultiSed()

	ms.append( sed.RawStringSed() )

	ms.append( sed.SimpleSed( r"\batoi\b"				, "_ttoi"    )	)
	ms.append( sed.SimpleSed( r"\b_atoi64\b"			, "_ttoi64"  )	)
	ms.append( sed.SimpleSed( r"\bstrcmp\b"				, "_tcscmp"  ) 	)
	ms.append( sed.SimpleSed( r"\bsscanf\b"				, "_stscanf" ) 	)
	ms.append( sed.SimpleSed( r"\bscanf\b"				, "_tscanf"  ) 	)
	ms.append( sed.SimpleSed( r"\bfscanf\b"				, "_ftscanf" ) 	)
	ms.append( sed.SimpleSed( r"\bfprintf\b"			, "_ftprintf") 	)
	ms.append( sed.SimpleSed( r"\bprintf\b"				, "_tprintf" ) 	)
	ms.append( sed.SimpleSed( r"\bsprintf\b"			, "_stprintf") 	)

	ms.append( sed.SimpleSed( r"(unsigned )*char( )*\*"	, "TCHAR *"  ) 	)

	ms.append( sed.AddArgsSed(r"\batof\b", "_tcstod", ", NULL "	     )	)
	ms.append( sed.AddArgsSed(r"\batol\b", "_tcstol", ", NULL, 10 "  )	)

	return ms


class DiffManager(object):
	""" 
		Diff creator : given an input directory, process every source file
		and create an JSON file with all the modifications to be done.
	"""

	def __init__(self, **args):
		self.sed = init_sed()
		self.JSON = {}
		self.args = args

		if '-f' in self.args and self.args['-f']:
			self.args['INPUT_FILE'] = args['INPUT_FOLDER']
			self.args['INPUT_FOLDER'] = os.path.dirname(os.path.abspath(args['INPUT_FOLDER']))




	@staticmethod
	def apply_modification(filename, delta ):
		""" Modify the input file with the delta lines. """

		if delta == {}:
			print (filename, " : delta file empty")

		else:

			with codecs.open(filename, "r", encoding="cp1252" ) as f:
				source_code =  list(f.readlines())
				f.close()
			
			for line_index in delta:
				# Print debug
				# """print   '_+_', source_code[ int(line_index) ],  
				# 		'---', delta[line_index]["ante"],		
				# 		'+++', delta[line_index]["post"] """

				source_code[ int(line_index) ] = delta[line_index]["post"]


			with codecs.open(filename, "w", encoding="cp1252") as f:
				f.writelines(source_code)
			



	def process_file( self, filename ):
		""" Iterate over source lines to look for modifications """
		file_diff = {}
		source_code =  open(filename, "r").readlines()


		for line_idx, line in enumerate(source_code):
			linediff = self.sed.parse(line)

			if linediff != line:
				file_diff[line_idx] = { "ante" : line, "post" : linediff}

		return file_diff


	def process(self):
		""" Iterate over source files to look for modifications """

		if '-f' in self.args and self.args['-f']:
			self.JSON[self.args['INPUT_FILE']] = self.process_file(self.args['INPUT_FILE'])
		else:
			with cd(self.args['INPUT_FOLDER']):

				types = ("*.h", "*.cpp", "*.inl") 
				for filename in multiple_file_types(*types):
					self.JSON[filename] = self.process_file(filename) 
		
	
	def save(self):
		""" Write the differences to a file. """
		with open(os.path.join(self.args['<gen_path>'],self.args['<gen_name>']) + ".json" , "wb") as ofile :
			ofile.write( bytes(self.__str__(), 'utf-8') )
		
		self.pprint()

	def pprint(self):
		"""
			Pretty printing of the json diff object, to be easily
			modifiable by humans.
		"""
		with open(os.path.join(self.args['<gen_path>'],self.args['<gen_name>']) + ".diff", "wb") as ofile :
			for f in sorted(self.JSON) : 
				if self.JSON[f] != {} : 
					ofile.write(  bytes(f + "\n", 'utf-8') )

					for line in self.JSON[f]:
						ofile.write( bytes( "" +  str(line)  + " :\n", 'utf-8') )
						ofile.write( bytes( "" + '---' +  self.JSON[f][line]["ante"] + 
						 			 		"" + '+++' +  self.JSON[f][line]["post"] +  "\n", 'utf-8') )


	def __str__(self):
		""" 
			JSON serialisation, for easy data loading/saving.
		"""
		return json.dumps(self.JSON,  sort_keys = True, indent = 4, separators= (',', ': ') )


	def apply(self):
		""" 
			Given a diff , checkout the files and apply the inline modifications.
			Optional checkin in the future.
		"""

		if {} == self.JSON:
			return

		if '-f' in self.args and self.args['-f']:
			print(self.args['INPUT_FILE'], end="")
			try:
				DiffManager.apply_modification(self.args['INPUT_FILE'], self.JSON[self.args['INPUT_FILE']])
				print(" modified")
			except IOError as e: 
				print(" not modified : {0}".format(e))
		else:
			with cd(self.args['INPUT_FOLDER']):

				for fname in filter( lambda f:  self.JSON[f] != {},  sorted(multiple_file_types(*("*.h", "*.cpp", "*.inl"))) ):
					print(fname, end="")
					try:
						DiffManager.apply_modification( fname, self.JSON[fname] )
						print(" modified")
					except IOError as e: 
						print(" not modified : {0}".format(e))
					



if __name__ == '__main__':

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
	
	dm = DiffManager(**arguments)
	dm.process()
	dm.save()

	if arguments['-a']:
		dm.apply()
