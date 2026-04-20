$domain = "blog-writing-agent.duckdns.org"
$token = "b494a2cd-050f-4b70-ad38-77ad1c59de4a"
$url = "https://www.duckdns.org/update?domains=$domain&token=$token&ip="

while($true) {
    try {
        $response = Invoke-RestMethod -Uri $url
        Write-Host "Updated DuckDNS: $response"
    } catch { Write-Host "Failed" }
    Start-Sleep -Seconds 300
}