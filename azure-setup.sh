#!/bin/bash
# Azure Setup Script for Medical Chatbot
# This script helps you set up Azure resources for deployment

set -e

echo "🚀 Azure Setup Script for Medical Chatbot"
echo "=========================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if Azure CLI is installed
if ! command -v az &> /dev/null; then
    echo -e "${RED}❌ Azure CLI is not installed.${NC}"
    echo "Please install it from: https://aka.ms/installazurecliwindows"
    exit 1
fi

echo -e "${GREEN}✅ Azure CLI found${NC}"
echo ""

# Login check
echo "Checking Azure login status..."
if ! az account show &> /dev/null; then
    echo -e "${YELLOW}⚠️  Not logged in to Azure. Please login:${NC}"
    az login
fi

echo -e "${GREEN}✅ Logged in to Azure${NC}"
echo ""

# Get user inputs
read -p "Enter Resource Group name (default: medical-chatbot-rg): " RESOURCE_GROUP
RESOURCE_GROUP=${RESOURCE_GROUP:-medical-chatbot-rg}

read -p "Enter Azure location (default: eastus): " LOCATION
LOCATION=${LOCATION:-eastus}

read -p "Enter ACR name (must be globally unique, lowercase, 5-50 chars): " ACR_NAME
if [ -z "$ACR_NAME" ]; then
    echo -e "${RED}❌ ACR name is required${NC}"
    exit 1
fi

read -p "Choose deployment target [1] Container Apps [2] App Service [3] Container Instances (default: 1): " DEPLOYMENT_CHOICE
DEPLOYMENT_CHOICE=${DEPLOYMENT_CHOICE:-1}

echo ""
echo "=========================================="
echo "Creating Azure Resources..."
echo "=========================================="
echo ""

# Create Resource Group
echo "📦 Creating Resource Group: $RESOURCE_GROUP"
az group create --name $RESOURCE_GROUP --location $LOCATION --output table
echo -e "${GREEN}✅ Resource Group created${NC}"
echo ""

# Create ACR (skip if already exists - e.g. after a previous failed run)
echo "🐳 Creating Azure Container Registry: $ACR_NAME"
if az acr show --name $ACR_NAME --resource-group $RESOURCE_GROUP &>/dev/null; then
  echo "   (ACR already exists, skipping create)"
else
  az acr create \
    --resource-group $RESOURCE_GROUP \
    --name $ACR_NAME \
    --sku Basic \
    --location $LOCATION \
    --output table
  echo "🔐 Enabling ACR admin user..."
  az acr update --name $ACR_NAME --admin-enabled true
fi

# Get ACR credentials
echo "📋 Getting ACR credentials..."
ACR_LOGIN_SERVER=$(az acr show --name $ACR_NAME --resource-group $RESOURCE_GROUP --query loginServer --output tsv)
ACR_USERNAME=$(az acr credential show --name $ACR_NAME --resource-group $RESOURCE_GROUP --query username --output tsv)
ACR_PASSWORD=$(az acr credential show --name $ACR_NAME --resource-group $RESOURCE_GROUP --query passwords[0].value --output tsv)

echo -e "${GREEN}✅ ACR created${NC}"
echo "  Login Server: $ACR_LOGIN_SERVER"
echo "  Username: $ACR_USERNAME"
echo ""

# Create Service Principal (MSYS_NO_PATHCONV=1 prevents Git Bash from mangling /subscriptions/... path)
echo "🔑 Creating Service Principal for GitHub Actions..."
SUBSCRIPTION_ID=$(az account show --query id --output tsv)
SP_NAME="github-actions-$ACR_NAME"
SCOPE="/subscriptions/${SUBSCRIPTION_ID}/resourceGroups/${RESOURCE_GROUP}/providers/Microsoft.ContainerRegistry/registries/${ACR_NAME}"

SP_OUTPUT=$(MSYS_NO_PATHCONV=1 az ad sp create-for-rbac \
  --name "$SP_NAME" \
  --role acrpush \
  --scopes "$SCOPE" \
  --output json)

AZURE_CLIENT_ID=$(echo $SP_OUTPUT | jq -r '.appId')
AZURE_CLIENT_SECRET=$(echo $SP_OUTPUT | jq -r '.password')
AZURE_TENANT_ID=$(echo $SP_OUTPUT | jq -r '.tenant')

echo -e "${GREEN}✅ Service Principal created${NC}"
echo ""

# Create deployment target based on choice
case $DEPLOYMENT_CHOICE in
  1)
    echo "🚀 Creating Azure Container Apps Environment..."
    ENV_NAME="${ACR_NAME}-env"
    az containerapp env create \
      --name $ENV_NAME \
      --resource-group $RESOURCE_GROUP \
      --location $LOCATION \
      --output table
    
    echo "🚀 Creating Container App..."
    APP_NAME="${ACR_NAME}-app"
    # Use placeholder image (real image does not exist yet). GitHub Actions will update to medical-chatbot:latest on first push.
    PLACEHOLDER_IMAGE="mcr.microsoft.com/azuredocs/containerapps-helloworld:latest"
    if az containerapp show --name $APP_NAME --resource-group $RESOURCE_GROUP &>/dev/null; then
      echo "   (Container App already exists, updating to placeholder image so it can provision)"
      az containerapp update \
        --name $APP_NAME \
        --resource-group $RESOURCE_GROUP \
        --image "$PLACEHOLDER_IMAGE" \
        --output table
    else
      az containerapp create \
        --name $APP_NAME \
        --resource-group $RESOURCE_GROUP \
        --environment $ENV_NAME \
        --image "$PLACEHOLDER_IMAGE" \
        --target-port 5000 \
        --ingress external \
        --min-replicas 0 \
        --max-replicas 1 \
        --cpu 1.0 \
        --memory 2.0Gi \
        --output table
    fi
    
    # Grant Contributor role to service principal (MSYS_NO_PATHCONV=1 for Git Bash)
    echo "🔐 Granting permissions..."
    RG_SCOPE="/subscriptions/${SUBSCRIPTION_ID}/resourceGroups/${RESOURCE_GROUP}"
    MSYS_NO_PATHCONV=1 az role assignment create \
      --assignee $AZURE_CLIENT_ID \
      --role Contributor \
      --scope "$RG_SCOPE" \
      --output none
    
    echo -e "${GREEN}✅ Container App created${NC}"
    echo "  App Name: $APP_NAME"
    echo "  Environment: $ENV_NAME"
    ;;
    
  2)
    echo "🚀 Creating App Service Plan..."
    PLAN_NAME="${ACR_NAME}-plan"
    az appservice plan create \
      --name $PLAN_NAME \
      --resource-group $RESOURCE_GROUP \
      --location $LOCATION \
      --is-linux \
      --sku B1 \
      --output table
    
    echo "🚀 Creating Web App..."
    APP_NAME="${ACR_NAME}-app"
    az webapp create \
      --name $APP_NAME \
      --resource-group $RESOURCE_GROUP \
      --plan $PLAN_NAME \
      --deployment-container-image-name $ACR_LOGIN_SERVER/$APP_NAME:latest \
      --output table
    
    echo "🔐 Configuring container registry..."
    az webapp config container set \
      --name $APP_NAME \
      --resource-group $RESOURCE_GROUP \
      --docker-custom-image-name $ACR_LOGIN_SERVER/$APP_NAME:latest \
      --docker-registry-server-url https://$ACR_LOGIN_SERVER \
      --docker-registry-server-user $AZURE_CLIENT_ID \
      --docker-registry-server-password $AZURE_CLIENT_SECRET \
      --output table
    
    echo "⚙️  Setting port..."
    az webapp config appsettings set \
      --name $APP_NAME \
      --resource-group $RESOURCE_GROUP \
      --settings WEBSITES_PORT=5000 \
      --output none
    
    echo -e "${GREEN}✅ App Service created${NC}"
    echo "  App Name: $APP_NAME"
    echo "  Plan: $PLAN_NAME"
    ;;
    
  3)
    echo "🚀 Container Instances will be created by GitHub Actions workflow"
    APP_NAME="${ACR_NAME}-instance"
    echo -e "${GREEN}✅ Ready for Container Instances deployment${NC}"
    echo "  Instance Name: $APP_NAME"
    ;;
esac

echo ""
echo "=========================================="
echo "✅ Setup Complete!"
echo "=========================================="
echo ""
echo "📋 GitHub Secrets to Add:"
echo "========================="
echo ""
echo "AZURE_ACR_NAME=$ACR_NAME"
echo "AZURE_ACR_LOGIN_SERVER=$ACR_LOGIN_SERVER"
echo "AZURE_CLIENT_ID=$AZURE_CLIENT_ID"
echo "AZURE_CLIENT_SECRET=$AZURE_CLIENT_SECRET"
echo "AZURE_TENANT_ID=$AZURE_TENANT_ID"
echo "AZURE_SUBSCRIPTION_ID=$SUBSCRIPTION_ID"
echo "AZURE_RESOURCE_GROUP=$RESOURCE_GROUP"
echo "AZURE_LOCATION=$LOCATION"
echo ""

case $DEPLOYMENT_CHOICE in
  1)
    echo "AZURE_CONTAINER_APP_NAME=$APP_NAME"
    echo "AZURE_CONTAINER_APP_ENV=$ENV_NAME"
    ;;
  2)
    echo "AZURE_APP_SERVICE_NAME=$APP_NAME"
    echo "AZURE_APP_SERVICE_PLAN=$PLAN_NAME"
    ;;
  3)
    echo "AZURE_CONTAINER_INSTANCE_NAME=$APP_NAME"
    ;;
esac

echo ""
echo "⚠️  IMPORTANT: Add these secrets in GitHub:"
echo "   Repo → Settings → Secrets and variables → Actions"
echo ""
echo "🔗 Next Steps:"
echo "1. Add the secrets above to GitHub"
echo "2. Push code to trigger the Azure CI/CD workflow"
echo "3. Monitor deployment in GitHub Actions"
echo ""
