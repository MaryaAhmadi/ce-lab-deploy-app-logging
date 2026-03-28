import structlog
import logging
from flask import Flask, request
import uuid

# تنظیم logging برای فایل
logging.basicConfig(
    filename='application.log',
    level=logging.INFO,
    format="%(message)s"
)

structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.stdlib.add_log_level,
        structlog.processors.JSONRenderer()
    ],
    logger_factory=structlog.stdlib.LoggerFactory(),
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
    logger.info("application_started", port=5001)
    app.run(host='0.0.0.0', port=5001)
