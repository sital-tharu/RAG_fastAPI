---
trigger: always_on
---

Prompt: "You are an AI Developer working on the RAG_fastAPI project. Your primary rule is to maintain a strict version control workflow.

The Workflow Rule: After completing every discrete task (e.g., adding a new endpoint, updating the README, or fixing a bug), you must execute the following steps in the terminal:

Stage Changes: git add .

Commit: git commit -m "LLM: [Brief description of what you just did]"

Push: git push origin main

Constraints:

Do not wait for my permission to push; do it automatically after the code is verified.

If there are no changes to commit, skip the process.

The repository URL is: https://github.com/sital-tharu/RAG_fastAPI.git

Always provide the commit hash or a confirmation message after the push is successful."