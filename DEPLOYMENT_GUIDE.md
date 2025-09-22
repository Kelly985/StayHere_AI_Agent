# Digital Ocean Deployment Guide - Kenyan Real Estate AI Agent

This comprehensive guide will walk you through deploying your Kenyan Real Estate AI Agent on Digital Ocean from scratch. This guide assumes you have never deployed an application before.

## 📋 Prerequisites

Before starting, you'll need:
- A Digital Ocean account (sign up at https://digitalocean.com)
- Your Together AI API key
- Basic familiarity with terminal/command line
- This project code ready on your local machine

## 💳 Step 1: Digital Ocean Account Setup

### 1.1 Create Account and Add Payment Method

1. Go to https://digitalocean.com and click "Sign up"
2. Complete registration with your email
3. Verify your email address
4. Add a payment method (credit card or PayPal)
5. You may get $200 in free credits for new accounts

### 1.2 Generate SSH Key (for secure access)

**On Windows:**
```bash
# Open PowerShell and run:
ssh-keygen -t rsa -b 4096 -C "your-email@example.com"
# Press Enter 3 times to accept defaults
```

**On Mac/Linux:**
```bash
ssh-keygen -t rsa -b 4096 -C "your-email@example.com"
# Press Enter 3 times to accept defaults
```

**Add SSH Key to Digital Ocean:**
1. Go to Digital Ocean dashboard → Settings → Security → SSH Keys
2. Click "Add SSH Key"
3. Copy your public key:
   - Windows: `type %USERPROFILE%\.ssh\id_rsa.pub`
   - Mac/Linux: `cat ~/.ssh/id_rsa.pub`
4. Paste the key and give it a name like "My Laptop"

## 🖥️ Step 2: Create a Droplet (Virtual Server)

### 2.1 Create New Droplet

1. In Digital Ocean dashboard, click "Create" → "Droplets"
2. **Choose an image**: Select "Ubuntu 22.04 (LTS) x64"
3. **Choose a plan**: 
   - For testing: Basic plan, $12/month (2GB RAM, 1 vCPU)
   - For production: Basic plan, $24/month (4GB RAM, 2 vCPUs) - **Recommended**
4. **Choose a datacenter region**: Select the closest to Kenya (Amsterdam or Frankfurt work well)
5. **Authentication**: Select "SSH Keys" and choose the key you added earlier
6. **Finalize and create**:
   - Hostname: `kenyan-real-estate-ai`
   - Tags: `real-estate`, `ai-agent`
   - Enable monitoring and IPv6
7. Click "Create Droplet"

### 2.2 Wait for Droplet Creation

The droplet will take 1-2 minutes to create. You'll get an IP address when it's ready.

## 🔐 Step 3: Connect to Your Server

### 3.1 Connect via SSH

Replace `YOUR_DROPLET_IP` with the actual IP address from Digital Ocean:

```bash
ssh root@YOUR_DROPLET_IP
```

If this is your first time connecting, type "yes" when prompted about authenticity.

### 3.2 Update the Server

```bash
# Update package lists
apt update

# Upgrade all packages
apt upgrade -y

# Install essential tools
apt install -y curl wget git vim ufw
```

## 🐳 Step 4: Install Docker and Docker Compose

### 4.1 Install Docker

```bash
# Remove old versions
apt remove -y docker docker-engine docker.io containerd runc

# Install dependencies
apt install -y apt-transport-https ca-certificates curl gnupg lsb-release

# Add Docker's official GPG key
mkdir -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg

# Add Docker repository
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null

# Update package list
apt update

# Install Docker
apt install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# Start Docker service
systemctl start docker
systemctl enable docker

# Verify installation
docker --version
docker compose version
```

### 4.2 Test Docker Installation

```bash
# Run hello world
docker run hello-world
```

You should see a "Hello from Docker!" message.

## 📁 Step 5: Deploy Your Application

### 5.1 Clone Your Code

**Option A: If your code is on GitHub/GitLab:**
```bash
git clone https://github.com/yourusername/GeneralAIAgent.git
cd GeneralAIAgent
```

**Option B: If your code is on local machine, upload it:**
```bash
# From your local machine, upload the code
scp -r /path/to/GeneralAIAgent root@YOUR_DROPLET_IP:/root/
```

Then on the server:
```bash
cd /root/GeneralAIAgent
```

### 5.2 Create Environment Variables

```bash
# Create environment file
nano .env
```

Add your configuration (press Ctrl+X, then Y, then Enter to save):
```env
# Together AI Configuration
TOGETHER_API_KEY=0ead0c7716c61be64bc13c4a0aea90147e4ddb56a7ac5d437fe15f57b758ea3f
TOGETHER_MODEL=deepseek-ai/DeepSeek-R1-Distill-Llama-70B-free

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=False

# Knowledge Base Configuration
KNOWLEDGE_BASE_PATH=./knowledgebase
MAX_CONTEXT_LENGTH=4000

# Application Settings
APP_NAME=Kenyan Real Estate AI Agent
APP_VERSION=1.0.0
CORS_ORIGINS=["*"]
```

### 5.3 Build and Run the Application

```bash
# Build the Docker image
docker compose build

# Start the application
docker compose up -d

# Check if it's running
docker compose ps
```

You should see your application running.

### 5.4 Test the Application

```bash
# Test health endpoint
curl http://localhost:8000/health

# Test chat endpoint
curl -X POST "http://localhost:8000/chat" \
     -H "Content-Type: application/json" \
     -d '{"query": "What are property prices in Nairobi?"}'
```

## 🔥 Step 6: Configure Firewall

### 6.1 Set up UFW (Uncomplicated Firewall)

```bash
# Reset firewall to defaults
ufw --force reset

# Default policies
ufw default deny incoming
ufw default allow outgoing

# Allow SSH (IMPORTANT: Don't lock yourself out!)
ufw allow ssh

# Allow HTTP and HTTPS
ufw allow 80
ufw allow 443

# Allow your application port
ufw allow 8000

# Enable firewall
ufw enable

# Check status
ufw status
```

## 🌐 Step 7: Set Up Domain Name (Optional but Recommended)

### 7.1 Purchase Domain

1. Buy a domain from Namecheap, GoDaddy, or any registrar
2. Example: `kenyan-real-estate-ai.com`

### 7.2 Configure DNS

In your domain registrar's control panel:
1. Create an A record pointing to your droplet's IP address:
   - Type: A
   - Name: @ (or your subdomain like `api`)
   - Value: YOUR_DROPLET_IP
   - TTL: 3600

### 7.3 Wait for DNS Propagation

DNS changes can take up to 24 hours, but usually work within 1-2 hours.

## 🔒 Step 8: Set Up SSL Certificate (HTTPS)

### 8.1 Install Certbot

```bash
# Install Certbot
apt install -y certbot
```

### 8.2 Stop Docker for Certificate Generation

```bash
# Stop the app temporarily
docker compose down
```

### 8.3 Generate SSL Certificate

Replace `your-domain.com` with your actual domain:

```bash
# Generate certificate
certbot certonly --standalone -d your-domain.com
```

Follow the prompts:
1. Enter your email address
2. Agree to terms of service
3. Choose whether to share email with EFF

### 8.4 Configure Nginx with SSL

Edit the nginx configuration:
```bash
nano nginx.conf
```

Update the server block:
```nginx
server {
    listen 80;
    server_name your-domain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;

    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    location / {
        proxy_pass http://kenyan-real-estate-ai:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto https;
    }
}
```

### 8.5 Update Docker Compose for SSL

Edit `docker-compose.yml`:
```bash
nano docker-compose.yml
```

Update the nginx service:
```yaml
nginx:
  image: nginx:alpine
  container_name: nginx-proxy
  restart: unless-stopped
  ports:
    - "80:80"
    - "443:443"
  volumes:
    - ./nginx.conf:/etc/nginx/nginx.conf:ro
    - /etc/letsencrypt:/etc/letsencrypt:ro
  networks:
    - real-estate-network
  depends_on:
    - kenyan-real-estate-ai
```

### 8.6 Start with SSL

```bash
# Start with production profile
docker compose --profile production up -d

# Check nginx logs if needed
docker compose logs nginx
```

### 8.7 Set Up Auto-Renewal

```bash
# Add cron job for certificate renewal
crontab -e
```

Add this line (select nano if prompted):
```
0 12 * * * /usr/bin/certbot renew --quiet && docker compose --profile production restart nginx
```

## 📊 Step 9: Monitor Your Application

### 9.1 Check Application Status

```bash
# View running containers
docker compose ps

# View logs
docker compose logs kenyan-real-estate-ai
docker compose logs nginx

# Follow logs in real-time
docker compose logs -f kenyan-real-estate-ai
```

### 9.2 Test Your Deployed Application

```bash
# Test health endpoint
curl https://your-domain.com/health

# Test from browser
# Visit https://your-domain.com/docs for API documentation
```

### 9.3 Monitor Resources

```bash
# Check disk usage
df -h

# Check memory usage
free -h

# Check running processes
top

# Docker resource usage
docker stats
```

## 🔄 Step 10: Application Updates and Maintenance

### 10.1 Updating Your Application

When you make changes to your code:

```bash
# Pull latest code (if using Git)
git pull

# Rebuild and restart
docker compose down
docker compose build
docker compose --profile production up -d

# Or use the shortcut
docker compose up -d --build
```

### 10.2 Backup Important Data

```bash
# Create backup script
nano /root/backup.sh
```

Add backup commands:
```bash
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
mkdir -p /root/backups

# Backup knowledge base
tar -czf /root/backups/knowledgebase_$DATE.tar.gz /root/GeneralAIAgent/knowledgebase/

# Backup configuration
cp /root/GeneralAIAgent/.env /root/backups/env_$DATE.backup

# Keep only last 10 backups
ls -t /root/backups/ | tail -n +11 | xargs -d '\n' rm -f

echo "Backup completed: $DATE"
```

Make it executable and schedule it:
```bash
chmod +x /root/backup.sh

# Add to crontab (daily backup at 2 AM)
crontab -e

# Add this line:
0 2 * * * /root/backup.sh >> /var/log/backup.log 2>&1
```

### 10.3 Monitoring Script

Create a monitoring script:
```bash
nano /root/monitor.sh
```

```bash
#!/bin/bash
# Simple monitoring script

echo "=== System Status $(date) ==="
echo "Disk Usage:"
df -h / | tail -1

echo "Memory Usage:"
free -h

echo "Docker Containers:"
docker compose ps

echo "Application Health:"
curl -s http://localhost:8000/health | python3 -m json.tool

echo "Nginx Status:"
systemctl is-active nginx

echo "Last 5 application logs:"
docker compose logs --tail=5 kenyan-real-estate-ai
```

Make it executable:
```bash
chmod +x /root/monitor.sh

# Run it
./monitor.sh
```

## 🚨 Step 11: Troubleshooting Common Issues

### 11.1 Application Won't Start

**Check logs:**
```bash
docker compose logs kenyan-real-estate-ai
```

**Common fixes:**
```bash
# Restart the application
docker compose restart kenyan-real-estate-ai

# Rebuild if needed
docker compose down
docker compose build --no-cache
docker compose up -d
```

### 11.2 Memory Issues

**Check memory usage:**
```bash
free -h
docker stats
```

**If low on memory:**
```bash
# Add swap space
fallocate -l 2G /swapfile
chmod 600 /swapfile
mkswap /swapfile
swapon /swapfile
echo '/swapfile none swap sw 0 0' | tee -a /etc/fstab
```

### 11.3 Disk Space Issues

**Check disk usage:**
```bash
df -h
du -sh /* | sort -hr
```

**Clean up:**
```bash
# Remove unused Docker images
docker image prune -a

# Remove logs older than 7 days
find /var/log -name "*.log" -type f -mtime +7 -delete

# Clean package cache
apt clean
```

### 11.4 Domain/SSL Issues

**Check certificate:**
```bash
certbot certificates
```

**Test SSL:**
```bash
curl -I https://your-domain.com
```

**Renew certificate manually:**
```bash
certbot renew --dry-run
```

### 11.5 Network Issues

**Check firewall:**
```bash
ufw status
```

**Test ports:**
```bash
netstat -tlnp | grep :8000
netstat -tlnp | grep :80
netstat -tlnp | grep :443
```

## 📞 Step 12: Support and Next Steps

### 12.1 Getting Help

If you encounter issues:
1. Check the logs: `docker compose logs kenyan-real-estate-ai`
2. Verify your configuration: `cat .env`
3. Check system resources: `./monitor.sh`
4. Review firewall settings: `ufw status`

### 12.2 Performance Optimization

For better performance:
1. **Upgrade your droplet** if you need more resources
2. **Enable caching** by adding Redis
3. **Use CDN** for static assets
4. **Database optimization** for larger knowledge bases

### 12.3 Security Hardening

Additional security measures:
1. **Change SSH port** from default 22
2. **Disable root login** and create a regular user
3. **Install fail2ban** for intrusion prevention
4. **Regular security updates**

### 12.4 Scaling Up

As your application grows:
1. **Load balancer** with multiple droplets
2. **Managed database** for persistent data
3. **Container orchestration** with Kubernetes
4. **Monitoring tools** like Prometheus and Grafana

## 🎉 Congratulations!

You have successfully deployed your Kenyan Real Estate AI Agent to Digital Ocean! Your application is now:

- ✅ Running in the cloud
- ✅ Accessible via HTTPS
- ✅ Automatically backed up
- ✅ Monitored and maintained

**Your API is now available at:**
- Main endpoint: `https://your-domain.com`
- API documentation: `https://your-domain.com/docs`
- Health check: `https://your-domain.com/health`

### Next Steps:
1. Test all endpoints thoroughly
2. Set up monitoring alerts
3. Plan for scaling as usage grows
4. Consider implementing user authentication
5. Add usage analytics

**Remember to:**
- Monitor your costs in the Digital Ocean dashboard
- Keep your Together AI API key secure
- Regular backups and updates
- Monitor application performance

Happy deploying! 🚀
