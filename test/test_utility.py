from scripts.utilityModule import get_encode_type


def test_get_encode_type():
    assert "utf-8" == get_encode_type("./test/encoding/utf-8.txt")
    assert "utf-8" == get_encode_type("./test/encoding/utf-8_only_ascii.txt")
    assert "SHIFT_JIS" == get_encode_type("./test/encoding/sjis.txt")
    assert "EUC-JP" == get_encode_type("./test/encoding/euc-jp.txt")
