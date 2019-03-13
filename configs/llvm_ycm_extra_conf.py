'''
Basic .ycm_extra_conf.py for LLVM

To get the most out of YouCompleteMe when using it to navigate through LLVM,
make sure that you generate a compile_commands.json file in your build
directory.

You can get CMake to generate this file for you by running:
   $ cmake -DCMAKE_EXPORT_COMPILE_COMMANDS=1
(during or after the initial configuration and generation). See here for more
details:
    http://clang.llvm.org/docs/JSONCompilationDatabase.html

Although YouCompleteMe can be used witout a compilation database, your milege
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
import ycm_core

# These are the compilation flags that will be used in case there's no
# compilation DATABASE set (by default, one is not set).
DEFAULT_FLAGS = ['-x', 'c++', '-Wall', '-Wextra', '-Werror']

# Set this to the absolute path to the folder (not the file!) containing the
# compile_commands.json file to use that instead of 'DEFAULT_FLAGS'. This is
# normally the LLVM build directory.
COMPILATION_DATABASE_FOLDER = ''

if os.path.exists(COMPILATION_DATABASE_FOLDER):
    DATABASE = ycm_core.CompilationDatabase(COMPILATION_DATABASE_FOLDER)
else:
    DATABASE = None

SOURCE_EXTENSIONS = ['.cpp', '.cxx', '.cc', '.c', '.m', '.mm']

def IsHeaderFile(filename):
    '''
    Returns true if `filename` is a header file.
    '''
    _, extension = os.path.splitext(filename)
    return extension in ['.h', '.hxx', '.hpp', '.hh']


def FindCorrespondingLLVMSourceFile(filename):
    '''
    For LLVM source files returns the input param (because it already
    represents a source file). For an LLVM header file `filename`, finds the
    corresponding LLVM source file using the following heuristics:
        * replace `include/llvm` with `lib/Support`
    '''
    if IsHeaderFile(filename):
        header_dir, header_file = os.path.split(filename)
        header_dir_split = header_dir.split('/')
        include_idx = header_dir_split.index('include')

        # Generate the source file directory
        source_dir_split = header_dir_split.copy()
        source_dir_split[include_idx] = 'lib'
        source_dir_split[include_idx+1] = 'Support'
        source_dir_split.pop()
        source_dir = os.path.join('/', *source_dir_split)

        header_file_name, _ = os.path.splitext(header_file)
        for ext in SOURCE_EXTENSIONS:
            replacement_file = os.path.join(source_dir, header_file_name + ext)
            if os.path.exists(replacement_file):
                return replacement_file
    return filename


def FlagsForFile(filename):
    '''
    Return compiler flags for file `filename`.
    '''
    # If the file is a header, try to find the corresponding source file and
    # retrieve its flags from the compilation DATABASE if using one. This is
    # necessary since compilation DATABASEs don't have entries for header
    # files.  In addition, use this source file as the translation unit. This
    # makes it possible to jump from a declaration in the header file to its
    # definition in the corresponding source file.
    filename = FindCorrespondingLLVMSourceFile(filename)

    if not DATABASE:
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
