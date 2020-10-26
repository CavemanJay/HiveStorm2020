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

def get_non_admins(path,sudoers):
    # Get list of allowed admins
    allowed_admins = readfile(path).split('\n')
    # Return list of users that are not in that list
    return [ user for user in sudoers if user not in allowed_admins ]
    
    

# Remove unauthorized users
def remove_unauth(unauth):
    for user in unauth:
        print 'Deleting user: {}'.format(user)
        delcmd = 'sudo deluser --remove-home {}\n\n'.format(user)
        print '> ' + delcmd
        stdout = shcmd(delcmd)
        print stdout


def change_passwords(users):
    # Strip newline character from echo command
    current_user = shcmd("echo $USER").strip()
    for user in users:
        # Don't change the password for current user
        if user == current_user:
            continue

        cmd = "echo '{}:{}' | sudo chpasswd".format(user, "Password123#!")
        print "Changing password for {}".format(user)
        print '> ' + cmd
        stdout = shcmd(cmd)
        print stdout

# Gets the users that are capable of running sudo
def get_sudoers(users):
    sudoers = []

    for user in users:
        cmd = "sudo -l -U {}".format(user)
        stdout = shcmd(cmd)
        if "not allowed" not in stdout:
            sudoers.append(user)

    return sudoers

def remove_sudoers(non_admins):
    for user in non_admins:
        print "Removing admin privileges for: {}".format(user)
        cmd = "sudo deluser {} sudo".format(user)
        print "> " + cmd
        stdout = shcmd(cmd)
        print stdout

args = sys.argv
users_path = args[1]
admin_users_path = args[2]

# unauth = get_unauth_users(users_path)
# remove_unauth(unauth)

users = getusers()
# change_passwords(users)

current_admins=get_sudoers(users)

non_admins = get_non_admins(admin_users_path,current_admins)
