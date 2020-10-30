#Requires -RunAsAdministrator
#Requires -Module PSWindowsUpdate

$scriptsFolder = Split-Path -Path $MyInvocation.MyCommand.Definition -Parent
. ("$scriptsFolder\utils.ps1")

function Check-FirewallStatus {
    [CmdletBinding()]
    param ()
    
    New-Section "Firewall"

    $rules = Get-NetFirewallProfile
    $disabled = $false

    foreach ($rule in $rules) {
        Write-Verbose "Firewall Profile: $($rule.Name) | Enabled: $($rule.Enabled)"
        if (!$rule.Enabled) {
            $disabled = $true
        }
    }


    if ($disabled) {
        $enableFirewall = Get-YesNo "Firewall is disabled. Would you like to enable it?"
        if ($enableFirewall -eq "y") {
            Write-Output "Enabling firewall"
            Set-NetFirewallProfile -Enabled True -Verbose:($PSBoundParameters['Verbose'] -eq $true)
        }
    }
    else {
        Write-Output "Firewall is enabled for all profiles"
    }
}

function Check-WindowsUpdate {
    [CmdletBinding()]
    param ()
    
    New-Section "Windows Update"
    Write-Output "Searching for windows update..."
    $availableUpdates = Get-WindowsUpdate -Verbose:($PSBoundParameters['Verbose'] -eq $true)
    if ($availableUpdates.Length -gt 0) {
        echo "One or more windows updates is available."
        echo $availableUpdates

        $installUpdatesYN = Get-YesNo "Would you like to install all updates?"
        if ($installUpdatesYN -eq "y") {
            Install-WindowsUpdate -Verbose:($PSBoundParameters['Verbose'] -eq $true)
        }
    }
    else {
        Write-Output "Windows appears to be up to date"
    }
}
