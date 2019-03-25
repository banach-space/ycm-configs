# ycm-configs
Config files for YouCompleteMe

At present consists of one `.ycm_extra_conf.py` file tweaked for LLVM.

To use, copy the file first to your LLVM build directory:
```
$ cp configs/llvm_ycm_extra_config.py <LLVM_BUILD_DIR>/.ycm_extra_config.py
```
Next, set the `COMPILATION_DATABASE_FOLDER` variable inside the script, and
re-run the YouCompleteMe server:
```
: YcmRestartServer
```
This particular `.ycm_extra_conf.py` file makes sure that for every LLVM header
file, YouCompleteMe knows where to look for the corresponding source file.
