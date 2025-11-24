"""
Comprehensive fix for all remaining test files
Updates them to use YOUR actual momentum tracker
"""
import os
import re

def update_file_header(content, filename):
    """Add actual momentum tracker import"""
    # Add import after the docstring
    import_code = """
import sys
import os
sys.path.append(os.path.dirname(__file__) + '/utils')

# Import YOUR actual momentum tracker
from actual_momentum_tracker import calculate_momentum_indicator as calc_momentum_full, backtest_baseline

"""
    
    # Find docstring end
    docstring_end = content.find('"""', 10) + 3
    if docstring_end > 3:
        content = content[:docstring_end] + import_code + content[docstring_end:]
    
    # Add note to docstring
    content = content.replace(
        'Expected:',
        '✅ NOW USING YOUR ACTUAL MOMENTUM TRACKER\n\nExpected:'
    )
    
    return content


def replace_momentum_function(content):
    """Replace simplified momentum with actual"""
    # Replace the entire function
    pattern = r'def calculate_momentum_indicator\(df\):.*?return (?:np\.array\(momentum_values\)|momentum_values)'
    
    replacement = '''def calculate_momentum_indicator(df):
    """Calculate momentum using YOUR exact algorithm"""
    result = calc_momentum_full(df, length=7, threshold=2.0)
    return result['momentum']'''
    
    content = re.sub(pattern, replacement, content, flags=re.DOTALL)
    return content


def replace_baseline_backtest(content):
    """Replace baseline backtest"""
    # Find and replace baseline function
    pattern = r'def backtest_baseline\(data.*?\n    return \{[^}]+\}'
    
    replacement = '''def backtest_baseline_test(data, initial_capital=10000, risk_pct=2.0):
    """Baseline backtest using YOUR actual momentum tracker"""
    result = backtest_baseline(data, initial_capital=initial_capital, 
                               risk_pct=risk_pct, trailing_stop_pct=3.0, long_only=True)
    return result'''
    
    content = re.sub(pattern, replacement, content, flags=re.DOTALL)
    
    # Update function calls
    content = content.replace("backtest_baseline(", "backtest_baseline_test(")
    
    return content


def fix_trade_counting(content):
    """Fix trade counting issues"""
    # Fix EXIT type checking
    content = re.sub(
        r"len\(\[t for t in (\w+)\['trades'\] if t\['type'\] == 'EXIT'\]\)",
        r"len(\1.get('trades', []))",
        content
    )
    
    return content


def process_file(filepath):
    """Process a single file"""
    print(f"\nProcessing: {filepath}")
    
    with open(filepath, 'r') as f:
        content = f.read()
    
    # Check if already updated
    if 'from actual_momentum_tracker import' in content:
        print(f"  ✓ Already updated - skipping")
        return
    
    # Apply fixes
    print(f"  → Adding imports...")
    content = update_file_header(content, filepath)
    
    print(f"  → Replacing momentum function...")
    content = replace_momentum_function(content)
    
    print(f"  → Replacing baseline backtest...")
    content = replace_baseline_backtest(content)
    
    print(f"  → Fixing trade counting...")
    content = fix_trade_counting(content)
    
    # Write back
    with open(filepath, 'w') as f:
        f.write(content)
    
    print(f"  ✓ Done!")


if __name__ == '__main__':
    # List of files to fix
    base_path = "/Users/aakarshraj/GG_ Script/tradingview-strategies/python_strategies"
    
    files_to_fix = [
        'test_multi_scale_attention.py',
        'test_walk_forward_bootstrap.py',
        'test_statistical_arbitrage_llm.py',
        'test_meta_rl_firm_momentum.py'
    ]
    
    print("="*80)
    print("  FIXING ALL TEST FILES TO USE ACTUAL MOMENTUM TRACKER")
    print("="*80)
    
    for filename in files_to_fix:
        filepath = os.path.join(base_path, filename)
        if os.path.exists(filepath):
            try:
                process_file(filepath)
            except Exception as e:
                print(f"  ✗ Error: {e}")
        else:
            print(f"\n✗ File not found: {filepath}")
    
    print("\n" + "="*80)
    print("  COMPLETE!")
    print("="*80)
    print("\nAll files updated to use YOUR actual momentum tracker.")
    print("Next step: Run comprehensive test suite")
