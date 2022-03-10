/*
 * Copyright (c) 2015-2022, Renesas Electronics Corporation. All rights reserved.
 *
 * SPDX-License-Identifier: BSD-3-Clause
 */

#include "common.h"
#include "scifdrv.h"
#include "bit.h"
#include "rzfive_def.h"
#include "rzfive_cpg_regs.h"
#include "scif_regs.h"
#include "devdrv.h"

/************************************************************************/
/*									*/
/*	Debug Seirial(SCIF ch0)						*/
/*									*/
/************************************************************************/
int32_t PutCharSCIF0(char outChar)
{
	while(!(0x60U & *((volatile uint16_t*)SCIF0_FSR)));
	*((volatile unsigned char*)SCIF0_FTDR) = outChar;
	*((volatile uint16_t*)SCIF0_FSR) &= ~0x60U;	/* TEND,TDFE clear */
	return(0);
}

int32_t GetCharSCIF0(char *inChar)
{
	do
	{
		if (0x91U & *((volatile uint16_t *)SCIF0_FSR))
		{
			*((volatile uint16_t *)SCIF0_FSR) &= ~0x91U;
		}
		if (0x01U & *((volatile uint16_t *)SCIF0_LSR))
		{
			PutStr("ORER", 1);
			*((volatile uint16_t *)SCIF0_LSR) &= ~0x01U;
		}
	} while (!(0x02U & *((volatile uint16_t *)SCIF0_FSR)));

	*inChar = *((volatile unsigned char*)SCIF0_FRDR);
	*((volatile uint16_t*)SCIF0_FSR) &= ~0x02U;
	return(0);
}

void PowerOnScif0(void)
{
	volatile uint32_t dataL;

	dataL = *((volatile uint32_t*)CPG_CLKMON_SCIF);
	if ((dataL & BIT0) == 0U)
	{
		/* case SCIF ch0 Standby */
		*((volatile uint32_t*)CPG_CLKON_SCIF) = (BIT0 | BIT16);
		do
		{
			dataL = *((volatile uint32_t*)CPG_CLKMON_SCIF);
		} while ((dataL & BIT0) == 0U);	/* wait until bit0=1 */
	}
	dataL = *((volatile uint32_t*)CPG_RST_SCIF);
	dataL |= 0x00010001U;
	*((volatile uint32_t*)CPG_RST_SCIF) = dataL;
	do
	{
		dataL = *((volatile uint32_t*)CPG_RSTMON_SCIF);
	} while ((dataL & BIT0) == 1U);	/* wait until bit0=1 */
}

void WaitPutScif0SendEnd(void)
{
	volatile uint16_t dataW;

	while(1)
	{
		dataW = *((volatile uint16_t*)SCIF0_FSR);
		if (dataW & BIT6)
		{
			break;
		}
	}
}

void InitScif0_SCIFCLK(uint32_t baudrate)
{
	volatile uint16_t dataW;
	uint32_t prr;

	dataW = *((volatile uint16_t*)SCIF0_LSR);	/* dummy read     		*/
	*((volatile uint16_t*)SCIF0_LSR) = 0x0000U;	/* clear ORER bit 		*/
	*((volatile uint16_t*)SCIF0_FSR) = 0x0000U;	/* clear all error bit	*/

	*((volatile uint16_t*)SCIF0_SCR) = 0x0000U;	/* clear SCR.TE & SCR.RE*/
	*((volatile uint16_t*)SCIF0_FCR) = 0x0006U;	/* reset tx-fifo, reset rx-fifo. */
	*((volatile uint16_t*)SCIF0_FSR) = 0x0000U;	/* clear ER, TEND, TDFE, BRK, RDF, DR */

	*((volatile uint16_t*)SCIF0_SCR) = 0x0000U;	/* internal clock P1/1 */
	*((volatile uint16_t*)SCIF0_SMR) = 0x0000U;	/* 8bit data, no-parity, 1 stop, Po/1 */
	*((volatile uint8_t*)SCIF0_SEMR) = 0x00U;
	SoftDelay(100);

	if (baudrate == 115200)
	{
		*((volatile uint8_t*)SCIF0_BRR)  = 0x1AU;	/* 115200bps */
	}
	else
	{
		*((volatile uint8_t*)SCIF0_BRR)  = 0x01U;	/* 921600bps */
	}
	*((volatile uint8_t*)SCIF0_SEMR) = 0x30U;
	if (baudrate == 115200)
	{
		*((volatile uint8_t*)SCIF0_MDDR) = 0xFFU;	/* 115200bps */
	}
	else
	{
		*((volatile uint8_t*)SCIF0_MDDR) = 0x97U;	/* 921600bps */
	}

	SoftDelay(100);
	*((volatile uint16_t*)SCIF0_FCR) = 0x0000U;	/* reset-off tx-fifo, rx-fifo. */
	*((volatile uint16_t*)SCIF0_SCR) = 0x0030U;	/* enable TE, RE  */

	SoftDelay(100);
}

uint32_t SCIF_TerminalInputCheck(char* str)
{
	char result = 0;

	if (0x91U & *((volatile uint16_t *)SCIF0_FSR))
	{
		*((volatile uint16_t *)SCIF0_FSR) &= ~0x91U;
	}
	if (0x01U & *((volatile uint16_t *)SCIF0_LSR))
	{
		PutStr("ORER",1);
		*((volatile uint16_t *)SCIF0_LSR) &= ~0x01U;
	}
	if (0x02U & *((volatile uint16_t *)SCIF0_FSR))
	{
		*str = *((volatile unsigned char*)SCIF0_FRDR);
		*((volatile uint16_t*)SCIF0_FSR) &= ~0x02U;
		result = 1;
	}
	return result;
}
