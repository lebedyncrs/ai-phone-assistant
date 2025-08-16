import os
from twilio.rest import Client
from dotenv import load_dotenv
from twilio.rest.api.v2010.account.call import CallInstance
from typing import List, Dict, Any

load_dotenv()

account_sid = os.environ["TWILIO_ACCOUNT_SID"]
auth_token = os.environ["TWILIO_AUTH_TOKEN"]


def get_latest_call() -> Dict[str, Any]:
    client = Client(account_sid, auth_token)

    calls: List[CallInstance] = client.calls.list(limit=10)
    if not calls:
        return {"error": "No calls found"}
    
    latest_call = calls[0]
    
    phone = latest_call.from_formatted[:12]
    formatted_from = f"{phone[:3]} {phone[3:6]} {phone[6:9]} {phone[9:12]}" 
       
    call_data = {
        "sid": latest_call.sid,
        "status": latest_call.status,
        "direction": latest_call.direction,
        "from": latest_call._from,
        "from_formatted": formatted_from,
        "to": latest_call.to,
        "duration": latest_call.duration,
        "start_time": str(latest_call.start_time) if latest_call.start_time else None,
        "end_time": str(latest_call.end_time) if latest_call.end_time else None,
        "price": str(latest_call.price) if latest_call.price else None,
    }
    
    return call_data
