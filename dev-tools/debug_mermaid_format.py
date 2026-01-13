import os

def print_hex_dump(data, length=128):
    """Print readable hex dump with offsets."""
    for i in range(0, min(len(data), length), 16):
        chunk = data[i:i+16]
        hex_str = chunk.hex(' ')
        text_str = "".join(chr(b) if 32 <= b <= 126 else "." for b in chunk)
        print(f"{i:04x}: {hex_str:<47}  {text_str}")

def debug_report(report_path):
    if not os.path.exists(report_path):
        print(f"File not found: {report_path}")
        return

    print(f"\n" + "="*80)
    print(f"REPORT: {report_path}")
    print("="*80)
    
    try:
        with open(report_path, 'rb') as f:
            content = f.read()
        
        # Check overall line endings
        has_cr = b'\r' in content
        has_lf = b'\n' in content
        print(f"GLOBAL LINE ENDINGS: CR(\\r): {has_cr}, LF(\\n): {has_lf}")
        
        # Find ALL mermaid blocks
        pos = 0
        block_count = 0
        while True:
            try:
                start = content.index(b"```mermaid", pos)
                end = content.index(b"```", start + 10)
                block = content[start:end+3]
                header = content[start:start+100].split(b'\n')[0]
                
                block_count += 1
                print(f"\n[Mermaid Block #{block_count}] ({len(block)} bytes)")
                print(f"Header: {header.decode('utf-8', errors='replace')}")
                print("-" * 40)
                
                # Check block-specific line endings
                b_cr = b'\r' in block
                b_lf = b'\n' in block
                print(f"Block Line Endings: CR(\\r): {b_cr}, LF(\\n): {b_lf}")
                
                print("\n--- HEX DUMP (Start of Block) ---")
                print_hex_dump(block, 128)
                
                print("\n--- TEXT PREVIEW (Start of Block) ---")
                print(block[:300].decode('utf-8', errors='replace'))
                
                pos = end + 3
            except ValueError:
                if block_count == 0:
                    print("\nNo Mermaid blocks found.")
                break
    except Exception as e:
        print(f"Error processing {report_path}: {e}")

if __name__ == "__main__":
    debug_report("auditing/reports/prompt_distribution_flow.md")
    debug_report("auditing/reports/comprehensive_audit.md")
