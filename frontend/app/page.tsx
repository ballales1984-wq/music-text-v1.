'use client'

import { useState, useRef, useEffect } from 'react'
import axios from 'axios'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001'

interface TranscriptionResult {
  job_id: string
  status: string
  original_audio_url?: string  // Audio originale caricato
  vocal_audio_url?: string | null  // Voce isolata
  vocal_clean_audio_url?: string | null  // Voce pulita (denoise)
  instrumental_audio_url?: string | null  // Base strumentale
  raw_transcription: {
    text: string
    cleaned_text?: string  // Testo pulito
    cleaning_stats?: {  // Statistiche pulizia
      original_sentences?: number
      cleaned_sentences?: number
      removed_sentences?: number
      reduction_percent?: number
      original_length?: number
      cleaned_length?: number
      length_reduction?: number
    }
    quality?: {  // Qualità testo
      quality_score?: number
      repetition_ratio?: number
      length_ratio?: number
      is_good_quality?: boolean
    }
    phonemes: string
    language: string
    confidence: number
    has_clear_words: boolean
    vocal_segments?: Array<[number, number]>
    vocal_segments_count?: number
    vocal_percentage?: number
    audio_features?: any
    audio_features_str?: string
    rhythmic_features?: any
    rhythmic_features_str?: string
    metric_pattern?: {  // NUOVO: pattern metrico
      syllable_count?: number
      strong_beats?: number
      time_signature?: string
      accents?: number[]
      detailed_structure?: {  // NUOVO: struttura dettagliata per riga
        total_lines?: number
        total_syllables?: number
        tempo?: number
        lines?: Array<{
          line_number?: number
          syllable_count?: number
          start_time?: number
          end_time?: number
          duration?: number
          accents?: number[]
          strong_syllables?: number[]
        }>
      }
    }
  }
  final_text: string
  italian_translation?: string
  lyrics_variants?: {
    variants: Array<{
      id: number
      full_text: string
      verses: string[]
      chorus: string[]
      preview: string
    }>
    selected: number
    total: number
  }
  vocal_segments?: Array<[number, number]>
  vocal_segments_count?: number
  audio_features?: {
    tempo?: number
    notes_count?: number
    melody?: Array<[number, number]>
    key?: string
  }
  rhythmic_features?: {
    tempo?: number
    beat_count?: number
    rhythm_pattern?: string
    time_signature?: string
  }
  metric_pattern?: {  // NUOVO: pattern metrico dalla pipeline
    syllable_count?: number
    strong_beats?: number
    time_signature?: string
    detailed_structure?: {  // NUOVO: struttura dettagliata per riga
      total_lines?: number
      total_syllables?: number
      tempo?: number
      lines?: Array<{
        line_number?: number
        syllable_count?: number
        start_time?: number
        end_time?: number
        duration?: number
        accents?: number[]
        strong_syllables?: number[]
      }>
    }
  }
  message: string
}

interface JobStatus {
  status: string
  step: number
  total_steps: number
  current_step: string
  progress: number
  error?: string
}

export default function Home() {
  const [file, setFile] = useState<File | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<TranscriptionResult | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [originalAudioUrl, setOriginalAudioUrl] = useState<string | null>(null)
  const [vocalAudioUrl, setVocalAudioUrl] = useState<string | null>(null)
  const [vocalCleanAudioUrl, setVocalCleanAudioUrl] = useState<string | null>(null)
  const [instrumentalAudioUrl, setInstrumentalAudioUrl] = useState<string | null>(null)
  const [italianTranslation, setItalianTranslation] = useState<string | null>(null)
  const [jobStatus, setJobStatus] = useState<JobStatus | null>(null)
  const [currentJobId, setCurrentJobId] = useState<string | null>(null)

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0]
    if (selectedFile) {
      setFile(selectedFile)
      setError(null)
      setResult(null)
      setVocalAudioUrl(null)
      setVocalCleanAudioUrl(null)
      setInstrumentalAudioUrl(null)
      setItalianTranslation(null)
      setLoading(false)
      setJobStatus(null)
      setCurrentJobId(null)
    } else {
      setFile(null)
    }
  }

  const handleUpload = async () => {
    // Leggi il file dall'input ref se lo stato è null (fallback)
    const fileToUpload = file || fileInputRef.current?.files?.[0]
    
    if (!fileToUpload) {
      setError('Seleziona un file audio prima di procedere')
      return
    }

    setLoading(true)
    setError(null)
    setResult(null)
    setVocalAudioUrl(null)
    setVocalCleanAudioUrl(null)
    setInstrumentalAudioUrl(null)
    setItalianTranslation(null)
    setJobStatus(null)
    setCurrentJobId(null)

    try {
      const formData = new FormData()
      formData.append('file', fileToUpload)
      
      // Aggiorna lo stato se non era già impostato
      if (!file && fileToUpload) {
        setFile(fileToUpload)
      }

      // Upload file (timeout breve - il backend risponde subito con job_id)
      const response = await axios.post<{job_id: string, status: string, message?: string}>(
        `${API_URL}/upload`,
        formData,
        {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
          timeout: 300000, // 5 minuti timeout per upload (per file grandi)
          maxContentLength: Infinity,
          maxBodyLength: Infinity,
        }
      )
      
      const jobId = response.data.job_id
      setCurrentJobId(jobId)
      
      // Polling per lo stato del job — limite 180 tentativi (~3 minuti)
      let pollAttempts = 0
      const MAX_POLL_ATTEMPTS = 180

      const pollStatus = async (): Promise<void> => {
        pollAttempts++
        if (pollAttempts > MAX_POLL_ATTEMPTS) {
          setError('Timeout: il processamento sta impiegando troppo. Riprova più tardi.')
          setLoading(false)
          return
        }

        try {
          const statusResponse = await axios.get<JobStatus & {result?: TranscriptionResult}>(
            `${API_URL}/status/${jobId}`,
            { timeout: 5000 }
          )
          
          setJobStatus(statusResponse.data)
          
          if (statusResponse.data.status === 'completed') {
            const result = statusResponse.data.result as TranscriptionResult
            
            if (result) {
              setResult(result)
              if (result.original_audio_url) setOriginalAudioUrl(`${API_URL}${result.original_audio_url}`)
              if (result.vocal_audio_url) setVocalAudioUrl(`${API_URL}${result.vocal_audio_url}`)
              if (result.vocal_clean_audio_url) setVocalCleanAudioUrl(`${API_URL}${result.vocal_clean_audio_url}`)
              if (result.instrumental_audio_url) setInstrumentalAudioUrl(`${API_URL}${result.instrumental_audio_url}`)
              if (result.italian_translation) setItalianTranslation(result.italian_translation)
            }
            setLoading(false)
          } else if (statusResponse.data.status === 'error') {
            setError(statusResponse.data.error || 'Errore durante il processamento')
            setLoading(false)
          } else {
            setTimeout(pollStatus, 1000)
          }
        } catch (err: any) {
          if (err.response?.status === 404 || err.code === 'ECONNABORTED' || err.message?.includes('timeout')) {
            setTimeout(pollStatus, 1000)
          } else {
            setTimeout(pollStatus, 2000)
          }
        }
      }
      
      setTimeout(pollStatus, 500)
      
    } catch (err: any) {
      let errorMessage = 'Errore durante il processamento del file'
      
      if (err.code === 'ECONNREFUSED' || err.message?.includes('Network Error')) {
        errorMessage = 'Impossibile connettersi al backend. Verifica che sia attivo su http://localhost:8001'
      } else if (err.code === 'ECONNABORTED' || err.message?.includes('timeout')) {
        errorMessage = 'Timeout durante upload. Il file potrebbe essere troppo grande (>100MB) o la connessione è lenta. Riprova con un file più piccolo.'
      } else if (err.response?.data?.detail) {
        errorMessage = err.response.data.detail
      } else if (err.message) {
        errorMessage = err.message
      }
      
      setError(errorMessage)
      setLoading(false)
      setJobStatus(null)
      setCurrentJobId(null)
    }
  }

  const downloadText = () => {
    if (!result) return

    const content = `=== MUSIC TEXT GENERATOR - RISULTATI ===\n\n` +
      `=== ANALISI AUDIO ===\n` +
      (result.audio_features?.tempo ? `Tempo: ${result.audio_features.tempo.toFixed(1)} BPM\n` : '') +
      (result.audio_features?.notes_count !== undefined ? `Note rilevate: ${result.audio_features.notes_count}\n` : '') +
      (result.raw_transcription.audio_features?.key ? `Tonalità: ${result.raw_transcription.audio_features.key}\n` : '') +
      (result.raw_transcription.audio_features_str ? `\n${result.raw_transcription.audio_features_str}\n` : '') +
      `\n=== TRASCRIZIONE ===\n` +
      `Trascrizione grezza:\n${result.raw_transcription.text}\n\n` +
      `Fonemi rilevati:\n${result.raw_transcription.phonemes}\n\n` +
      `Lingua: ${result.raw_transcription.language}\n` +
      `Confidenza: ${(result.raw_transcription.confidence * 100).toFixed(1)}%\n` +
      `Parole chiare: ${result.raw_transcription.has_clear_words ? 'Sì' : 'No'}\n` +
      `\n=== TESTO GENERATO (INGLESE) ===\n` +
      `${result.final_text}\n\n` +
      `=== NOTE ===\n` +
      `Il testo è stato generato analizzando pitch, timing, ritmo e metrica della melodia per adattarsi perfettamente alla musica.\n`

    const blob = new Blob([content], { type: 'text/plain' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `testo_generato_${result.job_id}.txt`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  }

  const downloadAudio = () => {
    if (!vocalAudioUrl) return

    const a = document.createElement('a')
    a.href = vocalAudioUrl
    a.download = `base_strumentale_${result?.job_id || 'audio'}.wav`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
  }

  return (
    <main className="container">
      <div className="card">
        <h1 style={{ fontSize: '2.5rem', marginBottom: '1rem', textAlign: 'center', color: '#333' }}>
          🎵 Music Text Generator
        </h1>
        <p style={{ textAlign: 'center', color: '#666', marginBottom: '2rem' }}>
          Isola la voce da un brano e genera testo dai suoni vocali
        </p>

        <div style={{ marginBottom: '2rem' }}>
          <input
            ref={fileInputRef}
            type="file"
            accept="audio/*"
            onChange={handleFileChange}
            className="input-file"
            id="audio-input"
            disabled={loading}
          />
          <label htmlFor="audio-input" className="file-label" style={{ display: 'block', width: '100%' }}>
            {file ? `📁 ${file.name}` : '📁 Seleziona file audio (MP3, WAV, M4A, FLAC)'}
          </label>
        </div>

        <button
          onClick={handleUpload}
          disabled={(!file && !fileInputRef.current?.files?.[0]) || loading}
          className="button"
          style={{ width: '100%', marginBottom: '1rem' }}
          title={(!file && !fileInputRef.current?.files?.[0]) ? 'Seleziona un file prima' : loading ? 'Processamento in corso...' : 'Clicca per processare'}
        >
          {loading ? (
            <span style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.5rem' }}>
              <span className="loading"></span>
              Processamento in corso...
            </span>
          ) : (
            '🚀 Processa Audio'
          )}
        </button>
        


        {loading && (
          <div style={{ 
            background: '#f0f0f0', 
            padding: '1.5rem', 
            borderRadius: '8px', 
            marginTop: '1rem',
            textAlign: 'center'
          }}>
            <div style={{ marginBottom: '1rem' }}>
              <div style={{ 
                fontSize: '1.2rem', 
                fontWeight: '600', 
                color: '#667eea',
                marginBottom: '0.5rem'
              }}>
                ⏳ Processamento in corso...
              </div>
              {jobStatus && (
                <div style={{ color: '#666', fontSize: '1rem', marginBottom: '0.5rem', fontWeight: '500' }}>
                  Step {jobStatus.step}/{jobStatus.total_steps}: {jobStatus.current_step}
                </div>
              )}
              <div style={{ color: '#666', fontSize: '0.9rem' }}>
                {jobStatus ? `Progresso: ${jobStatus.progress}%` : 'Inizializzazione...'}
              </div>
            </div>
            <div style={{
              width: '100%',
              height: '12px',
              background: '#e0e0e0',
              borderRadius: '6px',
              overflow: 'hidden',
              marginBottom: '0.5rem',
              position: 'relative'
            }}>
              <div style={{
                width: `${jobStatus?.progress || 0}%`,
                height: '100%',
                background: 'linear-gradient(90deg, #667eea, #764ba2)',
                borderRadius: '6px',
                transition: 'width 0.3s ease',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'flex-end',
                paddingRight: '8px'
              }}>
                {jobStatus && jobStatus.progress > 15 && (
                  <span style={{ color: 'white', fontSize: '0.7rem', fontWeight: '600' }}>
                    {jobStatus.progress}%
                  </span>
                )}
              </div>
            </div>
                     {jobStatus && (
                     <div style={{ color: '#999', fontSize: '0.85rem', marginTop: '0.5rem' }}>
                       {jobStatus.current_step && (
                         <span>⏳ {jobStatus.current_step}</span>
                       )}
                       {!jobStatus.current_step && (
                         <>
                           {jobStatus.step === 0 && '⏳ Separazione voce e base strumentale...'}
                           {jobStatus.step === 1 && '⏳ Trascrizione Whisper (può richiedere 1-2 minuti)...'}
                           {jobStatus.step === 2 && '⏳ Estrazione struttura e conteggio sillabe...'}
                           {jobStatus.step === 3 && '⏳ Generazione testo con AI linguistica...'}
                         </>
                       )}
                     </div>
                   )}
          </div>
        )}

        {error && (
          <div className="error">
            <strong>Errore:</strong> {error}
          </div>
        )}

        {result && (
          <div style={{ marginTop: '2rem' }}>
            <div className="success">
              ✅ Processamento completato!
            </div>

            {originalAudioUrl && (
              <div style={{ marginTop: '1rem' }}>
                <h2 style={{ marginBottom: '0.5rem' }}>🎵 Audio Originale</h2>
                <p style={{ fontSize: '0.9rem', color: '#666', marginBottom: '0.5rem' }}>
                  Ascolta l'audio originale per capire da dove viene il testo trascritto
                </p>
                <audio controls src={originalAudioUrl} className="audio-player" style={{ width: '100%', marginBottom: '0.5rem' }} />
                <button 
                  onClick={() => {
                    if (!originalAudioUrl) return
                    const a = document.createElement('a')
                    a.href = originalAudioUrl
                    a.download = `original_${result?.job_id || 'audio'}.mp3`
                    document.body.appendChild(a)
                    a.click()
                    document.body.removeChild(a)
                  }} 
                  className="button" 
                  style={{ marginTop: '0.5rem' }}
                >
                  💾 Scarica Audio Originale
                </button>
              </div>
            )}

            {vocalAudioUrl && (
              <div style={{ marginTop: '1rem' }}>
                <h2 style={{ marginBottom: '0.5rem' }}>🎤 Traccia Vocale Isolata</h2>
                <audio controls src={vocalAudioUrl} className="audio-player" />
                <button 
                  onClick={() => {
                    if (!vocalAudioUrl) return
                    const a = document.createElement('a')
                    a.href = vocalAudioUrl
                    a.download = `vocale_isolata_${result?.job_id || 'audio'}.wav`
                    document.body.appendChild(a)
                    a.click()
                    document.body.removeChild(a)
                  }}
                  className="button" 
                  style={{ marginTop: '0.5rem' }}
                >
                  💾 Scarica Audio Vocale
                </button>
              </div>
            )}

            {instrumentalAudioUrl && (
              <div style={{ marginTop: '1rem' }}>
                <h2 style={{ marginBottom: '0.5rem' }}>🥁 Base Strumentale Isolata</h2>
                <audio controls src={instrumentalAudioUrl} className="audio-player" />
                <button 
                  onClick={() => {
                    if (!instrumentalAudioUrl) return
                    const a = document.createElement('a')
                    a.href = instrumentalAudioUrl
                    a.download = `base_strumentale_${result?.job_id || 'audio'}.wav`
                    document.body.appendChild(a)
                    a.click()
                    document.body.removeChild(a)
                  }} 
                  className="button" 
                  style={{ marginTop: '0.5rem' }}
                >
                  💾 Scarica Base Strumentale
                </button>
              </div>
            )}

            {vocalCleanAudioUrl && (
              <div style={{ marginTop: '1rem' }}>
                <h2 style={{ marginBottom: '0.5rem' }}>✨ Traccia Vocale Pulita (Denoise)</h2>
                <audio controls src={vocalCleanAudioUrl} className="audio-player" />
                <button 
                  onClick={() => {
                    if (!vocalCleanAudioUrl) return
                    const a = document.createElement('a')
                    a.href = vocalCleanAudioUrl
                    a.download = `vocale_pulita_${result?.job_id || 'audio'}.wav`
                    document.body.appendChild(a)
                    a.click()
                    document.body.removeChild(a)
                  }} 
                  className="button" 
                  style={{ marginTop: '0.5rem' }}
                >
                  💾 Scarica Voce Pulita
                </button>
              </div>
            )}

            {/* Analisi Metrica (Stile Beatles) */}
            {result.metric_pattern && (
              <div style={{ marginTop: '2rem' }}>
                <h2 style={{ marginBottom: '0.5rem' }}>🎵 Analisi Metrica (Stile Beatles)</h2>
                <div style={{ 
                  background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)', 
                  padding: '1.5rem', 
                  borderRadius: '12px',
                  marginBottom: '1rem',
                  color: 'white'
                }}>
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', gap: '1rem' }}>
                    {result.metric_pattern.syllable_count !== undefined && (
                      <div>
                        <div style={{ fontSize: '0.85rem', opacity: 0.9, marginBottom: '0.25rem' }}>Sillabe Totali</div>
                        <div style={{ fontSize: '1.5rem', fontWeight: 'bold' }}>{result.metric_pattern.syllable_count}</div>
                      </div>
                    )}
                    {result.metric_pattern.strong_beats !== undefined && (
                      <div>
                        <div style={{ fontSize: '0.85rem', opacity: 0.9, marginBottom: '0.25rem' }}>Accenti Forti</div>
                        <div style={{ fontSize: '1.5rem', fontWeight: 'bold' }}>{result.metric_pattern.strong_beats}</div>
                      </div>
                    )}
                    {result.metric_pattern.time_signature && (
                      <div>
                        <div style={{ fontSize: '0.85rem', opacity: 0.9, marginBottom: '0.25rem' }}>Time Signature</div>
                        <div style={{ fontSize: '1.5rem', fontWeight: 'bold' }}>{result.metric_pattern.time_signature}</div>
                      </div>
                    )}
                    {result.metric_pattern.detailed_structure?.total_lines !== undefined && (
                      <div>
                        <div style={{ fontSize: '0.85rem', opacity: 0.9, marginBottom: '0.25rem' }}>Righe Analizzate</div>
                        <div style={{ fontSize: '1.5rem', fontWeight: 'bold' }}>{result.metric_pattern.detailed_structure.total_lines}</div>
                      </div>
                    )}
                  </div>
                  
                  {/* NUOVO: Struttura dettagliata per riga */}
                  {result.metric_pattern.detailed_structure && result.metric_pattern.detailed_structure.lines && result.metric_pattern.detailed_structure.lines.length > 0 && (
                    <div style={{ marginTop: '1.5rem', padding: '1rem', background: 'rgba(255,255,255,0.15)', borderRadius: '8px' }}>
                      <div style={{ fontSize: '1rem', fontWeight: '600', marginBottom: '1rem' }}>
                        📊 Struttura Vocale Dettagliata (Riga per Riga)
                      </div>
                      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem', maxHeight: '400px', overflowY: 'auto' }}>
                        {result.metric_pattern.detailed_structure.lines.map((line, idx) => (
                          <div 
                            key={idx}
                            style={{ 
                              padding: '0.75rem', 
                              background: 'rgba(255,255,255,0.1)', 
                              borderRadius: '6px',
                              fontSize: '0.9rem'
                            }}
                          >
                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.25rem' }}>
                              <strong>Riga {line.line_number || idx + 1}</strong>
                              <span style={{ opacity: 0.8 }}>
                                {line.syllable_count || 0} sillabe • {line.duration ? `${line.duration.toFixed(2)}s` : 'N/A'}
                              </span>
                            </div>
                            <div style={{ fontSize: '0.85rem', opacity: 0.9, marginTop: '0.25rem' }}>
                              {line.strong_syllables && line.strong_syllables.length > 0 && (
                                <span>
                                  Accenti forti: posizioni {line.strong_syllables.join(', ')}
                                </span>
                              )}
                              {line.start_time !== undefined && line.end_time !== undefined && (
                                <span style={{ marginLeft: '1rem' }}>
                                  Timing: {line.start_time.toFixed(2)}s - {line.end_time.toFixed(2)}s
                                </span>
                              )}
                            </div>
                            {line.accents && line.accents.length > 0 && (
                              <div style={{ marginTop: '0.5rem', fontSize: '0.8rem', opacity: 0.8 }}>
                                Pattern accenti: {line.accents.map((a, i) => (
                                  <span key={i} style={{ marginRight: '0.25rem' }}>
                                    {a === 1 ? '●' : '○'}
                                  </span>
                                ))}
                              </div>
                            )}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                  
                  <div style={{ marginTop: '1rem', padding: '1rem', background: 'rgba(255,255,255,0.1)', borderRadius: '8px', fontSize: '0.9rem' }}>
                    💡 La metrica analizza sillabe e accenti per generare testi che seguono perfettamente la melodia originale. 
                    {result.metric_pattern.detailed_structure && ' La struttura dettagliata mostra come la voce è stata analizzata riga per riga con timing, durata e accenti precisi.'}
                  </div>
                </div>
              </div>
            )}

            {/* Analisi Ritmica (Base Strumentale) */}
            {result.rhythmic_features && (
              <div style={{ marginTop: '2rem' }}>
                <h2 style={{ marginBottom: '0.5rem' }}>🥁 Analisi Ritmica (Base Strumentale)</h2>
                <div style={{ 
                  background: 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)', 
                  padding: '1.5rem', 
                  borderRadius: '12px',
                  marginBottom: '1rem',
                  color: 'white'
                }}>
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', gap: '1rem' }}>
                    {result.rhythmic_features.tempo && (
                      <div>
                        <div style={{ fontSize: '0.85rem', opacity: 0.9, marginBottom: '0.25rem' }}>BPM Base</div>
                        <div style={{ fontSize: '1.5rem', fontWeight: 'bold' }}>{result.rhythmic_features.tempo.toFixed(1)}</div>
                      </div>
                    )}
                    {result.rhythmic_features.beat_count !== undefined && (
                      <div>
                        <div style={{ fontSize: '0.85rem', opacity: 0.9, marginBottom: '0.25rem' }}>Beat Rilevati</div>
                        <div style={{ fontSize: '1.5rem', fontWeight: 'bold' }}>{result.rhythmic_features.beat_count}</div>
                      </div>
                    )}
                    {result.rhythmic_features.rhythm_pattern && (
                      <div>
                        <div style={{ fontSize: '0.85rem', opacity: 0.9, marginBottom: '0.25rem' }}>Pattern Ritmico</div>
                        <div style={{ fontSize: '1.5rem', fontWeight: 'bold' }}>
                          {result.rhythmic_features.rhythm_pattern === 'regular' ? 'Regolare' : 
                           result.rhythmic_features.rhythm_pattern === 'slightly_varied' ? 'Leggermente Variato' : 
                           'Variato'}
                        </div>
                      </div>
                    )}
                    {result.rhythmic_features.time_signature && (
                      <div>
                        <div style={{ fontSize: '0.85rem', opacity: 0.9, marginBottom: '0.25rem' }}>Time Signature</div>
                        <div style={{ fontSize: '1.5rem', fontWeight: 'bold' }}>{result.rhythmic_features.time_signature}</div>
                      </div>
                    )}
                  </div>
                  {result.raw_transcription.rhythmic_features_str && (
                    <div style={{ marginTop: '1rem', padding: '1rem', background: 'rgba(255,255,255,0.1)', borderRadius: '8px', fontSize: '0.9rem' }}>
                      <div style={{ fontWeight: '600', marginBottom: '0.5rem' }}>Dettagli Ritmici:</div>
                      <pre style={{ margin: 0, whiteSpace: 'pre-wrap', fontFamily: 'inherit' }}>
                        {result.raw_transcription.rhythmic_features_str}
                      </pre>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Analisi Audio Avanzata (Voce) */}
            {(result.audio_features || result.raw_transcription.audio_features) && (
              <div style={{ marginTop: '2rem' }}>
                <h2 style={{ marginBottom: '0.5rem' }}>🎵 Analisi Linguistica (Voce)</h2>
                <div style={{ 
                  background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)', 
                  padding: '1.5rem', 
                  borderRadius: '12px',
                  marginBottom: '1rem',
                  color: 'white'
                }}>
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', gap: '1rem' }}>
                    {result.audio_features?.tempo && (
                      <div>
                        <div style={{ fontSize: '0.85rem', opacity: 0.9, marginBottom: '0.25rem' }}>Tempo</div>
                        <div style={{ fontSize: '1.5rem', fontWeight: 'bold' }}>{result.audio_features.tempo.toFixed(1)} BPM</div>
                      </div>
                    )}
                    {result.audio_features?.notes_count !== undefined && (
                      <div>
                        <div style={{ fontSize: '0.85rem', opacity: 0.9, marginBottom: '0.25rem' }}>Note Rilevate</div>
                        <div style={{ fontSize: '1.5rem', fontWeight: 'bold' }}>{result.audio_features.notes_count}</div>
                      </div>
                    )}
                    {result.raw_transcription.audio_features?.key && (
                      <div>
                        <div style={{ fontSize: '0.85rem', opacity: 0.9, marginBottom: '0.25rem' }}>Tonalità</div>
                        <div style={{ fontSize: '1.5rem', fontWeight: 'bold' }}>{result.raw_transcription.audio_features.key}</div>
                      </div>
                    )}
                  </div>
                  {result.raw_transcription.audio_features_str && (
                    <div style={{ marginTop: '1rem', padding: '1rem', background: 'rgba(255,255,255,0.1)', borderRadius: '8px', fontSize: '0.9rem' }}>
                      <div style={{ fontWeight: '600', marginBottom: '0.5rem' }}>Dettagli Musicali:</div>
                      <pre style={{ margin: 0, whiteSpace: 'pre-wrap', fontFamily: 'inherit' }}>
                        {result.raw_transcription.audio_features_str}
                      </pre>
                    </div>
                  )}
                </div>
                
                {/* Sezione Prosodia (Andamento Vocale) */}
                {result.raw_transcription.audio_features?.prosody && (
                  <div style={{ 
                    marginTop: '1rem', 
                    padding: '1.5rem', 
                    background: 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)', 
                    borderRadius: '12px',
                    color: 'white'
                  }}>
                    <h3 style={{ marginBottom: '1rem', fontSize: '1.2rem', fontWeight: 'bold' }}>
                      🎤 Prosodia (Andamento Vocale)
                    </h3>
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem', fontSize: '0.9rem' }}>
                      {result.raw_transcription.audio_features.prosody.intonation && result.raw_transcription.audio_features.prosody.intonation.length > 0 && (
                        <div>
                          <div style={{ opacity: 0.9, marginBottom: '0.25rem' }}>Intonazione</div>
                          <div style={{ fontSize: '1.1rem', fontWeight: 'bold' }}>
                            {result.raw_transcription.audio_features.prosody.intonation.filter((i: any) => i.direction === 'rising').length} ↗️ / {' '}
                            {result.raw_transcription.audio_features.prosody.intonation.filter((i: any) => i.direction === 'falling').length} ↘️
                          </div>
                          <div style={{ fontSize: '0.8rem', opacity: 0.8 }}>Variazioni pitch</div>
                        </div>
                      )}
                      {result.raw_transcription.audio_features.prosody.stress && result.raw_transcription.audio_features.prosody.stress.length > 0 && (
                        <div>
                          <div style={{ opacity: 0.9, marginBottom: '0.25rem' }}>Enfasi/Accenti</div>
                          <div style={{ fontSize: '1.1rem', fontWeight: 'bold' }}>
                            {result.raw_transcription.audio_features.prosody.stress.filter((s: any) => s.level === 'strong').length} forti
                          </div>
                          <div style={{ fontSize: '0.8rem', opacity: 0.8 }}>
                            {result.raw_transcription.audio_features.prosody.stress.length} totali
                          </div>
                        </div>
                      )}
                      {result.raw_transcription.audio_features.prosody.syllable_duration && result.raw_transcription.audio_features.prosody.syllable_duration.length > 0 && (
                        <div>
                          <div style={{ opacity: 0.9, marginBottom: '0.25rem' }}>Durata Sillabe</div>
                          <div style={{ fontSize: '1.1rem', fontWeight: 'bold' }}>
                            {(result.raw_transcription.audio_features.prosody.syllable_duration.reduce((sum: number, d: any) => sum + (d.duration || 0), 0) / result.raw_transcription.audio_features.prosody.syllable_duration.length).toFixed(2)}s
                          </div>
                          <div style={{ fontSize: '0.8rem', opacity: 0.8 }}>Media durata</div>
                        </div>
                      )}
                      {result.raw_transcription.audio_features.prosody.pauses && result.raw_transcription.audio_features.prosody.pauses.length > 0 && (
                        <div>
                          <div style={{ opacity: 0.9, marginBottom: '0.25rem' }}>Pause</div>
                          <div style={{ fontSize: '1.1rem', fontWeight: 'bold' }}>
                            {result.raw_transcription.audio_features.prosody.pauses.length}
                          </div>
                          <div style={{ fontSize: '0.8rem', opacity: 0.8 }}>Silenzi/Respiro</div>
                        </div>
                      )}
                      {result.raw_transcription.audio_features.prosody.dynamics && result.raw_transcription.audio_features.prosody.dynamics.length > 0 && (
                        <div>
                          <div style={{ opacity: 0.9, marginBottom: '0.25rem' }}>Dinamica</div>
                          <div style={{ fontSize: '1.1rem', fontWeight: 'bold' }}>
                            {result.raw_transcription.audio_features.prosody.dynamics.filter((d: any) => d.level === 'loud').length} forte
                          </div>
                          <div style={{ fontSize: '0.8rem', opacity: 0.8 }}>Variazioni volume</div>
                        </div>
                      )}
                      {result.raw_transcription.audio_features.prosody.articulation && (
                        <div>
                          <div style={{ opacity: 0.9, marginBottom: '0.25rem' }}>Articolazione</div>
                          <div style={{ fontSize: '1.1rem', fontWeight: 'bold' }}>
                            {result.raw_transcription.audio_features.prosody.articulation.quality === 'clear' ? '🔊 Chiara' : 
                             result.raw_transcription.audio_features.prosody.articulation.quality === 'smooth' ? '🎵 Fluida' : '🔇 Soffusa'}
                          </div>
                          <div style={{ fontSize: '0.8rem', opacity: 0.8 }}>Qualità voce</div>
                        </div>
                      )}
                      {result.raw_transcription.audio_features.prosody.vibrato?.present && (
                        <div>
                          <div style={{ opacity: 0.9, marginBottom: '0.25rem' }}>Vibrato</div>
                          <div style={{ fontSize: '1.1rem', fontWeight: 'bold' }}>
                            ✓ Presente
                          </div>
                          <div style={{ fontSize: '0.8rem', opacity: 0.8 }}>
                            Intensità: {(result.raw_transcription.audio_features.prosody.vibrato.intensity * 100).toFixed(1)}%
                          </div>
                        </div>
                      )}
                      {result.raw_transcription.audio_features.prosody.portamento && result.raw_transcription.audio_features.prosody.portamento.length > 0 && (
                        <div>
                          <div style={{ opacity: 0.9, marginBottom: '0.25rem' }}>Portamento</div>
                          <div style={{ fontSize: '1.1rem', fontWeight: 'bold' }}>
                            {result.raw_transcription.audio_features.prosody.portamento.length}
                          </div>
                          <div style={{ fontSize: '0.8rem', opacity: 0.8 }}>Transizioni fluide</div>
                        </div>
                      )}
                    </div>
                    <div style={{ marginTop: '1rem', padding: '0.75rem', background: 'rgba(255,255,255,0.15)', borderRadius: '6px', fontSize: '0.85rem', fontStyle: 'italic' }}>
                      💡 La prosodia analizza il modo in cui è detta la parola: intonazione, enfasi, durata, pause, dinamica, articolazione, vibrato e portamento. Queste informazioni aiutano a generare testo che si adatta perfettamente all'andamento vocale.
                    </div>
                  </div>
                )}
              </div>
            )}

            {result.vocal_segments_count !== undefined && result.vocal_segments_count > 0 && (
              <div style={{ marginTop: '2rem' }}>
                <h2 style={{ marginBottom: '0.5rem' }}>🎤 Sezioni Vocali Rilevate</h2>
                <div style={{ 
                  background: '#f0f4ff', 
                  padding: '1rem', 
                  borderRadius: '8px',
                  marginBottom: '1rem'
                }}>
                  <div style={{ marginBottom: '0.5rem' }}>
                    <strong>Sezioni trovate:</strong> {result.vocal_segments_count}
                    {result.raw_transcription.vocal_percentage && (
                      <span> ({result.raw_transcription.vocal_percentage.toFixed(1)}% del brano)</span>
                    )}
                  </div>
                  {result.vocal_segments && result.vocal_segments.length > 0 && (
                    <div style={{ fontSize: '0.9rem', color: '#666' }}>
                      <strong>Timing:</strong> {result.vocal_segments.slice(0, 10).map(([s, e], i) => (
                        <span key={i} style={{ marginRight: '0.5rem' }}>
                          {i + 1}: {s.toFixed(1)}s-{e.toFixed(1)}s
                        </span>
                      ))}
                      {result.vocal_segments.length > 10 && `... (+${result.vocal_segments.length - 10} altre)`}
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Statistiche Pulizia Testo */}
            {result.raw_transcription.cleaning_stats && (
              <div style={{ marginTop: '2rem' }}>
                <h2 style={{ marginBottom: '0.5rem' }}>🧹 Pulizia e Filtraggio Testo</h2>
                <div style={{ 
                  background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)', 
                  padding: '1.5rem', 
                  borderRadius: '12px',
                  color: 'white',
                  marginBottom: '1rem'
                }}>
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', gap: '1rem' }}>
                    {result.raw_transcription.cleaning_stats.removed_sentences !== undefined && (
                      <div>
                        <div style={{ fontSize: '0.85rem', opacity: 0.9, marginBottom: '0.25rem' }}>Ripetizioni Rimosse</div>
                        <div style={{ fontSize: '1.5rem', fontWeight: 'bold' }}>
                          {result.raw_transcription.cleaning_stats.removed_sentences}
                        </div>
                      </div>
                    )}
                    {result.raw_transcription.cleaning_stats.reduction_percent !== undefined && (
                      <div>
                        <div style={{ fontSize: '0.85rem', opacity: 0.9, marginBottom: '0.25rem' }}>Riduzione</div>
                        <div style={{ fontSize: '1.5rem', fontWeight: 'bold' }}>
                          {result.raw_transcription.cleaning_stats.reduction_percent.toFixed(1)}%
                        </div>
                      </div>
                    )}
                    {result.raw_transcription.quality?.quality_score !== undefined && (
                      <div>
                        <div style={{ fontSize: '0.85rem', opacity: 0.9, marginBottom: '0.25rem' }}>Qualità Testo</div>
                        <div style={{ fontSize: '1.5rem', fontWeight: 'bold' }}>
                          {result.raw_transcription.quality.quality_score.toFixed(1)}/100
                        </div>
                      </div>
                    )}
                    {result.raw_transcription.cleaning_stats.cleaned_sentences !== undefined && (
                      <div>
                        <div style={{ fontSize: '0.85rem', opacity: 0.9, marginBottom: '0.25rem' }}>Frasi Finali</div>
                        <div style={{ fontSize: '1.5rem', fontWeight: 'bold' }}>
                          {result.raw_transcription.cleaning_stats.cleaned_sentences}
                        </div>
                      </div>
                    )}
                  </div>
                  {result.raw_transcription.quality && (
                    <div style={{ marginTop: '1rem', padding: '0.75rem', background: 'rgba(255,255,255,0.15)', borderRadius: '6px', fontSize: '0.9rem' }}>
                      {result.raw_transcription.quality.is_good_quality ? (
                        <span>✅ Testo di buona qualità</span>
                      ) : (
                        <span>⚠️ Testo con molte ripetizioni (rimosso {result.raw_transcription.cleaning_stats?.removed_sentences || 0} ripetizioni)</span>
                      )}
                      {result.raw_transcription.quality.repetition_ratio && (
                        <span> • Rapporto ripetizioni: {result.raw_transcription.quality.repetition_ratio.toFixed(2)}x</span>
                      )}
                    </div>
                  )}
                </div>
              </div>
            )}

            <div style={{ marginTop: '2rem' }}>
              <h2 style={{ marginBottom: '0.5rem' }}>📝 Trascrizione Grezza</h2>
              <div className="text-output">
                {result.raw_transcription.text || '(Nessuna trascrizione disponibile)'}
              </div>
              {result.raw_transcription.cleaned_text && result.raw_transcription.cleaned_text !== result.raw_transcription.text && (
                <div style={{ marginTop: '1rem' }}>
                  <h3 style={{ marginBottom: '0.5rem', fontSize: '1rem' }}>📝 Testo Pulito (dopo rimozione ripetizioni)</h3>
                  <div className="text-output" style={{ background: '#f0f4ff', padding: '1rem', borderRadius: '8px' }}>
                    {result.raw_transcription.cleaned_text}
                  </div>
                </div>
              )}
              <div style={{ fontSize: '0.9rem', color: '#666', marginTop: '0.5rem' }}>
                Lingua: {result.raw_transcription.language} | 
                Confidenza: {(result.raw_transcription.confidence * 100).toFixed(1)}% | 
                Parole chiare: {result.raw_transcription.has_clear_words ? 'Sì' : 'No'}
                {result.vocal_segments_count !== undefined && (
                  <> | Sezioni vocali: {result.vocal_segments_count}</>
                )}
              </div>
            </div>

            {result.raw_transcription.phonemes && (
              <div style={{ marginTop: '1rem' }}>
                <h3 style={{ marginBottom: '0.5rem' }}>🔊 Fonemi Rilevati</h3>
                <div className="text-output" style={{ fontSize: '0.9rem' }}>
                  {result.raw_transcription.phonemes}
                </div>
              </div>
            )}

            <div style={{ marginTop: '2rem' }}>
              <h2 style={{ marginBottom: '0.5rem' }}>✨ Testo Finale Generato (Inglese)</h2>
              
              {result.lyrics_variants && result.lyrics_variants.variants.length > 1 ? (
                <div>
                  <div style={{ 
                    marginBottom: '1rem',
                    padding: '0.75rem',
                    background: '#f0f4ff',
                    borderRadius: '8px',
                    fontSize: '0.9rem',
                    color: '#667eea'
                  }}>
                    📝 {result.lyrics_variants.total} varianti generate - Seleziona quella che preferisci:
                  </div>
                  
                  <div style={{ display: 'grid', gap: '1rem', marginBottom: '1rem' }}>
                    {result.lyrics_variants.variants.map((variant, idx) => (
                      <div
                        key={variant.id}
                        onClick={() => {
                          const newResult = { ...result }
                          if (newResult.lyrics_variants) {
                            newResult.lyrics_variants.selected = idx
                            newResult.final_text = variant.full_text
                          }
                          setResult(newResult)
                        }}
                        style={{
                          background: result.lyrics_variants?.selected === idx ? '#fff' : '#f8f9fa',
                          border: `2px solid ${result.lyrics_variants?.selected === idx ? '#667eea' : '#e0e0e0'}`,
                          borderRadius: '12px',
                          padding: '1.5rem',
                          cursor: 'pointer',
                          transition: 'all 0.3s',
                          boxShadow: result.lyrics_variants?.selected === idx ? '0 4px 6px rgba(102, 126, 234, 0.2)' : 'none'
                        }}
                      >
                        <div style={{ 
                          display: 'flex', 
                          justifyContent: 'space-between', 
                          alignItems: 'center',
                          marginBottom: '0.5rem'
                        }}>
                          <strong style={{ color: '#667eea' }}>Variante {variant.id}</strong>
                          {result.lyrics_variants?.selected === idx && (
                            <span style={{ color: '#667eea', fontWeight: 'bold' }}>✓ Selezionata</span>
                          )}
                        </div>
                        <div style={{ 
                          whiteSpace: 'pre-wrap', 
                          lineHeight: '1.8', 
                          fontSize: '1rem',
                          color: '#333',
                          fontFamily: 'Georgia, serif'
                        }}>
                          {variant.full_text}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              ) : (
                <div style={{ 
                  background: '#fff', 
                  border: '2px solid #667eea', 
                  borderRadius: '12px', 
                  padding: '1.5rem', 
                  marginBottom: '1rem',
                  boxShadow: '0 4px 6px rgba(102, 126, 234, 0.1)'
                }}>
                  <div style={{ 
                    whiteSpace: 'pre-wrap', 
                    lineHeight: '1.8', 
                    fontSize: '1.1rem',
                    color: '#333',
                    fontFamily: 'Georgia, serif'
                  }}>
                    {result.final_text || '(Nessun testo generato)'}
                  </div>
                </div>
              )}
              
              <div style={{ 
                fontSize: '0.85rem', 
                color: '#666', 
                fontStyle: 'italic',
                padding: '0.5rem',
                background: '#f8f9fa',
                borderRadius: '6px'
              }}>
                💡 Questo testo è stato generato analizzando pitch, timing, ritmo e metrica della melodia per adattarsi perfettamente alla musica.
              </div>
            </div>

            {italianTranslation && (
              <div style={{ marginTop: '2rem' }}>
                <h2 style={{ marginBottom: '0.5rem' }}>🇮🇹 Traduzione Italiana</h2>
                <div style={{
                  background: '#fff',
                  border: '2px solid #28a745',
                  borderRadius: '12px',
                  padding: '1.5rem',
                  marginBottom: '1rem',
                  boxShadow: '0 4px 6px rgba(40, 167, 69, 0.1)'
                }}>
                  <div style={{
                    whiteSpace: 'pre-wrap',
                    lineHeight: '1.8',
                    fontSize: '1.1rem',
                    color: '#333',
                    fontFamily: 'Georgia, serif'
                  }}>
                    {italianTranslation}
                  </div>
                </div>
              </div>
            )}

            <div style={{ marginTop: '1rem', display: 'flex', gap: '1rem' }}>
              <button onClick={downloadText} className="button">
                💾 Scarica Testo
              </button>
            </div>
          </div>
        )}
      </div>

      <div className="card" style={{ background: '#f8f9fa' }}>
        <h3 style={{ marginBottom: '1rem' }}>ℹ️ Come funziona</h3>
        <ol style={{ lineHeight: '1.8', paddingLeft: '1.5rem' }}>
          <li>Carica un file audio (MP3, WAV, M4A, FLAC)</li>
          <li>Il sistema isola la traccia vocale</li>
          <li>Analizza pitch, timing, ritmo e metrica</li>
          <li>Whisper trascrive i suoni vocali (parole o fonemi)</li>
          <li>L'IA genera testo in inglese che si adatta perfettamente alla melodia</li>
          <li>Scarica il testo e la traccia vocale isolata</li>
        </ol>
      </div>
    </main>
  )
}
