from utils import shcmd, print_green, print_red, print_yellow
import re
import os
from pprint import pprint


def get_installed_programs(package_manager="apt"):
    installed = []
    if package_manager == "apt":
        cmd = "apt list --installed 2>/dev/null"
        stdout = shcmd(cmd)
        packages = stdout.split("\n")[1:]
        installed = [x.split("/")[0] for x in packages]

    if package_manager == "yum":
        cmd = "yum list installed"
        stdout = shcmd(cmd)
        packages = stdout.split("\n")

    if package_manager == "pacman":
        cmd = "pacman -Qqe"
        stdout = shcmd(cmd)
        packages = stdout.split("\n")
        installed = packages

    return installed


def get_acceptable_programs(installed):
    acceptable_patterns = [r'gir1.*', r'python.*',
                           r'xdg.*', r'lib.*', 'firefox', r'chrom*.', r'fonts.*',
                           r'gcc.*', r'binutil.*', r'linux.*', r'manpages.*',
                           r'ncurses.*', r'systemd.*', r'vim.*', r'dconf.*',
                           r'dpkg*', r'initra.*', r'glib.*', 'g\+\+.*', r'cloud.*',
                           r'cpp.*', r'openssh.*', r'xorg.*', r'bash.*', r'dbus.*',
                           r'gpg.*', r'gnupg.*', r'ubuntu.*', r'xserver.*', r'xfonts.*',
                           r'x11-.*', r'unity-.*', r'gstreamer.*', r'gnome-.*',
                           r'cups.*', r'avahi-.*', r'gconf.*', r'language-.*',
                           r'openjdk.*', r'pulseaudio.*', r'qml-mod.*', r'qtdec.*',
                           r'remmina.*', r'signon-.*', r'indicator-.*'
                           ]
    accepted_programs = []
    for pattern in acceptable_patterns:
        for program in installed:
            if program in accepted_programs:
                continue

            match_result = re.match(pattern, program)
            if match_result is not None:
                match_result = None
                accepted_programs.append(program)

    return accepted_programs


def list_services():
    cmd = "systemctl list-unit-files"
    stdout = shcmd(cmd)
    lines = "\n".join([line for line in stdout.split('\n')
                       if "disabled" not in line
                       and "systemd-" not in line
                       and "dbus-org" not in line
                       and "initrd-" not in line])
    print(stdout)
    print(lines)


def find_suids():
    print("SUID binaries on this machine:\n")
    cmd = "find / -perm /4000 2>/dev/null"
    os.system(cmd)


if __name__ == "__main__":
    programs = get_installed_programs()
    accepted = get_acceptable_programs(programs)

    to_examine = [p for p in programs if p not in accepted]
    print("System packages to examine:\n")
    pprint(to_examine)

    list_services()
    # find_suids()
