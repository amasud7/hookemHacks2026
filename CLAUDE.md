# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Multimodal short-form content search engine** — built for HookEm Hacks 2026 at UT Austin.

The core problem: people recall short-form content (TikToks, Reels, YouTube Shorts, etc.) by vibes and conversational descriptions, not keywords. Existing search (Google keyword matching, TikTok search) doesn't handle natural-language recall well. This project lets users describe content in conversational language and searches across multiple social media platforms, handling multiple modalities: video, audio, slideshows, and regular posts.

## Architecture

- **Content scraping**: Apify actors for pulling content from social media platforms
- **Embedding**: Google Gemini Embeddings 2 for multimodal content embedding (text, video, audio)
- **Vector store**: MongoDB Atlas Vector Search for storing and querying embeddings
- **Search**: Semantic similarity search over embedded content using the conversational query

Pipeline: user query → embed query → vector similarity search (MongoDB Atlas) against pre-embedded content pool → ranked results across platforms and modalities.

## Key Technical Decisions

- Apify handles platform-specific scraping complexity (rate limits, auth, format differences)
- Gemini Embeddings 2 chosen for native multimodal support (single model handles text + video + audio embeddings)
- MongoDB Atlas Vector Search for vector storage and retrieval (hackathon sponsor)
- Cross-platform search from a single natural-language input
