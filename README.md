# Lab M6.01 - Deploy Application with Logging Configuration

**Repository:** https://github.com/cloud-engineering-bootcamp/ce-lab-deploy-app-logging.git

**Activity Type:** Individual  
**Estimated Time:** 45 minutes



# Lab M6.01 - Deploy Application with Logging Configuration

## Overview

In this lab, I deployed a Flask-based web application with structured JSON logging and configured the Amazon CloudWatch Agent to collect and send logs to CloudWatch Logs.

The application generates structured logs in JSON format, which enables efficient searching, filtering, and analysis using CloudWatch Logs Insights.

---

## Architecture

* **Application:** Flask API with structured JSON logging using `structlog`
* **Logging:** Logs written to a local file (`application.log`)
* **Agent:** CloudWatch Agent collects logs and sends them to CloudWatch
* **Cloud Service:** AWS CloudWatch Logs
* **Analysis Tool:** CloudWatch Logs Insights

---

## Setup & Deployment

### 1. Launch EC2 Instance

* Ubuntu Server 22.04
* Instance type: t2.micro
* Enabled public IP
* Configured Security Group:

  * SSH (22)
  * Custom TCP (5001)

---

### 2. SSH into EC2

```bash
ssh -i ~/Downloads/ce-lab1-key.pem ubuntu@<EC2-PUBLIC-IP>
```

---

### 3. Install Dependencies

```bash
sudo apt update
sudo apt install -y python3-pip python3-venv

cd ~/app
python3 -m venv venv
source venv/bin/activate

pip install flask structlog
```

---

### 4. Application with Structured Logging

* Logs are generated in JSON format using `structlog`
* Logs are written to:

```
/home/ubuntu/app/application.log
```

Example log:

```json
{
  "event": "order_created",
  "amount": 99.99,
  "user_id": "user-123",
  "timestamp": "2026-03-28T14:16:47Z"
}
```

---

### 5. Install CloudWatch Agent

```bash
wget https://amazoncloudwatch-agent.s3.amazonaws.com/ubuntu/amd64/latest/amazon-cloudwatch-agent.deb
sudo dpkg -i -E ./amazon-cloudwatch-agent.deb
```

---

### 6. Configure IAM Role

Attached policy:

```
CloudWatchAgentServerPolicy
```

This allows:

* Create log groups
* Create log streams
* Send log events

---

### 7. Configure CloudWatch Agent

File:

```
/opt/aws/amazon-cloudwatch-agent/etc/config.json
```

```json
{
  "logs": {
    "logs_collected": {
      "files": {
        "collect_list": [
          {
            "file_path": "/home/ubuntu/app/application.log",
            "log_group_name": "/aws/application/api",
            "log_stream_name": "{instance_id}",
            "timezone": "UTC"
          }
        ]
      }
    }
  }
}
```

---

### 8. Start Agent

```bash
sudo /opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-ctl \
  -a fetch-config \
  -m ec2 \
  -s \
  -c file:/opt/aws/amazon-cloudwatch-agent/etc/config.json
```

---

### 9. Verify Logs

```bash
aws logs describe-log-groups
aws logs describe-log-streams --log-group-name /aws/application/api
aws logs tail /aws/application/api --follow
```

---

## Screenshots

* CloudWatch Log Group created (`/aws/application/api`)
* Log Streams with instance ID
* Logs Insights queries results
* Running application on EC2

---

## CloudWatch Logs Insights Queries

### Find all orders

```
fields @timestamp, @message
| filter event = "order_created"
| sort @timestamp desc
| limit 20
```

### Average order value

```
fields amount
| filter event = "order_created"
| stats avg(amount) as avg_order, count() as total_orders
```

### Count events

```
fields event
| stats count() by event
| sort count() desc
```

### Track request by correlation ID

```
fields @timestamp, event, @message
| filter correlation_id = "YOUR_ID"
| sort @timestamp asc
```

---

## Retention Policy

Set to 30 days:

```bash
aws logs put-retention-policy \
  --log-group-name /aws/application/api \
  --retention-in-days 30
```

---

## Challenges & Solutions

### Issue 1: SSH Connection Errors

* Problem: Timeout / permission denied
* Solution: Fixed Security Group and used correct key pair

### Issue 2: Python Package Installation Error (PEP 668)

* Problem: pip install blocked
* Solution: Used virtual environment (`venv`)

### Issue 3: Logs not appearing in CloudWatch

* Problem: Agent not configured correctly
* Solution: Fixed config file path and IAM role permissions

### Issue 4: Port conflict

* Problem: Port 5000 already in use
* Solution: Switched application to port 5001

---

## Reflection Questions

### 1. Why use structured logging?

Structured logging (JSON) allows easier searching, filtering, and analysis compared to plain text logs.

---

### 2. What sensitive data should not be logged?

* Passwords
* API keys
* Credit card data
* Personal identifiable information (PII)

---

### 3. How does correlation ID help?

It allows tracking a single request across multiple services and logs, making debugging much easier.

---

### 4. What retention period should be used?

Depends on requirements, but 30 days is a good balance between cost and observability.

---

### 5. How to reduce CloudWatch costs?

* Use shorter retention
* Avoid logging unnecessary data
* Use log levels (INFO, ERROR)
* Filter logs before sending

---

## Conclusion

This lab demonstrated how to implement structured logging, ship logs to CloudWatch, and analyze them using Logs Insights. This setup significantly improves observability and debugging capabilities in production systems.


## Detailed Instructions

### Part 1: Create Application with Structured Logging (15 min)

**Python Application Example:**

```python
# app/server.py
import structlog
from flask import Flask, request
import uuid
import time

# Configure structured logging
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.stdlib.add_log_level,
        structlog.processors.JSONRenderer()
    ],
    logger_factory=structlog.PrintLoggerFactory(),
)

logger = structlog.get_logger()
app = Flask(__name__)

@app.route('/')
def index():
    correlation_id = request.headers.get('X-Correlation-ID', str(uuid.uuid4()))
    
    logger.info(
        "request_received",
        correlation_id=correlation_id,
        path="/",
        method=request.method,
        ip=request.remote_addr
    )
    
    return {"message": "Hello World", "correlation_id": correlation_id}

@app.route('/health')
def health():
    logger.info("health_check", status="healthy")
    return {"status": "healthy"}

@app.route('/order', methods=['POST'])
def create_order():
    correlation_id = str(uuid.uuid4())
    data = request.get_json()
    
    logger.info(
        "order_created",
        correlation_id=correlation_id,
        order_id=f"ord-{uuid.uuid4().hex[:8]}",
        amount=data.get('amount', 0),
        items=data.get('items', 0),
        user_id=data.get('user_id')
    )
    
    return {"status": "created", "correlation_id": correlation_id}

if __name__ == '__main__':
    logger.info("application_started", port=5000)
    app.run(host='0.0.0.0', port=5000)
```

**Requirements:**
```
# requirements.txt
flask
structlog
boto3
```

**Node.js Alternative:**

```javascript
// app/server.js
const express = require('express');
const winston = require('winston');
const { v4: uuidv4 } = require('uuid');

const logger = winston.createLogger({
  format: winston.format.combine(
    winston.format.timestamp(),
    winston.format.json()
  ),
  transports: [
    new winston.transports.Console(),
    new winston.transports.File({ filename: 'application.log' })
  ]
});

const app = express();
app.use(express.json());

app.get('/', (req, res) => {
  const correlationId = req.headers['x-correlation-id'] || uuidv4();
  
  logger.info('request_received', {
    correlation_id: correlationId,
    path: '/',
    method: req.method,
    ip: req.ip
  });
  
  res.json({ message: 'Hello World', correlation_id: correlationId });
});

app.get('/health', (req, res) => {
  logger.info('health_check', { status: 'healthy' });
  res.json({ status: 'healthy' });
});

app.post('/order', (req, res) => {
  const correlationId = uuidv4();
  
  logger.info('order_created', {
    correlation_id: correlationId,
    order_id: `ord-${uuidv4().substring(0, 8)}`,
    amount: req.body.amount || 0,
    items: req.body.items || 0,
    user_id: req.body.user_id
  });
  
  res.json({ status: 'created', correlation_id: correlationId });
});

const PORT = 5000;
app.listen(PORT, () => {
  logger.info('application_started', { port: PORT });
  console.log(`Server running on port ${PORT}`);
});
```

### Part 2: Install CloudWatch Logs Agent (10 min)

**Install Agent:**
```bash
# Download
wget https://s3.amazonaws.com/amazoncloudwatch-agent/ubuntu/amd64/latest/amazon-cloudwatch-agent.deb

# Install
sudo dpkg -i -E ./amazon-cloudwatch-agent.deb

# Verify installation
/opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-ctl -a query -m ec2 -c default -s
```

**Create IAM Role:**
```bash
# Create policy
cat > cloudwatch-logs-policy.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents",
        "logs:DescribeLogStreams"
      ],
      "Resource": "arn:aws:logs:*:*:*"
    }
  ]
}
EOF

# Create policy
aws iam create-policy \
  --policy-name CloudWatchLogsPolicy \
  --policy-document file://cloudwatch-logs-policy.json

# Attach to EC2 instance role
aws iam attach-role-policy \
  --role-name YourEC2Role \
  --policy-arn arn:aws:iam::YOUR-ACCOUNT-ID:policy/CloudWatchLogsPolicy
```

### Part 3: Configure CloudWatch Agent (10 min)

**Configuration File:**
```json
{
  "logs": {
    "logs_collected": {
      "files": {
        "collect_list": [
          {
            "file_path": "/home/ubuntu/app/application.log",
            "log_group_name": "/aws/application/api",
            "log_stream_name": "{instance_id}",
            "timezone": "UTC",
            "timestamp_format": "%Y-%m-%dT%H:%M:%S"
          }
        ]
      }
    }
  }
}
```

**Save and Start Agent:**
```bash
# Save config
sudo mkdir -p /opt/aws/amazon-cloudwatch-agent/etc/
sudo nano /opt/aws/amazon-cloudwatch-agent/etc/config.json
# Paste config above

# Start agent
sudo /opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-ctl \
  -a fetch-config \
  -m ec2 \
  -s \
  -c file:/opt/aws/amazon-cloudwatch-agent/etc/config.json
```

### Part 4: Generate Logs and Verify (10 min)

**Generate Traffic:**
```bash
# Start application
python3 app/server.py

# In another terminal, generate requests
curl http://localhost:5000/
curl http://localhost:5000/health
curl -X POST http://localhost:5000/order \
  -H "Content-Type: application/json" \
  -d '{"amount": 99.99, "items": 3, "user_id": "user-123"}'

# Generate multiple requests
for i in {1..50}; do
  curl http://localhost:5000/ &
done
```

**Verify in CloudWatch:**
```bash
# List log groups
aws logs describe-log-groups

# List log streams
aws logs describe-log-streams --log-group-name /aws/application/api

# Tail logs
aws logs tail /aws/application/api --follow

# Get recent events
aws logs get-log-events \
  --log-group-name /aws/application/api \
  --log-stream-name i-your-instance-id \
  --limit 10
```

### Part 5: CloudWatch Logs Insights Queries (5 min)

**Query Examples:**

**Find all order_created events:**
```
fields @timestamp, @message
| filter event = "order_created"
| sort @timestamp desc
| limit 20
```

**Calculate average order amount:**
```
fields amount
| filter event = "order_created"
| stats avg(amount) as avg_order, count() as total_orders
```

**Count events by type:**
```
fields event
| stats count() by event
| sort count() desc
```

**Find slow requests (if you add duration):**
```
fields @timestamp, path, duration_ms
| filter duration_ms > 1000
| sort duration_ms desc
```

**Track requests by correlation ID:**
```
fields @timestamp, event, @message
| filter correlation_id = "your-correlation-id"
| sort @timestamp asc
```

### Part 6: Set Retention Policy (5 min)

```bash
# Set retention to 30 days
aws logs put-retention-policy \
  --log-group-name /aws/application/api \
  --retention-in-days 30

# Verify
aws logs describe-log-groups \
  --log-group-name-prefix /aws/application/api
```

## Reflection Questions

Answer these in your README:

1. **Why use structured logging instead of plain text?**
   - Hint: Think about search and analysis

2. **What sensitive data should never be logged?**
   - Hint: PII, credentials, payment info

3. **How does correlation ID help debugging?**
   - Hint: Track requests across services

4. **What retention period should you use?**
   - Hint: Balance compliance needs with cost

5. **How can you reduce CloudWatch Logs costs?**
   - Hint: Log levels, retention, filtering



## Troubleshooting

**Issue: Logs not appearing in CloudWatch**
- Check CloudWatch Agent status
- Verify IAM permissions
- Check log file path in config
- Look for agent errors: `/opt/aws/amazon-cloudwatch-agent/logs/`

**Issue: Permission denied**
- Ensure EC2 instance has IAM role
- Verify role has CloudWatch Logs permissions
- Check log file permissions

**Issue: Structured logs not parsing**
- Ensure JSON is valid
- Check timestamp format
- Verify log format in agent config

## Resources

- [CloudWatch Logs Agent](https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/CWL_GettingStarted.html)
- [Structured Logging Best Practices](https://www.thoughtworks.com/insights/blog/structured-logging)
- [CloudWatch Logs Insights Query Syntax](https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/CWL_QuerySyntax.html)
- [Python structlog Documentation](https://www.structlog.org/)

---

**Great work on instrumenting your application!** 🎉
