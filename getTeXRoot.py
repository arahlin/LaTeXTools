# ST2/ST3 compat
from __future__ import print_function 
import sublime
if sublime.version() < '3000':
	# we are on ST2 and Python 2.X
	_ST3 = False
else:
	_ST3 = True


import os.path, re
import codecs

# Return RC file from
# (1) TEXrc project setting
# (2) latexmkrc or .latexmkrc file (mimicing latexmk itself)

def get_rc_file(view):
	rcfile = view.settings().get('TEXrc',None)
	if rcfile is not None:
		rcfile = os.path.abspath(rcfile)
		if os.path.isfile(rcfile):
			print("RC file defined in project settings: " + root)
			return rcfile
	
	tex_root = os.path.dirname(get_tex_root(view))
	for f in ['.latexmkrc','latexmkrc']:
		tmpfile = os.path.join(tex_root,f)
		if os.path.isfile(tmpfile):
			rcfile = tmpfile
			print("Found RC file at %s" % rcfile)
			break
	return rcfile

# Return output directory from
# (1) TEXoutdir setting
# (2) RC file in the same directory as TEXroot
# (3) TEXroot's directory

def get_out_root(view):
	root = view.settings().get('TEXout',None)
	if root is not None:
		root = os.path.abspath(root)
		if os.path.isdir(os.path.dirname(root)):
			print("Output directory defined in project settings: " + root)
			return root
	
	rcfile = get_rc_file(view)
	if rcfile is not None:
		fid = codecs.open(rcfile, "r", "UTF-8")
		for line in fid.readlines():
			if "$out_dir" in line and not line.strip().startswith('#'):
				root = eval(line.split("=")[-1].replace(";","").strip())
				print("Output directory defined in RC file: %s" % root)
				if not os.path.isabs(root):
					root = os.path.join(os.path.dirname(rcfile),root)
				root = os.path.normpath(root)
				return root
		fid.close()
	if root is None:
		return os.path.abspath(os.path.dirname(get_tex_root(view)))

# recursively create output directory with appropriate subdirectories

def make_out_root(out_root,working_dir=None):
	if working_dir is None:
		working_dir = os.path.dirname(out_root)
	
	if os.path.normpath(working_dir) == os.path.normpath(out_root):
		return

	files = os.listdir(working_dir)
	# hack -- check if there are tex files in each directory
	# if so, mirror in the build tree
	if any([os.path.splitext(f)[-1].lower() == '.tex' for f in files]):
		if not os.path.isdir(out_root):
			print('Creating %s' % out_root)
			os.mkdir(out_root)
	for f in files:
		ff = os.path.join(working_dir,f)
		if os.path.isdir(ff):
			make_out_root(os.path.join(out_root,f),working_dir=ff)
	
# Return the current tex file in focus
# prompt to save if it doesn't have a filename

def get_tex_file(view):
	texfile = view.file_name()
	if texfile is None:
		sublime.status_message("latexmk: need to save the file to build!")
		view.run_command('prompt_save_as')
		return get_tex_file(view)
	else:
		return texfile

# Parse magic comments to retrieve TEX root
# Stops searching for magic comments at first non-comment line of file
# Returns root file or current file or None (if there is no root file,
# and the current buffer is an unnamed unsaved file)

# Contributed by Sam Finn

def get_tex_root(view):
	root = view.settings().get('TEXroot',None)
	if root is not None:
		root = os.path.abspath(root)
		if os.path.isfile(root):
			print("Main file defined in project settings: " + root)
			return root
	
	texFile = get_tex_file(view)
	root = texFile
	if texFile is None:
		# We are in an unnamed, unsaved file.
		# Read from the buffer instead.
		if view.substr(0) != '%':
			return None
		reg = view.find(r"^%[^\n]*(\n%[^\n]*)*", 0)
		if not reg:
			return None
		line_regs = view.lines(reg)
		lines = map(view.substr, line_regs)
		is_file = False

	else:
		# This works on ST2 and ST3, but does not automatically convert line endings.
		# We should be OK though.
		lines = codecs.open(texFile, "r", "UTF-8")
		is_file = True

	for line in lines:
		if not line.startswith('%'):
			break
		else:
			# We have a comment match; check for a TEX root match
			mroot = re.match(r"%\s*!TEX\s+root *= *(.*(tex|TEX))\s*$",line)
			if mroot:
				# we have a TEX root match 
				# Break the match into path, file and extension
				# Create TEX root file name
				# If there is a TEX root path, use it
				# If the path is not absolute and a src path exists, pre-pend it
				root = mroot.group(1)
				if not os.path.isabs(root) and texFile is not None:
					(texPath, texName) = os.path.split(texFile)
					root = os.path.join(texPath,root)
				root = os.path.normpath(root)
				break

	if is_file: # Not very Pythonic, but works...
		lines.close()

	return root
