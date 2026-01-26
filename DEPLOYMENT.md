# EC2 Deployment Setup Guide

This guide explains how to set up automatic deployment to EC2 via GitHub Actions.

> **📌 Note**: This repository now uses **Self-Hosted Runner** approach (as per YouTube flow). 
> For detailed step-by-step setup, see **[SELF_HOSTED_RUNNER_SETUP.md](./SELF_HOSTED_RUNNER_SETUP.md)**

## How It Works

**Yes, deployment happens automatically!** When you push code to the `main` branch:

1. ✅ **CI (Continuous Integration)**: GitHub Actions builds your Docker image and pushes it to ECR
2. ✅ **CD (Continuous Deployment)**: GitHub Actions automatically SSH into your EC2 instance and deploys the new version

## Prerequisites

### 1. EC2 Instance Setup

- **EC2 Instance**: Ubuntu-based instance (Ubuntu 20.04 or 22.04 recommended)
- **Security Group**: Allow inbound traffic on port 5000 (and port 22 for SSH)
- **IAM Role** (Recommended): Attach an IAM role to your EC2 instance with these permissions:
  ```json
  {
    "Version": "2012-10-17",
    "Statement": [
      {
        "Effect": "Allow",
        "Action": [
          "ecr:GetAuthorizationToken",
          "ecr:BatchCheckLayerAvailability",
          "ecr:GetDownloadUrlForLayer",
          "ecr:BatchGetImage"
        ],
        "Resource": "*"
      }
    ]
  }
  ```

### 2. SSH Key Setup

1. Generate an SSH key pair (if you don't have one):
   ```bash
   ssh-keygen -t rsa -b 4096 -C "github-actions-deploy" -f ~/.ssh/ec2_deploy_key
   ```

2. Copy the **public key** to your EC2 instance:
   ```bash
   ssh-copy-id -i ~/.ssh/ec2_deploy_key.pub ubuntu@your-ec2-ip
   ```
   Or manually add it to `~/.ssh/authorized_keys` on the EC2 instance

3. Keep the **private key** (`ec2_deploy_key`) - you'll add it to GitHub Secrets

### 3. GitHub Secrets Configuration

Go to your GitHub repository → **Settings** → **Secrets and variables** → **Actions** → **New repository secret**

Add these secrets:

#### Required Secrets:

| Secret Name | Description | Example |
|------------|-------------|---------|
| `AWS_ACCESS_KEY_ID` | AWS access key for ECR push | `AKIAIOSFODNN7EXAMPLE` |
| `AWS_SECRET_ACCESS_KEY` | AWS secret key for ECR push | `wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY` |
| `AWS_DEFAULT_REGION` | AWS region | `us-east-1` |
| `ECR_REPO` | Full ECR repository URI | `123456789.dkr.ecr.us-east-1.amazonaws.com/medical-chatbot` |
| `EC2_HOST` | EC2 instance IP or domain | `54.123.45.67` or `ec2.example.com` |
| `EC2_USER` | SSH username (usually `ubuntu` or `ec2-user`) | `ubuntu` |
| `EC2_SSH_KEY` | Private SSH key content (entire key including `-----BEGIN` and `-----END`) | Copy entire private key file content |
| `PINECONE_API_KEY` | Your Pinecone API key | `pcsk_...` |
| `AZURE_OPENAI_API_KEY` | Your Azure OpenAI API key | `...` |
| `AZURE_OPENAI_ENDPOINT` | Your Azure OpenAI endpoint | `https://...` |
| `SECRET_KEY` | Flask secret key (generate a random string) | `your-random-secret-key-here` |

#### How to get the private key content for `EC2_SSH_KEY`:

On Windows (PowerShell):
```powershell
Get-Content ~/.ssh/ec2_deploy_key | Out-String
```

On Linux/Mac:
```bash
cat ~/.ssh/ec2_deploy_key
```

Copy the **entire output** including:
```
-----BEGIN RSA PRIVATE KEY-----
...
-----END RSA PRIVATE KEY-----
```

## Deployment Flow

1. **Push to main branch** → Triggers workflow
2. **Build job** → Builds Docker image and pushes to ECR
3. **Deploy job** → Automatically:
   - Connects to EC2 via SSH
   - Installs Docker (if not present)
   - Installs AWS CLI (if not present)
   - Logs into ECR (using IAM role or credentials)
   - Pulls latest image
   - Stops old container
   - Starts new container with environment variables
   - Verifies deployment

## Manual Deployment (Optional)

You can also trigger deployment manually:
1. Go to **Actions** tab in GitHub
2. Select **CI/CD - Build, Push to ECR & Deploy to EC2** workflow
3. Click **Run workflow** → **Run workflow**

## Troubleshooting

### SSH Connection Issues
- Verify `EC2_HOST` is correct (IP or domain)
- Verify `EC2_USER` is correct (`ubuntu` for Ubuntu, `ec2-user` for Amazon Linux)
- Check EC2 security group allows SSH (port 22) from GitHub Actions IPs
- Verify SSH key is correctly added to GitHub Secrets

### ECR Access Issues
- Ensure EC2 instance has IAM role with ECR permissions (recommended)
- Or configure AWS credentials on EC2 instance manually

### Container Not Starting
- Check GitHub Actions logs for error messages
- SSH into EC2 and check: `sudo docker logs medical-chatbot`
- Verify all environment variables are set correctly in GitHub Secrets

### Port Access Issues
- Ensure EC2 security group allows inbound traffic on port 5000
- Check if application is running: `sudo docker ps`
- Test locally on EC2: `curl http://localhost:5000/health`

## Post-Deployment

After successful deployment, your application will be available at:
- `http://your-ec2-ip:5000`
- Or configure a reverse proxy (nginx) for a custom domain

## Data Persistence

The deployment script mounts a volume at `/home/${EC2_USER}/medical-chatbot-data:/app/data` to persist your SQLite database and other data across deployments.
