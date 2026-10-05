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

function ScaleControl({ attention, scaleIndex, setScaleIndex }) {
  if (!attention?.length || attention.length < 2) return null
  return (
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
          <ScaleControl attention={attention} scaleIndex={scaleIndex} setScaleIndex={setScaleIndex} />
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
        <span>prep {Number(item.prepare_ms || 0).toFixed(0)} ms</span>
        <span>modelo {Number(item.model_runtime_ms || 0).toFixed(0)} ms</span>
        <a href={item.edge} download={`${item.filename}-edge.png`}>baixar máscara</a>
        <a href={item.edge_overlay} download={`${item.filename}-edge-overlay.png`}>baixar overlay</a>
      </div>
    </article>
  )
}

function CompareResultCard({ item }) {
  const [scaleIndex, setScaleIndex] = useState(0)
  const modelResults = item.models || []
  const attention = modelResults[0]?.attention || []
  const selectedLabel = attention[Math.min(scaleIndex, Math.max(attention.length - 1, 0))]?.label || '—'

  return (
    <article className="result-card compare-card">
      <div className="result-head">
        <div>
          <p className="eyebrow">COMPARAÇÃO · {item.filename}</p>
          <h3>{item.width} × {item.height} · preprocessamento compartilhado {Number(item.prepare_ms || 0).toFixed(0)} ms</h3>
        </div>
        <div className="runtime">{modelResults.length} modelos</div>
      </div>

      <div className="compare-topline">
        <figure className="compare-original">
          <figcaption>Entrada comum</figcaption>
          <img src={item.original} alt="Original" />
        </figure>
        <div className="compare-scale">
          <p className="eyebrow">ESCALA SINCRONIZADA</p>
          <strong>{selectedLabel}</strong>
          <p className="fineprint">O mesmo controle altera o mapa de atenção de todos os modelos para facilitar a comparação visual.</p>
          <ScaleControl attention={attention} scaleIndex={scaleIndex} setScaleIndex={setScaleIndex} />
        </div>
      </div>

      <div className="compare-grid" style={{ '--compare-cols': Math.min(modelResults.length, 4) }}>
        {modelResults.map((r) => {
          const m = r.model || {}
          const att = r.attention?.[Math.min(scaleIndex, Math.max((r.attention?.length || 1) - 1, 0))]
          return (
            <section className="compare-model" key={m.id || `${m.measure}-${m.strategy}`}>
              <div className="compare-model-head">
                <div className="rank-badge">#{m.rank}</div>
                <div>
                  <strong>{m.name || m.measure}</strong>
                  <p>{m.measure} · {m.strategy}</p>
                </div>
              </div>
              <div className="compare-metrics">
                <Metric label="Selection ODS" value={Number(m.selection_ODS).toFixed(4)} />
                <Metric label="Held-out F1" value={Number(m.heldout_F1).toFixed(4)} />
              </div>
              <figure>
                <figcaption>Atenção · {att?.label || selectedLabel}</figcaption>
                {att && <img src={att.overlay} alt={`Attention ${m.name || m.measure}`} />}
              </figure>
              <figure>
                <figcaption>Borda final · overlay</figcaption>
                <img src={r.edge_overlay} alt={`Edges ${m.name || m.measure}`} />
              </figure>
              <figure className="compare-mask">
                <figcaption>Máscara final</figcaption>
                <img src={r.edge} alt={`Edge mask ${m.name || m.measure}`} />
              </figure>
              <div className="result-meta compact-meta">
                <span>thr {Number(r.threshold).toFixed(5)}</span>
                <span>{r.threshold_mode}</span>
                <span>{Number(r.model_runtime_ms || 0).toFixed(0)} ms</span>
                <a href={r.edge} download={`${item.filename}-${m.id || m.rank}-edge.png`}>máscara</a>
                <a href={r.edge_overlay} download={`${item.filename}-${m.id || m.rank}-overlay.png`}>overlay</a>
              </div>
            </section>
          )
        })}
      </div>
    </article>
  )
}

export default function Home() {
  const [models, setModels] = useState([])
  const [rankNote, setRankNote] = useState('')
  const [modelId, setModelId] = useState('')
  const [compareIds, setCompareIds] = useState([])
  const [maxCompare, setMaxCompare] = useState(4)
  const [mode, setMode] = useState('single')
  const [files, setFiles] = useState([])
  const [results, setResults] = useState([])
  const [resultMode, setResultMode] = useState('single')
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
        const rows = data.models || []
        setModels(rows)
        setRankNote(data.note || '')
        setMaxCompare(Number(data.max_compare_models || 4))
        if (rows.length) {
          setModelId(rows[0].id)
          setCompareIds(rows.slice(0, Math.min(3, rows.length)).map((m) => m.id))
        }
      })
      .catch((e) => setError(`Não foi possível conectar à API local: ${e.message}`))
  }, [])

  const selectedModel = useMemo(
    () => models.find((m) => m.id === modelId),
    [models, modelId]
  )
  const selectedCompareModels = useMemo(
    () => compareIds.map((id) => models.find((m) => m.id === id)).filter(Boolean),
    [models, compareIds]
  )

  function chooseTop(n) {
    setCompareIds(models.slice(0, Math.min(n, maxCompare, models.length)).map((m) => m.id))
  }

  function toggleCompare(id) {
    setCompareIds((current) => {
      if (current.includes(id)) return current.filter((x) => x !== id)
      if (current.length >= maxCompare) return current
      return [...current, id].sort((a, b) => {
        const ra = models.find((m) => m.id === a)?.rank || 9999
        const rb = models.find((m) => m.id === b)?.rank || 9999
        return ra - rb
      })
    })
  }

  async function run() {
    const valid = files.length && (mode === 'single' ? modelId : compareIds.length >= 2)
    if (!valid) return
    setBusy(true)
    setError('')
    setResults([])
    try {
      const form = new FormData()
      files.forEach((f) => form.append('files', f))
      form.append('max_side', String(maxSide))
      form.append('edge_quantile', String(quantile))
      let endpoint = '/api/infer'
      if (mode === 'single') {
        form.append('model_id', modelId)
      } else {
        endpoint = '/api/compare'
        form.append('model_ids', JSON.stringify(compareIds))
      }
      const r = await fetch(`${API}${endpoint}`, { method: 'POST', body: form })
      const data = await r.json()
      if (!r.ok) throw new Error(data.detail || `API ${r.status}`)
      setResults(data.results || [])
      setResultMode(mode)
    } catch (e) {
      setError(e.message)
    } finally {
      setBusy(false)
    }
  }

  const runDisabled = busy || !files.length || (mode === 'single' ? !modelId : compareIds.length < 2)

  return (
    <main>
      <section className="hero shell">
        <div>
          <p className="eyebrow">MFI-EDGE · DESKTOP LAB</p>
          <h1>Teste e compare modelos<br />com atenção multiescala.</h1>
          <p className="hero-copy">
            Interface local em Next.js para inferência e comparação lado a lado. O ranking é sempre exibido do melhor
            para o pior segundo a métrica de validação declarada, sem reordenar pelo held-out pós-hoc.
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
            <p className="eyebrow">1 · MODO E MODELOS</p>
            <div className="mode-switch">
              <button type="button" className={mode === 'single' ? 'active' : ''} onClick={() => setMode('single')}>Modelo único</button>
              <button type="button" className={mode === 'compare' ? 'active' : ''} onClick={() => setMode('compare')}>Comparar 2–{maxCompare}</button>
            </div>

            {mode === 'single' ? (
              <>
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
              </>
            ) : (
              <>
                <div className="quick-picks">
                  <span>Atalhos:</span>
                  {[2, 3, 4].filter((n) => n <= maxCompare).map((n) => (
                    <button type="button" key={n} onClick={() => chooseTop(n)}>Top {n}</button>
                  ))}
                </div>
                <div className="compare-picker">
                  {models.map((m) => {
                    const checked = compareIds.includes(m.id)
                    const disabled = !checked && compareIds.length >= maxCompare
                    return (
                      <label key={m.id} className={`compare-choice ${checked ? 'checked' : ''} ${disabled ? 'disabled' : ''}`}>
                        <input type="checkbox" checked={checked} disabled={disabled} onChange={() => toggleCompare(m.id)} />
                        <span className="choice-rank">#{m.rank}</span>
                        <span className="choice-copy">
                          <strong>{m.name || m.measure}</strong>
                          <small>ODS {Number(m.selection_ODS).toFixed(4)} · F1 {Number(m.heldout_F1).toFixed(4)}</small>
                        </span>
                      </label>
                    )
                  })}
                </div>
                <p className="selection-count">{compareIds.length}/{maxCompare} selecionados · mínimo 2</p>
              </>
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
            {mode === 'compare' && (
              <p className="fineprint accent-note">No modo comparação, condicionamento, features multiescala, orientação e Scharr são calculados uma única vez por imagem e reutilizados pelos modelos.</p>
            )}
            <button className="run" disabled={runDisabled} onClick={run}>
              {busy ? 'Processando…' : mode === 'compare' ? `Comparar ${compareIds.length} modelos` : `Executar ${files.length || ''}`}
            </button>
          </div>
        </aside>

        <section className="results">
          <div className="results-title">
            <div>
              <p className="eyebrow">SAÍDA</p>
              <h2>{results.length ? `${results.length} imagem(ns) processada(s)` : 'Aguardando imagens'}</h2>
              {results.length > 0 && resultMode === 'compare' && (
                <p className="result-subtitle">Comparação sincronizada de {selectedCompareModels.length} modelos</p>
              )}
            </div>
            {busy && <div className="spinner" />}
          </div>
          {error && <div className="error">{error}</div>}
          {!results.length && !busy && !error && (
            <div className="empty">
              <div className="empty-grid" />
              <h3>Original · atenção · borda · comparação</h3>
              <p>Use modelo único ou selecione de 2 a {maxCompare} modelos. Na comparação, um slider único percorre Σ, 25, 13, 7, 5 e 3 em todos os modelos simultaneamente.</p>
            </div>
          )}
          <div className="result-stack">
            {resultMode === 'compare'
              ? results.map((r, i) => <CompareResultCard key={`${r.filename}-${i}`} item={r} />)
              : results.map((r, i) => <ResultCard key={`${r.filename}-${i}`} item={r} />)}
          </div>
        </section>
      </section>
    </main>
  )
}
