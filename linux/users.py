#!/usr/bin/python3

from typing import List
from utils import readfile, shcmd, exit
import sys
import re
import argparse


def get_users():
    """Returns the list of users from /etc/passwd that contain login shells
    ending with 'sh'"""
    # Read the file
    entries = readfile('/etc/passwd').split('\n')
    # Get all lines that end with sh
    entries = (e for e in entries if e.endswith('sh'))
    # Return the list of usernames
    users = [x.split(':')[0] for x in entries]
    return users


def get_sudoers():
    """Returns a list of users capable of running sudo"""
    sudoers = []

    users = get_users()
    for user in users:
        cmd = "sudo -l -U" + user
        stdout = shcmd(cmd)
        if "not allowed" not in stdout:
            sudoers.append(user)

    return sudoers


def get_unauth_users(users: List[str]):
    current_users = get_users()
    unauth = [u for u in current_users if u not in users and u != 'root']
    return unauth


def handle_shadow(dry_run: bool):
    pass


def handle_users(users: List[str], dry_run: bool):
    unauth_users = get_unauth_users(users)
    if unauth_users:
        print(f"Unauthorized users: {unauth_users}")
    if not dry_run:
        remove_unauth_users(unauth_users)


def handle_sudoers(admins: List[str], dry_run: bool):
    invalid = get_invalid_admins(admins)
    if invalid:
        print(f"Unauthorized users: {invalid}")
    if not dry_run:
        remove_sudoers(invalid)


def get_invalid_admins(allowed_admins: List[str]):
    sudoers = get_sudoers()
    # Return list of users that are not in that list
    invalid_admins = [user for user in sudoers if user not in allowed_admins]
    invalid_admins.remove('root')

    return invalid_admins


def remove_unauth_users(unauth: List[str]):
    """Removes a list of users from the system"""
    for user in unauth:
        print('Deleting user: {}'.format(user))
        delcmd = 'sudo deluser --remove-home {}\n'.format(user)
        print('> ' + delcmd)
        stdout = shcmd(delcmd)
        print(stdout)


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
    main_user = "ratchet"  # hard code this
    for user in users:
        # Don't change the password for current user
        if user == current_user or user == main_user:
            continue
        password = 'Password123#!'
        cmd = "echo '{}:{}' | sudo chpasswd\n".format(user, password)
        print("Changing password for {}".format(user))
        print('> ' + cmd)
        if not dry_run:
            stdout = shcmd(cmd)
            print(stdout)


def remove_sudoers(non_admins: List[str]):
    """Removes users from the sudo group

    Args:
        non_admins (list): The list of users to remove from the sudo group
    """
    for user in non_admins:
        print("Removing admin privileges for: " + user)
        cmd = "sudo deluser {} sudo".format(user)
        print("> " + cmd)
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
            lines[i] = "allow-guest=false"
        else:
            lines.append('allow-guest=false')
    config_file = "{}".format('\n'.join(lines))
    print("\nRemoving guest account")
    cmd = "sudo cat << EOF > {}\n{}\nEOF".format(config_path, config_file)
    if not dry_run:
        shcmd(cmd)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-d", "--dry-run", help="Don't actually change anything", action='store_true')
    parser.add_argument(
        "-u", "--users", help="Comma separated list of authorized users")
    parser.add_argument(
        "-a", "--admins", help="Comma separated list of authorized admins")
    parser.add_argument(
        "-s", "--shadow", help="Check /etc/shadow configurations", action='store_true')
    parser.add_argument(
        "--root-ssh", help="Check the status of root ssh login", action='store_true')

    args = parser.parse_args()

    dry_run: bool = args.dry_run
    if args.users:
        handle_users(args.users.split(","), dry_run)

    if args.admins:
        handle_sudoers(args.admins.split(","), dry_run)

    if args.shadow:
        handle_shadow(dry_run)

    return

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
    remove_unauth_users(invalid_users, dry_run)

    invalid_admins = get_invalid_admins(ADMINFILE)
    remove_sudoers(invalid_admins, dry_run)

    # Read /etc/passwd and parse current users
    current_users = get_users()
    change_passwords(current_users, dry_run)
    remove_root_ssh(dry_run)
    disable_guest_account(dry_run)


if __name__ == "__main__":
    main()
