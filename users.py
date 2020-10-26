#!/usr/bin/python2

import os
import sys


# Helper function to read a file from a path
def readfile(path):
    with open(path) as file:
        return file.read()


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
    return unauth


# Remove unauthorized users
def remove_unauth(unauth):
    for user in unauth:
        print 'Deleting user: {}'.format(user)
        delcmd = 'sudo deluser --remove-home {}\n\n'.format(user)
        print '> ' + delcmd
        stdout = shcmd(delcmd)
        print stdout


def change_passwords(users):
    current_user = shcmd("echo $USER")
    for user in users:
        # Don't change the password for current user
        if user == current_user:
            continue

        cmd = "echo '{}:{}' | sudo chpasswd".format(user, "Password123#!")
        print "Changing password for {}".format(user)
        print '> ' + cmd
        # stdout = shcmd(cmd)
        # print stdout


# args = sys.argv
# users_path = args[1]
# unauth = get_unauth_users(users_path)

# remove_unauth(unauth)

users = getusers()
change_passwords(users)
