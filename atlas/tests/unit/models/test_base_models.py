"""
Unit tests for the base model classes.

This module tests the core model classes like TokenUsage and CostEstimate,
which are used across different provider implementations.
"""

import unittest
from unittest import mock
from typing import Dict, Any, List, Optional

from atlas.tests.helpers.decorators import unit_test

from atlas.models import (
    TokenUsage,
    CostEstimate,
)


class TestTokenUsageBase(unittest.TestCase):
    """Test the TokenUsage base class functionality."""

    @unit_test
    def test_token_usage_creation(self):
        """Test creating TokenUsage instances."""
        # Create with explicit values
        usage = TokenUsage(input_tokens=10, output_tokens=20, total_tokens=30)
        self.assertEqual(usage.input_tokens, 10)
        self.assertEqual(usage.output_tokens, 20)
        self.assertEqual(usage.total_tokens, 30)

        # Create with automatic total calculation
        usage = TokenUsage(input_tokens=15, output_tokens=25)
        self.assertEqual(usage.input_tokens, 15)
        self.assertEqual(usage.output_tokens, 25)
        self.assertEqual(usage.total_tokens, 40)  # Should be sum of input + output

        # Create with defaults
        usage = TokenUsage()
        self.assertEqual(usage.input_tokens, 0)
        self.assertEqual(usage.output_tokens, 0)
        self.assertEqual(usage.total_tokens, 0)

    @unit_test
    def test_token_usage_string_representation(self):
        """Test the string representation of TokenUsage."""
        usage = TokenUsage(input_tokens=100, output_tokens=200)
        
        # Check that the string representation contains the token counts
        string_repr = str(usage)
        self.assertIn("100", string_repr)
        self.assertIn("200", string_repr)
        self.assertIn("300", string_repr)  # Total
        
    @unit_test
    def test_token_usage_dictionary_conversion(self):
        """Test converting TokenUsage to a dictionary."""
        usage = TokenUsage(input_tokens=50, output_tokens=75)
        
        # Convert to dictionary
        usage_dict = usage.to_dict()
        
        # Check dictionary contents
        self.assertEqual(usage_dict["input_tokens"], 50)
        self.assertEqual(usage_dict["output_tokens"], 75)
        self.assertEqual(usage_dict["total_tokens"], 125)


class TestCostEstimateBase(unittest.TestCase):
    """Test the CostEstimate base class functionality."""

    @unit_test
    def test_cost_estimate_creation(self):
        """Test creating CostEstimate instances."""
        # Create with explicit values
        cost = CostEstimate(input_cost=0.01, output_cost=0.02, total_cost=0.03)
        self.assertEqual(cost.input_cost, 0.01)
        self.assertEqual(cost.output_cost, 0.02)
        self.assertEqual(cost.total_cost, 0.03)

        # Create with automatic total calculation
        cost = CostEstimate(input_cost=0.015, output_cost=0.025)
        self.assertEqual(cost.input_cost, 0.015)
        self.assertEqual(cost.output_cost, 0.025)
        self.assertEqual(cost.total_cost, 0.04)  # Should be sum of input + output

        # Create with defaults
        cost = CostEstimate()
        self.assertEqual(cost.input_cost, 0.0)
        self.assertEqual(cost.output_cost, 0.0)
        self.assertEqual(cost.total_cost, 0.0)

    @unit_test
    def test_cost_estimate_string_representation(self):
        """Test the string representation of CostEstimate."""
        cost = CostEstimate(input_cost=0.01, output_cost=0.02)
        
        # Check that the string representation contains the costs
        string_repr = str(cost)
        self.assertIn("$0.01", string_repr)
        self.assertIn("$0.02", string_repr)
        self.assertIn("$0.03", string_repr)  # Total
        
    @unit_test
    def test_cost_estimate_dictionary_conversion(self):
        """Test converting CostEstimate to a dictionary."""
        cost = CostEstimate(input_cost=0.05, output_cost=0.075)
        
        # Convert to dictionary
        cost_dict = cost.to_dict()
        
        # Check dictionary contents
        self.assertEqual(cost_dict["input_cost"], 0.05)
        self.assertEqual(cost_dict["output_cost"], 0.075)
        self.assertEqual(cost_dict["total_cost"], 0.125)
        
    @unit_test
    def test_cost_estimate_formatting(self):
        """Test cost formatting in different scenarios."""
        # Test very small cost
        tiny_cost = CostEstimate(input_cost=0.0000001, output_cost=0.0000002)
        tiny_str = str(tiny_cost)
        # Should use at least 7 decimal places or scientific notation for tiny costs
        self.assertTrue(
            "$0.0000003" in tiny_str or 
            "3.0e-07" in tiny_str or 
            "3e-07" in tiny_str, 
            f"Expected tiny cost format not found in {tiny_str}"
        )
        
        # Test larger cost
        large_cost = CostEstimate(input_cost=1.5, output_cost=2.5)
        large_str = str(large_cost)
        # Should show rounded to 2 decimal places for larger costs
        self.assertTrue(
            "$4.00" in large_str or 
            "$4.0" in large_str, 
            f"Expected large cost format not found in {large_str}"
        )


if __name__ == "__main__":
    unittest.main()