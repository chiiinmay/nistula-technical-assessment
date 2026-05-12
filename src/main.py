from fastapi import FastAPI, HTTPException
from .models import InboundMessage, NormalizedMessage, WebhookResponse
from .services import process_message_with_ai
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Nistula Guest Message Handler")

@app.post("/webhook/message", response_model=WebhookResponse)
async def webhook_message(msg: InboundMessage):
    if not msg.message.strip():
        raise HTTPException(status_code=400, detail="Message text cannot be empty")
    try:
        # 1. Normalize the message
        normalized_msg = NormalizedMessage(
            source=msg.source,
            guest_name=msg.guest_name,
            message_text=msg.message,
            timestamp=msg.timestamp,
            booking_ref=msg.booking_ref,
            property_id=msg.property_id
        )
        
        logger.info(f"Received message from {normalized_msg.guest_name} via {normalized_msg.source}")
        
        # 2. Process with AI (Classification + Drafting + Confidence)
        response = await process_message_with_ai(normalized_msg)
        
        logger.info(f"Processed message {response.message_id} with action {response.action}")
        
        return response
        
    except Exception as e:
        logger.error(f"Error processing webhook: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
