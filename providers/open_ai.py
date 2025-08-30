import os
from openai import OpenAI
import json

PROMPT = """
You are given:
1. A transcription of a restaurant ordering conversation between a client and an AI agent.
2. A menu in JSON with product IDs, variant IDs, and addon IDs.

Your task:
- Identify what the customer ordered.
- Match each ordered item with the corresponding product_id, variant_id, addon_id and category_id from the menu.
- Return ONLY valid JSON in the following format (without explanation or extra text):

{
  "customer_name": "Customer name from conversation",
  "products": [
    {
      "product_id": "product_id",
      "variant_id": "variant_id",
      "category_id": "category_id",
      "amount_ordered": 1,
      "final_price": 10,
      "addons": ["addon_id"],
      "name": "Product name"
    }
  ]
}

Rules:
- Include all ordered products (main items, sides, drinks).
- Use the exact IDs from the menu.
- If a product has no addons, return an empty list [].
- If a product has no variant, return null for variant_id.
- Do not add extra text, comments, or explanations outside of the JSON.
"""



def get_client():
    return OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

def match_ordered_products(menu: str, conversation: str):
    client = get_client()
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system", 
                "content": f"""{PROMPT}
                Menu: {menu}
                """
            },
            {"role": "user", "content": conversation}
        ],
    )
    return json.loads(response.choices[0].message.content)

