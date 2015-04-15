import re
import functools
import abc
try:
    from itertools import izip as zip
except ImportError: # will be 3.x series
    pass


'''	-------------------------
		TOOLS
   	-------------------------
'''
def compose(*functions):
	'''
		Compose a list of functions : f(g(h(...z(x))))
		Used to chain the parsers.
	'''
	return functools.reduce(lambda f, g: lambda x: f(g(x)), functions)

def pairwise(iterable):
    "s -> (s0,s1), (s2,s3), (s4, s5), ..."
    a = iter(iterable)
    return zip(a, a)

def backiter(iterable):
	'''
		Back iterator. Since we insert new text in the line string based on 
		index, we have to read from right to left in order to conserve the indexing.
	'''
	for m in [ m for m in iterable ][::-1]:
		yield m



'''	-------------------------
		Parsers
   	-------------------------
'''
class AbstractSed (object):
	__metaclass__ = abc.ABCMeta

	'''
		Abstract class for a line parser. It's just here to tell the dev
		to use an object with a parse method
	'''
	
	def __init__(self):
		pass

    
	@abc.abstractmethod
	def parse(self, linefeed):
		""" parse a line string and modify it"""
		return linefeed


class SimpleSed(AbstractSed):
	'''
		Simple substitution, aka Ctrl-F Ctrl-H.
		Can be used with regex input.
	'''
	def __init__(self, term_to_look_for, substitution_term ):
		AbstractSed.__init__(self)
		self.ctrlf = term_to_look_for
		self.ctrlh = substitution_term


	def parse(self, linefeed):
		return re.sub(self.ctrlf, self.ctrlh, linefeed)


class AddArgsSed(AbstractSed):
	'''
		A bit more complex line parser, where it locate the arguments
		following the term to remplace, and add new arguments.
	'''

	def __init__(self, term_to_look_for, substitution_term, new_args):
		AbstractSed.__init__(self)
		self.ctrlf = term_to_look_for
		self.ctrlh = substitution_term
		self.args  = new_args

	
	def find_enclosing_parenthesis(self, line,  index):
		'''
			Retun the positions of the following function arguments, enclosed by
			parenthesis.
		'''
		open_par = 0
		par_counter = 0
		cur_idx = index 
		line_length = len(list(line));

		while (not open_par or par_counter) and cur_idx <= line_length:
		
			if '(' == line[cur_idx]:
				
				if not open_par:
					open_par = cur_idx

				par_counter += 1
	
			elif ')' == line[cur_idx]  :
				par_counter -= 1

			cur_idx+=1

		if cur_idx == line_length :
			return None # pb in formating line (or multiline ?)
		else:
			return (open_par, cur_idx)



	def parse(self, linefeed):
		'''
			Parse the input linefeed. Look for the search term, replace it and
			add the new arguments to the list of existing ones.
		'''

		diff = linefeed
		pattern = re.compile(self.ctrlf)
		
		for match in backiter( pattern.finditer(linefeed) ) :

			par_pos =  self.find_enclosing_parenthesis( linefeed , match.end(0) )
			if None != par_pos:
				start, end = par_pos

				diff = diff[: end - 1 ] + self.args  + diff[ end - 1 :]


			diff = diff[:match.start(0)] + self.ctrlh  + diff[match.end(0):]


		return "".join(diff)


class RawStringSed(AbstractSed):
	'''
		Special line parser which add the "_TEXT" macro to raw string in the
		source code, where it hasn't already be made. Avoid comments and includes.
	'''

	def parse(self, linefeed):
		''' 
			Check for edge cases to exclude :
				- no raw string in the line
				- the line is a #include line 
				- the raw string has been commented out.

			Do not check : 
				- multiline comment (ala /* */ style)
				- if the raw string is in a fprintf (which can be harmful).

			Encapsulate every raw strings (i.e. "...") with the _TEXT macro.
		'''

		# Exclusion list
		index = linefeed.find("\"")
		has_include = "#include" in linefeed
		has_comment_before = ( -1 != linefeed.find("//") and 
							   -1 != linefeed.find("\"") and
							   linefeed.find("//") < linefeed.find("\"") )
		
		if (-1 == index or has_include or has_comment_before ):
			return linefeed
		


		# Replacement
		pattern = re.compile(r"\"")
		diff = list(linefeed)

		""" check if the current raw string is prefixed """
		test_prefix = lambda line, idx, prefix: idx >= len(prefix) and  prefix == line[ idx - len(prefix) : idx]

	
		for end,start in pairwise( backiter(pattern.finditer(linefeed)) ):

			# look for previously updated raw strings with _TEXT or _T prefix 
			if test_prefix(linefeed, start.start(0), "_TEXT(") or test_prefix(linefeed, start.start(0), "_T("):
				continue
			# '''extern C''' escape 
			elif "\"C\"" == linefeed[start.start(0):end.end(0)] and test_prefix(linefeed, start.start(0), "extern " ):
				continue
			# Looking for the escape char \ which break the regex.
			elif test_prefix(linefeed, start.start(0), "\\") or test_prefix(linefeed, end.end(0), "\\\"") :
				# TODO : start looking backwards for the right starting quote
				continue
			else:
				diff.insert(end.end(0),")" )
				diff.insert(start.start(0),"_TEXT(")

	
	
		return "".join(diff)




'''	-------------------------
		Chainer
   	-------------------------
'''
class MultiSed(AbstractSed, list):
	'''
		List of seds objects, composed in order to chain the parsing.
	'''

	def parse(self, linefeed):
		chainedparse = compose( *[s.parse for s in self] )
		return  chainedparse(linefeed) 