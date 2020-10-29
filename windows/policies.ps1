#Requires -RunAsAdministrator

[CmdletBinding()]
param (
    # [Parameter()]
    # [switch]
    # $verbose
)

$isVerbose = [bool]$PSCmdlet.MyInvocation.BoundParameters["Verbose"].IsPresent

Write-Output "Enabling firewall..."
Set-NetFirewallProfile -Enabled True -Verbose:$isVerbose