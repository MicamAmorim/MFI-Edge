'use client'

import { useEffect, useMemo, useState } from 'react'

const API = process.env.NEXT_PUBLIC_MFI_API || 'http://127.0.0.1:8000'

function Metric({ label, value }) {
  return (
    <div className="metric">
      <span>{label}</span>
      <strong>{value ?? '—'}</strong>
    </div>
  )
}

function ResultCard({ item }) {
  const [scaleIndex, setScaleIndex] = useState(0)
  const attention = item.attention || []
  const selected = attention[Math.min(scaleIndex, Math.max(attention.length - 1, 0))]

  return (
    <article className="result-card">
      <div className="result-head">
        <div>
          <p className="eyebrow">{item.filename}</p>
          <h3>{item.width} × {item.height}</h3>
        </div>
        <div className="runtime">{item.runtime_ms.toFixed(0)} ms</div>
      </div>

      <div className="visual-grid">
        <figure>
          <figcaption>Original</figcaption>
          <img src={item.original} alt="Original" />
        </figure>

        <figure className="attention-panel">
          <figcaption>Atenção · {selected?.label || '—'}</figcaption>
          {selected && <img src={selected.overlay} alt="Attention overlay" />}
          {attention.length > 1 && (
            <div className="scale-control">
              <input
                type="range"
                min="0"
                max={attention.length - 1}
                value={scaleIndex}
                onChange={(e) => setScaleIndex(Number(e.target.value))}
              />
              <div className="scale-ticks">
                {attention.map((a, i) => (
                  <button
                    type="button"
                    key={`${a.label}-${i}`}
                    onClick={() => setScaleIndex(i)}
                    className={i === scaleIndex ? 'active' : ''}
                  >
                    {a.scale ? a.scale : 'Σ'}
                  </button>
                ))}
              </div>
            </div>
          )}
        </figure>

        <figure>
          <figcaption>Borda final · máscara</figcaption>
          <img src={item.edge} alt="Final edge map" />
        </figure>

        <figure>
          <figcaption>Borda final · overlay</figcaption>
          <img src={item.edge_overlay} alt="Final edge overlay" />
        </figure>
      </div>

      <div className="result-meta">
        <span>threshold {item.threshold.toFixed(5)}</span>
        <span>{item.threshold_mode}</span>
        <a href={item.edge} download={`${item.filename}-edge.png`}>baixar máscara</a>
        <a href={item.edge_overlay} download={`${item.filename}-edge-overlay.png`}>baixar overlay</a>
      </div>
    </article>
  )
}

export default function Home() {
  const [models, setModels] = useState([])
  const [rankNote, setRankNote] = useState('')
  const [modelId, setModelId] = useState('')
  const [files, setFiles] = useState([])
  const [results, setResults] = useState([])
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [maxSide, setMaxSide] = useState(768)
  const [quantile, setQuantile] = useState(0.90)

  useEffect(() => {
    fetch(`${API}/api/models`)
      .then((r) => {
        if (!r.ok) throw new Error(`API ${r.status}`)
        return r.json()
      })
      .then((data) => {
        setModels(data.models || [])
        setRankNote(data.note || '')
        if (data.models?.length) setModelId(data.models[0].id)
      })
      .catch((e) => setError(`Não foi possível conectar à API local: ${e.message}`))
  }, [])

  const selectedModel = useMemo(
    () => models.find((m) => m.id === modelId),
    [models, modelId]
  )

  async function run() {
    if (!files.length || !modelId) return
    setBusy(true)
    setError('')
    setResults([])
    try {
      const form = new FormData()
      files.forEach((f) => form.append('files', f))
      form.append('model_id', modelId)
      form.append('max_side', String(maxSide))
      form.append('edge_quantile', String(quantile))
      const r = await fetch(`${API}/api/infer`, { method: 'POST', body: form })
      const data = await r.json()
      if (!r.ok) throw new Error(data.detail || `API ${r.status}`)
      setResults(data.results || [])
    } catch (e) {
      setError(e.message)
    } finally {
      setBusy(false)
    }
  }

  return (
    <main>
      <section className="hero shell">
        <div>
          <p className="eyebrow">MFI-EDGE · DESKTOP LAB</p>
          <h1>Teste local de modelos<br />com atenção multiescala.</h1>
          <p className="hero-copy">
            Interface local em Next.js, preparada para receber os modelos promovidos do pipeline experimental.
            O ranking é sempre exibido do melhor para o pior segundo a métrica de validação declarada.
          </p>
        </div>
        <div className="status-card">
          <span className="dot" /> API local
          <strong>{API}</strong>
        </div>
      </section>

      <section className="shell workspace">
        <aside className="controls">
          <div className="panel">
            <p className="eyebrow">1 · MODELO</p>
            <label>Modelo ranqueado</label>
            <select value={modelId} onChange={(e) => setModelId(e.target.value)}>
              {models.map((m) => (
                <option key={m.id} value={m.id}>
                  #{m.rank} · {m.name} · ODS {Number(m.selection_ODS).toFixed(4)}
                </option>
              ))}
            </select>
            {selectedModel && (
              <div className="model-card">
                <div className="model-rank">#{selectedModel.rank}</div>
                <div>
                  <strong>{selectedModel.measure}</strong>
                  <p>{selectedModel.strategy}</p>
                </div>
                <div className="metric-row">
                  <Metric label="Selection ODS" value={Number(selectedModel.selection_ODS).toFixed(4)} />
                  <Metric label="Held-out F1" value={Number(selectedModel.heldout_F1).toFixed(4)} />
                </div>
              </div>
            )}
            <p className="fineprint">{rankNote}</p>
          </div>

          <div className="panel">
            <p className="eyebrow">2 · ENTRADA</p>
            <label className="dropzone">
              <input
                type="file"
                accept="image/*"
                multiple
                onChange={(e) => setFiles(Array.from(e.target.files || []))}
              />
              <strong>{files.length ? `${files.length} imagem(ns) selecionada(s)` : 'Clique ou arraste imagens'}</strong>
              <span>PNG, JPEG, WEBP · até 64 por lote</span>
            </label>
            {!!files.length && (
              <div className="file-list">
                {files.slice(0, 8).map((f) => <span key={`${f.name}-${f.size}`}>{f.name}</span>)}
                {files.length > 8 && <span>+ {files.length - 8} arquivos</span>}
              </div>
            )}
          </div>

          <div className="panel advanced">
            <p className="eyebrow">3 · EXECUÇÃO</p>
            <label>Maior lado: {maxSide}px</label>
            <input type="range" min="256" max="1536" step="128" value={maxSide} onChange={(e) => setMaxSide(Number(e.target.value))} />
            <label>Quantil de borda*: {quantile.toFixed(2)}</label>
            <input type="range" min="0.70" max="0.99" step="0.01" value={quantile} onChange={(e) => setQuantile(Number(e.target.value))} />
            <p className="fineprint">*Usado somente quando o registro ainda não possui o threshold congelado exportado do benchmark.</p>
            <button className="run" disabled={busy || !files.length || !modelId} onClick={run}>
              {busy ? 'Processando…' : `Executar ${files.length || ''}`}
            </button>
          </div>
        </aside>

        <section className="results">
          <div className="results-title">
            <div>
              <p className="eyebrow">SAÍDA</p>
              <h2>{results.length ? `${results.length} resultado(s)` : 'Aguardando imagens'}</h2>
            </div>
            {busy && <div className="spinner" />}
          </div>
          {error && <div className="error">{error}</div>}
          {!results.length && !busy && !error && (
            <div className="empty">
              <div className="empty-grid" />
              <h3>Original · atenção · borda</h3>
              <p>O painel de atenção terá um slider para navegar entre a fusão multiescala e cada janela MFI.</p>
            </div>
          )}
          <div className="result-stack">
            {results.map((r, i) => <ResultCard key={`${r.filename}-${i}`} item={r} />)}
          </div>
        </section>
      </section>
    </main>
  )
}
