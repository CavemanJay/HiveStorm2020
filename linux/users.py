#!/usr/bin/python3

from typing import List
from utils import print_green, print_red, print_yellow, read_passwd, read_shadow, readfile, shcmd, exit
import sys
import re
import argparse
import os


def get_users():
    """Returns the list of users from /etc/passwd that contain login shells
    ending with 'sh'"""
    # Read the file
    entries = read_passwd()
    # Get all lines that end with sh
    entries = (e for e in entries if e.strip().endswith('sh'))
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


def check_passwd_file():
    entries = read_passwd()
    users_w_no_pass = [x.split(":")[0]
                       for x in entries if x.split(":")[1] == ""]
    plaintext_passwds = [x for x in [x.split(":")[0]
                                     for x in entries if x.split(":")[1] != "x"] if x not in users_w_no_pass]
    if users_w_no_pass:
        print_red(f"Users with no password: {users_w_no_pass}")
    if plaintext_passwds:
        print_red(f"Users with plaintext password entry: {plaintext_passwds}")


def handle_passwords(main_user: str, dry_run: bool):
    check_passwd_file()
    change_passwords(main_user, dry_run)

    # TODO: 
        # Password expiration age
        # Minimum password length
        # Dictionary based password strength checks
            # These are the standard /etc/pam.d/common-auth and /etc/pam.d/common-password configurations


def handle_users(users: List[str], dry_run: bool):
    unauth_users = get_unauth_users(users)
    if unauth_users:
        print_red(f"Unauthorized users: {unauth_users}")
    if not dry_run:
        remove_unauth_users(unauth_users)

    disable_guest_account(dry_run)


def handle_sudoers(admins: List[str], dry_run: bool):
    invalid = get_invalid_admins(admins)
    if invalid:
        print_red(f"Unauthorized admins: {invalid}")
    if not dry_run:
        remove_sudoers(invalid)


def get_invalid_admins(allowed_admins: List[str]):
    sudoers = get_sudoers()
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


def change_passwords(main_user: str, dry_run: bool, password="Password123#!"):
    """Changes the password of all users specified to the password supplied.
    Does not change the password for the current user"""
    # Strip newline character from echo command
    current_user = shcmd("echo -n $USER")
    for user in get_users():
        # Don't change the password for current user
        if user == current_user or user == main_user:
            continue
        cmd = "echo '{}:{}' | chpasswd\n".format(user, password)
        print_yellow("Changing password for {}".format(user))
        print('> ' + cmd)
        if not dry_run:
            stdout = shcmd(cmd)
            print(stdout)


def remove_sudoers(non_admins: List[str]):
    """Removes users from the sudo group"""
    for user in non_admins:
        print("Removing admin privileges for: " + user)
        cmd = "sudo deluser {} sudo".format(user)
        print("> " + cmd)
        stdout = shcmd(cmd)
        print(stdout)


def remove_root_ssh(dry_run):
    """Sets PermitRootLogin to no in /etc/sshd_config"""
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
    is_root = os.getgid() == 0
    if not is_root:
        print("This script requires root permissions")
        sys.exit(1)

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "main_user", help="Main user of the machine (do not change their password)")
    parser.add_argument(
        "-x", "--execute", help="Actually change things on the system", action='store_true')
    parser.add_argument(
        "-u", "--users", help="Comma separated list of authorized users")
    parser.add_argument(
        "-a", "--admins", help="Comma separated list of authorized admins")
    parser.add_argument(
        "-p", "--passwords", help="Check password requirements", action='store_true')
    parser.add_argument(
        "-r", "--root-ssh", help="Check the status of root ssh login", action='store_true')

    args = parser.parse_args()

    dry_run: bool = not args.execute
    main_user: str = args.main_user

    if args.users:
        users = readfile(args.users).splitlines() if os.path.exists(
            args.users) else args.users.split(",") + [main_user]
        print_green(f"Authorized users: {users}")
        handle_users(users, dry_run)

    if args.admins:
        admins = readfile(args.admins).splitlines() if os.path.exists(
            args.admins) else args.admins.split(",") + [main_user]
        print_green(f"Authorized admins: {admins}")
        handle_sudoers(admins, dry_run)

    if args.passwords:
        handle_passwords(main_user, dry_run)

    if args.root_ssh:
        remove_root_ssh(dry_run)

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
