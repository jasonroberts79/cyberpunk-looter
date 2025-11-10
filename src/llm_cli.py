#!/usr/bin/env python3
"""Command-line test harness for the LLM service."""

import asyncio
import os
from pprint import pprint
from anthropic.types import ToolUseBlock
from dotenv import load_dotenv, dotenv_values

from container import Container

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
        pprint(dotenv_values(".env"))
        self.container = Container()
        self.user_id = "Jason(CLI)"
        self.party_id = os.getenv("RED_PARTY_ID", "default_cli_party")

    def print_banner(self):
        """Print welcome banner."""
        print(f"\n{Colors.BOLD}{Colors.BLUE}{'=' * 70}")
        print("  LLM Service CLI Test Harness")
        print(f"{'=' * 70}{Colors.END}\n")
        print(f"{Colors.GREEN}Commands:{Colors.END}")
        print("  - Type your questions naturally")
        print("  - Commands: 'reindex', 'help', 'exit', 'quit'\n")

    async def initialize(self):
        """Initialize all services."""        
        await self.container.initialize()        
        self.container.conversation_memory.clear_messages(self.user_id)        
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
        print("    reindex   - Force KB reindex")
        print("    help     - Show this help message")
        print("    exit     - Exit the CLI\n")

    async def handle_tool_calls(self, tool_call: ToolUseBlock) -> bool:
        if not self.container.tool_execution_service.requires_confirmation(tool_call.name):            
            result_message = self.container.tool_execution_service.execute_tool(
                tool_call.name, tool_call.input, self.user_id, self.party_id
            )

            print(f"\n{Colors.GREEN}{result_message}{Colors.END}\n")
        else:
            # Print confirmation request
            msg = self.container.tool_registry.generate_confirmation_message(tool_call.name, tool_call.input)
            print(f"\n{Colors.YELLOW}{msg}{Colors.END}\n")

            # Get user confirmation
            while True:
                response = (await asyncio.to_thread(input, f"{Colors.BOLD}Confirm? (y/n): {Colors.END}")).strip().lower()
                if response in ["y", "yes"]:
                    # Execute the action
                    result_message = self.container.tool_execution_service.execute_tool(
                        tool_call.name, tool_call.input, self.user_id, self.party_id
                    )

                    print(f"\n{Colors.GREEN}{result_message}{Colors.END}\n")
                    break
                elif response in ["n", "no"]:
                    print(f"\n{Colors.YELLOW}Action cancelled.{Colors.END}\n")
                    break
                else:
                    print(f"{Colors.RED}Please answer 'y' or 'n'{Colors.END}")

        return True

    async def process_query(self, question: str):
        try:
            print(f"{Colors.YELLOW}Processing...{Colors.END}")            
            content = self.container.conversation_service.process_query(self.user_id, self.party_id, question)
            for block in content:
                if block.type == "text":                
                    print(f"\n{Colors.BOLD}{Colors.BLUE}Assistant:{Colors.END}")
                    print(f"{block.text}\n")
                elif block.type == "tool_use":            
                    await self.handle_tool_calls(block)
        except Exception as e:
            print(f"\n{Colors.RED}Error: {str(e)}{Colors.END}\n")
            import traceback

            traceback.print_exc()

    async def run(self):
        """Run the interactive CLI."""
        await self.initialize()        
        self.print_banner()

        while True:
            try:
                # Get user input
                user_input = (await asyncio.to_thread(input, f"{Colors.BOLD}{Colors.GREEN}You: {Colors.END}")).strip()

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
                await self.process_query(user_input)

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
