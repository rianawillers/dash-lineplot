#clean a precisely defined set of files from a precisely defined directory set.
#the specified files are deleted, after the user has been prompted

import os.path, fnmatch
import sys

################################################################
#lists the files in a directory and subdirectories
#this code is adapted from a recipe in the Python Cookbook
def listFiles(root, patterns='*', recurse=1, return_folders=0, useRegex=False):
    """Lists the files/directories meeting specific requirement

        Returns a list of file paths to files in a file system, searching a 
        directory structure along the specified path, looking for files 
        that matches the glob pattern. If specified, the search will continue 
        into sub-directories.  A list of matching names is returned. The 
        function supports a local or network reachable filesystem, but not URLs.

    Args:
        | root (string): directory root from where the search must take place
        | patterns (string): glob/regex pattern for filename matching. Multiple pattens 
          may be present, each one separated by ;
        | recurse (unt): flag to indicate if subdirectories must also be searched (optional)
        | return_folders (int): flag to indicate if folder names must also be returned (optional)
        | useRegex (bool): flag to indicate if patterns areregular expression strings (optional)

    Returns:
        | A list with matching file/directory names

    Raises:
        | No exception is raised.
    """
    if useRegex:
        import re

    # Expand patterns from semicolon-separated string to list
    pattern_list = patterns.split(';')
    filenames = []
    filertn = []

    if sys.version_info[0] < 3:

        # Collect input and output arguments into one bunch
        class Bunch(object):
            def __init__(self, **kwds): self.__dict__.update(kwds)
        arg = Bunch(recurse=recurse, pattern_list=pattern_list,
                                return_folders=return_folders, results=[])

        def visit(arg, dirname, files):
            # Append to arg.results all relevant files (and perhaps folders)
            for name in files:
                fullname = os.path.normpath(os.path.join(dirname, name))
                if arg.return_folders or os.path.isfile(fullname):
                    for pattern in arg.pattern_list:
                        if useRegex:
                            #search returns None is pattern not found
                            regex = re.compile(pattern)
                            if regex.search(name):
                                arg.results.append(fullname)
                                break
                        else:
                            if fnmatch.fnmatch(name, pattern):
                                arg.results.append(fullname)
                                break
            # Block recursion if recursion was disallowed
            if not arg.recurse: files[:]=[]
        os.path.walk(root, visit, arg)
        return arg.results

    else: #python 3
        for dirpath,dirnames,files in os.walk(root):
            if dirpath==root or recurse:
                for filen in files:
                    # filenames.append(os.path.abspath(os.path.join(os.getcwd(),dirpath,filen)))
                    filenames.append(os.path.relpath(os.path.join(dirpath,filen)))
                if return_folders:
                    for dirn in dirnames:
                        # filenames.append(os.path.abspath(os.path.join(os.getcwd(),dirpath,dirn)))
                        filenames.append(os.path.relpath(os.path.join(dirpath,dirn)))

        for name in filenames:
            if return_folders or os.path.isfile(name):
                for pattern in pattern_list:
                    if useRegex:
                        #search returns None is pattern not found
                        regex = re.compile(pattern)
                        if regex.search(name):
                            filertn.append(name)
                            break
                    else:
                        # split only the filename to compare, discard folder path
                        if fnmatch.fnmatch(os.path.basename(name), pattern):
                            filertn.append(name)
                            break
    return filertn

#function to delete files in specified directory
#  first parameter defines if the search must be recursively 0=not, 1=recursive
#  second parameter specifies the path
#  third parameter specifies the file patterns to erase
#  the user is promted before the files are deleted
def QueryDelete(recurse,dir,patn):
    thefiles = listFiles(dir, patn,recurse)
    if len(thefiles)>0:
        for filename in thefiles:
            print(filename)
        if sys.version_info[0] < 3:
            instr=raw_input("Delete these files? (y/n)")
        else:
            instr=input("Delete these files? (y/n)")

        if instr=='y':
            for filename in thefiles:
                os.remove(filename)
   


#we take the conservative approach and do not do blanket erase, 
#rather do it by type, asking the user first
QueryDelete(1,'.', '*.ps')
QueryDelete(1,'.', '*.log')
QueryDelete(1,'.', '*.bbl;comment.cut')
QueryDelete(1,'.', '*.bbl;*.sav;*.bak;*.synctex;*.log;*.svn')
QueryDelete(1,'.', '*.blg;*.dfn;*.smb;*.bak;*.aux;*.out;*.lot;*.lof;*.toc;*.tex.bak;*.dvi;*.efc;Backup_of_*.*;*.abr')





