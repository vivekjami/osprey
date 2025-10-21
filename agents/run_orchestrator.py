"""
Run Pipeline Orchestrator Continuously

Runs orchestration loop at configurable intervals.
Monitors Schema Guardian + Anomaly Detective, makes decisions, executes actions.
"""

import os
import sys
from pathlib import Path
import time
import argparse
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.pipeline_orchestrator import PipelineOrchestrator


def monitor_loop(
    interval_seconds: int = 300,
    max_iterations: int = None
):
    """
    Run orchestrator in continuous loop
    
    Args:
        interval_seconds: Seconds between checks (default: 300 = 5 minutes)
        max_iterations: Max iterations (None = infinite)
    """
    print("=" * 60)
    print("🦅 PIPELINE ORCHESTRATOR - CONTINUOUS MONITORING")
    print("=" * 60)
    print(f"Interval: {interval_seconds} seconds ({interval_seconds/60:.1f} minutes)")
    print(f"Max iterations: {max_iterations or 'Infinite'}")
    print("Press Ctrl+C to stop")
    print("=" * 60)
    
    # Initialize orchestrator
    print("\nInitializing orchestrator...")
    orchestrator = PipelineOrchestrator()
    print("✅ Orchestrator ready!\n")
    
    iteration = 0
    
    try:
        while True:
            iteration += 1
            
            print(f"\n{'='*60}")
            print(f"ITERATION #{iteration} - {datetime.utcnow().isoformat()[:19]}Z")
            print(f"{'='*60}")
            
            # Run orchestration
            try:
                result = orchestrator.orchestrate()
                
                # Summary
                decision = result.get("decision", {})
                action_taken = decision.get("action", "NONE")
                priority = decision.get("priority", "N/A")
                
                print(f"\nIteration Summary:")
                print(f"  Action: {action_taken}")
                print(f"  Priority: {priority}")
                
                if action_taken != "CONTINUE":
                    print(f"  ⚠️  Action executed - check logs above")
                
            except Exception as e:
                print(f"\n❌ Orchestration error: {e}")
                print("   Continuing to next iteration...")
            
            # Check if max iterations reached
            if max_iterations and iteration >= max_iterations:
                print(f"\n✅ Reached max iterations ({max_iterations})")
                break
            
            # Sleep until next check
            print(f"\n💤 Sleeping for {interval_seconds} seconds...")
            print(f"   Next check at: {datetime.utcnow().isoformat()[:19]}Z + {interval_seconds}s")
            
            time.sleep(interval_seconds)
    
    except KeyboardInterrupt:
        print("\n\n⏹️  Orchestrator stopped by user (Ctrl+C)")
    
    finally:
        # Show final summary
        print("\n" + "=" * 60)
        print("FINAL SUMMARY")
        print("=" * 60)
        print(orchestrator.generate_summary())
        
        print("\n👋 Orchestrator shut down gracefully")


def main():
    """Parse arguments and run monitor loop"""
    parser = argparse.ArgumentParser(
        description="Run Pipeline Orchestrator in continuous monitoring mode"
    )
    
    parser.add_argument(
        "--interval",
        type=int,
        default=300,
        help="Seconds between orchestration runs (default: 300 = 5 min)"
    )
    
    parser.add_argument(
        "--max-iterations",
        type=int,
        default=None,
        help="Maximum iterations (default: infinite)"
    )
    
    parser.add_argument(
        "--quick-test",
        action="store_true",
        help="Run 3 iterations with 10-second intervals (for testing)"
    )
    
    args = parser.parse_args()
    
    # Override for quick test
    if args.quick_test:
        print("🧪 Quick test mode: 3 iterations, 10 seconds each\n")
        monitor_loop(interval_seconds=10, max_iterations=3)
    else:
        monitor_loop(
            interval_seconds=args.interval,
            max_iterations=args.max_iterations
        )


if __name__ == "__main__":
    main()
