# ⚡ Ottimizzazioni Velocità

## 🐌 Perché è lento?

Il processamento può essere lento per diversi motivi:

### 1. Whisper (Trascrizione)
- **Modello "base"**: ~74MB, più accurato ma più lento
- **Modello "tiny"**: ~39MB, più veloce ma meno accurato
- **Prima volta**: Scarica il modello (1-2 minuti)
- **Trascrizione**: 1-2 minuti per file di 2-3 minuti

### 2. Separazione Vocale
- Metodo fallback: veloce (~5-10 secondi)
- Demucs: più lento ma più accurato (richiede FFmpeg)

### 3. Generazione Testo
- Con OpenAI API: veloce (~5-10 secondi)
- Senza API: veloce (~1-2 secondi)

## ⚡ Ottimizzazioni Applicate

### Modello Whisper più piccolo
- **Cambiato da "base" a "tiny"**
- Velocità: ~2-3x più veloce
- Accuratezza: leggermente inferiore ma ancora buona

### Parametri Whisper ottimizzati
- `beam_size=1` (invece di 5) → più veloce
- `best_of=1` (invece di 5) → più veloce
- `temperature=0` → più veloce e deterministica

## 📊 Tempi Attesi (Dopo Ottimizzazioni)

### File 2.5 minuti
- **Separazione vocale**: ~5-10 secondi
- **Whisper (prima volta)**: ~30-60 secondi (scarica modello tiny ~39MB)
- **Whisper trascrizione**: ~30-60 secondi (con modello tiny)
- **Generazione testo**: ~5-10 secondi

**Totale**: ~1-2 minuti (prima volta), ~40-80 secondi (volte successive)

## 🔧 Modelli Whisper Disponibili

| Modello | Dimensione | Velocità | Accuratezza | Uso |
|---------|-----------|----------|-------------|-----|
| tiny    | ~39 MB    | ⚡⚡⚡⚡⚡ | ⭐⭐⭐ | **Attuale** - Veloce |
| base    | ~74 MB    | ⚡⚡⚡    | ⭐⭐⭐⭐ | Bilanciato |
| small   | ~244 MB   | ⚡⚡      | ⭐⭐⭐⭐⭐ | Accurato |
| medium  | ~769 MB   | ⚡        | ⭐⭐⭐⭐⭐ | Molto accurato |
| large   | ~1550 MB  | 🐌        | ⭐⭐⭐⭐⭐ | Massima accuratezza |

## 💡 Per Cambiare Modello

Modifica `backend/transcription.py`:
```python
model_name: str = "tiny"  # Cambia con: "base", "small", "medium", "large"
```

## 🎯 Trade-off

- **tiny**: Veloce ma meno accurato su accenti/cantato
- **base**: Bilanciato (consigliato per la maggior parte dei casi)
- **small+**: Più accurato ma molto più lento

## 📝 Note

- La prima volta è sempre più lenta (download modello)
- File più lunghi richiedono più tempo
- La qualità audio influisce sulla velocità

