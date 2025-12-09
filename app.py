from flask import Flask, request, jsonify
import json
import urllib.request
import base64
import re

app = Flask(__name__)

# CORS headers
@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
    response.headers.add('Access-Control-Allow-Methods', 'GET, OPTIONS')
    return response

@app.route('/')
def index():
    return jsonify({
        "service": "Yargı API",
        "endpoints": ["/search", "/document"],
        "source": "Bedesten API (Adalet Bakanlığı)"
    })

@app.route('/search')
def search():
    keyword = request.args.get('keyword', '')
    court = request.args.get('court', 'YARGITAYKARARI')
    page = int(request.args.get('page', 1))
    
    if not keyword:
        return jsonify({"error": "keyword parameter required"}), 400
    
    url = "https://bedesten.adalet.gov.tr/emsal-karar/searchDocuments"
    data = {
        "data": {
            "pageSize": 10,
            "pageNumber": page,
            "itemTypeList": [court],
            "phrase": keyword,
            "sortFields": ["KARAR_TARIHI"],
            "sortDirection": "desc"
        },
        "applicationName": "UyapMevzuat",
        "paging": True
    }
    
    req = urllib.request.Request(
        url,
        data=json.dumps(data).encode('utf-8'),
        headers={
            'Content-Type': 'application/json',
            'AdaletApplicationName': 'UyapMevzuat',
            'Origin': 'https://mevzuat.adalet.gov.tr',
            'Referer': 'https://mevzuat.adalet.gov.tr/'
        }
    )
    
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            result = json.loads(response.read().decode())
            decisions = [
                {
                    "id": d.get('documentId'),
                    "daire": d.get('birimAdi'),
                    "esasNo": d.get('esasNo'),
                    "kararNo": d.get('kararNo'),
                    "tarih": d.get('kararTarihiStr')
                }
                for d in result.get('data', {}).get('emsalKararList', [])
            ]
            return jsonify({
                "success": True, 
                "total": result.get('data', {}).get('total', 0), 
                "decisions": decisions
            })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route('/document')
def document():
    doc_id = request.args.get('id', '')
    
    if not doc_id:
        return jsonify({"error": "id parameter required"}), 400
    
    url = "https://bedesten.adalet.gov.tr/emsal-karar/getDocumentContent"
    data = {"data": {"documentId": doc_id}, "applicationName": "UyapMevzuat"}
    
    req = urllib.request.Request(
        url,
        data=json.dumps(data).encode('utf-8'),
        headers={
            'Content-Type': 'application/json',
            'AdaletApplicationName': 'UyapMevzuat',
            'Origin': 'https://mevzuat.adalet.gov.tr',
            'Referer': 'https://mevzuat.adalet.gov.tr/'
        }
    )
    
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            result = json.loads(response.read().decode())
            content_b64 = result.get('data', {}).get('content', '')
            content = base64.b64decode(content_b64).decode('utf-8', errors='ignore')
            text = re.sub(r'<[^>]+>', ' ', content)
            text = re.sub(r'\s+', ' ', text).strip()
            return jsonify({"success": True, "content": text[:8000]})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

if __name__ == '__main__':
    app.run(debug=True)
