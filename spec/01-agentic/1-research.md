# Agentic Bot Research - Making Commands Inferrable

## Project Overview

Transform the Cyberpunk Looter Discord bot from explicit command-based interactions to agentic, natural language-driven functionality. Users should be able to perform party management and gear recommendation actions through conversational requests in the `!ai` command.

## Current System Architecture

### Bot Structure
- **Platform:** Discord bot using `discord.py` (discord.ext.commands)
- **Command Prefix:** `!`
- **AI Backend:** Grok API (xAI) via OpenAI-compatible client
- **Model:** `grok-4-fast`
- **Base URL:** `https://api.x.ai/v1`

### Existing Commands

**Active Commands (to remain):**
- `!ai <question>` - Main conversational interface with knowledge base
- `!reindex [force]` - Rebuild knowledge graph
- `!clear` - Clear conversation history
- `!memory` - View interaction summary
- `!help_rag` - Show help message

**Commands to Deprecate (make agentic):**
- `!add_character <name> <role> <gear_prefs>` - Add/update party character
- `!remove_character <name>` - Remove party character
- `!view_party` - View all party members
- `!recommend_gear <loot>` - Get AI gear recommendations

### Core Systems

#### Memory System (`src/memory_system.py`)
- **Storage:** JSON-based persistent storage via `AppStorage`
- **Short-term Memory:** Last 10 messages per user (in-memory)
- **Long-term Memory:** User profiles, interaction counts, topics, party data (persistent)
- **Response Tracking:** Stores `previous_response_id` for conversation continuity
- **Party Storage:** Characters stored in `long_term_memory[user_id]["party_members"]`
  - Character key: lowercase name
  - Data: name, role, gear_preferences, created_at, updated_at

#### GraphRAG System (`src/graphrag_system.py`)
- **Database:** Neo4j graph database
- **Embeddings:** OpenAI `text-embedding-3-small`
- **Purpose:** Knowledge base about Cyberpunk RED RPG
- **Features:** Vector similarity search, sequential chunk relationships, incremental indexing

#### Current `!ai` Flow (bot.py:111-209)
1. Update long-term interaction count
2. Add user message to short-term memory
3. Retrieve knowledge base context (k=10)
4. Get user summary and party summary
5. Get previous response ID (if exists)
6. Build input messages:
   - If `previous_response_id` exists: send only new message
   - Otherwise: send system prompt + conversation history + new message
7. Call Grok API (`openai_client.responses.create()`)
8. Save response ID for future continuations
9. Add assistant response to short-term memory
10. Send response to Discord

## Grok API Capabilities

### Responses API - Input Parameters

```python
openai_client.responses.create(
    model="grok-4-fast",
    input=[...],  # string | array - text, image, or file
    previous_response_id=None,  # string | null - ID of previous response
    instructions=None,  # string | null - alternate system prompt (incompatible with previous_response_id)
    tools=None,  # array | null - max 128 tools (functions and web search)
    tool_choice=None,  # null | string | object - control tool invocation
    parallel_tool_calls=True,  # boolean - allow parallel tool calls (default: true)
    temperature=0.6,  # number - 0 to 2
    max_output_tokens=None,  # integer | null - includes output and reasoning tokens
    stream=False,  # boolean - server-sent events
    store=True,  # boolean - store messages for later retrieval
    # ... other parameters (logprobs, top_p, reasoning, search_parameters, etc.)
)
```

### Function Calling Support
- ✓ Standard function calling/tools (OpenAI-compatible)
- ✓ Parallel tool calls enabled by default
- ✓ Max 128 tools per request
- ✓ Supports web search as a tool type
- ✓ Tool choice parameter for controlling invocation

### Conversation Continuity
- Uses `previous_response_id` to maintain conversation state
- Incompatible with `instructions` parameter (system prompt from previous message is reused)
- Response ID must be tracked per user

## Target Agentic Behavior

### User Experience Goals

**Natural Language Intent Detection:**
- User: "Add V to my party, he's a Solo who likes assault rifles"
- Bot: Detects intent → Extracts parameters → Asks for confirmation → Executes

**Examples:**
```
User: "Can you add Johnny to the party?"
Bot: "I can add Johnny to your party. What role is Johnny?"
User: "He's a Rockerboy"
Bot: "Got it. Does Johnny have any gear preferences?"
User: "Handguns"
Bot: "I'd like to add:
     • Name: Johnny
     • Role: Rockerboy
     • Gear Preferences: Handguns

     Should I proceed? 👍👎"
User: "yes"
Bot: "✓ Johnny has been added to your party!"
```

### Actions to Make Agentic

1. **Add Party Character**
   - Required: name, role
   - Optional: gear_preferences (can be empty list)
   - Function: `memory_system.add_party_character(user_id, name, role, gear_preferences)`
   - Returns: boolean (True if new, False if updated)

2. **Remove Party Character**
   - Required: name
   - Function: `memory_system.remove_party_character(user_id, name)`
   - Returns: boolean (True if removed, False if not found)

3. **View Party Members**
   - No parameters required
   - Function: `memory_system.list_party_characters(user_id)`
   - Returns: List[Dict] with character data

4. **Recommend Gear Distribution**
   - Required: loot_description (natural language)
   - Optional: excluded_characters (list of names to exclude)
   - Current implementation: Custom function with GraphRAG context
   - Returns: AI-generated recommendation text

### Confirmation Flow Requirements

**Confirmation Request:**
- Must show extracted/inferred parameters clearly
- Add both text explanation AND reaction options (👍/👎)
- Use natural, conversational language

**Confirmation Response:**
- **Reactions:** 👍 = approve, 👎 = reject
- **Text:** Natural language understanding
  - Approval: "yes", "y", "sure", "ok", "do it", "go ahead", "yep", "yeah", "correct", "proceed", etc.
  - Rejection: "no", "n", "nope", "cancel", "don't", "nah", "stop", "nevermind", etc.
- **Timeout:** 1 minute - if no response, expire silently
- **Continuation:** User can continue other conversations while confirmation is pending

**Multi-Action Handling:**
- Each action gets separate confirmation
- Process sequentially, not in bulk
- Example: "Add V and remove Johnny" → confirm add first, then confirm remove

**State Management:**
- In-memory only (ephemeral)
- No persistence across bot restarts required
- Track pending confirmations per user
- Store: action type, parameters, message ID (for reactions), timestamp

### Parameter Collection Strategy

**Before Making Tool Calls:**
1. LLM detects user intent
2. LLM identifies missing required parameters
3. LLM asks follow-up questions naturally in conversation
4. Once all required parameters collected, LLM makes tool call
5. Bot intercepts tool call and requests confirmation
6. Upon confirmation, execute the actual function

**Example Flow:**
```
User: "Add a new character"
Bot: (detects intent but missing params)
     "I can help with that! What's the character's name?"
User: "Tank"
Bot: "Got it. What role is Tank?"
User: "Solo"
Bot: "Does Tank have any gear preferences?"
User: "Heavy armor and shields"
Bot: (now has all params, makes tool call internally)
     "I'd like to add:
      • Name: Tank
      • Role: Solo
      • Gear Preferences: Heavy armor, shields

      Should I proceed? 👍👎"
User: 👍 (reaction)
Bot: "✓ Tank has been added to your party!"
```

## Technical Considerations

### Discord Integration
- **Reactions:** Use `discord.Message.add_reaction()` to add 👍👎
- **Reaction Events:** Listen with `@bot.event async def on_reaction_add()`
- **Message Tracking:** Store message ID with pending confirmation
- **Timeout:** Use `asyncio.sleep()` or `asyncio.wait_for()` with 60-second timeout

### State Management Schema
```python
pending_confirmations = {
    "user_id": {
        "action": "add_character",  # or "remove_character", "view_party", "recommend_gear"
        "parameters": {
            "name": "V",
            "role": "Solo",
            "gear_preferences": ["Assault Rifles"]
        },
        "message_id": "123456789",  # Discord message ID for reaction tracking
        "timestamp": "2025-10-21T...",  # For timeout checking
        "conversation_context": {...}  # Any context needed to resume conversation
    }
}
```

### Tool Definitions
Need to define 4 tools for Grok:

1. **add_party_character**
   - Parameters: name (string), role (string), gear_preferences (array of strings, optional)

2. **remove_party_character**
   - Parameters: name (string)

3. **view_party_members**
   - Parameters: none

4. **recommend_gear**
   - Parameters: loot_description (string), excluded_characters (array of strings, optional)

### Integration Points

**Modify `!ai` Command:**
- Add `tools` parameter to Grok API call
- Check response for tool calls
- When tool call detected:
  - Generate confirmation message with parameters
  - Add to pending confirmations
  - Add reactions to message
  - Continue conversation normally
- Handle confirmation responses in next user message
- Execute tool and report result

**Add Reaction Handler:**
- New `@bot.event async def on_reaction_add(reaction, user)`
- Check if message has pending confirmation
- Check if user is the original requester
- Execute or cancel based on 👍/👎
- Remove from pending confirmations

**Add Confirmation Cleanup:**
- Background task or check on each message
- Remove confirmations older than 1 minute
- Clean up stale state

## Testing Considerations

### Test Files to Update
- `tests/test_party_system.py` - Party management tests
- `tests/test_recommend_gear_integration.py` - Gear recommendation tests
- New file needed: `tests/test_agentic_commands.py` - Integration tests for agentic behavior

### Test Scenarios
1. Intent detection with complete parameters
2. Intent detection with missing parameters (follow-up questions)
3. Confirmation approval (text)
4. Confirmation approval (reaction)
5. Confirmation rejection
6. Confirmation timeout
7. Multiple pending confirmations for same user
8. Concurrent conversations while confirmation pending
9. Invalid/malformed parameters
10. Multi-action scenarios

## Dependencies

### Current Dependencies (pyproject.toml)
- discord.py >= 2.4.0
- openai >= 2.3.0 (for Grok API client)
- python-dotenv >= 1.1.1
- neo4j-graphrag >= 1.10.0
- langchain >= 0.3.27

### No New Dependencies Required
All functionality can be implemented with existing libraries.

## Open Questions

### Resolved
- ✓ Confirmation timeout: 1 minute
- ✓ Concurrent conversations: Yes, allowed
- ✓ Parameter collection: Ask follow-ups before tool calls
- ✓ Confirmation format: Natural language + reactions
- ✓ State persistence: In-memory only
- ✓ API capabilities: Full function calling support

### To Be Determined During Implementation
- Exact tool call response format from Grok (assumed OpenAI-compatible)
- Error handling when tool execution fails
- Handling of edge cases (e.g., user deletes confirmation message)
- UX for expired confirmations (silent vs notification)

## Success Criteria

1. Users can perform all party management actions through natural language in `!ai`
2. Bot correctly identifies intent and extracts parameters
3. Bot asks follow-up questions when parameters are missing
4. Confirmation flow works with both text and reactions
5. Confirmations timeout after 1 minute
6. Users can continue conversations while confirmations are pending
7. Multi-action requests are handled sequentially with separate confirmations
8. Deprecated commands removed or marked as deprecated
9. All existing tests pass
10. New integration tests cover agentic behavior

## Next Steps

1. **INNOVATE MODE:** Brainstorm different architectural approaches
2. **PLAN MODE:** Create detailed implementation plan
3. **EXECUTE MODE:** Implement the solution
4. **REVIEW MODE:** Validate against plan
