# Evaluation

## Storage choice

- Current dataset: 143 saved links, with 104 indexed into 2,206 chunks.
- Keep Chroma: it provides vector storage, metadata filtering, and local persistence with little setup. Query speed is acceptable for current use.
- Why not FAISS: FAISS supports saving and loading vector indexes, but metadata storage and mappings between vectors and documents would require additional management.
- Revisit this choice if query latency or memory usage becomes a problem as the dataset grows. Benchmark alternatives before deciding whether to switch.