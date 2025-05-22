import os
import subprocess

# Ask for target domain
target_domain = input("Enter the target domain: ").strip()
if not target_domain:
    print("Error: Target domain cannot be empty.")
    exit(1)

# Create results directory
results_dir = f"results/{target_domain}"
os.makedirs(results_dir, exist_ok=True)

# Output files
subfinder_output = os.path.join(results_dir, "subfinder_output.txt")
assetfinder_output = os.path.join(results_dir, "assetfinder_output.txt")
github_subdomain_output = os.path.join(results_dir, "github_subdomain_output.txt")
domains_file = os.path.join(results_dir, "domains.txt")
httpx_output = os.path.join(results_dir, "httpx_output.txt")
wayback_output = os.path.join(results_dir, "waybackurls_output.txt")

# Function to prompt for file path
def prompt_for_file(tool, path, max_attempts=2):
    if os.path.exists(path):
        return path
    for attempt in range(1, max_attempts + 1):
        print(f"File {path} for {tool} not found. Enter new path (attempt {attempt}/{max_attempts}):")
        new_path = input().strip()
        if os.path.exists(new_path):
            return new_path
        print(f"Invalid path: {new_path}")
    print(f"Failed to find valid file for {tool} after {max_attempts} attempts. Exiting.")
    exit(1)

# Check and prompt for config/token files
subfinder_config = prompt_for_file("subfinder", "/root/.config/subfinder/provider-config.yaml")
github_tokens = prompt_for_file("github-subdomains", "/home/vansh/tools/github-tokens.txt")

# Run subdomain tools
tools = [
    ("subfinder", f"subfinder -d {target_domain} -all -r -config {subfinder_config} > {subfinder_output}"),
    ("assetfinder", f"assetfinder --subs-only {target_domain} > {assetfinder_output}"),
    ("github-subdomains", f"github-subdomains -t {github_tokens} -d {target_domain} -o {github_subdomain_output}")
]

for tool, command in tools:
    print(f"\nRunning {tool}...")
    try:
        subprocess.run(command, shell=True, check=True)
        print(f"{tool} completed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"{tool} failed with error: {e}")

# Combine subdomains into domains.txt
subdomains = set()
for output in [subfinder_output, assetfinder_output, github_subdomain_output]:
    if os.path.exists(output):
        with open(output, "r") as f:
            subdomains.update(line.strip() for line in f if line.strip())

if subdomains:
    with open(domains_file, "w") as f:
        f.write("\n".join(sorted(subdomains)))
    print(f"Combined subdomains saved to {domains_file}.")
else:
    print("No subdomains found to save to domains.txt.")

# Run httpx
if os.path.exists(domains_file) and os.path.getsize(domains_file) > 0:
    print("\nRunning httpx...")
    try:
        subprocess.run(f"cat {domains_file} | httpx -silent -timeout 10 -o {httpx_output}", shell=True, check=True)
        print(f"httpx completed successfully. Live domains saved to {httpx_output}.")
    except subprocess.CalledProcessError as e:
        print(f"httpx failed with error: {e}")
else:
    print("No domains to process with httpx. Skipping.")

# Process live domains with waybackurls
if os.path.exists(httpx_output) and os.path.getsize(httpx_output) > 0:
    with open(httpx_output, "r") as f:
        live_domains = [line.strip() for line in f if line.strip()]
    total_domains = len(live_domains)
    for i, domain in enumerate(live_domains, 1):
        print(f"Processing {i}/{total_domains}", end="\r")
        try:
            subprocess.run(f"echo {domain} | waybackurls >> {wayback_output}", shell=True, check=True)
        except subprocess.CalledProcessError:
            pass  # Silently skip failed domains
    print(f"Processing {total_domains}/{total_domains} completed.")
else:
    print("No live domains found to process with waybackurls.")
