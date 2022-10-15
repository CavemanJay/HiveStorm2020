import sys
import os


def readfile(path):
    """Will read a file from the specified path. 
    Exits the program if the file cannot be found

    Args:
        path (string): The path of the file to read

    Returns:
        The contents of the file as a single string
    """
    try:
        with open(path) as file:
            return file.read()
    except IOError as ex:
        print(" ".join(str(ex).split(' ')[2:]))
        sys.exit(ex.errno)


def exit():
    """Exit the program with error code 1"""
    sys.exit(1)


def shcmd(cmd):
    """Runs a shell command

    Args:
        cmd (string): The command to run

    Returns:
        string: The resulting stdout of the command
    """
    return os.popen(cmd).read()


def print_red(text):
    print("\033[91m{}\033[0m".format(text))


def print_green(text):
    print("\033[92m{}\033[0m".format(text))


def print_yellow(text):
    print("\033[93m{}\033[0m".format(text))

def read_passwd():
    with open('/etc/passwd') as f:
        return f.readlines()

def read_shadow():
    with open('/etc/shadow') as f:
        return f.readlines()