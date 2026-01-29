# 🚀 Medical Chatbot - Complete Deployment Guide

## 📋 **File Management: What to Keep vs Modify**

### ✅ **KEEP AS-IS (Don't Modify)**
These files are production-ready and should remain unchanged:

- **`.github/workflows/azure-cicd.yaml`** - Main CI/CD workflow (builds Docker, pushes to ACR, deploys to Azure)
- **`Dockerfile`** - Container image definition
- **`app.py`** - Flask application entry point
- **`src/chatbot.py`** - RAG chain logic (uses Azure OpenAI)
- **`src/memory.py`** - Conversation memory management
- **`src/storage.py`** - SQLite database operations
- **`src/prompt.py`** - System prompts for the chatbot
- **`src/helper.py`** - PDF loading and text splitting utilities
- **`src/store_index.py`** - Pinecone index creation script (uses HuggingFace embeddings)
- **`requirements.txt`** - Python dependencies
- **`templates/index.html`** - Frontend UI
- **`static/css/style.css`** - Styles
- **`static/js/script.js`** - Frontend JavaScript
- **`.gitignore`** - Git ignore rules
- **`azure-setup.sh`** - Azure resource creation script

### ✏️ **MODIFY/CREATE (You Need to Configure)**

1. **`.env`** (CREATE/UPDATE) - **REQUIRED**
   - Add your actual API keys and secrets
   - **DO NOT commit this file** (already in `.gitignore`)

2. **GitHub Secrets** (CONFIGURE) - **REQUIRED**
   - Add secrets in GitHub repo settings (see Section 4 below)

3. **`data/Medical_book.pdf`** (ADD YOUR PDF) - **REQUIRED**
   - Place your medical PDF documents in the `data/` folder
   - Run `python src/store_index.py` to index them

### 🗑️ **OPTIONAL TO DELETE**

- **`.github/workflows/cicd.yaml`** - Old workflow (if you're using `azure-cicd.yaml` only)
- **`practice/trials.ipynb`** - Development notebook (not needed for production)

---

## ✅ **Current Status**

- ✅ **Backend**: Flask app with RAG (Retrieval-Augmented Generation) using Pinecone + Azure OpenAI
- ✅ **Frontend**: Web UI ready (`templates/index.html`)
- ✅ **Docker**: Production-ready containerization
- ✅ **CI/CD**: GitHub Actions workflow configured for Azure deployment
- ✅ **Azure Setup**: Automated script (`azure-setup.sh`) available

**What's Missing:**
- ❌ Environment variables configured (`.env` file)
- ❌ Pinecone index created (need to run `src/store_index.py`)
- ❌ Azure resources created (need to run `azure-setup.sh`)
- ❌ GitHub Secrets configured (for CI/CD)

---

## 🎯 **Step-by-Step Deployment Guide**

### **1️⃣ Configure Local Environment**

#### **Create `.env` File**

Create a `.env` file in the project root with these variables:

```env
PINECONE_API_KEY=your-pinecone-api-key-here
AZURE_OPENAI_API_KEY=your-azure-openai-api-key-here
AZURE_OPENAI_ENDPOINT=https://your-azure-openai-endpoint.azure.com/
SECRET_KEY=generate-a-random-secret-key-here-min-32-chars
```

**Important Notes:**
- Get `PINECONE_API_KEY` from [Pinecone Console](https://app.pinecone.io/)
- Get `AZURE_OPENAI_API_KEY` and `AZURE_OPENAI_ENDPOINT` from Azure Portal → Your OpenAI resource
- Generate `SECRET_KEY` using: `python -c "import secrets; print(secrets.token_urlsafe(32))"`
- **NEVER commit `.env` to Git** (already in `.gitignore`)

#### **Install Dependencies**

```bash
# Create virtual environment (recommended)
python -m venv venv
# Activate it:
# Windows: venv\Scripts\activate
# Linux/Mac: source venv/bin/activate

# Install packages
pip install -r requirements.txt
```

---

### **2️⃣ Prepare Your Medical Data & Create Pinecone Index**

#### **Add PDF Files**

Place your medical PDF documents in the `data/` folder:
```
data/
  └── Medical_book.pdf  (your medical documents)
```

#### **Create Pinecone Index**

Run the indexing script to upload embeddings to Pinecone:

```bash
python src/store_index.py
```

**What this does:**
- Loads PDFs from `data/` folder
- Splits them into text chunks
- Generates embeddings using HuggingFace model (`sentence-transformers/all-MiniLM-L6-v2`)
- Creates Pinecone index named `medical-chatbot` (if doesn't exist)
- Uploads all embeddings to Pinecone

**Verify:**
- Check [Pinecone Dashboard](https://app.pinecone.io/) → Your index should show vector count > 0

---

### **3️⃣ Test Locally**

#### **Run the Flask App**

```bash
python app.py
```

You should see:
```
Starting Medical Chatbot application...
✅ Chatbot initialized successfully
 * Running on http://0.0.0.0:5000
```

#### **Test in Browser**

1. Open `http://localhost:5000`
2. Ask a medical question (e.g., "What are the symptoms of diabetes?")
3. Verify the chatbot responds with relevant information
4. Test the "Clear" button to reset conversation

**If errors occur:**
- Check `.env` file has all required keys
- Verify Pinecone index exists and has vectors
- Check Azure OpenAI endpoint is correct

**✅ Only proceed to Azure deployment after local testing works!**

---

### **4️⃣ Set Up Azure Resources & GitHub Secrets**

> **🎯 Goal of This Section:** Create all Azure cloud resources needed for deployment and configure GitHub to access them automatically.  
> **⏱️ Estimated Time:** 15-20 minutes  
> **✅ Success Criteria:** All Azure resources created + All GitHub Secrets added → **DO NOT proceed to Section 5 until this is 100% complete!**

---

#### **Step 4.1: Install Prerequisites on Your Local Machine**

**📍 WHERE:** Your local Windows computer  
**🔧 WHAT:** Install tools needed to run Azure commands

##### **4.1.1 Install Azure CLI**

**WHY:** Azure CLI lets you create and manage Azure resources from command line.

**HOW:**
1. **Download Azure CLI:**
   - Go to: https://aka.ms/installazurecliwindows
   - Click "Download" → Run the installer
   - Follow installation wizard (accept defaults)
   - **Restart your terminal/PowerShell after installation**

2. **Verify Installation:**
   - Open **PowerShell** (or Git Bash)
   - Run:
     ```powershell
     az --version
     ```
   - **Expected Output:** Should show Azure CLI version (e.g., `azure-cli 2.xx.x`)
   - **If Error:** Azure CLI not installed correctly → Reinstall

**✅ CHECKPOINT:** You should see Azure CLI version number. If yes, continue. If no, fix installation first.

---

##### **4.1.2 Install Git Bash or WSL (Windows Only)**

**WHY:** The `azure-setup.sh` script is a bash script and needs a bash environment to run.

**OPTION A: Use Git Bash (Easier)**
- If you have Git installed, Git Bash is already included
- Open **Git Bash** from Start Menu

**OPTION B: Use WSL (Windows Subsystem for Linux)**
- Open PowerShell as Administrator
- Run:
  ```powershell
  wsl --install
  ```
- Restart computer when prompted
- After restart, open **Ubuntu** from Start Menu

**OPTION C: Use PowerShell with WSL**
- If WSL already installed, just open **Ubuntu** terminal

**✅ CHECKPOINT:** You should have a bash terminal open (Git Bash or WSL/Ubuntu). If yes, continue.

---

##### **4.1.3 Install `jq` (JSON Parser)**

**WHY:** The setup script uses `jq` to parse JSON output from Azure CLI commands.

**HOW:**

**If using Git Bash:**
```bash
# Download jq for Windows
curl -L -o /usr/bin/jq.exe https://github.com/jqlang/jq/releases/download/jq-1.7.1/jq-win64.exe
chmod +x /usr/bin/jq.exe
```

**If using WSL/Ubuntu:**
```bash
sudo apt update
sudo apt install jq -y
```

**Verify Installation:**
```bash
jq --version
```
- **Expected Output:** Should show version (e.g., `jq-1.7.1`)
- **If Error:** `jq` not found → Check installation path or reinstall

**✅ CHECKPOINT:** `jq --version` should work. If yes, continue.

---

#### **Step 4.2: Login to Azure from Your Local Machine**

**📍 WHERE:** Your bash terminal (Git Bash or WSL)  
**🔧 WHAT:** Authenticate with Azure so you can create resources

**WHY:** Azure CLI needs your credentials to create resources in your Azure subscription.

**HOW:**
1. **Open your bash terminal** (Git Bash or WSL/Ubuntu)

2. **Run login command:**
   ```bash
   az login
   ```

3. **What happens:**
   - A browser window will open automatically
   - **If browser doesn't open:** Copy the URL shown in terminal and paste in browser
   - Login with your Azure account (the one you saw in the VM screenshot: `medharadavidraju@gm...`)
   - Click "Sign in"
   - You'll see: "You have logged in. You can close this window."

4. **Verify Login:**
   ```bash
   az account show
   ```
   - **Expected Output:** Shows your Azure subscription details (name, ID, tenant, etc.)
   - **If Error:** "Please run 'az login' to setup account" → Run `az login` again

5. **Check Active Subscription (if you have multiple):**
   ```bash
   az account list --output table
   ```
   - If you see multiple subscriptions, note which one you want to use
   - To switch subscription:
     ```bash
     az account set --subscription "Your-Subscription-Name"
     ```

**✅ CHECKPOINT:** `az account show` should display your subscription info. If yes, continue.

---

#### **Step 4.3: Navigate to Your Project Directory**

**📍 WHERE:** Your bash terminal  
**🔧 WHAT:** Change directory to where your Medical-Chatbot project is located

**WHY:** The setup script needs to be run from the project root directory.

**HOW:**

**If using Git Bash:**
```bash
# Navigate to your project (adjust path if different)
cd /e/Medical\ Chatbot/Medical-Chatbot

# Verify you're in the right place
ls -la
# You should see: app.py, Dockerfile, azure-setup.sh, src/, etc.
```

**If using WSL:**
```bash
# WSL can access Windows files at /mnt/c/, /mnt/d/, /mnt/e/, etc.
cd /mnt/e/Medical\ Chatbot/Medical-Chatbot

# Verify you're in the right place
ls -la
```

**Alternative (if path has spaces):**
```bash
# Use quotes around path
cd "/e/Medical Chatbot/Medical-Chatbot"
```

**✅ CHECKPOINT:** `ls -la` should show your project files (app.py, Dockerfile, etc.). If yes, continue.

---

#### **Step 4.4: Make Setup Script Executable**

**📍 WHERE:** Your bash terminal (in project directory)  
**🔧 WHAT:** Give execute permission to the bash script

**WHY:** Bash scripts need execute permission to run.

**HOW:**
```bash
chmod +x azure-setup.sh
```

**Verify:**
```bash
ls -l azure-setup.sh
```
- **Expected Output:** Should show `-rwxr-xr-x` (the `x` means executable)
- **If Error:** Script not found → Make sure you're in the project root directory

**✅ CHECKPOINT:** Script should have execute permission. If yes, continue.

---

#### **Step 4.5: Run Azure Setup Script**

**📍 WHERE:** Your bash terminal (in project directory)  
**🔧 WHAT:** Execute the script that creates all Azure resources

**WHY:** This script automates creating:
- Resource Group (container for all resources)
- Azure Container Registry (ACR) - stores Docker images
- Container Apps Environment - hosting platform
- Container App - your running application
- Service Principal - allows GitHub Actions to access Azure

**HOW:**
```bash
./azure-setup.sh
```

**What to Expect:**

1. **Script checks Azure login:**
   ```
   ✅ Azure CLI found
   ✅ Logged in to Azure
   ```

2. **Prompts for inputs (type your answers):**

   **a) Resource Group name:**
   ```
   Enter Resource Group name (default: medical-chatbot-rg):
   ```
   - **What to enter:** Press Enter for default OR type your own name (e.g., `medbot-rg`)
   - **Why:** Groups all resources together for easy management
   - **Example:** `medical-chatbot-rg` or `medbot-rg`

   **b) Azure location:**
   ```
   Enter Azure location (default: eastus):
   ```
   - **What to enter:** Press Enter for `eastus` OR type another region (e.g., `westus2`, `eastus2`)
   - **Why:** Where your resources will be hosted geographically
   - **Common choices:** `eastus`, `westus2`, `eastus2`
   - **Note:** Use same region as your Azure OpenAI resource if possible

   **c) ACR name (Azure Container Registry):**
   ```
   Enter ACR name (must be globally unique, lowercase, 5-50 chars):
   ```
   - **What to enter:** A unique name (e.g., `medbotacr2025`, `mychatbotregistry`)
   - **Why:** Must be globally unique across all Azure customers
   - **Rules:** 
     - Only lowercase letters and numbers
     - 5-50 characters
     - Must be unique (if taken, try different name)
   - **Example:** `medbotacr2025` or `medicalchatbot123`

   **d) Deployment target:**
   ```
   Choose deployment target [1] Container Apps [2] App Service [3] Container Instances (default: 1):
   ```
   - **What to enter:** Type `1` and press Enter (Container Apps is recommended)
   - **Why:** Container Apps is serverless, cost-effective, and auto-scales

3. **Script creates resources (takes 2-5 minutes):**
   ```
   📦 Creating Resource Group: medical-chatbot-rg
   ✅ Resource Group created
   
   🐳 Creating Azure Container Registry: medbotacr2025
   ✅ ACR created
   
   🔑 Creating Service Principal for GitHub Actions...
   ✅ Service Principal created
   
   🚀 Creating Azure Container Apps Environment...
   🚀 Creating Container App...
   ✅ Container App created
   ```

4. **Script prints GitHub Secrets (IMPORTANT - COPY THESE!):**
   ```
   ==========================================
   ✅ Setup Complete!
   ==========================================
   
   📋 GitHub Secrets to Add:
   =========================
   
   AZURE_ACR_NAME=medbotacr2025
   AZURE_ACR_LOGIN_SERVER=medbotacr2025.azurecr.io
   AZURE_CLIENT_ID=12345678-abcd-1234-abcd-123456789abc
   AZURE_CLIENT_SECRET=abc123~XYZ789SecretKey
   AZURE_TENANT_ID=87654321-dcba-4321-dcba-987654321cba
   AZURE_SUBSCRIPTION_ID=11111111-2222-3333-4444-555555555555
   AZURE_RESOURCE_GROUP=medical-chatbot-rg
   AZURE_LOCATION=eastus
   AZURE_CONTAINER_APP_NAME=medbotacr2025-app
   AZURE_CONTAINER_APP_ENV=medbotacr2025-env
   ```

**⚠️ CRITICAL:** Copy ALL these values! You'll need them in the next step.

**If Script Fails:**
- **"Resource group already exists":** Use a different resource group name
- **"ACR name not available":** Try a different ACR name (must be unique)
- **"Permission denied":** Make sure you're logged in with `az login`
- **"jq: command not found":** Install `jq` (see Step 4.1.3)

**✅ CHECKPOINT:** Script should complete successfully and print GitHub Secrets. If yes, continue. **If no, fix errors before proceeding.**

---

#### **Step 4.6: Verify Azure Resources Were Created**

**📍 WHERE:** Azure Portal (web browser)  
**🔧 WHAT:** Confirm all resources exist in Azure

**WHY:** Double-check everything was created correctly before configuring GitHub.

**HOW:**

1. **Open Azure Portal:**
   - Go to: https://portal.azure.com
   - Login with your Azure account

2. **Check Resource Group:**
   - Click "Resource groups" in left menu
   - Find your resource group (e.g., `medical-chatbot-rg`)
   - Click on it
   - **You should see these resources:**
     - ✅ Container Registry (ACR)
     - ✅ Container Apps Environment
     - ✅ Container App

3. **Verify Container Registry:**
   - Click on your ACR resource
   - Check "Repositories" → Should be empty (images will be pushed later)
   - Note the "Login server" (e.g., `medbotacr2025.azurecr.io`)

4. **Verify Container App:**
   - Click on your Container App resource
   - Check "Overview" → Status should show "Running" or "Stopped" (both OK for now)
   - Note the "Application Url" (e.g., `https://medbotacr2025-app.xxxxx.azurecontainerapps.io`)

**✅ CHECKPOINT:** All resources visible in Azure Portal. If yes, continue. If no, check script output for errors.

---

#### **Step 4.7: Add GitHub Secrets (Part 1 - Azure Secrets)**

**📍 WHERE:** GitHub website (in your browser)  
**🔧 WHAT:** Add Azure-related secrets so GitHub Actions can access Azure

**WHY:** GitHub Actions needs these credentials to:
- Push Docker images to Azure Container Registry
- Deploy to Azure Container Apps
- Authenticate with Azure services

**HOW:**

1. **Open GitHub Repository:**
   - Go to: https://github.com/your-username/Medical-Chatbot
   - (Replace `your-username` with your actual GitHub username)

2. **Navigate to Secrets:**
   - Click **"Settings"** tab (top of repository page)
   - In left sidebar, click **"Secrets and variables"**
   - Click **"Actions"** (under "Secrets and variables")

3. **Add Each Secret One by One:**

   **Click "New repository secret"** for each one below:

   **Secret 1: AZURE_ACR_NAME**
   - **Name:** `AZURE_ACR_NAME`
   - **Secret:** Paste the value from script output (e.g., `medbotacr2025`)
   - Click **"Add secret"**

   **Secret 2: AZURE_ACR_LOGIN_SERVER**
   - **Name:** `AZURE_ACR_LOGIN_SERVER`
   - **Secret:** Paste from script (e.g., `medbotacr2025.azurecr.io`)
   - Click **"Add secret"**

   **Secret 3: AZURE_CLIENT_ID**
   - **Name:** `AZURE_CLIENT_ID`
   - **Secret:** Paste the `AZURE_CLIENT_ID` value from script (long GUID)
   - Click **"Add secret"**

   **Secret 4: AZURE_CLIENT_SECRET**
   - **Name:** `AZURE_CLIENT_SECRET`
   - **Secret:** Paste the `AZURE_CLIENT_SECRET` value from script (long string)
   - ⚠️ **IMPORTANT:** Copy this carefully - you won't see it again!
   - Click **"Add secret"**

   **Secret 5: AZURE_TENANT_ID**
   - **Name:** `AZURE_TENANT_ID`
   - **Secret:** Paste from script (GUID)
   - Click **"Add secret"**

   **Secret 6: AZURE_SUBSCRIPTION_ID**
   - **Name:** `AZURE_SUBSCRIPTION_ID`
   - **Secret:** Paste from script (GUID)
   - Click **"Add secret"**

   **Secret 7: AZURE_RESOURCE_GROUP**
   - **Name:** `AZURE_RESOURCE_GROUP`
   - **Secret:** Paste from script (e.g., `medical-chatbot-rg`)
   - Click **"Add secret"**

   **Secret 8: AZURE_LOCATION**
   - **Name:** `AZURE_LOCATION`
   - **Secret:** Paste from script (e.g., `eastus`)
   - Click **"Add secret"**

   **Secret 9: AZURE_CONTAINER_APP_NAME**
   - **Name:** `AZURE_CONTAINER_APP_NAME`
   - **Secret:** Paste from script (e.g., `medbotacr2025-app`)
   - Click **"Add secret"**

   **Secret 10: AZURE_CONTAINER_APP_ENV**
   - **Name:** `AZURE_CONTAINER_APP_ENV`
   - **Secret:** Paste from script (e.g., `medbotacr2025-env`)
   - Click **"Add secret"**

**Verify All Secrets Added:**
- In "Secrets and variables → Actions" page, you should see all 10 secrets listed
- Count them: Should be exactly 10 secrets

**✅ CHECKPOINT:** All 10 Azure secrets added in GitHub. If yes, continue. If no, add missing ones.

---

#### **Step 4.8: Add GitHub Secrets (Part 2 - Application Secrets)**

**📍 WHERE:** GitHub website (same page as Step 4.7)  
**🔧 WHAT:** Add application secrets from your `.env` file

**WHY:** Your chatbot needs these to connect to Pinecone and Azure OpenAI at runtime.

**HOW:**

1. **Open Your `.env` File:**
   - On your local machine, open: `e:\Medical Chatbot\Medical-Chatbot\.env`
   - You should see your keys there

2. **Add Each Secret:**

   **Secret 11: PINECONE_API_KEY**
   - **Name:** `PINECONE_API_KEY`
   - **Secret:** Copy value from `.env` file (starts with `pcsk_...`)
   - Click **"Add secret"**

   **Secret 12: AZURE_OPENAI_API_KEY**
   - **Name:** `AZURE_OPENAI_API_KEY`
   - **Secret:** Copy value from `.env` file (long string)
   - Click **"Add secret"**

   **Secret 13: AZURE_OPENAI_ENDPOINT**
   - **Name:** `AZURE_OPENAI_ENDPOINT`
   - **Secret:** Copy value from `.env` file (URL like `https://xxxxx.azure.com/`)
   - Click **"Add secret"**

   **Secret 14: SECRET_KEY**
   - **Name:** `SECRET_KEY`
   - **Why it's needed:** Flask uses it to sign session cookies (e.g. your chat `session_id`). Without a random secret, someone could forge or tamper with sessions. It is not an API key—just a long random string you generate once.
   - **Secret:** Copy value from `.env` file, or generate a new one:
     ```bash
     python -c "import secrets; print(secrets.token_urlsafe(32))"
     ```
   - Click **"Add secret"**

**Final Verification:**
- Go to "Secrets and variables → Actions"
- **Total secrets should be: 14**
- Verify all names match exactly (case-sensitive):
  - `AZURE_ACR_NAME`
  - `AZURE_ACR_LOGIN_SERVER`
  - `AZURE_CLIENT_ID`
  - `AZURE_CLIENT_SECRET`
  - `AZURE_TENANT_ID`
  - `AZURE_SUBSCRIPTION_ID`
  - `AZURE_RESOURCE_GROUP`
  - `AZURE_LOCATION`
  - `AZURE_CONTAINER_APP_NAME`
  - `AZURE_CONTAINER_APP_ENV`
  - `PINECONE_API_KEY`
  - `AZURE_OPENAI_API_KEY`
  - `AZURE_OPENAI_ENDPOINT`
  - `SECRET_KEY`

**✅ CHECKPOINT:** All 14 secrets added and verified. If yes, **Section 4 is complete!** If no, add missing secrets.

---

#### **🎉 Section 4 Success Checklist**

Before moving to Section 5, verify ALL of these:

- [ ] Azure CLI installed and `az --version` works
- [ ] Bash terminal available (Git Bash or WSL)
- [ ] `jq` installed and `jq --version` works
- [ ] Logged into Azure (`az login` successful)
- [ ] `azure-setup.sh` script ran successfully
- [ ] All Azure resources visible in Azure Portal:
  - [ ] Resource Group exists
  - [ ] Container Registry (ACR) exists
  - [ ] Container Apps Environment exists
  - [ ] Container App exists
- [ ] All 14 GitHub Secrets added:
  - [ ] 10 Azure-related secrets (from script output)
  - [ ] 4 Application secrets (from `.env` file)
- [ ] Secret names match exactly (case-sensitive)

**✅ If ALL checkboxes are checked → Proceed to Section 5!**  
**❌ If ANY checkbox is unchecked → Fix it before proceeding!**

---

#### **🚨 Common Issues & Solutions**

**Issue: "az: command not found"**
- **Solution:** Azure CLI not installed → Install from Step 4.1.1

**Issue: "jq: command not found"**
- **Solution:** Install `jq` from Step 4.1.3

**Issue: "Please run 'az login'"**
- **Solution:** Run `az login` again (Step 4.2)

**Issue: "ACR name not available"**
- **Solution:** Try a different ACR name (must be globally unique)

**Issue: "Permission denied" when running script**
- **Solution:** Make sure script is executable (`chmod +x azure-setup.sh`)

**Issue: Can't find GitHub Secrets page**
- **Solution:** Make sure you're in repository Settings → Secrets and variables → Actions

**Issue: Secret name doesn't match**
- **Solution:** Secret names are case-sensitive → Check exact spelling in `.github/workflows/azure-cicd.yaml`

---

### **5️⃣ Deploy via GitHub CI/CD**

#### **Commit and Push Code**

```bash
# Make sure .env is NOT committed (check .gitignore)
git add .
git commit -m "Ready for Azure deployment"
git push origin main
```

#### **Trigger Deployment**

**Option A: Automatic Deployment (Recommended)**
- Push to `main` branch automatically triggers the workflow
- Default deployment target: `container-apps`

**Option B: Manual Workflow Dispatch**
1. Go to GitHub → **Actions** tab
2. Select workflow: **"CI/CD - Build, Push to ACR & Deploy to Azure"**
3. Click **"Run workflow"**
4. Select:
   - Branch: `main`
   - Deployment Target: `container-apps` (recommended)
5. Click **"Run workflow"**

#### **Monitor Deployment**

1. Click on the running workflow to see logs
2. Watch for these stages:
   - ✅ **continuous-integration**: Builds Docker image, pushes to ACR
   - ✅ **continuous-deployment-container-apps**: Deploys to Azure Container Apps
3. Look for this message in logs:
   ```
   🚀 Application deployed at: https://<your-app-name>.<region>.azurecontainerapps.io
   ```

#### **Access Your Chatbot**

Once deployment succeeds:
1. Copy the URL from workflow logs (format: `https://<app-name>.<region>.azurecontainerapps.io`)
2. Open it in your browser
3. Your chatbot should be live and accessible to anyone with the link! 🎉

**Troubleshooting:**
- If deployment fails, check workflow logs for errors
- Verify all GitHub Secrets are set correctly
- Ensure Azure resources were created successfully
- Check Container App logs in Azure Portal

---

### **6️⃣ Verify Deployment**

#### **Check Azure Portal**

1. Go to [Azure Portal](https://portal.azure.com)
2. Navigate to: **Resource Groups → Your Resource Group → Container Apps → Your Container App**
3. Check:
   - **Status**: Should be "Running"
   - **URL**: Copy the FQDN (Fully Qualified Domain Name)
   - **Logs**: View application logs if needed

#### **Test Public Access**

1. Open the Container App URL in an incognito/private browser window
2. Test the chatbot with a medical question
3. Verify responses are working correctly

**✅ Your chatbot is now publicly accessible via the Azure Container Apps URL!**

---

## 🔄 **Updating Your Chatbot**

### **Update Code**

1. Make changes to your code
2. Commit and push to `main`:
   ```bash
   git add .
   git commit -m "Update chatbot features"
   git push origin main
   ```
3. GitHub Actions automatically rebuilds and redeploys

### **Update Medical Data**

1. Add new PDFs to `data/` folder
2. Run `python src/store_index.py` locally to update Pinecone index
3. Push code changes (Pinecone index is external, so no redeployment needed)

### **Update Environment Variables**

1. Update GitHub Secrets in repository settings
2. Manually trigger workflow or push a commit to redeploy

---

## 🛠️ **Troubleshooting**

### **Local Issues**

- **"Missing required environment variables"**: Check `.env` file exists and has all keys
- **"Index does not exist"**: Run `python src/store_index.py` first
- **Port 5000 already in use**: Change port in `app.py` or stop other services

### **Azure Deployment Issues**

- **"Authentication failed"**: Verify GitHub Secrets are correct
- **"Resource not found"**: Run `azure-setup.sh` again or check resource names
- **"Image pull failed"**: Check ACR credentials and image name
- **"Container app not accessible"**: Verify ingress is set to "external" and check logs

### **Chatbot Not Responding**

- Check Container App logs in Azure Portal
- Verify Pinecone index has vectors
- Verify Azure OpenAI endpoint and keys are correct
- Check network connectivity from Container App to Pinecone/Azure OpenAI

---

## 📚 **Additional Resources**

- **Azure Container Apps Docs**: https://learn.microsoft.com/en-us/azure/container-apps/
- **GitHub Actions Docs**: https://docs.github.com/en/actions
- **Pinecone Docs**: https://docs.pinecone.io/
- **Azure OpenAI Docs**: https://learn.microsoft.com/en-us/azure/ai-services/openai/

---

## ✅ **Checklist Before Going Live**

- [ ] `.env` file created with all required keys
- [ ] Pinecone index created and has vectors
- [ ] Local testing successful (`python app.py` works)
- [ ] Azure CLI installed and logged in
- [ ] `azure-setup.sh` executed successfully
- [ ] All GitHub Secrets added correctly
- [ ] Code pushed to `main` branch
- [ ] GitHub Actions workflow completed successfully
- [ ] Container App URL accessible in browser
- [ ] Chatbot responds correctly to test questions

**Once all checked, your Medical Chatbot is live and accessible to anyone via the Azure Container Apps URL! 🎉**
