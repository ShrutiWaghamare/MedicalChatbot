# 🏥 Medical Chatbot

## 📌 Overview

A Medical Chatbot built using **LangChain**, **Azure OpenAI (LLM only)**, **Pinecone**, and **Flask**, with **AWS CI/CD deployment using GitHub Actions**.

---

## 🧰 Tech Stack

* Python
* LangChain
* Flask
* Azure OpenAI (LLM only)
* Pinecone
* Docker
* AWS (EC2, ECR, IAM)
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
```

---

### **STEP 04: Store Embeddings in Pinecone**

```bash
python store_index.py
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

## ☁️ AWS CI/CD Deployment with GitHub Actions

### **STEP 01: Login to AWS Console**

---

### **STEP 02: Create IAM User (For Deployment)**

Attach the following policies:

* `AmazonEC2FullAccess`
* `AmazonEC2ContainerRegistryFullAccess`

---

### **STEP 03: Create an ECR Repository**

Save the repository URI:

```
315865595366.dkr.ecr.us-east-1.amazonaws.com/medicalbot
```

---

### **STEP 04: Create an EC2 Instance**

* OS: **Ubuntu**
* Instance Type: As per requirement

---

### **STEP 05: Install Docker on EC2**

```bash
sudo apt-get update -y
sudo apt-get upgrade -y

curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

sudo usermod -aG docker ubuntu
newgrp docker
```

---

### **STEP 06: Configure EC2 as Self-Hosted GitHub Runner**

Go to:

```
GitHub Repo → Settings → Actions → Runners → New self-hosted runner
```

* Choose OS: **Linux**
* Run the commands **one by one** on EC2

---

### **STEP 07: Configure GitHub Secrets**

Add the following secrets in:

```
GitHub Repo → Settings → Secrets → Actions
```

```
AWS_ACCESS_KEY_ID
AWS_SECRET_ACCESS_KEY
AWS_DEFAULT_REGION
ECR_REPO
PINECONE_API_KEY
AZURE_OPENAI_API_KEY
```

---

## 📦 Deployment Flow (Behind the Scenes)

1. Build Docker image of the source code
2. Push Docker image to AWS ECR
3. Launch EC2 instance
4. Pull Docker image from ECR
5. Run Docker container on EC2

---

## ✅ You’re All Set!

Your Medical Chatbot will now be:

* Running locally via Flask
* Deployed on AWS using Docker + GitHub Actions

