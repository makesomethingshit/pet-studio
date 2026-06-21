"""Tests for model profile environment helpers."""

from __future__ import annotations

import unittest

from roost.model_profile import (
    build_model_profile_env,
    estimate_role_model_plan_savings,
    model_profile_cost_units,
    model_profile_env_clear,
    model_profile_env_overrides,
    model_profile_powershell_env_lines,
    model_profile_sort_key,
    model_profile_tier,
    role_model_env_clear,
    role_model_env_overrides,
    role_model_plan_powershell_env_lines,
)


class TestModelProfileEnv(unittest.TestCase):
    def test_openrouter_profile_sets_common_aliases(self):
        overrides = model_profile_env_overrides(
            {
                "id": "openrouter/sonnet",
                "provider": "openrouter",
                "model": "anthropic/claude-3.5-sonnet",
            }
        )

        self.assertEqual(overrides["PET_STUDIO_MODEL_PROFILE"], "openrouter/sonnet")
        self.assertEqual(overrides["PET_STUDIO_MODEL_PROVIDER"], "openrouter")
        self.assertEqual(overrides["PET_STUDIO_MODEL"], "anthropic/claude-3.5-sonnet")
        self.assertEqual(overrides["HERMES_MODEL"], "anthropic/claude-3.5-sonnet")
        self.assertEqual(overrides["OPENROUTER_MODEL"], "anthropic/claude-3.5-sonnet")

    def test_codex_profile_sets_codex_model_alias(self):
        overrides = model_profile_env_overrides(
            {
                "id": "codex/default",
                "provider": "codex",
                "model": "gpt-5-codex",
            }
        )

        self.assertEqual(overrides["CODEX_MODEL"], "gpt-5-codex")
        self.assertNotIn("OPENROUTER_MODEL", overrides)

    def test_build_env_preserves_existing_values(self):
        env = build_model_profile_env(
            {"id": "openrouter/cheap", "provider": "openrouter", "model": "cheap"},
            base_env={"OPENROUTER_API_KEY": "secret", "CODEX_MODEL": "stale"},
        )

        self.assertEqual(env["OPENROUTER_API_KEY"], "secret")
        self.assertEqual(env["OPENROUTER_MODEL"], "cheap")
        self.assertNotIn("CODEX_MODEL", env)

    def test_build_env_clears_stale_provider_model_values(self):
        env = build_model_profile_env(
            {"id": "local/default", "provider": "local", "model": "local"},
            base_env={"OPENROUTER_MODEL": "stale-openrouter", "CODEX_MODEL": "stale-codex"},
        )

        self.assertNotIn("OPENROUTER_MODEL", env)
        self.assertNotIn("CODEX_MODEL", env)
        self.assertEqual(env["PET_STUDIO_MODEL_PROFILE"], "local/default")

    def test_model_profile_env_clear_lists_stale_provider_model_values(self):
        self.assertEqual(
            model_profile_env_clear({"id": "codex/default", "provider": "codex", "model": "gpt-5-codex"}),
            ["OPENROUTER_MODEL"],
        )
        self.assertEqual(
            model_profile_env_clear({"id": "openrouter/fast", "provider": "openrouter", "model": "fast"}),
            ["CODEX_MODEL"],
        )
        self.assertEqual(
            model_profile_env_clear({"id": "local/default", "provider": "local"}),
            ["OPENROUTER_MODEL", "CODEX_MODEL"],
        )

    def test_powershell_env_lines_escape_quotes(self):
        lines = model_profile_powershell_env_lines(
            {
                "id": "openrouter/test",
                "provider": "openrouter",
                "model": "vendor/model's-fast",
            }
        )

        self.assertIn("$env:HERMES_MODEL = 'vendor/model''s-fast'", lines)
        self.assertIn("$env:OPENROUTER_MODEL = 'vendor/model''s-fast'", lines)
        self.assertIn("Remove-Item Env:CODEX_MODEL -ErrorAction SilentlyContinue", lines)

    def test_powershell_env_lines_clear_provider_specific_values(self):
        lines = model_profile_powershell_env_lines(
            {
                "id": "local/default",
                "provider": "local",
                "model": "local",
            }
        )

        self.assertIn("Remove-Item Env:OPENROUTER_MODEL -ErrorAction SilentlyContinue", lines)
        self.assertIn("Remove-Item Env:CODEX_MODEL -ErrorAction SilentlyContinue", lines)

    def test_model_profile_tier_matches_user_hierarchy(self):
        self.assertEqual(model_profile_tier({"id": "codex/default", "provider": "codex"}), "closed")
        self.assertEqual(model_profile_tier({"id": "openrouter/sota", "provider": "openrouter"}), "open-sota")
        self.assertEqual(model_profile_tier({"id": "local/default", "provider": "local"}), "local")
        self.assertEqual(model_profile_tier({"id": "openrouter/fast", "cost": "low"}), "value")
        self.assertEqual(model_profile_tier({"id": "openrouter/cheap", "cost": "free"}), "free")

    def test_model_profile_sort_key_orders_user_hierarchy(self):
        profiles = [
            {"id": "openrouter/cheap", "cost": "free"},
            {"id": "openrouter/fast", "cost": "low"},
            {"id": "openrouter/sota"},
            {"id": "local/default", "provider": "local"},
            {"id": "closed/claude", "model": "claude"},
            {"id": "codex/default", "provider": "codex"},
        ]

        ordered = [profile["id"] for profile in sorted(profiles, key=model_profile_sort_key)]

        self.assertEqual(
            ordered,
            [
                "codex/default",
                "closed/claude",
                "openrouter/sota",
                "local/default",
                "openrouter/fast",
                "openrouter/cheap",
            ],
        )

    def test_model_profile_cost_units_use_existing_cost_hints(self):
        self.assertEqual(model_profile_cost_units({"id": "local/default", "provider": "local"}), 0)
        self.assertEqual(model_profile_cost_units({"id": "openrouter/fast", "cost": "low"}), 1)
        self.assertEqual(model_profile_cost_units({"id": "openrouter/sota", "cost": "high"}), 3)

    def test_estimate_role_model_plan_savings_against_lead_only(self):
        plan = [
            {"role": "scout", "profile": {"id": "local/default", "provider": "local"}},
            {"role": "coordinator", "profile": {"id": "openrouter/fast", "cost": "low"}},
            {"role": "lead", "profile": {"id": "openrouter/sota", "cost": "high"}},
        ]

        estimate = estimate_role_model_plan_savings(plan, {"id": "openrouter/sota", "cost": "high"})

        self.assertEqual(estimate["baseline"], "lead-only")
        self.assertEqual(estimate["baselineUnits"], 9)
        self.assertEqual(estimate["planUnits"], 4)
        self.assertEqual(estimate["savedUnits"], 5)
        self.assertEqual(estimate["savedPercent"], 56)

    def test_estimate_role_model_plan_savings_can_show_over_baseline(self):
        plan = [
            {"role": "scout", "profile": {"id": "local/default", "provider": "local"}},
            {"role": "coordinator", "profile": {"id": "openrouter/fast", "cost": "low"}},
            {"role": "lead", "profile": {"id": "local/default", "provider": "local"}},
        ]

        estimate = estimate_role_model_plan_savings(plan, {"id": "local/default", "provider": "local"})

        self.assertEqual(estimate["baselineUnits"], 0)
        self.assertEqual(estimate["planUnits"], 1)
        self.assertEqual(estimate["savedUnits"], -1)
        self.assertEqual(estimate["savedPercent"], 0)

    def test_role_model_env_overrides_groups_by_role(self):
        plan = [
            {"role": "scout", "profile": {"id": "local/default", "provider": "local", "model": "local"}},
            {"role": "coordinator", "profile": {"id": "openrouter/fast", "provider": "openrouter", "model": "fast"}},
        ]

        env = role_model_env_overrides(plan)

        self.assertEqual(env["scout"]["PET_STUDIO_MODEL_PROFILE"], "local/default")
        self.assertEqual(env["coordinator"]["OPENROUTER_MODEL"], "fast")

    def test_role_model_env_clear_groups_by_role(self):
        plan = [
            {"role": "scout", "profile": {"id": "local/default", "provider": "local", "model": "local"}},
            {"role": "coordinator", "profile": {"id": "openrouter/fast", "provider": "openrouter", "model": "fast"}},
        ]

        clear = role_model_env_clear(plan)

        self.assertEqual(clear["scout"], ["OPENROUTER_MODEL", "CODEX_MODEL"])
        self.assertEqual(clear["coordinator"], ["CODEX_MODEL"])

    def test_role_model_plan_powershell_env_lines_groups_sections(self):
        plan = [
            {"role": "scout", "profile": {"id": "local/default", "provider": "local", "model": "local"}},
            {"role": "coordinator", "profile": {"id": "openrouter/fast", "provider": "openrouter", "model": "fast"}},
        ]

        lines = role_model_plan_powershell_env_lines(plan)

        self.assertIn("# Pet Studio team model env plan", lines)
        self.assertIn("# Copy one role section at a time; later sections reuse the same env variable names.", lines)
        self.assertIn("# scout: local/default", lines)
        self.assertIn("# coordinator: openrouter/fast", lines)
        self.assertIn("$env:OPENROUTER_MODEL = 'fast'", lines)


if __name__ == "__main__":
    unittest.main()
