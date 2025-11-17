'use client'

import { useState } from 'react'
import axios from 'axios'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

interface TranscriptionResult {
  job_id: string
  status: string
  vocal_audio_url: string
  raw_transcription: {
    text: string
    phonemes: string
    language: string
    confidence: number
    has_clear_words: boolean
    vocal_segments?: Array<[number, number]>
    vocal_segments_count?: number
    vocal_percentage?: number
  }
  final_text: string
  vocal_segments?: Array<[number, number]>
  vocal_segments_count?: number
  message: string
}

interface JobStatus {
  status: string
  step: number
  total_steps: number
  current_step: string
  progress: number
}

export default function Home() {
  const [file, setFile] = useState<File | null>(null)
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<TranscriptionResult | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [vocalAudioUrl, setVocalAudioUrl] = useState<string | null>(null)
  const [jobStatus, setJobStatus] = useState<JobStatus | null>(null)
  const [currentJobId, setCurrentJobId] = useState<string | null>(null)

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0])
      setError(null)
      setResult(null)
      setVocalAudioUrl(null)
    }
  }

  const handleUpload = async () => {
    if (!file) {
      setError('Seleziona un file audio prima di procedere')
      return
    }

    setLoading(true)
    setError(null)
    setResult(null)
    setVocalAudioUrl(null)
    setJobStatus(null)
    setCurrentJobId(null)

    try {
      const formData = new FormData()
      formData.append('file', file)

      const response = await axios.post<TranscriptionResult>(
        `${API_URL}/upload`,
        formData,
        {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
        }
      )

      setCurrentJobId(response.data.job_id)
      
      // Polling per lo stato del job
      const pollStatus = async () => {
        try {
          const statusResponse = await axios.get<JobStatus>(
            `${API_URL}/status/${response.data.job_id}`
          )
          setJobStatus(statusResponse.data)
          
          if (statusResponse.data.status === 'completed') {
            setResult(response.data)
            if (response.data.vocal_audio_url) {
              const audioUrl = `${API_URL}${response.data.vocal_audio_url}`
              setVocalAudioUrl(audioUrl)
            }
            setLoading(false)
          } else {
            // Continua il polling ogni 500ms
            setTimeout(pollStatus, 500)
          }
        } catch (err) {
          // Se il job è completato, usa i dati della risposta originale
          setResult(response.data)
          if (response.data.vocal_audio_url) {
            const audioUrl = `${API_URL}${response.data.vocal_audio_url}`
            setVocalAudioUrl(audioUrl)
          }
          setLoading(false)
        }
      }
      
      // Inizia il polling dopo un breve delay
      setTimeout(pollStatus, 500)
      
    } catch (err: any) {
      setError(
        err.response?.data?.detail || 
        err.message || 
        'Errore durante il processamento del file'
      )
      console.error('Errore upload:', err)
      setLoading(false)
    }
  }

  const downloadText = () => {
    if (!result) return

    const content = `=== TESTO GENERATO ===\n\n` +
      `Trascrizione grezza:\n${result.raw_transcription.text}\n\n` +
      `Fonemi rilevati:\n${result.raw_transcription.phonemes}\n\n` +
      `Testo finale:\n${result.final_text}\n\n` +
      `Lingua: ${result.raw_transcription.language}\n` +
      `Confidenza: ${(result.raw_transcription.confidence * 100).toFixed(1)}%\n`

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
    a.download = `vocale_isolata_${result?.job_id || 'audio'}.wav`
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
          disabled={!file || loading}
          className="button"
          style={{ width: '100%', marginBottom: '1rem' }}
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
                {jobStatus.step === 0 && '⏳ Rilevamento sezioni vocali in corso...'}
                {jobStatus.step === 1 && '⏳ Separazione vocale in corso...'}
                {jobStatus.step === 2 && '⏳ Trascrizione Whisper in corso... (può richiedere 30-60 secondi)'}
                {jobStatus.step === 3 && '⏳ Generazione testo creativo in corso...'}
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

            {vocalAudioUrl && (
              <div style={{ marginTop: '1rem' }}>
                <h2 style={{ marginBottom: '0.5rem' }}>🎤 Traccia Vocale Isolata</h2>
                <audio controls src={vocalAudioUrl} className="audio-player" />
                <button onClick={downloadAudio} className="button" style={{ marginTop: '0.5rem' }}>
                  💾 Scarica Audio Vocale
                </button>
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

            <div style={{ marginTop: '2rem' }}>
              <h2 style={{ marginBottom: '0.5rem' }}>📝 Trascrizione Grezza</h2>
              <div className="text-output">
                {result.raw_transcription.text || '(Nessuna trascrizione disponibile)'}
              </div>
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
              <h2 style={{ marginBottom: '0.5rem' }}>✨ Testo Finale Generato</h2>
              <div className="text-output">
                {result.final_text}
              </div>
            </div>

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
          <li>Il sistema isola la traccia vocale usando Demucs</li>
          <li>Whisper trascrive i suoni vocali (parole o fonemi)</li>
          <li>L'IA genera un testo creativo basato sui suoni rilevati</li>
          <li>Scarica il testo e la traccia vocale isolata</li>
        </ol>
      </div>
    </main>
  )
}

