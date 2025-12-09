import React, { useState, useEffect } from 'react';

// RENDER API - Gerçek Yargıtay verileri
const API_BASE = 'https://yargi-api.onrender.com';

const hesaplaCeza = (temel, indirimler) => {
  let s = temel;
  indirimler.forEach(i => { if (i.aktif) s *= (1 - i.oran); });
  return Math.round(s * 10) / 10;
};

const hesaplaFaiz = (ana, oran, gun) => Math.round(ana * (oran / 100) * (gun / 365));

export default function App() {
  const [tab, setTab] = useState('arama');
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState(null);
  const [selectedDoc, setSelectedDoc] = useState(null);
  const [docContent, setDocContent] = useState(null);
  const [loading, setLoading] = useState(false);
  const [apiStatus, setApiStatus] = useState('checking');
  
  const [cezaAy, setCezaAy] = useState(24);
  const [indirimler, setIndirimler] = useState([
    { id: 'tahrik', ad: 'Haksız Tahrik', oran: 0.25, aktif: false },
    { id: 'iyihal', ad: 'İyi Hal (TCK 62)', oran: 0.166, aktif: false },
    { id: 'etkin', ad: 'Etkin Pişmanlık', oran: 0.5, aktif: false },
    { id: 'yas', ad: 'Yaş Küçüklüğü', oran: 0.333, aktif: false },
  ]);
  const [faiz, setFaiz] = useState({ ana: 100000, oran: 24, gun: 180 });

  // API durumunu kontrol et
  useEffect(() => {
    const checkApi = async () => {
      try {
        const res = await fetch(API_BASE, { mode: 'cors' });
        if (res.ok) setApiStatus('live');
        else setApiStatus('offline');
      } catch (e) {
        setApiStatus('offline');
      }
    };
    checkApi();
  }, []);

  // Yargıtay'da ara
  const searchYargitay = async () => {
    if (!searchQuery.trim()) return;
    setLoading(true);
    setSearchResults(null);
    setSelectedDoc(null);
    setDocContent(null);
    
    try {
      const encoded = encodeURIComponent(searchQuery);
      const res = await fetch(`${API_BASE}/search?keyword=${encoded}`, { mode: 'cors' });
      const data = await res.json();
      setSearchResults(data);
      setApiStatus('live');
    } catch (e) {
      setSearchResults({ success: false, error: 'API bağlantı hatası. Render uyandırılıyor (30-50sn bekleyin)...' });
    }
    setLoading(false);
  };

  // Karar metnini getir
  const loadDocument = async (docId) => {
    setSelectedDoc(docId);
    setDocContent({ loading: true });
    try {
      const res = await fetch(`${API_BASE}/document?id=${docId}`, { mode: 'cors' });
      const data = await res.json();
      setDocContent(data);
    } catch (e) {
      setDocContent({ success: false, error: 'Belge yüklenemedi' });
    }
  };

  const t = {
    bg: '#FAFAF8', card: '#FFF', cardAlt: '#F7F7F5', border: '#E8E8E6',
    text: '#1A1A1A', muted: '#777', light: '#AAA',
    primary: '#5B7C6F', primaryBg: '#EDF3EE',
    accent: '#B8956B', accentBg: '#F9F5E8',
    blue: '#5B7C99', blueBg: '#EDF1F7',
    red: '#C45B5B', redBg: '#FDEEEE'
  };

  return (
    <div style={{ minHeight: '100vh', background: t.bg, color: t.text, fontFamily: 'Inter, system-ui, sans-serif', padding: 16, maxWidth: 760, margin: '0 auto' }}>
      
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 20 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <div style={{ width: 38, height: 38, borderRadius: 10, background: t.primaryBg, display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 20 }}>⚖️</div>
          <div>
            <h1 style={{ margin: 0, fontSize: 17, fontWeight: 600 }}>Hukuk Asistanı</h1>
            <p style={{ margin: 0, fontSize: 11, color: t.light }}>Yargıtay Karar Arama</p>
          </div>
        </div>
        <div style={{ 
          background: apiStatus === 'live' ? t.primaryBg : apiStatus === 'offline' ? t.accentBg : t.accentBg,
          color: apiStatus === 'live' ? t.primary : t.accent,
          padding: '5px 12px', borderRadius: 12, fontSize: 10, fontWeight: 600 
        }}>
          {apiStatus === 'live' ? '● CANLI' : '● BEKLIYOR'}
        </div>
      </div>

      {apiStatus === 'offline' && (
        <div style={{ background: t.accentBg, borderRadius: 10, padding: 12, marginBottom: 16, fontSize: 11 }}>
          ⏳ <strong>Free Tier:</strong> İlk istek 30-50sn sürebilir. Arama yapınca uyanır!
        </div>
      )}

      {/* Tabs */}
      <div style={{ display: 'flex', gap: 2, marginBottom: 16, background: t.cardAlt, padding: 4, borderRadius: 12 }}>
        {[{ id: 'arama', label: '🔍 Karar Ara' }, { id: 'ceza', label: '⚖️ Ceza' }, { id: 'faiz', label: '💰 Faiz' }].map(item => (
          <button key={item.id} onClick={() => setTab(item.id)} style={{
            flex: 1, padding: 11, borderRadius: 9, border: 'none',
            background: tab === item.id ? t.card : 'transparent',
            color: tab === item.id ? t.text : t.muted,
            fontSize: 12, fontWeight: 500, cursor: 'pointer',
            boxShadow: tab === item.id ? '0 1px 3px rgba(0,0,0,0.06)' : 'none'
          }}>{item.label}</button>
        ))}
      </div>

      {/* ARAMA TAB */}
      {tab === 'arama' && (
        <div>
          <div style={{ background: t.card, borderRadius: 14, padding: 18, marginBottom: 14, border: `1px solid ${t.border}` }}>
            <div style={{ display: 'flex', gap: 10 }}>
              <input value={searchQuery} onChange={e => setSearchQuery(e.target.value)} onKeyDown={e => e.key === 'Enter' && searchYargitay()}
                placeholder="Anahtar kelime girin..." style={{ flex: 1, padding: 14, background: t.cardAlt, border: `1px solid ${t.border}`, borderRadius: 10, fontSize: 14, outline: 'none' }} />
              <button onClick={searchYargitay} disabled={loading} style={{
                padding: '14px 24px', borderRadius: 10, border: 'none', background: loading ? t.cardAlt : t.primary, color: loading ? t.muted : '#fff', fontSize: 14, fontWeight: 500, cursor: 'pointer'
              }}>{loading ? '⏳' : 'Ara'}</button>
            </div>
            <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginTop: 12 }}>
              {['TCK 141', 'TCK 86', 'trafik kazasi', 'icra itiraz', 'bosanma'].map(ex => (
                <button key={ex} onClick={() => setSearchQuery(ex)} style={{ padding: '6px 12px', borderRadius: 8, border: `1px solid ${t.border}`, background: t.card, color: t.muted, fontSize: 11, cursor: 'pointer' }}>{ex}</button>
              ))}
            </div>
          </div>

          {loading && (
            <div style={{ background: t.card, borderRadius: 14, padding: 40, textAlign: 'center', border: `1px solid ${t.border}` }}>
              <div style={{ fontSize: 32 }}>⏳</div>
              <div style={{ color: t.text, fontSize: 14, marginTop: 12 }}>Yargıtay aranıyor...</div>
            </div>
          )}

          {searchResults && !loading && (
            <div style={{ background: t.card, borderRadius: 14, padding: 18, border: `1px solid ${searchResults.success ? t.blue : t.red}` }}>
              {searchResults.success ? (
                <>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 14 }}>
                    <span style={{ fontSize: 11, color: t.blue, fontWeight: 600 }}>📚 SONUÇLAR</span>
                    <span style={{ fontSize: 12, color: t.muted }}>{searchResults.total?.toLocaleString('tr-TR')} karar</span>
                  </div>
                  {searchResults.decisions?.map((d, i) => (
                    <div key={i} onClick={() => loadDocument(d.id)} style={{ 
                      padding: 14, background: selectedDoc === d.id ? t.blueBg : t.cardAlt, borderRadius: 10, marginBottom: 8, cursor: 'pointer',
                      border: selectedDoc === d.id ? `2px solid ${t.blue}` : '2px solid transparent'
                    }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                        <span style={{ fontSize: 13, fontWeight: 600, color: t.blue }}>{d.daire}</span>
                        <span style={{ fontSize: 11, color: t.muted }}>{d.tarih}</span>
                      </div>
                      <div style={{ fontSize: 12, marginTop: 6 }}>E: {d.esasNo} • K: {d.kararNo}</div>
                    </div>
                  ))}
                </>
              ) : (
                <div style={{ textAlign: 'center', padding: 20, color: t.red }}>{searchResults.error}</div>
              )}
            </div>
          )}

          {docContent && (
            <div style={{ background: t.card, borderRadius: 14, padding: 18, marginTop: 14, border: `1px solid ${t.primary}` }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 12 }}>
                <span style={{ fontSize: 11, color: t.primary, fontWeight: 600 }}>📄 KARAR METNİ</span>
                <button onClick={() => setDocContent(null)} style={{ background: 'none', border: 'none', cursor: 'pointer' }}>✕</button>
              </div>
              {docContent.loading ? <div style={{ textAlign: 'center', padding: 20 }}>Yükleniyor...</div> :
               docContent.success ? <pre style={{ fontSize: 12, lineHeight: 1.7, whiteSpace: 'pre-wrap', background: t.cardAlt, padding: 16, borderRadius: 10, maxHeight: 400, overflow: 'auto', margin: 0 }}>{docContent.content}</pre> :
               <div style={{ color: t.red }}>{docContent.error}</div>}
            </div>
          )}
        </div>
      )}

      {/* CEZA TAB */}
      {tab === 'ceza' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
          <div style={{ background: t.card, borderRadius: 14, padding: 18, border: `1px solid ${t.border}` }}>
            <div style={{ fontSize: 10, color: t.muted, fontWeight: 600, marginBottom: 14 }}>TEMEL CEZA (AY)</div>
            <input type="range" min="1" max="240" value={cezaAy} onChange={e => setCezaAy(+e.target.value)} style={{ width: '100%', accentColor: t.primary }} />
            <div style={{ textAlign: 'center', marginTop: 12 }}>
              <span style={{ fontSize: 32, fontWeight: 600, color: t.primary }}>{cezaAy}</span>
              <span style={{ fontSize: 14, color: t.muted, marginLeft: 8 }}>ay</span>
            </div>
          </div>
          <div style={{ background: t.card, borderRadius: 14, padding: 18, border: `1px solid ${t.border}` }}>
            <div style={{ fontSize: 10, color: t.muted, fontWeight: 600, marginBottom: 14 }}>İNDİRİMLER</div>
            {indirimler.map(i => (
              <div key={i.id} onClick={() => setIndirimler(prev => prev.map(x => x.id === i.id ? {...x, aktif: !x.aktif} : x))} style={{
                display: 'flex', justifyContent: 'space-between', padding: 12, background: i.aktif ? t.primaryBg : t.cardAlt, borderRadius: 10, marginBottom: 8, cursor: 'pointer'
              }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                  <div style={{ width: 20, height: 20, borderRadius: 5, border: i.aktif ? 'none' : `2px solid ${t.border}`, background: i.aktif ? t.primary : 'transparent', color: '#fff', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>{i.aktif && '✓'}</div>
                  <span>{i.ad}</span>
                </div>
                <span style={{ color: t.primary, fontWeight: 600 }}>-{(i.oran*100).toFixed(0)}%</span>
              </div>
            ))}
          </div>
          <div style={{ background: t.primaryBg, borderRadius: 14, padding: 24, textAlign: 'center' }}>
            <div style={{ fontSize: 42, fontWeight: 600, color: t.primary }}>{hesaplaCeza(cezaAy, indirimler).toFixed(1)} ay</div>
            {hesaplaCeza(cezaAy, indirimler) <= 24 && <div style={{ marginTop: 12, padding: '8px 18px', background: t.card, borderRadius: 20, display: 'inline-block', fontSize: 12, color: t.primary }}>✓ HAGB Uygulanabilir</div>}
          </div>
        </div>
      )}

      {/* FAİZ TAB */}
      {tab === 'faiz' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
          <div style={{ background: t.card, borderRadius: 14, padding: 18, border: `1px solid ${t.border}` }}>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3,1fr)', gap: 14 }}>
              {[['Anapara (₺)', 'ana'], ['Faiz (%)', 'oran'], ['Gün', 'gun']].map(([l, k]) => (
                <div key={k}>
                  <label style={{ fontSize: 10, color: t.muted, fontWeight: 600 }}>{l}</label>
                  <input type="number" value={faiz[k]} onChange={e => setFaiz({...faiz, [k]: +e.target.value})} style={{ width: '100%', padding: 14, marginTop: 6, background: t.cardAlt, border: `1px solid ${t.border}`, borderRadius: 10, fontSize: 15, outline: 'none' }} />
                </div>
              ))}
            </div>
          </div>
          <div style={{ background: t.accentBg, borderRadius: 14, padding: 24, textAlign: 'center' }}>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3,1fr)', gap: 14 }}>
              <div><div style={{ fontSize: 10, color: t.muted }}>ANAPARA</div><div style={{ fontSize: 18, fontWeight: 600 }}>{faiz.ana.toLocaleString('tr-TR')} ₺</div></div>
              <div><div style={{ fontSize: 10, color: t.muted }}>FAİZ</div><div style={{ fontSize: 18, fontWeight: 600, color: t.accent }}>+{hesaplaFaiz(faiz.ana, faiz.oran, faiz.gun).toLocaleString('tr-TR')} ₺</div></div>
              <div><div style={{ fontSize: 10, color: t.muted }}>TOPLAM</div><div style={{ fontSize: 20, fontWeight: 700, color: t.primary }}>{(faiz.ana + hesaplaFaiz(faiz.ana, faiz.oran, faiz.gun)).toLocaleString('tr-TR')} ₺</div></div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
