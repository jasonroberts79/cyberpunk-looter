# Project settings
- The application files are in src/
- The tests are in tests/
- The IaC is in terraform/
- Always use uv to manage dependencies and virtual environments
- Don't use Makefiles
- When writing code, always use the command 'uv run pyright' to do static type checking and run the tests via 'uv run pytest'

# Structure
- bot.py - this is the main class for running the bot. it should contain code related to receiving Discord commands and delegating the handling to other classes
- bot-reactions.py - this class handles confirmation messages for tool usage with the Discord bot
- llm_service.py - this is the class responsible for making calls to the LLM via the Anthropic SDK
- tool_system.py - this class is responsible for defining tools available to the agent and parsing tool data fields
- memory_system.py - this class handles short and long term memory for the LLM agent
- app_storage.py - this class is responsible for persistence for the application
- graphrag_system.py - this class handles the retrieval augmented generation capabilities for the LLM
- prompt_library.py - this module should define the prompts used by the LLM agent
- app_config.py - a wrapper for loading configuration from envvars and validating their presence
- llm_cli.py - for executing the LLM functionality via CLI

# Modules
- Use @RIPER-5.md

<!-- start: Packmind standards -->
# Packmind Standards

Before starting your work, make sure to review the coding standards relevant to your current task.

Always consult the sections that apply to the technology, framework, or type of contribution you are working on.

All rules and guidelines defined in these standards are mandatory and must be followed consistently.

Failure to follow these standards may lead to inconsistencies, errors, or rework. Treat them as the source of truth for how code should be written, structured, and maintained.

## Standard: Uncle Bob

Conduct comprehensive code reviews using Uncle Bob's Clean Code and SOLID principles to ensure high-quality, maintainable software by focusing on structural elements, meaningful names, and proper error handling when assessing recently written or modified code. :
* No rules defined yet.

Full standard is available here for further request: [Uncle Bob](.packmind/standards/uncle-bob.md)
<!-- end: Packmind standards -->