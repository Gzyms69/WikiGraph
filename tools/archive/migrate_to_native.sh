#!/bin/bash
set -e

echo "🚀 Starting Session-Safe Native Docker Installation..."

# 1. Stop Docker Desktop service first (User session level)
echo "🛑 Stopping Docker Desktop service..."
systemctl --user stop docker-desktop || true

# 2. Check current installation state
echo "🔍 Current Docker packages:"
dpkg -l | grep docker || echo "No docker packages found."

# 3. Add Official Repository (Required for docker-ce)
echo "📦 Adding Docker Repository..."
sudo apt-get update
sudo apt-get install -y ca-certificates curl gnupg
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# 4. Install Native Docker (docker-ce)
echo "📦 Installing Native Docker Engine..."
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io

# 5. Add user to group
echo "👤 Adding $USER to docker group..."
sudo usermod -aG docker $USER

# 6. Start native Docker service (System level)
echo "🔌 Enabling and starting Native Docker..."
sudo systemctl enable --now docker

# 7. Context Switch
echo "🔀 Switching CLI context to 'default'..."
docker context use default || true

echo "-------------------------------------------------------"
echo "✅ Installation Complete."
echo "🚀 TO USE DOCKER NOW WITHOUT LOGGING OUT, RUN:"
echo "   newgrp docker"
echo "-------------------------------------------------------"
echo "After running 'newgrp docker', try: 'docker info'"