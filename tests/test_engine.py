"""Cooldowns and cancellation without real clocks, sleeps, threads, or keys."""

from types import SimpleNamespace
import unittest
from unittest.mock import patch

from tests.support import FakeClock, FakeEvent, ManualThreads, offline_backend


class EngineTestCase(unittest.TestCase):
    def setUp(self):
        context = offline_backend("engine")
        modules, self.inputs = context.__enter__()
        self.addCleanup(context.__exit__, None, None, None)
        self.engine = modules.engine
        self.clock = FakeClock()
        self.threads = ManualThreads()
        patches = patch.multiple(
            self.engine,
            time=SimpleNamespace(time=self.clock.time, sleep=self.clock.sleep),
            threading=SimpleNamespace(Event=FakeEvent, Thread=self.threads.Thread),
        )
        patches.start()
        self.addCleanup(patches.stop)
        self.logs = []


class SkillTests(EngineTestCase):
    def test_all_skill_indices_map_to_number_keys(self):
        game = self.engine.GameClassEngine([0] * 6)
        for index in range(6):
            self.assertTrue(game.use_skill(index, FakeEvent(), self.logs.append))
        self.assertEqual(self.inputs.presses, ["0", "1", "2", "3", "4", "5"])
        self.assertEqual(self.clock.sleeps, [])
        self.assertEqual(self.threads.created, [])

    def test_cooldown_and_skill_indices_are_validated_before_pressing(self):
        for cooldowns in ([], [0] * 5, [0] * 7):
            with self.subTest(cooldowns=cooldowns), self.assertRaises(AssertionError):
                self.engine.GameClassEngine(cooldowns)
        game = self.engine.GameClassEngine([0] * 6)
        for index in (-1, 6):
            with self.subTest(index=index), self.assertRaises(AssertionError):
                game.use_skill(index, FakeEvent(), self.logs.append)
        self.assertEqual(self.inputs.presses, [])

    def test_skill_one_does_not_seed_other_cooldowns_and_reset_clears_state(self):
        game = self.engine.GameClassEngine([0, 0.5, 5, 3, 1.5, 6])
        self.assertEqual(game.last_left, [0.0] * 6)
        game.use_skill(1, FakeEvent(), self.logs.append)
        self.assertEqual(game.last_left, [0, 0.5, 0, 0, 0, 0])
        game.use_skill(2, FakeEvent(), self.logs.append)
        self.assertEqual(game.last_left, [0, 0.5, 5, 1, 1, 1])
        game.reset()
        self.assertEqual(game.last_left, [0.0] * 6)
        self.assertEqual(self.inputs.presses, ["1", "2"])
        self.assertEqual(self.clock.sleeps, [])

    def test_reusing_skill_waits_and_decrements_other_cooldowns(self):
        game = self.engine.GameClassEngine([0, 0.5, 0.2, 0.1, 0.3, 0.4])
        event = FakeEvent()
        game.use_skill(2, event, self.logs.append)
        self.assertEqual(game.last_left, [0, 0.5, 0.2, 0.1, 0.3, 0.4])
        before = self.clock.time()
        self.assertTrue(game.use_skill(2, event, self.logs.append))
        self.assertAlmostEqual(self.clock.time() - before, 0.2)
        self.assertEqual(self.clock.sleeps, [0.05] * 4)
        for actual, expected in zip(game.last_left, [0, 0.3, 0.2, 0.1, 0.1, 0.2]):
            self.assertAlmostEqual(actual, expected)
        self.assertEqual(self.inputs.presses, ["2", "2"])
        self.assertTrue(any("Waiting 0.2s for skill 2" in log for log in self.logs))

    def test_cancellation_during_cooldown_returns_false_without_press_or_state_change(self):
        game = self.engine.GameClassEngine([0, 0, 0.2, 0, 0, 0])
        event = FakeEvent()
        game.use_skill(2, event, self.logs.append)
        previous = list(game.last_left)
        self.clock.on_sleep = event.set
        self.assertFalse(game.use_skill(2, event, self.logs.append))
        self.assertEqual(game.last_left, previous)
        self.assertEqual(self.inputs.presses, ["2"])
        self.assertEqual(self.clock.sleeps, [0.05])

    def test_already_cancelled_cooldown_does_not_wait_or_press(self):
        game = self.engine.GameClassEngine([0, 0, 1, 0, 0, 0])
        game.last_left[2] = 1
        event = FakeEvent()
        event.set()
        self.assertFalse(game.use_skill(2, event, self.logs.append))
        self.assertEqual(self.inputs.presses, [])
        self.assertEqual(self.clock.sleeps, [])
        self.assertEqual(game.last_left[2], 1)


class RunnerTests(EngineTestCase):
    def setUp(self):
        super().setUp()
        self.runner = self.engine.AutomationRunner()

    def start(self, *, cooldowns=None, sequence=None, repeat=1, delay=0, log=None):
        self.runner.start(
            cooldowns=[0] * 6 if cooldowns is None else cooldowns,
            sequence=[1, 2] if sequence is None else sequence,
            repeat=repeat,
            initial_delay=delay,
            log=self.logs.append if log is None else log,
        )
        return self.threads.created[-1]

    def test_finite_repeats_preserve_order_after_simulated_startup_delay(self):
        self.assertFalse(self.runner.is_running())
        pressed_at = []

        def log(message):
            self.logs.append(message)
            if "pressed" in message:
                pressed_at.append(self.clock.time())

        before = self.clock.time()
        thread = self.start(sequence=[5, 2, 1], repeat=2, delay=0.15, log=log)
        self.assertTrue(thread.daemon)
        self.assertTrue(self.runner.is_running())
        self.assertEqual(self.inputs.presses, [])
        thread.run_to_completion()
        self.assertFalse(self.runner.is_running())
        self.assertEqual(self.inputs.presses, ["5", "2", "1", "5", "2", "1"])
        self.assertEqual(self.clock.sleeps, [0.05] * 3)
        for timestamp in pressed_at:
            self.assertAlmostEqual(timestamp - before, 0.15)
        self.assertTrue(any("Loop 1/2" in log for log in self.logs))
        self.assertTrue(any("Loop 2/2" in log for log in self.logs))
        self.assertIn("✅ Sequence complete.", self.logs)
        self.assertEqual(self.logs[-1], "🔴 Automation stopped.")

    def test_duplicate_start_does_not_create_or_replace_active_worker(self):
        first = self.start(sequence=[2])
        self.runner.start([0] * 6, [5], 9, 10, self.logs.append)
        self.assertEqual(self.threads.created, [first])
        self.assertIs(self.runner._thread, first)
        first.run_to_completion()
        self.assertEqual(self.inputs.presses, ["2"])

    def test_stop_during_startup_aborts_before_any_skill(self):
        self.clock.on_sleep = self.runner.stop
        thread = self.start(delay=1)
        thread.run_to_completion()
        self.assertEqual(self.inputs.presses, [])
        self.assertEqual(self.clock.sleeps, [0.05])
        self.assertIn("🛑 Aborted during startup delay.", self.logs)
        self.assertNotIn("🟢 Automation running.", self.logs)
        self.assertFalse(self.runner.is_running())

    def test_stop_before_worker_runs_is_observed_without_pressing(self):
        thread = self.start()
        self.runner.stop()
        thread.run_to_completion()
        self.assertEqual(self.inputs.presses, [])
        self.assertEqual(self.clock.sleeps, [])
        self.assertFalse(self.runner.is_running())

    def test_stop_during_skill_cooldown_prevents_remaining_sequence(self):
        self.clock.on_sleep = self.runner.stop
        thread = self.start(
            cooldowns=[0, 0, 0.2, 0, 0, 0], sequence=[2, 2, 5], repeat=0,
        )
        thread.run_to_completion()
        self.assertEqual(self.inputs.presses, ["2"])
        self.assertEqual(self.clock.sleeps, [0.05])
        self.assertFalse(self.runner.is_running())
        self.assertEqual(self.logs[-1], "🔴 Automation stopped.")

    def test_stop_between_skills_prevents_next_keypress(self):
        def log(message):
            self.logs.append(message)
            if "Skill 2 pressed" in message:
                self.runner.stop()

        thread = self.start(sequence=[2, 3, 4], repeat=0, log=log)
        thread.run_to_completion()
        self.assertEqual(self.inputs.presses, ["2"])
        self.assertEqual(self.clock.sleeps, [])
        self.assertFalse(self.runner.is_running())

    def test_infinite_repeat_stops_at_deterministic_keypress_boundary(self):
        def log(message):
            self.logs.append(message)
            if "pressed" in message and len(self.inputs.presses) == 5:
                self.runner.stop()

        thread = self.start(repeat=0, log=log)
        thread.run_to_completion()
        self.assertEqual(self.inputs.presses, ["1", "2", "1", "2", "1"])
        self.assertEqual(sum("Loop ∞" in log for log in self.logs), 3)
        self.assertEqual(self.clock.sleeps, [])
        self.assertFalse(self.runner.is_running())
        self.assertNotIn("✅ Sequence complete.", self.logs)

    def test_completed_or_cancelled_runner_can_restart_with_cleared_stop_event(self):
        first = self.start(sequence=[3])
        self.runner.stop()
        first.run_to_completion()
        self.assertEqual(self.inputs.presses, [])
        second = self.start(sequence=[4])
        self.assertFalse(self.runner._stop_event.is_set())
        self.assertIsNot(first, second)
        second.run_to_completion()
        self.assertEqual(self.inputs.presses, ["4"])
        third = self.start(sequence=[5])
        third.run_to_completion()
        self.assertEqual(self.inputs.presses, ["4", "5"])
        self.assertFalse(self.runner.is_running())
