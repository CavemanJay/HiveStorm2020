#!/usr/bin/python3

import getopt
from utils import readfile, shcmd, exit
import sys
import re


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
        cmd = "sudo -l -U" + user
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


def remove_unauth(unauth, dry_run):
    """Removes a list of users from the system

    Args:
        unauth (list): List of unauthorized users
        dry_run (bool): Whether or not to follow through with the operation
    """
    for user in unauth:
        print('Deleting user: {}'.format(user))
        delcmd = 'sudo deluser --remove-home {}\n'.format(user)
        print('> ' + delcmd)
        if not dry_run:
            stdout = shcmd(delcmd)
            print(stdout)
        else:
            print("")


def change_passwords(users, dry_run, password="Password123#!"):
    """Changes the password of all users specified to the password supplied.
    Does not change the password for the current user

    Args:
        users (list): The list of users
        dry_run (bool): Whether or not to follow through with the operation
        password (str, optional): The password to set for all users. Defaults to "Password123#!".
    """
    # Strip newline character from echo command
    current_user = shcmd("echo $USER").strip()
    for user in users:
        # Don't change the password for current user
        if user == current_user:
            continue
        password = 'Password123#!'
        cmd = "echo '{}:{}' | sudo chpasswd\n".format(user, password)
        print("Changing password for {}".format(user))
        print('> ' + cmd)
        if not dry_run:
            stdout = shcmd(cmd)
            print(stdout)


def remove_sudoers(non_admins, dry_run):
    """Removes users from the sudo group

    Args:
        non_admins (list): The list of users to remove from the sudo group
        dry_run (bool): Whether or not to follow through with the operation
    """
    for user in non_admins:
        print("Removing admin privileges for: " +user)
        cmd = "sudo deluser {} sudo".format(user)
        print("> " + cmd)
        if not dry_run:
            stdout = shcmd(cmd)
            print(stdout)


def remove_root_ssh(dry_run):
    """Sets PermitRootLogin to no in /etc/sshd_config

    Args:
        dry_run (bool): Whether dry run mode is enabled
    """
    config_path = "/etc/ssh/sshd_config"
    lines = readfile(config_path).split('\n')
    pattern = '^#?PermitRootLogin'

    for (i, line) in enumerate(lines):
        match = re.search(pattern, line)
        if match is not None:
            lines[i] = "PermitRootLogin no"

    config_file = "{}".format('\n'.join(lines))
    print("\nRemoving root ssh login")
    cmd = "sudo cat << EOF > {}\n{}\nEOF".format(config_path, config_file)

    if not dry_run:
        shcmd(cmd)
def disable_guest_account(dry_run):
    config_path = "/etc/lightdm/lightdm.conf"
    lines = readfile(config_path).split('\n')
    pattern = '^#?allow-guest'
    for (i, line) in enumerate(lines):
        match = re.search(pattern, line)
        if match is not None:
            lines[i] = "allow=guest=false"
    config_file = "{}".format('\n'.join(lines))
    print("\n Removing guest account")
    cmd = "sudo cat << EOF > {}\n{}\nEOF".format(config_path, config_file)
    if not dry_run:
        shcmd(cmd)

def print_usage():
    print(
        "Usage:\n\n-h --help \n-d --dry-run\n\nRequired:\n[*] -u --users <Authorized Users List Path>\n[*] -a --admins <Admin Users List Path>")
    sys.exit(0)


def main(argv):
    """The main function of this program file

    Args:
        argv (list): The cli arguments supplied to this file
    """
    if len(argv) == 1:
        print_usage()

    try:
        opts, args = getopt.getopt(argv[1:], "hdu:a:", ["users=", "admins="])
    except getopt.GetoptError:
        print(argv[0] + ": Incorrect Syntax, try '-h' for help.")
        sys.exit(2)

    # Set the options based on arguments passed in
    USERFILE = None
    ADMINFILE = None
    dry_run = False
    for opt, arg in opts:
        if opt == "-h" or opt == "--help":
            print_usage()
        elif opt == "-u" or opt == '--users':
            USERFILE = arg
        elif opt == "-a" or opt == '--admins':
            ADMINFILE = arg
        elif opt == '-d' or opt == '--dry-run':
            dry_run = True

    if USERFILE is None:
        raise ValueError("User file is a required argument.")

    if ADMINFILE is None:
        raise ValueError("Admin file is a required argument.")

    if dry_run:
        print("Running in dry-run mode\n")

    invalid_users = get_unauth_users(USERFILE)
    remove_unauth(invalid_users, dry_run)

    invalid_admins = get_non_admins(ADMINFILE)
    remove_sudoers(invalid_admins, dry_run)

    # Read /etc/passwd and parse current users
    current_users = getusers()
    change_passwords(current_users, dry_run)

    remove_root_ssh(dry_run)

    disable_guest_account(dry_run)


if __name__ == "__main__":
    main(sys.argv)
