# Agentic Bot Architecture - Implementation Design

## Overview

This document outlines the architectural decisions for implementing agentic behavior in the Cyberpunk Looter Discord bot. The goal is to transform explicit commands into natural language interactions through the `!ai` command, with user confirmation via Discord reactions.

## Chosen Approach: Hybrid Interceptor + Conversational

### Core Architecture

**Pattern Name:** "Hybrid: Interceptor + Conversational Confirmation"

**Key Principles:**
1. LLM makes tool calls normally with conversation continuity maintained
2. Intercept tool calls before execution
3. Generate confirmation message and add reactions
4. Track pending action in-memory with timeout
5. Discord reaction events handle execution/cancellation
6. Conversation flow never blocked - users can continue chatting
7. Timeout cleanup handled lazily on interaction

### Why This Approach?

**Advantages:**
- Natural conversation flow maintained throughout
- User can ignore confirmation and keep chatting
- Timeout handles abandoned confirmations gracefully
- Discord reactions provide clear, unambiguous approval path
- LLM context preserved throughout the conversation
- No risk of misinterpreting user messages
- Clean separation of concerns: LLM handles intent, bot handles confirmation

**Rejected Alternatives:**

1. **Two-Phase LLM** - Too slow, extra API calls, parsing brittleness
2. **Wrapper Functions Pattern** - LLM confusion, conversation disruption
3. **State Machine Pattern** - Too rigid, poor UX during confirmation
4. **Text-based Confirmation** - Ambiguous, complex parsing, false positives

## Confirmation Flow Design

### User Experience Flow

```
┌─────────────────────────────────────────────────────────┐
│ User: "Add V to my party, he's a Solo"                  │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│ LLM: Detects intent → Makes tool call                   │
│      add_party_character(name="V", role="Solo", ...)    │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│ Bot: Intercepts tool call                                │
│      Generates confirmation message                      │
│      Adds 👍👎 reactions                                 │
│      Stores pending confirmation                         │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│ Bot displays:                                            │
│ "📋 Confirmation Required                               │
│                                                          │
│  I'll add V to your party:                              │
│  • Role: Solo                                           │
│  • Gear Preferences: None                               │
│                                                          │
│  👍 Confirm  👎 Cancel"                                 │
│ [👍👎 reactions visible]                                 │
└─────────────────────────────────────────────────────────┘
                        ↓
        ┌───────────────┴───────────────┐
        │                               │
   User reacts 👍                  User reacts 👎
        │                               │
        ↓                               ↓
Execute action                    Cancel action
        │                               │
        ↓                               ↓
"✓ V added to party!"          "Cancelled adding V"
        │                               │
        └───────────────┬───────────────┘
                        ↓
            Remove from pending confirmations
```

### Timeout Behavior

**After 60 seconds with no reaction:**

1. Edit the confirmation message:
   - Apply strikethrough to original text
   - Append timeout indicator
2. Remove from pending confirmations
3. Keep reactions visible (historical record)
4. No notification sent to user

**Example:**
```
Before:
📋 Confirmation Required

I'll add V to your party:
• Role: Solo
• Gear Preferences: None

👍 Confirm  👎 Cancel

After timeout:
~~📋 Confirmation Required~~

~~I'll add V to your party:~~
~~• Role: Solo~~
~~• Gear Preferences: None~~

~~👍 Confirm  👎 Cancel~~

⏱️ Request timed out
```

### Reaction Handling Logic

**Rules:**
1. **Only the requesting user** can confirm/cancel (user who sent original message)
2. **First reaction wins** - either 👍 or 👎 locks in the decision
3. **Subsequent reactions ignored** - automatically removed by bot
4. **Other users' reactions ignored** - no processing, no removal

**Implementation:**
```python
@bot.event
async def on_reaction_add(reaction, user):
    # Ignore bot's own reactions
    if user.bot:
        return

    message_id = str(reaction.message.id)

    # Check if this message has a pending confirmation
    if message_id not in pending_confirmations:
        return

    confirmation = pending_confirmations[message_id]

    # Only original requester can confirm
    if str(user.id) != confirmation["user_id"]:
        return

    # Check if already processed
    if confirmation.get("processed"):
        # Remove subsequent reactions
        await reaction.remove(user)
        return

    # Process based on reaction
    if str(reaction.emoji) == "👍":
        # Mark as processed immediately
        confirmation["processed"] = True
        # Execute action
        # Send success message
        # Remove from pending
    elif str(reaction.emoji) == "👎":
        # Mark as processed immediately
        confirmation["processed"] = True
        # Cancel action
        # Send cancellation message
        # Remove from pending
    else:
        # Ignore other reactions
        return
```

## Tool Definitions

### Strategy: Match Memory System Methods

Each tool maps directly to an existing `memory_system` method for clarity and simplicity.

### Tool 1: add_party_character

```json
{
  "type": "function",
  "function": {
    "name": "add_party_character",
    "description": "Add a new character to the party or update an existing character. Requires character name and role. Gear preferences are optional.",
    "parameters": {
      "type": "object",
      "properties": {
        "name": {
          "type": "string",
          "description": "The character's name"
        },
        "role": {
          "type": "string",
          "description": "The character's role (e.g., Solo, Netrunner, Fixer, Rockerboy, etc.)"
        },
        "gear_preferences": {
          "type": "array",
          "items": {
            "type": "string"
          },
          "description": "Optional list of gear types the character prefers (e.g., 'Assault Rifles', 'Body Armor', 'Cyberware')",
          "default": []
        }
      },
      "required": ["name", "role"]
    }
  }
}
```

### Tool 2: remove_party_character

```json
{
  "type": "function",
  "function": {
    "name": "remove_party_character",
    "description": "Remove a character from the party by name.",
    "parameters": {
      "type": "object",
      "properties": {
        "name": {
          "type": "string",
          "description": "The name of the character to remove"
        }
      },
      "required": ["name"]
    }
  }
}
```

### Tool 3: view_party_members

```json
{
  "type": "function",
  "function": {
    "name": "view_party_members",
    "description": "View all current party members with their roles and gear preferences.",
    "parameters": {
      "type": "object",
      "properties": {},
      "required": []
    }
  }
}
```

### Tool 4: recommend_gear

```json
{
  "type": "function",
  "function": {
    "name": "recommend_gear",
    "description": "Get AI-powered gear distribution recommendations for party members based on loot description. Accepts natural language descriptions of loot items.",
    "parameters": {
      "type": "object",
      "properties": {
        "loot_description": {
          "type": "string",
          "description": "Natural language description of the loot to distribute (e.g., 'Assault Rifle, Body Armor, Neural Processor' or 'We got 2 SMGs from the ganger')"
        },
        "excluded_characters": {
          "type": "array",
          "items": {
            "type": "string"
          },
          "description": "Optional list of character names to exclude from gear distribution",
          "default": []
        }
      },
      "required": ["loot_description"]
    }
  }
}
```

## State Management

### Pending Confirmations Structure

**Storage:** In-memory dictionary (ephemeral, not persisted)

```python
pending_confirmations = {
    "<message_id>": {
        "user_id": "123456789",
        "action": "add_party_character",
        "parameters": {
            "name": "V",
            "role": "Solo",
            "gear_preferences": ["Assault Rifles"]
        },
        "timestamp": 1698765432.0,  # Unix timestamp
        "processed": False,  # Set to True after first reaction
        "message_id": "987654321",  # Discord message ID (redundant key for clarity)
    }
}
```

**Key Design Decisions:**
- Message ID as key (needed for reaction event lookup)
- User ID stored (to verify only requester can confirm)
- Action type stored (for executing correct function)
- Parameters stored exactly as received from LLM
- Timestamp for timeout checking
- Processed flag prevents duplicate processing

### Timeout Implementation: Lazy Cleanup

**Strategy:** Check and clean up on interaction, not background tasks

**Implementation:**
1. When user sends message: check all their pending confirmations for timeout
2. When reaction event fires: check if confirmation is timed out before processing
3. On timeout detection: edit message, remove from pending

**Advantages:**
- No background tasks/asyncio overhead
- No accumulation of pending tasks
- Automatic cleanup tied to user activity
- Simple to test and debug

**Timeout Check Function:**
```python
async def check_and_cleanup_timeouts(user_id: str):
    current_time = time.time()
    timeout_threshold = 60  # seconds

    for message_id, confirmation in list(pending_confirmations.items()):
        if confirmation["user_id"] != user_id:
            continue

        if current_time - confirmation["timestamp"] > timeout_threshold:
            # Edit message with strikethrough
            await edit_timeout_message(message_id, confirmation)
            # Remove from pending
            del pending_confirmations[message_id]
```

## Integration Points

### Modified `!ai` Command Flow

**New steps inserted into existing flow:**

```python
@bot.command(name="ask")
async def ask_question(ctx, *, question: str):
    user_id = str(ctx.author.id)

    # [1] NEW: Check and clean up timeouts for this user
    await check_and_cleanup_timeouts(user_id)

    # [Existing: Update memory, get context, etc.]

    # [Existing: Build messages for Grok API]

    # [2] NEW: Add tools to API call
    api_params = {
        "model": OPENAI_MODEL,
        "input": input_messages,
        "temperature": 0.6,
        "tools": get_tool_definitions(),  # NEW
        "tool_choice": "auto",  # NEW
    }

    # [Existing: Make API call]
    response = openai_client.responses.create(**api_params)

    # [3] NEW: Check for tool calls in response
    if has_tool_calls(response):
        # Generate confirmation messages
        for tool_call in get_tool_calls(response):
            await handle_tool_call(ctx, tool_call, user_id)
        return  # Don't send normal response

    # [Existing: Send normal response]
```

### New Event Handler: on_reaction_add

**New event handler to be added:**

```python
@bot.event
async def on_reaction_add(reaction, user):
    """Handle confirmation/cancellation via reactions"""

    # Skip bot's own reactions
    if user.bot:
        return

    message_id = str(reaction.message.id)

    # Check if this message has a pending confirmation
    if message_id not in pending_confirmations:
        return

    confirmation = pending_confirmations[message_id]

    # Only original requester can confirm
    if str(user.id) != confirmation["user_id"]:
        return

    # Check if already processed
    if confirmation.get("processed"):
        # Remove subsequent reactions from this user
        await reaction.remove(user)
        return

    # Check for timeout
    if is_timed_out(confirmation):
        await handle_timeout(message_id, confirmation)
        return

    # Process reaction
    if str(reaction.emoji) == "👍":
        await handle_approval(reaction.message, confirmation)
    elif str(reaction.emoji) == "👎":
        await handle_rejection(reaction.message, confirmation)
```

## Confirmation Message Formatting

### Creative Options (to be chosen during implementation)

**Option A: Cyberpunk-Themed**
```
🔐 Security Clearance Required

ACTION: Add character to party roster
├─ Name: V
├─ Role: Solo
└─ Gear Preferences: Assault Rifles, Body Armor

React 👍 to authorize | 👎 to abort
```

**Option B: Terminal-Style**
```
> PARTY_MANAGER.exe
> Pending operation: ADD_CHARACTER
>
> CHARACTER_DATA {
>   name: "V",
>   role: "Solo",
>   gear: ["Assault Rifles", "Body Armor"]
> }
>
> Confirm? 👍 Yes / 👎 No
```

**Option C: Simple & Clean**
```
📋 Confirmation Required

I'll add V to your party:
• Role: Solo
• Gear Preferences: Assault Rifles, Body Armor

👍 Confirm  👎 Cancel
```

**Formatting will vary by action type for better UX**

### Result Messages

**Success Messages:**
- `add_party_character`: "✓ {name} has been added to your party!"
- `remove_party_character`: "✓ {name} has been removed from your party."
- `view_party_members`: [Display formatted party list]
- `recommend_gear`: [Display recommendations]

**Cancellation Messages:**
- `add_party_character`: "Cancelled adding {name} to your party."
- `remove_party_character`: "Cancelled removing {name} from your party."
- `view_party_members`: "Cancelled viewing party members."
- `recommend_gear`: "Cancelled gear recommendation."

## Command Deprecation Strategy

### Commands to Deprecate

These commands will be removed/disabled:
- `!add_character`
- `!remove_character`
- `!view_party`
- `!recommend_gear`

### Deprecation Approach

**Option 1: Remove entirely**
- Delete command handlers
- Update help text

**Option 2: Soft deprecation**
- Keep commands but show deprecation message
- Guide users to use `!ai` instead
- Remove after transition period

**Recommendation:** Remove entirely for cleaner codebase

## Error Handling

### Edge Cases

1. **User deletes confirmation message**
   - Reaction event won't fire
   - Timeout cleanup will handle eventually
   - No action needed

2. **Bot loses permissions to add reactions**
   - Fallback: send message without reactions
   - Or send error message explaining permissions needed

3. **Tool execution fails**
   - Send error message to user
   - Remove from pending confirmations
   - Log error for debugging

4. **LLM returns malformed tool call**
   - Catch parsing errors
   - Send message: "I couldn't process that request. Please try again."
   - Continue conversation normally

5. **Multiple tool calls in one response**
   - Process sequentially
   - Create separate confirmation message for each
   - Each gets its own pending confirmation entry

6. **User reacts with both 👍 and 👎**
   - First reaction wins
   - Second reaction automatically removed
   - Action executes/cancels based on first

## Testing Strategy

### Unit Tests

**New test file:** `tests/test_agentic_confirmation.py`
- Test confirmation message generation
- Test timeout detection
- Test reaction validation (correct user, correct emoji)
- Test state management (add/remove pending confirmations)

### Integration Tests

**New test file:** `tests/test_agentic_integration.py`
- Mock Grok API responses with tool calls
- Test full flow: intent → confirmation → execution
- Test timeout message editing
- Test multiple pending confirmations
- Test reaction handling end-to-end

### Existing Tests to Update

- `tests/test_party_system.py` - Should still pass (underlying functions unchanged)
- `tests/test_recommend_gear_integration.py` - Should still pass

## Success Metrics

Implementation is complete when:

1. ✓ Users can add characters via natural language
2. ✓ Users can remove characters via natural language
3. ✓ Users can view party via natural language
4. ✓ Users can request gear recommendations via natural language
5. ✓ All actions require reaction-based confirmation
6. ✓ Timeouts work (60 seconds, strikethrough + message)
7. ✓ First reaction wins, subsequent reactions removed
8. ✓ Conversations continue uninterrupted during pending confirmations
9. ✓ Old commands deprecated/removed
10. ✓ All tests pass

## Implementation Checklist Preview

High-level tasks (detailed checklist in PLAN mode):

1. Define tool schemas
2. Create confirmation message generator
3. Implement state management (pending confirmations dict)
4. Modify `!ai` command to include tools
5. Add tool call interceptor/handler
6. Implement reaction event handler
7. Implement timeout checking and message editing
8. Update/remove deprecated commands
9. Write tests
10. Documentation updates

## Next Phase

**→ PLAN MODE**: Create detailed, step-by-step implementation checklist
