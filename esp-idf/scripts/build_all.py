#!/usr/bin/python3

import glob
import os
import subprocess
import shutil


# User configurable variables
ghidra_home = "/home/austinc/Desktop/yolink_ghidra_stuff/ghidra_10.4_DEV"
if not os.path.exists(ghidra_home):
    ghidra_home = "/Users/austinc/Desktop/yolink_ghidra_stuff/ghidra_10.4_DEV"

ghidra_project_name = "esp-idf_rizzo_func_sig"  # should not exist and will be created

# Get current dir
base_dir = os.getcwd()

# Dirs used for this script
examples_dir = os.path.join(base_dir, "examples")
ghidra_scripts_path = os.path.join(base_dir, "../", "ghidra_addins", "ghidra_scripts", "ghidra_rizzo")
ghidra_project_dir = os.path.join(base_dir, "ghidra", ghidra_project_name)
rizzo_out = os.path.join(base_dir, "rizzo_out")

# Ghidra included paths
ghidra_headless_subpath = "support/analyzeHeadless"
ghidra_headless_path = os.path.join(ghidra_home, ghidra_headless_subpath)

# Make dirs needed
os.mkdir(ghidra_project_dir)
os.mkdir(rizzo_out)

# Move into examples dir
os.chdir(examples_dir)

# Find all the readme's (Used to determine where a project lives)
example_project_glob = glob.glob('./**/README.md', recursive=True)

# Empty project list
example_projects = []

# Make full paths
for index, example_project in enumerate(example_project_glob):
    
    # Just use the dir for the project
    full_path = os.path.dirname(os.path.normpath(os.path.join(examples_dir, example_project)))
    
    # Used to skip the root dir where this is being run
    if not full_path == examples_dir:
        example_projects.append(full_path)

# Used for status output
example_project_count = len(example_projects) - 1

# Go into each project and build it
for index, example_project in enumerate(example_projects):
    
    # Status output
    print("\n\n\n\n\nBuilding example project {index} of {example_project_count}: {example_project}\n\n\n\n\n"
          .format(index=index+1, example_project_count=example_project_count+1, example_project=example_project))
    
    # Move into the project dir
    os.chdir(example_project)

    # No need to overwrite the file if its already there
    if not os.path.isfile("build_helper.sh"):
        
        # Place a helper build script to source export.sh first
        build_helper_script = open("build_helper.sh", "a")
        build_helper_script.write("#!/bin/bash\n")
        build_helper_script.write("source ~/esp/esp-idf/export.sh\n")
        build_helper_script.write("idf.py build\n")
        build_helper_script.close()

        # Make it executable
        subprocess.run(["chmod", "+x", "./build_helper.sh"], stdout=open(os.devnull, 'wb'))

    # Build the project
    subprocess.run(["./build_helper.sh"])

# Move into examples dir
os.chdir(examples_dir)

# Find all the readme's (Used to determine where a project lives)
elf_glob = glob.glob('./**/*.elf', recursive=True)

elf_count = len(elf_glob) - 1

# Go get the elfs
for index, elf in enumerate(elf_glob):
    elf = os.path.normpath(os.path.join(examples_dir, elf))

    if os.path.basename(elf) == "bootloader.elf":
        # Bootloader
        project_name = os.path.normpath(elf).split(os.path.sep)[-4]
    else:
        # App
        project_name = os.path.normpath(elf).split(os.path.sep)[-3]
    
    new_elf = os.path.normpath(elf).split(os.path.sep)
    new_elf[-1] = str(index) + "-" + project_name + "-" + os.path.basename(elf)
    new_elf = os.path.normpath(os.path.join("/", *new_elf))
    os.rename(elf, new_elf)

    out_file = os.path.join(rizzo_out, str(os.path.basename(new_elf) + ".riz"))
    subprocess.run(["touch", out_file])

    # Status output
    print("\n\n\n\n\nImporting/Analyzing/Generating Rizzo Signatures for elf {index} of {elf_count}: {elf}\n\n\n\n\n"
          .format(index=index+1, elf_count=elf_count+1, elf=new_elf))

    # "-recursive " can be added to below command between -import and -scriptPath if needed
    command = [ghidra_headless_path,
               ghidra_project_dir,
               ghidra_project_name,
               "-import", new_elf,
               "-scriptPath", ghidra_scripts_path,
               "-postScript", "RizzoSave.py", out_file]

    subprocess.run(command)