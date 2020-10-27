#!/usr/bin/python3

import getopt 
import os
import sys

# Helper function to read a file from a path
def readfile(path):
    try:
        with open(path) as file:
            return file.read()
    except IOError as ex:
        print (" ".join(str(ex).split(' ')[2:]))
        sys.exit(ex.errno)

def exit():
    sys.exit(1)

def shcmd(cmd):
    return os.popen(cmd).read()


# Function to read all the users from /etc/pass
# Finds entries that end with *sh
def getusers():
    # Read the file
    entries = readfile('/etc/passwd').split('\n')
    # Get all lines that end with sh
    entries = [e for e in entries if e.endswith('sh')]
    # Return the list of usernames
    users = [x.split(':')[0] for x in entries]
    return users


# Function to get the users that are not allowed on the system
# Pass in a path to a list of users
def get_unauth_users(path):
    current_users = getusers()
    allowed_users = readfile(path)
    unauth = [u for u in current_users if u not in allowed_users]
    unauth.remove('root')
    return unauth

def get_non_admins(path,sudoers):
    # Get list of allowed admins
    allowed_admins = readfile(path).split('\n')
    # Return list of users that are not in that list
    invalid_admins = [ user for user in sudoers if user not in allowed_admins]
    invalid_admins.remove('root')

    return invalid_admins

# Remove unauthorized users
def remove_unauth(unauth):
    for user in unauth:
        print (f'Deleting user: {user}')
        delcmd = f'sudo deluser --remove-home {user}\n\n'
        print ('> ' + delcmd)
        stdout = shcmd(delcmd)
        print (stdout)


def change_passwords(users):
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

# Gets the users that are capable of running sudo
def get_sudoers():
    sudoers = []

    users = getusers()
    for user in users:
        cmd = f"sudo -l -U {user}"
        stdout = shcmd(cmd)
        if "not allowed" not in stdout:
            sudoers.append(user)

    return sudoers

def remove_sudoers(non_admins):
    for user in non_admins:
        print(f"Removing admin privileges for: {user}")
        cmd = f"sudo deluser {user} sudo"
        print("> " + cmd)
        stdout = shcmd(cmd)
        print (stdout)

# https://docs.python.org/2/library/getopt.html

def main(argv):
    try:
        opts, args = getopt.getopt(argv[1:], "hu:a:",["users=","admins="])
    except getopt.GetoptError:
        print(argv[0] + ": Incorrect Syntax, try '-h' for help.")
        sys.exit(2)

    # Set the options based on arguments passed in
    USERFILE = None
    ADMINFILE = None
    for opt, arg in opts:
        if opt == "-h" or opt == "--help":
            print("Usage:\n\n-h --help \n\nRequired:\n[*] -u --users <Authorized Users List Path>\n[*] -a --admins <Admin Users List Path>")
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

    #Remove unAuth Users from /etc/passwd
    remove_unauth(invalid_users)

    if ADMINFILE is not None:
        current_admins = get_sudoers()
        invalid_admins = get_non_admins(ADMINFILE,current_admins)
        remove_sudoers(invalid_admins)
    else:
        print("Admin file is required.")
        exit()

    # Read /etc/passwd and parse current users
    current_users = getusers()
    change_passwords(current_users)


if __name__ == "__main__":
    main(sys.argv[0:])