/*
 * Copyright (c) 2023, Renesas Electronics Corporation. All rights reserved.
 *
 * SPDX-License-Identifier: BSD-3-Clause
 */

#ifndef DEBUG_H
#define DEBUG_H

#define	INFO(...)
#define	ERROR(...)
#define	VERBOSE(...)
#define ARRAY_SIZE(X) (sizeof(X)/(sizeof(X[0])))

#define	panic(...)	while(1)
#define	dsb(...)

#endif /* DEBUG_H */

