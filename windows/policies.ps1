#Requires -RunAsAdministrator

[CmdletBinding()]
param (
    # [Parameter()]
    # [switch]
    # $verbose
)

function New-Section {
    param (
        [string]
        $header
    )
    
    Clear-Host
    echo "============ $header ============" 
}

function Get-YesNo {
    param (
        [string]
        $prompt
    )

    do {
        $input = (Read-Host "$prompt (Y/N)").ToLower()
    }
    while ($input -notin @('y', 'n'))
    return $input
}

$isVerbose = [bool]$PSCmdlet.MyInvocation.BoundParameters["Verbose"].IsPresent


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
        Set-NetFirewallProfile -Enabled True -Verbose:$isVerbose
    }
}
else {
    echo "Firewall is enabled for all profiles"
}

# New-Section -header "Test"