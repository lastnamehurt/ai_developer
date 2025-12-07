# How the MCP Memory Server Works

This document explains the functionality of the `memory` MCP server and how it enables memory across multiple AI sessions and assistants.

## Overview

The `memory` server provides a form of persistent memory for an AI assistant. Instead of a simple key-value store, it implements a **local knowledge graph**. This allows the AI to store, retrieve, and connect complex pieces of information about people, things, and their relationships, much like a human would.

The server's description is: "Persistent memory and context preservation across sessions."

---

## How It Works: A Knowledge Graph

The memory is structured as a graph with three core concepts:

1.  **Entities:** These are the primary nodes or subjects in the graph. An entity could be a person, an organization, a project, or any noun. Each entity has a unique name, a type (e.g., "person"), and a list of observations.

2.  **Observations:** These are atomic facts or pieces of information attached to an entity. For example, for an entity named "Jane_Doe", an observation might be "Prefers Python for data analysis".

3.  **Relations:** These are directed links that define the relationship between two entities. For example, a relation could link the "Jane_Doe" entity to the "AI_Developer_Project" entity with the relation type "contributes_to".

All of this data is stored persistently in a single JSONL (JSON Lines) file on your local filesystem.

---

## Use Case 1: Memory Across Multiple AI Sessions

The key to cross-session memory is the persistent storage file.

- When the `memory` server runs, it reads the knowledge graph from its JSONL file.
- As the AI assistant learns new things (by using tools like `create_entities` or `add_observations`), the server writes these updates back to the file.
- When you end your session and start a new one later, the `memory` server restarts and loads its state from the same file.

This allows the AI's knowledge to be durable and grow over time, enabling it to remember context from previous conversations.

## Use Case 2: Memory Across Multiple AI Assistants

The `memory` server can be shared between different AI assistants or profiles, allowing them to have a shared understanding and context.

This is achieved through configuration. The server's storage file can be set using the `MEMORY_FILE_PATH` environment variable.

- **To share memory:** Configure the `memory` MCP server in each AI assistant's profile to point to the **exact same `MEMORY_FILE_PATH`**. When Assistant A saves a fact about a project, Assistant B (which uses the same memory file) will have immediate access to that fact.

- **To isolate memory:** If you want different assistants to have separate memories, simply configure them to use different `MEMORY_FILE_PATH`s (e.g., `~/.ai_memory/work_assistant.jsonl` and `~/.ai_memory/personal_assistant.jsonl`).

By managing this file path, you have full control over whether memory is shared or siloed.

---

## Available API Tools

The AI assistant interacts with the knowledge graph using a rich set of tools, including:

- **Create/Delete:** `create_entities`, `delete_entities`, `create_relations`, `delete_relations`, `add_observations`, `delete_observations`
- **Read/Search:** `read_graph` (to get everything), `search_nodes` (to find specific entities based on a query), and `open_nodes` (to retrieve specific entities by name).

This API allows the assistant to manage its memory in a structured and sophisticated way.
