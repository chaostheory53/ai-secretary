from flask import Flask, request, jsonify
import os

app = Flask(__name__)

@app.route('/webhook/evolution', methods=['POST'])
def evolution_webhook():
    data = request.json
    print(f"Received webhook data: {data}")
    # TODO: Process incoming message and send to agents
    return jsonify({"status": "received", "data": data}), 200

def run_webhook_server():
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)

if __name__ == '__main__':
    run_webhook_server()
