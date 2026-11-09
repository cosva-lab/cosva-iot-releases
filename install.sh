#!/usr/bin/env bash
# Public bootstrap for the signed-key Cosva helper Debian. No application source.
# Keep execution inside a function so an incomplete curl response cannot install.
cosva_install() (
  set -euo pipefail

  fail() { printf 'Cosva: %s\n' "$*" >&2; exit 1; }
  usage() {
    cat <<'HELP'
Instala o actualiza cosva-setup en Ubuntu Desktop 24.04/26.04 ARM64.
Ejecuta el comando fuera del ordeño.

Uso: bash install.sh [--candidate | --version VERSION]
  Sin opciones       Última versión estable certificada.
  --candidate        Última publicación, incluidas las versiones candidatas.
  --version VERSION  Una versión publicada concreta.
  --help             Muestra esta ayuda sin instalar.

Conserva la configuración local. No reinicia el equipo ni solicita una
actualización de los servicios de la aplicación.
HELP
  }

  local channel=stable version='' selected=false
  while (($#)); do
    case "$1" in
      --help|-h) usage; return 0 ;;
      --candidate)
        [[ "$selected" == false ]] || fail 'Elige un solo canal o versión.'
        channel=candidate; selected=true; shift ;;
      --version)
        [[ "$selected" == false && $# -ge 2 ]] || fail 'Indica una versión con --version VERSION.'
        [[ "$2" =~ ^[0-9][A-Za-z0-9.-]{0,95}$ ]] || fail 'Versión no válida.'
        version=$2; selected=true; shift 2 ;;
      *) fail "Opción desconocida: $1. Usa --help." ;;
    esac
  done
  [[ -z "$version" || "$version" =~ ^[0-9][A-Za-z0-9.-]{0,95}$ ]] || fail 'Versión no válida.'
  [[ "$(uname -s)" == Linux ]] || fail 'Ejecuta este comando en la Raspberry con Ubuntu Desktop ARM64.'
  local command
  for command in cat curl dpkg dpkg-deb apt-get sha256sum sed grep mktemp chmod id; do
    command -v "$command" >/dev/null || fail "Falta el comando requerido: $command."
  done
  local os_info
  os_info=$(cat /etc/os-release) || fail 'No se pudo identificar Ubuntu.'
  grep -Eq '^ID="?ubuntu"?$' <<<"$os_info" || fail 'Se requiere Ubuntu Desktop 24.04 o 26.04.'
  grep -Eq '^VERSION_ID="?(24\.04|26\.04)"?$' <<<"$os_info" || fail 'Se requiere Ubuntu Desktop 24.04 o 26.04.'
  [[ "$(dpkg --print-architecture)" == arm64 ]] || fail 'Se requiere ARM64 (arm64).'

  local cosva_tmp
  cosva_tmp=$(mktemp -d /tmp/cosva-setup.XXXXXXXX)
  trap 'rm -rf -- "$cosva_tmp"' EXIT
  # APT's _apt account must be able to read the downloaded package.
  chmod 0755 "$cosva_tmp"
  cd "$cosva_tmp"
  local repository=https://github.com/cosva-lab/cosva-iot-releases
  local api=https://api.github.com/repos/cosva-lab/cosva-iot-releases/releases
  local -a download=(curl --fail --silent --show-error --location --retry 3 --connect-timeout 20 --max-time 180 --proto '=https' --proto-redir '=https')
  if [[ -z "$version" ]]; then
    local endpoint="$api/latest"
    [[ "$channel" != candidate ]] || endpoint="$api?per_page=1"
    if ! "${download[@]}" --header 'Accept: application/vnd.github+json' "$endpoint" --output release-metadata.json; then
      fail 'No se pudo consultar la versión. Si todavía no hay una estable, usa --candidate para instalar una candidata.'
    fi
    # The unauthenticated API excludes drafts; per_page=1 selects one release.
    # Accept only a single safe tag from GitHub's line-oriented JSON response.
    version=$(sed -nE 's/^[[:space:]]*"tag_name"[[:space:]]*:[[:space:]]*"([0-9][A-Za-z0-9.-]{0,95})"[[:space:]]*,?[[:space:]]*$/\1/p' release-metadata.json)
    [[ "$version" =~ ^[0-9][A-Za-z0-9.-]{0,95}$ ]] || fail 'No se encontró una versión publicada válida.'
  fi
  printf 'Cosva: descargando cosva-setup %s. Ejecuta la instalación fuera del ordeño.\n' "$version"
  if [[ "$channel" == candidate ]]; then
    printf 'Canal: última publicación; puede ser una candidata pendiente de certificación física.\n'
  fi
  local package="cosva-setup_${version}_arm64.deb"
  local url="$repository/releases/download/$version"
  "${download[@]}" "$url/$package" --output "$package"
  "${download[@]}" "$url/$package.sha256" --output "$package.sha256"
  local receipt hash
  receipt=$(cat "$package.sha256")
  hash=${receipt%% *}
  [[ "$hash" =~ ^[a-fA-F0-9]{64}$ && "$receipt" == "$hash  $package" ]] || fail 'El comprobante SHA-256 no corresponde al paquete.'
  sha256sum --check "$package.sha256" || fail 'La descarga no supera la verificación SHA-256.'
  [[ "$(dpkg-deb --field "$package" Package)" == cosva-setup ]] || fail 'El archivo no contiene cosva-setup.'
  [[ "$(dpkg-deb --field "$package" Version)" == "$version" ]] || fail 'La versión del paquete no coincide.'
  [[ "$(dpkg-deb --field "$package" Architecture)" == arm64 ]] || fail 'La arquitectura del paquete no coincide.'

  local -a install=(apt-get --yes -o Dpkg::Options::=--force-confdef -o Dpkg::Options::=--force-confold install "$cosva_tmp/$package")
  if [[ "$(id -u)" != 0 ]]; then
    command -v sudo >/dev/null || fail 'Se requiere sudo para instalar el paquete.'
    install=(sudo -- "${install[@]}")
  fi
  # sudo reads the password from the terminal; APT never consumes the curl pipe.
  "${install[@]}" </dev/null
  printf '\nCosva: helper instalado. Abre http://127.0.0.1:3501/setup\n'
)

cosva_install "$@"
