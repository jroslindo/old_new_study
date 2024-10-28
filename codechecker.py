#!/usr/bin/env python3.11

import argparse
import os
import sys
import subprocess
import json

verbose = False
BASE_PATH = os.path.dirname(os.path.abspath(__file__))
CODECHECKER_TEXT = """
{
	"analyze": [
		"--disable-all",
        "--disable=alpha",
        "--disable=bugprone",
        "--disable=cert-err60-cpp",
        "--disable=clang-diagnostic",
        "--disable=google",
        "--disable=performance",
        "--disable=readability",
		"--disable=cppcoreguidelines",
		"--enable=bugprone-unchecked-optional-access",
		"--jobs=8",
		"--clean",
		"--ignore=skipfiles"
	],
	"parse": [
		"--ignore=skipfiles"
	]
}
"""

DESCRIPTION_HELP = """
This is a script to run CodeChecker analyzer inside fusion project.
Performs the following operations:
    - Helps github actions.
    - Works as a local analyzer for devs.
Please do not use git action mode.

Commands usage:
Calling just ./codechecker.py will trigger the anylize in files unstaged.
Calling with the argument --analyze=git_branch will check the diff between your last commit and the specified branch.
Using --force will create generated classes and compile_commands, this may take a while because the compile commands uses make all.
Using --verbose will display the full output of all commands used. Use it if you find troubles executing.
"""


def create_skipfiles_codechecker_config(files:list[str]):
    #writing skipfiles
    arq = open(f"{BASE_PATH}/skipfiles", "w")
    for file in files:
        arq.write(f"+*/{file}\n")
    arq.write("-*/*\n")
    arq.close()

    
    if not os.path.isfile(f"{BASE_PATH}/codechecker.json"):
        arq = open(f"{BASE_PATH}/codechecker.json", "w")
        arq.write(CODECHECKER_TEXT)
        arq.close()

def execute_github_codechecker(files:str):
    #splitting files and filtering for .cpp
    files = files.split(" ")
    files = [file for file in files if file.find(".cpp") > 0]
    create_skipfiles_codechecker_config(files)

def grep_different_files(branch:str)->list[str]|None:
    #Looking for differences into another branch
    try:
        if branch != "":
            result = subprocess.run(
                ["git", "diff", "--name-only", branch],
                check=True,
                text=True,  # Ensures output is returned as a string
                capture_output=True,  # Capture standard output and error
                cwd="../../../../"
            )
        else:
            result = subprocess.run(
                ["git", "diff", "--name-only"],
                check=True,
                text=True,  # Ensures output is returned as a string
                capture_output=True,  # Capture standard output and error
                cwd="../../../../"
            )
        # Retrieve the output
        changed_files = result.stdout.strip().splitlines()
        
        if len(changed_files)==0:
            print("No changes found, exiting...")
            sys.exit()

        return changed_files
    except subprocess.CalledProcessError as e:
        print("Error collecting branch differences:", e)
        print("finishing the application with error.")
        sys.exit()

def filter_files(changed_files: list[str])->list[str]:
    arq = open(f"{BASE_PATH}/ignores.txt", "r")
    ignores = arq.readlines()
    arq.close()
    
    filtered_files = []
    for file in changed_files:
        if file.find(".cpp") >0: #if its a cpp
            should_ignore= False
            for ignore in ignores:
                if file.find(ignore[:-1]) != -1: #if it's not a ignored file
                    should_ignore = True
            
            if not should_ignore:
                filtered_files.append(file)

    if len(filtered_files) == 0:
        print("No changes found after filtering, exiting...")
        sys.exit()

    return filtered_files


def read_skipfiles_from_txt():
    arq = open(f"{BASE_PATH}/files.txt", "r")
    ignores = arq.readlines()
    arq.close()
    
    return ignores

def evaluate_results()->bool:
    """
        Return True if there are bugs
    """
    if os.path.isfile(f"{BASE_PATH}/../../../../build/shell/fusionIV-debug/reports.json"):
        try:
            with open(f"{BASE_PATH}/../../../../build/shell/fusionIV-debug/reports.json", "r") as result_files:
                results_json : dict = json.load(result_files)
        except:
            print("Problem checking results. Exiting...")
            sys.exit()
    else:
        print("reports.json not found. Exiting...")
        sys.exit()
    
    if len(results_json.get("reports", [])) == 0:
        print("No bugs found.")
        return False
    print("Bugs found!!!")
    return True


def analyze_single_PR(branch:str, force:bool):
    global verbose
    std_argument = subprocess.DEVNULL
    if verbose:
        std_argument = None

    #Generating makefiles
    if force or not os.path.isdir(f"{BASE_PATH}/../../../fusion-web-services/generated-code/"):
        print("Generating files.")
        commands = [
            ["sudo", f"{BASE_PATH}/../../../../build/shell/fusionIV-debug/ws_generate.sh"],
            ["sudo", f"{BASE_PATH}/../../../../typegen-scripts/run-typegen.sh", "-dev"],
            ["sudo", f"{BASE_PATH}/../../../../build/shell/fusionIV-debug/gen_qmake.sh"]
        ]

        for command in commands:
            try:
                subprocess.run(command, check=True, stdout=std_argument, stderr=std_argument)
            except subprocess.CalledProcessError as e:
                print(f"Error executing command: {command}. Error: {e}")
                print("finishing the application with error.")
                sys.exit()

    #Detecting diff between branchs, creating skipfiles and codechecker.json - this needs a update
    print("Finding differences")
    changed_files = grep_different_files(branch)
    filtered_files = filter_files(changed_files)

    # Let's create our main files of CodeChecker
    create_skipfiles_codechecker_config(filtered_files)

    print("Changed files already filtered:")
    for file in filtered_files:
        print(f"-    {file}")
    print()
    input("press enter to continue or finish with ctrl+c:")

    # Executing log, analyze and parse
    commands = []
    if force or not os.path.isfile(f"{BASE_PATH}/../../../../build/shell/fusionIV-debug/compile_commands.json"): # Do we need to generate compile_commands?
        print("Generating compile commands... This may take a while!")
        commands.append(["sudo", "chmod", "-R", "777", f"{BASE_PATH}/../../../../"]),
        commands.append(["sudo", "make", "clean"]),
        commands.append(["CodeChecker", "log", "--build", f"make -j{os.cpu_count()-2}", "--output", "./compile_commands.json"])
    commands.append(["CodeChecker","analyze","./compile_commands.json","--output","./reports","--config","codechecker.json"])
    commands.append(["CodeChecker","parse","--export","html","--output","./reports_html","./reports","--config","codechecker.json"])
    commands.append(["CodeChecker","parse","--export","json","--output","./reports.json","./reports","--config","codechecker.json"])

    for command in commands:
        try:
            check = True
            if command in commands[-2:]:
                print("Parsing...")
                check = False

            if command == commands[-3]:
                print("Analyzing...")

            subprocess.run(
                command, 
                check=check,
                cwd=f"{BASE_PATH}/../../../../build/shell/fusionIV-debug/",
                stdout=std_argument,  # Mute standard output
                stderr=std_argument   # Mute standard error
            )
        except subprocess.CalledProcessError as e:
            print(f"Error executing command: {command}. Error: {e}")
            print("finishing the application with error.")
            sys.exit()
    
    if evaluate_results():
        print("Openning firefox to check results")
        os.environ['MESA_GLTHREAD'] = 'false'
        subprocess.Popen(
            ["firefox", f"{BASE_PATH}/../../../../build/shell/fusionIV-debug/reports_html/statistics.html"]
        )

    print("ANALYIZES FINISHED")


def check_args(args):
    #Git action mode
    if args.github_action:
        if args.files == "":
            print("For git action mode files is required.")
            sys.exit()
    else: #Local mode
        if args.analyze != "":
            print(f"Analyzing branch: {args.analyze}")
        else:
            print("Running analyzes with unstaged changes")

        if args.force == True:
            print("Will run the full setup, this may take a while.")


def main(args):
    # Check if there's anything wrong if arguments
    check_args(args)
    # Local or git?
    if args.github_action and args.files !="":
        execute_github_codechecker(args.files)
    else:
        analyze_single_PR(args.analyze, args.force)

if __name__ == "__main__":
    # Create the parser
    parser = argparse.ArgumentParser(description= DESCRIPTION_HELP, formatter_class=argparse.RawTextHelpFormatter)
    
    # Add arguments
    parser.add_argument('--github_action', type=bool, help='Is it github actions?', default=False, required=False, action=argparse.BooleanOptionalAction)
    parser.add_argument('--analyze', type=str, help='Branch the PR will be open to', default="", required=False)
    parser.add_argument('--files', type=str, help='Files to check', default="", required=False)
    parser.add_argument('--force', type=bool, help='Execute the full setup, good for first time', default=False, required=False, action=argparse.BooleanOptionalAction)
    parser.add_argument('--verbose', type=bool, help='Enable verbose output', default=False, required=False, action=argparse.BooleanOptionalAction)

    # Parse the arguments
    args = parser.parse_args()
    
    verbose = args.verbose
    
    # Call the main function with the parsed arguments
    main(args)