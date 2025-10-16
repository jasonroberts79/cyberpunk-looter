import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from collections import defaultdict
from app_storage import AppStorage


class MemorySystem:
    def __init__(self, memory_file: str = "long_term_memory.json"):
        self.memory_file = memory_file
        self.storage = AppStorage()
        self.short_term_memory: Dict[str, List[Dict]] = defaultdict(list)
        self.long_term_memory: Dict[str, Dict] = {}
        self.load_long_term_memory()

    def load_long_term_memory(self):
        try:
            data = self.storage.readdata(self.memory_file)
            if data:
                self.long_term_memory = json.loads(data)
                print(f"Loaded long-term memory for {len(self.long_term_memory)} users")
            else:
                self.long_term_memory = {}
        except Exception as e:
            print(f"Error loading long-term memory: {e}")
            self.long_term_memory = {}

    def save_long_term_memory(self):
        try:
            data = json.dumps(self.long_term_memory, indent=2)
            self.storage.writedata(self.memory_file, data)
        except Exception as e:
            print(f"Error saving long-term memory: {e}")

    def add_to_short_term(self, user_id: str, role: str, content: str):
        self.short_term_memory[user_id].append(
            {"role": role, "content": content, "timestamp": datetime.now().isoformat()}
        )

        if len(self.short_term_memory[user_id]) > 10:
            self.short_term_memory[user_id].pop(0)

    def get_short_term_context(self, user_id: str, max_messages: int = 6) -> List[Dict]:
        messages = self.short_term_memory.get(user_id, [])
        return messages[-max_messages:] if messages else []

    def clear_short_term(self, user_id: str):
        if user_id in self.short_term_memory:
            del self.short_term_memory[user_id]

    def update_long_term(self, user_id: str, key: str, value: Any):
        if user_id not in self.long_term_memory:
            self.long_term_memory[user_id] = {
                "user_id": user_id,
                "created_at": datetime.now().isoformat(),
                "preferences": {},
                "interaction_count": 0,
                "topics_discussed": [],
            }

        if key == "interaction":
            self.long_term_memory[user_id]["interaction_count"] += 1
            self.long_term_memory[user_id]["last_interaction"] = (
                datetime.now().isoformat()
            )
        elif key == "preference":
            if "preferences" not in self.long_term_memory[user_id]:
                self.long_term_memory[user_id]["preferences"] = {}
            self.long_term_memory[user_id]["preferences"].update(value)
        elif key == "topic":
            if "topics_discussed" not in self.long_term_memory[user_id]:
                self.long_term_memory[user_id]["topics_discussed"] = []
            if value not in self.long_term_memory[user_id]["topics_discussed"]:
                self.long_term_memory[user_id]["topics_discussed"].append(value)

        self.save_long_term_memory()

    def get_long_term_context(self, user_id: str) -> Optional[Dict]:
        return self.long_term_memory.get(user_id)

    def get_user_summary(self, user_id: str) -> str:
        user_data = self.get_long_term_context(user_id)

        if not user_data:
            return "This is our first conversation."

        summary_parts = []

        if user_data.get("interaction_count", 0) > 0:
            summary_parts.append(
                f"We've interacted {user_data['interaction_count']} times."
            )

        if user_data.get("preferences"):
            prefs = ", ".join(
                [f"{k}: {v}" for k, v in user_data["preferences"].items()]
            )
            summary_parts.append(f"Your preferences: {prefs}")

        if user_data.get("topics_discussed"):
            topics = ", ".join(user_data["topics_discussed"][-5:])
            summary_parts.append(f"Topics we've discussed: {topics}")

        return (
            " ".join(summary_parts)
            if summary_parts
            else "This is our first conversation."
        )
