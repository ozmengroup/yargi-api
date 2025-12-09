from flask import Flask, request, jsonify
import json
import urllib.request
import ssl
import base64
import re
from bs4 import BeautifulSoup

app = Flask(__name__)

# SSL context for APIs that need it
ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE

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
        "service": "Yargı API v2.0",
        "endpoints": [
            "/search - Yargıtay kararları ara",
            "/document - Karar içeriği getir",
            "/danistay - Danıştay kararları ara",
            "/danistay/document - Danıştay karar içeriği",
            "/mevzuat - Kanun/mevzuat ara",
            "/mevzuat/madde - Kanun maddesi içeriği",
            "/aym - Anayasa Mahkemesi kararları ara"
        ],
        "sources": [
            "Bedesten API (Yargıtay)",
            "karararama.danistay.gov.tr (Danıştay)",
            "mevzuat.gov.tr (Mevzuat)",
            "normkararlarbilgibankasi.anayasa.gov.tr (AYM)"
        ]
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

# ==================== DANIŞTAY API ====================
@app.route('/danistay')
def danistay_search():
    """Danıştay kararları arama"""
    keyword = request.args.get('keyword', '')
    page = int(request.args.get('page', 1))

    if not keyword:
        return jsonify({"error": "keyword parameter required"}), 400

    url = "https://karararama.danistay.gov.tr/aramalist"
    data = {
        "data": {
            "andKelimeler": [f'"{keyword}"'],
            "orKelimeler": [],
            "notAndKelimeler": [],
            "notOrKelimeler": [],
            "pageSize": 10,
            "pageNumber": page
        }
    }

    req = urllib.request.Request(
        url,
        data=json.dumps(data).encode('utf-8'),
        headers={
            'Content-Type': 'application/json; charset=UTF-8',
            'Accept': 'application/json, text/plain, */*',
            'X-Requested-With': 'XMLHttpRequest'
        }
    )

    try:
        with urllib.request.urlopen(req, timeout=30, context=ssl_context) as response:
            result = json.loads(response.read().decode())

            decisions = []
            if result.get('data') and result['data'].get('data'):
                for d in result['data']['data']:
                    decisions.append({
                        "id": d.get('id'),
                        "daire": d.get('dpiDaire'),
                        "esasNo": d.get('esasNo'),
                        "kararNo": d.get('kararNo'),
                        "tarih": d.get('kararTarihi'),
                        "konu": d.get('konu', '')[:200] if d.get('konu') else ''
                    })

            total = result.get('data', {}).get('recordsTotal', 0)
            return jsonify({
                "success": True,
                "total": total,
                "decisions": decisions,
                "source": "Danıştay"
            })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route('/danistay/document')
def danistay_document():
    """Danıştay karar içeriği getir"""
    doc_id = request.args.get('id', '')

    if not doc_id:
        return jsonify({"error": "id parameter required"}), 400

    url = f"https://karararama.danistay.gov.tr/getDokuman?id={doc_id}&arananKelime="

    req = urllib.request.Request(
        url,
        headers={
            'Accept': 'text/html,application/xhtml+xml',
            'User-Agent': 'Mozilla/5.0'
        }
    )

    try:
        with urllib.request.urlopen(req, timeout=30, context=ssl_context) as response:
            html_content = response.read().decode('utf-8', errors='ignore')

            # HTML'den metin çıkar
            soup = BeautifulSoup(html_content, 'lxml')
            # Script ve style etiketlerini kaldır
            for tag in soup(['script', 'style']):
                tag.decompose()

            text = soup.get_text(separator='\n', strip=True)
            # Fazla boşlukları temizle
            text = re.sub(r'\n\s*\n', '\n\n', text)

            return jsonify({"success": True, "content": text[:10000]})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

# ==================== MEVZUAT API ====================
# Sık kullanılan kanunların numaraları
KANUN_NUMARALARI = {
    "TCK": "5237",      # Türk Ceza Kanunu
    "CMK": "5271",      # Ceza Muhakemesi Kanunu
    "TMK": "4721",      # Türk Medeni Kanunu
    "TBK": "6098",      # Türk Borçlar Kanunu
    "HMK": "6100",      # Hukuk Muhakemeleri Kanunu
    "İİK": "2004",      # İcra ve İflas Kanunu
    "IIK": "2004",      # İcra ve İflas Kanunu (alternatif)
    "TTK": "6102",      # Türk Ticaret Kanunu
    "İK": "4857",       # İş Kanunu
    "IK": "4857",       # İş Kanunu (alternatif)
    "ANAYASA": "2709",  # Anayasa
    "VUK": "213",       # Vergi Usul Kanunu
    "KVK": "5520",      # Kurumlar Vergisi Kanunu
    "GVK": "193",       # Gelir Vergisi Kanunu
    "KVKK": "6698",     # Kişisel Verilerin Korunması Kanunu
    "SGK": "5510",      # Sosyal Sigortalar ve Genel Sağlık Sigortası Kanunu
}

@app.route('/mevzuat')
def mevzuat_search():
    """Mevzuat arama - kanun adı veya numarası ile"""
    query = request.args.get('query', '').strip().upper()
    kanun_no = request.args.get('no', '')

    # Kısaltma kontrolü
    if query in KANUN_NUMARALARI:
        kanun_no = KANUN_NUMARALARI[query]

    if not kanun_no and not query:
        return jsonify({"error": "query veya no parameter required"}), 400

    # Mevzuat.gov.tr iframe URL'i ile içerik çek
    if kanun_no:
        # Doğrudan kanun numarası ile
        iframe_url = f"https://www.mevzuat.gov.tr/anasayfa/MevzuatFihristDetayIframe?MevzuatTur=1&MevzuatNo={kanun_no}&MevzuatTertip=5"

        req = urllib.request.Request(
            iframe_url,
            headers={
                'Accept': 'text/html',
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
            }
        )

        try:
            with urllib.request.urlopen(req, timeout=30) as response:
                html = response.read().decode('utf-8', errors='ignore')
                soup = BeautifulSoup(html, 'lxml')

                # Kanun başlığını bul
                title = ""
                title_tag = soup.find('div', class_='mevzuatBaslik') or soup.find('h1')
                if title_tag:
                    title = title_tag.get_text(strip=True)

                # Maddeleri çıkar
                maddeler = []
                madde_divs = soup.find_all('div', class_='madde') or soup.find_all(text=re.compile(r'MADDE \d+'))

                for i, madde in enumerate(madde_divs[:50]):  # İlk 50 madde
                    if hasattr(madde, 'get_text'):
                        text = madde.get_text(strip=True)
                    else:
                        text = str(madde)[:500]

                    madde_no_match = re.search(r'MADDE\s*(\d+)', text, re.IGNORECASE)
                    madde_no = madde_no_match.group(1) if madde_no_match else str(i+1)

                    maddeler.append({
                        "no": madde_no,
                        "text": text[:1000]
                    })

                return jsonify({
                    "success": True,
                    "kanun_no": kanun_no,
                    "title": title,
                    "madde_sayisi": len(maddeler),
                    "maddeler": maddeler,
                    "source": "mevzuat.gov.tr"
                })
        except Exception as e:
            return jsonify({"success": False, "error": str(e)})

    return jsonify({"success": False, "error": "Kanun numarası bulunamadı"})

@app.route('/mevzuat/madde')
def mevzuat_madde():
    """Belirli bir kanun maddesinin tam metnini getir"""
    kanun = request.args.get('kanun', '').strip().upper()
    madde_no = request.args.get('madde', '')

    # Kısaltmayı numaraya çevir
    kanun_no = KANUN_NUMARALARI.get(kanun, kanun)

    if not kanun_no or not madde_no:
        return jsonify({"error": "kanun ve madde parametreleri gerekli"}), 400

    # Mevzuat.gov.tr'den madde içeriğini çek
    iframe_url = f"https://www.mevzuat.gov.tr/anasayfa/MevzuatFihristDetayIframe?MevzuatTur=1&MevzuatNo={kanun_no}&MevzuatTertip=5"

    req = urllib.request.Request(
        iframe_url,
        headers={
            'Accept': 'text/html',
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        }
    )

    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            html = response.read().decode('utf-8', errors='ignore')
            soup = BeautifulSoup(html, 'lxml')

            # Tüm metni al ve maddeyi bul
            full_text = soup.get_text()

            # Madde başlangıç ve bitiş noktalarını bul
            pattern = rf'MADDE\s*{madde_no}\s*[-–]'
            match = re.search(pattern, full_text, re.IGNORECASE)

            if match:
                start = match.start()
                # Sonraki maddeyi bul
                next_pattern = rf'MADDE\s*{int(madde_no)+1}\s*[-–]'
                next_match = re.search(next_pattern, full_text[start+10:], re.IGNORECASE)

                if next_match:
                    end = start + 10 + next_match.start()
                else:
                    end = start + 3000  # Sonraki madde yoksa 3000 karakter al

                madde_text = full_text[start:end].strip()
                # Temizle
                madde_text = re.sub(r'\s+', ' ', madde_text)

                return jsonify({
                    "success": True,
                    "kanun": kanun,
                    "kanun_no": kanun_no,
                    "madde": madde_no,
                    "content": madde_text,
                    "source": "mevzuat.gov.tr"
                })
            else:
                return jsonify({"success": False, "error": f"Madde {madde_no} bulunamadı"})

    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

# ==================== ANAYASA MAHKEMESİ API ====================
@app.route('/aym')
def aym_search():
    """Anayasa Mahkemesi norm denetimi kararları arama"""
    keyword = request.args.get('keyword', '')

    if not keyword:
        return jsonify({"error": "keyword parameter required"}), 400

    # AYM arama URL'i
    base_url = "https://normkararlarbilgibankasi.anayasa.gov.tr/Ara"
    params = f"?KelimeAra[]={urllib.parse.quote(keyword)}"

    req = urllib.request.Request(
        base_url + params,
        headers={
            'Accept': 'text/html,application/xhtml+xml',
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'Accept-Language': 'tr-TR,tr;q=0.9'
        }
    )

    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            html = response.read().decode('utf-8', errors='ignore')
            soup = BeautifulSoup(html, 'lxml')

            decisions = []

            # Karar sayısını bul
            total = 0
            bulunan_div = soup.find('div', class_='bulunankararsayisi')
            if bulunan_div:
                match = re.search(r'(\d+)\s*Karar', bulunan_div.get_text())
                if match:
                    total = int(match.group(1))

            # Kararları çıkar
            karar_divs = soup.find_all('div', class_='birkarar')

            for karar in karar_divs[:10]:  # İlk 10 karar
                # Başlık ve E.K. numarası
                baslik = karar.find('div', class_='bkararbaslik')
                ek_no = ""
                if baslik:
                    ek_match = re.search(r'E\.\s*\d+/\d+\s*,\s*K\.\s*\d+/\d+', baslik.get_text())
                    if ek_match:
                        ek_no = ek_match.group(0)

                # Karar bilgileri
                bilgi_div = karar.find('div', class_='kararbilgileri')
                tarih = ""
                sonuc = ""
                if bilgi_div:
                    parts = bilgi_div.get_text(separator='|').split('|')
                    if len(parts) > 2:
                        sonuc = parts[2].strip() if len(parts) > 2 else ""
                    if len(parts) > 3:
                        tarih = parts[3].replace('Karar Tarihi:', '').strip()

                # Link
                link_tag = karar.find('a', href=True)
                doc_url = ""
                if link_tag:
                    doc_url = "https://normkararlarbilgibankasi.anayasa.gov.tr" + link_tag['href']

                decisions.append({
                    "esas_karar_no": ek_no,
                    "tarih": tarih,
                    "sonuc": sonuc,
                    "url": doc_url
                })

            return jsonify({
                "success": True,
                "total": total,
                "decisions": decisions,
                "source": "Anayasa Mahkemesi"
            })

    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

import urllib.parse

if __name__ == '__main__':
    app.run(debug=True)
