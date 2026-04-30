# Contributing to Retail Demand Forecaster

Thank you for your interest in contributing! This document provides guidelines and information for contributors.

---

## Getting Started

### Prerequisites
- Python 3.10 or higher
- UV package manager
- Git
- Docker (optional but recommended)

### Setup Development Environment

```bash
# 1. Clone the repository
git clone https://github.com/your-username/retail-demand-forecaster.git
cd retail-demand-forecaster

# 2. Install dependencies with UV
make install

# 3. Generate sample data
make generate-data

# 4. Run tests to verify setup
make test
```

---

## Development Workflow

### 1. Create a Branch

```bash
# Choose a descriptive branch name
git checkout -b feature/add-real-time-streaming
# or
git checkout -b fix/forecast-lag-bug
# or
git checkout -b docs/enhance-readme
```

**Branch Naming Convention**:
- `feature/` - New functionality
- `fix/` - Bug fixes
- `docs/` - Documentation changes
- `refactor/` - Code restructuring
- `test/` - Test improvements
- `chore/` - Maintenance tasks

### 2. Make Changes

**Code Standards**:
- Follow PEP 8 style guide
- Use type hints everywhere (`-> str`, `Optional[Dict]`)
- Write docstrings (Google style):
```python
def forecast_demand(sku_id: str, store_id: str) -> Dict:
    """Generate demand forecast.
    
    Args:
        sku_id: Product identifier
        store_id: Store identifier
        
    Returns:
        Dict containing forecast data
        
    Raises:
        ValueError: If SKU not found
    """
```

- Add unit tests for new functionality
- Update documentation (README, /docs/)
- Keep changes focused (one feature/fix per PR)

### 3. Run Tests

```bash
# Run all tests
make test

# Run specific test file
pytest tests/test_demand_forecaster.py -v

# Run with coverage
make test-cov

# Lint code
make lint

# Format code
make format

# Type check
make typecheck
```

**All checks must pass before submitting PR.**

### 4. Commit Changes

```bash
git add <changed-files>
git commit -m "feat: add real-time sales streaming support"
```

**Commit Message Format** (Conventional Commits):
```
<type>: <description>

[optional body]

[optional footer]
```

**Types**:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style (formatting, no logic change)
- `refactor`: Code restructuring
- `test`: Add or update tests
- `chore`: Maintenance tasks

**Examples**:
```
feat: add Kafka streaming for sales data
fix: correct lag feature calculation in forecaster
docs: update architecture diagram with Mermaid
test: add tests for promotion date parsing
```

### 5. Push and Open PR

```bash
git push origin feature/your-feature-name
```

Then open a Pull Request on GitHub.

---

## Pull Request Process

### PR Template

```markdown
## Description
[What does this PR do?]

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Unit tests added/updated
- [ ] Integration tests pass
- [ ] Manual testing completed

## Screenshots (if applicable)
[Add screenshots for UI changes]

## Checklist
- [ ] Code follows PEP 8
- [ ] Type hints added
- [ ] Docstrings updated
- [ ] Documentation updated
- [ ] All tests pass
- [ ] No new linting errors
```

### Review Process

1. **Automated Checks**: CI runs tests, linting, type checking
2. **Code Review**: At least one maintainer reviews
3. **Feedback**: Address review comments
4. **Approval**: PR approved by maintainer
5. **Merge**: Squash and merge to main

**Expected Timeline**: Review within 2-3 business days.

---

## Coding Standards

### Python Style

- **Line Length**: Maximum 100 characters
- **Imports**: Group as: stdlib → third-party → local
- **Naming**: `snake_case` for functions/variables, `PascalCase` for classes
- **Constants**: `UPPER_CASE`
- **Docstrings**: Google style

**Good**:
```python
from typing import Dict, Optional
import json
import pandas as pd


class DemandForecaster:
    """Forecasts demand using ML models."""
    
    def __init__(self, data_dir: Path) -> None:
        """Initialize forecaster.
        
        Args:
            data_dir: Path to data directory
        """
        self.data_dir = data_dir
    
    def forecast(self, sku_id: str, days: int = 7) -> Optional[Dict]:
        """Generate forecast.
        
        Returns:
            Forecast dictionary or None if failed
        """
        pass
```

### Documentation Standards

- **README.md**: Keep updated with new features
- **/docs/**: Add new guides as needed
- **Inline Comments**: Explain "why", not "what"
- **Architecture Diagrams**: Use Mermaid for all diagrams
- **API Examples**: Update with changes

### Testing Standards

- **Coverage**: Aim for >90%
- **Isolation**: Tests independent, no shared state
- **Fixtures**: Use `conftest.py` for common setup
- **Mocking**: Mock external dependencies (SMTP, APIs)
- **Names**: `test_<function>_<scenario>`

**Example**:
```python
def test_forecast_with_insufficient_history():
    """Test that forecast handles limited data gracefully."""
    # Arrange
    sku_id = "SKU_001"
    store_id = "STORE_001"
    
    # Act
    result = forecast_demand(sku_id, store_id, horizon_days=7)
    
    # Assert
    assert result is not None
    assert "forecast" in result
    assert len(result["forecast"]) == 7
```

---

## Adding New Agents

To add a new agent:

1. Create `src/agents/<agent_name>.py`
2. Define clear interfaces (inputs/outputs as dicts)
3. Add to `src/agents/__init__.py`
4. Write unit tests (`tests/test_<agent_name>.py`)
5. Add API endpoint if needed (`src/app/main.py`)
6. Update sequence diagram in README
7. Document in `/docs/architecture.md`

---

## Adding New API Endpoints

1. Add Pydantic model for request/response
2. Implement endpoint in `src/app/main.py`
3. Add tests in `tests/test_api.py`
4. Update API reference in `docs/api_reference.md`
5. Add to endpoint table in README
6. Update `docs/agentic_engineering.md` if agent interaction changes

---

## Reporting Bugs

### Bug Report Template

```markdown
## Description
[Clear description of bug]

## Steps to Reproduce
1. [First step]
2. [Second step]
3. [etc.]

## Expected Behavior
[What should happen]

## Actual Behavior
[What actually happens]

## Environment
- OS: [e.g., Ubuntu 22.04]
- Python: [e.g., 3.11.2]
- Version: [e.g., 1.0.0]

## Additional Context
[Screenshots, logs, error messages]
```

**Submit**: Open [GitHub Issue](https://github.com/your-username/retail-demand-forecaster/issues)

---

## Feature Requests

We welcome suggestions! Before submitting:

1. **Check existing issues** to avoid duplicates
2. **Describe the use case**: Who benefits and how?
3. **Provide examples**: Mock API responses, UI mockups
4. **Consider complexity**: Is it feasible?

**Submit**: Open [GitHub Issue](https://github.com/your-username/retail-demand-forecaster/issues) with `[Feature Request]` prefix.

---

## Code Review Guidelines

### For Reviewers

1. **Functionality**: Does it work as intended?
2. **Tests**: Adequate coverage? Edge cases?
3. **Security**: Any vulnerabilities?
4. **Performance**: Efficient? Scalable?
5. **Readability**: Clear, maintainable?
6. **Documentation**: Code and user docs updated?
7. **Style**: PEP 8 compliant?

**Approval**: At least 1 maintainer approval required.

---

## Release Process

### Versioning

Semantic Versioning (SemVer):
- **MAJOR**: Breaking changes
- **MINOR**: New features (backward compatible)
- **PATCH**: Bug fixes

**Current Version**: 1.0.0

### Release Checklist

- [ ] All tests passing
- [ ] Documentation updated
- [ ] CHANGELOG.md updated
- [ ] Version bumped in `src/__init__.py`
- [ ] Git tag created: `git tag v1.0.0`
- [ ] GitHub Release published
- [ ] Docker images pushed
- [ ] K8s manifests updated

---

## Community

### Code of Conduct

We follow the [Contributor Covenant](https://www.contributor-covenant.org/). Be respectful, inclusive, and constructive.

### Communication

- **Issues**: Bug reports, feature requests
- **Discussions**: General questions, ideas
- **Pull Requests**: Code contributions

### Recognition

Contributors are listed in:
- README.md "Contributors" section
- GitHub contributors graph
- Release notes

---

## Learning Resources

### For New Contributors
1. Read [Architecture Decision Records](architecture_decisions.md)
2. Study agent patterns in `src/agents/`
3. Run the demo (`make docker-up`)
4. Explore API docs (`/docs` endpoint)

### For Advanced Contributions
- [FastAPI Advanced](https://fastapi.tiangolo.com/advanced/)
- [Prophet Documentation](https://facebook.github.io/prophet/)
- [XGBoost Parameters](https://xgboost.readthedocs.io/)
- [Kubernetes Patterns](https://k8s.iximiuz.com/)

---

## FAQ

**Q: How do I add a new supplier?**  
A: Update `supplier_email_map` in `supplier_communicator.py` and add to `supplier_metadata.json`.

**Q: Can I use a different ML model?**  
A: Yes! Modify `DemandForecaster` class to plug in your model.

**Q: How to add real database support?**  
A: Create `src/db/` with SQLAlchemy models. See ADR-004 for migration strategy.

**Q: Where do I add new environment variables?**  
A: Update `.env.example` and use `os.getenv()` with defaults.

**Q: How to improve forecast accuracy?**  
A: Try feature engineering, hyperparameter tuning, or different models (LSTM, DeepAR).

---

## Getting Help

- **Documentation**: `/docs/` folder
- **API Docs**: http://localhost:8000/docs (when running)
- **Issues**: Search [GitHub Issues](https://github.com/your-username/retail-demand-forecaster/issues)
- **Discussions**: [GitHub Discussions](https://github.com/your-username/retail-demand-forecaster/discussions)

---

## License

By contributing, you agree that your contributions will be licensed under the MIT License (see LICENSE file).

---

**Happy Contributing!** 🚀

*Questions? Contact: your.email@example.com*