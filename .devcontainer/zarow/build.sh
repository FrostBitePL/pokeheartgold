#!/usr/bin/env bash
set -euo pipefail
export XDG_RUNTIME_DIR=/tmp DEBIAN_FRONTEND=noninteractive
sudo apt-get update -q
sudo apt-get -y -q install software-properties-common lsb-release wget unzip p7zip-full libpng-dev pkg-config libpugixml-dev binutils-arm-none-eabi make build-essential python3
sudo add-apt-repository ppa:ubuntu-toolchain-r/test -y
sudo apt-get update -q
sudo apt-get -y -q --allow-downgrades install g++-10-multilib
sudo dpkg --add-architecture i386
sudo mkdir -pm755 /etc/apt/keyrings
sudo wget -q -O /etc/apt/keyrings/winehq-archive.key https://dl.winehq.org/wine-builds/winehq.key
sudo wget -q -NP /etc/apt/sources.list.d/ https://dl.winehq.org/wine-builds/ubuntu/dists/$(lsb_release -cs)/winehq-$(lsb_release -cs).sources
sudo apt-get update -q
sudo apt-get -y -q --allow-downgrades install --install-recommends winehq-stable
cd /workspaces/pokeheartgold
bash .devcontainer/setup-devcontainer.sh || true
export CC=gcc-10 CXX=g++-10
make COMPARE=0 -j4 > /tmp/build.log 2>&1
echo BUILD_DONE > /tmp/build_done
