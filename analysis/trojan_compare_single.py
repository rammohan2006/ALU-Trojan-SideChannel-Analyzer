import sys, os, re
from collections import defaultdict
import matplotlib.pyplot as plt

def parse_single_vcd(path):
    """Parse a VCD and return timestamped changes for Y_clean and Y_trojan"""
    if not os.path.exists(path):
        raise FileNotFoundError(f"VCD not found: {path}")
    
    id_to_signal = {}
    signal_values = {}
    timeline = []  # list of (time, Y_clean, Y_trojan)
    
    cur_time = 0
    y_clean_val = None
    y_trojan_val = None

    with open(path, 'r', errors='ignore') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue

            # Capture variable definitions
            if line.startswith("$var"):
                parts = line.split()
                if len(parts) >= 5:
                    sigid = parts[3]
                    signame = parts[4]
                    id_to_signal[sigid] = signame
                continue

            # Capture time steps
            if line.startswith("#"):
                cur_time = int(line[1:])
                # store the current state of both signals
                if y_clean_val is not None and y_trojan_val is not None:
                    timeline.append((cur_time, y_clean_val, y_trojan_val))
                continue

            # Capture signal value changes
            if line.startswith("b"):
                # Vector assignment: b<value> <id>
                val_part, sigid = line[1:].split()
                val = val_part.strip()
            elif line[0] in "01xz":
                val = line[0]
                sigid = line[1:]
            else:
                continue

            sig = id_to_signal.get(sigid)
            if sig == "Y_clean":
                y_clean_val = val
            elif sig == "Y_trojan":
                y_trojan_val = val

    return timeline

def analyze_differences(timeline, report_path="deviation_report_single.txt"):
    """Compare Y_clean and Y_trojan values over time"""
    mismatches = []
    for t, y1, y2 in timeline:
        if y1 != y2:
            mismatches.append((t, y1, y2))
    
    with open(report_path, "w") as f:
        f.write("=== Hardware Trojan Detection Report (Single VCD) ===\n\n")
        f.write(f"Total time points analyzed: {len(timeline)}\n")
        f.write(f"Mismatches detected: {len(mismatches)}\n\n")
        if mismatches:
            f.write(f"{'Time (ns)':>10s} {'Y_clean':>10s} {'Y_trojan':>10s}\n")
            f.write("-"*40 + "\n")
            for t, y1, y2 in mismatches:
                f.write(f"{t:10d} {y1:>10s} {y2:>10s}\n")
        else:
            f.write("No mismatches found. Trojan not triggered.\n")
    
    print(f"\nReport written to: {report_path}")
    if mismatches:
        print(f"{len(mismatches)} mismatches detected — Trojan likely triggered!")
        print(f"First mismatch: Time={mismatches[0][0]}  Clean={mismatches[0][1]}  Trojan={mismatches[0][2]}")
    else:
        print("No mismatches detected — both outputs identical.")
    
    return mismatches

def plot_waveforms(timeline, out_png="waveform_compare.png"):
    """Plot Y_clean vs Y_trojan for visual confirmation"""
    times = [t for t,_,_ in timeline]
    y_clean_vals = [int(v,2) if re.fullmatch(r"[01]+",v) else 0 for _,v,_ in timeline]
    y_trojan_vals = [int(v,2) if re.fullmatch(r"[01]+",v) else 0 for _,_,v in timeline]

    plt.figure(figsize=(10,4))
    plt.plot(times, y_clean_vals, label="Y_clean", drawstyle="steps-post")
    plt.plot(times, y_trojan_vals, label="Y_trojan", drawstyle="steps-post", linestyle="--")
    plt.xlabel("Time (ns)")
    plt.ylabel("Value (decimal)")
    plt.title("Clean vs Trojan Output Comparison")
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(out_png, dpi=200)
    plt.close()
    print(f"Waveform plot saved as: {out_png}")

def main():
    vcd_path = sys.argv[1] if len(sys.argv) > 1 else "../simulation/alu_both.vcd"
    print(f"Parsing VCD file: {vcd_path}")
    timeline = parse_single_vcd(vcd_path)
    print(f"Parsed {len(timeline)} timepoints.")
    mismatches = analyze_differences(timeline)
    plot_waveforms(timeline)

if __name__ == "__main__":
    main()