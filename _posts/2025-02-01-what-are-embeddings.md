---
layout: friendly-explainer
title: "What Are Embeddings? A Friendly Guide"
date: 2025-02-01
tags: [embeddings, NLP, beginner-friendly]
description: "A gentle introduction to word and sentence embeddings in machine learning."
tldr: "Embeddings are numerical representations of words or concepts that capture meaning. Similar words end up close together in this number space. They power search, recommendations, and modern AI."
---

## The Big Picture

Imagine you could turn any word into a list of numbers — and these numbers actually capture the *meaning* of the word. That's what embeddings do!

The word "king" might become `[0.2, 0.8, -0.3, ...]`, and "queen" might become `[0.21, 0.79, -0.28, ...]`. Notice they're close? That's because they have similar meanings.

## Why Do We Need Embeddings?

Computers don't understand words — they understand numbers. But not all number representations are created equal.

### The Old Way: One-Hot Encoding

In the old days, "cat" = `[1, 0, 0, ...]` and "dog" = `[0, 1, 0, ...]`. The problem? These vectors tell the computer nothing about how "cat" and "dog" are related.

### The New Way: Dense Embeddings

With embeddings, "cat" and "dog" end up near each other in vector space because they share many properties (animals, pets, four legs).

## How Are Embeddings Created?

The key insight: **you can learn word meanings from context.** If "cat" and "dog" appear in similar sentences, they must mean similar things.

> "You shall know a word by the company it keeps." — J.R. Firth, 1957

This idea led to Word2Vec (2013), GloVe (2014), and eventually the contextual embeddings in BERT and GPT.

## Practical Applications

- **Search engines** — Find documents that match the *meaning* of your query
- **Recommendations** — "Users who liked X also liked Y"
- **Clustering** — Group similar items together automatically
- **Translation** — Map concepts across languages

## Key Takeaway

Embeddings are one of the most important ideas in modern AI. They turn fuzzy human concepts into precise mathematical objects that computers can work with. Once you understand embeddings, a lot of AI suddenly makes sense!
