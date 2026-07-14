from __future__ import annotations

import io
import json
import unittest
from contextlib import redirect_stdout

import live_profile_probe as probe


class EmitTests(unittest.TestCase):
    def test_emit_is_ascii_safe_on_cp932_stdout(self) -> None:
        buffer = io.BytesIO()
        stream = io.TextIOWrapper(buffer, encoding="cp932", newline="\n")

        with redirect_stdout(stream):
            probe.emit({"text": "\ufffd"})
            stream.flush()

        encoded = buffer.getvalue()
        self.assertTrue(encoded.isascii())
        self.assertEqual(json.loads(encoded.decode("ascii")), {"text": "\ufffd"})


class TypeNameTests(unittest.TestCase):
    def test_type_name_fields_separate_binary_type_code(self) -> None:
        data = b"MXR300-32       " + bytes.fromhex("cdab")

        fields = probe.type_name_fields(data)

        self.assertEqual(fields["raw_hex"], data.hex())
        self.assertEqual(fields["text"], "MXR300-32")
        self.assertEqual(fields["type_code_hex"], "cdab")

    def test_type_name_fields_omit_type_code_when_response_is_short(self) -> None:
        fields = probe.type_name_fields(b"MXR300-32")

        self.assertEqual(fields["text"], "MXR300-32")
        self.assertNotIn("type_code_hex", fields)


if __name__ == "__main__":
    unittest.main()
