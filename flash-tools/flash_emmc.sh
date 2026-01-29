#!/bin/bash
# Flash RZ/V2N SolidRun SoM via eMMC
# Usage: ./runme_emmc.sh

echo "=== RZ/V2N eMMC Flash Programming ==="

# Step 1: Download Flash Writer
echo "Downloading Flash Writer..."
./flash_writer_tool.sh config_v2n_emmc.ini fw

# Step 2: Write BL2 bootloader
echo "Writing BL2 bootloader..."
./flash_writer_tool.sh config_v2n_emmc.ini bl2

# Step 3: Write FIP image
echo "Writing FIP image..."
./flash_writer_tool.sh config_v2n_emmc.ini fip

# Step 4: Configure eMMC
echo "Configuring eMMC..."
./flash_writer_tool.sh config_v2n_emmc.ini emmc_config

echo "=== eMMC Flash Programming Complete ==="