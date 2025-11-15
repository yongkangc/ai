---
description: Create a draft pull request with structured format
---

Create a draft pull request with the following format:

### Problem
[Clearly describe the problem being solved or feature being added]

### Solution
[Explain the approach taken to solve the problem]

### Changes
[List the key changes made in bullet points]

### Expected Impact
[Describe what impact these changes will have]

Follow these guidelines:
- Analyze the git diff and commit history to understand what changed
- Keep the description clear and succinct
- Use the exact format with ### headers as shown above
- Create the PR as a draft using `gh pr create --draft`
- Don't push unless changes are already committed

Arguments: $ARGUMENTS (optional: base branch or PR title)
