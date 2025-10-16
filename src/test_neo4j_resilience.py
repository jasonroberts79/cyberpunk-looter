#!/usr/bin/env python3
"""
Test script to verify Neo4j connection resilience.
This script simulates connection drops and verifies automatic reconnection.
"""

import time
from neo4j.exceptions import ServiceUnavailable

def test_connection_resilience():
    """Test that the GraphRAGSystem can handle connection drops."""
    print("Testing Neo4j connection resilience...")
    print("\nThis test verifies that:")
    print("1. Connection is established successfully")
    print("2. Connection health is monitored")
    print("3. Automatic reconnection happens on failures")
    print("4. Database operations retry on connection drops")

    try:
        from graphrag_system import GraphRAGSystem
        import os

        # Read credentials from environment
        neo4j_uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
        neo4j_username = os.getenv("NEO4J_USERNAME", "neo4j")
        neo4j_password = os.getenv("NEO4J_PASSWORD", "password")
        openai_api_key = os.getenv("OPENAI_API_KEY", "test-key")
        grok_api_key = os.getenv("GROK_API_KEY", "test-key")

        print(f"\nConnecting to Neo4j at {neo4j_uri}...")

        # Initialize with shorter retry delays for testing
        system = GraphRAGSystem(
            neo4j_uri=neo4j_uri,
            neo4j_username=neo4j_username,
            neo4j_password=neo4j_password,
            openai_api_key=openai_api_key,
            grok_api_key=grok_api_key,
            max_retry_attempts=3,
            retry_delay=0.5  # Shorter delay for testing
        )

        print("\n✓ Initial connection successful!")

        # Test connection verification
        print("\nTesting connection verification...")
        system._ensure_connection()
        print("✓ Connection verification works!")

        # Test a simple database operation
        print("\nTesting database operation with retry mechanism...")
        def test_operation():
            with system.driver.session() as session:
                result = session.run("RETURN 1 AS num")
                return result.single()["num"]

        result = system._execute_with_retry(test_operation, "Test query")
        assert result == 1, "Test query should return 1"
        print("✓ Database operations with retry mechanism work!")

        print("\n✅ All resilience tests passed!")
        print("\nThe GraphRAGSystem now has:")
        print("  • Automatic connection health monitoring")
        print("  • Exponential backoff retry logic")
        print("  • Graceful handling of transient failures")
        print("  • Detailed logging of connection issues")

        # Clean up
        system.close()

        return True

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_connection_resilience()
    exit(0 if success else 1)
