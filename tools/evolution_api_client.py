import requests

class EvolutionAPIClient:
    def __init__(self, base_url: str, instance_key: str):
        self.base_url = base_url
        self.instance_key = instance_key

    def send_message(self, to_number: str, message_text: str):
        url = f"{self.base_url}/message/sendText/{self.instance_key}"
        headers = {'Content-Type': 'application/json'}
        payload = {
            'number': to_number,
            'textMessage': {
                'text': message_text
            }
        }
        try:
            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status() # Raise an HTTPError for bad responses (4xx or 5xx)
            print(f"Message sent successfully to {to_number}: {message_text}")
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error sending message to {to_number}: {e}")
            return None
