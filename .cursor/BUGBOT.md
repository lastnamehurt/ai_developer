# Programming Best Practices

## Ruby Metaprogramming

Ruby Metaprogramming reduces readability and increases cognitive load, and it hinders tooling and static analysis.

### What to Avoid

**Do not open classes and monkey patch**, which can introduce global conflicts, paralyzes upgrades and bypasses security fixes.

**Do not use `send` or `public_send`**, not in production code or tests. If you are using them in test, you should only test public methods. Consider extracting other classes if private helper methods are too bloated.

**Do not use `define_method`**, which makes method definitions hard to trace, and circumvent static code analysis tooling like Packwerk for modularity.

**Do not use `method_missing`**, which introduces opacity, performance penalties, and poor error handling.

**Do not use `instance_eval` or `class_eval`**, which breaks encapsulation and access control as well as obscures scope and readability.

## Test Quality Guidelines

### Review Tests According to These Standards

When reviewing tests, ensure they meet the following quality criteria:

1. **Clarity**: Tests should clearly express intent and be easy to understand
2. **Isolation**: Each test should be independent and not rely on other tests
3. **Maintainability**: Tests should be easy to update when requirements change
4. **Coverage**: Tests should cover edge cases and failure scenarios, not just happy paths
5. **Speed**: Tests should run quickly to enable fast feedback loops
6. **Reliability**: Tests should be deterministic and not flaky

### Language-Agnostic Principles

These principles apply regardless of programming language:

- **Test public interfaces only**: Don't test private/internal implementation details
- **Use descriptive test names**: Test names should describe what is being tested and expected behavior
- **One assertion per test**: Keep tests focused on a single behavior
- **Avoid test interdependencies**: Tests should not depend on execution order
- **Mock external dependencies**: Don't rely on external services, databases, or file systems unless integration testing
- **Keep tests DRY but readable**: Balance code reuse with test comprehension

### Translation to Other Languages

When reviewing code in languages other than Ruby:

- **Python**: Apply similar principles to avoid `exec()`, `eval()`, excessive use of `__getattr__`
- **JavaScript/TypeScript**: Avoid excessive use of `eval()`, `with`, prototype pollution
- **Java**: Avoid reflection abuse, excessive annotation processing, bytecode manipulation
- **Go**: Avoid reflection for core logic, prefer explicit over implicit
- **General**: Prefer explicit, static, and analyzable code over dynamic metaprogramming
