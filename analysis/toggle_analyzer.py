import sys, os, re
import matplotlib.pyplot as plt
from collections import defaultdict

def parse_vcd_for_toggles(vcd_path):
    if not os.path.exists(vcd_path):
        raise FileNotFoundError(f"VCD file not found: {vcd_path}")

    print(f"Parsing {vcd_path} for all signal toggles...")

    id_to_signal = {}
    signal_last_val = {}
    clean_toggles = defaultdict(int)
    trojan_toggles = defaultdict(int)
    current_scope = ""

    val_regex = re.compile(r"b([01xz]+)\s+(\S+)")

    with open(vcd_path, 'r', errors='ignore') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue

            # Track scope
            if line.startswith("$scope"):
                scope_name = line.split()[2]
                current_scope = f"{current_scope}.{scope_name}" if current_scope else scope_name
                continue
            if line.startswith("$upscope"):
                current_scope = ".".join(current_scope.split('.')[:-1])
                continue

            # Variable definition
            if line.startswith("$var"):
                parts = line.split()
                try:
                    sig_type, sig_width, sig_id, sig_name = parts[1:5]
                    full_sig_name = f"{current_scope}.{sig_name}"
                    id_to_signal[sig_id] = full_sig_name
                    signal_last_val[full_sig_name] = None
                except ValueError:
                    continue
            if line.startswith("$enddefinitions"):
                print("VCD definitions parsed. Starting toggle counting...")
                continue

            # Value change
            if line.startswith('b'):
                match = val_regex.match(line)
                if not match:
                    continue
                new_val_str, sig_id = match.groups()
            elif line[0] in '01xz':
                new_val_str = line[0]
                sig_id = line[1:].strip()
            else:
                continue

            full_sig_name = id_to_signal.get(sig_id)
            if not full_sig_name:
                continue

            last_val_str = signal_last_val.get(full_sig_name)

            if last_val_str is not None and 'x' not in new_val_str and 'z' not in last_val_str:
                toggles = 0
                if len(new_val_str) == 1:
                    if new_val_str != last_val_str:
                        toggles = 1
                else:
                    try:
                        new_val_int = int(new_val_str, 2)
                        last_val_int = int(last_val_str, 2)
                        toggles = bin(new_val_int ^ last_val_int).count('1')
                    except (ValueError, TypeError):
                        toggles = 0

                if toggles > 0:
                    if ".u_clean." in full_sig_name:
                        local_sig_name = full_sig_name.split('.u_clean.')[1]
                        clean_toggles[local_sig_name] += toggles
                    elif ".u_trojan." in full_sig_name:
                        local_sig_name = full_sig_name.split('.u_trojan.')[1]
                        trojan_toggles[local_sig_name] += toggles

            signal_last_val[full_sig_name] = new_val_str

    print("Toggle counting complete.")
    return clean_toggles, trojan_toggles


def analyze_and_plot(clean_data, trojan_data, plot_png="toggle_analysis.png"):
    total_clean_toggles = sum(clean_data.values())
    total_trojan_toggles = sum(trojan_data.values())

    print("\n--- Side-Channel Analysis Report ---")
    print(f"Total Toggles (Clean ALU):   {total_clean_toggles}")
    print(f"Total Toggles (Trojan ALU):  {total_trojan_toggles}")

    deviation = total_trojan_toggles - total_clean_toggles
    deviation_pct = (deviation / total_clean_toggles) * 100 if total_clean_toggles else 0
    print(f"Switching Activity Deviation: {deviation:+d} toggles ({deviation_pct:+.2f}%)")

    if abs(deviation_pct) > 0.1:
        print("DETECTION: Trojan-infected design shows subtle but measurable switching deviation.")
    else:
        print("NO DETECTION: Trojan stealth maintained globally.")

    # Compute per-signal deviations
    all_signals = sorted(list(set(clean_data.keys()) | set(trojan_data.keys())))
    deviations = {sig: trojan_data.get(sig,0) - clean_data.get(sig,0) for sig in all_signals}
    abs_devs = {sig: abs(diff) for sig, diff in deviations.items()}

    # Identify Top 10 stealth differences
    print("\nTop 10 signals with highest toggle deviation:")
    for sig in sorted(abs_devs, key=abs_devs.get, reverse=True)[:10]:
        print(f"{sig:35s}  Clean={clean_data.get(sig,0):5d}  Trojan={trojan_data.get(sig,0):5d}  Δ={deviations[sig]:+4d}")

    # Plot results
    top_n = 30
    plot_data = sorted(all_signals, key=lambda s: abs(deviations[s]), reverse=True)[:top_n]

    clean_vals = [clean_data.get(s, 0) for s in plot_data]
    trojan_vals = [trojan_data.get(s, 0) for s in plot_data]
    dev_labels = [deviations[s] for s in plot_data]

    plt.figure(figsize=(18, 7))
    x = range(len(plot_data))
    width = 0.4
    plt.bar([i - width/2 for i in x], clean_vals, width=width, label='Clean')
    plt.bar([i + width/2 for i in x], trojan_vals, width=width, label='Trojan')

    plt.ylabel('Toggle Count')
    plt.title(f'Top {top_n} Signals Showing Stealthy Deviations')
    plt.xticks(x, plot_data, rotation=90)
    plt.legend()
    plt.grid(axis='y', linestyle='--', alpha=0.6)

    # Highlight signals with subtle deviation
    for i, dev in enumerate(dev_labels):
        if dev != 0:
            plt.text(i, max(clean_vals[i], trojan_vals[i]) + 0.5, f"{dev:+d}", ha='center', fontsize=8, rotation=90)

    plt.tight_layout()
    plt.savefig(plot_png, dpi=150)
    print(f"\n New toggle deviation plot saved to: {plot_png}")


def main():
    vcd_path = "../simulation/alu_both.vcd"
    if not os.path.exists(vcd_path):
        print(f"Error: VCD file not found at {vcd_path}")
        sys.exit(1)

    clean_toggles, trojan_toggles = parse_vcd_for_toggles(vcd_path)

    if not clean_toggles and not trojan_toggles:
        print("\n--- ERROR ---")
        print("Could not find any signals for 'u_clean' or 'u_trojan'.")
        print("Please verify instance names in tb_alu.v.")
        sys.exit(1)

    analyze_and_plot(clean_toggles, trojan_toggles)


if __name__ == "__main__":
    main()
