"""Prompt library for the LLM agent.

This module defines all prompts used by the LLM agent, including system prompts,
user prompts, and context templates.
"""

# Game context used across all prompts
GAME_CONTEXT = (
    "You have with access to a knowledge base about the RPG Cyberpunk RED. "
    "Be careful not to make up answers or to use information about the other "
    "Cyberpunk games (like Cyberpunk 2077 or Cyberpunk 2020)."
)


def create_main_system_prompt(
    context: str, user_summary: str, party_summary: str
) -> str:
    """
    Create the main system prompt for the LLM assistant.

    Args:
        context: Knowledge base context retrieved from GraphRAG
        user_summary: Summary of user's interaction history
        party_summary: Summary of user's party members

    Returns:
        The complete system prompt string
    """
    return f"""You are a helpful AI assistant.
{GAME_CONTEXT}
User Context: {user_summary}
Party Context:
{party_summary}
Use the following context from the knowledge base to answer questions. If the answer isn't in the context, say so clearly.
Knowledge Base Context:
{context}
Be concise and direct. Remember details from our conversation."""


def create_gear_recommendation_system_prompt() -> str:
    """
    Create the system prompt for gear recommendation requests.

    Returns:
        The system prompt for gear recommendations
    """
    return (
        "You are a knowledgeable game master who helps parties distribute loot "
        "fairly and strategically with access to a knowledge base about the RPG "
        "Cyberpunk RED. Be careful not to make up answers or to use information "
        "about the other Cyberpunk games (like Cyberpunk 2077 or Cyberpunk 2020) "
        "unless it is explicitly in the knowledge base."
    )


def create_gear_recommendation_user_prompt(
    loot_description: str, party_context: str, knowledge_context: str
) -> str:
    """
    Create the user prompt for gear recommendation requests.

    Args:
        loot_description: Natural language description of the loot
        party_context: Formatted string describing party members
        knowledge_context: Context from the knowledge base about the gear

    Returns:
        The complete user prompt for gear recommendations
    """
    return f"""Please help distribute this loot among my party members.
{GAME_CONTEXT}

Party Context:
{party_context}

Loot Description:
{loot_description}

Use the knowledge base context, if needed, to inform your recommendation:
{knowledge_context}

Parse the loot description to identify individual items, then recommend how to distribute them among the party members. Consider:
1. Character roles and their typical gear needs
2. Each character's stated gear preferences
3. Fair distribution when preferences conflict
4. Overall party effectiveness
5. The market value of the item if no clear preference can be determined

Provide your recommendations in this format:
**[Character Name]** ([Role])
  - [Item 1]
  - [Item 2]
  ..."""
