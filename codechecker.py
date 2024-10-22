import argparse
import os

CODECHECKER_TEXT = """
{
	"analyze": [
		"--disable-all",
		"--enable=bugprone-unchecked-optional-access",
		"--jobs=10",
		"--clean",
		"--ignore=skipfiles"
	],
	"parse": [
		"--ignore=skipfiles"
	]
}
"""


def execute_github_codechecker(files:str):
    BASE_PATH = os.path.dirname(os.path.abspath(__file__))

    #splitting files and filtering for .cpp
    files = files.split(" ")
    files = [file for file in files if file.find(".cpp") > 0]

    #writing skipfiles
    arq = open(f"{BASE_PATH}/skpifiles", "w")
    for file in files:
        arq.write(f"+*/{file}\n")
    arq.write("-*/*\n")
    arq.close()

    
    if not os.path.isfile(f"{BASE_PATH}/codechecker.json"):
        arq = open(f"{BASE_PATH}/codechecker.json", "w")
        arq.write(CODECHECKER_TEXT)
        arq.close()

def main(args):
    if args.github_action and args.files !="":
        execute_github_codechecker(args.files)
    print(args)

if __name__ == "__main__":
    # Create the parser
    parser = argparse.ArgumentParser(description="Teste")
    
    # Add arguments
    parser.add_argument('--github_action', type=bool, help='Is it github actions?', default=False, required=False)
    parser.add_argument('--compare_branch', type=str, help='Branch the PR will be open to', default="", required=False)
    parser.add_argument('--files', type=str, help='Files to check', default="", required=False)
    parser.add_argument('--verbose', action='store_true', help='Enable verbose output')

    # Parse the arguments
    args = parser.parse_args()

    # Call the main function with the parsed arguments
    
    main(args)