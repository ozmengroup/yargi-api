from http.server import BaseHTTPRequestHandler
import json
import urllib.request
import urllib.parse
import base64
import re

class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(parsed.query)
        doc_id = params.get('id', [''])[0]
        
        if not doc_id:
            self._send_json(400, {"error": "id parameter required"})
            return
        
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
                # HTML to plain text
                text = re.sub(r'<[^>]+>', ' ', content)
                text = re.sub(r'\s+', ' ', text).strip()
                output = {"success": True, "content": text[:8000]}
        except Exception as e:
            output = {"success": False, "error": str(e)}
        
        self._send_json(200, output)
    
    def _send_json(self, code, data):
        self.send_response(code)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode('utf-8'))
