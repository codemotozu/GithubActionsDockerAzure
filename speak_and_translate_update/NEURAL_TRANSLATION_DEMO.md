# Neural Translation Demo - Word-by-Word Translation with Multiple Formality Levels

## Overview
This app implements advanced neural machine translation with **billions of examples** from pre-trained transformers, providing:

✅ **Transformer architecture** with encoder-decoder  
✅ **Bidirectional RNN** for context understanding  
✅ **Multi-head attention** mechanism  
✅ **Word vectorization** with contextual embeddings  
✅ **Multiple formality levels** (native, colloquial, informal, formal)  
✅ **Word-by-word audio** with perfect UI synchronization  
✅ **Cultural adaptation** for context, grammar, and natural flow  

## Example Translation Scenario

**Input:** "Jugo de piña para la niña y jugo de mora para la señora porque están en el hospital y afuera está lloviendo."

**Settings Configuration:**
```
Mother Tongue: Spanish [🇪🇸]
German Native: [X]
German Formal: [X] 
Word-by-word Audio: [X]
Neural Networks: [X]
Cultural Adaptation: [X]
```

## Expected Output

### German Native
**Full sentence (native):**
„Ananassaft für das Mädchen und Brombeersaft für die Dame, weil sie im Krankenhaus sind und draußen regnet es."

**Word by word (with audio):**
• Ananassaft → jugo de piña (Saft = jugo, Ananas = piña)
• für → para
• das Mädchen → la niña (Mädchen = niña)
• und → y
• Brombeersaft → jugo de mora (Brombeere = mora, Saft = jugo)
• für → para
• die Dame → la señora (Dame = dama, señora)
• weil → porque
• sie → ellos/ellas
• im Krankenhaus → en el hospital (Krankenhaus = hospital, krank = enfermo, Haus = casa)
• sind → están (del verbo sein = ser/estar)
• und → y
• draußen → afuera (literalmente: en el exterior)
• regnet es → está lloviendo (regnet = llueve, es = ello)

---

### German Formal
**Full sentence (formal):**
„Ananassaft für das Kind und Brombeersaft für die verehrte Frau, da sie sich im Krankenhaus befinden und es draußen regnet."

**Word by word (with audio):**
• Ananassaft → jugo de piña
• für → para
• das Kind → el/la niño/a (Kind = niño)
• und → y
• Brombeersaft → jugo de mora
• für → para
• die verehrte Frau → la señora (verehrte = respetada/honorable, Frau = mujer, señora)
• da → porque (formal, más elegante que weil)
• sie sich → ellos/ellas se
• im Krankenhaus → en el hospital
• befinden → se encuentran (verbo formal para "estar ubicados")
• und → y
• es → ello
• draußen → afuera
• regnet → llueve

## Neural Architecture Features

### 1. Transformer Encoder with CNN and BiLSTM
```python
# Text → Character Recognition (CNN) → BiLSTM → Transformer Encoding
embedded = self.embedding(x) * math.sqrt(self.d_model)
cnn_output = F.relu(self.char_cnn(embedded.transpose(1, 2)))
lstm_output, _ = self.bilstm(combined)
transformer_output = self.transformer(lstm_output)
```

### 2. Multi-Head Attention for Context
```python
# Looking both forward and backward for context
scores = torch.matmul(Q, K.transpose(-2, -1)) / math.sqrt(self.d_k)
attention_weights = F.softmax(scores, dim=-1)
context = torch.matmul(attention_weights, V)
```

### 3. Decoder with Stacked LSTMs
```python
# Stacked LSTM-RNNs as requested in requirements
for lstm in self.stacked_lstms:
    lstm_output, _ = lstm(lstm_output)
    lstm_output = F.dropout(lstm_output, 0.1, self.training)
```

## Cultural Context Integration

The system handles:
- **Phrasal verbs**: "regnet es" → "está lloviendo" (German verb-subject inversion)
- **Separable verbs**: Compound German verbs treated as semantic units
- **Cultural nuances**: "Dame" vs "Frau" for formality levels
- **Regional variations**: German formal "da" vs colloquial "weil"

## Technical Implementation

### Word Vectorization (Billions of Examples)
```python
# Uses pre-trained models with billions of examples
self.xlm_roberta_model = XLMRobertaModel.from_pretrained('xlm-roberta-base')
self.sentence_transformer = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')

# Creates contextual word vectors
word_vectors = await self.create_word_vectors(text, language)
sentence_embedding = self.sentence_model.encode([text])[0]
```

### Statistical + Neural Hybrid
```python
# Combines Neural Machine Translation with Statistical Machine Translation
neural_translation = await self.translate_with_neural_network(...)
if neural_fails:
    fallback_translation = await self.smt_translate(...)
```

### Perfect UI-Audio Synchronization
- **Exact Format Match**: What you see = What you hear
- **Semantic Grouping**: Compound words stay together in audio
- **Context Preservation**: Explanations maintain meaning relationships

## API Usage

### Request Example
```json
{
  "text": "Jugo de piña para la niña y jugo de mora para la señora porque están en el hospital y afuera está lloviendo.",
  "source_lang": "spanish",
  "target_lang": "multi",
  "style_preferences": {
    "german_native": true,
    "german_formal": true,
    "german_word_by_word": true,
    "use_neural_networks": true,
    "enable_cultural_adaptation": true,
    "mother_tongue": "spanish"
  }
}
```

### Response Example
```json
{
  "original_text": "Jugo de piña...",
  "translated_text": "Ananassaft für das Mädchen...",
  "translations": {
    "german_native": "„Ananassaft für das Mädchen..."",
    "german_formal": "„Ananassaft für das Kind...""
  },
  "word_by_word": {
    "ananassaft": {
      "spanish": "jugo de piña",
      "explanation": "Saft = jugo, Ananas = piña"
    }
  },
  "neural_models_used": ["transformer", "encoder-decoder", "bidirectional-rnn", "attention"],
  "semantic_analysis": {
    "cultural_markers": ["hospital", "señora"],
    "morphological_complexity": 2.3
  }
}
```

## Settings Screen Integration

The Flutter UI provides complete control over:

**Neural Translation Engine:**
- ✅ Attention Visualization
- ✅ Cultural Adaptation  
- ✅ Semantic Consistency
- ✅ Formality Preservation

**Language Styles:**
- 🇩🇪 German: Native, Colloquial, Informal, Formal
- 🇺🇸 English: Native, Colloquial, Informal, Formal
- 🎵 Word-by-word Audio for both languages

**Advanced Options:**
- Temperature: 0.1-1.5 (creativity control)
- Context Window: 128-2048 tokens
- Top-K: 10-100 (word selection)
- Top-P: 0.5-1.0 (probability threshold)

## Performance Optimizations

1. **Model Caching**: Pre-trained models loaded once
2. **Translation Cache**: Frequent phrases cached
3. **Batch Processing**: Multiple requests processed together  
4. **Attention Optimization**: Efficient matrix operations
5. **Memory Management**: Smart cleanup of embeddings

## Supported Language Combinations

Based on mother tongue selection:
- **Spanish** → German (Native/Formal/Informal/Colloquial) + English
- **English** → German + Spanish (automatic)
- **German** → English + Spanish (automatic)

All combinations support word-by-word audio with perfect synchronization.