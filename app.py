from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import base64
import re

app = Flask(__name__)
CORS(app)  # Tüm originlere izin ver

BEDESTEN_URL = "https://bedesten.adalet.gov.tr/emsal-karar"
HEADERS = {
    'Content-Type': 'application/json',
    'AdaletApplicationName': 'UyapMevzuat',
    'Origin': 'https://mevzuat.adalet.gov.tr',
    'Referer': 'https://mevzuat.adalet.gov.tr/'
}

COURT_TYPES = {
    "yargitay": "YARGITAYKARARI",
    "danistay": "DANISTAYKARAR",
    "yerel": "YERELHUKUK",
    "istinaf": "ISTINAFHUKUK",
    "kyb": "KYB"
}

@app.route('/')
def home():
    return jsonify({
        "service": "Yargı API",
        "endpoints": {
            "/search": "GET ?q=arama&court=yargitay&page=1",
            "/document": "GET ?id=documentId"
        },
        "courts": list(COURT_TYPES.keys()),
        "source": "Bedesten API (Adalet Bakanlığı)"
    })

@app.route('/search')
def search():
    q = request.args.get('q', '')
    court = request.args.get('court', 'yargitay').lower()
    page = int(request.args.get('page', 1))
    size = int(request.args.get('size', 10))
    
    if not q:
        return jsonify({"success": False, "error": "q parameter required"}), 400
    
    court_type = COURT_TYPES.get(court, "YARGITAYKARARI")
    
    payload = {
        "data": {
            "pageSize": min(size, 20),
            "pageNumber": page,
            "itemTypeList": [court_type],
            "phrase": q,
            "sortFields": ["KARAR_TARIHI"],
            "sortDirection": "desc"
        },
        "applicationName": "UyapMevzuat",
        "paging": True
    }
    
    try:
        resp = requests.post(f"{BEDESTEN_URL}/searchDocuments", json=payload, headers=HEADERS, timeout=30)
        data = resp.json()
        
        decisions = []
        for d in data.get('data', {}).get('emsalKararList', []):
            decisions.append({
                "id": d.get('documentId'),
                "daire": d.get('birimAdi'),
                "esasNo": d.get('esasNo'),
                "kararNo": d.get('kararNo'),
                "tarih": d.get('kararTarihiStr'),
                "ozet": (d.get('documentSummary') or '')[:200]
            })
        
        return jsonify({
            "success": True,
            "total": data.get('data', {}).get('total', 0),
            "page": page,
            "decisions": decisions
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/document')
def document():
    doc_id = request.args.get('id', '')
    
    if not doc_id:
        return jsonify({"success": False, "error": "id parameter required"}), 400
    
    payload = {
        "data": {"documentId": doc_id},
        "applicationName": "UyapMevzuat"
    }
    
    try:
        resp = requests.post(f"{BEDESTEN_URL}/getDocumentContent", json=payload, headers=HEADERS, timeout=30)
        data = resp.json()
        
        content_b64 = data.get('data', {}).get('content', '')
        content = base64.b64decode(content_b64).decode('utf-8', errors='ignore')
        
        # HTML to plain text
        text = re.sub(r'<[^>]+>', ' ', content)
        text = re.sub(r'\s+', ' ', text).strip()
        
        return jsonify({
            "success": True,
            "id": doc_id,
            "content": text[:10000]
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/health')
def health():
    return jsonify({"status": "ok"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
