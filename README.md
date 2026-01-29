# RZ/V2N Flash Writer

Flash Writer is a firmware programming utility for the Renesas RZ/V2N SoC. It provides an interactive command-line interface over SCIF (serial) for writing to eMMC and SPI NOR flash memory.

## Supported Boards

| BOARD | DDR | Output |
|-------|-----|--------|
| `RZV2N_EVK` | LPDDR4X | `Flash_Writer_SCIF_RZV2N_EVK_LPDDR4X.mot` |
| `RZV2N_DEV` | LPDDR4X | `Flash_Writer_SCIF_RZV2N_DEV_LPDDR4X.mot` |
| `RZV2N_UNIVERSAL` | Internal memory only | `Flash_Writer_SCIF_RZV2N_COMMON_INTERNAL_MEMORY.mot` |

## Prerequisites

Download and extract the ARM GCC cross-compiler (aarch64-none-elf):

```bash
cd ~
wget https://developer.arm.com/-/media/Files/downloads/gnu-a/10.3-2021.07/binrel/gcc-arm-10.3-2021.07-x86_64-aarch64-none-elf.tar.xz
tar xvf gcc-arm-10.3-2021.07-x86_64-aarch64-none-elf.tar.xz
```

## Building

```bash
CROSS_COMPILE=/home/root/gcc/gcc-arm-10.3-2021.07-x86_64-aarch64-none-elf/bin/aarch64-none-elf- \
    make -f makefile-v2n.gcc-arm BOARD=RZV2N_EVK
```

Replace `BOARD=RZV2N_EVK` with the target board from the table above.

### Build Options

| Option | Values | Default | Description |
|--------|--------|---------|-------------|
| `SERIAL_FLASH` | `ENABLE`, `DISABLE` | `ENABLE` | Include SPI NOR flash support |
| `EMMC` | `ENABLE`, `DISABLE` | `ENABLE` | Include eMMC support |
| `QSPI_IOV` | `1_8V`, `3_3V` | `1_8V` | QSPI I/O voltage |
| `EMMC_IOV` | `1_8V`, `3_3V` | `1_8V` | eMMC I/O voltage |

Example with options:

```bash
CROSS_COMPILE=/home/root/gcc/gcc-arm-10.3-2021.07-x86_64-aarch64-none-elf/bin/aarch64-none-elf- \
    make -f makefile-v2n.gcc-arm BOARD=RZV2N_EVK SERIAL_FLASH=ENABLE EMMC=DISABLE
```

### Clean

```bash
make -f makefile-v2n.gcc-arm clean
```

## Output

Build artifacts are placed in `AArch64_output/`:

- `.mot` — Motorola S-record (used for flashing)
- `.bin` — Raw binary
- `.axf` — ARM executable

## License

BSD 3-Clause — see [LICENSE.md](LICENSE.md) for details.
