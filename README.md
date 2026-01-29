# 🏥 Medical Chatbot

## 📌 Overview

A Medical Chatbot built using **LangChain**, **Azure OpenAI (LLM only)**, **Pinecone**, and **Flask**, with **Azure CI/CD deployment** using GitHub Actions.

### 🌐 Live Demo

**[Medical Chatbot – AI Health Assistant](https://medicalchatbot-app.whitehill-a20af7d4.eastus.azurecontainerapps.io/)** — try it in your browser.

---

## 🧰 Tech Stack

* Python
* LangChain
* Flask
* Azure OpenAI (LLM only)
* Pinecone
* Docker
* **Azure Cloud Platform:**
  * Azure Container Apps (Serverless containers)
  * Azure Container Registry (ACR)
* GitHub Actions (CI/CD)

---

## 🚀 How to Run the Project (Local Setup)

### **STEP 01: Clone the Repository & Create Conda Environment**

```bash
conda create -n medibot python=3.10 -y
conda activate medibot
```

---

### **STEP 02: Install Dependencies**

```bash
pip install -r requirements.txt
```

---

### **STEP 03: Create `.env` File**

Create a `.env` file in the **root directory** and add:

```env
PINECONE_API_KEY="xxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
AZURE_OPENAI_API_KEY="xxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
AZURE_OPENAI_ENDPOINT="https://your-endpoint.azure.com/"
SECRET_KEY="generate-a-random-secret-key-min-32-chars"
```

**Note:** This project uses **Azure OpenAI** (not OpenAI API). Get your keys from Azure Portal → Your OpenAI resource.

---

### **STEP 04: Store Embeddings in Pinecone**

```bash
python src/store_index.py
```

---

### **STEP 05: Run the Application**

```bash
python app.py
```

---

### **STEP 06: Open in Browser**

```
http://localhost:5000
```

---

## ☁️ Azure CI/CD Deployment with GitHub Actions

### **⭐ Recommended Plan: Azure Container Apps**

For detailed Azure deployment instructions, see **[AZURE_DEPLOYMENT_PLAN.md](AZURE_DEPLOYMENT_PLAN.md)**

**Why Container Apps?**
- ✅ **FREE for first 12 months** (generous free tier allowances)
- ✅ Serverless - Pay only when running
- ✅ Auto-scaling to zero when idle
- ✅ Built-in HTTPS
- ✅ Cost-effective (~$0/month with free tier, ~$5-20/month after)
- ✅ Modern platform for containers

**💡 Free Tier Info:** See [AZURE_FREE_TIER.md](AZURE_FREE_TIER.md) for details on deploying for FREE!

---

### **Quick Setup Steps**

#### **Option 1: Automated Setup (Recommended)**

1. **Run the setup script:**
   ```bash
   chmod +x azure-setup.sh
   ./azure-setup.sh
   ```

2. **Add GitHub Secrets** (output from script):
   ```
   GitHub Repo → Settings → Secrets and variables → Actions
   ```

#### **Option 2: Manual Setup**

1. **Create Azure Resources:**
   - Resource Group
   - Azure Container Registry (ACR)
   - Container Apps Environment
   - Container App

2. **Create Service Principal:**
   ```bash
   az ad sp create-for-rbac --name github-actions-medical-chatbot --role acrpush
   ```

3. **Add GitHub Secrets:**
   ```
   AZURE_ACR_NAME
   AZURE_ACR_LOGIN_SERVER
   AZURE_CLIENT_ID
   AZURE_CLIENT_SECRET
   AZURE_TENANT_ID
   AZURE_SUBSCRIPTION_ID
   AZURE_RESOURCE_GROUP
   AZURE_LOCATION
   AZURE_CONTAINER_APP_NAME
   AZURE_CONTAINER_APP_ENV
   PINECONE_API_KEY
   AZURE_OPENAI_API_KEY
   AZURE_OPENAI_ENDPOINT
   SECRET_KEY
   ```

4. **Deploy:**
   - Push to `main` branch (auto-deploys to Container Apps)
   - Or use manual workflow dispatch

---

## 📦 Deployment Flow (Behind the Scenes)

1. Build Docker image of the source code
2. Push Docker image to Azure Container Registry (ACR)
3. Deploy to Azure Container Apps
4. Application is accessible via HTTPS URL

---

## ✅ You're All Set!

Your Medical Chatbot will now be:

* Running locally via Flask
* Deployed on **Azure Container Apps** using Docker + GitHub Actions

---

## 📚 Additional Resources

- **📖 Complete Deployment Guide:** [NEXT_STEPS.md](NEXT_STEPS.md) - **START HERE for step-by-step deployment instructions**
- **Workflow File:** `.github/workflows/azure-cicd.yaml`
- **Setup Script:** `azure-setup.sh`
