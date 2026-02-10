# Building an embedded knowledge graph library in Go for AI agents

An embedded, file-system-backed knowledge graph library in Go is both technically feasible and architecturally well-supported by the existing ecosystem. The recommended approach: build a **property graph model on top of Pebble** (CockroachDB's LSM-tree storage engine), with composite key encoding for efficient traversal, bidirectional edge indexes, temporal versioning, and a serialization layer that converts subgraphs into LLM-ready context. This architecture draws directly from production patterns in Dgraph, TuGraph, Cayley, and Graphiti — all of which demonstrate how to map graph structures onto key-value stores effectively. The Go ecosystem provides every building block needed: battle-tested embedded storage engines, graph algorithm libraries, and LLM integration frameworks.

---

## How knowledge graphs differ from RAG and why agents need both

Traditional RAG operates on **unstructured text chunks** retrieved by vector similarity — the query is embedded, the top-k semantically similar passages are fetched, and an LLM generates an answer from those passages. Knowledge graphs store information as **structured networks of entities and relationships**, where each connection carries explicit semantic meaning. The difference is fundamental: RAG finds *similar* text while KGs traverse *connected* facts.

This distinction matters for AI agents in three concrete ways. First, **multi-hop reasoning** — answering "Which suppliers are connected to products affected by Regulation X?" requires following chains of typed relationships (Policy → Department → Project → Supplier). RAG retrieves disconnected passages and leaves the LLM to infer connections, which fails as hop count increases. Second, **structured analytical queries** — filtering, aggregation, and sorting ("Which company with a solo founder has the highest valuation?") are native graph operations but nearly impossible with vector similarity. Third, **disambiguation** — "Apple" as a company versus fruit is resolved by typed nodes and explicit relationship graphs, not embedding distance.

The emerging production pattern is **dual-channel retrieval**: one channel performs vector similarity search on text chunks while the other performs graph traversal. Results merge via Reciprocal Rank Fusion into unified LLM context. Microsoft's GraphRAG, Graphiti (by Zep), and Cognee all implement variants of this hybrid approach, consistently showing **70–80% improvement in comprehensiveness** over naive RAG for questions requiring cross-document synthesis.

### Property graph vs RDF: which model to implement

Two dominant data models exist for knowledge graphs. **RDF triples** express every fact as `(subject, predicate, object)` with URI identifiers, backed by W3C standards (SPARQL, OWL, SHACL) that enable automated inference. **Property graphs** store nodes with labels and key-value properties, connected by directed, labeled edges that also carry properties.

For an AI agent knowledge graph library, **property graphs are the clear choice**. Three factors drive this:

- **Rich relationship metadata is trivial.** Agent memory requires timestamps, confidence scores, and provenance on relationships. In a property graph: `(Alice)-[:WORKS_FOR {since: "2020-01-15", confidence: 0.95}]->(Acme)`. In RDF, this requires reification — creating extra nodes and triples, which is cumbersome and slow.
- **Performance for traversal.** Property graphs support index-free adjacency (each node directly references its neighbors), delivering millisecond multi-hop queries. RDF triple stores must reconstruct context from individual triples, adding overhead that grows with graph density.
- **Schema flexibility for dynamic knowledge.** AI agents build and extend graphs dynamically from LLM extraction. Property graphs accommodate new node types, edge types, and properties without migration or predefined ontologies.

RDF remains valuable for cross-organizational data integration with shared ontologies (biomedical domains using SNOMED, Gene Ontology) and when formal inference is required. But for an embedded library targeting agent memory and reasoning, property graphs provide the right balance of expressiveness, performance, and simplicity.

---

## The landscape of existing tools and Go libraries

### Go-native embeddable graph databases

Two Go projects stand out as direct architectural references. **Cayley** (~15K GitHub stars, Apache-2.0) is Google-inspired and implements a quad store (subject-predicate-object-label) with swappable backends including BoltDB, LevelDB, and in-memory. It is fully embeddable as a Go library and supports Gremlin-inspired queries. However, development has largely stalled since 2022–2023, it lacks node/edge properties (pure triple store), and its iterator design is considered overly complex.

**EliasDB** (~966 stars, MPL-2.0) implements a **property graph model** with a custom disk-based storage engine in pure Go. It provides ACID transactions, a full-text phrase index on all data, both EQL and GraphQL query languages, and a clean embedding API (`graph.NewGraphManager(storage)`). Despite lower popularity, EliasDB is arguably more feature-complete for embedded property graph use cases.

For storage backends, three options dominate. **bbolt** (~8K stars, MIT) is a B+ tree, single-file, memory-mapped store with single-writer/multiple-reader MVCC — the simplest option, best for read-heavy workloads. **BadgerDB** (~14K stars, Apache-2.0) is the LSM-tree engine underlying Dgraph, offering **375x faster writes than BoltDB** but significantly higher memory consumption. **Pebble** (by CockroachDB) provides the best read/write balance, built-in MVCC via sequence numbers, and extensive testing infrastructure — production-ready since CockroachDB v20.1.

Smaller but relevant Go libraries include **wallix/triplestore** (pure Go triple management with DSL and binary encoding), **gonum/graph** (standard graph algorithm implementations: BFS, DFS, shortest path, SCC), and **dominikbraun/graph** (modern generic interface using Go 1.18+ generics with pluggable storage).

### AI-agent-specific knowledge graph tools

**Graphiti by Zep** (~22.5K stars, Apache-2.0, Python) represents the current state of the art for agent memory knowledge graphs. It builds **real-time, temporally-aware knowledge graphs** from agent interactions using a bi-temporal data model that tracks both `valid_at` (when a fact became true) and `invalid_at` (when it was superseded). Graphiti performs incremental entity resolution — new episodes are integrated immediately without batch recomputation — and achieves **P95 retrieval latency of ~300ms without any LLM calls at query time** by combining semantic embeddings, BM25 keyword search, and graph traversal.

**Cognee** (Apache-2.0, Python) takes a pipeline approach: ingest heterogeneous data sources → build ontology-aware knowledge graphs using Pydantic models → combine vector search with graph traversal for retrieval. It supports 30+ data source types and multiple graph backends (Neo4j, FalkorDB, Kuzu, Memgraph).

**Mem0** (~37K stars, Apache-2.0, Python) implements a hybrid memory architecture with five pillars: LLM-powered fact extraction, vector storage, graph storage, key-value history, and intelligent ranking. It reports **26% higher accuracy than OpenAI Memory** and 91% lower latency.

**Microsoft GraphRAG** (~25K stars, MIT, Python) pioneered the community-detection approach: extract entities and relationships with LLMs, apply the **Leiden hierarchical clustering algorithm** to find communities of densely connected nodes, then generate LLM-powered community summaries at multiple hierarchy levels. At query time, global questions use community summaries (map-reduce) while local questions use entity neighborhoods. GraphRAG stores graph data as **Parquet files** (DataFrames, not a traditional graph database), which is notable — it demonstrates that a full graph database is not required for effective GraphRAG.

| Tool | Language | Graph Storage | Embeddable | Key Pattern |
|------|----------|--------------|------------|-------------|
| Cayley | Go | BoltDB/LevelDB/Memory | ✅ Yes | Quad store, swappable backends |
| EliasDB | Go | Custom disk storage | ✅ Yes | Property graph, ACID, full-text |
| Graphiti (Zep) | Python | Neo4j | ❌ Server | Bi-temporal, incremental entity resolution |
| Cognee | Python | Neo4j/FalkorDB/Kuzu | ❌ Server | Pipeline: ingest → cognify → search |
| Mem0 | Python | Neo4j/Memgraph/Kuzu | ❌ Server | 5-pillar hybrid memory |
| Microsoft GraphRAG | Python | Parquet files | ✅ File-based | Community detection + summarization |
| Dgraph | Go | BadgerDB | ❌ Server | Posting lists, predicate sharding |

None of the AI-agent-specific tools are embeddable Go libraries — they all require external graph database servers (typically Neo4j) or are Python-only. This confirms a genuine gap that an embedded Go library would fill.

---

## Storage layer architecture: mapping graphs to key-value stores

The central design question is how to encode graph topology and properties into key-value pairs. Three production-proven approaches exist, each with distinct trade-offs.

### Vertex-centric adjacency packing

This is the recommended approach for an embedded library. Used by NebulaGraph (on RocksDB) and TuGraph (on LMDB), it encodes **composite keys** that naturally cluster a vertex's data together:

```
Out-edge key: [prefix:1B][srcVertexID:8B][edgeType:4B][dstVertexID:8B][edgeID:8B]
In-edge key:  [prefix:1B][dstVertexID:8B][edgeType:4B][srcVertexID:8B][edgeID:8B]
Vertex key:   [prefix:1B][vertexID:8B][labelID:4B]
```

Each edge is stored as **two independent KV pairs** (out-edge keyed by source, in-edge keyed by destination) so both forward and reverse traversals use efficient prefix scans. Properties are packed inline with topology data in the value bytes. TuGraph adds **adaptive mapping** — when a vertex's data grows beyond a threshold, it switches from a single KV pair to multiple pairs, preventing hot-spot performance degradation on high-degree nodes.

The key insight is that KV stores with ordered keys (B-tree or LSM-tree) turn prefix scans into sequential reads. Querying "all outgoing WORKS_FOR edges from vertex 42" becomes a simple prefix scan on `[OUT_EDGE][42][WORKS_FOR]`, which is fast on both B-trees and LSM-trees.

### Posting list approach

Dgraph maps graph data to BadgerDB using **posting lists** keyed by `(predicate, subject)`. The key `friend::0x1` maps to a sorted list of all UIDs that entity `0x1` has a `friend` relationship with. This approach shards data by predicate rather than by vertex, which optimizes for join operations but makes single-vertex neighborhood retrieval require multiple key lookups across different predicates. Better suited for distributed systems than embedded single-process libraries.

### Indexing strategies for fast traversal at scale

A minimum of **three index types** is required for practical graph queries. Forward edge indexes (prefix scan by source vertex) and reverse edge indexes (prefix scan by destination vertex) handle traversal in both directions. Property indexes (`[labelID][propertyKey][propertyValue] → vertexID`) enable entity lookup by attribute. For triple-store-style queries, the **Hexastore pattern** (all six permutations of SPO) provides optimal coverage, though in practice three permutations (SPO, POS, OSP) suffice for most query patterns.

Full-text search on entity names and descriptions is critical for entity linking (matching user query mentions to graph nodes). **Bleve** is the standard Go full-text search library and can be embedded alongside the graph store. For approximate matching, embedding vectors stored as node properties enable cosine similarity search, though a dedicated vector index (HNSW) would be needed for large-scale similarity queries.

For **multi-hop traversals**, the core operation is recursive prefix scanning: retrieve all out-edges of the source vertex, collect destination IDs, then repeat for each destination. Co-locating vertex data with its edges in the key ordering (the vertex-centric approach above) ensures this operation reads sequential disk pages rather than random locations, which is critical for performance at scale.

### B-tree vs LSM-tree for graph workloads

Graph workloads are typically **read-heavy** (TuGraph measured a 20:1 read-to-write ratio). B-tree stores (bbolt, LMDB) provide better point-read and range-scan latency because data is always in sorted order on disk with no compaction overhead. LSM-tree stores (BadgerDB, Pebble) offer **1.5–2x higher write throughput** but introduce read amplification (must check memtable + bloom filters + multiple SSTable levels).

TuGraph chose LMDB specifically because graph traversal is read-dominated, and B-tree's zero-copy memory-mapped reads eliminate serialization overhead. Dgraph chose BadgerDB because distributed ingestion is write-heavy and the WiscKey design (separating keys from values) optimizes for SSDs. **For an embedded single-process library, Pebble offers the best compromise** — LSM-tree write performance with well-optimized reads, built-in MVCC for versioning, and a pure Go implementation with no CGo dependencies.

---

## Designing the graph data model and schema evolution

### Recommended key layout

```
Node storage:
  Key:   n:<nodeID>
  Value: protobuf{type, properties, version, created_at, updated_at}

Out-edge storage:
  Key:   eo:<srcNodeID>:<edgeType>:<dstNodeID>:<edgeID>
  Value: protobuf{properties, version, created_at, valid_at, invalid_at}

In-edge storage (reverse index):
  Key:   ei:<dstNodeID>:<edgeType>:<srcNodeID>:<edgeID>
  Value: protobuf{same as out-edge or pointer}

Type index:
  Key:   it:<nodeType>:<nodeID>
  Value: empty (existence index)

Property index:
  Key:   ip:<nodeType>:<propertyKey>:<propertyValue>:<nodeID>
  Value: empty (existence index)

Predicate index:
  Key:   ir:<edgeType>:<srcNodeID>:<edgeID>
  Value: empty (existence index)
```

This layout ensures that all common query patterns — node lookup by ID, neighbors by direction, neighbors by edge type, nodes by type, nodes by property — resolve to single prefix scans. The `eo:` and `ei:` prefixes separate forward and reverse edge indexes, and including `edgeType` before `dstNodeID` in the key means filtering by relationship type is a prefix narrowing rather than a post-scan filter.

### Schema versioning and evolution

Following NebulaGraph and TuGraph's pattern, embed a **schema version prefix** in every serialized value. Maintain a schema registry mapping version numbers to field layouts. When the schema changes (new properties, renamed fields), increment the version. Old records are decoded using their original version's schema; new fields receive default values. This enables online schema evolution without migration — critical for agent-built graphs where entity types emerge dynamically from LLM extraction.

```go
type SchemaRegistry struct {
    versions map[uint16]SchemaVersion
}

type SchemaVersion struct {
    Version    uint16
    Fields     []FieldDef
    Decoder    func([]byte) (map[string]any, error)
}
```

---

## How AI agents query and update the knowledge graph

### Building context from graph data

The typical pipeline for an AI agent using a knowledge graph follows four steps. First, **entity extraction and linking**: the LLM parses the user query to identify mentioned entities, which are then mapped to canonical graph nodes via exact match, fuzzy match (Bleve full-text search), or embedding similarity. Second, **intent classification**: the agent determines whether this is a local query (about specific entities) or a global query (about themes across the whole graph). Third, **subgraph extraction**: starting from identified entity nodes, fan out k hops (typically 1–2), collecting all traversed vertices and edges, filtering by relationship type relevance, temporal validity, and hop distance. Fourth, **serialization**: convert the subgraph into a format the LLM can consume.

Three serialization formats work well for LLM context windows. **Structured text** is most token-efficient: `"Alice WORKS_FOR Acme Corp (since: 2020, role: Engineer)"`. **JSON** is more parseable for tool-calling agents: `{"entities": [...], "relationships": [...]}`. **Natural language narration** works best for conversational agents: `"Alice is an engineer at Acme Corp. She has worked there since 2020 and reports to Bob."` The Graphiti team found that structured text with entity descriptions and typed relationships produces the best LLM reasoning results while using fewer tokens than JSON.

### Updating the graph from agent interactions

Graphiti's architecture provides the clearest production pattern for graph updates. Each agent interaction creates an **episode** (timestamped message, document, or observation). The episode enters an extraction pipeline: an LLM extracts entities and relationships in structured format, entity resolution matches extracted entities against existing graph nodes (via name matching + embedding similarity), and new or updated facts are written to the graph with `valid_at` timestamps. When new information contradicts existing facts (e.g., "Alice was promoted to Team Lead"), the old relationship is marked `invalid_at = current_time` and a new relationship is created — preserving full history.

Entity extraction from LLMs uses tool-calling/function-calling APIs for structured output:

```json
{"head": "Alice", "head_type": "Person", "relation": "works_at",
 "tail": "Acme Corp", "tail_type": "Organization",
 "properties": {"role": "Team Lead", "since": "2024-01-15"}}
```

The KGGen research framework (arxiv 2502.09956) found that a **two-step extraction process** produces higher quality graphs: first extract entities alone, then extract relationships given the entity list plus source text. This decomposition reduces LLM confusion compared to extracting everything in a single prompt.

### Temporal knowledge and versioning

The bi-temporal model from Graphiti is the recommended approach. Every edge carries two temporal dimensions: `valid_at` (when the real-world fact became true) and `invalid_at` (when the fact was superseded), plus `created_at` (when the graph entry was created — ingestion time). This supports three query patterns: point-in-time queries ("What was Alice's role in March 2022?"), change tracking ("When did Alice change roles?"), and temporal overlap ("What was happening when the database migration started?").

In the KV store, this maps naturally to versioned keys or properties. Using Pebble's built-in MVCC (sequence numbers), you can create **snapshots** for consistent temporal reads without blocking writes. For explicit temporal queries, include timestamps in edge properties and filter during traversal.

### Rules storage and retrieval

Rules (business logic, constraints, inference rules) are stored as **typed nodes** in the graph with structured properties. A rule node might have type `Rule`, properties like `{condition: "IF project.risk_level = 'high'", action: "REQUIRE executive_approval", priority: 1}`, and edges connecting it to the entity types it applies to (`Rule --[APPLIES_TO]--> ProjectType`). At query time, when building context for an agent, rules are retrieved by traversing from the relevant entity types to their associated rule nodes, then included in the LLM prompt as constraints.

---

## Practical Go implementation architecture

### Recommended technology choices

| Component | Choice | Rationale |
|-----------|--------|-----------|
| Primary storage | **Pebble** | Best read/write balance, built-in MVCC, pure Go, extensively tested |
| Fallback storage | **bbolt** | Simpler, lower memory, single file, good for small deployments |
| Internal encoding | **Protocol Buffers** | Compact, fast, schema-enforced, excellent Go tooling |
| LLM serialization | **JSON** + structured text | LLM-compatible, human-readable |
| Full-text search | **Bleve** | Pure Go, embeddable, good for entity linking |
| Graph algorithms | **gonum/graph** | Standard Go graph algorithms (BFS, DFS, shortest path) |

Pebble is the primary recommendation because knowledge graphs need both fast traversal reads (for agent queries) and burst writes (for entity extraction from LLMs). Pebble's LSM-tree handles write bursts well while its bloom filters and block cache keep reads fast. Its **built-in MVCC via sequence numbers** is essential for temporal versioning, and the `vfs.NewMem()` option enables in-memory operation for tests. For projects where minimal memory footprint matters more than write throughput, bbolt's single-file simplicity is the pragmatic alternative.

### Core interface design

The interface design draws from gonum/graph's composability, dominikbraun/graph's generics, and Cayley's pluggable backends:

```go
package kg

type NodeID string
type EdgeID string
type Version uint64

type Node struct {
    ID         NodeID
    Type       string
    Properties map[string]any
    Version    Version
    CreatedAt  time.Time
    UpdatedAt  time.Time
}

type Edge struct {
    ID         EdgeID
    From       NodeID
    To         NodeID
    Type       string
    Properties map[string]any
    Version    Version
    ValidAt    *time.Time  // when fact became true
    InvalidAt  *time.Time  // when fact was superseded
    CreatedAt  time.Time
}

// Store is the pluggable storage abstraction
type Store interface {
    GetNode(ctx context.Context, id NodeID) (*Node, error)
    PutNode(ctx context.Context, node *Node) error
    DeleteNode(ctx context.Context, id NodeID) error
    OutEdges(ctx context.Context, id NodeID, edgeType string) EdgeIterator
    InEdges(ctx context.Context, id NodeID, edgeType string) EdgeIterator
    NodesByType(ctx context.Context, nodeType string) NodeIterator
    Close() error
}

// Graph provides high-level operations
type Graph interface {
    Store
    Begin(ctx context.Context, writable bool) (Tx, error)
    Neighbors(ctx context.Context, id NodeID, opts TraversalOpts) NodeIterator
    Traverse(ctx context.Context, start NodeID, depth int) (*Subgraph, error)
    SubgraphJSON(ctx context.Context, seeds []NodeID, depth int) ([]byte, error)
    SubgraphText(ctx context.Context, seeds []NodeID, depth int) (string, error)
    ImportTriples(ctx context.Context, triples []Triple) error
}

// Iterator follows Go-idiomatic pattern
type NodeIterator interface {
    Next() bool
    Node() *Node
    Err() error
    Close() error
}
```

Transaction handling follows BoltDB's closure pattern to ensure proper cleanup: `graph.Update(func(tx Tx) error { ... })` for writes and `graph.View(func(tx Tx) error { ... })` for reads. This prevents leaked transactions, which is the most common source of bugs in embedded database usage.

### Project structure and build order

```
kg/
├── kg.go              # Core types: Node, Edge, Triple, Subgraph
├── graph.go           # Graph implementation orchestrating store + indexes
├── store/
│   ├── store.go       # Store interface definition
│   ├── pebble/        # Pebble backend: key encoding, prefix scans
│   ├── bolt/          # bbolt backend
│   └── memory/        # In-memory backend for testing
├── index/
│   └── index.go       # Secondary index management (type, property)
├── traverse/
│   ├── bfs.go         # Breadth-first traversal
│   ├── dfs.go         # Depth-first traversal
│   └── path.go        # Shortest path, all paths
├── serialize/
│   ├── proto.go       # Protobuf encoding for storage
│   ├── json.go        # JSON for API/LLM
│   └── text.go        # Structured text for LLM context
├── temporal/
│   └── version.go     # MVCC, temporal queries, valid_at/invalid_at
├── extract/
│   ├── entity.go      # Parse LLM entity extraction results
│   └── resolve.go     # Entity deduplication and resolution
└── kg_test.go         # Integration tests
```

The recommended build order prioritizes a functional core before adding agent-specific features:

**Phase 1 — Core storage.** Node/Edge CRUD with the in-memory store backend. Protobuf serialization. Comprehensive table-driven tests for all CRUD operations. This validates the data model and interface design before introducing storage complexity.

**Phase 2 — Pebble backend.** Implement the Store interface over Pebble with the composite key encoding described above. Secondary indexes for type and property lookups. Transaction support via Pebble's batch and snapshot primitives.

**Phase 3 — Traversal.** BFS and DFS using gonum/graph algorithms adapted for the Store interface. Subgraph extraction (k-hop neighborhood from seed nodes). Iterator composition for filtered traversals.

**Phase 4 — LLM integration.** JSON and structured-text serialization of subgraphs. Entity extraction result parsing (JSON → Node/Edge structs). Context builder that assembles graph data into token-budgeted prompts.

**Phase 5 — Temporal versioning.** `valid_at`/`invalid_at` on edges. Point-in-time queries using Pebble snapshots. History retrieval for entity change tracking.

**Phase 6 — Query DSL.** Simple pattern-matching query language (inspired by Cypher's MATCH patterns but as a Go builder API). Iterator cost estimation following Cayley's pattern for query optimization.

---

## Scaling to millions and billions of nodes

For an embedded single-process library, scaling depends on three strategies. **Memory-mapped storage** (used by LMDB, BoltDB) defers memory management to the OS — hot pages stay in RAM via the page cache while cold data lives on disk, transparently handling datasets larger than available memory. TuGraph supports up to **2^40 vertices per graph** on a single machine using this approach.

**Partitioning within a single process** can be achieved by maintaining separate Pebble instances per logical subgraph or label type, with a shared metadata instance tracking the partition map. This reduces contention and enables parallel compaction. For extremely large graphs, data can be split across multiple files by vertex ID range (hash-based partitioning: `vertexID % numPartitions`).

**Caching topology separately from properties** is the key performance insight from NebulaGraph's architecture. Graph traversal only needs edge endpoints and types (topology), not full property payloads. By structuring keys so that topology data clusters in hot pages while properties spread across cold pages, the OS page cache naturally prioritizes the data that matters most for traversal performance. For application-level caching, an **LRU cache for decoded Node/Edge objects** avoids repeated deserialization of frequently accessed entities.

Write optimization for bulk entity extraction follows Dgraph's pattern: buffer writes in memory (Pebble's memtable handles this natively), use batch APIs for bulk ingestion, and rely on LSM-tree's background compaction to merge data efficiently. A single Pebble batch write of 1,000 edges will dramatically outperform 1,000 individual writes.

---

## Conclusion: what makes this architecture work

The embedded Go knowledge graph library outlined here fills a genuine gap — no existing tool combines embeddability, Go-native implementation, property graph support, and AI agent integration. The architecture succeeds because it layers proven patterns from multiple production systems: TuGraph's vertex-centric key encoding for efficient prefix-scan traversal, Graphiti's bi-temporal model for agent memory that tracks knowledge evolution, Microsoft GraphRAG's community detection for hierarchical summarization, and Pebble's battle-tested MVCC for consistent versioned reads.

The most important design decision is **keeping the storage abstraction clean**. By defining a narrow `Store` interface with prefix-scan-based iteration, you can start with bbolt for prototyping, move to Pebble for production, and potentially add LMDB or custom memory-mapped storage later — without touching the graph logic. The second critical decision is building LLM serialization as a first-class concern rather than an afterthought: the `SubgraphJSON` and `SubgraphText` methods on the Graph interface ensure that every graph query can produce agent-ready context.

Start with Phase 1 (core types + in-memory store + tests), validate the interface design with real agent workloads, then layer in Pebble storage and temporal versioning. The property graph model, composite key encoding, and bidirectional edge indexes described here will scale to millions of nodes on a single machine while maintaining sub-millisecond single-hop traversal latency — exactly what an AI agent needs for real-time knowledge retrieval.