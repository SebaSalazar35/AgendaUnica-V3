# Prueba todos los endpoints de la API con curl y guarda la evidencia.
# Uso (con el servidor corriendo en otra terminal):
#   powershell -ExecutionPolicy Bypass -File pruebas\probar_api.ps1
# Las claves se leen del .env; los tokens se guardan truncados.

$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$base = "http://127.0.0.1:8000"
$raiz = Split-Path $PSScriptRoot -Parent
$salida = Join-Path $PSScriptRoot "salida_curl.txt"
$tmp = Join-Path $env:TEMP "body_api.json"

$envVars = @{}
Get-Content (Join-Path $raiz ".env") | ForEach-Object {
    if ($_ -match "^\s*([A-Z_]+)\s*=\s*(.*)$") { $envVars[$matches[1]] = $matches[2].Trim() }
}

function Truncar($texto) {
    [regex]::Replace($texto, "eyJ[\w-]+\.[\w-]+\.[\w-]+", { param($m) $m.Value.Substring(0, 12) + "..." })
}

function Llamar($titulo, $esperado, $metodo, $ruta, $token = $null, $json = $null) {
    $curlArgs = @("-s", "-i", "-X", $metodo, "$base$ruta")
    $comando = "curl -X $metodo"
    if ($token) {
        $curlArgs += @("-H", "Authorization: Bearer $token")
        $comando += " -H `"Authorization: Bearer $($token.Substring(0, 12))...`""
    }
    if ($json) {
        [System.IO.File]::WriteAllText($tmp, $json)
        $curlArgs += @("-H", "Content-Type: application/json", "--data-binary", "@$tmp")
        $comando += " -H `"Content-Type: application/json`" -d '$(Truncar $json)'"
    }
    $comando += " $base$ruta"
    $respuesta = (& curl.exe @curlArgs) -join "`n"
    $codigo = ($respuesta -split "`n")[0].Trim()
    $cuerpo = ($respuesta -split "`n")[-1]
    $bloque = @"
==================================================================
$titulo
Esperado: $esperado
`$ $comando
$codigo
$(Truncar $cuerpo)

"@
    Add-Content -Path $salida -Value $bloque -Encoding UTF8
    Write-Host "$titulo -> $codigo"
    return $cuerpo
}

function Token($usuario, $clave) {
    $json = "{`"username`": `"$usuario`", `"password`": `"$clave`"}"
    [System.IO.File]::WriteAllText($tmp, $json)
    $r = (& curl.exe -s -X POST -H "Content-Type: application/json" --data-binary "@$tmp" "$base/api/token/") | ConvertFrom-Json
    return $r
}

Set-Content -Path $salida -Value "Evidencia de pruebas API ES3 - $(Get-Date -Format 'yyyy-MM-dd HH:mm')`n" -Encoding UTF8

Llamar "1. Listar sin token" "401 Unauthorized" "GET" "/api/registros/" | Out-Null

$loginJson = "{`"username`": `"admin`", `"password`": `"$($envVars['PASS_ADMIN'])`"}"
Llamar "2. Pedir token (admin)" "200 OK con access y refresh" "POST" "/api/token/" $null $loginJson | Out-Null
(Get-Content $salida -Raw).Replace($envVars['PASS_ADMIN'], "********") | Set-Content $salida -Encoding UTF8

Llamar "3. Pedir token con clave mala" "401 Unauthorized" "POST" "/api/token/" $null '{"username": "admin", "password": "clave-mala"}' | Out-Null

$admin = Token "admin" $envVars['PASS_ADMIN']
$normal = Token "normal" $envVars['PASS_NORMAL']
$viewer = Token "viewer" $envVars['PASS_VIEWER']

Llamar "4. Listar con token (paginado de a 10)" "200 OK" "GET" "/api/registros/" $viewer.access | Out-Null

$creado = Llamar "5. Crear registro valido (rol normal)" "201 Created, resultado lo decide decidir()" "POST" "/api/registros/" $normal.access '{"nombre": "Pedro Rojas", "patente": "BCDF23", "servicio": "Cambio de aceite", "inasistencias": 0}'
$id = ([regex]::Match($creado, '"id":(\d+)')).Groups[1].Value

Llamar "6. Intentar fijar resultado desde el cliente" "201 Created, pero resultado lo ignora (read_only) y aplica la regla" "POST" "/api/registros/" $normal.access '{"nombre": "Tramposo", "inasistencias": 4, "resultado": "Aceptado"}' | Out-Null

Llamar "7. Crear con datos invalidos" "400 Bad Request con mensajes por campo" "POST" "/api/registros/" $normal.access '{"nombre": "", "patente": "XX", "inasistencias": -1}' | Out-Null

Llamar "8. Ver uno" "200 OK" "GET" "/api/registros/$id/" $viewer.access | Out-Null

Llamar "9. Editar un campo con PATCH (admin)" "200 OK" "PATCH" "/api/registros/$id/" $admin.access '{"servicio": "Alineacion y balanceo"}' | Out-Null

Llamar "10. Reemplazar con PUT (admin)" "200 OK" "PUT" "/api/registros/$id/" $admin.access '{"nombre": "Pedro Rojas", "telefono": "56911112222", "patente": "BCDF23", "servicio": "Frenos", "inasistencias": 1}' | Out-Null

Llamar "11. Viewer intenta crear" "403 Forbidden" "POST" "/api/registros/" $viewer.access '{"nombre": "X", "inasistencias": 0}' | Out-Null

Llamar "12. Normal intenta borrar" "403 Forbidden" "DELETE" "/api/registros/$id/" $normal.access | Out-Null

Llamar "13. Admin borra (borrado logico)" "204 No Content" "DELETE" "/api/registros/$id/" $admin.access | Out-Null

Llamar "14. Ver el registro borrado" "404 Not Found" "GET" "/api/registros/$id/" $admin.access | Out-Null

Llamar "15. Id que no existe" "404 Not Found" "GET" "/api/registros/99999/" $admin.access | Out-Null

Llamar "16. Accion propia: solo aceptados" "200 OK" "GET" "/api/registros/aceptados/" $viewer.access | Out-Null

Llamar "16b. Filtrar por resultado" "200 OK solo con rechazados por no-show" "GET" "/api/registros/?resultado=Rechazado:%20el%20cliente%20acumula%20demasiados%20no-show" $viewer.access | Out-Null

Llamar "16c. Filtrar por parte del nombre" "200 OK" "GET" "/api/registros/?nombre=maria" $viewer.access | Out-Null

Llamar "17. Refrescar el token" "200 OK con un access nuevo" "POST" "/api/token/refresh/" $null "{`"refresh`": `"$($viewer.refresh)`"}" | Out-Null

Llamar "18. Token falso o vencido" "401 Unauthorized" "GET" "/api/registros/" "eyJfalso.token.invalido" | Out-Null

Remove-Item $tmp -ErrorAction SilentlyContinue
Write-Host "Evidencia guardada en $salida"
