import argparse
import subprocess

def main(args):
    print(args)

if __name__ == "__main__":
    # Create the parser
    parser = argparse.ArgumentParser(description="Teste")
    
    # Add arguments
    parser.add_argument('--github-action', type=bool, help='Is it github actions?', default=False, required=False)
    parser.add_argument('--compare-branch', type=str, help='Branch the PR will be open to', default="", required=False)
    parser.add_argument('--files', type=str, help='Files to check', default="", required=False)
    parser.add_argument('--verbose', action='store_true', help='Enable verbose output')

    # Parse the arguments
    args = parser.parse_args()

    # Call the main function with the parsed arguments
    
    main(args)