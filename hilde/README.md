# HILDE: Human-in-the-Loop Decoding for AI Code Generation

A dual-LLM coding assistant that surfaces critical decision points and provides semantic alternatives during AI code generation.

## Overview

HILDE (Human-in-the-Loop Decoding) addresses the problem of AI over-reliance by transforming users from passive verifiers to active participants in code generation. Instead of presenting a single solution, HILDE shows the LLM's internal decision-making process and provides meaningful alternatives with explanations.

## Architecture

### Dual-LLM Design
- **Completion LLM**: Qwen2.5-Coder-32B for fast code generation with token probabilities
- **Analysis LLM**: GPT-4.1-nano for semantic reasoning and explanation generation
- **API Gateway**: Orchestrates communication and provides unified interface

### Core Components
1. **Token Alternatives & Semantic Scoring**: Identifies critical decision points using corrected entropy
2. **VS Code Extension**: Provides inline highlighting and alternative selection
3. **Suffix Preservation**: Maintains code consistency when alternatives are selected
4. **Security Integration**: Background security scanning with Semgrep/Bandit
5. **Constraint-Aware Debugging**: Real-time constraint violation detection and explanation
6. **Analytics**: Comprehensive logging and user behavior insights

## Features

### 🎯 Intentional Code Generation
- **Critical Decision Highlighting**: Red gradient underlines indicate important choices
- **Semantic Alternatives**: Each alternative comes with explanation and importance score
- **Granular Control**: Token-level decision making with immediate feedback

### 🔒 Security-First Approach
- **Proactive Prevention**: Identifies security implications before code is written
- **Background Scanning**: Automatic security analysis after completion acceptance
- **Best Practice Guidance**: Explains why certain alternatives are more secure

### 🛡️ Constraint-Aware Debugging
- **Custom Rule Definition**: Define coding constraints in JSON configuration
- **Real-time Violation Detection**: AST-based parsing for Python, regex fallback for other languages
- **Human-readable Explanations**: Natural language explanations suitable for VS Code display
- **Integrated Workflow**: Constraint violations included in completion responses

### 📊 Human-in-the-Loop Analytics
- **Decision Tracking**: Monitors user choices and decision-making patterns
- **Vulnerability Reduction**: Tracks security improvements over time
- **Performance Insights**: Identifies areas for interface optimization

## Installation

### Prerequisites
- Docker with CUDA support (for completion LLM)
- NVIDIA GPU with 40GB+ VRAM
- OpenAI API key (for analysis LLM)

### Quick Start
```bash
# Clone the repository
git clone <repository-url>
cd hilde

# Set environment variables
export OPENAI_API_KEY="your-api-key-here"

# Start services
docker-compose up -d

# Install VS Code extension
cd extension
npm install
npm run compile
```

### Service Configuration
```yaml
# docker-compose.yml
services:
  completion-llm:    # Port 8001 - Qwen2.5-Coder-32B
  analysis-llm:      # Port 8002 - GPT-4.1-nano  
  api-gateway:       # Port 8000 - Main interface
```

## Usage

### 1. Start HILDE Assistant
- Open VS Code
- Press `Ctrl+Shift+P` and run "Start HILDE Assistant"
- Begin coding in supported languages (Python, JavaScript, TypeScript)

### 2. Identify Critical Decisions
- Red underlines appear on tokens with high corrected entropy
- Hover over highlighted tokens to see alternatives
- Each alternative includes:
  - **Explanation Summary**: One-line description
  - **Category**: Significant/Minor/Incorrect
  - **Importance Score**: 0-1 impact rating

### 3. Select Alternatives
- Click on highlighted tokens to see alternative options
- Choose the most appropriate alternative
- HILDE automatically regenerates the suffix to maintain consistency

### 4. Security Mode
- Security scanning runs automatically in background
- Inline warnings appear for detected vulnerabilities
- Non-blocking notifications maintain workflow continuity

## Configuration

### VS Code Settings
```json
{
  "hilde.apiUrl": "http://localhost:8000",
  "hilde.highlightThreshold": 0.3,
  "hilde.mode": "intentional"  // or "efficient"
}
```

### Operation Modes
- **Intentional Mode**: More highlights, detailed explanations
- **Efficient Mode**: Fewer highlights, streamlined interface

### Constraint Configuration
Define coding constraints in `constraints.json`:

```json
{
  "constraints": {
    "no_global_vars": {
      "enabled": true,
      "description": "Prevent global variable declarations",
      "severity": "warning",
      "message": "Global variables can cause hidden side effects."
    },
    "sanitize_inputs": {
      "enabled": true,
      "description": "Ensure user inputs are properly sanitized",
      "severity": "error",
      "message": "User inputs should be sanitized to prevent injection attacks."
    },
    "disallow_raw_sql": {
      "enabled": true,
      "description": "Prevent raw SQL queries without parameterization",
      "severity": "error",
      "message": "Raw SQL queries are vulnerable to SQL injection attacks."
    }
  }
}
```

**Available Constraints:**
- `no_global_vars`: Prevent global variable declarations
- `sanitize_inputs`: Ensure input sanitization
- `disallow_raw_sql`: Prevent raw SQL queries
- `no_hardcoded_secrets`: Prevent hardcoded credentials
- `require_error_handling`: Require proper error handling
- `require_type_hints`: Require type annotations (Python)

## API Reference

### Main Endpoint
```http
POST /hilde/completion
{
  "prompt": "def hash_password(password):",
  "max_tokens": 100,
  "temperature": 0.1,
  "top_k": 10,
  "enable_analysis": true
}
```

### Response Format
```json
{
  "completion": "return hashlib.sha256(password.encode()).hexdigest()",
  "tokens": [...],
  "top_k_tokens": [...],
  "corrected_entropy_scores": [0.8, 0.2, 0.1],
  "highlighted_positions": [0, 25],
  "constraint_violations": [
    {
      "rule": "no_global_vars",
      "line": 12,
      "column": 0,
      "explanation": "This code defines a global variable, which can cause hidden side effects.",
      "severity": "warning",
      "code_snippet": "global_var = 'value'"
    }
  ]
}
```

### Constraint Checking Endpoint
```http
POST /constraints
{
  "code": "def process_data():\n    global_var = 'value'",
  "language": "python"
}
```

## Development

### Project Structure
```
hilde/
├── completion/          # Completion LLM service
├── analysis/            # Analysis LLM service  
├── gateway/             # API gateway
├── extension/           # VS Code extension
├── models/              # Model storage
├── logs/                # Analytics and logs
├── docker-compose.yml   # Service orchestration
└── README.md
```

### Adding New Languages
1. Update completion service tokenization
2. Add language-specific security rules
3. Extend VS Code extension language support

## Performance

### Latency Targets
- **Completion Generation**: < 2 seconds
- **Alternative Analysis**: < 1 second  
- **Security Scanning**: < 5 seconds (background)

### Resource Requirements
- **Completion LLM**: 2x NVIDIA A100 40GB
- **Analysis LLM**: CPU-only, 8GB RAM
- **Gateway**: 4GB RAM, minimal CPU

## Research & Validation

### Empirical Results
- **31% fewer vulnerabilities** compared to baseline AI assistants
- **76.2 seconds average decision time** vs 35.55 seconds baseline
- **71% of security repairs** occurred with HILDE vs 29% baseline

### User Study Insights
- Users discovered security issues they hadn't considered
- Interface helped overcome "availability heuristic" bias
- Granular control improved confidence-calibration

## Contributing

### Development Setup
```bash
# Install development dependencies
pip install -r requirements.txt

# Run tests
pytest tests/

# Format code
black .
flake8 .
```

### Testing
- Unit tests for core services
- Integration tests for API endpoints
- User experience testing with VS Code extension

## License

MIT License - see LICENSE file for details

## Citation

If you use HILDE in your research, please cite:
```
@article{hilde2024,
  title={HILDE: Human-in-the-Loop Decoding for Intentional Code Generation},
  author={...},
  journal={...},
  year={2024}
}
```

## Support

- **Issues**: GitHub Issues
- **Discussions**: GitHub Discussions  
- **Documentation**: [Wiki](link-to-wiki)

---

Built with ❤️ for intentional, secure, and human-centered AI programming.
