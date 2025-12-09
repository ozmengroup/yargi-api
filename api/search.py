from http.server import BaseHTTPRequestHandler
import json
import urllib.request
import urllib.parse

class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(parsed.query)
        keyword = params.get('keyword', [''])[0]
        court = params.get('court', ['YARGITAYKARARI'])[0]
        page = int(params.get('page', ['1'])[0])
        
        if not keyword:
            self._send_json(400, {"error": "keyword required"})
            return
        
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
                output = {"success": True, "total": result.get('data', {}).get('total', 0), "decisions": decisions}
        except Exception as e:
            output = {"success": False, "error": str(e)}
        
        self._send_json(200, output)
    
    def _send_json(self, code, data):
        self.send_response(code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode('utf-8'))
