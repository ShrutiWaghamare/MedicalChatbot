# Self-Hosted Runner Setup Guide (YouTube Flow)

This guide follows the self-hosted GitHub Actions runner approach where your EC2 instance acts as the runner.

## 📋 Step-by-Step Setup

### **Step 1: AWS Setup**

#### 1.1 Create IAM User
1. Go to **AWS Console** → **IAM** → **Users**
2. Click **Create user**
3. Username: `medical-chatbot-deploy`
4. Click **Next**
5. Select **Attach policies directly**
6. Attach these policies:
   - `AmazonEC2ContainerRegistryFullAccess` (for ECR)
   - `AmazonEC2FullAccess` (optional, if you need EC2 management)
7. Click **Next** → **Create user**
8. Click on the user → **Security credentials** tab
9. Click **Create access key**
10. Select **Command Line Interface (CLI)**
11. Click **Next** → **Create access key**
12. **IMPORTANT**: Copy and save:
    - **Access Key ID**
    - **Secret Access Key** (shown only once!)

#### 1.2 Create ECR Repository
1. Go to **AWS Console** → Search **ECR** (Elastic Container Registry)
2. Click **Create repository**
3. Visibility: **Private**
4. Repository name: `medical-chatbot`
5. Click **Create repository**
6. **Copy the repository URI** (e.g., `123456789.dkr.ecr.us-east-1.amazonaws.com/medical-chatbot`)
7. Note your **AWS region** (e.g., `us-east-1`)

#### 1.3 Launch EC2 Instance
1. Go to **EC2** → **Launch Instance**
2. **Name**: `medical-chatbot-server`
3. **AMI**: Ubuntu Server 22.04 LTS (or 20.04)
4. **Instance type**: `t3.medium` or `t3.large` (minimum 4GB RAM recommended)
5. **Key pair**: 
   - If you have one: Select it
   - If not: Click **Create new key pair** → Name it → Download `.pem` file
6. **Network settings**:
   - ✅ Allow SSH traffic from My IP
   - ✅ Allow HTTP traffic from the internet (0.0.0.0/0)
   - ✅ Allow HTTPS traffic from the internet (0.0.0.0/0)
7. **Configure storage**: 30 GB gp3
8. Click **Launch instance**
9. Wait for instance to be **running**
10. Note the **Public IPv4 address** (e.g., `54.123.45.67`)

#### 1.4 Configure Security Group (Important!)
1. Click on your EC2 instance
2. Go to **Security** tab → Click on **Security groups**
3. Click **Edit inbound rules**
4. Add these rules:
   - **Type**: SSH, Port: 22, Source: My IP (for initial setup)
   - **Type**: Custom TCP, Port: 5000, Source: 0.0.0.0/0 (for your app)
5. Click **Save rules**

---

### **Step 2: EC2 Instance Configuration**

#### 2.1 Connect to EC2
**On Windows (PowerShell):**
```powershell
# Navigate to where your .pem file is
cd C:\Users\YourName\Downloads

# Connect (replace with your key and IP)
ssh -i your-key.pem ubuntu@54.123.45.67
```

**On Mac/Linux:**
```bash
chmod 400 your-key.pem
ssh -i your-key.pem ubuntu@54.123.45.67
```

#### 2.2 Install Docker on EC2
Once connected to EC2, run:

```bash
# Update system
sudo apt-get update

# Install Docker
sudo apt-get install docker.io -y

# Start Docker service
sudo systemctl start docker
sudo systemctl enable docker

# Add current user to docker group (to run docker without sudo)
sudo usermod -aG docker $USER

# Log out and log back in for group changes to take effect
exit
```

**Reconnect to EC2:**
```bash
ssh -i your-key.pem ubuntu@54.123.45.67
```

**Verify Docker:**
```bash
docker --version
docker ps
```

#### 2.3 Install AWS CLI on EC2
```bash
# Install AWS CLI v2
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
sudo apt-get install unzip -y
unzip awscliv2.zip
sudo ./aws/install

# Verify installation
aws --version
```

#### 2.4 Configure AWS Credentials on EC2 (Optional - if not using IAM role)
```bash
aws configure
# Enter your Access Key ID
# Enter your Secret Access Key
# Enter your region (e.g., us-east-1)
# Enter default output format: json
```

**OR** (Recommended) Attach IAM Role to EC2:
1. Go to EC2 → Select your instance → **Actions** → **Security** → **Modify IAM role**
2. Create/Select IAM role with `AmazonEC2ContainerRegistryReadOnly` policy
3. Attach it to the instance

---

### **Step 3: Setup GitHub Actions Self-Hosted Runner**

#### 3.1 Get Runner Setup Token
1. Go to your **GitHub repository**
2. Click **Settings** → **Actions** → **Runners**
3. Click **New self-hosted runner**
4. Select **Linux** and **x64**
5. **Copy the commands** shown (they look like this):

```bash
# Create a folder
mkdir actions-runner && cd actions-runner

# Download the latest runner package
curl -o actions-runner-linux-x64-2.311.0.tar.gz -L https://github.com/actions/runner/releases/download/v2.311.0/actions-runner-linux-x64-2.311.0.tar.gz

# Extract the installer
tar xzf ./actions-runner-linux-x64-2.311.0.tar.gz

# Create the runner and start the configuration
./config.sh --url https://github.com/YOUR_USERNAME/YOUR_REPO --token YOUR_TOKEN
```

#### 3.2 Install Runner on EC2
**On your EC2 instance**, run the commands from step 3.1:

```bash
# Create a folder
mkdir actions-runner && cd actions-runner

# Download the latest runner package (use the URL from GitHub)
curl -o actions-runner-linux-x64-2.311.0.tar.gz -L https://github.com/actions/runner/releases/download/v2.311.0/actions-runner-linux-x64-2.311.0.tar.gz

# Extract the installer
tar xzf ./actions-runner-linux-x64-2.311.0.tar.gz

# Configure the runner (use YOUR repository URL and token from GitHub)
./config.sh --url https://github.com/YOUR_USERNAME/YOUR_REPO --token YOUR_TOKEN

# When prompted:
# - Enter runner name: medical-chatbot-runner (or press Enter for default)
# - Enter runner group: press Enter (default)
# - Enter labels: press Enter (default)
# - Enter work folder: press Enter (default)
```

#### 3.3 Start Runner as a Service
```bash
# Install as a service (runs automatically on boot)
sudo ./svc.sh install

# Start the service
sudo ./svc.sh start

# Check status
sudo ./svc.sh status
```

**Verify runner is online:**
- Go to GitHub → **Settings** → **Actions** → **Runners**
- You should see your runner with a green dot (online)

---

### **Step 4: Configure GitHub Secrets**

Go to your GitHub repository → **Settings** → **Secrets and variables** → **Actions** → **New repository secret**

Add these secrets:

| Secret Name | Value | Example |
|------------|-------|---------|
| `AWS_ACCESS_KEY_ID` | From Step 1.1 | `AKIAIOSFODNN7EXAMPLE` |
| `AWS_SECRET_ACCESS_KEY` | From Step 1.1 | `wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY` |
| `AWS_DEFAULT_REGION` | Your AWS region | `us-east-1` |
| `ECR_REPO` | Full ECR repository URI | `123456789.dkr.ecr.us-east-1.amazonaws.com/medical-chatbot` |
| `PINECONE_API_KEY` | Your Pinecone API key | `pcsk_...` |
| `AZURE_OPENAI_API_KEY` | Your Azure OpenAI API key | `...` |
| `AZURE_OPENAI_ENDPOINT` | Your Azure OpenAI endpoint | `https://...` |
| `SECRET_KEY` | Flask secret key (generate random string) | `your-random-secret-key-here` |

**Generate SECRET_KEY:**
```bash
# On Linux/Mac
openssl rand -hex 32

# On Windows PowerShell
-join ((48..57) + (65..90) + (97..122) | Get-Random -Count 32 | % {[char]$_})
```

---

### **Step 5: Verify Your Workflow File**

Your `.github/workflows/cicd.yaml` should now use `runs-on: self-hosted` (already updated!)

Key points:
- ✅ `continuous-integration` job uses `runs-on: self-hosted`
- ✅ `continuous-deployment` job uses `runs-on: self-hosted`
- ✅ No SSH keys needed!
- ✅ Runner executes directly on EC2

---

### **Step 6: Deploy!**

1. **Commit and push your code:**
```bash
git add .
git commit -m "Setup CI/CD with self-hosted runner"
git push origin main
```

2. **Watch the deployment:**
   - Go to GitHub → **Actions** tab
   - You'll see the workflow running
   - Click on it to see live logs

3. **What happens:**
   - ✅ Code is checked out on EC2
   - ✅ Docker image is built
   - ✅ Image is pushed to ECR
   - ✅ Image is pulled from ECR
   - ✅ Old container is stopped
   - ✅ New container is started

---

### **Step 7: Access Your Application**

After successful deployment:
- Open browser: `http://YOUR_EC2_IP:5000`
- Example: `http://54.123.45.67:5000`

---

## 🔍 Troubleshooting

### Runner Not Showing Online
```bash
# Check runner service status
sudo ./svc.sh status

# Check logs
sudo journalctl -u actions.runner.* -f

# Restart runner
sudo ./svc.sh stop
sudo ./svc.sh start
```

### Docker Permission Denied
```bash
# Add user to docker group
sudo usermod -aG docker $USER
# Log out and log back in
exit
```

### ECR Login Failed
- Verify AWS credentials in GitHub Secrets
- Check IAM user has ECR permissions
- Or ensure EC2 has IAM role with ECR access

### Container Not Starting
```bash
# Check container logs
docker logs medical-chatbot

# Check if container is running
docker ps -a

# Check port is accessible
curl http://localhost:5000/health
```

### Port 5000 Not Accessible
- Verify Security Group allows port 5000 (0.0.0.0/0)
- Check if container is running: `docker ps`
- Test locally: `curl http://localhost:5000/health`

---

## 🎯 Key Differences: Self-Hosted vs SSH Approach

| Feature | Self-Hosted Runner | SSH Approach |
|---------|-------------------|--------------|
| Setup Complexity | Medium | Easy |
| Security | Runner on EC2 | SSH keys in GitHub |
| Execution | Direct on EC2 | Remote via SSH |
| Runner Management | Manual | Automatic |
| Best For | Long-running instances | Temporary deployments |

---

## 💰 Cost Optimization

- **Stop EC2** when not in use (Instance State → Stop)
- **Terminate** when project is complete
- **Delete ECR repository** to avoid storage charges
- **Delete IAM user** after project completion

---

## ✅ Checklist

- [ ] IAM user created with access keys
- [ ] ECR repository created
- [ ] EC2 instance launched
- [ ] Security group configured (ports 22, 5000)
- [ ] Docker installed on EC2
- [ ] AWS CLI installed on EC2
- [ ] GitHub Actions runner installed and running
- [ ] All GitHub Secrets added
- [ ] Workflow file uses `self-hosted` runner
- [ ] Code pushed to main branch
- [ ] Application accessible at `http://EC2_IP:5000`

---

**You're all set! Every push to `main` will automatically deploy! 🚀**
