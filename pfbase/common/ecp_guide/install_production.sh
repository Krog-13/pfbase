#!/bin/bash
set -e  # Stop script on any error

# --- Ensure folder for extra certs exists ---
if [ -d /usr/local/share/ca-certificates/extra/ ]; then
    echo "Folder /usr/local/share/ca-certificates/extra already exists"
else
    sudo mkdir -p /usr/local/share/ca-certificates/extra
fi

# --- Copy PEM certificates to system cert folder ---
sudo cp -a production/*.pem /etc/ssl/certs/

# --- Convert .pem -> .crt for update-ca-certificates ---
cd production
for f in *.pem; do
    mv -- "$f" "${f%.pem}.crt"
done
cd ..

# --- Copy CRT certificates to extra CA folder ---
sudo cp -a production/*.crt /usr/local/share/ca-certificates/extra/

# --- Refresh CA certificates ---
sudo update-ca-certificates --fresh

# --- Convert .crt back -> .pem to restore original files ---
cd production
for f in *.crt; do
    mv -- "$f" "${f%.crt}.pem"
done
cd ..

# --- Ensure /srv/kalkan folder exists ---
if [ -d /srv/kalkan ]; then
    echo "Folder /srv/kalkan already exists"
else
    sudo mkdir -p /srv/kalkan
fi

# --- Copy Kalkan library to target location ---
sudo cp -f libkalkancryptwr-64.so /srv/kalkan/libkalkancryptwr-64.so

echo "Certificates and Kalkan library installed successfully."