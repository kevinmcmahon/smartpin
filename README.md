# 📚 smartpin (`pinit` CLI)

[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-Apache%202.0-green.svg)](LICENSE)
[![Version](https://img.shields.io/badge/version-0.2.3-blue.svg)](https://github.com/kevinmcmahon/smartpin/releases)

> AI-powered Pinboard bookmark manager with cloud-first storage and optional local database

**smartpin** installs the CLI tool `pinit`, which intelligently analyzes web pages and automatically saves bookmarks directly to your Pinboard.in account. By default, bookmarks are stored in the cloud via Pinboard's API for instant access anywhere. Optionally, you can maintain a local SQLite database for offline access and advanced bookmark management using the [pinboard-tools](https://github.com/kevinmcmahon/pinboard-tools) library. Just provide a URL, and AI will extract the title, generate a concise description, and suggest relevant tags - no manual data entry required! 🤖✨

## ✨ Features

- 🤖 **Automatic metadata extraction** - AI analyzes pages to extract title, description, and relevant tags
- 🎯 **Smart tagging** - AI suggests contextually appropriate tags for better organization
- 🔄 **Flexible AI models** - Supports Claude, OpenAI, Gemini, and other LLM providers
- ☁️ **Cloud-first storage** - Bookmarks saved directly to Pinboard.in for instant access anywhere
- 🗄️ **Optional local database** - Offline access and advanced bookmark management via pinboard-tools
- 🔄 **Bidirectional sync** - Keep local database and Pinboard.in perfectly synchronized
- 🌐 **Reliable content fetching** - Local HTTP client with BeautifulSoup for robust page parsing
- 💻 **Rich terminal UI** - Beautiful output with progress indicators and formatted results
- 🧪 **Dry-run mode** - Preview extractions and sync operations without making changes
- 📊 **JSON output** - Machine-readable format for scripting and automation
- 🔒 **Privacy controls** - Mark bookmarks as private or "to read" as needed
- 🏷️ **Advanced tag management** - Tag similarity detection and consolidation (via pinboard-tools)

## 🚀 Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/kevinmcmahon/smartpin.git
cd smartpin

# Install with uv (recommended)
uv pip install -e .

# Or install all dependencies
uv sync
```

### Configuration

**1. Get your Pinboard API token:**

Visit [https://pinboard.in/settings/password](https://pinboard.in/settings/password) to find your API token.

**2. Set up environment variables:**

```bash
# Required: Pinboard authentication
export PINBOARD_API_TOKEN=your_username:your_token

# Required: AI provider API key (choose one based on your model)
export ANTHROPIC_API_KEY=your_key  # For Claude models
# OR
export OPENAI_API_KEY=your_key     # For GPT models
# OR see LLM docs for other providers
```

**3. Optional: Create a `.env` file for persistent configuration:**

```bash
# Create in project directory as .env or at ~/.pinit/config
PINBOARD_API_TOKEN=your_username:your_token

# Choose your AI provider (set the appropriate key)
ANTHROPIC_API_KEY=your_anthropic_api_key  # For Claude models
# OPENAI_API_KEY=your_openai_api_key     # For GPT models

# Optional: specify model (defaults to claude-opus-4.5)
PINIT_MODEL=gpt-5  # or claude-opus-4.5, gpt-4.1, etc.
```

### Basic Usage

```bash
# Add a bookmark with AI analysis (saves directly to Pinboard.in)
pinit add https://example.com

# Preview extraction without saving
pinit add https://example.com --dry-run

# Add private bookmark marked as "to read"
pinit add https://example.com --private --toread

# Sync all bookmarks between local database and Pinboard (optional)
pinit sync

# Get JSON output for scripting
pinit add https://example.com --json
```

## 📖 Usage Examples

### Standard Bookmark Addition

```bash
pinit add https://example.com/ai-software-development
```

**Output:**

```bash
┌─ Extracted Bookmark ─────────────────────────────────┐
│ Title: How to Build Better Software with AI          │
│ URL: https://example.com/ai-software-development      │
│ Description: A comprehensive guide exploring how     │
│ artificial intelligence can enhance software         │
│ development workflows and code quality.              │
│ Tags: ai, software-development, programming, guide   │
└───────────────────────────────────────────────────────┘

✓ Bookmark saved to Pinboard.in successfully!
```

### Database Sync Operations

```bash
# Perform full bidirectional sync
pinit sync

# Preview sync operations without making changes
pinit sync --dry-run

# Check sync status and local database location
pinit config
```

### Advanced Options

```bash
# Use a different AI model
pinit add https://example.com --model gpt-5

# Or use gpt-4.1-nano for faster/cheaper processing
pinit add https://example.com --model gpt-4.1-nano

# Check your configuration and database location
pinit config

# JSON output for automation
pinit add https://example.com --json | jq '.tags'
```

## 🔧 Configuration

### Configuration Loading

Configuration is loaded in this priority order (highest to lowest):

1. System environment variables
2. Local `.env` file (current directory)
3. User configuration `~/.pinit/config`

### Local Database (Optional)

The application can optionally maintain a local SQLite database at `~/.pinit/bookmarks.db` when using the `pinit sync` command. This local database:

- **Provides offline access** to your bookmarks
- **Enables bidirectional sync** with Pinboard.in
- **Supports advanced features** like tag similarity detection and consolidation
- **Automatically initializes** when you first run `pinit sync`
- **Works seamlessly** with the pinboard-tools ecosystem

**Note**: The `pinit add` command saves bookmarks directly to Pinboard.in and does not use the local database. Only the `pinit sync` command creates and maintains the local database.

### AI Model Configuration

The application uses the [LLM library](https://llm.datasette.io/) for flexible AI model integration:

- **Default model**: `claude-opus-4.5` (can be changed via `PINIT_MODEL`)
- **Supported providers**: Anthropic Claude, OpenAI GPT, Google Gemini, and many others
- **Easy model switching**: Change models without code modifications
- **Required API keys** depend on your chosen provider:
  - `ANTHROPIC_API_KEY` for Claude models
  - `OPENAI_API_KEY` for GPT models
  - `GEMINI_API_KEY` for Google Gemini
  - See [LLM documentation](https://llm.datasette.io/en/stable/setup.html) for other providers

### Supported Models

| Provider | Popular Models | Environment Variable |
|----------|---------------|---------------------|
| OpenAI | gpt-5, gpt-4.5-preview, o4-mini, o3, gpt-4.1 | OPENAI_API_KEY |
| Anthropic | claude-opus-4.5, claude-sonnet-4.5, claude-opus-4.1, claude-haiku-4.5 | ANTHROPIC_API_KEY |
| Google | gemini-3-pro-preview, gemini-2.5-pro, gemini-2.5-flash, gemini-2.5-flash-lite | GEMINI_API_KEY |
| Others | Various | See [LLM docs](https://llm.datasette.io/en/stable/other-models.html) |

Choose the model that best fits your needs:

- **Speed**: gpt-4.1-nano, claude-haiku-4.5, gemini-2.5-flash-lite
- **Quality**: gpt-5, claude-opus-4.5, gemini-3-pro-preview
- **Cost**: gpt-4.1-nano, claude-haiku-4.5, gemini-2.5-flash-lite

## 🛠️ Development

### Setup Development Environment

```bash
# Install development dependencies
make dev

# Run all quality checks
make check

# Individual commands
make lint      # Run Ruff linting
make typecheck # Run MyPy type checking
make format    # Auto-format code
make clean     # Remove cache files
```

### Architecture

**smartpin** installs the CLI tool `pinit`, which follows modern Python best practices with:

- **Type hints** throughout the codebase
- **Comprehensive error handling** with user-friendly messages
- **Clean separation of concerns** between CLI, AI processing, and API interactions
- **Rich terminal formatting** for beautiful output
- **Configurable AI models** via the LLM library abstraction

### Core Components

- **`PinboardBookmarkExtractor`** - Interfaces with AI models to analyze web pages
- **`pinboard_client`** - Wrapper functions for Pinboard API operations and sync management
- **`cli`** - Click-based command interface with Rich formatting
- **Local SQLite database** - Managed via pinboard-tools for advanced bookmark operations
- **Bidirectional sync** - Keeps local and remote bookmarks synchronized
- **Jinja2 templates** - Customizable prompts for AI extraction

## 📦 Dependencies

### Core Libraries

- **CLI Framework**: `click` - Command-line interface creation
- **Terminal UI**: `rich` - Beautiful terminal formatting
- **AI Integration**: `llm` - Universal LLM library for multiple providers
- **Bookmark Management**: `pinboard-tools` - Local database and sync capabilities
- **API Client**: `pinboard` - Official Pinboard API client for direct operations
- **Configuration**: `python-dotenv` - Environment variable management
- **Templating**: `jinja2` - Prompt template rendering

### Key Features Enabled by Dependencies

- **pinboard-tools**: Local SQLite database, bidirectional sync, advanced bookmark management
- **llm**: Support for Claude, OpenAI, Gemini, and other AI providers
- **rich**: Beautiful terminal output with progress indicators and formatting

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Run quality checks (`make check`)
4. Commit your changes (`git commit -m 'Add amazing feature'`)
5. Push to the branch (`git push origin feature/amazing-feature`)
6. Open a Pull Request

## 📄 License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built with the excellent [LLM library](https://llm.datasette.io/) by Simon Willison
- Database and sync capabilities powered by [pinboard-tools](https://github.com/kevinmcmahon/pinboard-tools)
- Terminal UI enhanced by [Rich](https://github.com/Textualize/rich)
- Pinboard API by [Pinboard](https://pinboard.in/api/)

---
