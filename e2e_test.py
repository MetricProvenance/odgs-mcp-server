import os
import json
import logging
from pprint import pprint

# Set up env for MCP Server configuration
os.environ["ODGS_API_KEY"] = "sk-test-enterprise-123"
os.environ["ODGS_REGISTRY_URL"] = "http://127.0.0.1:8080"
os.environ["ODGS_PROJECT_ROOT"] = "/Users/kartik/Code/open-data-governance-protocol/odgs-v5"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("e2e_test")

def main():
    logger.info("Starting S-Cert end-to-end flow test")
    
    # 1. Initialize AuthGate (which should validate with our mock registry)
    from odgs_mcp_server.auth import AuthGate
    from odgs_mcp_server.config import ServerConfig
    
    cfg = ServerConfig.from_env()
    auth = AuthGate(
        api_key=cfg.api_key,
        registry_url=cfg.registry_url,
        cache_dir=cfg.cache_dir
    )
    
    logger.info(f"API Key Tier resolved as: {auth.tier}")
    assert auth.tier == "enterprise", f"Expected enterprise tier, got {auth.tier}"
    
    # 2. Download a Pack
    from odgs_mcp_server.tools.packs import download_pack
    logger.info("Downloading sample-pack via MCP tool...")
    dl_result = download_pack(
        pack_id="sample-pack",
        registry_url=cfg.registry_url,
        cache_dir=cfg.cache_dir,
        api_key=auth.api_key
    )
    logger.info(f"Download Result: {json.dumps(dl_result, indent=2)}")
    assert dl_result.get("success"), "Pack download failed"
    
    # 3. List Packs (should show it installed)
    from odgs_mcp_server.tools.packs import list_packs
    logger.info("Listing packs to ensure sample-pack is installed...")
    packs_result = list_packs(project_root=cfg.project_root, cache_dir=cfg.cache_dir)
    sample_installed = any(p["id"] == "sample-pack" and p["installed"] for p in packs_result["packs"])
    logger.info(f"sample-pack installed: {sample_installed}")
    
    logger.info("E2E Test Completed Successfully!")

if __name__ == "__main__":
    main()
