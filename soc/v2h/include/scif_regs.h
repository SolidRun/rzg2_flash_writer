/*
 * Copyright (c) 2023, Renesas Electronics Corporation. All rights reserved.
 *
 * SPDX-License-Identifier: BSD-3-Clause
 */

#ifndef __SCIF_REGS_H__
#define __SCIF_REGS_H__

#include <rz_soc_def.h>		/* Get the SCIF0 base address */

/* SCIF ch0 */
#define SCIF0_SMR		(RZV2H_SCIF_BASE + 0x0000U)
#define SCIF0_BRR		(RZV2H_SCIF_BASE + 0x0002U)
#define SCIF0_MDDR		(RZV2H_SCIF_BASE + 0x0002U)
#define SCIF0_SCR		(RZV2H_SCIF_BASE + 0x0004U)
#define SCIF0_FTDR		(RZV2H_SCIF_BASE + 0x0006U)
#define SCIF0_FSR		(RZV2H_SCIF_BASE + 0x0008U)
#define SCIF0_FRDR		(RZV2H_SCIF_BASE + 0x000AU)
#define SCIF0_FCR		(RZV2H_SCIF_BASE + 0x000CU)
#define SCIF0_FDR		(RZV2H_SCIF_BASE + 0x000EU)
#define SCIF0_SPTR		(RZV2H_SCIF_BASE + 0x0010U)
#define SCIF0_LSR		(RZV2H_SCIF_BASE + 0x0012U)
#define SCIF0_SEMR		(RZV2H_SCIF_BASE + 0x0014U)

#endif	/* __SCIF_REGS_H__ */
