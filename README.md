# HiLDe-Lite: Streamlined Code Assistant

A focused, modular code generation system implementing the **Generate → Analyze → Summarize** workflow.

## 🏗️ Architecture

### Core Components

1. **HiLDeCompletionEngine** (`hilde_lite_completion_engine.py`)
   - Generates code completions using Qwen2.5-Coder-7B
   - Simplified, single-purpose component

2. **ConstraintDebugger** (`hilde/analysis/constraint_debugger.py`)
   - Performs fast, local AST-based analysis
   - Checks for: global variables, input sanitization, function length
   - Produces raw, technical violation data

3. **GPT4AnalysisEngine** (`hilde_lite_analysis_engine.py`)
   - Converts technical violations into human-readable summaries
   - Uses GPT-4 API with expert prompting
   - Includes fallback for API unavailability

4. **HiLDeLiteGateway** (`hilde_lite_api_gateway.py`)
   - Orchestrates the three-step workflow
   - Provides REST API endpoints
   - Returns structured responses

## 🔄 Workflow

```
Prompt → Generate → Analyze → Summarize → Response
```

1. **Generate**: Create code completion
2. **Analyze**: Check constraints with AST parsing
3. **Summarize**: Convert violations to human-readable explanations

## 🚀 Quick Start

```bash
# Install dependencies
pip install -r hilde/requirements.txt

# Set OpenAI API key
export OPENAI_API_KEY="your-key-here"

# Run the gateway
python hilde_lite_api_gateway.py

# Test the workflow
python test_new_workflow.py
```

## 📡 API Usage

```bash
curl -X POST http://localhost:5000/hilde/completion \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "def process_user_input():",
    "max_tokens": 100,
    "enable_analysis": true
  }'
```

## 📋 Response Format

```json
{
  "completion": "Generated code string",
  "constraint_violations": [
    {
      "rule": "no_global_vars",
      "line": 12,
      "explanation": "Global variables can cause hidden side effects",
      "severity": "warning"
    }
  ],
  "summary": "GPT-4 generated human-readable summary",
  "metadata": {
    "violations_count": 1,
    "components_used": ["HiLDeCompletionEngine", "ConstraintDebugger", "GPT4AnalysisEngine"]
  }
}
```

## 🎯 Key Features

- **Modular Design**: Each component has a single, focused responsibility
- **Fast Analysis**: Local AST parsing for immediate constraint checking
- **Human-Readable**: GPT-4 powered explanations of technical violations
- **Robust**: Fallback mechanisms for API unavailability
- **Configurable**: Easy rule customization via `constraints.json`

## 📁 Project Structure

```
├── hilde_lite_api_gateway.py      # Main API gateway
├── hilde_lite_completion_engine.py # Code generation
├── hilde_lite_analysis_engine.py   # GPT-4 summarization
├── test_new_workflow.py           # Workflow validation
├── hilde/
│   ├── analysis/
│   │   └── constraint_debugger.py # AST-based analysis
│   ├── constraints.json           # Rule definitions
│   └── requirements.txt           # Dependencies
└── README.md                      # This file
```

This streamlined architecture focuses on the core value proposition: combining local code generation with intelligent constraint checking and AI-powered explanations.