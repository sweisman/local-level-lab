/* SPDX-License-Identifier: AGPL-3.0-or-later */
#include "ilvis0_tangent.cpp"
#include <new>
#define SCALAR Dual
#define NUMBER(x) ((x).v)
#define SET_DERIVATIVE(x, i, value) ((x).d[i]=(value))
#define EXPORT extern "C"
#define IS_TANGENT 1
#define isfinite std::isfinite
#include "ilvis0_stream_body.h"
