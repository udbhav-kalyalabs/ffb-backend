# 🔐 Environment Setup Guide

## Required Environment Variables

Create a `.env` file in the root directory with these variables:

```env
# ============================================================================
# AWS CONFIGURATION (Required)
# ============================================================================
AWS_ACCESS_KEY_ID=your_aws_access_key
AWS_SECRET_ACCESS_KEY=your_aws_secret_key
AWS_REGION=us-east-1

# ============================================================================
# S3 STORAGE (Required)
# ============================================================================
S3_BUCKET_NAME=agriai-images
S3_ORIGINAL_PREFIX=originals/
S3_ANNOTATED_PREFIX=annotated/
S3_PRESIGNED_URL_EXPIRATION=3600

# ============================================================================
# MONGODB (Required)
# ============================================================================
MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/?retryWrites=true&w=majority
MONGO_DATABASE=agriai_db
MONGO_COLLECTION=analyses

# ============================================================================
# AWS BEDROCK (Required)
# ============================================================================
BEDROCK_MODEL_ID=anthropic.claude-3-5-sonnet-20240620-v1:0

# ============================================================================
# OBJECT DETECTION (Optional)
# ============================================================================
USE_OBJECT_DETECTION=true
DETECTION_BACKEND=roboflow
DETECTION_CONFIDENCE=0.40

ROBOFLOW_API_KEY=your_roboflow_key
ROBOFLOW_MODEL_ID=oil-palm-segmentation1
ROBOFLOW_VERSION=1
```

---

## 🔍 How to Get These Values

### 1. AWS Credentials

**AWS Access Key & Secret Key:**
1. Go to AWS Console → IAM
2. Create a user or use existing
3. Go to "Security credentials" tab
4. Click "Create access key"
5. Copy both `Access Key ID` and `Secret Access Key`

**Required IAM Permissions:**
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:PutObject",
        "s3:GetObject",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::agriai-images/*",
        "arn:aws:s3:::agriai-images"
      ]
    },
    {
      "Effect": "Allow",
      "Action": [
        "bedrock:InvokeModel"
      ],
      "Resource": "*"
    }
  ]
}
```

### 2. S3 Bucket

**Create Bucket:**
```bash
# Using AWS CLI
aws s3 mb s3://agriai-images --region us-east-1
```

Or via AWS Console:
1. Go to S3 Console
2. Click "Create bucket"
3. Name: `agriai-images`
4. Region: Choose your region
5. Keep default settings
6. Click "Create bucket"

**Bucket Name:**
- Use any unique name
- Update `S3_BUCKET_NAME` in `.env`

### 3. MongoDB

**MongoDB Atlas (Recommended - Free Tier Available):**

1. Go to https://www.mongodb.com/cloud/atlas
2. Sign up or log in
3. Create a cluster (Free M0 tier is fine)
4. Click "Connect" → "Connect your application"
5. Copy the connection string
6. Replace `<password>` with your password

**Connection String Format:**
```
mongodb+srv://username:password@cluster.mongodb.net/?retryWrites=true&w=majority
```

**Important:**
- Whitelist your IP or use 0.0.0.0/0 for development
- For ECS, whitelist the NAT Gateway IP

### 4. AWS Bedrock Model ID

**Default (recommended):**
```
anthropic.claude-3-5-sonnet-20240620-v1:0
```

**Enable Bedrock:**
1. Go to AWS Bedrock Console
2. Click "Model access"
3. Request access to Anthropic Claude models
4. Wait for approval (usually instant)

### 5. Roboflow API Key (Optional)

**If using Roboflow for object detection:**

1. Sign up at https://roboflow.com
2. Go to Settings → API
3. Copy your API key
4. Find a model or use Universe models
5. Copy the model ID

**Alternative:** Set `DETECTION_BACKEND=mock` for testing without detection

---

## 🚀 Quick Setup Script

```bash
# 1. Clone/navigate to project
cd AgriAI

# 2. Install dependencies
pip install -r requirements.txt

# 3. Create .env file
cat > .env << 'EOF'
AWS_ACCESS_KEY_ID=your_key
AWS_SECRET_ACCESS_KEY=your_secret
AWS_REGION=us-east-1

S3_BUCKET_NAME=agriai-images

MONGODB_URI=mongodb+srv://user:pass@cluster.mongodb.net/
MONGO_DATABASE=agriai_db

BEDROCK_MODEL_ID=anthropic.claude-3-5-sonnet-20240620-v1:0

USE_OBJECT_DETECTION=true
DETECTION_BACKEND=roboflow
ROBOFLOW_API_KEY=your_roboflow_key
EOF

# 4. Update .env with your actual values
nano .env  # or use your preferred editor

# 5. Create S3 bucket
aws s3 mb s3://agriai-images

# 6. Run the API
python main.py
```

---

## ✅ Verification

### Test MongoDB Connection:
```bash
mongosh "your-mongodb-uri"
```

### Test S3 Access:
```bash
aws s3 ls s3://agriai-images/
```

### Test Bedrock Access:
```bash
aws bedrock list-foundation-models --region us-east-1
```

### Test API:
```bash
# Start API
python main.py

# In another terminal
curl http://localhost:8000/api/v1/health
```

---

## 🔒 Security Best Practices

### For Development:
- ✅ Use `.env` file (gitignored)
- ✅ Never commit credentials to git
- ✅ Use IAM users with minimal permissions

### For Production (ECS):
- ✅ Use AWS Secrets Manager
- ✅ Use IAM roles instead of access keys
- ✅ Rotate credentials regularly
- ✅ Enable CloudTrail logging

**ECS Task Definition Example:**
```json
{
  "secrets": [
    {
      "name": "MONGODB_URI",
      "valueFrom": "arn:aws:secretsmanager:us-east-1:123456789:secret:mongodb-uri"
    }
  ]
}
```

---

## 🔧 Troubleshooting

### Issue: "AWS credentials not found"
**Solution:**
```bash
# Verify .env file exists
cat .env | grep AWS_ACCESS_KEY_ID

# Check if dotenv is loading
python -c "from dotenv import load_dotenv; load_dotenv(); import os; print(os.getenv('AWS_ACCESS_KEY_ID'))"
```

### Issue: "MongoDB connection timeout"
**Solution:**
- Check IP whitelist in MongoDB Atlas
- Verify connection string format
- Test connection: `mongosh "your-uri"`

### Issue: "S3 bucket not found"
**Solution:**
```bash
# List buckets
aws s3 ls

# Create bucket
aws s3 mb s3://agriai-images
```

### Issue: "Bedrock access denied"
**Solution:**
- Go to Bedrock Console → Model access
- Request access to Claude models
- Check IAM permissions

---

## 📋 Environment Variables Reference

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `AWS_ACCESS_KEY_ID` | ✅ | - | AWS access key |
| `AWS_SECRET_ACCESS_KEY` | ✅ | - | AWS secret key |
| `AWS_REGION` | ✅ | us-east-1 | AWS region |
| `S3_BUCKET_NAME` | ✅ | - | S3 bucket name |
| `S3_ORIGINAL_PREFIX` | ❌ | originals/ | Prefix for original images |
| `S3_ANNOTATED_PREFIX` | ❌ | annotated/ | Prefix for annotated images |
| `S3_PRESIGNED_URL_EXPIRATION` | ❌ | 3600 | Presigned URL validity (seconds) |
| `MONGODB_URI` | ✅ | - | MongoDB connection string |
| `MONGO_DATABASE` | ❌ | agriai_db | Database name |
| `MONGO_COLLECTION` | ❌ | analyses | Collection name |
| `BEDROCK_MODEL_ID` | ✅ | - | Bedrock model identifier |
| `USE_OBJECT_DETECTION` | ❌ | true | Enable object detection |
| `DETECTION_BACKEND` | ❌ | roboflow | Detection backend |
| `ROBOFLOW_API_KEY` | ❌ | - | Roboflow API key |

---

## 🎯 Minimal .env for Testing

```env
# Minimum required for basic testing (without storage)
AWS_ACCESS_KEY_ID=your_key
AWS_SECRET_ACCESS_KEY=your_secret
AWS_REGION=us-east-1
BEDROCK_MODEL_ID=anthropic.claude-3-5-sonnet-20240620-v1:0

# Set these to dummy values if not using storage yet
S3_BUCKET_NAME=test-bucket
MONGODB_URI=mongodb://localhost:27017
USE_OBJECT_DETECTION=false
```

**Note:** Analysis will work, but storage features will fail with this minimal config.

---

## 📞 Need Help?

1. Check the error logs when running `python main.py`
2. The startup event logs MongoDB and S3 connection status
3. Use `/api/v1/health` endpoint to verify service
4. Check `IMPLEMENTATION_SUMMARY.md` for complete docs

---

**Ready to start? Follow the Quick Setup Script above! 🚀**

