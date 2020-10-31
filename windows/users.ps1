function Get-AllowedUsers {
    [CmdletBinding()]
    param (
        [string] 
        $UsersPath
    )

    $users = Get-LocalUser | Select Name

    $allowedUsersStr = cat $usersPath
    $allowedUsersStr += "`nAdministrator"
    $allowedUsersStr += "`nDefaultAccount"
    $allowedUsersStr += "`nGuest"

    $allowedUsers = $allowedUsersStr.Split("`n")

    foreach ($user in $users) {
        if ($allowedUsers -contains $user.Name) {
            echo $user
        } 
    }
}

# $users = Get-LocalUser | Select Name
# $allowedUsers = (Get-AllowedUsers .\users.txt).Name

# foreach ($user in $users) {
#     if ($allowedUsers -contains $user.Name) 
#     {
#         echo $user
#     }
# }

# echo $allowedUsers

# $password = ConvertTo-SecureString "test" -AsPlainText -Force
# New-LocalUser "Testing" -Password $password -FullName "Jay Testing" -Description "A test user account"

# TODO: Remove unauthorized users and admins
$currentAdmins = Get-LocalGroupMember -Name Administrators

$allowedAdminsStr = cat admins.txt
$allowedAdminsStr += "`nAdministrator"

$allowedAdmins = $allowedAdminsStr.Split("`n")


echo $allowedAdmins
echo $currentAdmins