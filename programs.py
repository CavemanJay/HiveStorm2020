from utils import shcmd, print_green, print_red, print_yellow
import re


def get_installed_programs(package_manager="apt"):
    installed = []
    if package_manager == "apt":
        cmd = "apt list --installed"
        stdout = shcmd(cmd)
        packages = stdout.split("\n")[1:]
        installed = [x.split("/")[0] for x in packages]

        return installed


def get_acceptable_programs(installed):
    acceptable_patterns = [r'gir1.*', r'python.*',
                           r'xdg.*', r'lib.*', 'firefox', r'chrom*.', r'fonts.*',
                           r'gcc.*', r'binutil.*', r'linux.*', r'manpages.*',
                           r'ncurses.*', r'systemd.*', r'vim.*', r'dconf.*',
                           r'dpkg*', r'initra.*', r'glib.*', 'g\+\+.*']
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


if __name__ == "__main__":
    programs = get_installed_programs()
    accepted = get_acceptable_programs(programs)
    for x in [p for p in programs if p not in accepted]:
        print_yellow(x)
