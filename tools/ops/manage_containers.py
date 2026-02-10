#!/usr/bin/env python3
import sys
import argparse
import subprocess
import time
from pathlib import Path

# Add project root to sys.path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(project_root))

from config.language_manager import LanguageManager

import os

# --- Configuration ---
HEAP_SIZE = os.environ.get("WIKIGRAPH_HEAP", "4G")
PAGECACHE_SIZE = os.environ.get("WIKIGRAPH_PAGECACHE", "4G")

def get_ports(lang):
    """
    Determine HTTP and Bolt ports for a language.
    1. Check for explicit ports in config/languages/{lang}.yaml
    2. Fallback to dynamic allocation based on language code hash.
    """
    # 1. Try Config
    try:
        infra = LanguageManager.get_infrastructure_config(lang)
        ports = infra.get('ports', {})
        if 'http' in ports and 'bolt' in ports:
            return (ports['http'], ports['bolt'])
    except Exception:
        pass

    # 2. Stable Hash Fallback
    # We use a simple hash of the language code to pick a port in a safe range.
    # Range: 7500 - 7599 (100 slots)
    import hashlib
    hash_val = int(hashlib.md5(lang.encode()).hexdigest(), 16)
    offset = hash_val % 100
    
    http_port = 7500 + offset
    bolt_port = 7713 + offset # Consistent 213 offset
    
    return (http_port, bolt_port)

def start_container(lang):
    http_port, bolt_port = get_ports(lang)
    container_name = f"wikigraph-neo4j-{lang}"
    
    paths = LanguageManager.get_paths(lang)
    neo4j_data_dir = paths['neo4j_bulk_dir'].parent / lang # Use standard data/neo4j_data/{lang} pattern?
    # Actually, dev.sh used "$PROJECT_ROOT/data/neo4j_data/$lang"
    # LanguageManager returns 'neo4j_bulk_dir' as data/neo4j_bulk/{lang}
    # Let's stick to the dev.sh convention for the volume mount source:
    data_mount_source = project_root / "data" / "neo4j_data" / lang
    
    print(f"🚀 Starting Neo4j ({lang})...")
    print(f"   Ports: HTTP={http_port}, Bolt={bolt_port}")
    
    # Check if running
    res = subprocess.run(["docker", "ps", "--format", "{{.Names}}"], capture_output=True, text=True)
    if container_name in res.stdout.split():
        print(f"✅ {container_name} is already running.")
        return

    # Check if exists (stopped)
    res_all = subprocess.run(["docker", "ps", "-a", "--format", "{{.Names}}"], capture_output=True, text=True)
    if container_name in res_all.stdout.split():
        print(f"📦 Starting existing container...")
        subprocess.run(["docker", "start", container_name], check=True)
        return

    print(f"📦 Provisioning new container...")
    
    # Ensure directories exist
    (data_mount_source / "data").mkdir(parents=True, exist_ok=True)
    (data_mount_source / "plugins").mkdir(parents=True, exist_ok=True)

    cmd = [
        "docker", "run", "-d",
        "--name", container_name,
        "--publish", f"{http_port}:7474",
        "--publish", f"{bolt_port}:7687",
        "--volume", f"{data_mount_source}/data:/data",
        "--volume", f"{data_mount_source}/plugins:/plugins",
        "--env", "NEO4J_AUTH=neo4j/wikigraph",
        "--env", "NEO4J_PLUGINS=[\"apoc\", \"graph-data-science\"]",
        "--env", "NEO4J_dbms_security_procedures_unrestricted=gds.*,apoc.*",
        "--env", "NEO4J_server_memory_heap_initial__size=2G",
        "--env", f"NEO4J_server_memory_heap_max__size={HEAP_SIZE}",
        "--env", f"NEO4J_server_memory_pagecache_size={PAGECACHE_SIZE}",
        "neo4j:5-community"
    ]
    
    subprocess.run(cmd, check=True)

def stop_container(lang):
    container_name = f"wikigraph-neo4j-{lang}"
    print(f"🛑 Stopping {container_name}...")
    subprocess.run(["docker", "stop", container_name], check=False)

def wait_for_ready(lang):
    container_name = f"wikigraph-neo4j-{lang}"
    print(f"⏳ Waiting for {container_name} to be ready...", end="", flush=True)
    
    for _ in range(30):
        res = subprocess.run(
            ["docker", "exec", container_name, "cypher-shell", "-u", "neo4j", "-p", "wikigraph", "RETURN 1"],
            capture_output=True
        )
        if res.returncode == 0:
            print(" ✅ OK")
            return
        print(".", end="", flush=True)
        time.sleep(2)
    print(" ❌ TIMEOUT")

def main():
    parser = argparse.ArgumentParser(description="Manage WikiGraph Neo4j Containers")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Start
    start_parser = subparsers.add_parser("start")
    start_parser.add_argument("lang", help="Language code (or 'all')")

    # Stop
    stop_parser = subparsers.add_parser("stop")
    stop_parser.add_argument("lang", help="Language code (or 'all')")

    # Restart
    restart_parser = subparsers.add_parser("restart")
    restart_parser.add_argument("lang", help="Language code (or 'all')")
    
    # Status
    subparsers.add_parser("status")

    args = parser.parse_args()

    if args.command == "status":
        print("\n=== Active Containers ===")
        subprocess.run(["docker", "ps", "--format", "table {{.Names}}\t{{.Status}}\t{{.Ports}}", "--filter", "name=wikigraph-neo4j"])
        return

    available_langs = LanguageManager.list_available_languages()
    targets = available_langs if args.lang == 'all' else [args.lang]

    if args.command == "start":
        for lang in targets:
            start_container(lang)
            wait_for_ready(lang)

    elif args.command == "stop":
        for lang in targets:
            stop_container(lang)

    elif args.command == "restart":
        for lang in targets:
            stop_container(lang)
            time.sleep(2)
            start_container(lang)
            wait_for_ready(lang)

if __name__ == "__main__":
    main()
