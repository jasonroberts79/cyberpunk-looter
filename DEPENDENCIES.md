# Dependency Management

This project uses `pyproject.toml` as the source of truth for dependencies, with `requirements.txt` auto-generated for Docker and CI/CD compatibility.

## Overview

- **pyproject.toml**: Primary dependency specification (modern Python standard)
- **requirements.txt**: Generated lock file with pinned versions for reproducible builds

## Managing Dependencies

### Adding a New Dependency

1. Edit `pyproject.toml` and add the dependency:
   ```toml
   dependencies = [
       "new-package>=1.0.0",
       # ... other dependencies
   ]
   ```

2. Regenerate `requirements.txt`:
   ```bash
   make requirements
   ```

   Or manually:
   ```bash
   python3 -m pip install pip-tools
   python3 -m piptools compile pyproject.toml --output-file=requirements.txt --resolver=backtracking
   ```

### Installing Dependencies

For local development:
```bash
make install
# or
pip install -r requirements.txt
```

### Updating Dependencies

To update all dependencies to their latest compatible versions:

1. Update version constraints in `pyproject.toml` if needed
2. Regenerate requirements.txt:
   ```bash
   make requirements
   ```

## Available Make Commands

```bash
make help           # Show all available commands
make requirements   # Generate requirements.txt from pyproject.toml
make install        # Install dependencies from requirements.txt
make test           # Run tests and linting
make clean          # Remove generated files
```

## CI/CD Integration

The GitHub Actions workflows automatically use `requirements.txt` for:
- Testing (app-deploy.yml)
- Docker builds (Dockerfile)

**Important**: Always commit both `pyproject.toml` and the generated `requirements.txt` together when updating dependencies.

## Why Both Files?

- **pyproject.toml**: Modern Python packaging standard, human-readable, version ranges
- **requirements.txt**: Lock file with exact versions for reproducible builds in Docker/CI

This approach gives you the best of both worlds:
- Easy dependency management with pyproject.toml
- Reproducible builds with pinned versions in requirements.txt
