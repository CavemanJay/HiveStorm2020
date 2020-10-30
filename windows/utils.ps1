function New-Section {
    [CmdletBinding()]
    param (
        [string]
        $header
    )
    
    Clear-Host
    Write-Output "============ $header ============" 
}

function Get-YesNo {
    [CmdletBinding()]
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