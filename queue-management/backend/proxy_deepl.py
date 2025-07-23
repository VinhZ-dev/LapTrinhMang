from flask import Flask, request, jsonify
import requests
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

DEEPL_API_KEY = "df4385c2-33de-e423-4134-ca1f7b3ea8b7"

@app.route('/deepl-translate', methods=['POST'])
def deepl_translate():
    text = request.json.get('text')
    target_lang = request.json.get('target_lang', 'EN')
    if not text:
        return jsonify({'error': 'No text provided'}), 400
    res = requests.post(
        "https://api-free.deepl.com/v2/translate",
        data={
            "auth_key": DEEPL_API_KEY,
            "text": text,
            "target_lang": target_lang
        }
    )
    return jsonify(res.json()), res.status_code

if __name__ == '__main__':
    app.run(port=5001) 