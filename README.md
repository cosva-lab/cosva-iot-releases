# Cosva IoT — descargas

Instaladores y versiones distribuidas de Cosva para **Raspberry Pi 5 de 8 GB**, con **Ubuntu Desktop 24.04 o 26.04 LTS ARM64**.

**[Abrir la página de descargas](https://github.com/cosva-lab/cosva-iot-releases/releases)**

No necesitas cuenta ni token de GitHub para descargar el instalador o las imágenes de la aplicación. Este repositorio contiene documentación y archivos distribuidos; el desarrollo se mantiene en repositorios privados.

## Instalar

1. Descarga el archivo `cosva-setup_VERSION_arm64.deb` y su `.sha256` desde una versión publicada.
2. En la Raspberry, fuera del ordeño, verifica e instala:

```sh
sha256sum -c cosva-setup_VERSION_arm64.deb.sha256
sudo apt install ./cosva-setup_VERSION_arm64.deb
```

3. Abre **Cosva — Installation and recovery**, o `http://127.0.0.1:3501/setup`.
4. Crea el administrador del equipo y elige una instalación nueva o la adopción de una existente.
5. Proporciona la configuración de tu finca. Una instalación nueva también requiere la clave de la API y la contraseña MQTT configurada en los dispositivos.
6. Sigue el progreso. Al terminar, reinicia manualmente para comprobar el arranque de Cosva al encender.

El Debian instala el helper y sus servicios. El asistente prepara Docker, Compose, Chromium y la aplicación después de terminar APT. La aplicación funciona localmente; la primera instalación y la descarga de una versión nueva requieren internet.

## Versiones y actualizaciones

- **Candidata / prerelease:** para pruebas en una Pi y certificación con sensores reales. No se considera lista para producción.
- **Estable / latest:** requiere evidencia de certificación física antes de su promoción.
- Publicar una versión no actualiza los equipos. Cada actualización necesita una solicitud del administrador desde **Configuración → Actualizaciones**.
- Si hay ordeño o un turno abierto, la actualización se rechaza. El helper verifica firma, esquema y respaldo antes de reemplazar servicios y comprueba la pantalla y los servicios antes de habilitar nuevos ordeños.
- La recuperación utiliza las imágenes anteriores guardadas localmente; no restaura automáticamente la base de datos sobre datos nuevos.

La pantalla administrativa de recuperación está en `http://127.0.0.1:3501/updates`. Sigue funcionando aunque el dashboard de Cosva no cargue.

## Archivos de cada entrega

| Archivo | Uso |
| --- | --- |
| `cosva-setup_VERSION_arm64.deb` | Instalador para Ubuntu Desktop ARM64 |
| `cosva-setup_VERSION_arm64.deb.sha256` | Comprobación de integridad del instalador |
| `release.json` | Manifiesto firmado con las imágenes y versiones exactas |

La Raspberry verifica los manifiestos con la clave pública incluida en el instalador. Las imágenes se descargan por digest inmutable. La clave privada de firma, las credenciales de construcción y los datos de las fincas no se distribuyen.
