'''
Basic .ycm_extra_conf.py for LLVM (to be used with a compilation database)

To get the most out of YouCompleteMe when using it to navigate through LLVM,
make sure that you generate a compile_commands.json file in your build
directory.

You can get CMake to generate this file for you by running:
   $ cmake -DCMAKE_EXPORT_COMPILE_COMMANDS=1
(during or after the initial configuration and generation). See here for more
details:
    http://clang.llvm.org/docs/JSONCompilationDatabase.html

Although YouCompleteMe can be used without a compilation database, your mileage
will vary.

LICENSE:
 This is free and unencumbered software released into the public domain.

 Anyone is free to copy, modify, publish, use, compile, sell, or
 distribute this software, either in source code form or as a compiled
 binary, for any purpose, commercial or non-commercial, and by any
 means.

 In jurisdictions that recognize copyright laws, the author or authors
 of this software dedicate any and all copyright interest in the
 software to the public domain. We make this dedication for the benefit
 of the public at large and to the detriment of our heirs and
 successors. We intend this dedication to be an overt act of
 relinquishment in perpetuity of all present and future rights to this
 software under copyright law.

 THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
 EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
 MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
 IN NO EVENT SHALL THE AUTHORS BE LIABLE FOR ANY CLAIM, DAMAGES OR
 OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
 ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
 OTHER DEALINGS IN THE SOFTWARE.

 For more information, please refer to <http://unlicense.org/>
'''

import os
import subprocess
import ycm_core

# These are the compilation flags that will be used in case there's no
# compilation DATABASE set (by default, one is not set).
DEFAULT_FLAGS = ['-x', 'c++', '-Wall', '-Wextra', '-Werror']

# Set this to the absolute path to the folder (not the file!) containing the
# compile_commands.json file to use that instead of 'DEFAULT_FLAGS'. This is
# normally the LLVM build directory.
# =========================> IMPORTANT!!!! <================================
#           PROVIDE THE PATH TO THE COMPILATION DATABASE
# =========================> IMPORTANT!!!! <================================
COMPILATION_DATABASE_FOLDER = ''

if os.path.exists(COMPILATION_DATABASE_FOLDER):
    DATABASE = ycm_core.CompilationDatabase(COMPILATION_DATABASE_FOLDER)
else:
    DATABASE = None

LLVM_CPP_SOURCE_EXTENSION = '.cpp'


def is_header_file(filename):
    ''' Returns true if `filename` representes a header file '''
    try:
        _, extension = os.path.splitext(filename)
    except OSError:
        return False
    return extension in ['.h', '.hxx', '.hpp', '.hh']


def header_to_source_dir_support(header_file_dir):
    ''' Takes a header file dir and returns the full path of lib/Support

    Does the following directory transformation:
        in: <LLVM_ROOT>/include/llvm/<LLVM_INCLUDE_SUBDIR>
        out: <LLVM_ROOT>/lib/Support
    The output source directory is a possible location of source files
    corresponding to header files in the input dir.

    Examples of source-header couples for which this approach works:
        * APFLoat.{cpp|h}
        * Optional.{cpp|h}
    '''
    header_dir_split = header_file_dir.split('/')
    try:
        include_idx = header_dir_split.index('include')
    except ValueError:
        # The input file is not a traditional header file (could be
        # <something>.inc.h somewhere in Lib/Target, e.g.
        # SVEISelLowering.inc.h). In such cases just bail out.
        invalid_dir = os.path.join(header_file_dir,
                "SomeDummyStringToInvalidateThePath")
        return invalid_dir

    source_dir_split = header_dir_split.copy()
    source_dir_split[include_idx] = 'lib'
    source_dir_split[include_idx+1] = 'Support'
    source_dir_split.pop()
    source_dir = os.path.join('/', *source_dir_split)

    return source_dir

def header_to_source_dir_clang(header_file_dir):
    ''' Takes a clang header file dir and returns the correspodning source dir

    Does the following directory transformation:
        in: <LLVM_ROOT>/tools/clang/include/clang/<CLANG_INCLUDE_SUBDIR>
        out: <LLVM_ROOT>/tools/clang/lib/<CLANG_INCLUDE_SUBDIR>
    The output source directory is a possible location of source files
    corresponding to header files in the input dir.

    Examples of source-header couples for which this approach works:
        * ParsedAttr.{cpp|h}
    '''
    header_dir_split = header_file_dir.split('/')
    include_idx = header_dir_split.index('include')

    source_dir_split = header_dir_split.copy()
    # Replace 'include' with 'lib'
    source_dir_split[include_idx] = 'lib'
    # Remove 'clang' (the one following 'include')
    del source_dir_split[include_idx+1]
    source_dir = os.path.join('/', *source_dir_split)

    return source_dir


def header_to_source_dir_generic(header_file_dir):
    ''' Takes a header file dir and returns the corresponding source dir

    Does the following directory transformation:
        in: <LLVM_ROOT>/include/llvm/<LLVM_INCLUDE_SUBDIR>
        out: <LLVM_ROOT>/lib/<LLVM_INCLUDE_SUBDIR>
    The output source directory is the most likely location of source files
    corresponding to header files in the input dir.

    Examples of source-header couples for which this approach works:
        * Value.{cpp|h}
    '''
    header_dir_split = header_file_dir.split('/')
    try:
        include_idx = header_dir_split.index('include')
    except ValueError:
        # This file is not a traditional header file (could be
        # <something>.inc.h somewhere in Lib/Target, e.g.
        # SVEISelLowering.inc.h). In such cases just bail out.
        invalid_dir = os.path.join(header_file_dir,
                "SomeDummyStringToInvalidateThePath")
        return invalid_dir

    source_dir_split = header_dir_split.copy()
    source_dir_split[include_idx] = 'lib'
    # Get the index of the last occurrence of "llvm" in the path. This
    # component of the path is only present in header files and appears after
    # "include", e.g. "include/llvm"
    idx = len(source_dir_split) - 1 - source_dir_split[::-1].index('llvm')
    source_dir_split.pop(idx)
    source_dir = os.path.join('/', *source_dir_split)

    return source_dir


def find_llvm_source_file(header_file_path):
    '''
    Finds an llvm source file that corresponds to the input header file

    For most header files there's a corresponding source file, e.g. Value.h and
    Value.cpp. This function returns the path to that source file. If no such
    file exists, then any source file that includes the input header file is
    returned. If that also fails then the input header file is returned.
    '''
    header_file_dir, header_file_base = os.path.split(header_file_path)
    header_file_name, _ = os.path.splitext(header_file_base)

    # Policy #1: Look for the corresponding *.cpp file
    source_dir = header_to_source_dir_generic(header_file_dir)

    source_file = header_file_name + LLVM_CPP_SOURCE_EXTENSION
    replacement_file_path = os.path.abspath(os.path.join(source_dir,
                                                         source_file))

    if os.path.exists(replacement_file_path):
        return replacement_file_path

    # Policy #2: Look for the corresponding *.cpp file
    source_dir = header_to_source_dir_support(header_file_dir)

    source_file = header_file_name + LLVM_CPP_SOURCE_EXTENSION
    replacement_file_path = os.path.abspath(os.path.join(source_dir,
                                                         source_file))

    if os.path.exists(replacement_file_path):
        return replacement_file_path

    # Policy #3: There are no *.cpp files corresponding to this header file.
    # Use any file that includes it instead.
    # The following `grep` command has a separate `--exclude-dir` for each
    # directory. On the command line the following works as well:
    #   $ grep -IlZEr --include=*.cpp --exclude-dir={Target,unittests,tools}
    #   header_file_base
    # I don't know why that doesn't work when running through subprocess
    # module.
    out = subprocess.check_output(["grep", "-IlZEr", "--include=*.cpp",
                                   # Commenting this out for SVEISelLowering.inc.h
                                   # "--exclude-dir=Target",
                                   "--exclude-dir=unittests",
                                   "--exclude-dir=tools",
                                   header_file_base])
    out_list = out.decode('UTF-8').rstrip()
    out_list = out_list.split("\x00")
    out_list.remove("")
    replacement_file_path = os.path.abspath(out_list[int(len(out_list) / 2)])
    if os.path.exists(replacement_file_path):
        return replacement_file_path

    return header_file_path


def find_clang_source_file(header_file_path):
    '''
    Finds an clang source file that corresponds to the input header file

    For most header files there's a corresponding source file, e.g. Value.h and
    Value.cpp. This function returns the path to that source file. If no such
    file exists, then any source file that includes the input header file is
    returned. If that also fails then the input header file is returned.
    '''
    header_file_dir, header_file_base = os.path.split(header_file_path)
    header_file_name, _ = os.path.splitext(header_file_base)

    # Policy #1: Look for the corresponding *.cpp file
    source_dir = header_to_source_dir_clang(header_file_dir)

    source_file = header_file_name + LLVM_CPP_SOURCE_EXTENSION
    replacement_file_path = os.path.abspath(os.path.join(source_dir,
                                                         source_file))

    if os.path.exists(replacement_file_path):
        return replacement_file_path


def FlagsForFile(filename):
    '''
    Return compiler flags for the input file.

    The name does not conform to snake_case style from PEP8, but that's
    required by YouCompleteMe
    '''
    # If the file is a header, try to find the corresponding source file. This
    # is necessary since compilation DATABASEs don't have entries for header
    # files.
    if is_header_file(filename):
        if "include/llvm" in filename:
            filename = find_llvm_source_file(filename)
        elif "tools/clang" in filename:
            filename = find_clang_source_file(filename)

    if not DATABASE or is_header_file(filename):
        return {
            'flags': DEFAULT_FLAGS,
            'include_paths_relative_to_dir':
            os.path.dirname(os.path.abspath(__file__)),
            'override_filename': filename
        }

    compilation_info = DATABASE.GetCompilationInfoForFile(filename)
    if not compilation_info.compiler_flags_:
        return None

    # Bear in mind that compilation_info.compiler_flags_ does NOT return a
    # python list, but a "list-like" StringVec object.
    final_flags = list(compilation_info.compiler_flags_)

    return {
        'flags': final_flags,
        'include_paths_relative_to_dir':
        compilation_info.compiler_working_dir_,
        'override_filename': filename
    }
