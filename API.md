# API

## POST /translate

Translate a list of sentences from a source language to a target language.

### Request Snippet

```bash
curl -XPOST http://localhost:24080/translate \
  -H 'content-type: application/json' \
  -d '{
    "text": ["hello"],
    "target_lang": "pt-BR",
    "source_lang": "en"
  }'
```

## GET /translate

Translate a single sentence or a list of sentences from a source language to a target language.

### Request Snippet

```bash
curl -XGET http://localhost:24080/translate?target_lang=pt-BR&source_lang=en&text=hello&text=world
```