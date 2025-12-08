```
+-------------------+         +-------------------+
|  User Interaction |         |    CLI Layer      |
|                   |         | (src/aidev/cli.py) |
+---------+---------+         +--------+----------+
          |                              |
          |  runs aidev workflow         |
          |                              |
          V                              V
+---------+---------+         +----------+--------+
| User  ------------> {aidev workflow command} ----> | workflow() function |
+-------------------+         +----------+--------+
                                         |
                                         |  parses
                                         |
                                         V
                               +----------+----------+
                               | CLI arguments:       |
                               | workflow_name,       |
                               | --ticket, --file,    |
                               | --execute, etc.      |
                               +----------+----------+
                                         |
                                         |  instantiates
                                         |  WorkflowEngine
                                         V
+-------------------------------------------------------------------------------------------------------+
|                                    Core Logic (src/aidev/workflow.py)                               |
|                                                                                                       |
| +---------------------+                                                                               |
| |  WorkflowEngine     | <----------------------------------------------------------+                  |
| +----------+----------+                                                            |                  |
|            |                                                                       | loads and parses |
|            | loads and parses                                                      |                  |
|            |                                                                       |                  |
|            V                                                                       |                  |
| +----------+----------+         +---------------------+                           |                  |
| | workflows.yaml      | ------->| WorkflowSpec objects| <--------------------------+                  |
| | (definitions)       |         +----------+----------+                                              |
| +----------+----------+                    |                                                         |
|            |                                | contains a list of                                       |
|            |                                V                                                         |
|            |                     +----------+----------+                                              |
|            |                     | WorkflowStep objects|                                              |
|            |                     +----------+----------+                                              |
|            |                          |                                                              |
|            |                          | references                                                    |
|            |                          V                                                              |
|            |                     +----------+----------+                                              |
|            |                     | Prompt files (.txt) |                                              |
|            |                     | (src/aidev/prompts/)|                                              |
|            |                     +----------+----------+                                              |
|            |                                                                                          |
|            | called by CLI workflow() function                                                       |
|            V                                                                                          |
| +----------+----------+                                                                               |
| | run_workflow()      |                                                                               |
| +----------+----------+                                                                               |
|            |                                                                                          |
|            | generates                                                                                |
|            V                                                                                          |
| +----------+----------+                                                                               |
| | Run Manifest        |                                                                               |
| | (JSON file)         |                                                                               |
| | (e.g., .aidev/workflow-runs/workflow-name-timestamp.json)                                           |
| +----------+----------+                                                                               |
|            |                                                                                          |
|            | if --execute flag is present, CLI calls:                                                 |
|            V                                                                                          |
| +----------+----------+                                                                               |
| | execute_manifest()  |                                                                               |
| | (Conceptual, currently a placeholder)                                                               |
| +----------+----------+                                                                               |
|            |                                                                                          |
|            | reads and updates                                                                        |
|            V                                                                                          |
| +-------------------------------------------------------------------------------------------------------+
| | Run Manifest Content:                                                                                |
| | - workflow name                                                                                      |
| | - input information                                                                                  |
| | - steps (resolved assistant, prompt text, tool options, timeout, retries)                            |
| | - placeholder for execution output (status, result)                                                  |
| +-------------------------------------------------------------------------------------------------------+
```