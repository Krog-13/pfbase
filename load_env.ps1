# runserver.ps1

$envFile = ".env"

if (-Not (Test-Path $envFile)) {
    Write-Error ".env file not found"
    exit 1
}

Get-Content $envFile | ForEach-Object {
    $line = $_.Trim()

    if ($line -eq "" -or $line.StartsWith("#")) {
        return
    }

    if ($line -match "^\s*([^=]+)\s*=\s*(.*)\s*$") {
        $name = $matches[1].Trim()
        $value = $matches[2].Trim()

        # Remove surrounding quotes
        $value = $value.Trim('"').Trim("'")

        Set-Item -Path "Env:$name" -Value $value
    }
}

Write-Host "Loaded .env variables"
