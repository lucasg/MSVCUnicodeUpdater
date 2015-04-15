# MSVCUnicodeUpdater
A Python CLI useful for updating a legacy C++ codebase in order to get full Unicode support


This project cater for thoses who need to upgrade existing code in order to support multi-bytes encodings with MVSC. It basically involves adding several macros (_T or _TEXT) around raw strings and using _TCHAR independant functions like _ttoi instead of atoi. Since it's a tedious and repetitive task, it can be greatly sped up by automating the detection and replacement part. Of course, the verification part is left to the human eye (not every char array is a string).

More info on _UNICODE support :
 - https://msdn.microsoft.com/library/2dax2h36.aspx
 - https://msdn.microsoft.com/library/vstudio/c426s321


The python files were written for Python3, but it can be backported to Python2.xx quite easily. diff.py and updater.py relies on docopt for command-line arguments management, so docopt need to be present.

Files : 
 - sed.py : every little replacement rules
 - diff.py : given a folder containing sources files, diff.py produces a json file with every modification (machine readable) and a diff file (human readable). 
 			 Look at example_output.json & example_output.diff for a sample.
 - updater.py : updater is a script built on top of diff.py which also check-out sources file from SourceSafe before-hand.
 - vss.py : a SourceSafe automation bot copied from somewhere on Internet, and catered to this project's needs.

```
	Usage:
		diff.py [-arf] [-n <gen_name>|--name <gen_name>] [-o <gen_path>|--output <gen_path>] (INPUT_FOLDER)
		updater.py [-arf] [-n <gen_name>|--name <gen_name>] [-o <gen_path>|--output <gen_path>] (INPUT_FOLDER)
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
		-file
			work on a single file (instead of folder)
```

