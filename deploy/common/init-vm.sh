#!/usr/bin/env bash
set -euo pipefail

# Ubuntu 24.04 VM 공통 초기화
# Mac/Windows 호스트와 무관하게 Ubuntu VM 내부에서 실행합니다.
#
# 예:
#   sudo ROLE=web APPLY_STATIC_IP=yes ./init-vm.sh
#   sudo ROLE=was APPLY_STATIC_IP=yes ./init-vm.sh
#   sudo ROLE=db APPLY_STATIC_IP=yes ./init-vm.sh

ROLE="${ROLE:-}"

WEB_IP="${WEB_IP:-192.168.100.10}"
WAS_IP="${WAS_IP:-192.168.100.20}"
DB_IP="${DB_IP:-192.168.100.30}"
PREFIX_LENGTH="${PREFIX_LENGTH:-24}"
GATEWAY="${GATEWAY:-192.168.100.2}"
DNS_SERVERS="${DNS_SERVERS:-8.8.8.8,1.1.1.1}"

APPLY_STATIC_IP="${APPLY_STATIC_IP:-no}"
ENABLE_UFW="${ENABLE_UFW:-yes}"
DO_UPGRADE="${DO_UPGRADE:-no}"

usage() {
  cat <<EOF
사용법:
  sudo ROLE=web [APPLY_STATIC_IP=yes] $0
  sudo ROLE=was [APPLY_STATIC_IP=yes] $0
  sudo ROLE=db  [APPLY_STATIC_IP=yes] $0

기본 네트워크:
  web-vm: $WEB_IP
  was-vm: $WAS_IP
  db-vm : $DB_IP
  gateway: $GATEWAY

호스트의 VMware NAT 대역이 다르면 WEB_IP, WAS_IP, DB_IP, GATEWAY를
실행 시 환경변수로 전달하세요.
EOF
}

fail() {
  echo "오류: $*" >&2
  exit 1
}

[[ $EUID -eq 0 ]] || fail "일반 사용자 계정에서 sudo로 실행하세요."
[[ -n ${SUDO_USER:-} && ${SUDO_USER} != root ]] \
  || fail "root로 직접 로그인하지 말고 일반 사용자 계정에서 sudo를 사용하세요."

case "$ROLE" in
  web)
    VM_HOSTNAME="${VM_HOSTNAME:-web-vm}"
    STATIC_IP="${STATIC_IP:-$WEB_IP}"
    ;;
  was)
    VM_HOSTNAME="${VM_HOSTNAME:-was-vm}"
    STATIC_IP="${STATIC_IP:-$WAS_IP}"
    ;;
  db)
    VM_HOSTNAME="${VM_HOSTNAME:-db-vm}"
    STATIC_IP="${STATIC_IP:-$DB_IP}"
    ;;
  *)
    usage
    exit 1
    ;;
esac

REAL_USER="$SUDO_USER"
export DEBIAN_FRONTEND=noninteractive

echo "ROLE       : $ROLE"
echo "HOSTNAME   : $VM_HOSTNAME"
echo "STATIC_IP  : $STATIC_IP/$PREFIX_LENGTH"
echo "GATEWAY    : $GATEWAY"

configure_hostname() {
  hostnamectl set-hostname "$VM_HOSTNAME"

  sed -i \
    -e '/[[:space:]]web-vm\([[:space:]]\|$\)/d' \
    -e '/[[:space:]]was-vm\([[:space:]]\|$\)/d' \
    -e '/[[:space:]]db-vm\([[:space:]]\|$\)/d' \
    /etc/hosts

  cat >>/etc/hosts <<EOF
$WEB_IP web-vm web.local
$WAS_IP was-vm was.local
$DB_IP db-vm db.local
EOF
}

configure_static_ip() {
  if [[ $APPLY_STATIC_IP != yes ]]; then
    echo "고정 IP 설정을 생략합니다."
    return
  fi

  local default_iface backup_dir config_file dns_yaml
  default_iface="$(ip route show default | awk 'NR == 1 {print $5}')"
  [[ -n $default_iface ]] || fail "기본 네트워크 인터페이스를 찾지 못했습니다."

  backup_dir="/etc/netplan/backup-$(date +%Y%m%d-%H%M%S)"
  mkdir -p "$backup_dir"
  for config_file in /etc/netplan/*.yaml; do
    [[ -e $config_file ]] || continue
    mv "$config_file" "$backup_dir/"
  done

  dns_yaml="${DNS_SERVERS//,/, }"
  cat >/etc/netplan/99-3tier-static.yaml <<EOF
network:
  version: 2
  ethernets:
    $default_iface:
      dhcp4: false
      addresses:
        - $STATIC_IP/$PREFIX_LENGTH
      routes:
        - to: default
          via: $GATEWAY
      nameservers:
        addresses: [$dns_yaml]
EOF

  chmod 600 /etc/netplan/99-3tier-static.yaml
  netplan generate
  netplan apply
}

verify_role_ip() {
  if [[ $APPLY_STATIC_IP != yes ]]; then
    echo "현재 IPv4 주소:"
    ip -4 -brief address
    return
  fi

  ip -4 -o address show | awk '{print $4}' | cut -d/ -f1 \
    | grep -Fxq "$STATIC_IP" \
    || fail "$STATIC_IP 적용을 확인하지 못했습니다."
}

install_common_packages() {
  apt-get update
  if [[ $DO_UPGRADE == yes ]]; then
    apt-get upgrade -y
  fi

  apt-get install -y \
    ca-certificates \
    cron \
    curl \
    git \
    openssh-server \
    ufw

  timedatectl set-timezone Asia/Seoul
  systemctl enable --now cron
  systemctl enable --now ssh
}

install_docker() {
  if command -v docker >/dev/null 2>&1 \
    && docker compose version >/dev/null 2>&1; then
    echo "Docker Engine과 Compose Plugin이 이미 설치되어 있습니다."
  else
    apt-get remove -y \
      docker.io \
      docker-doc \
      docker-compose \
      docker-compose-v2 \
      podman-docker \
      containerd \
      runc 2>/dev/null || true

    install -m 0755 -d /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg \
      -o /etc/apt/keyrings/docker.asc
    chmod a+r /etc/apt/keyrings/docker.asc

    . /etc/os-release
    cat >/etc/apt/sources.list.d/docker.sources <<EOF
Types: deb
URIs: https://download.docker.com/linux/ubuntu
Suites: ${UBUNTU_CODENAME:-$VERSION_CODENAME}
Components: stable
Architectures: $(dpkg --print-architecture)
Signed-By: /etc/apt/keyrings/docker.asc
EOF

    apt-get update
    apt-get install -y \
      docker-ce \
      docker-ce-cli \
      containerd.io \
      docker-buildx-plugin \
      docker-compose-plugin
  fi

  systemctl enable --now docker
  usermod -aG docker "$REAL_USER"
  docker --version
  docker compose version
}

configure_firewall() {
  if [[ $ENABLE_UFW != yes ]]; then
    echo "UFW 설정을 생략합니다."
    return
  fi

  ufw default deny incoming
  ufw default allow outgoing
  ufw allow 22/tcp

  case "$ROLE" in
    web)
      ufw allow 80/tcp
      ;;
    was)
      ufw allow from "$WEB_IP" to any port 8000 proto tcp
      ;;
    db)
      ufw allow from "$WAS_IP" to any port 3306 proto tcp
      ;;
  esac

  ufw --force enable
  ufw status verbose
}

configure_hostname
configure_static_ip
verify_role_ip
install_common_packages
install_docker
configure_firewall

echo
echo "VM 초기화 완료: $ROLE"
echo "저장소를 clone한 뒤 해당 역할의 deploy.sh를 실행하세요."
echo "docker 그룹 권한 적용을 위해 로그아웃 후 다시 로그인하세요."
