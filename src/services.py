import httpx
import os
import json
from dotenv import load_dotenv
from .models import NormalizedMessage, QueryType, ActionType, WebhookResponse

load_dotenv()

CLAUDE_API_KEY = os.getenv("CLAUDE_API_KEY")
MODEL_NAME = os.getenv("MODEL_NAME", "claude-sonnet-4-20250514")

PROPERTY_CONTEXT = """
Property: Villa B1, Assagao, North Goa
Bedrooms: 3 | Max guests: 6 | Private pool: Yes
Check-in: 2pm | Check-out: 11am
Base rate: INR 18,000 per night (up to 4 guests)
Extra guest: INR 2,000 per night per person
WiFi password: Nistula@2024
Caretaker: Available 8am to 10pm
Chef on call: Yes, pre-booking required
Availability April 20-24: Available
Cancellation: Free up to 7 days before check-in
"""

async def process_message_with_ai(normalized_msg: NormalizedMessage) -> WebhookResponse:
    prompt = f"""
You are an AI guest relations agent for Nistula, a premium villa management company.
Your goal is to handle guest messages professionally and accurately.

PROPERTY CONTEXT:
{PROPERTY_CONTEXT}

GUEST MESSAGE:
Guest Name: {normalized_msg.guest_name}
Message: {normalized_msg.message_text}
Source: {normalized_msg.source}
Booking Reference: {normalized_msg.booking_ref or "N/A"}

TASK:
1. Classify the message into one of these types: 
   - pre_sales_availability
   - pre_sales_pricing
   - post_sales_checkin
   - special_request
   - complaint
   - general_enquiry

2. Draft a polite, helpful reply based on the property context. 
   - If it's a pricing query, calculate the total if possible (Base: 18k for 4 guests, 2k per extra guest).
   - If it's a complaint, be empathetic and escalate.

3. Assign a confidence score (0.0 to 1.0) based on how certain you are of the information provided in the reply.
    - 0.9+ : Information is explicitly in the context.
    - 0.7-0.9 : Reasonable inference but needs verification.
    - 0.55-0.70 : For complaints or highly ambiguous requests.
    - <0.55 : Missing critical info or severe escalation.

RESPONSE FORMAT:
Return ONLY a JSON object with the following keys:
- query_type: string
- drafted_reply: string
- confidence_score: float

Example:
{{
  "query_type": "pre_sales_availability",
  "drafted_reply": "Hi Rahul! Villa B1 is available...",
  "confidence_score": 0.95
}}
"""

    headers = {
        "x-api-key": CLAUDE_API_KEY,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json"
    }

    data = {
        "model": MODEL_NAME,
        "max_tokens": 1024,
        "messages": [
            {"role": "user", "content": prompt}
        ]
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post("https://api.anthropic.com/v1/messages", headers=headers, json=data, timeout=30.0)
            response.raise_for_status()
            result = response.json()
            
            content = result['content'][0]['text']
            # Extract JSON from content
            try:
                ai_data = json.loads(content)
            except json.JSONDecodeError:
                import re
                json_match = re.search(r'\{.*\}', content, re.DOTALL)
                if json_match:
                    ai_data = json.loads(json_match.group())
                else:
                    raise Exception("Failed to parse AI response")
        except httpx.HTTPStatusError as e:
            # Handle API error (e.g. invalid key or quota)
            return WebhookResponse(
                message_id=normalized_msg.message_id,
                query_type=QueryType.general_enquiry,
                drafted_reply="I'm sorry, I am having trouble connecting to my brain right now. Please wait for an agent.",
                confidence_score=0.0,
                action=ActionType.escalate
            )
        except Exception as e:
            raise Exception(f"AI Processing failed: {str(e)}")

        # Determine action based on confidence and query type
        confidence = ai_data["confidence_score"]
        query_type = ai_data["query_type"]
        
        action = ActionType.agent_review
        if query_type == "complaint" or confidence < 0.60:
            action = ActionType.escalate
        elif confidence > 0.85:
            action = ActionType.auto_send
        else:
            action = ActionType.agent_review

        return WebhookResponse(
            message_id=normalized_msg.message_id,
            query_type=QueryType(query_type),
            drafted_reply=ai_data["drafted_reply"],
            confidence_score=confidence,
            action=action
        )
