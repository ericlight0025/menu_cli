"""Regression tests use in-memory fixtures; never touch the user's data files."""
import io
import unittest
from copy import deepcopy
from pathlib import Path
from unittest.mock import patch

import actions
import csv_import
import menu


class CsvRegressionTests(unittest.TestCase):
    def setUp(self):
        self.root = {
            "name": "My menu",
            "children": [
                {"name": "Tools", "children": [
                    {"name": "About", "action": {"type": "about"}}
                ]},
                {"name": "Empty", "children": []},
            ],
        }
        self.loader = patch.object(csv_import, "load_menu_data", return_value=self.root)
        self.saver = patch.object(csv_import, "save_menu_data")
        self.loader.start()
        self.save = self.saver.start()
        self.addCleanup(self.loader.stop)
        self.addCleanup(self.saver.stop)

    def test_group_update_preserves_children(self):
        result, errors = csv_import.import_csv_to_menu([
            {"path": "My menu", "name": "Tools", "kind": "group", "action": ""}
        ])
        self.assertEqual(errors, [])
        self.assertEqual(result, self.root)
        self.save.assert_called_once_with(result)

    def test_export_import_round_trip_with_renamed_root_and_empty_group(self):
        rows = csv_import._menu_to_csv_rows(self.root)
        self.assertEqual(rows[-1]["kind"], "group")
        result, errors = csv_import.import_csv_to_menu(rows)
        self.assertEqual(errors, [])
        self.assertEqual(result, self.root)

    def test_group_after_child_does_not_erase_child(self):
        result, errors = csv_import.import_csv_to_menu([
            {"path": "New", "name": "Item", "kind": "action", "action": '{"type":"about"}'},
            {"path": "", "name": "New", "kind": "group", "action": ""},
        ])
        self.assertEqual(errors, [])
        self.assertEqual(result["children"][-1]["children"][0]["name"], "Item")

    def test_invalid_action_does_not_save_or_mutate_source(self):
        original = deepcopy(self.root)
        _, errors = csv_import.import_csv_to_menu([
            {"path": "New", "name": "Invalid", "kind": "action", "action": "[]"}
        ])
        self.assertTrue(errors)
        self.save.assert_not_called()
        self.assertEqual(self.root, original)

    def read_text(self, text):
        with patch.object(Path, "exists", return_value=True), patch.object(
            Path, "open", return_value=io.StringIO(text)
        ):
            return csv_import.read_csv_rows(Path("memory.csv"))

    def test_extra_columns_raise_readable_error(self):
        with self.assertRaisesRegex(ValueError, "第 2 行"):
            self.read_text('path,name,kind,action\n,Item,action,{},extra\n')

    def test_missing_headers_raise_readable_error(self):
        with self.assertRaisesRegex(ValueError, "path"):
            self.read_text('name,kind\nItem,action\n')

    def test_quoted_action_and_blank_lines(self):
        rows = self.read_text('path,name,kind,action\n,Item,action,"{""type"":""about""}"\n,,,\n')
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["action"], '{"type":"about"}')


class ActionRegressionTests(unittest.TestCase):
    def test_template_opens_generated_file_not_import_file(self):
        template = csv_import.CSV_TEMPLATE_FILE
        with patch.object(actions, "write_csv_template_from_menu", return_value=template), patch.object(
            actions.os, "startfile", create=True
        ) as opener, patch.object(actions, "_info"):
            actions.download_csv_template()
        opener.assert_called_once_with(str(template))

    def test_csv_read_errors_do_not_crash_or_import(self):
        for handler in (actions.show_csv_preview, actions.import_csv_menu):
            with self.subTest(handler=handler.__name__), patch.object(
                actions, "ensure_csv_import_file"
            ), patch.object(actions, "read_csv_rows", side_effect=ValueError("bad CSV")), patch.object(
                actions, "_pause"
            ), patch.object(actions, "_error") as error, patch.object(
                actions, "import_csv_to_menu"
            ) as importer:
                handler()
                error.assert_called_once()
                importer.assert_not_called()


class NavigationRegressionTests(unittest.TestCase):
    def test_empty_group_can_navigate_back(self):
        empty = {"name": "Empty", "children": []}
        root = {"name": "Home", "children": [empty]}
        with patch.object(menu, "MenuState"), patch.object(menu, "load_menu_data", return_value=root), patch.object(
            menu, "draw_header"
        ), patch.object(menu, "get_prompt_style"), patch.object(menu, "clear"), patch.object(
            menu, "ask_fuzzy", side_effect=[empty, menu.NAV_BACK, None]
        ) as prompt, patch.object(menu, "execute_action") as execute, patch("builtins.print"):
            menu.run()
        self.assertEqual(prompt.call_count, 3)
        self.assertIs(prompt.call_args_list[1].args[0][0]["value"], menu.NAV_BACK)
        execute.assert_not_called()

    def test_empty_root_can_exit(self):
        with patch.object(menu, "MenuState"), patch.object(
            menu, "load_menu_data", return_value={"name": "Home", "children": []}
        ), patch.object(menu, "draw_header"), patch.object(menu, "get_prompt_style"), patch.object(
            menu, "clear"
        ), patch.object(menu, "ask_fuzzy", return_value=None), patch("builtins.print"):
            menu.run()


if __name__ == "__main__":
    unittest.main()
