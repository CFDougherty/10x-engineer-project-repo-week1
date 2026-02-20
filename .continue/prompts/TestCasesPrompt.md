---
name: TestCasesPrompt
description: Instructional prompt to write test coverage
invokable: true
---

 Evaluate this file against the following requirements. Use the name of the file to reference the appropriate requirements section
 
 Ask questions until you have at least an 80% understanding, and examine the surrounding code and files for reference as needed.
 
 It is crucial that the 80% test coverage includes edge cases and can make my code fail as part of TDD practices.
 
 My criterial for good and working tests are not ones that succeed with my current code, but rather, tests that identify gaps and holes and areas for improvement in my code


 
Write Comprehensive Test Suite
Achieve **80%+ code coverage**:

**`tests/test_api.py`:**
- [ ] Test all endpoints (happy path)
- [ ] Test error cases (404, 400, etc.)
- [ ] Test edge cases (empty strings, special characters)
- [ ] Test query parameters (sorting, filtering)

**`tests/test_storage.py`:**
- [ ] Test CRUD operations
- [ ] Test data persistence within session
- [ ] Test edge cases

**`tests/test_utils.py`:**
- [ ] Test all utility functions
- [ ] Test edge cases and error conditions

**`tests/test_models.py`:**
- [ ] Test model validation
- [ ] Test default values
- [ ] Test serialization

When complete, propose your changes, justify them, and be ready to defend them against a technical evaluation. Then help me implement those proposals in my code