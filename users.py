#!/usr/bin/python3

import getopt
import os
import sys


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


def getusers():
    """Returns the list of users from /etc/passwd that contain login shells
    ending with 'sh'

    Returns:
        list: A list of users
    """
    # Read the file
    entries = readfile('/etc/passwd').split('\n')
    # Get all lines that end with sh
    entries = [e for e in entries if e.endswith('sh')]
    # Return the list of usernames
    users = [x.split(':')[0] for x in entries]
    return users


def get_sudoers():
    """Returns a list of users capable of running sudo

    Returns:
        list: List of system usernames
    """
    sudoers = []

    users = getusers()
    for user in users:
        cmd = f"sudo -l -U {user}"
        stdout = shcmd(cmd)
        if "not allowed" not in stdout:
            sudoers.append(user)

    return sudoers


def get_unauth_users(path):
    """Gets a list of unauthorized users by comparing the current users on the system
    to the contents of a file

    Args:
        path (string): The path of the newline-separated authorized users list

    Returns:
        list: The list of unauthorized users
    """
    current_users = getusers()
    allowed_users = readfile(path)
    unauth = [u for u in current_users if u not in allowed_users]
    unauth.remove('root')
    return unauth


def get_non_admins(path):
    """Returns a list of users that currently have sudo capabilities that shouldn't

    Args:
        path (string): The path to a newline-separated list of authorized sudoers

    Returns:
        list: The list of people who should be removed from sudo group
    """
    sudoers = get_sudoers()
    # Get list of allowed admins
    allowed_admins = readfile(path).split('\n')
    # Return list of users that are not in that list
    invalid_admins = [user for user in sudoers if user not in allowed_admins]
    invalid_admins.remove('root')

    return invalid_admins


def remove_unauth(unauth):
    """Removes a list of users from the system

    Args:
        unauth (list): List of unauthorized users
    """
    for user in unauth:
        print(f'Deleting user: {user}')
        delcmd = f'sudo deluser --remove-home {user}\n\n'
        print('> ' + delcmd)
        stdout = shcmd(delcmd)
        print(stdout)


def change_passwords(users, password="Password123#!"):
    """Changes the password of all users specified to the password supplied.
    Does not change the password for the current user

    Args:
        users (list): The list of users
        password (str, optional): The password to set for all users. Defaults to "Password123#!".
    """
    # Strip newline character from echo command
    current_user = shcmd("echo $USER").strip()
    for user in users:
        # Don't change the password for current user
        if user == current_user:
            continue
        password = 'Password123#!'
        cmd = f"echo '{user}:{password}' | sudo chpasswd"
        print(f"Changing password for {user}")
        print('> ' + cmd)
        stdout = shcmd(cmd)
        print(stdout)


def remove_sudoers(non_admins):
    """Removes users from the sudo group

    Args:
        non_admins (list): The list of users to remove from the sudo group
    """
    for user in non_admins:
        print(f"Removing admin privileges for: {user}")
        cmd = f"sudo deluser {user} sudo"
        print("> " + cmd)
        stdout = shcmd(cmd)
        print(stdout)


def main(argv):
    """The main function of this program file

    Args:
        argv (list): The cli arguments supplied to this file
    """
    try:
        opts, args = getopt.getopt(argv[1:], "hu:a:", ["users=", "admins="])
    except getopt.GetoptError:
        print(argv[0] + ": Incorrect Syntax, try '-h' for help.")
        sys.exit(2)

    # Set the options based on arguments passed in
    USERFILE = None
    ADMINFILE = None
    for opt, arg in opts:
        if opt == "-h" or opt == "--help":
            print(
                "Usage:\n\n-h --help \n\nRequired:\n[*] -u --users <Authorized Users List Path>\n[*] -a --admins <Admin Users List Path>")
            sys.exit(0)
        elif opt == "-u" or opt == '--users':
            USERFILE = arg
        elif opt == "-a" or opt == '--admins':
            ADMINFILE = arg

    if USERFILE is not None:
        invalid_users = get_unauth_users(USERFILE)
    else:
        print("User file is required.")
        exit()

    # Remove unAuth Users from /etc/passwd
    remove_unauth(invalid_users)

    if ADMINFILE is not None:
        invalid_admins = get_non_admins(ADMINFILE)
        remove_sudoers(invalid_admins)
    else:
        print("Admin file is required.")
        exit()

    # Read /etc/passwd and parse current users
    current_users = getusers()
    change_passwords(current_users)


if __name__ == "__main__":
    main(sys.argv[0:])
