# Azure Production Deployment Guide: Enigma - Club Attendance & Daily Quiz Web App

This guide walks you step-by-step through deploying this Django application to **Microsoft Azure** using **Azure App Service (Linux)** and **Azure Database for MySQL Flexible Server**.

---

## 1. Prerequisites
- An active [Microsoft Azure Account](https://portal.azure.com/).
- [Azure CLI](https://learn.microsoft.com/en-us/cli/azure/install-azure-cli) installed or Azure Cloud Shell.
- Git installed.

---

## 2. Option A: Deploy via Azure App Service with Docker (Recommended)

### Step 1: Create an Azure Resource Group
```bash
az group create --name rg-club-attendance --location eastus
```

### Step 2: Create Azure Database for MySQL Flexible Server
```bash
az mysql flexible-server create \
    --name mysql-club-attendance \
    --resource-group rg-club-attendance \
    --location eastus \
    --admin-user clubadmin \
    --admin-password "YourStrongPassword#2026" \
    --sku-name Standard_B1ms \
    --tier Burstable \
    --version 8.0 \
    --storage-size 32
```

Create the application database:
```bash
az mysql flexible-server db create \
    --resource-group rg-club-attendance \
    --server-name mysql-club-attendance \
    --database-name club_attendance_db
```

Allow Azure services to connect to MySQL:
```bash
az mysql flexible-server firewall-rule create \
    --resource-group rg-club-attendance \
    --name AllowAllAzureIPs \
    --server-name mysql-club-attendance \
    --start-ip-address 0.0.0.0 \
    --end-ip-address 0.0.0.0
```

### Step 3: Build & Push Docker Image to Azure Container Registry (ACR)
```bash
# Create ACR registry
az acr create --resource-group rg-club-attendance --name acrclubattendance --sku Basic --admin-enabled true

# Build and push the image directly with ACR
az acr build --registry acrclubattendance --image club-attendance:v1 .
```

### Step 4: Create Azure App Service Plan & Web App
```bash
# Create Linux App Service Plan (B1 basic plan)
az appservice plan create \
    --name plan-club-attendance \
    --resource-group rg-club-attendance \
    --is-linux \
    --sku B1

# Create the Web App from ACR image
az webapp create \
    --resource-group rg-club-attendance \
    --plan plan-club-attendance \
    --name app-club-attendance \
    --deployment-container-image-name acrclubattendance.azurecr.io/club-attendance:v1
```

### Step 5: Configure Application Settings (Environment Variables) in Azure
Set the required environment variables in the App Service configuration:

```bash
az webapp config appsettings set \
    --resource-group rg-club-attendance \
    --name app-club-attendance \
    --settings \
        DEBUG="False" \
        SECRET_KEY="generate-a-strong-random-50-character-secret-key" \
        ALLOWED_HOSTS="app-club-attendance.azurewebsites.net" \
        CSRF_TRUSTED_ORIGINS="https://app-club-attendance.azurewebsites.net" \
        DB_ENGINE="mysql" \
        DB_NAME="club_attendance_db" \
        DB_USER="clubadmin" \
        DB_PASSWORD="YourStrongPassword#2026" \
        DB_HOST="mysql-club-attendance.mysql.database.azure.com" \
        DB_PORT="3306" \
        EMAIL_BACKEND="django.core.mail.backends.smtp.EmailBackend" \
        EMAIL_HOST="smtp.gmail.com" \
        EMAIL_PORT="587" \
        EMAIL_USE_TLS="True" \
        EMAIL_HOST_USER="your-club-email@gmail.com" \
        EMAIL_HOST_PASSWORD="your-app-password" \
        AUTO_SEED_DATA="True"
```

---

## 3. Option B: Direct Python Code Deployment to Azure App Service (No Docker)

If you prefer deploying code directly without Docker:

1. Create a Linux App Service with Python 3.12:
   ```bash
   az webapp create \
       --resource-group rg-club-attendance \
       --plan plan-club-attendance \
       --name app-club-attendance \
       --runtime "PYTHON:3.12"
   ```

2. In the Azure Portal:
   - Go to **Configuration** &rarr; **General settings**.
   - Set **Startup Command**:
     ```bash
     gunicorn --bind=0.0.0.0 --timeout 600 club_attendance.wsgi:application
     ```
   - Deploy code using Git:
     ```bash
     az webapp up --sku B1 --name app-club-attendance
     ```

---

## 4. Initial Access Credentials
Once seeded (or via `python manage.py seed_data`), log in:
- **Master Admin Portal URL**: `https://<your-app-name>.azurewebsites.net/admin-portal/login/`
  - Email: `admin@club.edu`
  - Password: `Admin@123`
- **Student Sign In**: `https://<your-app-name>.azurewebsites.net/accounts/login/`
  - Email: `arun.sharma@example.com`
  - Password: `Student@123`
