# ADR-004: pgvector sobre la misma instancia PostgreSQL (no vector store dedicado)

**Estado:** Aceptado

## Contexto
Los agentes necesitan almacenamiento vectorial para embeddings (búsqueda semántica sobre specs, código, decisiones previas).

## Decisión
Se usa la extensión pgvector sobre la misma instancia PostgreSQL 16 que ya sirve como base de datos relacional del sistema (Docker local, RDS en AWS).

## Alternativas consideradas
Vector store dedicado (Pinecone, Weaviate, Qdrant) — descartado para mantener una sola pieza de infraestructura que operar y respaldar, evitando el costo/complejidad de un servicio adicional en un proyecto de este tamaño.

## Consecuencias
Menos piezas móviles en `docker-compose.yml` y en Terraform. Trade-off: pgvector es menos especializado que un vector store dedicado en escala/latencia; aceptable mientras el volumen de embeddings sea moderado.
