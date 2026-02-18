# AI Digest Bot

AI-powered Telegram summarization bot using local LLMs (Llama3 via Ollama).

## Problem
Telegram users consume large volumes of content and experience information overload.

## Solution
AI Digest automatically classifies text (travel/news/work) and generates structured summaries.

## Features
- Auto mode detection
- Structured digest output
- LLM routing (fast vs full model)
- Post-processing cleanup layer
- Save to Markdown

## Tech Stack
- Python
- python-telegram-bot
- Ollama (Llama3)

## Architecture
User → handlers → detection → summarizer → llm → cleaning → response

## Limitations

- Local LLM latency may vary depending on hardware
- Classification may fail on edge-case mixed content
- No persistent user-level personalization yet

## Roadmap

- Feedback loop (like/dislike summaries)
- Model evaluation comparison
- Batch digest mode
- Topic clustering


## How to run
1. Install Ollama
2. Pull model: llama3
3. Create .env file
4. Run: python bot.py
