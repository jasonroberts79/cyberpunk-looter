#!/usr/bin/env python3
"""Command-line test harness for the LLM service."""

import asyncio
import json
import os
from pprint import pprint
from dotenv import load_dotenv, dotenv_values

from llm_service import LLMService
from memory_system import MemorySystem
import tool_system


# ANSI color codes for terminal output
class Colors:
    BLUE = "\033[94m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"
    END = "\033[0m"


class LLMCLIHarness:
    """CLI test harness for LLM service."""

    def __init__(self):
        """Initialize the test harness."""
        load_dotenv()

        self.user_id = "Jason(CLI)"
        self.party_id = os.getenv('RED_PARTY_ID', 'default_cli_party')

    def print_banner(self):
        """Print welcome banner."""
        print(f"\n{Colors.BOLD}{Colors.BLUE}{'=' * 70}")
        print("  LLM Service CLI Test Harness")
        print(f"{'=' * 70}{Colors.END}\n")
        print(f"{Colors.GREEN}Commands:{Colors.END}")
        print("  - Type your questions naturally")
        print("  - Type 'help' for more commands")
        print("  - Type 'exit' or 'quit' to quit\n")

    async def initialize(self):
        """Initialize all services."""
        pprint(dotenv_values(".env"))

        print(f"{Colors.YELLOW}Initializing services...{Colors.END}")
        print(f"{Colors.YELLOW}  → Building knowledge graph...{Colors.END}")

        # Initialize memory system
        print(f"{Colors.YELLOW}  → Initializing memory system...{Colors.END}")
        self.memory_system = MemorySystem()
        self.memory_system.clear_short_term(self.user_id)

        # Initialize LLM service
        print(f"{Colors.YELLOW}  → Initializing LLM service...{Colors.END}")
        self.llm_service = LLMService(self.memory_system)
        print(f"{Colors.GREEN}✓ All services initialized successfully!{Colors.END}\n")

    def print_help(self):
        """Print help information."""
        print(f"\n{Colors.BOLD}{Colors.BLUE}Available Commands:{Colors.END}")
        print(f"\n  {Colors.BOLD}Natural Language Queries:{Colors.END}")
        print("    'What are assault rifles in Cyberpunk RED?'")
        print("    'Add V to my party as a Solo who likes assault rifles'")
        print("    'Remove Johnny from the party'")
        print("    'Recommend gear for: assault rifle, cyberdeck, body armor'")

        print(f"\n  {Colors.BOLD}System Commands:{Colors.END}")
        print("    party    - View current party members")
        print("    clear    - Clear conversation history")
        print("    memory   - View user interaction summary")
        print("    help     - Show this help message")
        print("    exit     - Exit the CLI\n")

    def handle_tool_calls(self, tool_calls: list) -> bool:
        assert self.llm_service is not None
        """Handle tool calls with user confirmation."""
        if not tool_calls:
            return False

        for tool_call in tool_calls:
            tool_name = tool_call["name"]
            tool_arguments = tool_call["arguments"]
            if not tool_system.is_tool_confirmation_required(tool_name):
                # Execute the action directly
                result_message = self.llm_service.execute_tool_action(
                    tool_name, tool_arguments, self.user_id, self.party_id
                )

                print(f"\n{Colors.GREEN}{result_message}{Colors.END}\n")
                continue
            if isinstance(tool_arguments, str):
                parameters = json.loads(tool_arguments)
            else:
                parameters = tool_arguments

            # Generate confirmation message
            confirmation_msg = tool_system.generate_confirmation_message(tool_name, parameters)

            # Print confirmation request
            print(f"\n{Colors.YELLOW}{confirmation_msg}{Colors.END}\n")

            # Get user confirmation
            while True:
                response = (
                    input(f"{Colors.BOLD}Confirm? (y/n): {Colors.END}").strip().lower()
                )
                if response in ["y", "yes"]:
                    # Execute the action
                    result_message = self.llm_service.execute_tool_action(
                        tool_name, parameters, self.user_id, self.party_id
                    )

                    print(f"\n{Colors.GREEN}{result_message}{Colors.END}\n")
                    break
                elif response in ["n", "no"]:
                    print(f"\n{Colors.YELLOW}Action cancelled.{Colors.END}\n")
                    break
                else:
                    print(f"{Colors.RED}Please answer 'y' or 'n'{Colors.END}")

        return True

    def process_query(self, question: str):
        """Process a user query."""
        if not self.llm_service:
            print(f"{Colors.RED}Error: LLM service not initialized{Colors.END}")
            return

        try:
            print(f"{Colors.YELLOW}Processing...{Colors.END}")
            response = self.llm_service.process_query(self.user_id, self.party_id, question)
            tool_calls = self.llm_service.extract_tool_calls(response)
            # Handle tool calls if present
            if tool_calls is not None:
                self.handle_tool_calls(tool_calls)
                return

            # Get the answer text
            answer = self.llm_service.get_answer(response)
            if not answer:
                answer = "I couldn't generate a response."

            # Print the response
            print(f"\n{Colors.BOLD}{Colors.BLUE}Assistant:{Colors.END}")
            print(f"{answer}\n")

        except Exception as e:
            print(f"\n{Colors.RED}Error: {str(e)}{Colors.END}\n")
            import traceback

            traceback.print_exc()

    async def run(self):
        """Run the interactive CLI."""
        await self.initialize()
        await self.llm_service.initialize()
        self.print_banner()

        while True:
            try:
                # Get user input
                user_input = input(
                    f"{Colors.BOLD}{Colors.GREEN}You: {Colors.END}"
                ).strip()

                if not user_input:
                    continue

                # Handle system commands
                if user_input.lower() in ["exit", "quit"]:
                    print(f"\n{Colors.BLUE}Goodbye!{Colors.END}\n")
                    break

                elif user_input.lower() == "help":
                    self.print_help()
                    continue

                # Process as a query
                self.process_query(user_input)

            except KeyboardInterrupt:
                print(f"\n\n{Colors.BLUE}Goodbye!{Colors.END}\n")
                break
            except EOFError:
                print(f"\n\n{Colors.BLUE}Goodbye!{Colors.END}\n")
                break
            except Exception as e:
                print(f"\n{Colors.RED}Error: {str(e)}{Colors.END}\n")
                import traceback

                traceback.print_exc()


async def main():
    """Main entry point."""
    harness = LLMCLIHarness()
    await harness.run()


if __name__ == "__main__":
    asyncio.run(main())
