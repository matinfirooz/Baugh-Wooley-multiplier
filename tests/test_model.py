"""Dependency-free functional tests, including exhaustive signed 8-bit coverage."""

import itertools
import unittest

from baugh_wooley import (
    baugh_wooley, from_bits, full_adder, half_adder, multiply_with_trace,
    to_bits, transformed_sum,
)


class CellTests(unittest.TestCase):
    def test_half_adder_truth_table(self):
        for a, b in itertools.product((0, 1), repeat=2):
            s, c = half_adder(a, b)
            self.assertEqual(s + (c << 1), a + b)

    def test_full_adder_truth_table(self):
        for a, b, cin in itertools.product((0, 1), repeat=3):
            s, c = full_adder(a, b, cin)
            self.assertEqual(s + (c << 1), a + b + cin)


class MultiplierTests(unittest.TestCase):
    def test_exhaustive_signed_eight_bit(self):
        for a in range(-128, 128):
            for b in range(-128, 128):
                actual = baugh_wooley(a, b)
                self.assertEqual(actual, a * b, (a, b))

    def test_exhaustive_small_widths_against_independent_models(self):
        for width in (2, 3, 4, 5):
            limit = 1 << (width - 1)
            for a in range(-limit, limit):
                for b in range(-limit, limit):
                    trace = multiply_with_trace(a, b, width)
                    self.assertEqual(trace.product, a * b, (width, a, b))
                    self.assertEqual(trace.output_bits, transformed_sum(a, b, width))

    def test_eight_bit_trace_and_weighted_row_invariants(self):
        trace = multiply_with_trace(-3, 5)
        self.assertEqual(trace.output_bits, 0xFFF1)
        self.assertEqual(trace.correction_positions, (8, 15))
        expected_s = (0x85, 0x42, 0x24, 0x16, 0x0F, 0x03, 0x01, 0xFF, 0xFF)
        expected_c = (0x80, 0x81, 0x81, 0x81, 0x85, 0x85, 0x00, 0x00)
        self.assertEqual(tuple(trace.sum_word(r) for r in range(9)), expected_s)
        self.assertEqual(tuple(trace.carry_word(r) for r in range(1, 9)), expected_c)
        # At row r, low r+1 bits have left the array; the remaining S/C
        # weighted rows conserve all processed partial products and bit 8.
        for row in range(1, 8):
            low = sum(trace.sums[r][0] << r for r in range(row + 1))
            live_s = sum(trace.sums[row][j] << (row + j) for j in range(1, 8))
            live_c = sum(trace.carries[row][j] << (row + j + 1) for j in range(8))
            processed_pp = sum(
                bit << (r + j)
                for r in range(row + 1)
                for j, bit in enumerate(trace.partial_products[r])
            )
            self.assertEqual(low + live_s + live_c, processed_pp + (1 << 8))

    def test_large_width_boundaries(self):
        for width in (6, 8, 12, 16):
            limit = 1 << (width - 1)
            for a, b in itertools.product((-limit, -1, 0, 1, limit - 1), repeat=2):
                self.assertEqual(baugh_wooley(a, b, width), a * b)

    def test_bit_pattern_helpers(self):
        self.assertEqual(to_bits(-3, 8), 253)
        self.assertEqual(from_bits(253, 8), -3)
        self.assertEqual(from_bits(0xFFF1, 16), -15)
        for value in range(-128, 128):
            self.assertEqual(from_bits(to_bits(value, 8), 8), value)

    def test_invalid_operands_and_widths(self):
        for value in (-129, 128):
            with self.assertRaises(ValueError):
                baugh_wooley(value, 1)
            with self.assertRaises(ValueError):
                baugh_wooley(1, value)
        for width in (0, 1, -1, 2.5, True):
            with self.assertRaises(ValueError):
                baugh_wooley(1, 1, width)
        for value in (1.5, "3", True):
            with self.assertRaises(TypeError):
                baugh_wooley(value, 1)
        for bits in (-1, 256):
            with self.assertRaises(ValueError):
                from_bits(bits, 8)


if __name__ == "__main__":
    unittest.main()
