# RsyncPython

# Rsync is a command for copying files/folders from source path to destination path.
# The program includs a command line interface for copying multiple files/folders.

# To use the command you need to run: python rsync/run.py 
# Make sure you added the RsyncPython directory to your PYTHONPATH before running the program.

# The program uses argparse for getting input from the user.
# Run pyhton rsync/run.py --help for help

# In order to copy files/folders you need to write each pair of source and destination in this format 'src:dst'
# Each pair needs to be separated by comma
# Example python rsync/run.py --pairs src1:dst1,src2:dst2
# All pairs will be copied in parallel.

# You can add a bandwidth limit if you wish by using the flag --bandwidth
# The default value of bandwidth limit is 10KB per second.

# Notice:
# if source is a file - the destination can be either a file or a directory. 
# By default the program will treat the destination as file, so if you want the destination to be a directory you need to create the directory first.

# If source is a directiry - the destination should be a directory.
# If the destination directory ends with '/' - the content of the source directory will be copied to the destination dirctory.
# If the destination directory doesn't end with '/' - the source directory and all its contents will be copyied to the destination directory.  
