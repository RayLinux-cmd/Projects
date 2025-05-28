@echo off
echo Instalando el programa...

:: Ejecutar monitor.exe (debe estar en el mismo directorio)
echo Ejecutando monitor.exe...
start "" "%~dp0monitor.exe"

:: Verificar si cargo está instalado
cargo --version >nul 2>&1
if errorlevel 1 (
    echo Cargo no está instalado. Por favor instala Rust desde https://rustup.rs/
    pause
    exit /b
)

:: Compilar main.rs
echo Compilando main.rs...
cargo build --release

if exist "target\release\main.exe" (
    echo Ejecutando main.rs...
    start "" "target\release\main.exe"
) else (
    echo No se pudo compilar main.rs
)

pause
