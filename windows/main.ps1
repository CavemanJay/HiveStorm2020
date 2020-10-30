$scriptsFolder = Split-Path -Path $MyInvocation.MyCommand.Definition -Parent
. ("$scriptsFolder\policies.ps1")

Check-FirewallStatus -Verbose
Check-WindowsUpdate -Verbose