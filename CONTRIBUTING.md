# Contributing to Claude Remote Runner

Thank you for your interest in contributing! This document provides guidelines for contributing to the project.

## Development Process

1. Fork the repository
2. Create a feature branch from `main`
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## Coding Standards

### Python Code
- Follow PEP 8 style guide
- Use type hints where appropriate
- Add docstrings to all functions
- Maximum line length: 100 characters

### Docker
- Use official base images when possible
- Pin versions for reproducibility
- Minimize layer count
- Document all environment variables

### Documentation
- Update README.md for user-facing changes
- Add implementation docs for new features
- Include code examples
- Keep changelog updated

## Testing

Before submitting:

```bash
# Run tests
docker exec telegram-bot python3 /app/test_keyboards.py
docker exec telegram-bot python3 /app/test_approval_workflow.py
docker exec telegram-bot python3 /app/test_command_helpers.py

# Test Docker build
docker-compose build

# Test deployment
docker-compose up -d
```

## Pull Request Process

1. Update documentation
2. Add tests for new features
3. Ensure all tests pass
4. Update CHANGELOG.md (if exists)
5. Request review from maintainers

## Commit Messages

Follow conventional commits:

```
feat: Add voice message length validation
fix: Correct webhook URL configuration
docs: Update deployment instructions
refactor: Simplify approval workflow logic
test: Add unit tests for transcription
```

## Questions?

Open an issue or discussion on GitHub.
