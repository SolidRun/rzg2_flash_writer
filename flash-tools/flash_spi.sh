#!/bin/bash
# Flash RZ/V2N SolidRun SoM via SPI NOR flash
# Usage: ./runme_spi.sh

echo "=== RZ/V2N SPI Flash Programming ==="

# Step 1: Download Flash Writer
echo "Downloading Flash Writer..."
./flash_writer_tool.sh config_v2n_spi.ini fw

# Step 2: Write BL2 bootloader
echo "Writing BL2 bootloader..."
./flash_writer_tool.sh config_v2n_spi.ini bl2

# Step 3: Write FIP image
echo "Writing FIP image..."
./flash_writer_tool.sh config_v2n_spi.ini fip

echo "=== SPI Flash Programming Complete ==="