# Agentic Bot Implementation Plan

## Technical Specification

### File Structure Changes

**New Files:**
- `src/agentic_handler.py` - Tool definitions, confirmation logic, state management
- `tests/test_agentic_confirmation.py` - Unit tests for confirmation system
- `tests/test_agentic_integration.py` - Integration tests for full flow

**Modified Files:**
- `src/bot.py` - Update `!ai` command, add reaction handler, deprecate old commands
- `src/memory_system.py` - No changes (existing methods used as-is)

### Detailed Component Specifications

#### Component 1: Tool Definitions (`src/agentic_handler.py`)

**Function:** `get_tool_definitions() -> List[Dict]`

Returns list of 4 tool definitions in OpenAI/Grok format:
1. `add_party_character` - name (str, required), role (str, required), gear_preferences (list[str], optional, default=[])
2. `remove_party_character` - name (str, required)
3. `view_party_members` - no parameters
4. `recommend_gear` - loot_description (str, required), excluded_characters (list[str], optional, default=[])

#### Component 2: State Management (`src/agentic_handler.py`)

**Global Variable:** `pending_confirmations: Dict[str, Dict] = {}`

Structure:
```python
{
    "<message_id>": {
        "user_id": str,
        "action": str,  # tool name
        "parameters": Dict,  # as received from LLM
        "timestamp": float,  # time.time()
        "processed": bool,  # default False
    }
}
```

**Function:** `add_pending_confirmation(message_id: str, user_id: str, action: str, parameters: Dict) -> None`

**Function:** `get_pending_confirmation(message_id: str) -> Optional[Dict]`

**Function:** `remove_pending_confirmation(message_id: str) -> None`

**Function:** `is_timed_out(confirmation: Dict, timeout_seconds: int = 60) -> bool`

#### Component 3: Confirmation Message Generation (`src/agentic_handler.py`)

**Function:** `generate_confirmation_message(action: str, parameters: Dict) -> str`

Returns formatted confirmation message based on action type. Different formatting for each:
- `add_party_character`: Show name, role, gear preferences
- `remove_party_character`: Show name
- `view_party_members`: Simple confirmation
- `recommend_gear`: Show loot description, excluded characters if any

#### Component 4: Tool Call Handler (`src/agentic_handler.py`)

**Function:** `async def handle_tool_calls(ctx, response, user_id: str, openai_client, memory_system) -> bool`

Returns True if tool calls were handled, False otherwise.

Logic:
1. Check if response contains tool calls
2. For each tool call:
   - Generate confirmation message
   - Send message to Discord
   - Add 👍👎 reactions to message
   - Store in pending_confirmations with message ID as key
3. Return True

#### Component 5: Reaction Handler (`src/bot.py`)

**New Event Handler:** `@bot.event async def on_reaction_add(reaction, user)`

Logic:
1. Skip if user is bot
2. Get message_id from reaction.message.id
3. Check if message_id in pending_confirmations, return if not
4. Get confirmation data
5. Verify user.id matches confirmation["user_id"], return if not
6. Check if confirmation["processed"], if yes: remove reaction and return
7. Check if timed out, if yes: call handle_timeout and return
8. If emoji is 👍: call handle_approval
9. If emoji is 👎: call handle_rejection
10. Mark confirmation as processed

#### Component 6: Approval/Rejection Handlers (`src/agentic_handler.py`)

**Function:** `async def handle_approval(message, confirmation: Dict, memory_system, user_id: str) -> None`

Logic:
1. Mark confirmation as processed
2. Extract action and parameters
3. Execute corresponding memory_system function:
   - `add_party_character`: memory_system.add_party_character(user_id, name, role, gear_preferences)
   - `remove_party_character`: memory_system.remove_party_character(user_id, name)
   - `view_party_members`: memory_system.list_party_characters(user_id)
   - `recommend_gear`: [call recommend_gear logic]
4. Generate success message
5. Send success message as reply to confirmation message
6. Remove from pending_confirmations

**Function:** `async def handle_rejection(message, confirmation: Dict) -> None`

Logic:
1. Mark confirmation as processed
2. Extract action and parameters
3. Generate cancellation message
4. Send cancellation message as reply to confirmation message
5. Remove from pending_confirmations

#### Component 7: Timeout Handler (`src/agentic_handler.py`)

**Function:** `async def handle_timeout(message_id: str, confirmation: Dict, bot) -> None`

Logic:
1. Get message object from Discord using message_id
2. Get original message content
3. Apply strikethrough to all lines: prepend `~~` and append `~~` to each line
4. Append: `\n\n⏱️ Request timed out`
5. Edit message with new content
6. Remove from pending_confirmations

**Function:** `async def check_and_cleanup_timeouts(user_id: str, bot) -> None`

Logic:
1. Iterate through all pending_confirmations
2. Filter to those matching user_id
3. Check if timed out using is_timed_out()
4. For each timed out: call handle_timeout
5. Remove from pending_confirmations

#### Component 8: Modified `!ai` Command (`src/bot.py`)

Changes to existing `ask_question` function at line 111:

1. After user_id extraction (line 117): Call `check_and_cleanup_timeouts(user_id, bot)`
2. In api_params dict (line 134 or 170): Add `"tools": get_tool_definitions()` and `"tool_choice": "auto"`
3. After response from API (line 177 or 312): Call `handled = await handle_tool_calls(ctx, response, user_id, openai_client, memory_system)`
4. If handled is True: return early (don't send normal response)
5. Otherwise: continue with existing flow

#### Component 9: Recommend Gear Integration (`src/agentic_handler.py`)

**Function:** `async def execute_recommend_gear(user_id: str, loot_description: str, excluded_characters: List[str], memory_system, graphrag_system, openai_client, OPENAI_MODEL: str) -> str`

Extract logic from current `!recommend_gear` command (bot.py:212-343) into reusable function.

Returns: recommendation text

#### Component 10: Command Deprecation (`src/bot.py`)

Remove these command handlers:
- `@bot.command(name="add_character")` at line 393
- `@bot.command(name="remove_character")` at line 458
- `@bot.command(name="view_party")` at line 424
- `@bot.command(name="recommend_gear")` at line 212

Update `@bot.command(name="help_rag")` at line 474:
- Remove references to deprecated commands
- Add guidance to use `!ai` for party management and gear recommendations

---

## IMPLEMENTATION CHECKLIST

### Phase 1: Setup and Structure

1. Create new file `src/agentic_handler.py`
2. Add imports to `src/agentic_handler.py`: `import time`, `from typing import Dict, List, Optional, Any`, `import discord`
3. Create global variable `pending_confirmations: Dict[str, Dict] = {}` in `src/agentic_handler.py`

### Phase 2: State Management Functions

4. Implement `add_pending_confirmation(message_id: str, user_id: str, action: str, parameters: Dict) -> None` in `src/agentic_handler.py`
5. Implement `get_pending_confirmation(message_id: str) -> Optional[Dict]` in `src/agentic_handler.py`
6. Implement `remove_pending_confirmation(message_id: str) -> None` in `src/agentic_handler.py`
7. Implement `is_timed_out(confirmation: Dict, timeout_seconds: int = 60) -> bool` in `src/agentic_handler.py`

### Phase 3: Tool Definitions

8. Implement `get_tool_definitions() -> List[Dict]` in `src/agentic_handler.py`
9. Add tool definition for `add_party_character` with parameters: name (required, string), role (required, string), gear_preferences (optional, array of strings)
10. Add tool definition for `remove_party_character` with parameters: name (required, string)
11. Add tool definition for `view_party_members` with no parameters
12. Add tool definition for `recommend_gear` with parameters: loot_description (required, string), excluded_characters (optional, array of strings)

### Phase 4: Confirmation Message Generation

13. Implement `generate_confirmation_message(action: str, parameters: Dict) -> str` in `src/agentic_handler.py`
14. Add formatting logic for `add_party_character` action: show name, role, gear preferences with bullet points
15. Add formatting logic for `remove_party_character` action: show name to be removed
16. Add formatting logic for `view_party_members` action: simple confirmation message
17. Add formatting logic for `recommend_gear` action: show loot description and excluded characters if any
18. Add creative emoji/styling to confirmation messages (choose style during implementation)

### Phase 5: Tool Call Response Parsing

19. Implement function to check if Grok response contains tool calls in `src/agentic_handler.py`
20. Implement function to extract tool calls from Grok response in `src/agentic_handler.py`

### Phase 6: Tool Call Handler

21. Implement `async def handle_tool_calls(ctx, response, user_id: str, openai_client, memory_system, graphrag_system, OPENAI_MODEL: str, bot) -> bool` in `src/agentic_handler.py`
22. Add logic to check if response has tool calls, return False if none
23. Add loop to iterate through tool calls
24. For each tool call: extract action name and parameters
25. For each tool call: generate confirmation message using `generate_confirmation_message()`
26. For each tool call: send confirmation message to Discord channel
27. For each tool call: add 👍 reaction to sent message
28. For each tool call: add 👎 reaction to sent message
29. For each tool call: call `add_pending_confirmation()` with message ID, user ID, action, and parameters
30. Return True after processing all tool calls

### Phase 7: Timeout Handling

31. Implement `async def handle_timeout(message_id: str, confirmation: Dict, bot) -> None` in `src/agentic_handler.py`
32. Add logic to fetch Discord message object from message_id
33. Add logic to get original message content
34. Add logic to apply strikethrough: split by newlines, prepend `~~` and append `~~` to each line
35. Add logic to append `\n\n⏱️ Request timed out` to strikethrough text
36. Add logic to edit Discord message with new content
37. Add logic to call `remove_pending_confirmation(message_id)`
38. Implement `async def check_and_cleanup_timeouts(user_id: str, bot) -> None` in `src/agentic_handler.py`
39. Add logic to iterate through all entries in `pending_confirmations`
40. Add logic to filter confirmations by user_id
41. Add logic to check each confirmation with `is_timed_out()`
42. For timed out confirmations: call `handle_timeout()`

### Phase 8: Recommend Gear Extraction

43. Extract recommend_gear logic from `bot.py` lines 212-343 into new function `async def execute_recommend_gear(user_id: str, loot_description: str, excluded_characters: List[str], memory_system, graphrag_system, openai_client, OPENAI_MODEL: str) -> str` in `src/agentic_handler.py`
44. Modify extracted function to return recommendation text string instead of sending Discord messages
45. Handle empty party case: return error message string
46. Keep GraphRAG context retrieval logic
47. Keep LLM API call logic with prompt construction
48. Return the generated recommendation text

### Phase 9: Action Execution Functions

49. Implement `async def execute_tool_action(action: str, parameters: Dict, user_id: str, memory_system, graphrag_system, openai_client, OPENAI_MODEL: str) -> tuple[bool, str]` in `src/agentic_handler.py`
50. Add case for `add_party_character`: extract name, role, gear_preferences; call `memory_system.add_party_character()`; return success and message
51. Add case for `remove_party_character`: extract name; call `memory_system.remove_party_character()`; check result; return success/failure and message
52. Add case for `view_party_members`: call `memory_system.list_party_characters()`; format result; return success and formatted text
53. Add case for `recommend_gear`: extract loot_description and excluded_characters; call `execute_recommend_gear()`; return success and recommendation

### Phase 10: Approval Handler

54. Implement `async def handle_approval(message: discord.Message, confirmation: Dict, memory_system, graphrag_system, openai_client, OPENAI_MODEL: str, bot) -> None` in `src/agentic_handler.py`
55. Mark confirmation as processed: set `confirmation["processed"] = True`
56. Extract action and parameters from confirmation
57. Extract user_id from confirmation
58. Call `execute_tool_action()` with action, parameters, user_id, and required systems
59. Generate success message based on action and result
60. Send success message as reply to the confirmation message
61. Call `remove_pending_confirmation()` with message_id

### Phase 11: Rejection Handler

62. Implement `async def handle_rejection(message: discord.Message, confirmation: Dict) -> None` in `src/agentic_handler.py`
63. Mark confirmation as processed: set `confirmation["processed"] = True`
64. Extract action and parameters from confirmation
65. Generate cancellation message based on action (e.g., "Cancelled adding {name} to your party")
66. Send cancellation message as reply to the confirmation message
67. Call `remove_pending_confirmation()` with message_id

### Phase 12: Reaction Event Handler

68. Add import `from agentic_handler import *` to `src/bot.py` (at top after other imports)
69. Add new event handler `@bot.event async def on_reaction_add(reaction, user):` to `src/bot.py` after the `on_ready` event handler (after line 108)
70. Add check: if `user.bot`, return
71. Extract `message_id = str(reaction.message.id)`
72. Add check: if `message_id not in pending_confirmations`, return
73. Get confirmation: `confirmation = get_pending_confirmation(message_id)`
74. Add check: if `str(user.id) != confirmation["user_id"]`, return (only requester can confirm)
75. Add check: if `confirmation.get("processed")`, remove reaction and return
76. Add check: if `is_timed_out(confirmation)`, call `handle_timeout()` and return
77. Add check: if `str(reaction.emoji) == "👍"`, call `await handle_approval(reaction.message, confirmation, memory_system, graphrag_system, openai_client, OPENAI_MODEL, bot)`
78. Add check: if `str(reaction.emoji) == "👎"`, call `await handle_rejection(reaction.message, confirmation)`

### Phase 13: Modify `!ai` Command

79. In `src/bot.py`, locate `@bot.command(name="ask")` function at line 111
80. After `user_id = str(ctx.author.id)` at line 117, add call to `await check_and_cleanup_timeouts(user_id, bot)`
81. Locate the `api_params` dictionary construction for the case WITH `previous_response_id` (around line 134)
82. Add `"tools": get_tool_definitions()` to `api_params` dictionary
83. Add `"tool_choice": "auto"` to `api_params` dictionary
84. Locate the `api_params` dictionary construction for the case WITHOUT `previous_response_id` (around line 170)
85. Add `"tools": get_tool_definitions()` to `api_params` dictionary
86. Add `"tool_choice": "auto"` to `api_params` dictionary
87. After `response = openai_client.responses.create(**api_params)` (line 177), add: `handled = await handle_tool_calls(ctx, response, user_id, openai_client, memory_system, graphrag_system, OPENAI_MODEL, bot)`
88. Add check: `if handled: return` to skip normal response processing when tool calls are handled
89. Repeat steps 87-88 for the second API call location (after line 312 in the except block retry logic)

### Phase 14: Deprecate Old Commands

90. Remove `@bot.command(name="add_character")` function entirely (lines 393-421 in `src/bot.py`)
91. Remove `@bot.command(name="view_party")` function entirely (lines 424-455 in `src/bot.py`)
92. Remove `@bot.command(name="remove_character")` function entirely (lines 458-471 in `src/bot.py`)
93. Remove `@bot.command(name="recommend_gear")` function entirely (lines 212-343 in `src/bot.py`)

### Phase 15: Update Help Command

94. Locate `@bot.command(name="help_rag")` function in `src/bot.py` (line 474)
95. Remove `!add_character` from help text
96. Remove `!view_party` from help text
97. Remove `!remove_character` from help text
98. Remove `!recommend_gear` from help text
99. Add guidance: "Use `!ai` to manage your party and get gear recommendations through natural conversation"
100. Update examples to show natural language: "!ai Can you add V to my party? He's a Solo who likes assault rifles"

### Phase 16: Unit Tests - State Management

101. Create new file `tests/test_agentic_confirmation.py`
102. Add imports: `pytest`, `from src.agentic_handler import *`, `from unittest.mock import Mock, AsyncMock`
103. Write test `test_add_pending_confirmation()`: verify confirmation added to dict with correct structure
104. Write test `test_get_pending_confirmation()`: verify retrieval of existing confirmation
105. Write test `test_get_pending_confirmation_not_found()`: verify None returned for non-existent message_id
106. Write test `test_remove_pending_confirmation()`: verify confirmation removed from dict
107. Write test `test_is_timed_out_not_expired()`: verify returns False for recent confirmation
108. Write test `test_is_timed_out_expired()`: verify returns True for old confirmation (>60 seconds)

### Phase 17: Unit Tests - Tool Definitions

109. Write test `test_get_tool_definitions_structure()`: verify returns list of 4 dicts
110. Write test `test_add_party_character_tool_schema()`: verify correct parameters (name required, role required, gear_preferences optional)
111. Write test `test_remove_party_character_tool_schema()`: verify correct parameters (name required)
112. Write test `test_view_party_members_tool_schema()`: verify no required parameters
113. Write test `test_recommend_gear_tool_schema()`: verify correct parameters (loot_description required, excluded_characters optional)

### Phase 18: Unit Tests - Confirmation Messages

114. Write test `test_generate_confirmation_message_add_character()`: verify format includes name, role, gear prefs
115. Write test `test_generate_confirmation_message_remove_character()`: verify format includes character name
116. Write test `test_generate_confirmation_message_view_party()`: verify simple confirmation message
117. Write test `test_generate_confirmation_message_recommend_gear()`: verify includes loot description

### Phase 19: Integration Tests - Setup

118. Create new file `tests/test_agentic_integration.py`
119. Add imports: `pytest`, `from unittest.mock import Mock, AsyncMock, patch`, `from src.bot import *`, `from src.agentic_handler import *`
120. Create fixture `mock_discord_ctx()`: returns mock Discord context with channel, author, etc.
121. Create fixture `mock_grok_client()`: returns mock OpenAI client
122. Create fixture `mock_memory_system()`: returns mock MemorySystem
123. Create fixture `mock_graphrag_system()`: returns mock GraphRAGSystem

### Phase 20: Integration Tests - Tool Call Handling

124. Write test `test_handle_tool_calls_with_add_character()`: mock response with add_party_character tool call, verify confirmation message sent, verify reactions added, verify pending_confirmations updated
125. Write test `test_handle_tool_calls_with_remove_character()`: similar to above for remove action
126. Write test `test_handle_tool_calls_no_tool_calls()`: verify returns False when response has no tool calls
127. Write test `test_handle_tool_calls_multiple_tools()`: verify multiple confirmations created for multiple tool calls

### Phase 21: Integration Tests - Reaction Handling

128. Write test `test_reaction_approval_executes_action()`: mock reaction event with 👍, verify action executed, verify success message sent
129. Write test `test_reaction_rejection_cancels_action()`: mock reaction event with 👎, verify action not executed, verify cancellation message sent
130. Write test `test_reaction_from_wrong_user_ignored()`: verify reaction from different user doesn't execute action
131. Write test `test_subsequent_reactions_removed()`: verify second reaction from same user is removed
132. Write test `test_reaction_after_timeout_ignored()`: verify reaction on timed-out confirmation doesn't execute

### Phase 22: Integration Tests - Timeout Handling

133. Write test `test_timeout_edits_message()`: mock timed-out confirmation, call handle_timeout, verify message edited with strikethrough and timeout text
134. Write test `test_check_and_cleanup_timeouts()`: create multiple confirmations (some expired), call cleanup function, verify expired ones handled
135. Write test `test_timeout_removes_from_pending()`: verify timed-out confirmation removed from pending_confirmations dict

### Phase 23: Integration Tests - End-to-End

136. Write test `test_ask_command_with_tool_call_flow()`: mock full flow from !ai to tool call to confirmation to approval to execution
137. Write test `test_ask_command_normal_flow_no_tools()`: verify normal !ai flow still works when no tool calls in response
138. Write test `test_concurrent_confirmations_different_users()`: verify multiple users can have pending confirmations simultaneously
139. Write test `test_conversation_continues_during_pending()`: verify user can send additional !ai commands while confirmation pending

### Phase 24: Error Handling

140. Add try-except block to `handle_approval()` around `execute_tool_action()` call, catch exceptions and send error message
141. Add try-except block to `handle_timeout()` around message editing, catch NotFound exception if message deleted
142. Add try-except block to `handle_tool_calls()` around tool call parsing, catch KeyError/TypeError and log error
143. Add error message when `view_party_members` returns empty list: "You don't have any party members yet."
144. Add error message when `remove_party_character` returns False: "Character {name} not found in your party."

### Phase 25: Final Testing and Validation

145. Run all unit tests: `uv run pytest tests/test_agentic_confirmation.py -v`
146. Run all integration tests: `uv run pytest tests/test_agentic_integration.py -v`
147. Run existing tests to ensure no regression: `uv run pytest tests/test_party_system.py -v`
148. Run existing tests: `uv run pytest tests/test_recommend_gear_integration.py -v`
149. Run full test suite: `uv run pytest tests/ -v`
150. Manual test: Start bot and test natural language add character
151. Manual test: Test reaction approval
152. Manual test: Test reaction rejection
153. Manual test: Test timeout behavior (wait 60 seconds)
154. Manual test: Test concurrent conversations during pending confirmation
155. Manual test: Test all 4 tool types (add, remove, view, recommend)

---

## Plan Complete

This implementation checklist contains 155 atomic, sequential steps to fully implement the agentic bot functionality. Each step is specific and actionable.

**Ready for:** ENTER EXECUTE MODE
