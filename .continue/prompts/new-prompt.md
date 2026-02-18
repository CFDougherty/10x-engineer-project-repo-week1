---
name: documentation for read
description: Check and validate documentation
invokable: true
---

You are reviewing a provided excerpt of README.md from THIS repository.

Goal:
Validate that the instructions are accurate, runnable, and complete for a typical GitHub Codespaces environment.

Instructions:
Given this snippet of documentation in README.md, I want you to perform the following:

- Evaluate the text for accuracy and completeness

- Where relevant, test any claims / functions / endpoints provided to ensure accuracy in instruction. Refer to surrounding information as-needed

- If any gaps in instruction are noted, then add to or re-write relevant sections of the readme for completeness

- If there are any missing instructions based on the context of the code base, then add to or re-write the relevant sections of the readme for completeness

- Any provided code snippest must be tested

- Examples should be standalone and not reliant on previous steps. For generating sample outputs, you may use any other API calls or sample data as needed. However, provided snippets should not be in powershell syntax with $VARIABLE names which create dependencies in examples

- You are not to modify any files or code outside of README.md



If there is any ambiguity, please ask follow up questions until there is an >80% understanding of the problem before continuing

When your evaluations are complete, please check if the server is stopped and stop it if needed. Validate once complete.