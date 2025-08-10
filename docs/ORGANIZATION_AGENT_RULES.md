# Organization-Wide AI Agent Rules

These rules apply to all AI agents (@claude, @gemini, @codegen) across all repositories in this organization unless overridden by repository-specific rules.

## How to Address AI Agents

### Agent Mentions and Commands

"Use @claude for code implementation, debugging, and Russian language tasks."
"Use @gemini for codebase research, analysis, and information processing."
"Use @codegen for repository-wide changes, PR reviews, and Linear issue resolution."
"Tag agents in Slack threads: @codegen in channel, continue conversation in thread."
"Direct message agents for private consultations: send DM to agent bot."

### Communication Patterns

"Address agents professionally: 'Please implement...', 'Can you analyze...', 'Review this approach...'."
"Be specific about scope: 'Add type hints to services/ directory', 'Fix all failing integration tests'."
"Request step-by-step analysis: 'Explain the multi-backend fallback mechanism in detail'."
"Specify context clearly: 'Using FastAPI patterns from this codebase, implement...'."
"Always include quality requirements: 'With 80% test coverage and full type hints'."

## Model-Specific Usage Guidelines

### @claude - Code Implementation & Development

"Primary agent for writing, modifying, and debugging code."
"Use for implementing new features and fixing bugs."
"Best for Russian language processing and cultural context adaptation."
"Ideal for code review, refactoring, and optimization."
"Strong at test implementation and security analysis."

### @gemini - Research & Codebase Analysis

"Use for exploring and understanding large codebases."
"Excellent for research tasks and information processing with Exa search capabilities."
"Best for analyzing patterns across multiple files and directories."
"Ideal for documentation review and architectural analysis."
"Strong at processing large amounts of information and finding connections."
"Can use Exa tools for deep web research: web_search_exa, company_research_exa, crawling_exa, deep_researcher_start."

### @codegen - Repository Operations

"Use for repository-wide changes and mass refactoring."
"Ideal for Linear issue resolution and automated PR creation."
"Best for cross-file consistency fixes and pattern enforcement."
"Effective for dependency updates and configuration management."
"Good for automated code reviews and compliance checking."

## Security and Access Control

### Data Protection (CRITICAL)

"Never share API keys, secrets, or credentials with any agent."
"Don't expose personal data, user information, or proprietary algorithms."
"Agents should not commit sensitive configuration files (.env, keys, certificates)."
"Always review agent-generated code for security vulnerabilities before merging."

### Repository Access

"Agents operate with permissions of the user who invoked them."
"Repository access is controlled by individual user authentication."
"No agent has independent write permissions without user authorization."
"All agent actions are logged and attributed to the requesting user."

## Code Quality Standards

### Formatting and Style (MANDATORY)

"All agents must follow organization code formatting standards."
"Python: Black + isort + flake8 + mypy enforcement."
"JavaScript/TypeScript: Prettier + ESLint compliance."
"Never commit unformatted code - run linters before any commit."
"Type hints are mandatory for all new functions and methods."

### Testing Requirements

"Minimum 80% test coverage for all new code."
"Include unit tests, integration tests, and end-to-end tests as appropriate."
"Mock external dependencies and API calls in tests."
"Performance tests required for critical path operations."

## Communication and Workflow

### Linear Integration

"Agents can self-assign Linear issues when beginning work."
"Move issues to 'Started' status when beginning implementation."
"Include Linear issue ID in commit messages: 'ENG-123: implement feature'."
"Tag @codegen in Linear issues for automated resolution."

### Slack Integration  

"Create #codegen channel for general agent experimentation."
"Use thread conversations to maintain context with agents."
"Tag relevant team members when agent completes significant work."
"Share agent insights and solutions with team in appropriate channels."

### GitHub Integration

"Agents should create PRs only when explicitly requested."
"Include comprehensive PR descriptions with testing instructions."
"Request human review for all security-sensitive changes."
"Auto-assign PRs to appropriate team members based on code ownership."

## Performance and Cost Optimization

### Efficiency Guidelines

"Use most cost-effective model for routine tasks (Claude Haiku, Gemini Flash)."
"Reserve premium models for complex architectural decisions."
"Prefer batch operations over multiple individual requests."
"Cache frequently requested information and patterns."

### Task Distribution

"Route coding tasks to Claude, research tasks to Gemini."
"Use Claude for implementation, Gemini for exploration and analysis."
"Use Gemini when working with large amounts of information or multiple files."
"Use Claude when writing, debugging, or modifying specific code."
"Optimize prompt design to minimize token usage while maintaining quality."

## Error Handling and Fallbacks

### Graceful Degradation

"When primary agent is unavailable, fallback to alternative models."
"Always implement proper error handling in agent-generated code."
"Include logging and monitoring for agent-performed operations."
"Maintain human oversight for critical system modifications."

### Quality Assurance

"All agent output must be reviewed by qualified team member."
"Run full test suite before merging any agent-generated changes."
"Validate security implications of agent-suggested modifications."
"Document any deviations from standard patterns in code comments."

## Multi-Agent Coordination

### Parallel Operations

"Different agents can work on different components simultaneously."
"Coordinate through shared documentation and Linear issue assignments."
"Avoid conflicting changes by clearly defining agent responsibilities."
"Use branch strategies to isolate agent work until integration."

### Knowledge Sharing

"Agents should reference existing patterns and conventions in codebase."
"Share successful solutions and patterns across agent interactions."
"Update documentation based on agent insights and improvements."
"Maintain consistency in architectural decisions across all agent work."

## Advanced Research Capabilities

### Exa AI Integration (Configured)

"Exa MCP server configured globally with API access for comprehensive web research."
"Available tools: web_search_exa, company_research_exa, crawling_exa, linkedin_search_exa, deep_researcher_start."
"Use for market research, competitive analysis, technical documentation lookup."
"Ideal for gathering current information beyond training data cutoffs."
"Can crawl specific URLs for detailed content extraction and analysis."

### Research Workflow Examples

"@gemini research latest FastAPI testing patterns" - Uses Exa web search + analysis
"@gemini analyze competitor astrological apps" - Uses company research + competitive analysis  
"@gemini find technical documentation for Kerykeion library" - Uses web crawling + synthesis
"@gemini deep research on Russian astrological terminology" - Uses deep researcher for comprehensive analysis

Remember: AI agents are powerful tools that augment human capabilities but require proper oversight, clear communication, and adherence to security best practices.
